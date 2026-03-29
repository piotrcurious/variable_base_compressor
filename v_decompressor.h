// General-purpose Variable Base decompressor for Arduino
#ifndef V_DECOMPRESSOR_H
#define V_DECOMPRESSOR_H

#ifdef MOCK_ARDUINO
#include "mock_arduino.h"
#else
#include <Arduino.h>
#include <avr/pgmspace.h>
#endif

typedef struct {
    const uint8_t* compressed_data; // 2 bytes (AVR) / 4-8 bytes (others)
    unsigned int original_len;      // 2 bytes
    unsigned long total_bits;       // 4 bytes
    unsigned long bit_pos;          // 4 bytes
    unsigned int current_idx;       // 2 bytes

    const int16_t* common_h_ptr;    // 2 bytes - points to flash

    int16_t common_denom;           // 2 bytes
    uint8_t base_size;              // 1 byte (max 256 as per compressor)
    int16_t num_unique_vals;        // 2 bytes

    uint8_t k;                      // 1 byte
    uint8_t u;                      // 1 byte
} VDecompressor;

// Total RAM per VDecompressor: ~20-24 bytes on AVR.

void v_init(VDecompressor* d, const int16_t* common_h_ptr, const uint8_t* compressed, unsigned int len, unsigned long bits) {
    d->common_h_ptr = common_h_ptr;
    d->common_denom = pgm_read_word_near(&common_h_ptr[0]);
    d->base_size = (uint8_t)pgm_read_word_near(&common_h_ptr[1]);
    d->num_unique_vals = pgm_read_word_near(&common_h_ptr[2]);

    d->compressed_data = compressed;
    d->original_len = len;
    d->total_bits = bits;
    d->bit_pos = 0;
    d->current_idx = 0;

    d->k = 0;
    if (d->base_size > 1) {
        int temp = d->base_size;
        while (temp >>= 1) d->k++;
    }
    d->u = (1 << (d->k + 1)) - d->base_size;
}

int v_get_next(VDecompressor* d) {
    if (d->current_idx >= d->original_len) return -1;

    int q = 0;
    while (d->bit_pos < d->total_bits) {
        uint8_t b = pgm_read_byte_near(&d->compressed_data[d->bit_pos / 8]);
        bool bit = (b >> (7 - (d->bit_pos % 8))) & 1;
        d->bit_pos++;
        if (bit) {
            q++;
        } else {
            break;
        }
    }

    int r = 0;
    if (d->base_size > 1) {
        for (int b_idx = 0; b_idx < d->k; b_idx++) {
            if (d->bit_pos < d->total_bits) {
                uint8_t b = pgm_read_byte_near(&d->compressed_data[d->bit_pos / 8]);
                bool bit = (b >> (7 - (d->bit_pos % 8))) & 1;
                d->bit_pos++;
                r = (r << 1) | (bit ? 1 : 0);
            }
        }

        if (r >= d->u) {
            if (d->bit_pos < d->total_bits) {
                uint8_t b = pgm_read_byte_near(&d->compressed_data[d->bit_pos / 8]);
                bool bit = (b >> (7 - (d->bit_pos % 8))) & 1;
                d->bit_pos++;
                r = (r << 1) | (bit ? 1 : 0);
                r -= d->u;
            }
        }
    }

    d->current_idx++;
    int idx = q * d->base_size + r;
    if (idx < d->num_unique_vals) {
        // symbols start at offset 4 in common_h
        int16_t symbol = pgm_read_word_near(&d->common_h_ptr[4 + idx]);
        return (int)symbol * d->common_denom;
    }
    return -1;
}

int v_get_at(VDecompressor* d, unsigned int index) {
    if (index >= d->original_len) return -1;

    if (index < d->current_idx) {
        d->bit_pos = 0;
        d->current_idx = 0;
    }

    while (d->current_idx < index) {
        v_get_next(d);
    }

    return v_get_next(d);
}

#endif
