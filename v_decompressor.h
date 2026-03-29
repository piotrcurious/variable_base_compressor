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
    const uint8_t* compressed_data; // Pointer to compressed bytes in flash
    unsigned int original_len;      // Original size of data
    unsigned long total_bits;       // Total number of bits in compressed data
    unsigned long bit_pos;          // Current bit position
    unsigned int current_idx;       // Current byte index in original data

    const int16_t* common_h_ptr;    // Pointer to dictionary in flash

    int16_t common_denom;           // Common multiplier for all symbols
    int16_t base_size;              // Number of symbols per "base" level
    int16_t num_unique_vals;        // Number of unique symbols in dictionary

    uint8_t k;                      // Number of bits for truncated binary (k)
    uint8_t u;                      // Truncated binary threshold (u)
} VDecompressor;

// Total RAM per VDecompressor: ~22-26 bytes on AVR.

/**
 * Helper to read a single bit from the compressed stream.
 */
static inline bool v_read_bit(VDecompressor* d) {
    if (d->bit_pos >= d->total_bits) return false;
    uint8_t b = pgm_read_byte_near(&d->compressed_data[d->bit_pos >> 3]);
    bool bit = (b >> (7 - (d->bit_pos & 7))) & 1;
    d->bit_pos++;
    return bit;
}

/**
 * Initializes the decompressor with the dictionary and compressed data.
 */
void v_init(VDecompressor* d, const int16_t* common_h_ptr, const uint8_t* compressed, unsigned int len, unsigned long bits) {
    d->common_h_ptr = common_h_ptr;
    d->common_denom = pgm_read_word_near(&common_h_ptr[0]);
    d->base_size = pgm_read_word_near(&common_h_ptr[1]);
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

/**
 * Decompress the next value and store it in *out.
 * Returns true if successful, false if EOF or error.
 */
bool v_get_next(VDecompressor* d, int16_t* out) {
    if (d->current_idx >= d->original_len) return false;

    // 1. Read quotient (q) using unary coding
    int q = 0;
    while (d->bit_pos < d->total_bits) {
        if (v_read_bit(d)) {
            q++;
        } else {
            break;
        }
    }

    // 2. Read remainder (r) using truncated binary coding
    int r = 0;
    if (d->base_size > 1) {
        // Read k bits
        for (uint8_t b_idx = 0; b_idx < d->k; b_idx++) {
            r = (r << 1) | (v_read_bit(d) ? 1 : 0);
        }

        // If r >= u, read one more bit
        if (r >= d->u) {
            r = (r << 1) | (v_read_bit(d) ? 1 : 0);
            r -= d->u;
        }
    }

    d->current_idx++;
    int idx = q * d->base_size + r;
    if (idx < d->num_unique_vals) {
        // dictionary symbols start at offset 4 in common_h
        int16_t symbol = pgm_read_word_near(&d->common_h_ptr[4 + idx]);
        // Note: product could exceed int16_t if not careful.
        // We return as int16_t to match dictionary type.
        *out = (int16_t)(symbol * d->common_denom);
        return true;
    }
    return false;
}

/**
 * Returns the value at the specified index. Supports random access by seeking.
 * Returns true if successful, false if index is out of bounds.
 */
bool v_get_at(VDecompressor* d, unsigned int index, int16_t* out) {
    if (index >= d->original_len) return false;

    // Check if we need to restart or can continue forward
    if (index < d->current_idx) {
        d->bit_pos = 0;
        d->current_idx = 0;
    }

    // Seek forward until we reach the desired index
    int16_t temp;
    while (d->current_idx < index) {
        if (!v_get_next(d, &temp)) return false;
    }

    return v_get_next(d, out);
}

#endif
