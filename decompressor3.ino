#include "mock_arduino.h"
#include "common.h"
#include "file_data.h"
#include <vector>

// Common parameters (using fixed-width for portability)
int16_t common_denom;
int16_t base_size;
int16_t num_unique_vals;
int16_t bits_for_mod;

void setup() {
  common_denom = pgm_read_word_near(&common_h[0]);
  base_size = pgm_read_word_near(&common_h[1]);
  num_unique_vals = pgm_read_word_near(&common_h[2]);
  bits_for_mod = pgm_read_word_near(&common_h[3]);
}

void decompress_file(const char* name, const uint8_t* compressed, unsigned int original_len, unsigned long total_bits) {
    Serial.print("File ");
    Serial.print(name);
    Serial.print(": ");

    unsigned long bit_pos = 0;
    for (unsigned int i = 0; i < original_len; i++) {
        int q = 0;
        bool q_done = false;
        while (bit_pos < total_bits) {
            uint8_t b = pgm_read_byte_near(&compressed[bit_pos / 8]);
            bool bit = (b >> (7 - (bit_pos % 8))) & 1;
            bit_pos++;
            if (bit) {
                q++;
            } else {
                q_done = true;
                break;
            }
        }
        
        if (!q_done && bit_pos >= total_bits && i < original_len) break;

        int r = 0;
        for (int b_idx = 0; b_idx < bits_for_mod; b_idx++) {
            if (bit_pos < total_bits) {
                uint8_t b = pgm_read_byte_near(&compressed[bit_pos / 8]);
                bool bit = (b >> (7 - (bit_pos % 8))) & 1;
                bit_pos++;
                r = (r << 1) | bit;
            }
        }

        int idx = q * base_size + r;
        if (idx < num_unique_vals) {
            int16_t val = pgm_read_word_near(&common_h[4 + idx]);
            Serial.print((int)val * common_denom);
            if (i < original_len - 1) Serial.print(",");
        }
    }
    Serial.println();
}

extern std::vector<FileData> files_to_test;

void loop() {
    for (auto& f : files_to_test) {
        decompress_file(f.name, f.data, f.len, f.bits);
    }
}
