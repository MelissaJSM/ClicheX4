"""Read-only Steam/PS1 resource comparison; never writes into the installation."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, file_info, mt_arc, psx_arc


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steam-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    steam, dest = args.steam_root.resolve(), args.output.resolve()
    if not dest.is_relative_to((ROOT / 'work').resolve()) or dest.is_relative_to(steam):
        raise ValueError('Output must be in project work/, outside Steam')
    dest.mkdir(parents=True, exist_ok=True)
    old = json.loads((ROOT / 'work/discovery/20261023T052917668160Z/inventory.json').read_text(encoding='utf-8'))
    prior = {Path(f['path']).name: f['sha256'] for f in old['steam']['archives']}
    report = {'created_utc': datetime.now(timezone.utc).isoformat(), 'installation_read_only': True}
    exe = steam / 'RXC1.exe'
    report['executable'] = file_info(exe)
    exe_raw = exe.read_bytes()
    pe = struct.unpack_from('<I', exe_raw, 60)[0]
    assert exe_raw[pe:pe+4] == b'PE\0\0'
    report['pe_machine'] = hex(struct.unpack_from('<H', exe_raw, pe+4)[0])
    report['exe_matches_oct23'] = report['executable']['sha256'] == old['steam']['executable']['sha256']
    manifest = steam.parents[1] / 'appmanifest_743890.acf'
    manifest_raw = manifest.read_text(encoding='utf-8')
    report['manifest'] = {k: re.findall(r'"'+k+r'"\s+"([^"]*)"', manifest_raw)
                          for k in ('appid', 'buildid', 'StateFlags', 'language')}
    arc_root = steam / 'nativeDX10/X4/romPC'
    archives, payloads, by_key = {}, {}, defaultdict(list)
    for path in sorted(arc_root.glob('*.arc')):
        data = path.read_bytes()
        rec = {**file_info(path), **mt_arc(data)}
        rec['matches_oct23'] = rec['sha256'] == prior.get(path.name)
        archives[path.name] = rec
        for e in rec['entries']:
            raw = zlib.decompress(data[e['offset']:e['offset']+e['compressed_size']])
            e['magic'] = raw[:4].decode('ascii', errors='backslashreplace').rstrip('\0')
            key = (e['name'], e['type_hash'])
            by_key[key].append((path.name, e['sha256']))
            if path.name in ('pl00.arc', 'pl01.arc', 'pl02.arc', 'pl00_eng.arc', 'pl01_eng.arc', 'pl02_eng.arc', 'drawunit.arc', 'load.arc', 'load_eng.arc'):
                payloads[(path.name, e['name'], e['type_hash'])] = raw
    report['archives'] = archives
    pairs = []
    for name, rec in archives.items():
        if name.endswith('_eng.arc') and name.replace('_eng.arc', '.arc') in archives:
            base = archives[name.replace('_eng.arc', '.arc')]
            a = {(e['name'], e['type_hash']): e for e in base['entries']}
            b = {(e['name'], e['type_hash']): e for e in rec['entries']}
            overlap = set(a) & set(b)
            pairs.append({'base': Path(base['path']).name, 'eng': name,
                          'base_entries': len(a), 'eng_entries': len(b),
                          'identical_internal_key': len(overlap),
                          'same_payload': sum(a[k]['sha256'] == b[k]['sha256'] for k in overlap),
                          'different_payload': [{'name': k[0], 'type': k[1]} for k in sorted(overlap) if a[k]['sha256'] != b[k]['sha256']]})
    paired = {p[k] for p in pairs for k in ('base', 'eng')}
    report['language_pairs'] = pairs
    report['unpaired_archives'] = sorted(set(archives) - paired)
    report['internal_key_collisions'] = [{'name': k[0], 'type': k[1], 'archives': v,
                                          'distinct_payloads': len(set(x[1] for x in v))}
                                         for k, v in sorted(by_key.items()) if len(v) > 1]
    report['sound_files'] = [file_info(p) for p in sorted((steam/'nativeDX10/X4').rglob('*'))
                             if p.is_file() and 'sound' in p.parts]
    report['executable_resource_strings'] = sorted(set(s.decode('ascii') for s in re.findall(rb'[ -~]{6,}', exe_raw)
                                                      if re.search(rb'(pl0[012]|drawunit|load_eng|X4\\|X4/)', s, re.I)))
    # Exact containment is evidence of data reuse, not a runtime renderer test.
    disc = Path(old['discs'][0]['path'])
    report['ps1_original'] = file_info(disc)
    assert report['ps1_original']['sha256'] == old['discs'][0]['sha256']
    comparisons = []
    with disc.open('rb') as stream:
        reader = DiscReader(stream, disc.stat().st_size)
        records = {r['name'].split(';')[0]: r for r in reader.inspect()['files'] if not r['directory']}
        for player in ('pl00', 'pl01', 'pl02'):
            r = records[player.upper() + '_U.ARC']
            psraw = reader.read(r['lba'], r['size'])
            for ent in psx_arc(psraw):
                if ent['type'] not in ('0x3', '0x9'):
                    continue
                psdata = psraw[ent['offset']:ent['offset']+ent['size']]
                for (arc, name, kind), raw in payloads.items():
                    if arc != player + '_eng.arc' or raw[:4] not in (b'PAT\0', b'COL\0'):
                        continue
                    match = raw.find(psdata)
                    comparisons.append({'ps1_arc': player.upper()+'_U.ARC', 'ps1_type': ent['type'],
                                        'ps1_size': len(psdata), 'steam_arc': arc, 'steam_name': name,
                                        'steam_magic': raw[:4].hex(), 'steam_size': len(raw),
                                        'full_ps1_payload_offset': match,
                                        'steam_header_hex': raw[:48].hex()})
    report['ps1_exact_comparisons'] = comparisons
    # Selected extracted bytes stay under work/ and are never installed.
    for (arc, name, kind), raw in payloads.items():
        target = dest / 'extracted' / arc / (name.replace('\\', '/') + '.' + kind)
        if not target.resolve().is_relative_to(dest):
            raise ValueError('Unsafe archive name')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    report['summary'] = {'arc_count': len(archives), 'entry_count': sum(len(r['entries']) for r in archives.values()),
                         'archive_bytes': sum(r['size'] for r in archives.values()),
                         'all_archives_match_oct23': all(r['matches_oct23'] for r in archives.values()),
                         'pair_count': len(pairs), 'unpaired_count': len(report['unpaired_archives']),
                         'types': dict(Counter(e['magic'] for r in archives.values() for e in r['entries']))}
    protected = [report['executable']] + list(archives.values()) + report['sound_files'] + [report['ps1_original']]
    report['input_hashes_preserved'] = all(file_info(Path(r['path']))['sha256'] == r['sha256'] for r in protected)
    assert report['input_hashes_preserved']
    (dest / 'inventory.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'summary': report['summary'], 'unpaired': report['unpaired_archives'],
                      'ps1_matches': [r for r in comparisons if r['full_ps1_payload_offset'] >= 0],
                      'input_hashes_preserved': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
