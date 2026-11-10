#include "fir.h"

int32_t fir_c_run(const int32_t *coeffs, int32_t num_taps,
                  const int32_t *input, int32_t num_samples,
                  int32_t *output, int32_t *state)
{
    if (num_samples <= 0 || num_taps <= 0) {
        return 0;
    }

    for (int32_t i = 0; i < num_samples; i++) {
        int32_t acc = 0;
        for (int32_t k = 0; k < num_taps; k++) {
            int32_t sample = 0;
            if (i >= k) {
                sample = input[i - k];
            } else {
                sample = state[num_taps - 1 - (k - i)];
            }
            acc += coeffs[k] * sample;
        }
        output[i] = acc;
    }

    int32_t delay_len = num_taps - 1;
    if (num_samples >= delay_len) {
        for (int32_t j = 0; j < delay_len; j++) {
            state[j] = input[num_samples - delay_len + j];
        }
    } else {
        int32_t shift = delay_len - num_samples;
        for (int32_t j = 0; j < shift; j++) {
            state[j] = state[j + num_samples];
        }
        for (int32_t j = 0; j < num_samples; j++) {
            state[shift + j] = input[j];
        }
    }

    return 0;
}
