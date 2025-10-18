#ifndef __MAIN_C__
#define __MAIN_C__

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "limits.h"
#include "immintrin.h"
#include "main.h"

#ifdef UNITTEST
#include "tests/unittest.c"
#endif

// ************************************************** //
// ********************* config ********************* //
// ************************************************** //
#define MAX_METRIC                                  ( UINT32_MAX >> 1 )


// *************************************************** //
// ********************* defines ********************* //
// *************************************************** //
#define MAX(a,b)            ( a > b ? a : b )
#define MIN(a,b)            ( a < b ? a : b )

// ************************************************ //
// ********************* Misc ********************* //
// ************************************************ //
static uint32_t reverse(uint32_t n, uint32_t num_bits)
{
    uint32_t output = 0;
    while (num_bits-- > 0) {
        output = (output << 1) + (n & 1);
        n >>= 1;
    }
    return output;
}

static void reverse_polynomes(SoftViterbi_t *pCodec)
{
    if (pCodec->has_reversed_polys) return;
    pCodec->has_reversed_polys = true;
    for (int i = 0; i < pCodec->num_polys; i++) {
        pCodec->polynomes[i] = reverse(pCodec->polynomes[i], pCodec->depth);
    }
}

static void calc_depth(SoftViterbi_t *pCodec)
{
    pCodec->depth = 0;
    for (int i = 0; i < pCodec->num_polys; i++) {
        if (pCodec->polynomes[i] == 0)
        {
            fprintf(stderr, "Polynomes can't be zeros\n");
            exit(1);
        }
        pCodec->depth = MAX(pCodec->depth, 
                    8*sizeof(pCodec->polynomes[0]) - __builtin_clz(pCodec->polynomes[i]));
    }
    pCodec->depth_mask = (1U << pCodec->depth) - 1;
}

static void calc_poly_lsb_mask(SoftViterbi_t *pCodec)
{
    pCodec->poly_lsb_mask = 0;
    for (int i = 0; i < pCodec->num_polys; i++) {
        if (pCodec->polynomes[i]&1) {
            pCodec->poly_lsb_mask |= 1 << i;
        } 
    }
}

static void init_codec(SoftViterbi_t *pCodec)
{
    calc_depth(pCodec);
    reverse_polynomes(pCodec);
    calc_poly_lsb_mask(pCodec);

    pCodec->num_states = 1 << (pCodec->depth-1);
}

static void parse_polynomes(SoftViterbi_t *pCodec, char **poly_strs, int num_polys)
{
    pCodec->num_polys = num_polys;
    if (num_polys > MAX_POLYNOMES) {
        fprintf(stderr, "Error: Too many polynomes (max %d)\n",
                         MAX_POLYNOMES);
        return;
    }
    for (int i = 0; i < num_polys; i++) {
        pCodec->polynomes[i] = 0;
        size_t poly_len = strlen(poly_strs[i]);
        for (int j = 0; j < poly_len; j++) {
            pCodec->polynomes[i] = (pCodec->polynomes[i] << 1) | (poly_strs[i][j] == '1' ? 1 : 0);
        }
    }
}

static bit_t *parse_soft_bits(size_t len, char *hex)
{
    if (strlen(hex) != 2*len) {
        fprintf(stderr, "Invalid input bits\n");
        exit(1);
    }

    bit_t *bits = malloc(len * sizeof(*bits));
    for (int i = 0; i < len; i++) {
        char byte_str[3] = {hex[2 * i], hex[2 * i + 1], '\0'};
        bits[i] = strtol(byte_str, NULL, 16);
    }
    return bits;
}

// ************************************************** //
// ********************* Encode ********************* //
// ************************************************** //
static encbits_t encode_bit(SoftViterbi_t *pCodec, bit_t bit, state_t state)
{
    encbits_t res = 0;
    state = state << 1 | bit;
    for (int j = 0; j < pCodec->num_polys; j++) {
        res |= __builtin_parity(state & pCodec->polynomes[j]) << j;
    }
    return res;
}

char* encode(SoftViterbi_t *pCodec, unsigned char *bits, size_t len) {
    init_codec(pCodec);

    state_t state = 0;
    char *res = calloc((len*pCodec->num_polys + 1), sizeof(*res));
    for (int i = 0; i < len; i++) {
        encbits_t encbit = encode_bit(pCodec, bits[i], state);
        state = ( (state << 1) | bits[i] ) & pCodec->depth_mask;
        for (int j = 0; j < pCodec->num_polys; j++) {
            res[i*pCodec->num_polys + j] = encbit & (1<<j) ? '1' : '0';
        }
    }
    return res;
}


// ************************************************** //
// ********************* Decode ********************* //
// ************************************************** //
#define SWAP(pA, pB) \
    { \
        void *tmp = (pA); \
        (pA) = (pB); \
        (pB) = tmp; \
    }

static void compute_hamming_dists(SoftViterbi_t *pCodec, bit_t *soft_bits, metric_t *ham_dists) {
    bit_t branch0[MAX_POLYNOMES], branch1[MAX_POLYNOMES];
    for (int i=0; i < pCodec->num_polys; i++) {
        branch0[i] = soft_bits[i];
        branch1[i] = 255 - branch0[i];
    }

    for (int i = 0; i < (1 << pCodec->num_polys); i++) {
        int dist = 0;
        for (int j = 0; j < pCodec->num_polys; j++) {
            dist += (i & (1 << j)) ? branch1[j] : branch0[j];
        }
        ham_dists[i] = dist;
    }
}

static state_t find_best_state(metric_t *metrics, size_t len) {
    int state = 0;
    metric_t min_metric = MAX_METRIC;
    for (int i = 0; i < len; i++) {
        if (metrics[i] < min_metric) {
            min_metric = metrics[i];
            state = i;
        }
    }
    return state;
}

static void init_metrics(SoftViterbi_t *pCodec, metric_t *metrics) {
    for (state_t state = 0; state < pCodec->num_states; state++) {
        metrics[state] = MAX_METRIC;
    }
    metrics[0] = 0;
}

static void init_encode_table(SoftViterbi_t *pCodec, encbits_t *encode_table) {
    for (state_t state = 0; state < pCodec->num_states; state++) {
        encode_table[state] = encode_bit(pCodec, 0, state);
    }
}

char *decode(SoftViterbi_t *pCodec, bit_t *soft_bits, size_t len, char *final_state) {
    init_codec(pCodec);
    size_t out_len = len / pCodec->num_polys;

    encbits_t *encode_table = malloc((pCodec->num_states) * sizeof(encbits_t));
    metric_t *ham_dists = malloc((1 << pCodec->num_polys) * sizeof(metric_t));
    metric_t *new_metrics = malloc((pCodec->num_states) * sizeof(metric_t));
    metric_t *metrics = malloc((pCodec->num_states) * sizeof(metric_t));
    decisions_t *decisions = malloc((pCodec->num_states * out_len + DNBITS - 1) / DNBITS
         * sizeof(decisions_t));
    
    if (!encode_table || !ham_dists || !new_metrics || !metrics || !decisions) {
        fprintf(stderr, "Memory allocation failed\n");
        return NULL;
    }    

    init_metrics(pCodec, metrics);
    init_encode_table(pCodec, encode_table);

    decisions_t curr_trellis = 0, trellis_bit = 1;
    for (int i = 0; i < out_len; i++) {
        compute_hamming_dists(pCodec, soft_bits, ham_dists);
    
        for (state_t state = 0; state < pCodec->num_states; state += 2) {
            state_t prev_state0 = state >> 1 | (0 << (pCodec->depth-2));
            state_t prev_state1 = prev_state0 | (1 << (pCodec->depth-2));
            
            encbits_t enc0 = encode_table[prev_state0];
            encbits_t enc1 = encode_table[prev_state1];

            metric_t m0 = metrics[prev_state0] + ham_dists[enc0];
            metric_t m2 = metrics[prev_state0] + ham_dists[enc0^pCodec->poly_lsb_mask];
            metric_t m1 = metrics[prev_state1] + ham_dists[enc1];
            metric_t m3 = metrics[prev_state1] + ham_dists[enc1^pCodec->poly_lsb_mask];
            
            new_metrics[state]   = MIN(m0, m1);
            new_metrics[state+1] = MIN(m2, m3);

            curr_trellis |= (m0 > m1) * trellis_bit;
            trellis_bit <<= 1;
            curr_trellis |= (m2 > m3) * trellis_bit;
            trellis_bit <<= 1;

            if (trellis_bit == 0) {
                decisions[(i*pCodec->num_states+state)/DNBITS] = curr_trellis;
                curr_trellis = 0;
                trellis_bit = 1;
            }
        }      
        SWAP(metrics, new_metrics);
        soft_bits += pCodec->num_polys;
    }  
    if (curr_trellis) {
        decisions[((out_len-1)*pCodec->num_states)/DNBITS] = curr_trellis;
    }
        
    // traceback
    state_t state = final_state ? strtoul(final_state, NULL, 2)&pCodec->depth_mask : 
                                  find_best_state(metrics, pCodec->num_states);
    
    char *res = calloc(out_len + 1, sizeof(*res));    
    for (int i = out_len-1; i >= 0; i--) {
        long long ind = i*pCodec->num_states+state;
        bit_t d = decisions[ind/DNBITS] & (1<<(ind%DNBITS)) ? 1 : 0;
        res[i] = state & 1 ? '1' : '0';
        state = (state >> 1) | (d << (pCodec->depth-2));
    }

    // free memory
    if (metrics) free(metrics);
    if (new_metrics) free(new_metrics);
    if (ham_dists) free(ham_dists);
    if (decisions) free(decisions);
    if (encode_table) free(encode_table);
    
    return res;
}

// ************************************************ //
// ********************* Main ********************* //
// ************************************************ //
#ifndef ASLIB

static void print_help() {
    printf("Usage: softviterbi [options]\n");
    printf("Options:\n");
    printf("  -h, --help    Show this help message\n");
}

int main(int argc, char *argv[]) {  
    if ( argc < 3 ) {
#ifdef UNITTEST
        return unittest();
#else
        print_help();
#endif
        return 0;
    }
    
    char *final_state = NULL;
    int ind = 2;
    
    if ( strcmp(argv[ind], "--final-state") == 0 ) {
        final_state = argv[ind+1];
        ind += 2;
    }
    
    // initialize codec
    SoftViterbi_t codec = {0};

    // parse polynomes
    int num_polys = argc - ind - 1;
    char **poly_strs = &argv[ind];
    parse_polynomes(&codec, poly_strs, num_polys);
    
    // parse soft bits
    char *hex = argv[argc-1];
    size_t len = strlen(hex)/2;
    bit_t *bits = parse_soft_bits(len, hex);
    
    char *res = NULL;
    if ( strcmp(argv[1], "-enc") == 0 ) {
        res = encode(&codec, bits, len);
    }
    else if ( strcmp(argv[1], "-dec") == 0 ) {
        res = decode(&codec, bits, len, final_state);
    }
    else if ( strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0 ) {
        print_help();
    }
    else {
        fprintf(stderr, "Unknown option: %s\n", argv[1]);
        print_help();
    }

    if (bits) {
        free(bits);
    }

    if (res) {
        puts(res);
        free(res);
    }

    return 0;
}

#endif // ASLIB

#endif // __MAIN_C__