import platform

try:
    import numpy as np # type: ignore
    from numpy.random import randint as randi # type: ignore
    from viterbi import Viterbi # type: ignore
    from tqdm import tqdm # type: ignore
except ImportError as e:
    print("\n\033[1;35mMissing dependencies. Please run:\033[0m")
    print("    \033[1mpython3 -m venv tests/venv && ", end="")
    if platform.system().lower() == "windows":
        print("tests\\venv\\Scripts\\activate && ", end="")
    else:
        print("source tests/venv/bin/activate && ", end="")
    print("pip install -r tests/requirements.txt\n\033[0m")
    print("\033[1;35mand then try again\033[0m\n")
    exit(1)

import os
import subprocess
from copy import deepcopy

np.random.seed(1)

polys = np.array([
    7,11,19,37,55,61,67,103,109,131,137,143,157,191,203,213,229,247,285,299,351,355,357,
    361,451,487,529,557,601,623,631,731,787,817,865,875,901,911,995,1001,1033,1051,1135,
    1293,1305,1315,1329,1509,1531,1555,1663,1869,1891,2041,2053,2091,2093,2147,2189,2341,
    2419,2431,2579,2963,3085,3227,3515,3851,4179,4621,4879,5957,6005,6231,6699,6865,6881,
    7057,7079,7207,7515,8123,8219,8895,9123,9905,10063,10643,12287,12409,12769,13077,13661,
    14375,14803,14889,16707,17475,18139,18499,19045,21489,23531,24217,24683,26047,26743,26927,
    31939,32353,32771,32785,32897,32975,33827,33841,33847,34473,34601,35015,36875,36925,39381,
    65533,66525,69643,69765,79555,80075,80967,83211,94317,95361,99439,101303,101615,101959,102231,
    131081,131087,131105,131137,131353,131545,132973,135247,135743,135901,149679,174761,174807,
    196619,262207,262273,262311,262407,262897,263031,263127,263329,263457,263679,263689,270417,
    294949,295429,524327,524351,524359,524399,524413,524463,524705,524735,524767,525089,525167,
    525215,527357,527807,599187,1048585,1049129,1050957,1066865,1197213,1572889,2097157,2097565,
    2098269,2105381,2113669,2113741,2117853,2131517,3932221,4194307,4194851,4223119,4326023,4338055,
    5570647,8388641,8388659,8391905,8392753,8423097,8462441,8521761,8522547,8726821,10485921,16777351,
    19916339,22367153,33554441,33554447,33557341,33558553,33561049,33686543,33822841,34603049,
    34670639,44565161,67108935,67759085,69581689,72952759,73473339,82636645,86206675,134217767,
    134483513,138422393,138600515,141996193,151589263,153692793,178269167,180176281,268435465,268446249,
    268894777,269124685,272632857,286331161,536870917,536875141,537149517,537460813,537921541,
    537987357,538968101,545261117,553672989,603979813,1082130439,1091659911,1093972699,1133332827,
    1271469507,2147483657,2147483663,2147492105,2147549469,2148565049,2148794537,2149584911,2160115865,
    2181578895,2290649225,2290650863,4299161607,4302746963,4303570409,4374732215,4559351687,4564274787])

#np.random.seed(1)

exe = os.path.join(os.getcwd(), "softviterbi")

def gen_bits(n, depth):
    bits_arr = randi(0,2,n)
    bits_arr[-depth:] = 0
    return bits_arr

def build():
    cmd = "make"
    subprocess.run(cmd, shell=True)

def run(argv):
    cmd = f"{exe} {' '.join(argv)}"
    ret = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return ret.stdout.strip()

def hexify(n):
    return hex(n)[2:].zfill(2)

def _cmd(cmd, polynomes, bits_arr):
    polys = [bin(p)[2:] for p in polynomes]
    bits = "".join(map(hexify, bits_arr))
    return [f"-{cmd}"] + polys + [bits]

def baseline_encdec(polynomes, bits_arr):
    depth = max(map(binlen, polynomes))
    baseline_viterbi = Viterbi(depth, deepcopy(polynomes))
    enc = baseline_viterbi.encode(bits_arr)
    dec = baseline_viterbi.decode(enc)
    return enc, dec

def enccmd(polynomes, bits_arr):
    return _cmd("enc", polynomes, bits_arr)

def deccmd(polynomes, bits_arr):
    return _cmd("dec", polynomes, bits_arr)

def encdec(polynomes, bits_arr):
    enc = run(enccmd(polynomes, bits_arr))
    dec = run(deccmd(polynomes, [255 if q=='1' else 0 for q in enc]))
    return list(map(int,enc)), list(map(int,dec))

def binlen(x):
    return len(bin(x))-2

def build_state_order(depth):
    num_states = 1 << depth
    states = []
    for i in range(num_states):
        prev_state0 = i >> 1
        prev_state1 = (i >> 1) | (1 << (depth - 1))
        states.append(prev_state0)
        states.append(prev_state1)
    
    q = 3

def flip_bits(n, depth):
    res = 0
    for i in range(depth):
        if n & (1 << i):
            res |= 1 << (depth - 1 - i)
    return res

def get_random_polys(depth, max_depth, num_polys=2):
    filtered_polys = deepcopy(polys)
    if depth is not None:
        filtered_polys = polys[np.bitwise_and(((1<<(depth-1))<polys),((1<<(depth))>polys))]
    else:
        filtered_polys = polys[polys<(1<<(max_depth-1))]
    assert len(filtered_polys) >= num_polys
    return np.random.choice(np.unique(filtered_polys), num_polys, replace=False)

def gen_dataset(depth, max_depth, n, num_polys):
    polynomes = get_random_polys(depth=depth, max_depth=max_depth, num_polys=randi(2,4) if num_polys is None else num_polys)
    depth = max(map(binlen, polynomes))
    bits_arr = gen_bits(n, depth)
    return polynomes, bits_arr, depth

def decode_cmd(n, depth=None, max_depth=None, num_polys=None):
    polynomes, bits_arr, depth = gen_dataset(depth=depth, max_depth=max_depth, n=n, num_polys=num_polys)
    baseline_viterbi = Viterbi(depth, deepcopy(polynomes))
    enc = baseline_viterbi.encode(bits_arr)
    expected = baseline_viterbi.decode(enc)
    return cmd_pipeline("decode", polynomes, (255*np.array(enc)).astype(np.uint8), "".join(map(str, expected)))

def encode_cmd(n, depth=None, max_depth=None, num_polys=None):
    assert n > max_depth
    polynomes, bits_arr, depth = gen_dataset(depth=depth, max_depth=max_depth, n=n, num_polys=num_polys)
    baseline_viterbi = Viterbi(depth, deepcopy(polynomes))
    expected = baseline_viterbi.encode(bits_arr)
    return cmd_pipeline("encode", polynomes, bits_arr, "".join(map(str, expected)))

def baseline_encdec_str(polynomes, bits_arr):
    enc, dec = baseline_encdec(polynomes, bits_arr)
    return "".join(map(str, enc)), "".join(map(str, dec))

def cmd_pipeline(funcname, polynomes, bits_arr, expected):
    depth = max(map(binlen, polynomes))
    polys = ",".join([str(p) for p in polynomes])
    final_state = "NULL"
    if funcname == "decode" and randi(0,2) == 1:
        final_state = f'"{expected[-depth:]}"'
    c_cmd = f"""
    TEST_{funcname.upper()}(WRAP({{{polys}}}), {len(polynomes)}, \\
        WRAP({{{",".join([str(b) for b in bits_arr])}}}), \\
        "{expected}", {final_state});"""
    py_cmd = f"""
        {funcname}({list(map(int,polynomes))}, [{",".join([str(b) for b in bits_arr])}], '{expected}')"""
    return c_cmd, py_cmd.strip()
        
def build_unittest_c():
    c_encodes, c_decodes, py_encodes, py_decodes = "", "", "", ""
    c_decodes_14, py_decodes_14 = "", ""
    c_decodes_18, c_decodes_19, py_decodes_18, py_decodes_19 = "", "", "", ""
    c_decodes_20, c_decodes_21, py_decodes_20, py_decodes_21 = "", "", "", ""
    c_encode_decodes, py_encode_decodes = "", ""
    c_decodes_24, py_decodes_24 = "", ""
    
    for _ in tqdm(range(10), desc="generating encode_decode pairs"):
        polynomes, bits_arr, _ = gen_dataset(max_depth=16, n=randi(50, 350), num_polys=None, depth=None)
        c_cmd, py_cmd = cmd_pipeline("encode_decode", polynomes, bits_arr, "")
        c_encode_decodes = c_encode_decodes + c_cmd + "\n"
        py_encode_decodes = py_encode_decodes + py_cmd + "\n"
    
    for _ in tqdm(range(10), desc="generating long tests"):
        c_cmd, py_cmd = encode_cmd(max_depth=16, n=randi(50, 350))
        c_encodes = c_encodes + c_cmd + "\n"
        py_encodes = py_encodes + py_cmd + "\n"
        c_cmd, py_cmd = decode_cmd(max_depth=16, n=randi(50, 350))
        c_decodes = c_decodes + c_cmd + "\n"
        py_decodes = py_decodes + py_cmd + "\n"
        
    for _ in tqdm(range(10), desc="generating short tests"):
        c_cmd, py_cmd = encode_cmd(max_depth=6, n=10)
        c_encodes = c_encodes + c_cmd + "\n"
        py_encodes = py_encodes + py_cmd + "\n"
        c_cmd, py_cmd = decode_cmd(max_depth=6, n=10)
        c_decodes = c_decodes + c_cmd + "\n"
        py_decodes = py_decodes + py_cmd + "\n"
    
    for _ in tqdm(range(3), desc="generating tests with depth=14"):
        c_cmd, py_cmd = decode_cmd(depth=14, n=500, num_polys=3)
        c_decodes_14 = c_decodes_14 + c_cmd + "\n"
        py_decodes_14 = py_decodes_14 + py_cmd + "\n"
         
    for _ in tqdm(range(5), desc="generating tests with depth=18 and 19"):
        c_cmd, py_cmd = decode_cmd(depth=18, n=350, num_polys=2)
        c_decodes_18 = c_decodes_18 + c_cmd + "\n"
        py_decodes_18 = py_decodes_18 + py_cmd + "\n"
        c_cmd, py_cmd = encode_cmd(max_depth=6, n=10)
        c_decodes_19 = c_decodes_19 + c_cmd + "\n"
        py_decodes_19 = py_decodes_19 + py_cmd + "\n"
        
    for _ in tqdm(range(20), desc="generating tests with depth=20 and 21"):
        c_cmd, py_cmd = decode_cmd(depth=20, n=350, num_polys=2) 
        c_decodes_20 = c_decodes_20 + c_cmd + "\n"
        py_decodes_20 = py_decodes_20 + py_cmd + "\n"
        c_cmd, py_cmd = decode_cmd(depth=21, n=350, num_polys=2)
        c_decodes_21 = c_decodes_21 + c_cmd + "\n"
        py_decodes_21 = py_decodes_21 + py_cmd + "\n"
    
    for _ in tqdm(range(1), desc="generating tests with depth=24"):
        c_cmd, py_cmd = decode_cmd(depth=24, n=350, num_polys=2)
        c_decodes_24 = c_decodes_24 + c_cmd + "\n"
        py_decodes_24 = py_decodes_24 + py_cmd + "\n"
        
    c = f"""
#ifndef __UNITTEST_C__
#define __UNITTEST_C__

#include <stdio.h>
#include <stdbool.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>
#include "time.h"
#include "../main.h"

extern unsigned int depth_mask;
extern unsigned int p_last_bits;

extern SoftViterbi_t codec;

static int test_num = 0;
static int agg_runtime_cnt = 0;
static double agg_runtime = 0;

#define WRAP(...) __VA_ARGS__ 

#define PRINT_AVG_RUNTIME() \\
    if (agg_runtime_cnt > 0) {{ \\
        printf("\\tAverage runtime: %.2fs\\n", agg_runtime/agg_runtime_cnt); \\
        agg_runtime = 0; \\
        agg_runtime_cnt = 0; \\
    }}
    
#define TEST_ENCODE(__polynomes, __num_polys, __bits, __expected, ...) \\
    TEST(encode(&codec, bits, sizeof(bits)/sizeof(bits[0])), WRAP(__polynomes), __num_polys, WRAP(__bits), __expected)

#define TEST_DECODE(__polynomes, __num_polys, __bits, __expected, __final_state) \\
    TEST(decode(&codec, bits, sizeof(bits)/sizeof(bits[0]), __final_state), WRAP(__polynomes), __num_polys, WRAP(__bits), __expected)

#define TEST_ENCODE_DECODE(__polynomes, __num_polys, __bits, ...) \\
    {{ \\
    clock_t start = clock(); \\
    /* setup codec */\\
    SoftViterbi_t codec = {{0}}; \\
    codec.num_polys = __num_polys; \\
    unsigned int _polynomes[] = __polynomes; \\
    for (int i = 0; i < codec.num_polys; i++) codec.polynomes[i] = _polynomes[i]; \\
    \\
    /* input bits */\\
    unsigned char input_bits[] = __bits; \\
    char *input_bits_str = calloc(1, 1+sizeof(input_bits)/sizeof(input_bits[0])); \\
    for (int i = 0; i < sizeof(input_bits)/sizeof(input_bits[0]); i++) input_bits_str[i] = (input_bits[i] == 1) ? '1' : '0'; \\
    \\
    /* encode */\\
    char *encoded_str = encode(&codec, input_bits, sizeof(input_bits)/sizeof(input_bits[0])); \\
    unsigned char *encoded_bits = malloc(strlen(encoded_str)); \\
    for (int i = 0; i < strlen(encoded_str); i++) encoded_bits[i] = (encoded_str[i] == '1') ? 255 : 0; \\
    \\
    /* decode */\\
    char *decoded_str = decode(&codec, encoded_bits, strlen(encoded_str), NULL); \\
    double cpu_time_used = ((double) (clock() - start)) / CLOCKS_PER_SEC; \\
    CHECK_RESULT(decoded_str, input_bits_str, cpu_time_used); \\
    \\
    }}
           
#define CHECK_RESULT(res, __expected, cpu_time_used) \\
        agg_runtime += cpu_time_used; \\
        agg_runtime_cnt++; \\
        test_num++; \\
        if (res && strcmp(res, __expected) == 0) {{ \\
            printf("\\t\\033[0;32mTest #%d passed (%.2fs)\\033[0m\\n", test_num, cpu_time_used); \\
        }} \\
        else {{ \\
            if (res) {{ \\
                printf("\\t\\033[0;31mTest #%d failed (%.2fs):\\n\\t\\tgot\\t\\t%s\\n\\t\\texpected\\t%s\\n\\033[0m", test_num, cpu_time_used, res, __expected); \\
            }} else {{ \\
                printf("\\t\\033[0;31mTest #%d failed (%.2fs):\\n\\t\\tgot\\t\\t%s\\n\\t\\texpected\\t%s\\n\\033[0m", test_num, cpu_time_used, "NULL", __expected); \\
            }} \\
            return 1; \\
        }}
            
#define TEST(__functional, __polynomes, __num_polys, __bits, __expected) \\
    {{ \\
        unsigned int _polynomes[] = __polynomes; \\
        SoftViterbi_t codec = {{0}}; \\
        codec.num_polys = __num_polys; \\
        for (int i = 0; i < codec.num_polys; i++) codec.polynomes[i] = _polynomes[i]; \\
        \\
        unsigned char bits[] = __bits; \\
        clock_t start = clock(); \\
        char *res = __functional; \\
        double cpu_time_used = ((double) (clock() - start)) / CLOCKS_PER_SEC; \\
        CHECK_RESULT(res, __expected, cpu_time_used); \\
        if (res) free(res); \\
    }}

int unittest()
{{  
    // test encoder
    printf("\\nTesting encoder...\\n");
    {c_encodes}
    PRINT_AVG_RUNTIME();
    
    // test decoder
    printf("\\nTesting decoder...\\n");
    {c_decodes}
    PRINT_AVG_RUNTIME();

    // test encode + decode
    printf("\\nTesting encode + decode...\\n");
    {c_encode_decodes}
    PRINT_AVG_RUNTIME();
    
#ifdef VALGRIND

    // test decoder (depth=14)
    printf("\\nTesting decoder (depth=14)...\\n");
    {c_decodes_14}
    PRINT_AVG_RUNTIME();
    
#else
    
    // test decoder (depth=18)
    printf("\\nTesting decoder (depth=18)...\\n");
    {c_decodes_18}
    PRINT_AVG_RUNTIME();

    // test decoder (depth=19)
    printf("\\nTesting decoder (depth=19)...\\n");
    {c_decodes_19}
    PRINT_AVG_RUNTIME();
    
    // test decoder (depth=20)
    printf("\\nTesting decoder (depth=20)...\\n");
    {c_decodes_20}
    PRINT_AVG_RUNTIME();
    
    // test decoder (depth=21)
    printf("\\nTesting decoder (depth=21)...\\n");
    {c_decodes_21}
    PRINT_AVG_RUNTIME();
    
    // test decoder (depth=24)
    printf("\\nTesting decoder (depth=24)...\\n");
    {c_decodes_24}
    PRINT_AVG_RUNTIME();

#endif

    return 0; // all passed
}}

#endif // __UNITTEST_C__
    """
    
    py = f"""#!tests/venv/bin/python3

from softviterbi import SoftViterbi # type: ignore
import time

test_num = 0
agg_runtime_cnt = 0
agg_runtime = 0
t = 0

def tic():
    global t
    t = time.time()

def toc():
    global t
    return time.time() - t

def add_runtime(cpu_time_used):
    global agg_runtime, agg_runtime_cnt
    agg_runtime += cpu_time_used
    agg_runtime_cnt += 1
    
def PRINT_AVG_RUNTIME():
    global agg_runtime, agg_runtime_cnt
    if agg_runtime_cnt > 0:
        print(f"\\tAverage runtime: {{agg_runtime/agg_runtime_cnt:.2}}");
        agg_runtime = 0
        agg_runtime_cnt = 0

def check_results(res, expected):
    global test_num
    cpu_time_used = toc()
    if res == expected:
        print(f"\\t\\033[0;32mTest #{{test_num}} passed ({{cpu_time_used:.2}})\\033[0m");
    else:
        print("\\t\\033[0;31mTest #{{test_num}} failed ({{cpu_time_used:.2}}):\\n\\t\\tgot\\t\\t{{res}}\\n\\t\\texpected\\t{{expected}}\\033[0m");
  
    test_num += 1
    add_runtime(cpu_time_used)

def encode(polynomes, bits, expected):
    tic()
    codec = SoftViterbi(polynomes)
    encoded = codec.encode(bits)
    check_results(encoded, list(map(int,expected)))

def decode(polynomes, bits, expected):
    tic()
    codec = SoftViterbi(polynomes)
    encoded = codec.decode(bits)
    check_results(encoded, list(map(int,expected)))

def encode_decode(polynomes, bits, *_):
    tic()
    codec = SoftViterbi(polynomes)
    encoded = codec.encode(bits)
    decoded = codec.decode([255*b for b in encoded]) 
    check_results(decoded, bits)
    
# test encoder
print("\\nTesting encoder...")
{py_encodes}
PRINT_AVG_RUNTIME();

# test decoder
print("\\nTesting decoder...")
{py_decodes}
PRINT_AVG_RUNTIME();

# test encode + decode
print("\\nTesting encode + decode...")
{py_encode_decodes}
PRINT_AVG_RUNTIME()

# test decoder (depth=14)
print("\\nTesting decoder (depth=14)...")
{py_decodes_14}
PRINT_AVG_RUNTIME()

# test decoder (depth=18)
print("\\nTesting decoder (depth=18)...")
{py_decodes_18}
PRINT_AVG_RUNTIME()

# test decoder (depth=19)
print("\\nTesting decoder (depth=19)...")
{py_decodes_19}
PRINT_AVG_RUNTIME()

# test decoder (depth=20)
print("\\nTesting decoder (depth=20)...")
{py_decodes_20}
PRINT_AVG_RUNTIME()

# test decoder (depth=21)
print("\\nTesting decoder (depth=21)...")
{py_decodes_21}
PRINT_AVG_RUNTIME()

# test decoder (depth=24)
print("\\nTesting decoder (depth=24)...")
{py_decodes_24}
PRINT_AVG_RUNTIME()

"""
    
    with open("tests/unittest.c", "w") as f:
        f.write(c)
        
    with open("tests/unittest.py", "w") as f:
        f.write(py)
        
if __name__ == "__main__":
    build()
    build_unittest_c()