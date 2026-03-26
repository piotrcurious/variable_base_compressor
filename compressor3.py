import os
import math
import heapq
import bitarray
import numpy as np

# Constants
PROGMEM = "__attribute__((section(\".progmem.data\")))"

def build_huffman_tree(counts):
    # Use a priority queue to build the tree
    # (frequency, unique_id, [symbol, left, right])
    # Added unique_id to prevent comparison errors between nodes with same frequency
    heap = [[freq, i, [sym, None, None]] for i, (sym, freq) in enumerate(counts.items())]
    heapq.heapify(heap)

    if len(heap) == 1:
        sym, freq = next(iter(counts.items()))
        return {sym: 1}

    next_id = len(heap)
    while len(heap) > 1:
        freq1, id1, node1 = heapq.heappop(heap)
        freq2, id2, node2 = heapq.heappop(heap)
        combined_node = [None, node1, node2]
        heapq.heappush(heap, [freq1 + freq2, next_id, combined_node])
        next_id += 1

    code_lengths = {}
    def traverse(node, length):
        sym, left, right = node
        if sym is not None:
            code_lengths[sym] = length
        else:
            traverse(left, length + 1)
            traverse(right, length + 1)

    _, _, root = heap[0]
    traverse(root, 0)
    return code_lengths

def build_canonical_codes(code_lengths):
    sorted_symbols = sorted(code_lengths.keys(), key=lambda x: (code_lengths[x], x))

    canonical_codes = {}
    current_code = 0
    current_length = 0

    for sym in sorted_symbols:
        length = code_lengths[sym]
        if length > current_length:
            current_code <<= (length - current_length)
            current_length = length

        canonical_codes[sym] = (current_code, length)
        current_code += 1

    return canonical_codes

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
    counts = {}
    for x in all_data:
        counts[x] = counts.get(x, 0) + 1
    
    code_lengths = build_huffman_tree(counts)
    canonical_codes = build_canonical_codes(code_lengths)
    
    max_len = max(code_lengths.values())
    len_counts = [0] * (max_len + 1)
    for l in code_lengths.values():
        len_counts[l] += 1

    sorted_symbols = sorted(code_lengths.keys(), key=lambda x: (code_lengths[x], x))
    common_data = [len(sorted_symbols), max_len] + len_counts[1:] + sorted_symbols
    
    with open("common.h", "w") as f:
        f.write("#ifndef COMMON_H\n#define COMMON_H\n#include <stdint.h>\n\n")
        f.write(f"const int16_t common_h[] {PROGMEM} = {{\n")
        for i, x in enumerate(common_data):
            f.write(str(int(x)))
            if i < len(common_data) - 1: f.write(", ")
            if (i+1) % 12 == 0: f.write("\n")
        f.write("\n};\n\n#endif\n")

    for i, data in enumerate(data_list):
        encoded_bits = bitarray.bitarray()
        for x in data:
            code, length = canonical_codes[x]
            code_bits = bin(code)[2:].zfill(length)
            encoded_bits.extend(code_bits)

        header_name = file_names[i].replace(".", "_") + "_h"
        filename = file_names[i] + ".h"

        with open(filename, "w") as f:
            guard = filename.upper().replace(".", "_")
            f.write(f"#ifndef {guard}\n#define {guard}\n#include <stdint.h>\n\n")
            f.write(f"const uint8_t {header_name}[] {PROGMEM} = {{\n")
            bytes_data = encoded_bits.tobytes()
            for j, x in enumerate(bytes_data):
                f.write(f"0x{x:02x}")
                if j < len(bytes_data) - 1: f.write(", ")
                if (j + 1) % 12 == 0: f.write("\n")
            f.write("\n};\n\n")
            f.write(f"const unsigned int {header_name}_len = {len(data)};\n")
            f.write(f"const unsigned long {header_name}_bits = {len(encoded_bits)};\n")
            f.write("#endif\n")

    return 1.0, []

if __name__ == "__main__":
    import sys
    dir_name = "diverse_test_dir"
    if len(sys.argv) > 1:
        dir_name = sys.argv[1]
    compress_dir(dir_name)
