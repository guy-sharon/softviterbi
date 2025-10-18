import random
from softviterbi import SoftViterbi

codec = SoftViterbi([1135, 557, 5957])

for i in range(10):
    bits = [random.randint(0, 1) for _ in range(100)]
    
    encoded = codec.encode(bits)
    decoded = codec.decode([255*b for b in encoded]) # soft bits are between 0 and 255
    
    if decoded != bits:
        print("\033[0;31msoftviterbi python package failed.\033[0m")
        exit(0)
    else:
        print(f"Test #{i} passed")

print("\033[0;32msoftviterbi python package OK.\033[0m")