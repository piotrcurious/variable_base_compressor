// General-purpose Variable Base decompressor for Arduino (Optimized - Context Adaptive)
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

    int8_t block_mode; // 0..3
    int16_t rle_val;
    unsigned int block_count;

    const uint16_t* cp_ptr;
    int16_t cp_count;

    int16_t prev_val;
    uint8_t cached_byte;
    int8_t cached_idx;
} VDecompressor;

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

static int16_t v_unfold(int16_t f) {
    if (f % 2 == 0) return f / 2;
    else return -((f + 1) / 2);
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

static int16_t v_decode_val(VDecompressor* d) {
    int prof_idx = (d->prev_val < 8) ? 0 : ((d->prev_val < 32) ? 1 : ((d->prev_val < 128) ? 2 : 3));
    int32_t idx = 0, multiplier = 1;
    int16_t n_b = d->profile_lens[prof_idx];
    const int16_t* b_ptr = d->profile_bases[prof_idx];
    for (int i = 0; i < n_b; i++) {
        int16_t b = pgm_read_word_near(&b_ptr[i]);
        idx += (int32_t)v_read_truncated(d, b) * multiplier;
        multiplier *= (int32_t)b;
        if (!v_read_bit(d)) goto found;
        idx += multiplier;
    }
    { int q = 0; while (v_read_bit(d)) q++; idx += (int32_t)q * multiplier; }
found:
    if (idx < (int32_t)d->num_unique_vals) return (int16_t)pgm_read_word_near(&d->symbols_ptr[idx]);
    return 0;
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
    d->cp_ptr = cp; d->cp_count = cp_count; d->prev_val = 0;

    // Skip dummy pattern space
    d->bit_pos = 4;
}

bool v_get_next(VDecompressor* d, int16_t* out) {
    if (d->current_idx >= d->original_len) return false;
    if (d->current_idx % CP_INTERVAL == 0) {
        d->prev_val = 0;
        d->block_count = 0;
    }
    if (d->block_count == 0) {
        if (!v_read_bit(d)) d->block_mode = 0;
        else if (!v_read_bit(d)) d->block_mode = 1;
        else if (!v_read_bit(d)) d->block_mode = 2;
        else d->block_mode = 3;
        d->block_count = (d->original_len - d->current_idx < BLOCK_SIZE) ? (d->original_len - d->current_idx) : BLOCK_SIZE;
        if (d->block_mode == 2) d->rle_val = (uint8_t)(v_decode_val(d) * d->common_denom);
    }

    int16_t val;
    if (d->block_mode == 2) val = d->rle_val;
    else {
        int16_t decoded = v_decode_val(d);
        if (d->block_mode == 0) val = (uint8_t)(decoded * d->common_denom);
        else if (d->block_mode == 1) val = (uint8_t)(d->prev_val + v_unfold(decoded));
        else val = (uint8_t)(d->prev_val ^ (uint8_t)(decoded * d->common_denom));
    }
    d->prev_val = val;
    d->current_idx++; d->block_count--; *out = val; return true;
}

bool v_get_at(VDecompressor* d, unsigned int index, int16_t* out) {
    if (index >= d->original_len) return false;
    unsigned int tr = index;
    if (d->cp_ptr && (tr < d->current_idx || tr > d->current_idx + 16)) {
        int cp_i = tr / CP_INTERVAL;
        if (cp_i < d->cp_count) {
            uint32_t bp = pgm_read_word_near(&d->cp_ptr[cp_i * 3 + 0]);
            bp |= ((uint32_t)pgm_read_word_near(&d->cp_ptr[cp_i * 3 + 1]) << 16);
            d->bit_pos = bp; d->current_idx = cp_i * CP_INTERVAL; d->block_count = 0; d->cached_idx = -1;
            d->prev_val = 0;
        } else if (tr < d->current_idx) {
            d->bit_pos = 4; d->current_idx = 0; d->block_count = 0; d->cached_idx = -1; d->prev_val = 0;
        }
    } else if (tr < d->current_idx) {
        d->bit_pos = 4; d->current_idx = 0; d->block_count = 0; d->cached_idx = -1; d->prev_val = 0;
    }
    int16_t temp; while (d->current_idx < tr) if (!v_get_next(d, &temp)) return false;
    return v_get_next(d, out);
}
#endif
