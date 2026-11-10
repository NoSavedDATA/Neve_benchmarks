#include "fft.h"

int32_t fft_c_run(float *real, float *imag,
                  const float *cos_table, const float *sin_table,
                  const int32_t *bit_rev, int32_t n, int32_t table_n)
{
    if (n <= 0) {
        return 0;
    }

    /* 1. Permutação bit-reversal */
    for (int32_t i = 0; i < n; i++) {
        int32_t j = bit_rev[i];
        if (i < j) {
            float tr = real[i];
            real[i] = real[j];
            real[j] = tr;

            float ti = imag[i];
            imag[i] = imag[j];
            imag[j] = ti;
        }
    }

    /* 2. Estágios de borboleta Cooley-Tukey */
    int32_t len_half = 1;
    while (len_half < n) {
        int32_t step = table_n / (2 * len_half);
        int32_t m = 2 * len_half;
        for (int32_t k = 0; k < n; k += m) {
            for (int32_t j = 0; j < len_half; j++) {
                int32_t u = k + j;
                int32_t v = u + len_half;
                float wr = cos_table[j * step];
                float wi = sin_table[j * step];

                float tr = wr * real[v] - wi * imag[v];
                float ti = wr * imag[v] + wi * real[v];

                real[v] = real[u] - tr;
                imag[v] = imag[u] - ti;

                real[u] = real[u] + tr;
                imag[u] = imag[u] + ti;
            }
        }
        len_half = len_half * 2;
    }

    return 0;
}
