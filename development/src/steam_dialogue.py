"""Korean DAT4/font conversion and bounded native X4 glyph-emitter changes."""
import struct

from .steam_player import unpack_indices

SPACE = 1023
FONT_FIRST = 512


def decode_dat4(data):
    if len(data) < 12 or data[:8] != b'DAT4'+struct.pack('<I', 1):
        raise ValueError('Expected DAT4 version 1')
    n = struct.unpack_from('<I', data, 8)[0]
    if n not in (49, 55):
        raise ValueError('Unexpected X4 message count')
    pos = 12
    messages = []
    for _ in range(n):
        if pos+4 > len(data):
            raise ValueError('Truncated DAT4 count')
        count = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        if not 0 < count < 4096 or pos+count*2 > len(data):
            raise ValueError('Truncated DAT4 message')
        messages.append(list(struct.unpack_from('<'+'H'*count, data, pos)))
        pos += count*2
    if pos != len(data):
        raise ValueError('Unexpected DAT4 tail')
    return messages


def encode_dat4(messages):
    data = b'DAT4'+struct.pack('<II', 1, len(messages))
    for message in messages:
        data += struct.pack('<I', len(message))+struct.pack('<'+'H'*len(message), *message)
    if decode_dat4(data) != messages:
        raise ValueError('DAT4 roundtrip differs')
    return data


def korean_source(data, count, font):
    if data[128:132] != b'KOR1' or count not in (49, 55):
        raise ValueError('Expected accepted PS1 Korean text')
    font_offset, glyph_count, text_end = struct.unpack_from('<III', data, 132)
    if not 144 <= text_end <= font_offset <= len(data) or font_offset+glyph_count*18 > len(data):
        raise ValueError('Korean source boundaries invalid')
    offsets = list(struct.unpack_from('<'+'H'*count, data))
    if offsets != sorted(set(offsets)) or offsets[0] != 144 or offsets[-1] >= text_end:
        raise ValueError('Korean message directory invalid')
    messages = []
    atlas = unpack_indices(font)
    glyphs = {}
    for i, lo in enumerate(offsets):
        hi = offsets[i+1] if i+1 < count else text_end
        words = list(struct.unpack('<'+'H'*((hi-lo)//2), data[lo:hi]))
        ends = [j for j, word in enumerate(words) if word & 0x8000]
        if len(ends) != 1 or any(words[ends[0]+1:]):
            raise ValueError('Message terminator or padding differs')
        words = words[:ends[0]+1]
        messages.append(words)
        for word in words:
            code = word & 2047
            if code == 2047 or code in glyphs:
                continue
            if code < 256:
                x, y = code%16*16, code//16*16
                pixels = b''.join(atlas[(y+r)*256+x:(y+r)*256+x+16] for r in range(16))
            else:
                if code-256 >= glyph_count:
                    raise ValueError('Korean glyph index exceeds dictionary')
                bits = int.from_bytes(data[font_offset+(code-256)*18:font_offset+(code-255)*18], 'little')
                pixels = bytearray(256)
                for y in range(12):
                    for x in range(12):
                        if bits >> (y*12+x) & 1:
                            pixels[(y+2)*16+x] = 14
                pixels = bytes(pixels)
            if len(pixels) != 256:
                raise ValueError('Korean tile is incomplete')
            glyphs[code] = pixels
    return messages, glyphs


def remap_messages(messages, glyphs, mapping):
    converted = []
    for words in messages:
        result = []
        for word in words:
            code = word & 2047
            tile = SPACE if code == 2047 else mapping[glyphs[code]]
            if tile > SPACE:
                raise ValueError('Dialogue atlas address overflow')
            new = (word & 0xf800) | tile
            if new & 0xf800 != word & 0xf800:
                raise ValueError('Page/side/typewriter control changed')
            result.append(new)
        converted.append(result)
    return converted


def runtime_patches():
    # All addresses are in the verified, normally loaded RXC1 X4 engine.
    # No on-disk executable changes, executable loader changes, or new threads.
    start = 0x98312c
    old = bytes.fromhex('8bcdc644b00400e8687c01008bcf0fbff0e86ed900008bcd668bd8e834c3feff8bcd885cb005')
    new = bytearray()
    def emit(hexbytes):
        new.extend(bytes.fromhex(hexbytes))
    def call(address):
        new.extend(b'\xe8'+struct.pack('<i', address-(start+len(new)+5)))
    # ESI already contains the visible glyph index. Omit its redundant getter
    # to fit page+tile stores into the original 38-byte block.
    emit('8bcf'); call(0x990ab0)       # current encoded word
    emit('668bd88bcd'); call(0x96f480) # BX=word, EAX=quad array
    emit('885cb005')                  # low 8 bits -> tile
    emit('8bd3c1ea0880e2038854b004')    # page=(word>>8)&3, no control bits
    emit('8bcd')                      # same ECX for the next native getter
    if len(new) > len(old):
        raise ValueError('Inline dialogue change exceeds its original block')
    new.extend(b'\x90'*(len(old)-len(new)))
    return [
        ('dialogue_space_mask_initial', 0x982f9f, bytes.fromhex('bbff010000'), bytes.fromhex('bbff030000')),
        ('dialogue_space_mask_loop', 0x9831b5, bytes.fromhex('bbff010000'), bytes.fromhex('bbff030000')),
        ('dialogue_glyph_page_and_tile', start, old, bytes(new)),
        ('dialogue_korean_advance', 0x98320e,
         bytes.fromhex('488bcff7d81bc083e0fc83c010'),
         bytes.fromhex('8bcfb80c000000909090909090')),
    ]
