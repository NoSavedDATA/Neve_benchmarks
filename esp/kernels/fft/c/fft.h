#ifndef FFT_H
#define FFT_H

#include <stdint.h>

int32_t fft_c_run(float *real, float *imag,
                  const float *cos_table, const float *sin_table,
                  const int32_t *bit_rev, int32_t n, int32_t table_n);

#endif /* FFT_H */
