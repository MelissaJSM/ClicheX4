"""입력을 rb로만 읽고 새 work/discovery 하위에 조사 JSON을 기록한다.

그래픽 추출기나 패처가 아니다. ISO9660 읽기는 단일 MODE2/2352 데이터
트랙의 Form1 파일에 한정한다. EDC/ECC, 게임 실행, 프레임 복원은 검사하지 않는다.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def file_info(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'path': str(path.resolve()), 'size': path.stat().st_size, 'sha256': digest}


def psx_arc(data):
    if len(data) < 2048:
        raise ValueError('PSX ARC header truncated')
    count, size = struct.unpack_from('<II', data)
    if size != len(data) or 8 + count * 8 > 2048:
        raise ValueError('PSX ARC header mismatch')
    pos, entries = 2048, []
    for i in range(count):
        kind, length = struct.unpack_from('<II', data, 8 + i * 8)
        if pos + length > size:
            raise ValueError('PSX ARC entry out of bounds')
        entries.append({'index': i, 'type': hex(kind), 'offset': pos,
                        'size': length, 'sha256': sha256(data[pos:pos+length])})
        pos += (length + 2047) // 2048 * 2048
    if pos != size:
        raise ValueError('PSX ARC padded size mismatch')
    return entries


def mt_arc(data):
    if len(data) < 8 or data[:4] != b'ARC\0':
        raise ValueError('MT ARC magic/header mismatch')
    version, count = struct.unpack_from('<HH', data, 4)
    end = 8 + count * 80
    if end > len(data):
        raise ValueError('MT ARC directory truncated')
    entries, ranges = [], []
    for i in range(count):
        rec = data[8+i*80:8+(i+1)*80]
        name = rec[:64].split(b'\0')[0].decode('ascii')
        kind, length, size_flags, offset = struct.unpack_from('<IIII', rec, 64)
        size = size_flags & 0x1fffffff
        if offset < end or offset + length > len(data) or size > 64*1024*1024:
            raise ValueError('MT ARC entry out of bounds')
        decoder = zlib.decompressobj()
        payload = decoder.decompress(data[offset:offset+length], size + 1)
        if len(payload) != size or not decoder.eof or decoder.unused_data:
            raise ValueError('MT ARC zlib length/stream mismatch')
        ranges.append((offset, offset+length))
        entries.append({'index': i, 'name': name, 'type_hash': hex(kind),
                        'offset': offset, 'compressed_size': length, 'size': size,
                        'flags': hex(size_flags >> 29), 'magic_hex': payload[:16].hex(),
                        'sha256': sha256(payload)})
        if payload[:4] == b'TEX\0' and len(payload) >= 20:
            packed = struct.unpack_from('<I', payload, 8)[0]
            entries[-1]['tex_header'] = {
                'format_code': payload[13], 'width': (packed >> 6) & 8191,
                'height': packed >> 19, 'mip_count': packed & 63,
                'pixel_offset': struct.unpack_from('<I', payload, 16)[0]}
    ranges.sort()
    if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise ValueError('MT ARC entries overlap')
    return {'version': version, 'entries': entries}


class DiscReader:
    def __init__(self, stream, size):
        if size % 2352:
            raise ValueError('BIN is not a multiple of 2352')
        self.stream, self.sectors = stream, size // 2352

    def scan_headers(self):
        self.stream.seek(0)
        counts = Counter()
        for _ in range(self.sectors):
            raw = self.stream.read(2352)
            if raw[:12] != b'\0'+b'\xff'*10+b'\0':
                counts['no_data_sync'] += 1
            elif raw[15] == 2:
                counts['mode2_form2' if raw[18] & 32 else 'mode2_form1'] += 1
                if raw[16:20] != raw[20:24]:
                    counts['subheader_mismatch'] += 1
            else:
                counts['other_mode_'+str(raw[15])] += 1
        return dict(counts)

    def sector(self, lba):
        if not 0 <= lba < self.sectors:
            raise ValueError('LBA out of bounds')
        self.stream.seek(lba * 2352)
        raw = self.stream.read(2352)
        if raw[:12] != b'\0'+b'\xff'*10+b'\0' or raw[15] != 2:
            raise ValueError('Not a Mode2 sector')
        if raw[16:20] != raw[20:24] or raw[18] & 0x20:
            raise ValueError('Expected duplicated XA header and Form1')
        return raw[24:2072]

    def read(self, lba, size):
        if size < 0 or size > 16*1024*1024:
            raise ValueError('Discovery read size limit exceeded')
        return b''.join(self.sector(lba+i) for i in range((size+2047)//2048))[:size]

    @staticmethod
    def record(data):
        if len(data) < 34 or data[0] != len(data) or 33+data[32] > len(data):
            raise ValueError('Invalid ISO directory record')
        lba, size = struct.unpack_from('<I', data, 2)[0], struct.unpack_from('<I', data, 10)[0]
        if lba != struct.unpack_from('>I', data, 6)[0] or size != struct.unpack_from('>I', data, 14)[0]:
            raise ValueError('ISO endian copies mismatch')
        return {'name': data[33:33+data[32]].decode('ascii'), 'lba': lba,
                'size': size, 'directory': bool(data[25] & 2)}

    def inspect(self):
        pvd = self.sector(16)
        if pvd[:7] != b'\x01CD001\x01' or struct.unpack_from('<H', pvd, 128)[0] != 2048:
            raise ValueError('Unsupported ISO PVD')
        root = self.record(pvd[156:156+pvd[156]])
        entries, seen = [], set()
        def walk(rec, parent):
            if rec['lba'] in seen or len(seen) > 1024:
                raise ValueError('ISO directory cycle/limit')
            seen.add(rec['lba'])
            data = self.read(rec['lba'], rec['size'])
            pos = 0
            while pos < len(data):
                length = data[pos]
                if not length:
                    pos = (pos//2048+1)*2048
                    continue
                child = self.record(data[pos:pos+length]); pos += length
                if child['name'] in ('\0', '\x01'):
                    continue
                child['path'] = parent+'/'+child['name']
                entries.append(child)
                if child['directory']:
                    walk(child, child['path'])
        walk(root, '')
        selected = []
        for rec in entries:
            name = rec['name']
            if not rec['directory'] and (name == 'SYSTEM.CNF;1' or re.match(r'SL[UP][SS]_\d+\.\d+;1', name) or re.match(r'PL0[0-2].*\.ARC;1', name)):
                payload = self.read(rec['lba'], rec['size'])
                item = {**rec, 'sha256': sha256(payload)}
                if name == 'SYSTEM.CNF;1':
                    item['text'] = payload.decode('ascii').rstrip('\0')
                elif name.endswith('.ARC;1'):
                    try:
                        item['entries'] = psx_arc(payload)
                    except ValueError as error:
                        item['arc_parse_error'] = str(error)
                        item['header_hex'] = payload[:32].hex()
                else:
                    item['magic'] = payload[:8].decode('ascii', errors='replace')
                    item['load_address'] = hex(struct.unpack_from('<I', payload, 24)[0])
                selected.append(item)
        return {'volume_id': pvd[40:72].decode('ascii').strip(), 'sectors': self.sectors,
                'volume_blocks': struct.unpack_from('<I', pvd, 80)[0],
                'files': entries, 'selected': selected, 'sector_headers': self.scan_headers()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steam-root', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = {'created_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
              'root': str(root), 'discs': [], 'cues': [], 'references': [], 'tools': [], 'steam': {}}
    for path in sorted(root.glob('*.bin')):
        info = file_info(path)
        with path.open('rb') as stream:
            info.update(DiscReader(stream, info['size']).inspect())
        report['discs'].append(info)
    for path in sorted(root.glob('*.cue')):
        info = file_info(path); info['text'] = path.read_text(encoding='utf-8-sig')
        info['file_references'] = [{'name': n, 'exists': (path.parent/n).is_file()}
                                   for n in re.findall(r'FILE\s+"([^"]+)"', info['text'])]
        report['cues'].append(info)
    from PIL import Image, __version__ as pillow_version
    report['pillow'] = pillow_version
    for path in sorted((root/'character').rglob('*.webp')):
        info = file_info(path)
        with Image.open(path) as picture:
            picture.load()
            info.update(width=picture.width, height=picture.height, mode=picture.mode, format=picture.format)
        report['references'].append(info)
    for relative in ['ePSXe2018/ePSXe.exe', 'ePSXe2018/bios/SCPH1001.BIN']:
        report['tools'].append(file_info(root/relative))
    steam = args.steam_root.resolve()
    report['steam']['root'] = str(steam)
    report['steam']['executable'] = file_info(steam/'RXC1.exe')
    manifest = steam.parents[1]/'appmanifest_743890.acf'
    text = manifest.read_text(encoding='utf-8')
    report['steam']['manifest'] = {k: re.findall('"'+k+'"\\s+"([^"]*)"', text)
                                   for k in ['appid','name','installdir','buildid','StateFlags','language']}
    report['steam']['archives'] = []
    for path in sorted((steam/'nativeDX10/X4/romPC').glob('*.arc')):
        info = file_info(path)
        if path.name.startswith('pl0'):
            info.update(mt_arc(path.read_bytes()))
        report['steam']['archives'].append(info)
    output_base = root/'work'/'discovery'
    if not output_base.resolve().is_relative_to(root):
        raise ValueError('Output escaped project root')
    output = output_base/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True, exist_ok=False)
    with (output/'inventory.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(output/'inventory.json')
    for disc in report['discs']:
        print(Path(disc['path']).name, disc['sha256'], disc['sectors'])
        for rec in disc['selected']:
            print(rec['path'], rec['lba'], rec['size'], rec['sha256'])
    print('Steam', report['steam']['manifest'])


if __name__ == '__main__':
    main()
