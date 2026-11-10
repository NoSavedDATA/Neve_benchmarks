#pragma once
typedef struct { const char *name; const char *sql; int kind; int joined; } QueryCase;
static const char *SCHEMA = "PRAGMA foreign_keys=ON; PRAGMA temp_store=MEMORY; PRAGMA cache_size=-4096; CREATE TABLE customers (id INTEGER PRIMARY KEY, region INTEGER NOT NULL, active INTEGER NOT NULL); CREATE INDEX idx_customers_region ON customers(region); CREATE TABLE items (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id), quantity INTEGER NOT NULL, price REAL NOT NULL, label TEXT NOT NULL); CREATE INDEX idx_items_customer_qty ON items(customer_id, quantity);";
static const char *PAYLOAD = "benchmark-item-payload";
static const char *UPDATED = "benchmark-updated-payload";
static const QueryCase QUERIES[] = {
    {"select_pk", "SELECT id, quantity, price, label FROM items WHERE id = ?", 0, 0},
    {"where_indexed", "SELECT id, quantity, price, label FROM items WHERE customer_id = ? AND quantity >= ? ORDER BY id", 1, 0},
    {"where_scan", "SELECT id, quantity, price, label FROM items WHERE quantity >= ? AND quantity < ? ORDER BY id", 2, 0},
    {"join_pk", "SELECT i.id, i.quantity, i.price, i.label, c.region FROM items AS i INNER JOIN customers AS c ON c.id = i.customer_id WHERE i.id = ? AND c.active = 1", 0, 1},
    {"join_indexed", "SELECT i.id, i.quantity, i.price, i.label, c.region FROM items AS i INNER JOIN customers AS c ON c.id = i.customer_id WHERE i.customer_id = ? AND c.region = ? AND i.quantity >= ? ORDER BY i.id", 3, 1},
    {"join_scan", "SELECT i.id, i.quantity, i.price, i.label, c.region FROM items AS i INNER JOIN customers AS c ON c.id = i.customer_id WHERE (i.quantity + c.region) % 10 = ? ORDER BY i.id", 4, 1},
};
