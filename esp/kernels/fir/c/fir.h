#ifndef FIR_H
#define FIR_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int32_t fir_c_run(const int32_t *coeffs, int32_t num_taps,
                  const int32_t *input, int32_t num_samples,
                  int32_t *output, int32_t *state);

#ifdef __cplusplus
}
#endif

#endif /* FIR_H */
