"""
Mythic decompressor (Move-To-Front + frequency dictionary decoding).
Used for CompressionFlag.Mythic (flag == 3) inside modern UOP files and compressed cliloc files.
"""

import struct


class MythicDecompress:
    HEADER_XOR_KEY = 0x8E2C9A3D
    FREQUENCY_HEADER_SIZE = 1024  # 256 32-bit ints

    @classmethod
    def decompress(cls, buffer: bytes) -> bytes:
        if len(buffer) < 4:
            return b""

        raw_len = struct.unpack_from("<I", buffer, 0)[0]
        data_len = raw_len ^ cls.HEADER_XOR_KEY

        mtf_input = buffer[4:]
        mtf_decoded = cls._decode_mtf(mtf_input)
        return cls._internal_decompress(mtf_decoded, data_len)

    @staticmethod
    def _decode_mtf(input_bytes: bytes) -> bytearray:
        symbols = bytearray(range(256))
        output = bytearray(len(input_bytes))

        for i, ind in enumerate(input_bytes):
            val = symbols[ind]
            output[i] = val
            # Move to front
            if ind > 0:
                del symbols[ind]
                symbols.insert(0, val)

        return output

    @classmethod
    def _internal_decompress(cls, input_data: bytearray, expected_len: int) -> bytes:
        if len(input_data) < cls.FREQUENCY_HEADER_SIZE:
            return b""

        # Read 256 ints from frequency header
        partial_input = list(struct.unpack_from("<256i", input_data, 0)) + [0] * (256 * 2)

        total_sum = sum(partial_input[:256])
        if total_sum == 0:
            return b""

        symbol_table = bytearray(range(256))
        frequency = bytearray(256)

        # Count non-zero frequencies
        non_zero_count = sum(1 for x in partial_input[:256] if x != 0)

        # Frequency sorting
        tmp = list(partial_input[:256])
        for i in range(256):
            max_val = 0
            max_idx = 0
            for j in range(256):
                if tmp[j] > max_val:
                    max_idx = j
                    max_val = tmp[j]
            if max_val == 0:
                break
            frequency[i] = max_idx
            tmp[max_idx] = 0

        # Build symbol table and partial input offsets
        m = 0
        for i in range(non_zero_count):
            freq = frequency[i]
            symbol_table[input_data[m + cls.FREQUENCY_HEADER_SIZE]] = freq
            partial_input[freq + 256] = m + 1
            m += partial_input[freq]
            partial_input[freq + 512] = m

        val = symbol_table[0]
        destination = bytearray(total_sum)
        count = 0

        while count < total_sum:
            destination[count] = val
            first_val = partial_input[val + 256]

            if first_val < partial_input[val + 512]:
                idx = input_data[first_val + cls.FREQUENCY_HEADER_SIZE]
                partial_input[val + 256] += 1

                if idx != 0:
                    # ShiftLeft up to idx
                    for k in range(idx):
                        symbol_table[k] = symbol_table[k + 1]
                    symbol_table[idx] = val
                    val = symbol_table[0]
            elif non_zero_count > 0:
                non_zero_count -= 1
                for k in range(non_zero_count):
                    symbol_table[k] = symbol_table[k + 1]
                val = symbol_table[0]

            count += 1

        return bytes(destination[:expected_len]) if expected_len > 0 else bytes(destination)
