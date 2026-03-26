import os
import random
import subprocess
import glob

def create_random_test_files(dir_name, num_files=3, max_size=100):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    for i in range(num_files):
        size = random.randint(10, max_size)
        data = bytes([random.randint(0, 255) for _ in range(size)])
        with open(os.path.join(dir_name, f"random_{i}.bin"), "wb") as f:
            f.write(data)

def generate_test_runner():
    headers = glob.glob("*.h")
    file_headers = [h for h in headers if h not in ["common.h", "mock_arduino.h", "file_data.h"]]

    with open("test_runner.cpp", "w") as f:
        f.write('#include "mock_arduino.h"\n')
        f.write('#include "common.h"\n')
        f.write('#include "file_data.h"\n')
        for h in file_headers:
            f.write(f'#include "{h}"\n')

        f.write('#include <vector>\n')

        f.write('std::vector<FileData> files_to_test = {\n')
        for h in file_headers:
            name = h.replace(".h", "")
            array_name = name.replace(".", "_") + "_h"
            f.write(f'    {{"{name}", {array_name}, {array_name}_len, {array_name}_bits}},\n')
        f.write('};\n\n')

        f.write('#include "decompressor3.ino"\n')
        f.write('#include "main.cpp"\n')

def run_test(dir_name):
    print(f"Running test on {dir_name}...")
    # Clean old headers
    for h in glob.glob("*.h"):
        if h not in ["mock_arduino.h", "file_data.h"]:
            os.remove(h)

    subprocess.run(["python3", "compressor3.py", dir_name], check=True)
    generate_test_runner()
    subprocess.run(["g++", "-o", "decompressor", "test_runner.cpp", "-I."], check=True)
    result = subprocess.run(["./decompressor"], capture_output=True, text=True, check=True)
    output = result.stdout

    files = sorted([f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))])

    all_passed = True
    for file_name in files:
        with open(os.path.join(dir_name, file_name), "rb") as f:
            original_data = list(f.read())

        line_prefix = f"File {file_name}: "
        found_line = None
        for line in output.split("\n"):
            if line.startswith(line_prefix):
                found_line = line
                break

        if found_line:
            data_part = found_line.split(": ")[1].strip()
            decompressed_data = [int(x) for x in data_part.split(",")] if data_part else []

            if original_data == decompressed_data:
                print(f"PASSED: {file_name}")
            else:
                print(f"FAILED: {file_name}")
                all_passed = False
        else:
            print(f"NOT FOUND: {file_name} in output")
            all_passed = False

    return all_passed

if __name__ == "__main__":
    if not os.path.exists("sample_dir"):
        os.makedirs("sample_dir")
        with open("sample_dir/file1.txt", "w") as f: f.write("Hello World!")

    if not os.path.exists("random_test_dir"):
        create_random_test_files("random_test_dir", 3, 50)

    try:
        p1 = run_test("sample_dir")
        p2 = run_test("random_test_dir")

        if p1 and p2:
            print("\nALL SYSTEM TESTS PASSED!")
        else:
            exit(1)
    finally:
        # Cleanup
        for h in glob.glob("*.h"):
            if h not in ["mock_arduino.h", "file_data.h"]:
                try: os.remove(h)
                except: pass
        if os.path.exists("decompressor"): os.remove("decompressor")
        if os.path.exists("test_runner.cpp"): os.remove("test_runner.cpp")
        if os.path.exists("sample_dir"):
             import shutil
             shutil.rmtree("sample_dir")
        if os.path.exists("random_test_dir"):
             import shutil
             shutil.rmtree("random_test_dir")
