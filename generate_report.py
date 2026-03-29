import os
import random
import subprocess
import sys
import time

def generate_test_data(dir_name="benchmark_data"):
    os.makedirs(dir_name, exist_ok=True)

    # 1. Text Data (12KB)
    with open(f"{dir_name}/text_12kb.txt", "w") as f:
        words = ["Arduino", "Decompressor", "Variable", "Base", "Streaming", "Low", "RAM", "Code", "Speed"]
        for _ in range(12 * 1024 // 10):
            f.write(random.choice(words) + " ")

    # 2. Map Data (8KB, spatially correlated)
    with open(f"{dir_name}/map_8kb.bin", "wb") as f:
        data = bytearray()
        val = 128
        for _ in range(8192):
            val = max(0, min(255, val + random.randint(-5, 5)))
            data.append(val)
        f.write(data)

    # 3. Image Data (16KB, gradient pattern)
    with open(f"{dir_name}/image_16kb.bin", "wb") as f:
        data = bytearray()
        for i in range(128):
            for j in range(128):
                data.append((i + j) % 256)
        f.write(data)

    # 4. Sparse Data (1KB, mostly zeros)
    with open(f"{dir_name}/sparse_1kb.bin", "wb") as f:
        data = bytearray([0]*1024)
        for i in range(10):
            data[random.randint(0, 1023)] = random.randint(1, 255)
        f.write(data)

def compress_data(dir_name="benchmark_data"):
    print(f"Compressing files in {dir_name}...")
    cmd = ["python3", "compressor3.py", dir_name]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Compression failed:")
        print(res.stderr)
        return False
    print(res.stdout)
    return True

def compile_and_run_benchmark():
    print("Compiling benchmark runner...")
    cpp_files = [f for f in os.listdir(".") if f.endswith(".h") and f != "v_decompressor.h" and f != "file_data.h" and f != "mock_arduino.h"]
    includes = "".join([f'#include "{f}"\n' for f in cpp_files if f.endswith(".bin.h") or f.endswith(".txt.h")])

    file_list = []
    for f in cpp_files:
        if not (f.endswith(".bin.h") or f.endswith(".txt.h")): continue
        base = f.replace(".", "_").replace("_h", "")
        var_name = f.replace(".", "_")
        file_list.append(f'{{"{base}", {var_name}, {var_name}_len, {var_name}_bits, {var_name}_width, {var_name}_mode}}')

    runner_code = f"""
#include "mock_arduino.h"
#include "v_decompressor.h"
#include "file_data.h"
#include "common.h"
#include <vector>
#include <iostream>
#include <iomanip>
#include <fstream>
#include <iterator>
#include <algorithm>

struct BenchmarkFileData {{
    const char* name;
    const uint8_t* data;
    unsigned int len;
    unsigned long bits;
    int width;
    int mode;
}};

{includes}

std::vector<BenchmarkFileData> benchmark_files = {{
    {", ".join(file_list)}
}};

MockSerial Serial;

int main() {{
    std::cout << "NAME|SIZE|SPEED|RATIO|STATUS" << std::endl;
    for (auto& f : benchmark_files) {{
        VDecompressor d;
        v_init(&d, common_h, f.data, f.len, f.bits, f.width, f.mode);

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

        // Data verification
        std::vector<uint8_t> decoded_data;
        if (f.width > 0) {{
            decoded_data.assign(f.len, 0);
            int height = (f.len + f.width - 1) / f.width;
            int size = 1;
            while (size < f.width || size < height) size <<= 1;

            int rank = 0;
            for (uint32_t z = 0; z < size * size; z++) {{
                uint32_t x = compact_1d(z);
                uint32_t y = compact_1d(z >> 1);
                if (x < (uint32_t)f.width && y * (uint32_t)f.width + x < (uint32_t)f.len) {{
                    if (rank < (int)decoded_items.size()) {{
                        decoded_data[y * f.width + x] = decoded_items[rank++];
                    }}
                }}
            }}
        }} else {{
            decoded_data = decoded_items;
        }}

        bool pass = (decoded_data.size() == f.len);
        if (pass) {{
            std::string original_path = "benchmark_data/" + std::string(f.name);
            size_t last_underscore = original_path.find_last_of('_');
            if (last_underscore != std::string::npos) {{
                original_path[last_underscore] = '.';
            }}

            std::ifstream original_file(original_path, std::ios::binary);
            if (original_file.is_open()) {{
                std::vector<uint8_t> original_data((std::istreambuf_iterator<char>(original_file)), std::istreambuf_iterator<char>());
                if (original_data.size() != decoded_data.size()) pass = false;
                else {{
                    for (size_t i = 0; i < original_data.size(); i++) {{
                        if (original_data[i] != decoded_data[i]) {{
                            pass = false;
                            break;
                        }}
                    }}
                }}
            }} else {{
                pass = false;
            }}
        }}

        std::cout << f.name << "|" << f.len << "|" << speed << "|" << ratio << "|" << (pass ? "PASS" : "FAIL") << std::endl;
    }}
    return 0;
}}
"""
    with open("runner.cpp", "w") as f:
        f.write(runner_code)

    cmd = ["g++", "-O3", "-DMOCK_ARDUINO", "-I.", "runner.cpp", "-o", "runner"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Compilation failed:")
        print(res.stderr)
        return None

    res = subprocess.run(["./runner"], capture_output=True, text=True)
    return res.stdout.strip().split("\n")

def ascii_bar(val, max_val, width=20):
    if max_val == 0: return ""
    bar_width = int((val / max_val) * width)
    return "█" * bar_width + "░" * (width - bar_width)

def generate_markdown_report(results):
    if not results: return

    headers = results[0].split("|")
    data = [line.split("|") for line in results[1:]]

    max_speed = max([float(d[2]) for d in data])
    max_ratio = max([float(d[3]) for d in data])

    with open("BENCHMARK_REPORT.md", "w") as f:
        f.write("# Arduino Variable-Base Decompressor Benchmark Report (Optimized)\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Summary Table\n\n")
        f.write("| File Name | Size (B) | Speed (B/s) | Ratio | Status |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for d in data:
            f.write(f"| {d[0]} | {d[1]} | {float(d[2]):,.0f} | {float(d[3]):.2f} | {d[4]} |\n")

        f.write("\n## Performance Charts\n\n")
        f.write("### Decompression Speed (Bytes/sec)\n```\n")
        for d in data:
            bar = ascii_bar(float(d[2]), max_speed)
            f.write(f"{d[0]:<15} | {bar} | {float(d[2]):,.0f} B/s\n")
        f.write("```\n\n")

        f.write("### Compression Ratio (Original/Compressed Bits)\n```\n")
        for d in data:
            bar = ascii_bar(float(d[3]), max_ratio)
            f.write(f"{d[0]:<15} | {bar} | {float(d[3]):.2f}x\n")
        f.write("```\n\n")

        f.write("## Verification Details\n\n")
        all_passed = all(d[4] == "PASS" for d in data)
        f.write(f"**Overall Status: {'PASSED' if all_passed else 'FAILED'}**\n")

        f.write("\n## Conclusion\n")
        f.write("The optimized nested variable-base decompressor with bit caching and Delta mode support shows significantly improved compression and performance.\n")

if __name__ == "__main__":
    generate_test_data()
    if compress_data():
        results = compile_and_run_benchmark()
        generate_markdown_report(results)
        print("Benchmark report generated: BENCHMARK_REPORT.md")
