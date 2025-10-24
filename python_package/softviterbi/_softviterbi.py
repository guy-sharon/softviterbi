from typing import List
from ctypes import Structure, c_uint8, c_uint32, c_size_t, c_ubyte, POINTER, byref, CDLL, c_char_p
import importlib.resources
import platform

MAX_POLYNOMES = 16

class SoftViterbi:
    
    class __SoftViterbi_Struct(Structure):
        _fields_ = [
            ("num_polys", c_uint8),
            ("polynomes", c_uint32 * MAX_POLYNOMES),
            ("has_reversed_polys", c_uint8),
            ("poly_lsb_mask", c_uint32),
            ("depth", c_uint32),
            ("depth_mask", c_uint32),
            ("num_states", c_size_t),
        ]
    
    def __init__(self, polynomes: List[int]):
        if not polynomes:
            raise ValueError("At least one polynomial is required")

        self.__lib = self.__load_library()
        self.__codec = SoftViterbi.__SoftViterbi_Struct()
        self.__codec.num_polys = len(polynomes)

        for i, poly in enumerate(polynomes):
            self.__codec.polynomes[i] = poly

    def __load_library(self):
        if platform.system().lower() == "windows":
            lib_name = "softviterbi.dll"
        else:
            lib_name = "libsoftviterbi.so"
            
        with importlib.resources.path("softviterbi", lib_name) as lib_path:
            lib = CDLL(str(lib_path))
            
        lib.encode.argtypes = [POINTER(SoftViterbi.__SoftViterbi_Struct), POINTER(c_ubyte), c_size_t]
        lib.encode.restype = c_char_p
        lib.decode.argtypes = [POINTER(SoftViterbi.__SoftViterbi_Struct), POINTER(c_ubyte), c_size_t, c_char_p]
        lib.decode.restype = c_char_p

        return lib

    def encode(self, bits: List[int]) -> List[int]:
        arr = (c_ubyte * len(bits))(*bits)
        result = self.__lib.encode(byref(self.__codec), arr, len(bits))
        return [int(b) for b in result.decode()]

    def decode(self, soft_bits: List[int], final_state: bytes | None = None) -> List[int]:
        arr = (c_ubyte * len(soft_bits))(*soft_bits)
        result = self.__lib.decode(byref(self.__codec), arr, len(soft_bits), final_state)
        return [int(b) for b in result.decode()]
