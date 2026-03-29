// General-purpose Variable Base decompressor for Arduino (Optimized v11 - Low RAM)
#ifndef V_DECOMPRESSOR_H
#define V_DECOMPRESSOR_H

#ifdef MOCK_ARDUINO
#include "mock_arduino.h"
#else
#include <Arduino.h>
#include <avr/pgmspace.h>
#endif

#define BLOCK_SIZE 64
#define CP_INTERVAL 128

typedef struct {
    const uint8_t* compressed_data;
    unsigned int original_len;
    unsigned long total_bits;
    unsigned long bit_pos;
    unsigned int current_idx;

    const int16_t* common_h_ptr;
    int16_t common_denom;
    int16_t num_unique_vals;
    int16_t bit_width;
    int16_t num_profiles;
    const int16_t* profile_bases[4];
    int16_t profile_lens[4];
    const int16_t* symbols_ptr;

    int8_t block_mode; // 0..5
    int8_t block_profile;
    int16_t rle_val;
    unsigned int block_count;

    int16_t width;
    const uint16_t* cp_ptr;
    int16_t cp_count;

    uint8_t h0, h1; // History for prediction
    uint8_t cached_byte;
    int8_t cached_idx;
} VDecompressor;

// Total RAM usage: ~60-80 bytes. No line buffer.

static inline bool v_read_bit(VDecompressor* d) {
    if (d->bit_pos >= d->total_bits) return false;
    int8_t bit_offset = 7 - (d->bit_pos & 7);
    if (d->cached_idx != bit_offset + 1 && d->cached_idx != bit_offset) {
        d->cached_byte = pgm_read_byte_near(&d->compressed_data[d->bit_pos >> 3]);
    }
    bool bit = (d->cached_byte >> bit_offset) & 1;
    d->bit_pos++; d->cached_idx = bit_offset;
    return bit;
}

void v_init(VDecompressor* d, const int16_t* common_h_ptr, const uint8_t* compressed, unsigned int len, unsigned long bits, int width = 0, const uint16_t* cp = 0, int cp_count = 0) {
    d->common_h_ptr = common_h_ptr;
    d->common_denom = pgm_read_word_near(&common_h_ptr[0]);
    d->num_profiles = pgm_read_word_near(&common_h_ptr[1]);
    int offset = 2 + d->num_profiles;
    for (int i=0; i<d->num_profiles; i++) {
        d->profile_lens[i] = pgm_read_word_near(&common_h_ptr[2 + i]);
        d->profile_bases[i] = &common_h_ptr[offset];
        offset += d->profile_lens[i];
    }
    d->num_unique_vals = pgm_read_word_near(&common_h_ptr[offset]);
    d->bit_width = pgm_read_word_near(&common_h_ptr[offset + 1]);
    d->symbols_ptr = &common_h_ptr[offset + 2];
    d->compressed_data = compressed; d->original_len = len; d->total_bits = bits;
    d->bit_pos = 0; d->current_idx = 0; d->block_count = 0; d->cached_idx = -1;
    d->width = width; d->cp_ptr = cp; d->cp_count = cp_count;
    d->h0 = 0; d->h1 = 0;
}

static int16_t v_read_truncated(VDecompressor* d, int16_t b) {
    if (b <= 1) return 0;
    int k = 0, temp = b;
    while (temp >>= 1) k++;
    int16_t u = (1 << (k + 1)) - b;
    int16_t r = 0;
    for (int i = 0; i < k; i++) r = (r << 1) | (v_read_bit(d) ? 1 : 0);
    if (r >= u) { r = (r << 1) | (v_read_bit(d) ? 1 : 0); r -= u; }
    return r;
}

static int16_t v_decode_idx(VDecompressor* d) {
    int32_t idx = 0, multiplier = 1;
    int16_t n_b = d->profile_lens[d->block_profile];
    const int16_t* b_ptr = d->profile_bases[d->block_profile];
    for (int i = 0; i < n_b; i++) {
        int16_t b = pgm_read_word_near(&b_ptr[i]);
        idx += (int32_t)v_read_truncated(d, b) * multiplier;
        multiplier *= (int32_t)b;
        if (!v_read_bit(d)) goto found;
        idx += multiplier;
    }
    { int q = 0; while (v_read_bit(d)) q++; idx += (int32_t)q * multiplier; }
found:
    return (int16_t)idx;
}

bool v_get_next(VDecompressor* d, int16_t* out) {
    if (d->current_idx >= d->original_len) return false;
    if (d->block_count == 0) {
        if (!v_read_bit(d)) d->block_mode = 0; // 0
        else if (!v_read_bit(d)) d->block_mode = 1; // 10
        else if (!v_read_bit(d)) d->block_mode = 2; // 110
        else if (!v_read_bit(d)) d->block_mode = 3; // 1110
        else if (!v_read_bit(d)) d->block_mode = 4; // 11110
        else d->block_mode = 5; // 11111
        d->block_profile = (v_read_bit(d) ? 2 : 0) | (v_read_bit(d) ? 1 : 0);
        d->block_count = (d->original_len - d->current_idx < BLOCK_SIZE) ? (d->original_len - d->current_idx) : BLOCK_SIZE;
        if (d->block_mode == 2) {
            int16_t idx = v_decode_idx(d);
            d->rle_val = (int16_t)(pgm_read_word_near(&d->symbols_ptr[idx]) * d->common_denom);
        }
    }
    int16_t val = 0;
    if (d->block_mode == 2) val = d->rle_val;
    else if (d->block_mode == 5) {
        int32_t idx = 0;
        for (int i = 0; i < d->bit_width; i++) idx = (idx << 1) | (v_read_bit(d) ? 1 : 0);
        val = (int16_t)(pgm_read_word_near(&d->symbols_ptr[idx]) * d->common_denom);
    } else {
        int16_t res_idx = v_decode_idx(d);
        int16_t res = (int16_t)(pgm_read_word_near(&d->symbols_ptr[res_idx]) * d->common_denom);
        uint8_t pred = d->h0;
        if (d->block_mode == 4) {
             int16_t p = 2*(int16_t)d->h0 - (int16_t)d->h1;
             pred = (uint8_t)((p < 0) ? 0 : ((p > 255) ? 255 : p));
        }
        if (d->block_mode == 0) val = res;
        else if (d->block_mode == 3) val = (int16_t)(pred ^ res);
        else val = (int16_t)((pred + res) % 256);
    }
    d->h1 = d->h0; d->h0 = (uint8_t)val;
    d->current_idx++; d->block_count--; *out = val; return true;
}

static inline uint32_t compact_1d(uint32_t n) {
    n &= 0x55555555; n = (n | (n >> 1)) & 0x33333333; n = (n | (n >> 2)) & 0x0f0f0f0f; n = (n | (n >> 4)) & 0x00ff00ff; n = (n | (n >> 8)) & 0x0000ffff; return n;
}
static inline void z_order_decode(uint32_t z, uint32_t* x, uint32_t* y) { *x = compact_1d(z); *y = compact_1d(z >> 1); }
static inline uint32_t part1d(uint32_t n) {
    n &= 0x0000ffff; n = (n | (n << 8)) & 0x00ff00ff; n = (n | (n << 4)) & 0x0f0f0f0f; n = (n | (n << 2)) & 0x33333333; n = (n | (n << 1)) & 0x55555555; return n;
}
static inline uint32_t z_order_encode(uint32_t x, uint32_t y) { return (part1d(y) << 1) | part1d(x); }

bool v_get_at(VDecompressor* d, unsigned int index, int16_t* out) {
    if (index >= d->original_len) return false;
    unsigned int tr = index;
    if (d->width > 0) {
        uint32_t xt = index % d->width, yt = index / d->width, zt = z_order_encode(xt, yt);
        if ((d->width & (d->width - 1)) == 0 && (unsigned long)d->width * d->width <= d->original_len) tr = zt;
        else {
            tr = 0;
            for (uint32_t z = 0; z < zt; z++) {
                uint32_t cx, cy; z_order_decode(z, &cx, &cy);
                if (cx < (uint32_t)d->width && (cy * (uint32_t)d->width + cx) < d->original_len) tr++;
            }
        }
    }
    if (d->cp_ptr && (tr < d->current_idx || tr > d->current_idx + 16)) {
        int cp_i = tr / CP_INTERVAL;
        if (cp_i < d->cp_count) {
            uint32_t bp = pgm_read_word_near(&d->cp_ptr[cp_i * 3 + 0]);
            bp |= ((uint32_t)pgm_read_word_near(&d->cp_ptr[cp_i * 3 + 1]) << 16);
            uint16_t m = pgm_read_word_near(&d->cp_ptr[cp_i * 3 + 2]);
            d->bit_pos = bp; d->current_idx = cp_i * CP_INTERVAL; d->block_count = m & 0xFF; d->cached_idx = -1;
            d->h0 = (uint8_t)(m >> 8); d->h1 = 0; // approximate recovery
        } else if (tr < d->current_idx) {
            d->bit_pos = 0; d->current_idx = 0; d->block_count = 0; d->cached_idx = -1; d->h0 = 0; d->h1 = 0;
        }
    } else if (tr < d->current_idx) {
        d->bit_pos = 0; d->current_idx = 0; d->block_count = 0; d->cached_idx = -1; d->h0 = 0; d->h1 = 0;
    }
    int16_t temp; while (d->current_idx < tr) if (!v_get_next(d, &temp)) return false;
    return v_get_next(d, out);
}
#endif
