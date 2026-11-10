"""Strict local X4 MS-ADPCM/SBKR readers; preserve event tables and other chunks."""
import re
import struct
import math


def wave_chunks(raw):
    if len(raw)<12 or raw[:4] != b'RIFF' or raw[8:12] != b'WAVE':
        raise ValueError('Invalid RIFF length/header')
    end=struct.unpack_from('<I',raw,4)[0]+8
    # X4 appends its authoring timestamp/version outside the declared RIFF.
    if end!=len(raw) and not (end+28==len(raw) and raw[end:end+8]==b'tIME\x08\0\0\0' and raw[end+16:end+24]==b'ver.\x04\0\0\0'):
        raise ValueError('Invalid RIFF length/trailer')
    pos = 12
    rows = []
    while pos < len(raw):
        if pos + 8 > len(raw): raise ValueError('Truncated WAVE chunk')
        tag, size = struct.unpack_from('<4sI', raw, pos)
        start = pos + 8
        if start + size > len(raw): raise ValueError('Truncated WAVE data')
        rows.append((tag, start, size))
        pos = start + size + (size & 1)
    if pos != len(raw) or len({r[0] for r in rows}) != len(rows): raise ValueError('Unsupported WAVE chunks')
    return rows


def wave_info(raw):
    rows = {tag: (start, size) for tag, start, size in wave_chunks(raw)}
    if b'fmt ' not in rows or b'data' not in rows: raise ValueError('Missing WAVE format/data')
    at, size = rows[b'fmt ']
    if size != 50: raise ValueError('Unsupported X4 WAVE format length')
    codec, channels, rate, avg, block, bits, extra, samples, count = struct.unpack_from('<HHIIHHHHH', raw, at)
    if (codec, bits, extra, count) != (2, 4, 32, 7) or channels not in (1,2): raise ValueError('Unsupported MS ADPCM format')
    if block < 7*channels or samples != (block - 7*channels) * 2 // channels + 2 or not 8000 <= rate <= 96000: raise ValueError('Invalid ADPCM block/rate')
    if not 32<=samples<=512 or samples%32:raise ValueError('Unsupported XAudio2 ADPCM sample block')
    data, length = rows[b'data']
    if length % block: raise ValueError('Truncated MS ADPCM block')
    return {'rate': rate, 'channels':channels, 'block': block, 'samples_per_block': samples,
            'frames': length // block * samples, 'data_offset': data, 'data_size': length}


def mute_wave(raw):
    info = wave_info(raw)
    if info['channels']!=1:raise ValueError('Mute encoder is mono only')
    zero = b'\x00\x10\x00' + bytes(info['block'] - 3)
    result = bytearray(raw)
    start = info['data_offset']
    result[start:start + info['data_size']] = zero * (info['data_size'] // info['block'])
    return bytes(result)


def encode_native_mono(pcm,template,rate=48000):
    """Encode the native 128-sample / 70-byte MS-ADPCM block variant."""
    info=wave_info(template)
    if info['channels']!=1 or info['block']!=70:raise ValueError('Native mono template required')
    chunks={t:template[a:a+n] for t,a,n in wave_chunks(template)}
    fmt=bytearray(chunks[b'fmt ']);coefs=list(struct.iter_unpack('<hh',fmt[22:50]))
    adapt=(230,230,230,230,307,409,512,614,768,614,512,409,307,230,230,230)
    data=bytearray();values=[int(x) for x in pcm]
    values+=([0]*((-len(values))%128))
    for start in range(0,len(values),128):
        target=values[start:start+128];best=None
        for predictor,(a,b) in enumerate(coefs):
            estimates=[abs(target[i]-int((target[i-1]*a+target[i-2]*b)/256)) for i in range(2,18)]
            initial=max(16,round(sum(estimates)/len(estimates)))
            for factor in (.5,1,2):
                delta0=max(16,min(32767,round(initial*factor)));delta=delta0
                previous,older=target[1],target[0];error=0;nibbles=[]
                for wanted in target[2:]:
                    prediction=int((previous*a+older*b)/256)
                    q=max(-8,min(7,math.floor((wanted-prediction)/delta+.5)))
                    actual=max(-32768,min(32767,prediction+q*delta))
                    error+=(wanted-actual)**2;nibbles.append(q&15)
                    delta=max(16,adapt[q&15]*delta//256);older,previous=previous,actual
                if best is None or error<best[0]:best=(error,predictor,delta0,nibbles)
        _,predictor,delta,nibbles=best
        data.extend(struct.pack('<Bhhh',predictor,delta,target[1],target[0]))
        data.extend((nibbles[i]<<4)|nibbles[i+1] for i in range(0,126,2))
    struct.pack_into('<II',fmt,4,rate,rate*70//128)
    # Retain the native one-shot sampler descriptor and authoring trailer.
    content=b'WAVE'+b''.join(tag+struct.pack('<I',len(payload))+payload for tag,payload in ((b'fmt ',bytes(fmt)),(b'data',bytes(data)),(b'smpl',chunks[b'smpl'])))
    trailer=b''.join(tag+struct.pack('<I',len(chunks[tag]))+chunks[tag] for tag in (b'tIME',b'ver.'))
    result=b'RIFF'+struct.pack('<I',len(content))+content+trailer
    wave_info(result)
    return result


def bank_records(raw):
    if raw[:8] != b'SBKR\x04\0\0\0': raise ValueError('Unsupported SBKR')
    count = struct.unpack_from('<I', raw, 12)[0]
    matches = list(re.finditer(rb'X4\\sound[^\x00]+\x00', raw))
    if len(matches) != count or not matches or matches[0].start() not in (32, 44, 56): raise ValueError('Unexpected SBKR records')
    result = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw) - 8
        if end - m.end() != 80: raise ValueError('SBKR record width differs')
        record = raw[m.end():end]
        if record[:4] != bytes.fromhex('79f84d72'): raise ValueError('SBKR audio resource kind differs')
        result.append((m.group()[:-1].decode('ascii'), m.end(), record))
    return result


def sequence_events(raw):
    if raw[:8] != b'SRQR\x05\0\0\0': raise ValueError('Unsupported SRQR')
    count = struct.unpack_from('<I', raw, 8)[0]
    end = struct.unpack_from('<I', raw, 32)[0]
    if end != 52 + count * 132 or end + 4 > len(raw): raise ValueError('SRQR table bounds')
    result = []
    for i in range(count):
        at = 52 + i * 132
        result.append((struct.unpack_from('<H', raw, at)[0], raw[at + 2], raw[at:at + 132]))
    if len({r[0] for r in result}) != len(result): raise ValueError('Duplicate SRQR event')
    return result


def stream_records(raw):
    if raw[:8]!=b'STQR\x08\0\0\0' or len(raw)<344: raise ValueError('Unsupported voice STQR')
    if struct.unpack_from('<3I',raw,8)!=(8,16,1) or struct.unpack_from('<2I',raw,32)!=(56,344): raise ValueError('Voice STQR table differs')
    rows=[]
    for i in range(8):
        at=56+i*36
        ptr,size,frames,channels,rate,*_=struct.unpack_from('<9I',raw,at)
        if not 344<=ptr<len(raw) or not size or not frames or channels!=2 or rate!=48000: raise ValueError('Invalid voice stream record')
        end=raw.find(b'\0',ptr)
        if end<0: raise ValueError('Unterminated voice stream path')
        name=raw[ptr:end].decode('ascii')
        if not re.fullmatch(r'X4\\sound\\voice\\wav\\VOICE[1-5]\\(?:eng\\)?VOICE[1-5]_000[1-8](?:_eng)?',name): raise ValueError('Unexpected voice path')
        rows.append({'name':name,'size':size,'frames':frames,'rate':rate,'offset':at})
    return rows
