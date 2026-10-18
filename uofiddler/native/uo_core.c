#define BUILDING_UO_CORE
#include "uo_core.h"
#include <string.h>
#include <stdlib.h>

// ---------------------------------------------------------------------
// 1. Color Lookup Tables & Conversions
// ---------------------------------------------------------------------

static const uint8_t COLOR_5_TO_8[32] = {
    0, 8, 16, 24, 32, 41, 49, 57, 65, 74, 82, 90, 98, 106, 115, 123,
    131, 139, 148, 156, 164, 172, 180, 189, 197, 205, 213, 222, 230, 238, 246, 255
};

static const uint8_t COLOR_8_TO_5[256] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2,
    3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5,
    6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8,
    9, 9, 9, 9, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 11, 11, 11,
    12, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 14, 14,
    15, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 16, 17, 17, 17, 17, 17, 17, 17, 17, 17,
    18, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 19, 19, 19, 20, 20, 20, 20, 20, 20, 20, 20,
    21, 21, 21, 21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 22, 22, 22, 22, 23, 23, 23, 23, 23, 23, 23, 23,
    24, 24, 24, 24, 24, 24, 24, 24, 25, 25, 25, 25, 25, 25, 25, 25, 26, 26, 26, 26, 26, 26, 26, 26, 26,
    27, 27, 27, 27, 27, 27, 27, 27, 28, 28, 28, 28, 28, 28, 28, 28, 29, 29, 29, 29, 29, 29, 29, 29,
    30, 30, 30, 30, 30, 30, 30, 30, 31
};

UO_API uint32_t uo_color16_to_rgba(uint16_t c) {
    if (c == 0) return 0;
    uint32_t r = COLOR_5_TO_8[(c >> 10) & 0x1F];
    uint32_t g = COLOR_5_TO_8[(c >> 5) & 0x1F];
    uint32_t b = COLOR_5_TO_8[c & 0x1F];
    return (0xFF000000u) | (b << 16) | (g << 8) | r;
}

UO_API uint16_t uo_rgba_to_color16(uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    if (a < 128) return 0;
    uint16_t r5 = COLOR_8_TO_5[r];
    uint16_t g5 = COLOR_8_TO_5[g];
    uint16_t b5 = COLOR_8_TO_5[b];
    uint16_t c = (r5 << 10) | (g5 << 5) | b5;
    if (c == 0) c = 1;
    return c | 0x8000;
}

// ---------------------------------------------------------------------
// 2. Art Decoders (Static Items & Land Tiles)
// ---------------------------------------------------------------------

UO_API int uo_decode_static(
    const uint8_t* raw_data,
    size_t data_len,
    uint32_t* out_pixels,
    int max_w,
    int max_h,
    int* out_w,
    int* out_h
) {
    if (!raw_data || data_len < 8 || !out_pixels || !out_w || !out_h) return 0;

    const uint16_t* words = (const uint16_t*)raw_data;
    size_t word_count = data_len / 2;
    int width = words[2];
    int height = words[3];

    if (width <= 0 || height <= 0 || width > max_w || height > max_h) return 0;
    if (word_count < (size_t)(4 + height)) return 0;

    *out_w = width;
    *out_h = height;

    memset(out_pixels, 0, (size_t)width * (size_t)height * sizeof(uint32_t));

    const uint16_t* lookups = &words[4];
    for (int y = 0; y < height; y++) {
        size_t count = (size_t)height + 4 + lookups[y];
        int x = 0;
        uint32_t* row = &out_pixels[y * width];

        while (count + 1 < word_count) {
            uint16_t x_offset = words[count++];
            uint16_t x_run = words[count++];
            if ((x_offset | x_run) == 0) break;
            x += x_offset;
            if (x + x_run > width) break;

            for (int r = 0; r < x_run && count < word_count; r++) {
                row[x++] = uo_color16_to_rgba(words[count++] ^ 0x8000);
            }
        }
    }
    return 1;
}

UO_API int uo_decode_land(const uint8_t* raw_data, size_t data_len, uint32_t* out_pixels) {
    if (!raw_data || data_len < 2048 || !out_pixels) return 0;

    const uint16_t* words = (const uint16_t*)raw_data;
    memset(out_pixels, 0, 44 * 44 * sizeof(uint32_t));

    size_t word_idx = 0;
    int x_offset = 21;
    int x_run = 2;

    // Top half (rows 0 to 21)
    for (int y = 0; y < 22; y++) {
        uint32_t* row = &out_pixels[y * 44];
        for (int x = x_offset; x < x_offset + x_run; x++) {
            if (word_idx < 1024) {
                row[x] = uo_color16_to_rgba(words[word_idx++] | 0x8000);
            }
        }
        x_offset -= 1;
        x_run += 2;
    }

    x_offset = 0;
    x_run = 44;

    // Bottom half (rows 22 to 43)
    for (int y = 22; y < 44; y++) {
        uint32_t* row = &out_pixels[y * 44];
        for (int x = x_offset; x < x_offset + x_run; x++) {
            if (word_idx < 1024) {
                row[x] = uo_color16_to_rgba(words[word_idx++] | 0x8000);
            }
        }
        x_offset += 1;
        x_run -= 2;
    }

    return 1;
}

// ---------------------------------------------------------------------
// 3. Hue Application
// ---------------------------------------------------------------------

UO_API void uo_apply_hue(uint32_t* pixels, int count, const uint32_t* palette_32, int only_gray) {
    if (!pixels || count <= 0 || !palette_32) return;

    for (int i = 0; i < count; i++) {
        uint32_t px = pixels[i];
        uint32_t a = (px >> 24) & 0xFF;
        if (a == 0) continue;

        uint32_t r = px & 0xFF;
        uint32_t g = (px >> 8) & 0xFF;
        uint32_t b = (px >> 16) & 0xFF;
        if (r == 0 && g == 0 && b == 0) continue;

        if (only_gray) {
            if (r == g && g == b) {
                uint8_t idx = COLOR_8_TO_5[r];
                pixels[i] = (palette_32[idx] & 0x00FFFFFFu) | (a << 24);
            }
        } else {
            uint8_t idx = COLOR_8_TO_5[r];
            pixels[i] = (palette_32[idx] & 0x00FFFFFFu) | (a << 24);
        }
    }
}

// ---------------------------------------------------------------------
// 4. Mythic MTF Decompression
// ---------------------------------------------------------------------

#define MYTHIC_HEADER_XOR_KEY 0x8E2C9A3D
#define MYTHIC_FREQUENCY_HEADER_SIZE 1024

UO_API int uo_decompress_mythic(
    const uint8_t* src,
    size_t src_len,
    uint8_t* dst,
    size_t max_dst_len,
    size_t* out_decompressed_len
) {
    if (!src || src_len < 4 || !dst || !out_decompressed_len) return 0;

    uint32_t raw_len = (uint32_t)src[0] | ((uint32_t)src[1] << 8) | ((uint32_t)src[2] << 16) | ((uint32_t)src[3] << 24);
    uint32_t expected_len = raw_len ^ MYTHIC_HEADER_XOR_KEY;

    size_t mtf_len = src_len - 4;
    const uint8_t* mtf_input = src + 4;

    uint8_t* mtf_decoded = (uint8_t*)malloc(mtf_len);
    if (!mtf_decoded) return 0;

    uint8_t symbols[256];
    for (int i = 0; i < 256; i++) symbols[i] = (uint8_t)i;

    for (size_t i = 0; i < mtf_len; i++) {
        uint8_t ind = mtf_input[i];
        uint8_t val = symbols[ind];
        mtf_decoded[i] = val;
        if (ind > 0) {
            memmove(&symbols[1], &symbols[0], ind);
            symbols[0] = val;
        }
    }

    if (mtf_len < MYTHIC_FREQUENCY_HEADER_SIZE) {
        free(mtf_decoded);
        return 0;
    }

    int32_t partial_input[256 * 3];
    memset(partial_input, 0, sizeof(partial_input));
    for (int i = 0; i < 256; i++) {
        partial_input[i] = (int32_t)(
            (uint32_t)mtf_decoded[i * 4] |
            ((uint32_t)mtf_decoded[i * 4 + 1] << 8) |
            ((uint32_t)mtf_decoded[i * 4 + 2] << 16) |
            ((uint32_t)mtf_decoded[i * 4 + 3] << 24)
        );
    }

    int32_t total_sum = 0;
    int non_zero_count = 0;
    for (int i = 0; i < 256; i++) {
        total_sum += partial_input[i];
        if (partial_input[i] != 0) non_zero_count++;
    }

    if (total_sum <= 0 || (size_t)total_sum > max_dst_len) {
        free(mtf_decoded);
        return 0;
    }

    uint8_t symbol_table[256];
    uint8_t frequency[256];
    for (int i = 0; i < 256; i++) {
        symbol_table[i] = (uint8_t)i;
        frequency[i] = 0;
    }

    int32_t tmp[256];
    memcpy(tmp, partial_input, 256 * sizeof(int32_t));
    for (int i = 0; i < 256; i++) {
        int32_t max_val = 0;
        int max_idx = 0;
        for (int j = 0; j < 256; j++) {
            if (tmp[j] > max_val) {
                max_idx = j;
                max_val = tmp[j];
            }
        }
        if (max_val == 0) break;
        frequency[i] = (uint8_t)max_idx;
        tmp[max_idx] = 0;
    }

    int32_t m = 0;
    for (int i = 0; i < non_zero_count; i++) {
        uint8_t freq = frequency[i];
        if ((size_t)(m + MYTHIC_FREQUENCY_HEADER_SIZE) >= mtf_len) {
            free(mtf_decoded);
            return 0;
        }
        symbol_table[mtf_decoded[m + MYTHIC_FREQUENCY_HEADER_SIZE]] = freq;
        partial_input[freq + 256] = m + 1;
        m += partial_input[freq];
        partial_input[freq + 512] = m;
    }

    uint8_t val = symbol_table[0];
    int32_t count = 0;

    while (count < total_sum) {
        dst[count] = val;
        int32_t first_val = partial_input[val + 256];

        if (first_val < partial_input[val + 512]) {
            if ((size_t)(first_val + MYTHIC_FREQUENCY_HEADER_SIZE) >= mtf_len) {
                break;
            }
            uint8_t idx = mtf_decoded[first_val + MYTHIC_FREQUENCY_HEADER_SIZE];
            partial_input[val + 256]++;

            if (idx != 0) {
                for (int k = 0; k < idx; k++) {
                    symbol_table[k] = symbol_table[k + 1];
                }
                symbol_table[idx] = val;
                val = symbol_table[0];
            }
        } else if (non_zero_count > 0) {
            non_zero_count--;
            for (int k = 0; k < non_zero_count; k++) {
                symbol_table[k] = symbol_table[k + 1];
            }
            val = symbol_table[0];
        }
        count++;
    }

    free(mtf_decoded);
    *out_decompressed_len = (expected_len > 0 && (size_t)expected_len <= (size_t)total_sum) ? (size_t)expected_len : (size_t)total_sum;
    return 1;
}

// ---------------------------------------------------------------------
// 5. UOP 64-bit Jenkins Hash
// ---------------------------------------------------------------------

static inline uint32_t rotl32(uint32_t x, int k) {
    return (x << k) | (x >> (32 - k));
}

UO_API uint64_t uo_hash_file_name(const char* s, size_t len) {
    if (!s) return 0;

    uint32_t a = (uint32_t)len + 0xDEADBEEFu;
    uint32_t b = a;
    uint32_t c = a;

    size_t i = 0;
    size_t l = len;

    while (l > 12) {
        a += (uint32_t)((uint8_t)s[i]) |
             ((uint32_t)((uint8_t)s[i + 1]) << 8) |
             ((uint32_t)((uint8_t)s[i + 2]) << 16) |
             ((uint32_t)((uint8_t)s[i + 3]) << 24);
        b += (uint32_t)((uint8_t)s[i + 4]) |
             ((uint32_t)((uint8_t)s[i + 5]) << 8) |
             ((uint32_t)((uint8_t)s[i + 6]) << 16) |
             ((uint32_t)((uint8_t)s[i + 7]) << 24);
        c += (uint32_t)((uint8_t)s[i + 8]) |
             ((uint32_t)((uint8_t)s[i + 9]) << 8) |
             ((uint32_t)((uint8_t)s[i + 10]) << 16) |
             ((uint32_t)((uint8_t)s[i + 11]) << 24);

        a -= c; a ^= rotl32(c, 4);  c += b;
        b -= a; b ^= rotl32(a, 6);  a += c;
        c -= b; c ^= rotl32(b, 8);  b += a;
        a -= c; a ^= rotl32(c, 16); c += b;
        b -= a; b ^= rotl32(a, 19); a += c;
        c -= b; c ^= rotl32(b, 4);  b += a;

        i += 12;
        l -= 12;
    }

    if (l == 12) c += ((uint32_t)((uint8_t)s[i + 11])) << 24;
    if (l >= 11) c += ((uint32_t)((uint8_t)s[i + 10])) << 16;
    if (l >= 10) c += ((uint32_t)((uint8_t)s[i + 9]))  << 8;
    if (l >= 9)  c += ((uint32_t)((uint8_t)s[i + 8]));
    if (l >= 8)  b += ((uint32_t)((uint8_t)s[i + 7]))  << 24;
    if (l >= 7)  b += ((uint32_t)((uint8_t)s[i + 6]))  << 16;
    if (l >= 6)  b += ((uint32_t)((uint8_t)s[i + 5]))  << 8;
    if (l >= 5)  b += ((uint32_t)((uint8_t)s[i + 4]));
    if (l >= 4)  a += ((uint32_t)((uint8_t)s[i + 3]))  << 24;
    if (l >= 3)  a += ((uint32_t)((uint8_t)s[i + 2]))  << 16;
    if (l >= 2)  a += ((uint32_t)((uint8_t)s[i + 1]))  << 8;
    if (l >= 1)  a += ((uint32_t)((uint8_t)s[i]));
    if (l == 0)  return ((uint64_t)c) << 32;

    c ^= b; c -= rotl32(b, 14);
    a ^= c; a -= rotl32(c, 11);
    b ^= a; b -= rotl32(a, 25);
    c ^= b; c -= rotl32(b, 16);
    a ^= c; a -= rotl32(c, 4);
    b ^= a; b -= rotl32(a, 14);
    c ^= b; c -= rotl32(b, 24);

    return (((uint64_t)b) << 32) | (uint64_t)c;
}
