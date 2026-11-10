#include "linear_search.h"

int32_t linear_search_c_run(const int32_t *arr, int32_t len, int32_t target)
{
    if (len <= 0) {
        return -1;
    }
    for (int32_t i = 0; i < len; i++) {
        if (arr[i] == target) {
            return i;
        }
    }
    return -1;
}
