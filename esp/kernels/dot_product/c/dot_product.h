#ifndef DOT_PRODUCT_H
#define DOT_PRODUCT_H

#include <stdint.h>

/* Paired domain: len>0 requires readable non-NULL inputs; minmax output
 * always holds two writable int32_t. Reject forbidden inputs in the harness
 * BEFORE this kernel, outside timing. len<=0 accepts NULL inputs, no reads. */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Calcula o produto escalar entre dois vetores de int32_t.
 *
 * @param a Primeiro vetor
 * @param b Segundo vetor
 * @param len Comprimento dos vetores
 * @return Soma dos produtos a[i]*b[i], ou 0 se len <= 0 ou ponteiros nulos
 */
int32_t dot_product_c_run(const int32_t *a, const int32_t *b, int32_t len);

#ifdef __cplusplus
}
#endif

#endif /* DOT_PRODUCT_H */
