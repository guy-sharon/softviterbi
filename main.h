#ifndef __MAIN_H__
#define __MAIN_H__

#include "stdint.h"
#include <stdbool.h>

#define MAX_POLYNOMES                               16


// **************************************************** //
// ********************* typedefs ********************* //
// **************************************************** //
typedef uint32_t encbits_t;
typedef uint32_t decisions_t;
typedef uint32_t metric_t;
typedef uint32_t state_t;
typedef uint8_t bit_t;

#define DNBITS               (sizeof(decisions_t)*8) 

typedef struct {
    uint8_t num_polys;
    uint32_t polynomes[MAX_POLYNOMES];
    uint8_t has_reversed_polys;
    uint32_t poly_lsb_mask;
    uint32_t depth;
    uint32_t depth_mask;
    size_t num_states;
} SoftViterbi_t;

#ifdef __cplusplus
extern "C" {
#endif

char *decode(SoftViterbi_t *pCodec, bit_t *soft_bits, size_t len, char *final_state);
char *encode(SoftViterbi_t *pCodec, bit_t *bits, size_t len);

#ifdef __cplusplus
}
#endif

#endif // __MAIN_H__