import os
import math
import bitarray
import random

# Constants
MAX_BASE_SIZE = 256
PROGMEM = "__attribute__((section(\".progmem.data\")))"
CHECKPOINT_INTERVAL = 128
BLOCK_SIZE = 64

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
        if b > 1: res.extend(encode_truncated_binary(r, b))
        if q > 0:
            res.append(True)
            curr_idx = q - 1
        else:
            res.append(False)
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
        if b > 1: bits += calculate_bits_truncated(r, b)
        bits += 1
        if q > 0: curr_idx = q - 1
        else: break
    else: bits += curr_idx + 1
    return bits

def find_best_bases(counts, sorted_vals, val_to_idx, trials=1000):
    best_base_sizes = [32]
    best_cost = sum(counts.get(v, 0) * cost_value(val_to_idx[v], best_base_sizes) for v in sorted_vals)
    temp = 1.0
    for _ in range(trials):
        new_bases = list(best_base_sizes)
        rv = random.random()
        if rv < 0.2 and len(new_bases) < 5: new_bases.append(random.randint(2, 64))
        elif rv < 0.4 and len(new_bases) > 1: new_bases.pop()
        else:
            idx = random.randrange(len(new_bases))
            new_bases[idx] = max(1, min(256, new_bases[idx] + random.randint(-16, 16)))
        cost = sum(counts.get(v, 0) * cost_value(val_to_idx[v], new_bases) for v in sorted_vals)
        if cost < best_cost or random.random() < math.exp((best_cost - cost) / (temp + 1e-9)):
            best_cost = cost
            best_base_sizes = new_bases
        temp *= 0.99
    return best_base_sizes, best_cost

def fold_residual(r):
    # 0->0, -1->1, 1->2, -2->3, 2->4 ...
    if r > 127: r -= 256
    if r < -128: r += 256
    if r >= 0: return r * 2
    else: return abs(r) * 2 - 1

def compress_dir(dir_name):
    if not os.path.exists(dir_name): return
    files = [f for f in sorted(os.listdir(dir_name)) if os.path.isfile(os.path.join(dir_name, f))]
    if not files: return

    file_info = []
    for file in files:
        with open(os.path.join(dir_name, file), "rb") as f:
            data = list(f.read())
            if not data: continue
            file_info.append({"name": file, "data": data})

    for f in file_info:
        f["data_processed"] = f["data"]

    all_processed = []
    for f in file_info:
        d = f["data_processed"]
        for i in range(len(d)):
            if i % CHECKPOINT_INTERVAL == 0:
                prev_val = 0
            else:
                prev_val = d[i-1]
            all_processed.append(d[i])
            all_processed.append(fold_residual(d[i] - prev_val))
            all_processed.append(d[i] ^ prev_val)

    counts = {}
    for x in all_processed: counts[x] = counts.get(x, 0) + 1
    sorted_vals = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
    val_to_idx = {val: i for i, val in enumerate(sorted_vals)}

    # Context-Adaptive Profiles (4 bins)
    p = [find_best_bases(counts, sorted_vals, val_to_idx, trials=2000)[0] for _ in range(4)]

    common_data = [1, 4] + [len(x) for x in p]
    for x in p: common_data.extend(x)
    common_data.extend([len(sorted_vals), (len(sorted_vals)-1).bit_length() if len(sorted_vals)>1 else 1] + sorted_vals)
    with open("common.h", "w") as f_out:
        f_out.write("#ifndef COMMON_H\n#define COMMON_H\n#include <stdint.h>\nconst int16_t common_h[] "+PROGMEM+" = {\n")
        for i, x in enumerate(common_data):
            f_out.write(str(int(x)) + (", " if i < len(common_data)-1 else ""))
            if (i+1)%12==0: f_out.write("\n")
        f_out.write("\n};\n#endif\n")

    for f in file_info:
        data = f["data_processed"]
        final_bits = bitarray.bitarray()
        checkpoints = []
        cur_bl_count = 0
        prev_val = 0

        # Dummy pattern space for compatibility
        final_bits.extend('0000')

        for i in range(len(data)):
            if i % CHECKPOINT_INTERVAL == 0:
                checkpoints.append((len(final_bits), prev_val, cur_bl_count))
                prev_val = 0
                cur_bl_count = 0

            if cur_bl_count == 0:
                block = data[i:i+BLOCK_SIZE]
                best_bl = None
                for mode in [0, 1, 2, 3]: # 0:Raw, 1:Delta, 2:RLE, 3:XOR
                    bits = bitarray.bitarray()
                    if mode == 0: bits.extend('0')
                    elif mode == 1: bits.extend('10')
                    elif mode == 2: bits.extend('110')
                    else: bits.extend('111')

                    if mode == 2:
                        if all(x == block[0] for x in block):
                            ctx = 0 if prev_val < 8 else (1 if prev_val < 32 else (2 if prev_val < 128 else 3))
                            bits.extend(encode_value(val_to_idx[block[0]], p[ctx]))
                        else: continue
                    else:
                        t_p = prev_val
                        for x in block:
                            ctx = 0 if t_p < 8 else (1 if t_p < 32 else (2 if t_p < 128 else 3))
                            v = x if mode == 0 else (fold_residual(x - t_p) if mode == 1 else (x ^ t_p))
                            bits.extend(encode_value(val_to_idx[v], p[ctx]))
                            t_p = x
                    if best_bl is None or len(bits) < len(best_bl): best_bl = bits
                final_bits.extend(best_bl)
                cur_bl_count = len(block)
            prev_val = data[i]
            cur_bl_count -= 1

        header_name = f["name"].replace(".", "_") + "_h"
        with open(f["name"]+".h", "w") as f_out:
            guard = f["name"].upper().replace(".", "_")
            f_out.write(f"#ifndef {guard}\n#define {guard}\n#include <stdint.h>\nconst uint8_t {header_name}[] "+PROGMEM+" = {\n")
            bytes_data = final_bits.tobytes()
            for j, x in enumerate(bytes_data):
                f_out.write(f"0x{x:02x}" + (", " if j < len(bytes_data)-1 else ""))
                if (j+1)%12==0: f_out.write("\n")
            f_out.write(f"\n}};\nconst uint16_t {header_name}_cp[] "+PROGMEM+" = {\n")
            for j, cp in enumerate(checkpoints):
                f_out.write(f"{cp[0] & 0xFFFF}, {(cp[0] >> 16) & 0xFFFF}, {(cp[1] << 8) | cp[2]}")
                if j < len(checkpoints) - 1: f_out.write(", ")
                if (j + 1) % 4 == 0: f_out.write("\n")
            f_out.write(f"\n}};\nconst unsigned int {header_name}_len = {len(data)};\n")
            f_out.write(f"const unsigned long {header_name}_bits = {len(final_bits)};\n")
            f_out.write(f"const int {header_name}_width = 0;\n")
            f_out.write(f"const int {header_name}_cp_count = {len(checkpoints)};\n#endif\n")

if __name__ == "__main__":
    import sys
    dir_name = "benchmark_data"
    if len(sys.argv) > 1: dir_name = sys.argv[1]
    compress_dir(dir_name)
