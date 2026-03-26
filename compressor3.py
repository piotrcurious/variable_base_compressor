import os
import math
import numpy as np
import bitarray
import random

# Constants
MAX_BASE_SIZE = 256
PROGMEM = "__attribute__((section(\".progmem.data\")))"

def create_freq_table(data):
    if not data:
        return [], {}, 1

    counts = {}
    for x in data:
        counts[x] = counts.get(x, 0) + 1

    sorted_vals = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
    return sorted_vals, counts, 1

def get_bits_needed(n):
    if n <= 1:
        return 0
    return (n - 1).bit_length()

def encode_data(data, val_to_idx, common_denom, base_size):
    encoded_bits = bitarray.bitarray()
    bits_for_mod = get_bits_needed(base_size)

    for x in data:
        val = x // common_denom
        idx = val_to_idx[val]
        q = idx // base_size
        r = idx % base_size

        # Unary for q
        encoded_bits.extend('1' * q)
        encoded_bits.append(False)

        # Binary for r
        if bits_for_mod > 0:
            for b_idx in range(bits_for_mod - 1, -1, -1):
                encoded_bits.append((r >> b_idx) & 1)

    return encoded_bits

def compress_dir(dir_name):
    if not os.path.exists(dir_name):
        return 0, []

    files = [f for f in sorted(os.listdir(dir_name)) if os.path.isfile(os.path.join(dir_name, f))]
    if not files: return 0, []

    data_list = []
    file_names = []
    for file in files:
        with open(os.path.join(dir_name, file), "rb") as f:
            data = list(f.read())
            if not data: continue
            data_list.append(data)
            file_names.append(file)
    
    if not data_list: return 0, []

    all_data = [x for data in data_list for x in data]
    sorted_vals, counts, common_denom = create_freq_table(all_data)
    val_to_idx = {val: i for i, val in enumerate(sorted_vals)}
    
    total_original_size = len(all_data)
    best_ratio = -1
    best_base_size = 1
    
    for b in range(1, min(len(sorted_vals) + 1, MAX_BASE_SIZE)):
        bits_for_mod = get_bits_needed(b)
        total_bits = 0
        for val, count in counts.items():
            idx = val_to_idx[val]
            q = idx // b
            total_bits += count * (q + 1 + bits_for_mod)

        compressed_data_size = (total_bits + 7) // 8
        overhead = 4 * 2 + len(sorted_vals) * 2 + len(data_list) * 12
        total_comp = compressed_data_size + overhead
        ratio = total_original_size / total_comp if total_comp > 0 else 0

        if ratio > best_ratio:
            best_ratio = ratio
            best_base_size = b

    print(f"Best base size: {best_base_size}, Optimal Ratio: {best_ratio:.2f}")
    
    bits_for_mod = get_bits_needed(best_base_size)
    # Using int16_t for compatibility
    common_data = [common_denom, best_base_size, len(sorted_vals), bits_for_mod] + sorted_vals
    
    with open("common.h", "w") as f:
        f.write("#ifndef COMMON_H\n#define COMMON_H\n#include <stdint.h>\n\n")
        f.write(f"const int16_t common_h[] {PROGMEM} = {{\n")
        for i, x in enumerate(common_data):
            f.write(str(int(x)))
            if i < len(common_data) - 1: f.write(", ")
            if (i+1) % 12 == 0: f.write("\n")
        f.write("\n};\n\n#endif\n")

    for i, data in enumerate(data_list):
        encoded = encode_data(data, val_to_idx, common_denom, best_base_size)
        header_name = file_names[i].replace(".", "_") + "_h"
        filename = file_names[i] + ".h"

        with open(filename, "w") as f:
            guard = filename.upper().replace(".", "_")
            f.write(f"#ifndef {guard}\n#define {guard}\n#include <stdint.h>\n\n")
            f.write(f"const uint8_t {header_name}[] {PROGMEM} = {{\n")
            bytes_data = encoded.tobytes()
            for j, x in enumerate(bytes_data):
                f.write(f"0x{x:02x}")
                if j < len(bytes_data) - 1: f.write(", ")
                if (j + 1) % 12 == 0: f.write("\n")
            f.write("\n};\n\n")
            f.write(f"const unsigned int {header_name}_len = {len(data)};\n")
            f.write(f"const unsigned long {header_name}_bits = {len(encoded)};\n")
            f.write("#endif\n")

    return best_ratio, []

if __name__ == "__main__":
    import sys
    dir_name = "diverse_test_dir"
    if len(sys.argv) > 1:
        dir_name = sys.argv[1]
    compress_dir(dir_name)
