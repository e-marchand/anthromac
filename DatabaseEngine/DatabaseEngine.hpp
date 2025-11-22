#pragma once

#include <string>
#include <string_view>
#include <map>
#include <vector>
#include <memory>
#include <fstream>
#include <filesystem>
#include <stdexcept>
#include <cstdint>
#include <cstring>
#include <optional>
#include <mutex>
#include <shared_mutex>
#include <algorithm>
#include <sstream>

namespace db {

namespace fs = std::filesystem;

// Exception types
class DatabaseError : public std::runtime_error {
public:
    explicit DatabaseError(const std::string& msg) : std::runtime_error(msg) {}
};

class KeyNotFoundError : public DatabaseError {
public:
    explicit KeyNotFoundError(const std::string& key)
        : DatabaseError("Key not found: " + key) {}
};

// Compression types
enum class CompressionType {
    None,
    Snappy,
    LZ4
};

// Forward declarations
class Iterator;
class Snapshot;
using IteratorPtr = std::unique_ptr<Iterator>;

// Database options
struct Options {
    bool create_if_missing = true;
    size_t memtable_size = 4 * 1024 * 1024;     // 4MB
    size_t block_size = 4096;                    // 4KB
    size_t max_open_files = 1000;
    CompressionType compression = CompressionType::None;
    int bloom_filter_bits_per_key = 10;
    bool use_bloom_filter = true;
    size_t write_buffer_size = 4 * 1024 * 1024;
    size_t l0_compaction_threshold = 4;
    size_t max_bytes_for_level_base = 10 * 1024 * 1024;  // 10MB
};

// Database statistics
struct Stats {
    size_t num_keys = 0;
    size_t num_sst_files = 0;
    size_t memtable_size = 0;
    size_t total_disk_size = 0;
    size_t num_compactions = 0;
};

// Bloom filter for fast negative lookups
class BloomFilter {
public:
    BloomFilter(size_t estimated_keys, int bits_per_key)
        : bits_per_key_(bits_per_key) {
        size_t bits = estimated_keys * bits_per_key;
        bits = std::max(bits, size_t(64));
        size_t bytes = (bits + 7) / 8;
        bits = bytes * 8;

        bits_.resize(bytes, 0);
        num_bits_ = bits;
        num_hash_funcs_ = static_cast<int>(bits_per_key * 0.69);  // ln(2)
        if (num_hash_funcs_ < 1) num_hash_funcs_ = 1;
        if (num_hash_funcs_ > 30) num_hash_funcs_ = 30;
    }

    void add(const std::string& key) {
        uint32_t h = hash(key);
        const uint32_t delta = (h >> 17) | (h << 15);

        for (int i = 0; i < num_hash_funcs_; ++i) {
            const uint32_t bit_pos = h % num_bits_;
            bits_[bit_pos / 8] |= (1 << (bit_pos % 8));
            h += delta;
        }
    }

    bool may_contain(const std::string& key) const {
        uint32_t h = hash(key);
        const uint32_t delta = (h >> 17) | (h << 15);

        for (int i = 0; i < num_hash_funcs_; ++i) {
            const uint32_t bit_pos = h % num_bits_;
            if ((bits_[bit_pos / 8] & (1 << (bit_pos % 8))) == 0) {
                return false;
            }
            h += delta;
        }
        return true;
    }

    std::vector<uint8_t> serialize() const {
        std::vector<uint8_t> result;
        result.reserve(bits_.size() + 12);

        // Header: num_bits, num_hash_funcs
        uint32_t nb = static_cast<uint32_t>(num_bits_);
        result.insert(result.end(), reinterpret_cast<uint8_t*>(&nb),
                     reinterpret_cast<uint8_t*>(&nb) + 4);
        result.insert(result.end(), reinterpret_cast<uint8_t*>(&num_hash_funcs_),
                     reinterpret_cast<uint8_t*>(&num_hash_funcs_) + 4);

        // Bit array
        result.insert(result.end(), bits_.begin(), bits_.end());
        return result;
    }

    static BloomFilter deserialize(const std::vector<uint8_t>& data) {
        if (data.size() < 8) {
            throw DatabaseError("Invalid bloom filter data");
        }

        uint32_t num_bits;
        int num_hash_funcs;
        std::memcpy(&num_bits, data.data(), 4);
        std::memcpy(&num_hash_funcs, data.data() + 4, 4);

        BloomFilter bf(1, 10);  // Dummy values
        bf.num_bits_ = num_bits;
        bf.num_hash_funcs_ = num_hash_funcs;
        bf.bits_.assign(data.begin() + 8, data.end());

        return bf;
    }

private:
    static uint32_t hash(const std::string& key) {
        // Simple hash function (Murmur-inspired)
        uint32_t h = 0xbc9f1d34;
        for (char c : key) {
            h ^= static_cast<uint32_t>(c);
            h *= 0x5bd1e995;
            h ^= h >> 15;
        }
        return h;
    }

    std::vector<uint8_t> bits_;
    size_t num_bits_;
    int num_hash_funcs_;
    int bits_per_key_;
};

// Entry in the database
struct Entry {
    std::string key;
    std::string value;
    uint64_t sequence;
    bool deleted = false;

    Entry() = default;
    Entry(std::string k, std::string v, uint64_t seq, bool del = false)
        : key(std::move(k)), value(std::move(v)), sequence(seq), deleted(del) {}
};

// MemTable: in-memory sorted map
class MemTable {
public:
    MemTable() : size_(0) {}

    void put(const std::string& key, const std::string& value, uint64_t sequence) {
        auto it = table_.find(key);
        if (it != table_.end()) {
            size_ -= it->second.value.size();
        }

        table_[key] = Entry(key, value, sequence, false);
        size_ += key.size() + value.size();
    }

    void del(const std::string& key, uint64_t sequence) {
        table_[key] = Entry(key, "", sequence, true);
        size_ += key.size();
    }

    std::optional<Entry> get(const std::string& key) const {
        auto it = table_.find(key);
        if (it != table_.end()) {
            return it->second;
        }
        return std::nullopt;
    }

    size_t size() const { return size_; }
    bool empty() const { return table_.empty(); }

    auto begin() const { return table_.begin(); }
    auto end() const { return table_.end(); }

    const std::map<std::string, Entry>& entries() const { return table_; }

private:
    std::map<std::string, Entry> table_;
    size_t size_;
};

// SSTable: immutable on-disk sorted file
class SSTable {
public:
    struct Footer {
        uint64_t index_offset;
        uint64_t bloom_offset;
        uint32_t magic = 0x5354424c;  // "STBL"
    };

    SSTable(const fs::path& path) : path_(path) {}

    // Write SSTable from MemTable
    static void write(const fs::path& path, const MemTable& memtable,
                     const Options& opts) {
        std::ofstream file(path, std::ios::binary);
        if (!file) {
            throw DatabaseError("Cannot create SSTable: " + path.string());
        }

        std::vector<std::pair<std::string, uint64_t>> index;  // key -> offset
        BloomFilter bloom(memtable.entries().size(), opts.bloom_filter_bits_per_key);

        // Write data blocks
        uint64_t offset = 0;
        for (const auto& [key, entry] : memtable.entries()) {
            // Add to bloom filter
            if (opts.use_bloom_filter) {
                bloom.add(key);
            }

            // Record index entry (one per key for simplicity)
            index.emplace_back(key, offset);

            // Write entry: [key_len][key][value_len][value][seq][deleted]
            uint32_t key_len = static_cast<uint32_t>(key.size());
            uint32_t value_len = static_cast<uint32_t>(entry.value.size());

            file.write(reinterpret_cast<const char*>(&key_len), 4);
            file.write(key.data(), key_len);
            file.write(reinterpret_cast<const char*>(&value_len), 4);
            file.write(entry.value.data(), value_len);
            file.write(reinterpret_cast<const char*>(&entry.sequence), 8);
            file.write(reinterpret_cast<const char*>(&entry.deleted), 1);

            offset = file.tellp();
        }

        // Write index block
        uint64_t index_offset = file.tellp();
        uint32_t index_size = static_cast<uint32_t>(index.size());
        file.write(reinterpret_cast<const char*>(&index_size), 4);

        for (const auto& [key, off] : index) {
            uint32_t key_len = static_cast<uint32_t>(key.size());
            file.write(reinterpret_cast<const char*>(&key_len), 4);
            file.write(key.data(), key_len);
            file.write(reinterpret_cast<const char*>(&off), 8);
        }

        // Write bloom filter
        uint64_t bloom_offset = file.tellp();
        if (opts.use_bloom_filter) {
            auto bloom_data = bloom.serialize();
            uint32_t bloom_size = static_cast<uint32_t>(bloom_data.size());
            file.write(reinterpret_cast<const char*>(&bloom_size), 4);
            file.write(reinterpret_cast<const char*>(bloom_data.data()), bloom_size);
        } else {
            uint32_t bloom_size = 0;
            file.write(reinterpret_cast<const char*>(&bloom_size), 4);
        }

        // Write footer
        Footer footer{index_offset, bloom_offset};
        file.write(reinterpret_cast<const char*>(&footer), sizeof(Footer));

        file.close();
    }

    // Read entry by key
    std::optional<Entry> get(const std::string& key) {
        if (!file_.is_open()) {
            open();
        }

        // Check bloom filter first
        if (bloom_ && !bloom_->may_contain(key)) {
            return std::nullopt;
        }

        // Binary search in index
        auto it = std::lower_bound(index_.begin(), index_.end(), key,
            [](const auto& entry, const std::string& k) {
                return entry.first < k;
            });

        if (it == index_.end() || it->first != key) {
            return std::nullopt;
        }

        // Read entry from file
        file_.seekg(it->second);

        uint32_t key_len, value_len;
        file_.read(reinterpret_cast<char*>(&key_len), 4);

        std::string entry_key(key_len, '\0');
        file_.read(&entry_key[0], key_len);

        file_.read(reinterpret_cast<char*>(&value_len), 4);
        std::string value(value_len, '\0');
        file_.read(&value[0], value_len);

        uint64_t sequence;
        bool deleted;
        file_.read(reinterpret_cast<char*>(&sequence), 8);
        file_.read(reinterpret_cast<char*>(&deleted), 1);

        return Entry(entry_key, value, sequence, deleted);
    }

    // Get all entries (for compaction)
    std::vector<Entry> get_all() {
        if (!file_.is_open()) {
            open();
        }

        std::vector<Entry> entries;
        entries.reserve(index_.size());

        for (const auto& [key, offset] : index_) {
            auto entry = get(key);
            if (entry) {
                entries.push_back(*entry);
            }
        }

        return entries;
    }

    const fs::path& path() const { return path_; }
    size_t num_keys() const { return index_.size(); }

private:
    void open() {
        file_.open(path_, std::ios::binary);
        if (!file_) {
            throw DatabaseError("Cannot open SSTable: " + path_.string());
        }

        // Read footer
        file_.seekg(-static_cast<int>(sizeof(Footer)), std::ios::end);
        Footer footer;
        file_.read(reinterpret_cast<char*>(&footer), sizeof(Footer));

        if (footer.magic != 0x5354424c) {
            throw DatabaseError("Invalid SSTable magic number");
        }

        // Read bloom filter
        file_.seekg(footer.bloom_offset);
        uint32_t bloom_size;
        file_.read(reinterpret_cast<char*>(&bloom_size), 4);

        if (bloom_size > 0) {
            std::vector<uint8_t> bloom_data(bloom_size);
            file_.read(reinterpret_cast<char*>(bloom_data.data()), bloom_size);
            bloom_ = std::make_unique<BloomFilter>(BloomFilter::deserialize(bloom_data));
        }

        // Read index
        file_.seekg(footer.index_offset);
        uint32_t index_size;
        file_.read(reinterpret_cast<char*>(&index_size), 4);

        index_.reserve(index_size);
        for (uint32_t i = 0; i < index_size; ++i) {
            uint32_t key_len;
            file_.read(reinterpret_cast<char*>(&key_len), 4);

            std::string key(key_len, '\0');
            file_.read(&key[0], key_len);

            uint64_t offset;
            file_.read(reinterpret_cast<char*>(&offset), 8);

            index_.emplace_back(key, offset);
        }
    }

    fs::path path_;
    std::ifstream file_;
    std::vector<std::pair<std::string, uint64_t>> index_;
    std::unique_ptr<BloomFilter> bloom_;
};

// Write-Ahead Log for durability
class WriteAheadLog {
public:
    explicit WriteAheadLog(const fs::path& path) : path_(path) {
        file_.open(path, std::ios::binary | std::ios::app);
        if (!file_) {
            throw DatabaseError("Cannot open WAL: " + path.string());
        }
    }

    void append(const std::string& key, const std::string& value,
                bool deleted, uint64_t sequence) {
        // Format: [seq][key_len][key][value_len][value][deleted]
        file_.write(reinterpret_cast<const char*>(&sequence), 8);

        uint32_t key_len = static_cast<uint32_t>(key.size());
        file_.write(reinterpret_cast<const char*>(&key_len), 4);
        file_.write(key.data(), key_len);

        uint32_t value_len = static_cast<uint32_t>(value.size());
        file_.write(reinterpret_cast<const char*>(&value_len), 4);
        file_.write(value.data(), value_len);

        file_.write(reinterpret_cast<const char*>(&deleted), 1);
        file_.flush();
    }

    void sync() {
        file_.flush();
    }

    void clear() {
        file_.close();
        file_.open(path_, std::ios::binary | std::ios::trunc);
    }

    // Replay WAL into memtable
    static void replay(const fs::path& path, MemTable& memtable, uint64_t& sequence) {
        if (!fs::exists(path)) {
            return;
        }

        std::ifstream file(path, std::ios::binary);
        if (!file) {
            return;
        }

        while (file.peek() != EOF) {
            uint64_t seq;
            if (!file.read(reinterpret_cast<char*>(&seq), 8)) break;

            uint32_t key_len;
            if (!file.read(reinterpret_cast<char*>(&key_len), 4)) break;

            std::string key(key_len, '\0');
            if (!file.read(&key[0], key_len)) break;

            uint32_t value_len;
            if (!file.read(reinterpret_cast<char*>(&value_len), 4)) break;

            std::string value(value_len, '\0');
            if (!file.read(&value[0], value_len)) break;

            bool deleted;
            if (!file.read(reinterpret_cast<char*>(&deleted), 1)) break;

            if (deleted) {
                memtable.del(key, seq);
            } else {
                memtable.put(key, value, seq);
            }

            sequence = std::max(sequence, seq + 1);
        }
    }

private:
    fs::path path_;
    std::ofstream file_;
};

// Snapshot for point-in-time reads
class Snapshot {
public:
    explicit Snapshot(uint64_t sequence) : sequence_(sequence) {}
    uint64_t sequence() const { return sequence_; }

private:
    uint64_t sequence_;
};

// Iterator for range scans
class Iterator {
public:
    virtual ~Iterator() = default;
    virtual void seek_to_first() = 0;
    virtual void seek_to_last() = 0;
    virtual void seek(const std::string& key) = 0;
    virtual void next() = 0;
    virtual void prev() = 0;
    virtual bool valid() const = 0;
    virtual std::string key() const = 0;
    virtual std::string value() const = 0;
};

// MemTable iterator
class MemTableIterator : public Iterator {
public:
    explicit MemTableIterator(const MemTable& memtable)
        : memtable_(memtable), it_(memtable.begin()), end_(memtable.end()) {}

    void seek_to_first() override {
        it_ = memtable_.begin();
    }

    void seek_to_last() override {
        if (memtable_.empty()) {
            it_ = end_;
        } else {
            it_ = std::prev(end_);
        }
    }

    void seek(const std::string& key) override {
        it_ = memtable_.entries().lower_bound(key);
    }

    void next() override {
        if (it_ != end_) {
            ++it_;
        }
    }

    void prev() override {
        if (it_ != memtable_.begin()) {
            --it_;
        }
    }

    bool valid() const override {
        return it_ != end_ && !it_->second.deleted;
    }

    std::string key() const override {
        return it_->first;
    }

    std::string value() const override {
        return it_->second.value;
    }

private:
    const MemTable& memtable_;
    std::map<std::string, Entry>::const_iterator it_;
    std::map<std::string, Entry>::const_iterator end_;
};

// WriteBatch for atomic operations
class WriteBatch {
public:
    void put(const std::string& key, const std::string& value) {
        operations_.push_back({key, value, false});
    }

    void del(const std::string& key) {
        operations_.push_back({key, "", true});
    }

    void clear() {
        operations_.clear();
    }

    const auto& operations() const { return operations_; }

private:
    struct Op {
        std::string key;
        std::string value;
        bool deleted;
    };
    std::vector<Op> operations_;
};

// Main database engine
class DatabaseEngine {
public:
    DatabaseEngine(const std::string& path, const Options& opts = Options())
        : path_(path), opts_(opts), sequence_(0) {

        // Create directory if needed
        if (opts.create_if_missing) {
            fs::create_directories(path_);
        }

        if (!fs::exists(path_)) {
            throw DatabaseError("Database path does not exist: " + path);
        }

        // Open WAL
        wal_path_ = fs::path(path_) / "wal.log";
        wal_ = std::make_unique<WriteAheadLog>(wal_path_);

        // Recover from WAL
        WriteAheadLog::replay(wal_path_, memtable_, sequence_);

        // Load existing SSTables
        load_sstables();
    }

    ~DatabaseEngine() {
        // Flush memtable on close
        if (!memtable_.empty()) {
            flush();
        }
    }

    // Write operations
    void put(const std::string& key, const std::string& value) {
        std::unique_lock lock(mutex_);

        uint64_t seq = sequence_++;
        wal_->append(key, value, false, seq);
        memtable_.put(key, value, seq);

        // Flush if memtable is full
        if (memtable_.size() >= opts_.memtable_size) {
            flush_locked();
        }
    }

    void del(const std::string& key) {
        std::unique_lock lock(mutex_);

        uint64_t seq = sequence_++;
        wal_->append(key, "", true, seq);
        memtable_.del(key, seq);
    }

    void write(const WriteBatch& batch) {
        std::unique_lock lock(mutex_);

        for (const auto& op : batch.operations()) {
            uint64_t seq = sequence_++;
            wal_->append(op.key, op.value, op.deleted, seq);

            if (op.deleted) {
                memtable_.del(op.key, seq);
            } else {
                memtable_.put(op.key, op.value, seq);
            }
        }

        if (memtable_.size() >= opts_.memtable_size) {
            flush_locked();
        }
    }

    // Read operations
    std::string get(const std::string& key) {
        std::shared_lock lock(mutex_);

        // Check memtable first
        auto entry = memtable_.get(key);
        if (entry) {
            if (entry->deleted) {
                throw KeyNotFoundError(key);
            }
            return entry->value;
        }

        // Check SSTables (newest to oldest)
        for (auto it = sstables_.rbegin(); it != sstables_.rend(); ++it) {
            auto entry = (*it)->get(key);
            if (entry) {
                if (entry->deleted) {
                    throw KeyNotFoundError(key);
                }
                return entry->value;
            }
        }

        throw KeyNotFoundError(key);
    }

    std::string get(const std::string& key, const std::string& default_value) {
        try {
            return get(key);
        } catch (const KeyNotFoundError&) {
            return default_value;
        }
    }

    bool exists(const std::string& key) {
        try {
            get(key);
            return true;
        } catch (const KeyNotFoundError&) {
            return false;
        }
    }

    // Scan operations
    IteratorPtr scan(const std::string& start, const std::string& end) {
        // Simplified: return memtable iterator
        // Real implementation would merge iterators from all levels
        return std::make_unique<MemTableIterator>(memtable_);
    }

    IteratorPtr scan_prefix(const std::string& prefix) {
        return scan(prefix, prefix + "\xff");
    }

    IteratorPtr new_iterator() {
        return std::make_unique<MemTableIterator>(memtable_);
    }

    // Snapshot operations
    Snapshot* create_snapshot() {
        std::shared_lock lock(mutex_);
        return new Snapshot(sequence_);
    }

    void release_snapshot(Snapshot* snapshot) {
        delete snapshot;
    }

    // Maintenance
    void flush() {
        std::unique_lock lock(mutex_);
        flush_locked();
    }

    void compact() {
        std::unique_lock lock(mutex_);

        if (sstables_.size() < opts_.l0_compaction_threshold) {
            return;
        }

        // Simple compaction: merge all SSTables
        compact_locked();
    }

    Stats get_stats() const {
        std::shared_lock lock(mutex_);

        Stats stats;
        stats.memtable_size = memtable_.size();
        stats.num_sst_files = sstables_.size();

        for (const auto& sst : sstables_) {
            stats.num_keys += sst->num_keys();
            if (fs::exists(sst->path())) {
                stats.total_disk_size += fs::file_size(sst->path());
            }
        }

        return stats;
    }

private:
    void flush_locked() {
        if (memtable_.empty()) {
            return;
        }

        // Generate SSTable filename
        auto sst_path = fs::path(path_) / ("sst_" + std::to_string(sequence_) + ".db");

        // Write SSTable
        SSTable::write(sst_path, memtable_, opts_);

        // Add to list
        sstables_.push_back(std::make_unique<SSTable>(sst_path));

        // Clear memtable and WAL
        memtable_ = MemTable();
        wal_->clear();

        // Trigger compaction if needed
        if (sstables_.size() >= opts_.l0_compaction_threshold) {
            compact_locked();
        }
    }

    void compact_locked() {
        if (sstables_.size() < 2) {
            return;
        }

        // Collect all entries from all SSTables
        std::map<std::string, Entry> merged;

        for (const auto& sst : sstables_) {
            auto entries = sst->get_all();
            for (const auto& entry : entries) {
                auto it = merged.find(entry.key);
                if (it == merged.end() || entry.sequence > it->second.sequence) {
                    merged[entry.key] = entry;
                }
            }
        }

        // Remove deleted entries
        std::erase_if(merged, [](const auto& item) {
            return item.second.deleted;
        });

        // Write compacted SSTable
        MemTable compacted_table;
        for (const auto& [key, entry] : merged) {
            compacted_table.put(key, entry.value, entry.sequence);
        }

        auto compacted_path = fs::path(path_) / ("compacted_" + std::to_string(sequence_++) + ".db");
        SSTable::write(compacted_path, compacted_table, opts_);

        // Delete old SSTables
        for (const auto& sst : sstables_) {
            fs::remove(sst->path());
        }

        // Replace with compacted SSTable
        sstables_.clear();
        sstables_.push_back(std::make_unique<SSTable>(compacted_path));
    }

    void load_sstables() {
        for (const auto& entry : fs::directory_iterator(path_)) {
            if (entry.path().extension() == ".db") {
                sstables_.push_back(std::make_unique<SSTable>(entry.path()));
            }
        }

        // Sort by filename (older first)
        std::sort(sstables_.begin(), sstables_.end(),
            [](const auto& a, const auto& b) {
                return a->path().filename() < b->path().filename();
            });
    }

    std::string path_;
    Options opts_;
    uint64_t sequence_;

    MemTable memtable_;
    std::vector<std::unique_ptr<SSTable>> sstables_;

    fs::path wal_path_;
    std::unique_ptr<WriteAheadLog> wal_;

    mutable std::shared_mutex mutex_;
};

} // namespace db
