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

// In a real Arduino project, you'd include the file headers here, e.g.:
// #include "data.csv.h"

#ifdef MOCK_ARDUINO
extern std::vector<FileData> files_to_test;
void setup() {
  Serial.begin(9600);
}

void loop() {
    for (auto& f : files_to_test) {
        Serial.print("File ");
        Serial.print(f.name);
        Serial.print(": ");

        VDecompressor d;
        v_init(&d, common_h, f.data, f.len, f.bits);

        for (unsigned int i = 0; i < f.len; i++) {
            int val = v_get_next(&d);
            if (val != -1) {
                Serial.print(val);
                if (i < f.len - 1) Serial.print(",");
            }
        }
        Serial.println();

        // Example of random access:
        if (f.len > 0) {
            Serial.print("Byte at index ");
            Serial.print(f.len / 2);
            Serial.print(": ");
            Serial.println(v_get_at(&d, f.len / 2));
        }
    }
    // Stop after one iteration in mock
    while(1);
}
#else
void setup() {
  Serial.begin(9600);
  // Example initialization:
  // VDecompressor d;
  // v_init(&d, common_h, some_file_h, some_file_h_len, some_file_h_bits);
}

void loop() {
  // Production loop: use v_get_next(&d) or v_get_at(&d, index) as needed.
}
#endif
