import os
import math
import numpy as np
import bitarray
import random

# Constants
MAX_BASE_SIZE = 256
MAX_ITER = 100
PROGMEM = "__attribute__((section(\".progmem.data\")))"

def create_freq_table(data):
    if not data:
        return {}, 1
    common_denom = data[0]
    for x in data[1:]:
        common_denom = math.gcd(common_denom, x)

    counts = {}
    for x in data:
        val = x // common_denom
        counts[val] = counts.get(val, 0) + 1

    # Sort values by frequency descending
    sorted_vals = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
    return sorted_vals, counts, common_denom

def get_bits_needed(n):
    if n <= 1:
        return 1
    return (n - 1).bit_length()

def encode_data(data, sorted_vals, common_denom, base_size):
    val_to_idx = {val: i for i, val in enumerate(sorted_vals)}
    encoded_bits = bitarray.bitarray()
    
    bits_for_mod = get_bits_needed(base_size)
    
    for x in data:
        val = x // common_denom
        idx = val_to_idx[val]
        q = idx // base_size
        r = idx % base_size

        # Unary for q: q ones followed by a zero
        encoded_bits.extend('1' * q)
        encoded_bits.append(False)

        # Binary for r: bits_for_mod bits
        r_bits = bin(r)[2:].zfill(bits_for_mod)
        encoded_bits.extend(r_bits)

    return encoded_bits

def write_header_file(filename, array_name, data, type="int", is_byte=False):
    with open(filename, "w") as f:
        guard = filename.upper().replace(".", "_")
        f.write(f"#ifndef {guard}\n")
        f.write(f"#define {guard}\n\n")
        f.write(f"const {type} {array_name}[] {PROGMEM} = {{\n")

        for i, x in enumerate(data):
            if is_byte:
                f.write(f"0x{x:02x}")
            else:
                f.write(str(x))
            if i < len(data) - 1:
                f.write(", ")
            if (i + 1) % 12 == 0:
                f.write("\n")

        f.write("\n};\n\n")
        f.write("#endif\n")

def compress_dir(dir_name):
    if not os.path.exists(dir_name):
        print(f"Directory {dir_name} not found.")
        return 0, []

    files = [f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]
    if not files:
        print("No files to compress.")
        return 0, []

    data_list = []
    file_names = []
    for file in files:
        with open(os.path.join(dir_name, file), "rb") as f:
            data = list(f.read())
            if not data: continue
            data_list.append(data)
            file_names.append(file)
    
    if not data_list:
        return 0, []

    all_data = [x for data in data_list for x in data]
    sorted_vals, counts, common_denom = create_freq_table(all_data)
    
    # Try different base sizes to find the best one
    best_ratio = -1
    best_base_size = 2
    
    total_original_size = len(all_data)
    
    for b in range(2, min(len(sorted_vals) + 1, MAX_BASE_SIZE)):
        bits_for_mod = get_bits_needed(b)
        total_bits = 0
        for val, count in counts.items():
            idx = sorted_vals.index(val)
            q = idx // b
            total_bits += count * (q + 1 + bits_for_mod)

        compressed_size = (total_bits + 7) // 8
        # Add overhead for common.h: common_denom, base_size, num_unique_vals, bits_for_mod, sorted_vals
        overhead = 4 * 2 + len(sorted_vals) * 2
        ratio = total_original_size / (compressed_size + overhead)

        if ratio > best_ratio:
            best_ratio = ratio
            best_base_size = b

    print(f"Best base size: {best_base_size}, Ratio: {best_ratio:.2f}")
    
    # Generate common.h
    bits_for_mod = get_bits_needed(best_base_size)
    common_data = [common_denom, best_base_size, len(sorted_vals), bits_for_mod] + sorted_vals
    write_header_file("common.h", "common_h", common_data)
    
    # Generate file headers
    for i, data in enumerate(data_list):
        encoded = encode_data(data, sorted_vals, common_denom, best_base_size)
        header_name = file_names[i].replace(".", "_") + "_h"
        filename = file_names[i] + ".h"
        # Combine data and metadata for the header file
        with open(filename, "w") as f:
            guard = filename.upper().replace(".", "_")
            f.write(f"#ifndef {guard}\n")
            f.write(f"#define {guard}\n\n")

            f.write(f"const unsigned char {header_name}[] {PROGMEM} = {{\n")
            bytes_data = encoded.tobytes()
            for j, x in enumerate(bytes_data):
                f.write(f"0x{x:02x}")
                if j < len(bytes_data) - 1:
                    f.write(", ")
                if (j + 1) % 12 == 0:
                    f.write("\n")
            f.write("\n};\n\n")

            f.write(f"const unsigned int {header_name}_len = {len(data)};\n")
            f.write(f"const unsigned long {header_name}_bits = {len(encoded)};\n")
            f.write("#endif\n")

    return best_ratio, []

if __name__ == "__main__":
    import sys
    dir_name = "sample_dir"
    if len(sys.argv) > 1:
        dir_name = sys.argv[1]

    # Create sample dir if it doesn't exist
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        with open(os.path.join(dir_name, "file1.txt"), "w") as f:
            f.write("Hello Hello Hello World World!")
        with open(os.path.join(dir_name, "file2.txt"), "w") as f:
            f.write("This is a test. This is only a test.")
        with open(os.path.join(dir_name, "file3.txt"), "wb") as f:
            f.write(bytes([10, 20, 10, 30, 10, 20, 40, 50] * 10))

    compress_dir(dir_name)
