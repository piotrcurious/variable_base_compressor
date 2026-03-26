import os
import math
import bitarray

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

def encode_truncated_binary(n, b):
    # Truncated Binary Encoding for 0 <= n < b
    # x is the number of bits for the smaller part
    # If b is a power of 2, it reduces to standard binary encoding
    k = b.bit_length() - 1
    u = (1 << (k + 1)) - b

    res = bitarray.bitarray()
    if n < u:
        # First u elements: k bits
        bits = bin(n)[2:].zfill(k)
        res.extend(bits)
    else:
        # Remaining b-u elements: k+1 bits
        # Offset n by u
        bits = bin(n + u)[2:].zfill(k + 1)
        res.extend(bits)
    return res

def encode_data(data, val_to_idx, common_denom, base_size):
    encoded_bits = bitarray.bitarray()

    for x in data:
        val = x // common_denom
        idx = val_to_idx[val]
        q = idx // base_size
        r = idx % base_size

        # Unary for q: q ones followed by a zero
        encoded_bits.extend('1' * q)
        encoded_bits.append(False)

        # Truncated Binary for r
        if base_size > 1:
            encoded_bits.extend(encode_truncated_binary(r, base_size))

    return encoded_bits

def calculate_bits_truncated(r, b):
    k = b.bit_length() - 1
    u = (1 << (k + 1)) - b
    return k if r < u else k + 1

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
        total_bits = 0
        for val, count in counts.items():
            idx = val_to_idx[val]
            q = idx // b
            r = idx % b

            # Bits for unary q
            total_bits += count * (q + 1)
            # Bits for truncated binary r
            if b > 1:
                total_bits += count * calculate_bits_truncated(r, b)

        compressed_data_size = (total_bits + 7) // 8
        # Memory overhead in flash (common.h data)
        overhead = 4 * 2 + len(sorted_vals) * 2
        total_comp = compressed_data_size + overhead
        ratio = total_original_size / total_comp if total_comp > 0 else 0

        if ratio > best_ratio:
            best_ratio = ratio
            best_base_size = b

    print(f"Best base size: {best_base_size}, Optimal Ratio: {best_ratio:.2f}")

    # Final encoding
    common_data = [common_denom, best_base_size, len(sorted_vals), 0] + sorted_vals
    
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
