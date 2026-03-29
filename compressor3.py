import os
import math
import bitarray
import random

# Constants
MAX_BASE_SIZE = 256
PROGMEM = "__attribute__((section(\".progmem.data\")))"
CHECKPOINT_INTERVAL = 128
BLOCK_SIZE = 64
HISTORY_SIZE = 4 # Reduced history for lower RAM

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

def apply_z_order(data, width):
    if width <= 1: return data
    height = (len(data) + width - 1) // width
    size = 1
    while size < width or size < height: size <<= 1
    reordered = [None] * (size * size)
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if idx < len(data):
                z = 0
                for i in range(16):
                    if x & (1 << i): z |= (1 << (2*i))
                    if y & (1 << i): z |= (1 << (2*i+1))
                reordered[z] = data[idx]
    return [x for x in reordered if x is not None]

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
        data = f["data"]
        sqrt_len = int(len(data)**0.5)
        best_width, best_reordered = 0, data
        # Search for best width (spatial locality)
        for w in range(max(2, sqrt_len - 10), sqrt_len + 11):
            if w <= 1: continue
            z_data = apply_z_order(data, w)
            if sum(abs(z_data[i] - z_data[i-1]) for i in range(1, len(z_data))) < sum(abs(best_reordered[i] - best_reordered[i-1]) for i in range(1, len(best_reordered))):
                best_width, best_reordered = w, z_data
        f["data_processed"] = best_reordered
        f["width"] = best_width

    all_filtered = []
    for f in file_info:
        d = f["data_processed"]
        all_filtered.extend(d)
        for i in range(1, len(d)):
            all_filtered.append((d[i] - d[i-1]) % 256)
            all_filtered.append(d[i] ^ d[i-1])

    counts = {}
    for x in all_filtered: counts[x] = counts.get(x, 0) + 1
    sorted_vals = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
    val_to_idx = {val: i for i, val in enumerate(sorted_vals)}
    num_unique = len(sorted_vals)
    bit_width = (num_unique - 1).bit_length() if num_unique > 1 else 1
    p = [find_best_bases(counts, sorted_vals, val_to_idx, trials=2500)[0] for _ in range(4)]

    common_data = [1, 4] + [len(x) for x in p]
    for x in p: common_data.extend(x)
    common_data.extend([num_unique, bit_width] + sorted_vals)
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
        history = [0, 0] # limited for prediction

        for i in range(len(data)):
            if i % CHECKPOINT_INTERVAL == 0:
                checkpoints.append((len(final_bits), history[0], cur_bl_count))
                force_reset = True
            else: force_reset = False

            if cur_bl_count == 0:
                block = data[i:i+BLOCK_SIZE]
                best_bl = None
                # Modes: 0:Raw, 1:Sub, 2:RLE, 3:XOR, 4:2ndOrder, 5:BitPacked
                for mode in [0, 1, 2, 3, 4, 5]:
                    if mode in [1, 3, 4] and force_reset: continue
                    for prof_idx in range(4):
                        bases = p[prof_idx]
                        bits = bitarray.bitarray()
                        # Mode Header: 0:Raw, 10:Sub, 110:RLE, 1110:XOR, 11110:2ndOrder, 11111:BitPacked
                        if mode == 0: bits.extend('0')
                        elif mode == 1: bits.extend('10')
                        elif mode == 2: bits.extend('110')
                        elif mode == 3: bits.extend('1110')
                        elif mode == 4: bits.extend('11110')
                        else: bits.extend('11111')
                        bits.extend(bin(prof_idx)[2:].zfill(2))

                        if mode == 2:
                            if all(x == block[0] for x in block): bits.extend(encode_value(val_to_idx[block[0]], bases))
                            else: continue
                        elif mode == 5:
                            for x in block: bits.extend(bin(val_to_idx[x])[2:].zfill(bit_width))
                        else:
                            temp_h = list(history)
                            for j in range(len(block)):
                                if mode == 0: pred = 0
                                elif mode == 1: pred = temp_h[0]
                                elif mode == 3: pred = temp_h[0]
                                else: pred = max(0, min(255, 2*temp_h[0] - temp_h[1]))

                                val = (block[j] ^ pred) if mode == 3 else (block[j] - pred) % 256
                                bits.extend(encode_value(val_to_idx[val], bases))
                                temp_h = [block[j], temp_h[0]]
                        if best_bl is None or len(bits) < len(best_bl): best_bl = bits
                final_bits.extend(best_bl)
                cur_bl_count = len(block)

            history = [data[i], history[0]]
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
            f_out.write(f"const int {header_name}_width = {f['width']};\n")
            f_out.write(f"const int {header_name}_cp_count = {len(checkpoints)};\n#endif\n")

if __name__ == "__main__":
    import sys
    dir_name = "benchmark_data"
    if len(sys.argv) > 1: dir_name = sys.argv[1]
    compress_dir(dir_name)
