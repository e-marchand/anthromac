#include "DatabaseEngine.hpp"
#include <iostream>
#include <iomanip>
#include <chrono>
#include <random>
#include <thread>

using namespace db;

void example_basic_operations() {
    std::cout << "\n=== Example 1: Basic Put/Get/Delete ===" << std::endl;

    // Create database
    DatabaseEngine db("./test_db1");

    // Put operations
    db.put("name", "Alice");
    db.put("age", "30");
    db.put("city", "New York");

    std::cout << "Inserted 3 keys" << std::endl;

    // Get operations
    std::cout << "name: " << db.get("name") << std::endl;
    std::cout << "age: " << db.get("age") << std::endl;
    std::cout << "city: " << db.get("city") << std::endl;

    // Delete operation
    db.del("age");
    std::cout << "\nDeleted 'age'" << std::endl;

    // Try to get deleted key
    try {
        db.get("age");
    } catch (const KeyNotFoundError& e) {
        std::cout << "Expected error: " << e.what() << std::endl;
    }

    // Get with default
    std::string country = db.get("country", "Unknown");
    std::cout << "country (with default): " << country << std::endl;

    // Check existence
    std::cout << "\nKey existence checks:" << std::endl;
    std::cout << "  'name' exists: " << (db.exists("name") ? "yes" : "no") << std::endl;
    std::cout << "  'age' exists: " << (db.exists("age") ? "yes" : "no") << std::endl;
}

void example_batch_operations() {
    std::cout << "\n=== Example 2: Batch Operations ===" << std::endl;

    DatabaseEngine db("./test_db2");

    // Create batch
    WriteBatch batch;
    batch.put("user:1:name", "Alice");
    batch.put("user:1:email", "alice@example.com");
    batch.put("user:2:name", "Bob");
    batch.put("user:2:email", "bob@example.com");
    batch.put("user:3:name", "Charlie");
    batch.put("user:3:email", "charlie@example.com");

    std::cout << "Writing batch of 6 operations..." << std::endl;
    db.write(batch);

    std::cout << "Batch written successfully" << std::endl;

    // Verify
    std::cout << "\nReading back:" << std::endl;
    std::cout << "  user:1:name = " << db.get("user:1:name") << std::endl;
    std::cout << "  user:2:email = " << db.get("user:2:email") << std::endl;

    // Another batch with deletes
    WriteBatch batch2;
    batch2.del("user:3:name");
    batch2.del("user:3:email");
    batch2.put("user:3:status", "deleted");

    db.write(batch2);
    std::cout << "\nUpdated user:3 status" << std::endl;
}

void example_persistence() {
    std::cout << "\n=== Example 3: Persistence and Recovery ===" << std::endl;

    // Write data
    {
        std::cout << "Creating database and writing data..." << std::endl;
        DatabaseEngine db("./test_db3");
        db.put("persistent_key", "persistent_value");
        db.put("test_key", "test_value");
        std::cout << "Data written, closing database..." << std::endl;
    }

    // Reopen and verify
    {
        std::cout << "\nReopening database..." << std::endl;
        DatabaseEngine db("./test_db3");
        std::string value = db.get("persistent_key");
        std::cout << "Read persistent_key: " << value << std::endl;
        std::cout << "Persistence verified!" << std::endl;
    }
}

void example_memtable_flush() {
    std::cout << "\n=== Example 4: MemTable Flush ===" << std::endl;

    Options opts;
    opts.memtable_size = 100;  // Very small for testing

    DatabaseEngine db("./test_db4", opts);

    std::cout << "Writing data to trigger MemTable flush..." << std::endl;

    // Write enough data to trigger flush
    for (int i = 0; i < 10; ++i) {
        std::string key = "key_" + std::to_string(i);
        std::string value = "value_" + std::to_string(i) + "_with_some_extra_data";
        db.put(key, value);
        std::cout << "  Wrote " << key << std::endl;
    }

    auto stats = db.get_stats();
    std::cout << "\nDatabase stats:" << std::endl;
    std::cout << "  SSTable files: " << stats.num_sst_files << std::endl;
    std::cout << "  Total keys: " << stats.num_keys << std::endl;
    std::cout << "  Disk size: " << stats.total_disk_size << " bytes" << std::endl;
}

void example_compaction() {
    std::cout << "\n=== Example 5: Compaction ===" << std::endl;

    Options opts;
    opts.memtable_size = 100;
    opts.l0_compaction_threshold = 3;

    DatabaseEngine db("./test_db5", opts);

    std::cout << "Writing data to trigger compaction..." << std::endl;

    // Write enough to create multiple SSTables
    for (int round = 0; round < 5; ++round) {
        for (int i = 0; i < 5; ++i) {
            std::string key = "key_" + std::to_string(i);
            std::string value = "value_round_" + std::to_string(round);
            db.put(key, value);
        }
        std::cout << "  Round " << round << " complete" << std::endl;
    }

    auto stats_before = db.get_stats();
    std::cout << "\nBefore compaction:" << std::endl;
    std::cout << "  SSTable files: " << stats_before.num_sst_files << std::endl;

    db.compact();
    std::cout << "\nCompaction triggered" << std::endl;

    auto stats_after = db.get_stats();
    std::cout << "After compaction:" << std::endl;
    std::cout << "  SSTable files: " << stats_after.num_sst_files << std::endl;
    std::cout << "  Disk size: " << stats_after.total_disk_size << " bytes" << std::endl;

    // Verify data still accessible
    std::cout << "\nVerifying data:" << std::endl;
    std::cout << "  key_0 = " << db.get("key_0") << std::endl;
    std::cout << "  key_4 = " << db.get("key_4") << std::endl;
}

void example_range_scan() {
    std::cout << "\n=== Example 6: Range Scan (Iterator) ===" << std::endl;

    DatabaseEngine db("./test_db6");

    // Insert sorted data
    db.put("apple", "fruit");
    db.put("banana", "fruit");
    db.put("carrot", "vegetable");
    db.put("date", "fruit");
    db.put("eggplant", "vegetable");

    std::cout << "Scanning all keys:" << std::endl;
    auto it = db.new_iterator();
    for (it->seek_to_first(); it->valid(); it->next()) {
        std::cout << "  " << it->key() << " = " << it->value() << std::endl;
    }

    std::cout << "\nSeeking to 'carrot':" << std::endl;
    it->seek("carrot");
    if (it->valid()) {
        std::cout << "  Found: " << it->key() << " = " << it->value() << std::endl;
    }

    std::cout << "\nIterating from 'carrot':" << std::endl;
    for (; it->valid(); it->next()) {
        std::cout << "  " << it->key() << " = " << it->value() << std::endl;
    }
}

void example_snapshots() {
    std::cout << "\n=== Example 7: Snapshots ===" << std::endl;

    DatabaseEngine db("./test_db7");

    // Initial data
    db.put("x", "1");
    db.put("y", "2");

    std::cout << "Initial state:" << std::endl;
    std::cout << "  x = " << db.get("x") << std::endl;
    std::cout << "  y = " << db.get("y") << std::endl;

    // Create snapshot
    auto snapshot = db.create_snapshot();
    std::cout << "\nSnapshot created" << std::endl;

    // Modify data
    db.put("x", "100");
    db.put("z", "3");
    db.del("y");

    std::cout << "\nCurrent state (after modifications):" << std::endl;
    std::cout << "  x = " << db.get("x") << std::endl;
    std::cout << "  z = " << db.get("z") << std::endl;
    try {
        db.get("y");
    } catch (const KeyNotFoundError&) {
        std::cout << "  y = <deleted>" << std::endl;
    }

    std::cout << "\nNote: Snapshot reads not fully implemented in this simplified version" << std::endl;
    std::cout << "(Would require passing snapshot to get() method)" << std::endl;

    db.release_snapshot(snapshot);
}

void example_bloom_filter() {
    std::cout << "\n=== Example 8: Bloom Filter Efficiency ===" << std::endl;

    Options opts;
    opts.use_bloom_filter = true;
    opts.bloom_filter_bits_per_key = 10;
    opts.memtable_size = 50;  // Small to force SSTable creation

    DatabaseEngine db("./test_db8", opts);

    // Insert data
    std::cout << "Inserting 100 keys..." << std::endl;
    for (int i = 0; i < 100; ++i) {
        std::string key = "key_" + std::to_string(i);
        std::string value = "value_" + std::to_string(i);
        db.put(key, value);
    }

    db.flush();  // Force flush to create SSTable

    std::cout << "Keys inserted and flushed to SSTable" << std::endl;

    // Query existing keys
    auto start_exists = std::chrono::high_resolution_clock::now();
    int found = 0;
    for (int i = 0; i < 100; ++i) {
        std::string key = "key_" + std::to_string(i);
        if (db.exists(key)) {
            ++found;
        }
    }
    auto end_exists = std::chrono::high_resolution_clock::now();
    auto duration_exists = std::chrono::duration_cast<std::chrono::microseconds>(
        end_exists - start_exists);

    std::cout << "\nQuerying 100 existing keys:" << std::endl;
    std::cout << "  Found: " << found << std::endl;
    std::cout << "  Time: " << duration_exists.count() << " μs" << std::endl;

    // Query non-existing keys (bloom filter should help)
    auto start_missing = std::chrono::high_resolution_clock::now();
    int not_found = 0;
    for (int i = 1000; i < 1100; ++i) {
        std::string key = "key_" + std::to_string(i);
        if (!db.exists(key)) {
            ++not_found;
        }
    }
    auto end_missing = std::chrono::high_resolution_clock::now();
    auto duration_missing = std::chrono::duration_cast<std::chrono::microseconds>(
        end_missing - start_missing);

    std::cout << "\nQuerying 100 non-existing keys:" << std::endl;
    std::cout << "  Not found: " << not_found << std::endl;
    std::cout << "  Time: " << duration_missing.count() << " μs" << std::endl;
    std::cout << "  (Bloom filter helps avoid disk reads)" << std::endl;
}

void example_statistics() {
    std::cout << "\n=== Example 9: Database Statistics ===" << std::endl;

    DatabaseEngine db("./test_db9");

    // Insert some data
    for (int i = 0; i < 50; ++i) {
        db.put("key_" + std::to_string(i), "value_" + std::to_string(i));
    }

    auto stats = db.get_stats();

    std::cout << "Database Statistics:" << std::endl;
    std::cout << "  Number of keys: " << stats.num_keys << std::endl;
    std::cout << "  Number of SSTable files: " << stats.num_sst_files << std::endl;
    std::cout << "  MemTable size: " << stats.memtable_size << " bytes" << std::endl;
    std::cout << "  Total disk size: " << stats.total_disk_size << " bytes" << std::endl;
}

void example_error_handling() {
    std::cout << "\n=== Example 10: Error Handling ===" << std::endl;

    DatabaseEngine db("./test_db10");

    // Key not found
    std::cout << "Attempting to get non-existent key..." << std::endl;
    try {
        db.get("nonexistent");
    } catch (const KeyNotFoundError& e) {
        std::cout << "Caught KeyNotFoundError: " << e.what() << std::endl;
    }

    // Invalid database path (commented out to avoid actual error)
    std::cout << "\nOther errors (DatabaseError) would be thrown for:" << std::endl;
    std::cout << "  - Invalid database path" << std::endl;
    std::cout << "  - Corrupted SSTable files" << std::endl;
    std::cout << "  - I/O errors" << std::endl;
}

void benchmark_write_performance() {
    std::cout << "\n=== Benchmark: Write Performance ===" << std::endl;

    DatabaseEngine db("./test_benchmark_write");

    const int num_operations = 10000;

    // Sequential writes
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < num_operations; ++i) {
        std::string key = "key_" + std::to_string(i);
        std::string value = "value_" + std::to_string(i);
        db.put(key, value);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    double ops_per_sec = (num_operations * 1000.0) / duration.count();

    std::cout << "Sequential writes:" << std::endl;
    std::cout << "  Operations: " << num_operations << std::endl;
    std::cout << "  Time: " << duration.count() << " ms" << std::endl;
    std::cout << "  Throughput: " << std::fixed << std::setprecision(0)
              << ops_per_sec << " ops/sec" << std::endl;
}

void benchmark_read_performance() {
    std::cout << "\n=== Benchmark: Read Performance ===" << std::endl;

    DatabaseEngine db("./test_benchmark_read");

    const int num_keys = 5000;

    // Prepare data
    std::cout << "Preparing " << num_keys << " keys..." << std::endl;
    for (int i = 0; i < num_keys; ++i) {
        db.put("key_" + std::to_string(i), "value_" + std::to_string(i));
    }

    // Sequential reads
    auto start_seq = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < num_keys; ++i) {
        volatile auto value = db.get("key_" + std::to_string(i));
    }
    auto end_seq = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end_seq - start_seq);

    double ops_per_sec_seq = (num_keys * 1000.0) / duration_seq.count();

    std::cout << "\nSequential reads:" << std::endl;
    std::cout << "  Operations: " << num_keys << std::endl;
    std::cout << "  Time: " << duration_seq.count() << " ms" << std::endl;
    std::cout << "  Throughput: " << std::fixed << std::setprecision(0)
              << ops_per_sec_seq << " ops/sec" << std::endl;

    // Random reads
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, num_keys - 1);

    auto start_rand = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < num_keys; ++i) {
        int idx = dis(gen);
        volatile auto value = db.get("key_" + std::to_string(idx));
    }
    auto end_rand = std::chrono::high_resolution_clock::now();
    auto duration_rand = std::chrono::duration_cast<std::chrono::milliseconds>(end_rand - start_rand);

    double ops_per_sec_rand = (num_keys * 1000.0) / duration_rand.count();

    std::cout << "\nRandom reads:" << std::endl;
    std::cout << "  Operations: " << num_keys << std::endl;
    std::cout << "  Time: " << duration_rand.count() << " ms" << std::endl;
    std::cout << "  Throughput: " << std::fixed << std::setprecision(0)
              << ops_per_sec_rand << " ops/sec" << std::endl;
}

void benchmark_batch_performance() {
    std::cout << "\n=== Benchmark: Batch Write Performance ===" << std::endl;

    DatabaseEngine db("./test_benchmark_batch");

    const int num_batches = 100;
    const int batch_size = 100;

    auto start = std::chrono::high_resolution_clock::now();

    for (int b = 0; b < num_batches; ++b) {
        WriteBatch batch;
        for (int i = 0; i < batch_size; ++i) {
            int idx = b * batch_size + i;
            batch.put("key_" + std::to_string(idx), "value_" + std::to_string(idx));
        }
        db.write(batch);
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    int total_ops = num_batches * batch_size;
    double ops_per_sec = (total_ops * 1000.0) / duration.count();

    std::cout << "Batch writes:" << std::endl;
    std::cout << "  Batches: " << num_batches << " x " << batch_size << " ops" << std::endl;
    std::cout << "  Total operations: " << total_ops << std::endl;
    std::cout << "  Time: " << duration.count() << " ms" << std::endl;
    std::cout << "  Throughput: " << std::fixed << std::setprecision(0)
              << ops_per_sec << " ops/sec" << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "   DatabaseEngine - LSM-Tree Examples  " << std::endl;
    std::cout << "========================================" << std::endl;

    try {
        example_basic_operations();
        example_batch_operations();
        example_persistence();
        example_memtable_flush();
        example_compaction();
        example_range_scan();
        example_snapshots();
        example_bloom_filter();
        example_statistics();
        example_error_handling();

        std::cout << "\n========================================" << std::endl;
        std::cout << "          Performance Benchmarks        " << std::endl;
        std::cout << "========================================" << std::endl;

        benchmark_write_performance();
        benchmark_read_performance();
        benchmark_batch_performance();

        std::cout << "\n========================================" << std::endl;
        std::cout << "   All examples completed successfully  " << std::endl;
        std::cout << "========================================" << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
