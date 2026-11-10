#include "minmax.h"

int32_t minmax_c_run(const int32_t *arr, int32_t len, int32_t *out_minmax)
{
    if (len <= 0) {
        out_minmax[0] = 0;
        out_minmax[1] = 0;
        return -1;
    }

    int32_t min_val = arr[0];
    int32_t max_val = arr[0];

    for (int32_t i = 1; i < len; i++) {
        int32_t v = arr[i];
        if (v < min_val) {
            min_val = v;
        }
        if (v > max_val) {
            max_val = v;
        }
    }

    out_minmax[0] = min_val;
    out_minmax[1] = max_val;
    return 0;
}
