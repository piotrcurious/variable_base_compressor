// General-purpose Variable Base decompressor for Arduino (with Nesting and Z-order)
#ifndef V_DECOMPRESSOR_H
#define V_DECOMPRESSOR_H

#ifdef MOCK_ARDUINO
#include "mock_arduino.h"
#else
#include <Arduino.h>
#include <avr/pgmspace.h>
#endif

typedef struct {
    const uint8_t* compressed_data;
    unsigned int original_len;
    unsigned long total_bits;
    unsigned long bit_pos;
    unsigned int current_idx;

    const int16_t* common_h_ptr;
    int16_t common_denom;
    int16_t num_unique_vals;

    int16_t num_bases;
    const int16_t* base_sizes;

    int16_t width; // Z-order width (0 if none)
} VDecompressor;

static inline bool v_read_bit(VDecompressor* d) {
    if (d->bit_pos >= d->total_bits) return false;
    uint8_t b = pgm_read_byte_near(&d->compressed_data[d->bit_pos >> 3]);
    bool bit = (b >> (7 - (d->bit_pos & 7))) & 1;
    d->bit_pos++;
    return bit;
}

void v_init(VDecompressor* d, const int16_t* common_h_ptr, const uint8_t* compressed, unsigned int len, unsigned long bits, int width = 0) {
    d->common_h_ptr = common_h_ptr;
    d->common_denom = pgm_read_word_near(&common_h_ptr[0]);
    d->num_bases = pgm_read_word_near(&common_h_ptr[1]);
    d->base_sizes = &common_h_ptr[2];
    d->num_unique_vals = pgm_read_word_near(&common_h_ptr[2 + d->num_bases]);

    d->compressed_data = compressed;
    d->original_len = len;
    d->total_bits = bits;
    d->bit_pos = 0;
    d->current_idx = 0;
    d->width = width;
}

static int16_t v_read_truncated(VDecompressor* d, int16_t b) {
    if (b <= 1) return 0;
    int k = 0;
    int temp = b;
    while (temp >>= 1) k++;
    int16_t u = (1 << (k + 1)) - b;

    int16_t r = 0;
    for (int i = 0; i < k; i++) {
        r = (r << 1) | (v_read_bit(d) ? 1 : 0);
    }
    if (r >= u) {
        r = (r << 1) | (v_read_bit(d) ? 1 : 0);
        r -= u;
    }
    return r;
}

bool v_get_next(VDecompressor* d, int16_t* out) {
    if (d->current_idx >= d->original_len) return false;

    int32_t idx = 0;
    int32_t multiplier = 1;

    for (int i = 0; i < d->num_bases; i++) {
        int16_t b = pgm_read_word_near(&d->base_sizes[i]);
        int16_t r = v_read_truncated(d, b);
        idx += (int32_t)r * multiplier;
        multiplier *= (int32_t)b;

        if (!v_read_bit(d)) {
            goto found;
        }
        idx += multiplier;
    }

    {
        int q = 0;
        while (v_read_bit(d)) q++;
        idx += (int32_t)q * multiplier;
    }

found:
    d->current_idx++;
    if (idx < (int32_t)d->num_unique_vals) {
        int16_t symbol = pgm_read_word_near(&d->common_h_ptr[4 + d->num_bases + idx]);
        *out = (int16_t)(symbol * d->common_denom);
        return true;
    }
    return false;
}

// Z-order ranking support for random access
static inline uint32_t compact_1d(uint32_t n) {
    n &= 0x55555555;
    n = (n | (n >> 1)) & 0x33333333;
    n = (n | (n >> 2)) & 0x0f0f0f0f;
    n = (n | (n >> 4)) & 0x00ff00ff;
    n = (n | (n >> 8)) & 0x0000ffff;
    return n;
}

static inline void z_order_decode(uint32_t z, uint32_t* x, uint32_t* y) {
    *x = compact_1d(z);
    *y = compact_1d(z >> 1);
}

static inline uint32_t part1d(uint32_t n) {
    n &= 0x0000ffff;
    n = (n | (n << 8)) & 0x00ff00ff;
    n = (n | (n << 4)) & 0x0f0f0f0f;
    n = (n | (n << 2)) & 0x33333333;
    n = (n | (n << 1)) & 0x55555555;
    return n;
}

static inline uint32_t z_order_encode(uint32_t x, uint32_t y) {
    return (part1d(y) << 1) | part1d(x);
}

bool v_get_at(VDecompressor* d, unsigned int index, int16_t* out) {
    if (index >= d->original_len) return false;

    unsigned int target_rank = index;
    if (d->width > 0) {
        // Find the rank of the current index (x,y) among valid z-ordered entries
        uint32_t x_target = index % d->width;
        uint32_t y_target = index / d->width;
        uint32_t z_target = z_order_encode(x_target, y_target);

        target_rank = 0;
        // This scan is O(Z_target), which is O(N) in worst case but still useful
        for (uint32_t z = 0; z < z_target; z++) {
            uint32_t cur_x, cur_y;
            z_order_decode(z, &cur_x, &cur_y);
            if (cur_x < (uint32_t)d->width && cur_y * (uint32_t)d->width + cur_x < d->original_len) {
                target_rank++;
            }
        }
    }

    if (target_rank < d->current_idx) {
        d->bit_pos = 0;
        d->current_idx = 0;
    }

    int16_t temp;
    while (d->current_idx < target_rank) {
        if (!v_get_next(d, &temp)) return false;
    }

    return v_get_next(d, out);
}

#endif
