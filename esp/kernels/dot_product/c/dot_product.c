#include "dot_product.h"

int32_t dot_product_c_run(const int32_t *a, const int32_t *b, int32_t len)
{
    if (len <= 0) {
        return 0;
    }
    int32_t acc = 0;
    for (int32_t i = 0; i < len; i++) {
        acc += a[i] * b[i];
    }
    return acc;
}
