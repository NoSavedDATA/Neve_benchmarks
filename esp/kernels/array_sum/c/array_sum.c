#include "array_sum.h"

int32_t array_sum_c_run(const int32_t *arr, int32_t len)
{
    if (len <= 0) {
        return 0;
    }
    int32_t acc = 0;
    for (int32_t i = 0; i < len; i++) {
        acc += arr[i];
    }
    return acc;
}
