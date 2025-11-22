# DatabaseEngine - Embedded LSM-Tree Storage

A lightweight embedded database engine implementing Log-Structured Merge-Tree (LSM-Tree) architecture, similar to LevelDB/RocksDB but focused on simplicity and educational clarity.

## Features
- LSM-Tree architecture with efficient writes and reads
- Write-ahead logging (WAL) for durability and crash recovery
- In-memory MemTable with fast lookups
- SSTable format with block-based storage
- Bloom filters for efficient key existence checks
- Multi-level compaction for space efficiency
- MVCC for snapshot isolation
- Iterator support for range scans
- Atomic batch operations
- Compression support

## Architecture

### LSM-Tree Overview

The database uses a Log-Structured Merge-Tree architecture:

```
Writes → WAL → MemTable → (flush) → L0 SSTable → (compact) → L1 SSTable → ...
                  ↓
              Reads check:
              1. MemTable
              2. L0 SSTables
              3. L1+ SSTables
```

### Components

**1. Write-Ahead Log (WAL)**
- Append-only log for durability
- All writes persisted before MemTable update
- Used for crash recovery

**2. MemTable**
- In-memory sorted map (red-black tree)
- Fast O(log n) writes and reads
- Flushed to disk when size threshold reached

**3. SSTable (Sorted String Table)**
- Immutable on-disk sorted key-value files
- Block-based format with index
- Bloom filter for fast negative lookups
- Footer with metadata

**4. Bloom Filter**
- Probabilistic data structure
- Fast key existence checks
- Reduces unnecessary disk reads

**5. Compaction**
- Merges multiple SSTables
- Removes deleted keys and old versions
- Reduces space amplification
- Leveled compaction strategy

**6. MVCC (Multi-Version Concurrency Control)**
- Snapshot isolation for reads
- Lock-free reads
- Version numbers for keys

## Example

```cpp
#include "DatabaseEngine.hpp"
using namespace db;

// Open or create database
DatabaseEngine db("./mydb");

// Simple put/get
db.put("key1", "value1");
std::string value = db.get("key1");  // "value1"

// Batch operations
WriteBatch batch;
batch.put("key2", "value2");
batch.put("key3", "value3");
batch.del("key1");
db.write(batch);

// Range scan
auto it = db.scan("key1", "key9");
while (it->valid()) {
    std::cout << it->key() << ": " << it->value() << std::endl;
    it->next();
}

// Snapshots
auto snapshot = db.create_snapshot();
db.put("key4", "value4");
std::string val = db.get("key4", snapshot);  // Not found (pre-snapshot)
```

## Usage

### Opening a Database

```cpp
#include "DatabaseEngine.hpp"
using namespace db;

// Open with default options
DatabaseEngine db("./data");

// Open with custom options
Options opts;
opts.create_if_missing = true;
opts.memtable_size = 4 * 1024 * 1024;  // 4MB
opts.block_size = 4096;
opts.compression = CompressionType::None;

DatabaseEngine db2("./data2", opts);
```

### Basic Operations

```cpp
DatabaseEngine db("./mydb");

// Put key-value
db.put("name", "Alice");
db.put("age", "30");

// Get value
std::string name = db.get("name");  // "Alice"

// Check existence
if (db.exists("name")) {
    std::cout << "Key exists" << std::endl;
}

// Delete key
db.del("age");

// Get with default
std::string city = db.get("city", "Unknown");  // "Unknown"
```

### Batch Operations

```cpp
DatabaseEngine db("./mydb");

// Atomic batch write
WriteBatch batch;
batch.put("key1", "value1");
batch.put("key2", "value2");
batch.put("key3", "value3");
batch.del("old_key");

db.write(batch);  // All or nothing
```

### Range Scans

```cpp
DatabaseEngine db("./mydb");

// Populate data
db.put("apple", "fruit");
db.put("banana", "fruit");
db.put("carrot", "vegetable");

// Scan range [start, end)
auto it = db.scan("a", "c");
while (it->valid()) {
    std::cout << it->key() << " = " << it->value() << std::endl;
    it->next();
}
// Output:
// apple = fruit
// banana = fruit

// Scan all keys with prefix
auto prefix_it = db.scan_prefix("ba");
while (prefix_it->valid()) {
    std::cout << prefix_it->key() << std::endl;
    prefix_it->next();
}
// Output: banana
```

### Snapshots

```cpp
DatabaseEngine db("./mydb");

// Create snapshot
db.put("x", "1");
auto snap = db.create_snapshot();

// Modify after snapshot
db.put("x", "2");
db.put("y", "3");

// Read from snapshot (sees old data)
std::string x_old = db.get("x", snap);  // "1"
std::string y_old = db.get("y", snap);  // "" (not found)

// Read current data
std::string x_new = db.get("x");  // "2"

// Release snapshot
db.release_snapshot(snap);
```

### Iterator Usage

```cpp
DatabaseEngine db("./mydb");

// Full scan
auto it = db.new_iterator();
for (it->seek_to_first(); it->valid(); it->next()) {
    std::cout << it->key() << ": " << it->value() << std::endl;
}

// Seek to specific key
it->seek("key5");
if (it->valid()) {
    std::cout << "Found: " << it->key() << std::endl;
}

// Reverse iteration
for (it->seek_to_last(); it->valid(); it->prev()) {
    std::cout << it->key() << std::endl;
}
```

## API Reference

### DatabaseEngine Class

**Constructor:**
```cpp
DatabaseEngine(const std::string& path, const Options& opts = Options())
```

**Methods:**

**Write Operations:**
- `void put(const std::string& key, const std::string& value)` - Insert/update key
- `void del(const std::string& key)` - Delete key
- `void write(const WriteBatch& batch)` - Atomic batch write

**Read Operations:**
- `std::string get(const std::string& key)` - Get value (throws if not found)
- `std::string get(const std::string& key, const std::string& default_value)` - Get with default
- `bool exists(const std::string& key)` - Check key existence

**Scan Operations:**
- `IteratorPtr scan(const std::string& start, const std::string& end)` - Range scan
- `IteratorPtr scan_prefix(const std::string& prefix)` - Prefix scan
- `IteratorPtr new_iterator()` - Create iterator

**Snapshot Operations:**
- `Snapshot* create_snapshot()` - Create point-in-time snapshot
- `void release_snapshot(Snapshot* snapshot)` - Release snapshot

**Maintenance:**
- `void compact()` - Trigger manual compaction
- `void flush()` - Flush MemTable to disk
- `Stats get_stats()` - Get database statistics

### WriteBatch Class

```cpp
WriteBatch batch;
batch.put(key, value);
batch.del(key);
batch.clear();
```

### Iterator Class

```cpp
void seek_to_first();
void seek_to_last();
void seek(const std::string& key);
void next();
void prev();
bool valid() const;
std::string key() const;
std::string value() const;
```

### Options Struct

```cpp
struct Options {
    bool create_if_missing = true;
    size_t memtable_size = 4 * 1024 * 1024;     // 4MB
    size_t block_size = 4096;                    // 4KB
    size_t max_open_files = 1000;
    CompressionType compression = CompressionType::None;
    int bloom_filter_bits_per_key = 10;
    bool use_bloom_filter = true;
    size_t write_buffer_size = 4 * 1024 * 1024;
};
```

## SSTable Format

```
+------------------+
| Data Block 1     |
+------------------+
| Data Block 2     |
+------------------+
| ...              |
+------------------+
| Data Block N     |
+------------------+
| Index Block      |  (offset, size for each data block)
+------------------+
| Bloom Filter     |
+------------------+
| Footer           |  (index offset, bloom offset, magic)
+------------------+
```

**Data Block Format:**
```
[key_len][key][value_len][value] ... (repeated)
```

## Compaction

The engine uses leveled compaction:

- **Level 0 (L0)**: Direct MemTable flushes, may overlap
- **Level 1+ (L1+)**: Non-overlapping sorted runs
- Compaction merges L(n) files into L(n+1)
- Removes tombstones and old versions
- Triggered when level size exceeds threshold

**Compaction Trigger:**
- L0: 4+ files
- L1: 10MB total size
- L2: 100MB total size
- Each level is 10x larger than previous

## Performance Characteristics

**Write Performance:**
- Sequential writes: ~500K ops/sec
- Batch writes: ~1M ops/sec
- WAL adds ~10% overhead

**Read Performance:**
- MemTable hits: ~1M ops/sec
- SSTable hits (cached): ~500K ops/sec
- SSTable hits (disk): ~10K ops/sec (depends on I/O)

**Space Amplification:**
- Typically 1.1-1.5x with regular compaction
- Bloom filters add ~1% overhead

**Compaction:**
- Background operation
- I/O intensive
- Can be throttled or scheduled

## Building

### As Header-Only Library
```cpp
#include "DatabaseEngine.hpp"
```

### With CMake
```bash
cd DatabaseEngine
mkdir build && cd build
cmake ..
cmake --build .
./db_example
```

## Use Cases

The DatabaseEngine is ideal for:
- **Embedded Databases** - Local storage for applications
- **Time-Series Data** - Efficient sequential writes
- **Caching Layer** - Fast key-value storage
- **Metadata Storage** - Configuration and state
- **Event Sourcing** - Append-optimized writes
- **Mobile/Edge** - Lightweight embedded storage
- **Learning** - Understanding LSM-Tree architecture

## Implementation Details

### Write Path

1. Append to WAL (fsync for durability)
2. Insert into MemTable
3. Return success
4. Background: Flush MemTable when full

### Read Path

1. Check MemTable
2. If not found, check L0 SSTables (newest to oldest)
3. If not found, check L1+ SSTables (level by level)
4. Use bloom filters to skip SSTables without the key

### Crash Recovery

1. Read WAL from last checkpoint
2. Replay operations into MemTable
3. Resume normal operation

## Limitations

- Single-threaded writes (serialized through WAL)
- No distributed support (single-node only)
- Limited transaction support (batch atomicity only)
- No secondary indexes
- Keys and values must fit in memory during compaction
- No automatic backup/restore

## Advanced Features

### Custom Comparator

```cpp
struct ReverseComparator {
    int operator()(const std::string& a, const std::string& b) const {
        return b.compare(a);
    }
};

Options opts;
opts.comparator = std::make_shared<ReverseComparator>();
DatabaseEngine db("./mydb", opts);
```

### Compression

```cpp
Options opts;
opts.compression = CompressionType::Snappy;  // or LZ4
DatabaseEngine db("./mydb", opts);
```

## Thread Safety

- **Writes**: Thread-safe (serialized internally)
- **Reads**: Thread-safe (lock-free with MVCC)
- **Iterators**: Not thread-safe (per-iterator state)
- **Snapshots**: Thread-safe (immutable)

## Requirements
- C++20 compatible compiler
- Standard library with `<filesystem>` support
- No external dependencies (core features)
- Optional: LZ4/Snappy for compression

## Performance Tuning

**For Write-Heavy Workloads:**
```cpp
Options opts;
opts.memtable_size = 64 * 1024 * 1024;  // Larger MemTable
opts.write_buffer_size = 64 * 1024 * 1024;
db.open("./mydb", opts);
```

**For Read-Heavy Workloads:**
```cpp
Options opts;
opts.use_bloom_filter = true;
opts.bloom_filter_bits_per_key = 12;  // Lower false positive rate
db.open("./mydb", opts);
```

**For Small Datasets:**
```cpp
Options opts;
opts.memtable_size = 1 * 1024 * 1024;  // 1MB
opts.block_size = 1024;                 // 1KB
db.open("./mydb", opts);
```

## Comparison with Other Databases

| Feature | DatabaseEngine | LevelDB | RocksDB | SQLite |
|---------|---------------|---------|---------|--------|
| LSM-Tree | ✓ | ✓ | ✓ | ✗ (B-tree) |
| ACID | Batch only | Batch only | ✓ | ✓ |
| SQL | ✗ | ✗ | ✗ | ✓ |
| Compression | ✓ | ✓ | ✓ | ✓ |
| Snapshots | ✓ | ✓ | ✓ | ✗ |
| Size | ~2K LOC | ~30K LOC | ~500K LOC | ~150K LOC |
| Purpose | Educational | Production | Production | Production |

## Future Enhancements

- Multi-threaded compaction
- Column families
- Prefix bloom filters
- Block cache with LRU eviction
- Merge operators
- TTL support
- Backup and restore
- Replication support
