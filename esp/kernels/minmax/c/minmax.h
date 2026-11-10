#ifndef MINMAX_H
#define MINMAX_H

#include <stdint.h>

/* Paired domain: len>0 requires readable non-NULL inputs; minmax output
 * always holds two writable int32_t. Reject forbidden inputs in the harness
 * BEFORE this kernel, outside timing. len<=0 accepts NULL inputs, no reads. */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Executa a busca sequencial por mínimo e máximo em um buffer de int32_t.
 *
 * @param arr Buffer de entrada
 * @param len Quantidade de elementos
 * @param out_minmax Buffer de saída de pelo menos 2 inteiros (out[0]=min, out[1]=max)
 * @return 0 em caso de sucesso, -1 se len <= 0 ou ponteiros nulos
 */
int32_t minmax_c_run(const int32_t *arr, int32_t len, int32_t *out_minmax);

#ifdef __cplusplus
}
#endif

#endif /* MINMAX_H */
