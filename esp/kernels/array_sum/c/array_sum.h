#ifndef ARRAY_SUM_H
#define ARRAY_SUM_H

#include <stdint.h>

/* Paired domain: len>0 requires readable non-NULL inputs; minmax output
 * always holds two writable int32_t. Reject forbidden inputs in the harness
 * BEFORE this kernel, outside timing. len<=0 accepts NULL inputs, no reads. */

#ifdef __cplusplus
extern "C" {
#endif

int32_t array_sum_c_run(const int32_t *arr, int32_t len);

#ifdef __cplusplus
}
#endif

#endif /* ARRAY_SUM_H */
