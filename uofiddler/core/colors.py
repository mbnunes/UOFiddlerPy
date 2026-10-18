"""
Color conversion utilities for 16-bit ARGB1555 / RGB555 used by Ultima Online.
Precomputes lookup tables for maximum conversion speed in Python.
"""

# Precomputed lookup tables for 5-bit to 8-bit color conversion (0..31 -> 0..255)
# In Ultima Online: val * 255 // 31 (or (val << 3) | (val >> 2))
COLOR_5_TO_8 = [int(i * 255 / 31) for i in range(32)]

# Precomputed 8-bit to 5-bit
COLOR_8_TO_5 = [int(i * 31 / 255) for i in range(256)]


def color16_to_rgba(c: int) -> tuple[int, int, int, int]:
    """
    Converts 16-bit ARGB1555 / RGB555 integer to (R, G, B, A).
    If bit 15 is 0 and c == 0, transparent (0, 0, 0, 0).
    """
    if c == 0:
        return (0, 0, 0, 0)
    r = COLOR_5_TO_8[(c >> 10) & 0x1F]
    g = COLOR_5_TO_8[(c >> 5) & 0x1F]
    b = COLOR_5_TO_8[c & 0x1F]
    return (r, g, b, 255)


def rgba_to_color16(r: int, g: int, b: int, a: int = 255) -> int:
    """
    Converts (r, g, b, a) to 16-bit ARGB1555 integer with high alpha bit set.
    """
    if a < 128:
        return 0
    r5 = COLOR_8_TO_5[min(255, max(0, r))]
    g5 = COLOR_8_TO_5[min(255, max(0, g))]
    b5 = COLOR_8_TO_5[min(255, max(0, b))]
    c = (r5 << 10) | (g5 << 5) | b5
    if c == 0:
        c = 1  # prevent opaque black from turning into transparent 0
    return c | 0x8000
