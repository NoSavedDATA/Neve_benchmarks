#include "iir.h"

int32_t iir_c_run(const int32_t *coeffs, const int32_t *input,
                  int32_t num_samples, int32_t *output,
                  int32_t *state, int32_t scale)
{
    if (num_samples <= 0) {
        return 0;
    }

    int32_t b0 = coeffs[0];
    int32_t b1 = coeffs[1];
    int32_t b2 = coeffs[2];
    int32_t a1 = coeffs[3];
    int32_t a2 = coeffs[4];

    int32_t x1 = state[0];
    int32_t x2 = state[1];
    int32_t y1 = state[2];
    int32_t y2 = state[3];

    for (int32_t i = 0; i < num_samples; i++) {
        int32_t x0 = input[i];
        int32_t acc = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
        int32_t y0 = 0;
        if (scale > 1) {
            y0 = acc / scale;
        } else {
            y0 = acc;
        }
        output[i] = y0;

        x2 = x1;
        x1 = x0;
        y2 = y1;
        y1 = y0;
    }

    state[0] = x1;
    state[1] = x2;
    state[2] = y1;
    state[3] = y2;

    return 0;
}
