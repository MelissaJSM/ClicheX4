"""Verified X4 SNGW wrapper and bounded Ogg/Vorbis stream metadata.

Format reference: vgmstream src/meta/ogg_vorbis_streamfile.h (SNGW).
Independent implementation; only single logical Vorbis streams are accepted.
"""
import struct

TITLE_STREAMS = {
    'nativeDX10/X4/sound/bgm/wav/clear/BGM5_0001.sngw':
        'nativeDX10/X4/sound/bgm/x4_clear.stqr',
    'nativeDX10/X4/sound/bgm/wav/clear/eng/BGM5_U_00000.sngw':
        'nativeDX10/X4/sound/bgm/x4_clear_eng.stqr',
}


def ogg_crc(raw):
    crc = 0
    for value in raw:
        crc ^= value << 24
        for _ in range(8):
            crc = ((crc << 1) ^ (0x04C11DB7 if crc & 0x80000000 else 0)) & 0xffffffff
    return crc


def ogg_info(raw):
    pages = []
    packets = []
    packet = bytearray()
    at = 0
    serial = None
    last_granule = 0
    while at < len(raw):
        if at + 27 > len(raw) or raw[at:at+5] != b'OggS\0':
            raise ValueError('Invalid Ogg page')
        flags = raw[at+5]
        granule, page_serial, seq, crc = struct.unpack_from('<QIII', raw, at+6)
        n = raw[at+26]
        if not n or at+27+n > len(raw):
            raise ValueError('Truncated Ogg segment table')
        sizes = raw[at+27:at+27+n]
        end = at+27+n+sum(sizes)
        if end > len(raw):
            raise ValueError('Truncated Ogg payload')
        page = bytearray(raw[at:end])
        page[22:26] = bytes(4)
        if ogg_crc(page) != crc:
            raise ValueError('Ogg checksum mismatch')
        if serial is None:
            serial = page_serial
        if page_serial != serial or seq != len(pages) or flags & ~7:
            raise ValueError('Unsupported Ogg chaining/sequence')
        if bool(flags & 1) != bool(packet) or bool(flags & 2) != (at == 0):
            raise ValueError('Ogg packet continuation/BOS mismatch')
        if bool(flags & 4) != (end == len(raw)):
            raise ValueError('Ogg EOS mismatch')
        pos = at+27+n
        for size in sizes:
            packet.extend(raw[pos:pos+size])
            pos += size
            if size < 255:
                if len(packets) < 3:
                    packets.append(bytes(packet))
                packet.clear()
        if granule != 0xffffffffffffffff:
            if granule < last_granule:
                raise ValueError('Ogg granule goes backward')
            last_granule = granule
        pages.append((at, end))
        at = end
    if packet or len(packets) != 3 or not pages or not last_granule:
        raise ValueError('Incomplete Vorbis stream')
    if any(p[:7] != bytes([kind])+b'vorbis' for p, kind in zip(packets, (1,3,5))):
        raise ValueError('Not Vorbis')
    header = packets[0]
    if len(header) != 30 or struct.unpack_from('<I', header, 7)[0] != 0 or header[29] != 1:
        raise ValueError('Unsupported Vorbis identification')
    channels = header[11]
    rate = struct.unpack_from('<I', header, 12)[0]
    if channels != 2 or rate != 48000:
        raise ValueError('Expected X4 stereo 48 kHz stream')
    return {'frames': last_granule, 'channels': channels, 'rate': rate,
            'serial': serial, 'pages': pages}


def decode_sngw(raw):
    if len(raw) < 32 or raw[:4] != raw[16:20]:
        raise ValueError('Unsupported SNGW signature')
    key = raw[:4]
    decoded = bytearray(len(raw))
    for i, value in enumerate(raw):
        value ^= key[i % 4]
        decoded[i] = (value >> 4) | ((value & 15) << 4)
    decoded[:4] = b'OggS'
    result = bytes(decoded)
    ogg_info(result)
    return result


def encode_sngw(ogg, key):
    info = ogg_info(ogg)
    if len(key) != 4 or ogg[16:20] != bytes(4):
        raise ValueError('SNGW requires compatible Ogg serial bytes')
    result = bytearray(len(ogg))
    for i, value in enumerate(ogg):
        value = 0 if i < 4 else value
        result[i] = ((value >> 4) | ((value & 15) << 4)) ^ key[i % 4]
    result = bytes(result)
    if decode_sngw(result) != ogg:
        raise ValueError('SNGW encoding roundtrip failed')
    return result


def comment_packet(ogg):
    """Locate the complete short Vorbis comment on the first header page.

    Both native X4 streams and our encoder use this arrangement. Refuse a
    different arrangement rather than making assumptions about page splitting.
    """
    info = ogg_info(ogg)
    a,b = info['pages'][1]
    count = ogg[a+26]
    size = ogg[a+27]
    pos = a+27+count
    packet = ogg[pos:pos+size]
    if ogg[a+5] != 0 or size == 255 or packet[:7] != b'\x03vorbis':
        raise ValueError('Unsupported Vorbis comment arrangement')
    return a,b,pos,packet


def vorbis_comments(ogg):
    _,_,_,packet=comment_packet(ogg)
    if len(packet)<16:raise ValueError('Truncated Vorbis comment')
    vendor_size=struct.unpack_from('<I',packet,7)[0]
    pos=11+vendor_size
    if pos+4>=len(packet):raise ValueError('Invalid Vorbis vendor size')
    count=struct.unpack_from('<I',packet,pos)[0];pos+=4;comments=[]
    for _ in range(count):
        if pos+4>len(packet):raise ValueError('Truncated Vorbis comment size')
        size=struct.unpack_from('<I',packet,pos)[0];pos+=4
        if pos+size>=len(packet):raise ValueError('Truncated Vorbis comment text')
        comments.append(packet[pos:pos+size].decode('ascii'));pos+=size
    if packet[pos:]!=b'\x01':raise ValueError('Vorbis comment framing mismatch')
    return comments


def preserve_native_comments(ogg, original):
    a,b,pos,old=comment_packet(ogg)
    _,_,_,replacement=comment_packet(original)
    page=bytearray(ogg[a:pos]+replacement+ogg[pos+len(old):b])
    page[27]=len(replacement)
    page[22:26]=bytes(4)
    struct.pack_into('<I',page,22,ogg_crc(page))
    result=ogg[:a]+page+ogg[b:]
    if vorbis_comments(result)!=vorbis_comments(original):
        raise ValueError('Native metadata preservation failed')
    ogg_info(result)
    return result


def native_title_info(raw):
    ogg=decode_sngw(raw)
    tags=vorbis_comments(ogg)
    # RXC1 0xCCFCE6 rejects the stream unless Ver=0002 was parsed.
    required=('Ver=0002','LoopStart=-1','LoopEnd=-1')
    if any(tags.count(t)!=1 for t in required) or sum(t.startswith('Time=') for t in tags)!=1:
        raise ValueError('Missing or unsupported native X4 title stream metadata')
    return ogg_info(ogg)


def clear_records(raw):
    if len(raw) < 164 or raw[:8] != b'STQR\x08\0\0\0':
        raise ValueError('Unsupported clear STQR')
    if struct.unpack_from('<3I', raw, 8) != (3,6,0) or struct.unpack_from('<2I', raw, 32) != (56,164):
        raise ValueError('Clear STQR table differs')
    rows = []
    for i in range(3):
        at = 56+i*36
        ptr,size,frames,channels,rate,a,b,kind,version = struct.unpack_from('<9I',raw,at)
        if not 164 <= ptr < len(raw) or not size or not frames:
            raise ValueError('Invalid clear stream record')
        if (channels,rate,a,b,kind,version) != (2,48000,0xffffffff,0xffffffff,0x255d51cd,3):
            raise ValueError('Unsupported clear stream codec')
        end = raw.find(b'\0',ptr)
        if end < 0:
            raise ValueError('Unterminated clear stream path')
        name = raw[ptr:end].decode('ascii')
        expected = (f'X4\\sound\\bgm\\wav\\clear\\BGM5_000{i+1}',
                    f'X4\\sound\\bgm\\wav\\clear\\eng\\BGM5_U_0000{i}')
        if name not in expected:
            raise ValueError('Unexpected clear stream path')
        rows.append({'name': name, 'size': size, 'frames': frames, 'rate': rate, 'offset': at})
    return rows
