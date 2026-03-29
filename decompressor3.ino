// General-purpose Variable Base decompressor for Arduino
#include "v_decompressor.h"

#ifdef MOCK_ARDUINO
#include "mock_arduino.h"
#include "file_data.h"
#include <vector>
#include "common.h"
#else
#include "common.h"
#endif

// Example decompressing and benchmarking
void run_benchmark(const char* name, const uint8_t* compressed, unsigned int len, unsigned long bits, int width = 0) {
    Serial.print("Testing: ");
    Serial.println(name);

    VDecompressor d;
    v_init(&d, common_h, compressed, len, bits, width);

    unsigned long start = micros();
    unsigned int count = 0;
    for (unsigned int i = 0; i < len; i++) {
        int16_t val;
        if (v_get_next(&d, &val)) {
            count++;
        }
    }
    unsigned long end = micros();

    if (count != len) {
        Serial.print("  ERROR: Expected ");
        Serial.print(len);
        Serial.print(" bytes, got ");
        Serial.println(count);
    }

    Serial.print("  Sequential Time: ");
    Serial.print(end - start);
    Serial.println(" us");

    // Random access benchmark (e.g. seek to middle)
    if (len > 0) {
        start = micros();
        int16_t middle_val;
        if (v_get_at(&d, len / 2, &middle_val)) {
            Serial.print("  Middle Byte: ");
            Serial.println(middle_val);
        }
        end = micros();
        Serial.print("  Seek Time: ");
        Serial.print(end - start);
        Serial.println(" us");
    }
    Serial.println();
}

#ifdef MOCK_ARDUINO
struct BenchmarkFileData {
    const char* name;
    const uint8_t* data;
    unsigned int len;
    unsigned long bits;
    int width;
};
extern std::vector<BenchmarkFileData> benchmark_files;
void setup() {
    Serial.begin(9600);
}

void loop() {
    for (auto& f : benchmark_files) {
        run_benchmark(f.name, f.data, f.len, f.bits, f.width);
    }
    while(1); // Stop after one iteration
}
#else
void setup() {
    Serial.begin(9600);
    // run_benchmark("somefile", somefile_h, somefile_h_len, somefile_h_bits);
}

void loop() {
    // Arduino production loop
}
#endif
