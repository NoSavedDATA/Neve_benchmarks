#ifndef IIR_H
#define IIR_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int32_t iir_c_run(const int32_t *coeffs, const int32_t *input,
                  int32_t num_samples, int32_t *output,
                  int32_t *state, int32_t scale);

#ifdef __cplusplus
}
#endif

#endif /* IIR_H */
