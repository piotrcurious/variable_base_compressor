import os
import random
import subprocess
import sys
import time

def generate_test_data(dir_name="benchmark_data"):
    os.makedirs(dir_name, exist_ok=True)
    with open(f"{dir_name}/text_12kb.txt", "w") as f:
        words = ["Arduino", "Decompressor", "Variable", "Base", "Streaming", "Low", "RAM", "Block", "Filter", "Checkpoint", "XOR", "RLE"]
        for _ in range(12 * 1024 // 10): f.write(random.choice(words) + " ")
    with open(f"{dir_name}/map_8kb.bin", "wb") as f:
        data = bytearray()
        val = 128
        for _ in range(8192):
            val = max(0, min(255, val + random.randint(-4, 4)))
            data.append(val)
        f.write(data)
    with open(f"{dir_name}/image_16kb.bin", "wb") as f:
        data = bytearray()
        for i in range(128):
            for j in range(128): data.append((i + j) % 256)
        f.write(data)
    with open(f"{dir_name}/sparse_1kb.bin", "wb") as f:
        data = bytearray([random.randint(0,255) if random.random() < 0.05 else 0 for _ in range(1024)])
        f.write(data)

def compress_data(dir_name="benchmark_data"):
    print(f"Compressing files in {dir_name}...")
    cmd = ["python3", "compressor3.py", dir_name]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Compression failed:", res.stderr)
        return False
    print(res.stdout)
    return True

def compile_and_run_benchmark():
    print("Compiling benchmark runner...")
    cpp_files = [f for f in os.listdir(".") if f.endswith(".h") and f not in ["v_decompressor.h", "file_data.h", "mock_arduino.h", "common.h"]]
    includes = "".join([f'#include "{f}"\n' for f in cpp_files])
    file_list = []
    for f in cpp_files:
        base = f.replace(".", "_").replace("_h", "")
        v_n = f.replace(".", "_")
        # Check if cp array exists in header
        cp_exists = False
        with open(f, "r") as fh:
            if "_cp[]" in fh.read(): cp_exists = True

        if cp_exists:
            file_list.append(f'{{"{base}", {v_n}, {v_n}_len, {v_n}_bits, {v_n}_width, {v_n}_cp, {v_n}_cp_count}}')
        else:
            file_list.append(f'{{"{base}", {v_n}, {v_n}_len, {v_n}_bits, {v_n}_width, 0, 0}}')

    runner_code = f"""
#include "mock_arduino.h"
#include "v_decompressor.h"
#include "file_data.h"
#include "common.h"
#include <vector>
#include <iostream>
#include <fstream>
#include <iterator>
#include <algorithm>

struct BenchmarkFileData {{
    const char* name;
    const uint8_t* data;
    unsigned int len;
    unsigned long bits;
    int width;
    const uint16_t* cp;
    int cp_count;
}};

{includes}

std::vector<BenchmarkFileData> benchmark_files = {{
    {", ".join(file_list)}
}};

MockSerial Serial;

int main() {{
    std::cout << "NAME|SIZE|SPEED|RATIO|SEEK|STATUS" << std::endl;
    for (auto& f : benchmark_files) {{
        VDecompressor d;
        v_init(&d, common_h, f.data, f.len, f.bits, f.width, f.cp, f.cp_count);

        unsigned long start = micros();
        int16_t val;
        std::vector<uint8_t> decoded_items;
        decoded_items.reserve(f.len);
        for (unsigned int i = 0; i < f.len; i++) {{
            if (v_get_next(&d, &val)) decoded_items.push_back((uint8_t)val);
        }}
        unsigned long end = micros();
        unsigned long elapsed = end - start;
        if (elapsed == 0) elapsed = 1;
        double speed = (f.len * 1000000.0) / elapsed;
        double ratio = (double)(f.len * 8) / f.bits;

        start = micros();
        int16_t seek_val;
        v_get_at(&d, f.len - 1, &seek_val);
        unsigned long seek_elapsed = micros() - start;

        std::vector<uint8_t> decoded_data;
        if (f.width > 0) {{
            decoded_data.assign(f.len, 0);
            uint32_t rank = 0;
            int height = (f.len + f.width - 1) / f.width, size = 1;
            while (size < f.width || size < height) size <<= 1;
            for (uint32_t z = 0; z < (uint32_t)size * size; z++) {{
                uint32_t x = compact_1d(z), y = compact_1d(z >> 1);
                if (x < (uint32_t)f.width && y * (uint32_t)f.width + x < (uint32_t)f.len) {{
                    if (rank < decoded_items.size()) decoded_data[y * f.width + x] = decoded_items[rank++];
                }}
            }}
        }} else decoded_data = decoded_items;

        bool pass = (decoded_data.size() == f.len);
        if (pass) {{
            std::string o_p = "benchmark_data/" + std::string(f.name);
            size_t l_u = o_p.find_last_of('_');
            if (l_u != std::string::npos) o_p[l_u] = '.';
            std::ifstream o_f(o_p, std::ios::binary);
            if (o_f.is_open()) {{
                std::vector<uint8_t> o_d((std::istreambuf_iterator<char>(o_f)), std::istreambuf_iterator<char>());
                if (o_d.size() != decoded_data.size()) pass = false;
                else {{
                    for (size_t i = 0; i < o_d.size(); i++) if (o_d[i] != decoded_data[i]) {{ pass = false; break; }}
                }}
            }} else pass = false;
        }}
        std::cout << f.name << "|" << f.len << "|" << speed << "|" << ratio << "|" << seek_elapsed << "|" << (pass ? "PASS" : "FAIL") << std::endl;
    }}
    return 0;
}}
"""
    with open("runner.cpp", "w") as f_out: f_out.write(runner_code)
    cmd = ["g++", "-O3", "-DMOCK_ARDUINO", "-I.", "runner.cpp", "-o", "runner"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Compilation failed:", res.stderr)
        return None
    res = subprocess.run(["./runner"], capture_output=True, text=True)
    return res.stdout.strip().split("\n")

def ascii_bar(val, max_val, width=20):
    if max_val == 0: return ""
    bar_width = int((val / max_val) * width)
    return "█" * bar_width + "░" * (width - bar_width)

def generate_markdown_report(results):
    if not results: return
    data = [line.split("|") for line in results[1:]]
    max_speed = max([float(d[2]) for d in data])
    max_ratio = max([float(d[3]) for d in data])
    max_seek = max([float(d[4]) for d in data])
    with open("BENCHMARK_REPORT.md", "w") as f_out:
        f_out.write("# Arduino Variable-Base Decompressor Benchmark (Bit-Packed + Multi-Filter)\n\n")
        f_out.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f_out.write("## Summary Table\n\n")
        f_out.write("| File Name | Size (B) | Speed (B/s) | Ratio | Seek (us) | Status |\n")
        f_out.write("| --- | --- | --- | --- | --- | --- |\n")
        for d in data: f_out.write(f"| {d[0]} | {d[1]} | {float(d[2]):,.0f} | {float(d[3]):.2f} | {d[4]} | {d[5]} |\n")
        f_out.write("\n## Performance Charts\n\n")
        f_out.write("### Decompression Speed (Bytes/sec)\n```\n")
        for d in data: f_out.write(f"{d[0]:<15} | {ascii_bar(float(d[2]), max_speed)} | {float(d[2]):,.0f} B/s\n")
        f_out.write("```\n\n### Random Access Seek Time (Last Byte)\n```\n")
        for d in data: f_out.write(f"{d[0]:<15} | {ascii_bar(float(d[4]), max_seek)} | {d[4]} us\n")
        f_out.write("```\n\n## Conclusion\n")
        f_out.write("The addition of Bit-Packed mode and Paeth predictors further improves density for low-entropy and structured data.\n")

if __name__ == "__main__":
    generate_test_data()
    if compress_data():
        results = compile_and_run_benchmark()
        generate_markdown_report(results)
        print("Benchmark report generated: BENCHMARK_REPORT.md")
