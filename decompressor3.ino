// General-purpose Variable Base decompressor for Arduino
#ifdef MOCK_ARDUINO
#include "mock_arduino.h"
#include "file_data.h"
#include <vector>
#else
#include "common.h"
#endif

int16_t v_common_denom;
int16_t v_base_size;
int16_t v_num_unique_vals;
const int16_t* v_sorted_symbols;

void v_setup(const int16_t* common_h_ptr) {
  v_common_denom = pgm_read_word_near(&common_h_ptr[0]);
  v_base_size = pgm_read_word_near(&common_h_ptr[1]);
  v_num_unique_vals = pgm_read_word_near(&common_h_ptr[2]);
  v_sorted_symbols = &common_h_ptr[4];
}

void v_decompress(const uint8_t* compressed, unsigned int original_len, unsigned long total_bits) {
    unsigned long bit_pos = 0;

    int k = 0;
    if (v_base_size > 1) {
        int temp = v_base_size;
        while (temp >>= 1) k++;
    }
    int u = (1 << (k + 1)) - v_base_size;

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
        if (v_base_size > 1) {
            for (int b_idx = 0; b_idx < k; b_idx++) {
                if (bit_pos < total_bits) {
                    uint8_t b = pgm_read_byte_near(&compressed[bit_pos / 8]);
                    bool bit = (b >> (7 - (bit_pos % 8))) & 1;
                    bit_pos++;
                    r = (r << 1) | (bit ? 1 : 0);
                }
            }

            if (r >= u) {
                if (bit_pos < total_bits) {
                    uint8_t b = pgm_read_byte_near(&compressed[bit_pos / 8]);
                    bool bit = (b >> (7 - (bit_pos % 8))) & 1;
                    bit_pos++;
                    r = (r << 1) | (bit ? 1 : 0);
                    r -= u;
                }
            }
        }

        int idx = q * v_base_size + r;
        if (idx < v_num_unique_vals) {
            int16_t symbol = pgm_read_word_near(&v_sorted_symbols[idx]);
            Serial.print((int)symbol * v_common_denom);
            if (i < original_len - 1) Serial.print(",");
        }
    }
    Serial.println();
}

#ifdef MOCK_ARDUINO
extern const int16_t common_h[];
extern std::vector<FileData> files_to_test;
void setup() {
  Serial.begin(9600);
  v_setup(common_h);
}
void loop() {
    for (auto& f : files_to_test) {
        Serial.print("File ");
        Serial.print(f.name);
        Serial.print(": ");
        v_decompress(f.data, f.len, f.bits);
    }
}
#else
void setup() {
  Serial.begin(9600);
  v_setup(common_h);
}
void loop() {
  // Production loop: decompress and output data from common.h/file.h
}
#endif
