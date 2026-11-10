#ifndef LINEAR_SEARCH_H
#define LINEAR_SEARCH_H

#include <stdint.h>

/* Paired domain: len>0 requires readable non-NULL inputs; minmax output
 * always holds two writable int32_t. Reject forbidden inputs in the harness
 * BEFORE this kernel, outside timing. len<=0 accepts NULL inputs, no reads. */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Busca linear da primeira ocorrência de target no buffer arr.
 *
 * @param arr Ponteiro para o buffer de inteiros
 * @param len Quantidade de elementos
 * @param target Valor procurado
 * @return Índice 0 <= idx < len da primeira ocorrência, ou -1 se não encontrado / len <= 0 / arr nulo
 */
int32_t linear_search_c_run(const int32_t *arr, int32_t len, int32_t target);

#ifdef __cplusplus
}
#endif

#endif /* LINEAR_SEARCH_H */
