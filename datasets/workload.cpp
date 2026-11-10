#include <sqlite3.h>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include "queries.h"

class Database {
public:
    sqlite3 *handle = nullptr;
    explicit Database(const char *path) {
        check(sqlite3_open(path, &handle), SQLITE_OK);
        sqlite3_busy_timeout(handle, 5000);
    }
    Database(const Database &) = delete;
    Database &operator=(const Database &) = delete;
    ~Database() { if (handle) sqlite3_close(handle); }
    void check(int actual, int expected) const {
        if (actual != expected) throw std::runtime_error("SQLite " + std::to_string(actual) + ": " + (handle ? sqlite3_errmsg(handle) : "no handle"));
    }
    void exec(const char *sql) { check(sqlite3_exec(handle, sql, nullptr, nullptr, nullptr), SQLITE_OK); }
    void changed_one() const { check(sqlite3_changes(handle), 1); }
    void close() { check(sqlite3_close(handle), SQLITE_OK); handle = nullptr; }
};

class Statement {
    Database &db;
public:
    sqlite3_stmt *handle = nullptr;
    Statement(Database &owner, const char *sql) : db(owner) { db.check(sqlite3_prepare_v2(db.handle, sql, -1, &handle, nullptr), SQLITE_OK); }
    Statement(const Statement &) = delete;
    Statement &operator=(const Statement &) = delete;
    ~Statement() { if (handle) sqlite3_finalize(handle); }
    void integer(int index, int value) { db.check(sqlite3_bind_int(handle, index, value), SQLITE_OK); }
    void real(int index, float value) { db.check(sqlite3_bind_double(handle, index, value), SQLITE_OK); }
    void text(int index, const std::string &value) { db.check(sqlite3_bind_text(handle, index, value.data(), static_cast<int>(value.size()), SQLITE_TRANSIENT), SQLITE_OK); }
    int step() { return sqlite3_step(handle); }
    void expect_step(int expected) { db.check(step(), expected); }
    void reset() { db.check(sqlite3_reset(handle), SQLITE_OK); }
    int integer_at(int column) const { return sqlite3_column_int(handle, column); }
    float real_at(int column) const { return static_cast<float>(sqlite3_column_double(handle, column)); }
    std::string text_at(int column) const {
        const auto *raw = sqlite3_column_text(handle, column);
        return std::string(reinterpret_cast<const char *>(raw), sqlite3_column_bytes(handle, column));
    }
    void finish() { int rc = sqlite3_finalize(handle); handle = nullptr; db.check(rc, SQLITE_OK); }
};

static long long now_us() {
    return std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
}
static int scalar(Database &db, const char *sql) {
    Statement statement(db, sql);
    statement.expect_step(SQLITE_ROW);
    int result = statement.integer_at(0);
    statement.expect_step(SQLITE_DONE);
    statement.finish();
    return result;
}
static void parameters(Statement &statement, int kind, int i, int n) {
    if (kind == 0) statement.integer(1, i % n);
    if (kind == 1) { statement.integer(1, i % 100); statement.integer(2, 25); }
    if (kind == 2) { int low = i % 10 * 5; statement.integer(1, low); statement.integer(2, low + 5); }
    if (kind == 3) { statement.integer(1, i % 100); statement.integer(2, i % 10); statement.integer(3, 25); }
    if (kind == 4) statement.integer(1, i % 10);
}
static long long run_query(Database &db, const QueryCase &query, int n, int repetitions) {
    int rows = 0, ids = 0, quantities = 0;
    auto start = now_us();
    Statement statement(db, query.sql);
    for (int i = 0; i < repetitions; ++i) {
        parameters(statement, query.kind, i, n);
        int rc;
        while ((rc = statement.step()) == SQLITE_ROW) {
            int id = statement.integer_at(0), quantity = statement.integer_at(1);
            float price = statement.real_at(2);
            std::string label = statement.text_at(3);
            if (price != 42.5f || label != PAYLOAD) throw std::runtime_error("REAL/TEXT mismatch");
            if (query.joined) db.check(statement.integer_at(4), id % 10);
            ++rows; ids += id; quantities += quantity;
        }
        db.check(rc, SQLITE_DONE);
        statement.reset();
    }
    statement.finish();
    auto elapsed = now_us() - start;
    std::cout << "CHECK " << query.name << "_rows " << rows << '\n'
              << "CHECK " << query.name << "_ids " << ids << '\n'
              << "CHECK " << query.name << "_quantity " << quantities << '\n';
    return elapsed;
}
int main() {
    try {
        int n = std::getenv("BENCH_N") ? std::atoi(std::getenv("BENCH_N")) : 1000;
        int repetitions = std::getenv("BENCH_QUERIES") ? std::atoi(std::getenv("BENCH_QUERIES")) : 1000;
        const char *path = std::getenv("BENCH_DATABASE");
        if (!path) path = ":memory:";
        Database db(path);
        db.exec(std::string(path) == ":memory:" ? "PRAGMA journal_mode=MEMORY; PRAGMA synchronous=OFF;" : "PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;");
        db.exec(SCHEMA);
        db.exec("BEGIN");
        Statement parent(db, "INSERT INTO customers VALUES (?, ?, ?)");
        for (int i = 0; i < 100; ++i) {
            parent.integer(1, i); parent.integer(2, i % 10); parent.integer(3, i % 2 == 0);
            parent.expect_step(SQLITE_DONE); parent.reset();
        }
        parent.finish(); db.exec("COMMIT");
        const std::string payload(PAYLOAD), updated(UPDATED);

        auto start = now_us(); db.exec("BEGIN");
        Statement insert(db, "INSERT INTO items (id, customer_id, quantity, price, label) VALUES (?, ?, ?, ?, ?)");
        for (int i = 0; i < n; ++i) {
            insert.integer(1, i); insert.integer(2, i % 100); insert.integer(3, i % 50);
            insert.real(4, 42.5f); insert.text(5, payload);
            insert.expect_step(SQLITE_DONE); db.changed_one(); insert.reset();
        }
        insert.finish(); db.exec("COMMIT");
        auto insert_us = now_us() - start;
        int insert_count = scalar(db, "SELECT COUNT(*) FROM items"), insert_quantity = scalar(db, "SELECT SUM(quantity) FROM items");
        std::vector<long long> query_times;
        for (const auto &query : QUERIES) query_times.push_back(run_query(db, query, n, repetitions));

        start = now_us(); db.exec("BEGIN");
        Statement update(db, "UPDATE items SET quantity = ?, price = ?, label = ? WHERE id = ?");
        for (int i = 0; i < n; ++i) {
            update.integer(1, i % 50 + 1); update.real(2, 99.5f); update.text(3, updated); update.integer(4, i);
            update.expect_step(SQLITE_DONE); db.changed_one(); update.reset();
        }
        update.finish(); db.exec("COMMIT");
        auto update_us = now_us() - start;
        int update_quantity = scalar(db, "SELECT SUM(quantity) FROM items");
        int update_exact = scalar(db, "SELECT COUNT(*) FROM items WHERE quantity = (id % 50) + 1 AND price = 99.5 AND label = 'benchmark-updated-payload'");

        start = now_us(); db.exec("BEGIN");
        Statement remove(db, "DELETE FROM items WHERE id = ?");
        for (int i = 0; i < n; ++i) {
            remove.integer(1, i); remove.expect_step(SQLITE_DONE); db.changed_one(); remove.reset();
        }
        remove.finish(); db.exec("COMMIT");
        auto delete_us = now_us() - start;
        int delete_count = scalar(db, "SELECT COUNT(*) FROM items");
        db.close();
        auto work_us = insert_us + update_us + delete_us;
        std::cout << "METRIC insert_us " << insert_us << '\n' << "METRIC update_us " << update_us << '\n' << "METRIC delete_us " << delete_us << '\n';
        for (size_t q = 0; q < query_times.size(); ++q) {
            work_us += query_times[q]; std::cout << "METRIC " << QUERIES[q].name << "_us " << query_times[q] << '\n';
        }
        std::cout << "METRIC work_us " << work_us << '\n';
        std::cout << "CHECK insert_count " << insert_count << '\n' << "CHECK insert_quantity " << insert_quantity << '\n'
                  << "CHECK update_quantity " << update_quantity << '\n' << "CHECK update_exact " << update_exact << '\n'
                  << "CHECK delete_count " << delete_count << '\n';
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "FAILED: " << error.what() << '\n';
        return 2;
    }
}
