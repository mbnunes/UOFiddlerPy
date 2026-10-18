"""
Bob Jenkins lookup3 (hashlittle2) and Adler32 hash implementations for Ultima Online Mythic Package (.uop) files.
"""

def rotl(x: int, k: int) -> int:
    return ((x << k) | (x >> (32 - k))) & 0xFFFFFFFF


def hash_file_name(s: str) -> int:
    """
    Calculates a UOP entry 64-bit hash from its entry path name.
    Matches Bob Jenkins' lookup3 (hashlittle2 variant) used by the Ultima Online client.
    """
    length = len(s)
    a = b = c = (length + 0xDEADBEEF) & 0xFFFFFFFF
    i = 0
    l = length

    while l > 12:
        a = (a + (ord(s[i]) | (ord(s[i + 1]) << 8) | (ord(s[i + 2]) << 16) | (ord(s[i + 3]) << 24))) & 0xFFFFFFFF
        b = (b + (ord(s[i + 4]) | (ord(s[i + 5]) << 8) | (ord(s[i + 6]) << 16) | (ord(s[i + 7]) << 24))) & 0xFFFFFFFF
        c = (c + (ord(s[i + 8]) | (ord(s[i + 9]) << 8) | (ord(s[i + 10]) << 16) | (ord(s[i + 11]) << 24))) & 0xFFFFFFFF

        a = (a - c) & 0xFFFFFFFF; a ^= rotl(c, 4);  c = (c + b) & 0xFFFFFFFF
        b = (b - a) & 0xFFFFFFFF; b ^= rotl(a, 6);  a = (a + c) & 0xFFFFFFFF
        c = (c - b) & 0xFFFFFFFF; c ^= rotl(b, 8);  b = (b + a) & 0xFFFFFFFF
        a = (a - c) & 0xFFFFFFFF; a ^= rotl(c, 16); c = (c + b) & 0xFFFFFFFF
        b = (b - a) & 0xFFFFFFFF; b ^= rotl(a, 19); a = (a + c) & 0xFFFFFFFF
        c = (c - b) & 0xFFFFFFFF; c ^= rotl(b, 4);  b = (b + a) & 0xFFFFFFFF
        i += 12
        l -= 12

    if l == 12: c = (c + (ord(s[i + 11]) << 24)) & 0xFFFFFFFF
    if l >= 11: c = (c + (ord(s[i + 10]) << 16)) & 0xFFFFFFFF
    if l >= 10: c = (c + (ord(s[i + 9])  << 8))  & 0xFFFFFFFF
    if l >= 9:  c = (c + ord(s[i + 8]))          & 0xFFFFFFFF
    if l >= 8:  b = (b + (ord(s[i + 7])  << 24)) & 0xFFFFFFFF
    if l >= 7:  b = (b + (ord(s[i + 6])  << 16)) & 0xFFFFFFFF
    if l >= 6:  b = (b + (ord(s[i + 5])  << 8))  & 0xFFFFFFFF
    if l >= 5:  b = (b + ord(s[i + 4]))          & 0xFFFFFFFF
    if l >= 4:  a = (a + (ord(s[i + 3])  << 24)) & 0xFFFFFFFF
    if l >= 3:  a = (a + (ord(s[i + 2])  << 16)) & 0xFFFFFFFF
    if l >= 2:  a = (a + (ord(s[i + 1])  << 8))  & 0xFFFFFFFF
    if l >= 1:  a = (a + ord(s[i]))              & 0xFFFFFFFF
    if l == 0:  return (c << 32) & 0xFFFFFFFFFFFFFFFF

    c ^= b; c = (c - rotl(b, 14)) & 0xFFFFFFFF
    a ^= c; a = (a - rotl(c, 11)) & 0xFFFFFFFF
    b ^= a; b = (b - rotl(a, 25)) & 0xFFFFFFFF
    c ^= b; c = (c - rotl(b, 16)) & 0xFFFFFFFF
    a ^= c; a = (a - rotl(c, 4))  & 0xFFFFFFFF
    b ^= a; b = (b - rotl(a, 14)) & 0xFFFFFFFF
    c ^= b; c = (c - rotl(b, 24)) & 0xFFFFFFFF

    return ((b << 32) | c) & 0xFFFFFFFFFFFFFFFF


def hash_adler32(data: bytes) -> int:
    """
    Computes Adler32 checksum.
    """
    a = 1
    b = 0
    for byte in data:
        a = (a + byte) % 65521
        b = (b + a) % 65521
    return ((b << 16) | a) & 0xFFFFFFFF
