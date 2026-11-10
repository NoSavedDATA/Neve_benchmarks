#define _POSIX_C_SOURCE 200809L
#include <sqlite3.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include "queries.h"

static sqlite3 *db;
static void check(int actual, int expected) {
    if (actual != expected) {
        fprintf(stderr, "CHECK FAILED %d != %d: %s\n", actual, expected, sqlite3_errmsg(db));
        exit(2);
    }
}
static int64_t now_us(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (int64_t)t.tv_sec * 1000000 + t.tv_nsec / 1000;
}
static void exec_sql(const char *sql) { check(sqlite3_exec(db, sql, NULL, NULL, NULL), SQLITE_OK); }
static sqlite3_stmt *prepare(const char *sql) {
    sqlite3_stmt *s = NULL;
    check(sqlite3_prepare_v2(db, sql, -1, &s, NULL), SQLITE_OK);
    return s;
}
static void integer(sqlite3_stmt *s, int index, int value) { check(sqlite3_bind_int(s, index, value), SQLITE_OK); }
static void real(sqlite3_stmt *s, int index, float value) { check(sqlite3_bind_double(s, index, value), SQLITE_OK); }
static void text(sqlite3_stmt *s, int index, const char *value) { check(sqlite3_bind_text(s, index, value, (int)strlen(value), SQLITE_TRANSIENT), SQLITE_OK); }
static int scalar(const char *sql) {
    sqlite3_stmt *s = prepare(sql);
    check(sqlite3_step(s), SQLITE_ROW);
    int value = sqlite3_column_int(s, 0);
    check(sqlite3_step(s), SQLITE_DONE);
    check(sqlite3_finalize(s), SQLITE_OK);
    return value;
}
static void query_parameters(sqlite3_stmt *s, int kind, int i, int n) {
    if (kind == 0) integer(s, 1, i % n);
    if (kind == 1) { integer(s, 1, i % 100); integer(s, 2, 25); }
    if (kind == 2) { int low = i % 10 * 5; integer(s, 1, low); integer(s, 2, low + 5); }
    if (kind == 3) { integer(s, 1, i % 100); integer(s, 2, i % 10); integer(s, 3, 25); }
    if (kind == 4) integer(s, 1, i % 10);
}
static int64_t run_query(const QueryCase *query, int n, int repetitions) {
    int count = 0, ids = 0, quantities = 0;
    int64_t start = now_us();
    sqlite3_stmt *s = prepare(query->sql);
    for (int i = 0; i < repetitions; ++i) {
        query_parameters(s, query->kind, i, n);
        int rc;
        while ((rc = sqlite3_step(s)) == SQLITE_ROW) {
            int id = sqlite3_column_int(s, 0), quantity = sqlite3_column_int(s, 1);
            float price = (float)sqlite3_column_double(s, 2);
            const unsigned char *raw = sqlite3_column_text(s, 3);
            int length = sqlite3_column_bytes(s, 3);
            char *label = malloc((size_t)length + 1);
            if (!label) exit(3);
            memcpy(label, raw, (size_t)length);
            label[length] = '\0';
            if (price != 42.5f || strcmp(label, PAYLOAD) != 0) exit(4);
            free(label);
            if (query->joined) check(sqlite3_column_int(s, 4), id % 10);
            ++count; ids += id; quantities += quantity;
        }
        check(rc, SQLITE_DONE);
        check(sqlite3_reset(s), SQLITE_OK);
    }
    check(sqlite3_finalize(s), SQLITE_OK);
    int64_t elapsed = now_us() - start;
    printf("CHECK %s_rows %d\nCHECK %s_ids %d\nCHECK %s_quantity %d\n", query->name, count, query->name, ids, query->name, quantities);
    return elapsed;
}
int main(void) {
    int n = getenv("BENCH_N") ? atoi(getenv("BENCH_N")) : 1000;
    int repetitions = getenv("BENCH_QUERIES") ? atoi(getenv("BENCH_QUERIES")) : 1000;
    const char *path = getenv("BENCH_DATABASE");
    if (!path) path = ":memory:";
    check(sqlite3_open(path, &db), SQLITE_OK);
    sqlite3_busy_timeout(db, 5000);
    exec_sql(strcmp(path, ":memory:") == 0 ? "PRAGMA journal_mode=MEMORY; PRAGMA synchronous=OFF;" : "PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;");
    exec_sql(SCHEMA);
    exec_sql("BEGIN");
    sqlite3_stmt *s = prepare("INSERT INTO customers VALUES (?, ?, ?)");
    for (int i = 0; i < 100; ++i) {
        integer(s, 1, i); integer(s, 2, i % 10); integer(s, 3, i % 2 == 0);
        check(sqlite3_step(s), SQLITE_DONE); check(sqlite3_reset(s), SQLITE_OK);
    }
    check(sqlite3_finalize(s), SQLITE_OK); exec_sql("COMMIT");

    int64_t start = now_us();
    exec_sql("BEGIN");
    s = prepare("INSERT INTO items (id, customer_id, quantity, price, label) VALUES (?, ?, ?, ?, ?)");
    for (int i = 0; i < n; ++i) {
        integer(s, 1, i); integer(s, 2, i % 100); integer(s, 3, i % 50);
        real(s, 4, 42.5f); text(s, 5, PAYLOAD);
        check(sqlite3_step(s), SQLITE_DONE); check(sqlite3_changes(db), 1); check(sqlite3_reset(s), SQLITE_OK);
    }
    check(sqlite3_finalize(s), SQLITE_OK); exec_sql("COMMIT");
    int64_t insert_us = now_us() - start;
    int insert_count = scalar("SELECT COUNT(*) FROM items"), insert_quantity = scalar("SELECT SUM(quantity) FROM items");
    int64_t query_times[sizeof(QUERIES) / sizeof(QUERIES[0])];
    for (size_t q = 0; q < sizeof(QUERIES) / sizeof(QUERIES[0]); ++q) query_times[q] = run_query(&QUERIES[q], n, repetitions);

    start = now_us(); exec_sql("BEGIN");
    s = prepare("UPDATE items SET quantity = ?, price = ?, label = ? WHERE id = ?");
    for (int i = 0; i < n; ++i) {
        integer(s, 1, i % 50 + 1); real(s, 2, 99.5f); text(s, 3, UPDATED); integer(s, 4, i);
        check(sqlite3_step(s), SQLITE_DONE); check(sqlite3_changes(db), 1); check(sqlite3_reset(s), SQLITE_OK);
    }
    check(sqlite3_finalize(s), SQLITE_OK); exec_sql("COMMIT");
    int64_t update_us = now_us() - start;
    int update_quantity = scalar("SELECT SUM(quantity) FROM items");
    int update_exact = scalar("SELECT COUNT(*) FROM items WHERE quantity = (id % 50) + 1 AND price = 99.5 AND label = 'benchmark-updated-payload'");

    start = now_us(); exec_sql("BEGIN");
    s = prepare("DELETE FROM items WHERE id = ?");
    for (int i = 0; i < n; ++i) {
        integer(s, 1, i); check(sqlite3_step(s), SQLITE_DONE); check(sqlite3_changes(db), 1); check(sqlite3_reset(s), SQLITE_OK);
    }
    check(sqlite3_finalize(s), SQLITE_OK); exec_sql("COMMIT");
    int64_t delete_us = now_us() - start;
    int delete_count = scalar("SELECT COUNT(*) FROM items");
    check(sqlite3_close(db), SQLITE_OK);
    int64_t work_us = insert_us + update_us + delete_us;
    printf("METRIC insert_us %lld\nMETRIC update_us %lld\nMETRIC delete_us %lld\n", (long long)insert_us, (long long)update_us, (long long)delete_us);
    for (size_t q = 0; q < sizeof(QUERIES) / sizeof(QUERIES[0]); ++q) {
        work_us += query_times[q]; printf("METRIC %s_us %lld\n", QUERIES[q].name, (long long)query_times[q]);
    }
    printf("METRIC work_us %lld\n", (long long)work_us);
    printf("CHECK insert_count %d\nCHECK insert_quantity %d\nCHECK update_quantity %d\nCHECK update_exact %d\nCHECK delete_count %d\n", insert_count, insert_quantity, update_quantity, update_exact, delete_count);
    return 0;
}
