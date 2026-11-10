"""2352-byte Mode2 Form1 섹터의 EDC와 P/Q 검사·재생성만 지원한다.

주소/모드/서브헤더는 유지한다. Form2나 ISO 재배치는 지원하지 않는다.
"""
import struct


def gf_product(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        a <<= 1
        if a & 256:
            a ^= 0x11d
        b >>= 1
    return result


DOUBLE = [gf_product(i,2) for i in range(256)]
INVERSE_THREE = next(i for i in range(256) if gf_product(i,3) == 1)
DIVIDE_THREE = [gf_product(i,INVERSE_THREE) for i in range(256)]


def edc(data):
    value = 0
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xd8018001 if value & 1 else 0)
    return value


def parity(data, columns, rows, column_stride, row_stride):
    if len(data) != columns*rows:
        raise ValueError('Invalid parity matrix size')
    result = bytearray(columns*2)
    for column in range(columns):
        initial = (column//2)*column_stride+(column & 1)
        total = weighted = 0
        for row in range(rows):
            value = data[(initial+row*row_stride) % len(data)]
            total ^= value
            weighted = DOUBLE[weighted ^ value]
        result[column] = DIVIDE_THREE[DOUBLE[weighted] ^ total]
        result[column+columns] = result[column] ^ total
    return result


def validate_layout(raw):
    if len(raw) != 2352 or raw[:12] != b'\0'+b'\xff'*10+b'\0' or raw[15] != 2:
        raise ValueError('Expected raw Mode2 sector')
    if raw[16:20] != raw[20:24] or raw[18] & 32:
        raise ValueError('Expected duplicated Form1 subheader')


def rebuild_checks(raw):
    validate_layout(raw)
    result = bytearray(raw)
    result[2072:2076] = struct.pack('<I',edc(result[16:2072]))
    # Mode2 parity uses a zero address/mode field; preserve the real header.
    basis = bytes(4)+result[16:2076]
    result[2076:2248] = parity(basis,86,24,2,86)
    result[2248:2352] = parity(basis+result[2076:2248],52,43,86,88)
    return bytes(result)


def validate_checks(raw):
    if rebuild_checks(raw) != raw:
        raise ValueError('Sector EDC/ECC mismatch')


def replace_payload(raw, payload):
    validate_checks(raw)
    if len(payload) != 2048:
        raise ValueError('Payload size must stay 2048')
    return rebuild_checks(raw[:24]+payload+raw[2072:])
