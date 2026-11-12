// #include <cblas.h>
#include <openblas/cblas.h>
#include <vector>
#include <random>
#include <chrono>
#include <iostream>

int main() {
    constexpr int M = 2048;
    constexpr int N = 2048;
    constexpr int K = 2048;

    std::vector<float> A(M * K);
    std::vector<float> B(K * N);
    std::vector<float> C(M * N);

    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(0.0f, 1.0f);

    for (auto &x : A) x = dist(rng);
    for (auto &x : B) x = dist(rng);

    auto start = std::chrono::high_resolution_clock::now();

    cblas_sgemm(
        CblasRowMajor,
        CblasNoTrans,
        CblasNoTrans,
        M,      // rows of A and C
        N,      // cols of B and C
        K,      // cols of A, rows of B
        1.0f,   // alpha
        A.data(),
        K,      // lda
        B.data(),
        N,      // ldb
        0.0f,   // beta
        C.data(),
        N       // ldc
    );

    auto end = std::chrono::high_resolution_clock::now();

    double seconds =
    std::chrono::duration<double>(end - start).count();

    double gflops =
        (2.0 * N * N * N) / seconds / 1e9;

    std::cout << "Time: " << seconds*1000 << " ms\n";

    std::cout << "Flops: " << gflops << " ms\n";
}
