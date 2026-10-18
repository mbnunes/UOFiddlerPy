#ifndef UO_CORE_H
#define UO_CORE_H

#include <stdint.h>
#include <stddef.h>

#if defined(_WIN32) || defined(__CYGWIN__)
  #ifdef BUILDING_UO_CORE
    #define UO_API __declspec(dllexport)
  #else
    #define UO_API __declspec(dllimport)
  #endif
#else
  #if defined(__GNUC__) && __GNUC__ >= 4
    #define UO_API __attribute__ ((visibility ("default")))
  #else
    #define UO_API
  #endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

// 1. Color conversion
UO_API uint32_t uo_color16_to_rgba(uint16_t c);
UO_API uint16_t uo_rgba_to_color16(uint8_t r, uint8_t g, uint8_t b, uint8_t a);

// 2. Art decoders
UO_API int uo_decode_static(const uint8_t* raw_data, size_t data_len, uint32_t* out_pixels, int max_w, int max_h, int* out_w, int* out_h);
UO_API int uo_decode_land(const uint8_t* raw_data, size_t data_len, uint32_t* out_pixels);

// 3. Hue application
UO_API void uo_apply_hue(uint32_t* pixels, int count, const uint32_t* palette_32, int only_gray);

// 4. Mythic MTF decompression
UO_API int uo_decompress_mythic(const uint8_t* src, size_t src_len, uint8_t* dst, size_t max_dst_len, size_t* out_decompressed_len);

// 5. UOP 64-bit Jenkins hash
UO_API uint64_t uo_hash_file_name(const char* s, size_t len);

#ifdef __cplusplus
}
#endif

#endif // UO_CORE_H
