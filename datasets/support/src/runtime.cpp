#include "include.h"
#include <ctime>
#include <cstdlib>
#include <cstdio>

namespace { thread_local timespec started; }

extern "C" int batch_rows(Scope_Struct *ctx) {
    const char *value = std::getenv("BENCH_N");
    return value ? std::atoi(value) : 1000;
}
extern "C" int batch_queries(Scope_Struct *ctx) {
    const char *value = std::getenv("BENCH_QUERIES");
    return value ? std::atoi(value) : 1000;
}
extern "C" int batch_start(Scope_Struct *ctx) {
    return clock_gettime(CLOCK_MONOTONIC, &started);
}
extern "C" int batch_elapsed_us(Scope_Struct *ctx) {
    timespec ended;
    clock_gettime(CLOCK_MONOTONIC, &ended);
    return static_cast<int>(((ended.tv_sec - started.tv_sec) * 1000000000LL + ended.tv_nsec - started.tv_nsec) / 1000);
}
extern "C" int batch_check(Scope_Struct *ctx, int actual, int expected) {
    if (actual != expected) {
        std::fprintf(stderr, "CHECK FAILED: actual=%d expected=%d\n", actual, expected);
        std::exit(2);
    }
    return actual;
}
extern "C" char *batch_path_C(Scope_Struct *ctx) {
    const char *path = std::getenv("BENCH_DATABASE");
    return CopyString(ctx, const_cast<char *>(path ? path : ":memory:"));
}
