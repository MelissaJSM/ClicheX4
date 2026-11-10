"""Bounded single-mip MT textures used by the local Collection frontend.

Format 0x2a stores Cr, alpha, Cb, Y in BC3 channels. Original shader constants
in RXC2ShaderPackage.mfx at 0x37e58..0x37e74 are 1.402, .34414, .71414, 1.772
and .5 offsets. The original X4 banner provides an independent visual check.
"""
import io
import struct

import numpy as np
from PIL import Image


def layout(raw):
    if len(raw) < 20 or raw[:8] != bytes.fromhex('54455800a1800020'):
        raise ValueError('Unsupported frontend texture header')
    packed = struct.unpack_from('<I', raw, 8)[0]
    width, height, mip = (packed >> 6) & 8191, packed >> 19, packed & 63
    fmt = raw[13]
    if mip not in (1, 10) or fmt not in (0x13, 0x17, 0x2a):
        raise ValueError('Unsupported frontend texture format/mips')
    if raw[12] != 1 or raw[14:16] != b'\x01\0':
        raise ValueError('Unsupported texture layout')
    block = 8 if fmt == 0x13 else 16
    offsets = struct.unpack_from('<' + 'I' * mip, raw, 16)
    cursor = 16 + 4 * mip
    levels = []
    for i, offset in enumerate(offsets):
        w, h = max(1, width >> i), max(1, height >> i)
        size = ((w + 3) // 4) * ((h + 3) // 4) * block
        if offset != cursor:
            raise ValueError('Texture mip directory mismatch')
        levels.append((w, h, offset, size))
        cursor += size
    if not width or not height or cursor != len(raw):
        raise ValueError('Texture extent/length mismatch')
    return width, height, fmt, block, levels


def info(raw):
    width, height, fmt, block, levels = layout(raw)
    if len(levels) != 1 or width % 4 or height % 4:
        raise ValueError('Region editing requires one aligned mip')
    return width, height, fmt, block


def decode(raw):
    width, height, fmt, _, levels = layout(raw)
    _, _, offset, size = levels[0]
    im = Image.frombytes('RGBA', (width, height), raw[offset:offset+size], 'bcn',
                         (1, 'DXT1') if fmt == 0x13 else (3, 'DXT5'))
    if fmt != 0x2a:
        return im
    a = np.asarray(im, dtype=np.float64)
    y, cr, cb = a[:, :, 3], a[:, :, 0] - 127.5, a[:, :, 2] - 127.5
    rgba = np.stack((y + 1.402 * cr, y - .34414 * cb - .71414 * cr,
                     y + 1.772 * cb, a[:, :, 1]), axis=2)
    return Image.fromarray(np.rint(rgba).clip(0, 255).astype(np.uint8))


def encode_blocks(im, fmt):
    im = im.convert('RGBA')
    if im.width % 4 or im.height % 4:
        raise ValueError('BC texture patches must be block aligned')
    if fmt == 0x2a:
        rgba = np.asarray(im, dtype=np.float64)
        # Invert the observed shader matrix, including its exact coefficients.
        matrix = np.array(((1, 1.402, 0), (1, -.71414, -.34414), (1, 0, 1.772)))
        ycc = rgba[:, :, :3] @ np.linalg.inv(matrix).T
        encoded = np.stack((ycc[:, :, 1] + 127.5, rgba[:, :, 3],
                            ycc[:, :, 2] + 127.5, ycc[:, :, 0]), axis=2)
        im = Image.fromarray(np.rint(encoded).clip(0, 255).astype(np.uint8))
    elif fmt not in (0x13, 0x17):
        raise ValueError('Unsupported texture compression')
    stream = io.BytesIO()
    im.save(stream, format='DDS', pixel_format='DXT1' if fmt == 0x13 else 'DXT5')
    dds = stream.getvalue()
    if dds[:4] != b'DDS ' or dds[84:88] != (b'DXT1' if fmt == 0x13 else b'DXT5'):
        raise ValueError('Unexpected DDS encoder output')
    packed = dds[128:]
    if fmt == 0x2a:
        # Pillow's fast alpha fit insets endpoints and visibly crushes bright
        # ink/highlights when this channel is luminance. Choose the lower-error
        # BC3 fit explicitly; the RGB/color blocks stay with the DDS encoder.
        a = np.asarray(im)[:, :, 3]
        blocks = a.reshape(im.height//4, 4, im.width//4, 4).transpose(0, 2, 1, 3).reshape(-1, 16)
        result = np.frombuffer(packed, np.uint8).reshape(-1, 16).copy()
        for start in range(0, len(blocks), 4096):
            pixels = blocks[start:start+4096].astype(np.int32)
            ordered = np.sort(pixels, axis=1)
            best_error = np.full(len(pixels), np.inf)
            best = np.zeros((len(pixels), 8), np.uint8)
            for low in (0, 1, 3):
                for high in (15, 14, 12):
                    for six in (False, True):
                        lo, hi = ordered[:, low], ordered[:, high]
                        a0, a1 = (lo, hi) if six else (hi, lo)
                        ramp = np.empty((len(pixels), 8), np.int32)
                        ramp[:, 0], ramp[:, 1] = a0, a1
                        if six:
                            for k in range(1, 5):ramp[:, k+1] = ((5-k)*a0+k*a1)//5
                            ramp[:, 6], ramp[:, 7] = 0, 255
                        else:
                            for k in range(1, 7):ramp[:, k+1] = ((7-k)*a0+k*a1)//7
                        delta = (pixels[:, :, None] - ramp[:, None, :]) ** 2
                        indices = delta.argmin(axis=2)
                        errors = delta.min(axis=2).sum(axis=1)
                        use = errors < best_error
                        if not use.any():continue
                        bits = np.zeros(len(pixels), np.uint64)
                        for k in range(16):bits |= indices[:, k].astype(np.uint64) << (3*k)
                        candidate = np.empty((len(pixels), 8), np.uint8)
                        candidate[:, 0], candidate[:, 1] = a0, a1
                        for k in range(6):candidate[:, k+2] = ((bits >> (8*k)) & 255).astype(np.uint8)
                        best[use], best_error[use] = candidate[use], errors[use]
            result[start:start+len(pixels), :8] = best
        packed = result.tobytes()
    return packed


def replace_region(raw, rect, image):
    width, height, fmt, block = info(raw)
    x0, y0, x1, y1 = rect
    if (not 0 <= x0 < x1 <= width or not 0 <= y0 < y1 <= height
            or any(v % 4 for v in rect) or image.size != (x1 - x0, y1 - y0)):
        raise ValueError('Invalid replacement rectangle')
    packed = encode_blocks(image, fmt)
    stride = (x1 - x0) // 4 * block
    if len(packed) != stride * ((y1 - y0) // 4):
        raise ValueError('Encoded texture size mismatch')
    result = bytearray(raw)
    intervals = []
    for row in range((y1 - y0) // 4):
        start = 20 + ((y0 // 4 + row) * (width // 4) + x0 // 4) * block
        result[start:start + stride] = packed[row * stride:(row + 1) * stride]
        intervals.append((start, start + stride))
    cursor = 0
    for start, end in intervals:
        if raw[cursor:start] != result[cursor:start]:
            raise ValueError('Non-target blocks changed')
        cursor = end
    if raw[cursor:] != result[cursor:]:
        raise ValueError('Texture tail changed')
    info(result)
    return bytes(result)


def replace_mipchain(raw, image):
    width, height, fmt, block, levels = layout(raw)
    if image.size != (width, height) or fmt != 0x17 or len(levels) != 10:
        raise ValueError('Unsupported full-mip replacement')
    result = bytearray(raw)
    for w, h, offset, size in levels:
        mip = image.resize((w, h), Image.Resampling.LANCZOS).convert('RGBA')
        # Last levels have dimensions smaller than a BC block. Replicate edge
        # texels into unused block cells; the original header keeps exact sizes.
        a = np.asarray(mip)
        a = np.pad(a, ((0, (-h) % 4), (0, (-w) % 4), (0, 0)), mode='edge')
        packed = encode_blocks(Image.fromarray(a), fmt)
        if len(packed) != size:
            raise ValueError('Mipmap encoded length mismatch')
        result[offset:offset+size] = packed
    if raw[:levels[0][2]] != result[:levels[0][2]]:
        raise ValueError('Mipmap metadata changed')
    layout(result)
    return bytes(result)
