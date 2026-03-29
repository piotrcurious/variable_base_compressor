import os
import math
import bitarray
import random

# Constants
MAX_BASE_SIZE = 256
PROGMEM = "__attribute__((section(\".progmem.data\")))"

def part1d(n):
    n &= 0x0000ffff
    n = (n | (n << 8)) & 0x00ff00ff
    n = (n | (n << 4)) & 0x0f0f0f0f
    n = (n | (n << 2)) & 0x33333333
    n = (n | (n << 1)) & 0x55555555
    return n

def z_order_encode(x, y):
    return (part1d(y) << 1) | part1d(x)

def apply_z_order(data, width):
    if width <= 1: return data
    height = (len(data) + width - 1) // width
    size = 1
    while size < width or size < height:
        size <<= 1

    reordered = [None] * (size * size)
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if idx < len(data):
                z = z_order_encode(x, y)
                reordered[z] = data[idx]

    return [x for x in reordered if x is not None]

def encode_truncated_binary(n, b):
    if b <= 1: return bitarray.bitarray()
    k = b.bit_length() - 1
    u = (1 << (k + 1)) - b
    res = bitarray.bitarray()
    if n < u:
        bits = bin(n)[2:].zfill(k)
        res.extend(bits)
    else:
        bits = bin(n + u)[2:].zfill(k + 1)
        res.extend(bits)
    return res

def calculate_bits_truncated(r, b):
    if b <= 1: return 0
    k = b.bit_length() - 1
    u = (1 << (k + 1)) - b
    return k if r < u else k + 1

def encode_value(idx, base_sizes):
    res = bitarray.bitarray()
    curr_idx = idx
    for i, b in enumerate(base_sizes):
        r = curr_idx % b
        q = curr_idx // b
        if b > 1:
            res.extend(encode_truncated_binary(r, b))
        if q > 0:
            res.append(True) # more levels
            curr_idx = q - 1 # offset to allow 0 to be meaningful
        else:
            res.append(False) # end of nesting
            break
    else:
        res.extend('1' * (curr_idx))
        res.append(False)
    return res

def cost_value(idx, base_sizes):
    bits = 0
    curr_idx = idx
    for i, b in enumerate(base_sizes):
        r = curr_idx % b
        q = curr_idx // b
        if b > 1:
            bits += calculate_bits_truncated(r, b)
        bits += 1 # nesting bit
        if q > 0:
            curr_idx = q - 1
        else:
            break
    else:
        bits += curr_idx + 1 # unary fallback
    return bits

def find_best_bases(counts, sorted_vals, val_to_idx):
    best_base_sizes = [32]
    best_cost = sum(counts[v] * cost_value(val_to_idx[v], best_base_sizes) for v in sorted_vals)

    for _ in range(500):
        new_bases = list(best_base_sizes)
        # Random mutation
        rand_val = random.random()
        if rand_val < 0.2 and len(new_bases) < 4:
            new_bases.append(random.randint(2, 64))
        elif rand_val < 0.4 and len(new_bases) > 1:
            new_bases.pop()
        else:
            idx = random.randrange(len(new_bases))
            new_bases[idx] = max(1, min(256, new_bases[idx] + random.randint(-5, 5)))

        cost = sum(counts[v] * cost_value(val_to_idx[v], new_bases) for v in sorted_vals)
        if cost < best_cost:
            best_cost = cost
            best_base_sizes = new_bases

    return best_base_sizes, best_cost

def compress_dir(dir_name):
    if not os.path.exists(dir_name): return

    files = [f for f in sorted(os.listdir(dir_name)) if os.path.isfile(os.path.join(dir_name, f))]
    if not files: return

    file_data_list = []
    for file in files:
        with open(os.path.join(dir_name, file), "rb") as f:
            data = list(f.read())
            if not data: continue
            file_data_list.append({"name": file, "data": data})
    
    if not file_data_list: return

    # Heuristic for Z-order: try different widths if data looks 2D
    for fd in file_data_list:
        best_width = 0
        original_data = fd["data"]

        # Test 1D vs 2D (Z-order)
        # We try square widths around sqrt(len)
        best_local_bases = [32]
        best_local_cost = 1e18

        # Initial 1D cost
        counts = {}
        for x in original_data: counts[x] = counts.get(x, 0) + 1
        sorted_vals = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
        val_to_idx = {val: i for i, val in enumerate(sorted_vals)}
        bases, cost = find_best_bases(counts, sorted_vals, val_to_idx)
        best_local_cost = cost
        best_local_bases = bases
        best_width = 0

        sqrt_len = int(len(original_data)**0.5)
        for w in range(max(2, sqrt_len - 10), sqrt_len + 11):
            if w <= 1: continue
            z_data = apply_z_order(original_data, w)
            counts_z = {}
            for x in z_data: counts_z[x] = counts_z.get(x, 0) + 1
            sorted_vals_z = sorted(counts_z.keys(), key=lambda x: counts_z[x], reverse=True)
            val_to_idx_z = {val: i for i, val in enumerate(sorted_vals_z)}
            bases_z, cost_z = find_best_bases(counts_z, sorted_vals_z, val_to_idx_z)
            if cost_z < best_local_cost:
                best_local_cost = cost_z
                best_local_bases = bases_z
                best_width = w

        fd["width"] = best_width
        if best_width > 0:
            fd["data"] = apply_z_order(original_data, best_width)
            print(f"File {fd['name']} using Z-order width {best_width}")

    # Re-calculate overall sorted symbols for the dictionary
    all_reordered_data = [x for fd in file_data_list for x in fd["data"]]
    counts = {}
    for x in all_reordered_data: counts[x] = counts.get(x, 0) + 1
    sorted_vals = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
    val_to_idx = {val: i for i, val in enumerate(sorted_vals)}
    
    best_base_sizes, _ = find_best_bases(counts, sorted_vals, val_to_idx)
    print(f"Final Optimal Bases: {best_base_sizes}")

    # Header generation
    # format: denom, num_bases, B1, B2, ..., num_unique, 0, S1, S2, ...
    common_data = [1, len(best_base_sizes)] + best_base_sizes + [len(sorted_vals), 0] + sorted_vals
    with open("common.h", "w") as f:
        f.write("#ifndef COMMON_H\n#define COMMON_H\n#include <stdint.h>\n\n")
        f.write(f"const int16_t common_h[] {PROGMEM} = {{\n")
        for i, x in enumerate(common_data):
            f.write(str(int(x)))
            if i < len(common_data) - 1: f.write(", ")
            if (i+1) % 12 == 0: f.write("\n")
        f.write("\n};\n\n#endif\n")

    for fd in file_data_list:
        encoded = bitarray.bitarray()
        for x in fd["data"]:
            encoded.extend(encode_value(val_to_idx[x], best_base_sizes))

        header_name = fd["name"].replace(".", "_") + "_h"
        filename = fd["name"] + ".h"
        with open(filename, "w") as f:
            guard = filename.upper().replace(".", "_")
            f.write(f"#ifndef {guard}\n#define {guard}\n#include <stdint.h>\n\n")
            f.write(f"const uint8_t {header_name}[] {PROGMEM} = {{\n")
            bytes_data = encoded.tobytes()
            for j, x in enumerate(bytes_data):
                f.write(f"0x{x:02x}")
                if j < len(bytes_data) - 1: f.write(", ")
                if (j + 1) % 12 == 0: f.write("\n")
            f.write(f"\n}};\n\nconst unsigned int {header_name}_len = {len(fd['data'])};\n")
            f.write(f"const unsigned long {header_name}_bits = {len(encoded)};\n")
            f.write(f"const int {header_name}_width = {fd['width']};\n")
            f.write("#endif\n")

if __name__ == "__main__":
    import sys
    dir_name = "diverse_test_dir"
    if len(sys.argv) > 1:
        dir_name = sys.argv[1]
    compress_dir(dir_name)
