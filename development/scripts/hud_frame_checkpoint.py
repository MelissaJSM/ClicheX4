"""인증된 ePSXe F1에서 HUD static atlas 변경분만 갱신하는 독립 사본 제작기.

원본/활성 F1, 카드, 프로세스, 게임 BIN은 쓰지 않는다. EXE와 모든 PL 비texture
entry가 같은 두 BIN에 한정하며, 진행을 포함한 RAM 전체도 바이트 보존한다.
"""
import argparse
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc

OUTPUT_ROOT = ROOT / 'work/hud_frame_fix_20261105/checkpoint'
NAMES = ('SLUS_005.61', 'PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC')
RP = 442
VR = 2569183
STATE_SIZE = 4254418
ATLAS_SIZE = 112640
TEXTURE_KIND = 0x10206


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(8 * 1024 * 1024):
            result.update(block)
    return result.hexdigest()


def entries(arc):
    rows = psx_arc(arc)
    return {int(row['type'], 16): arc[row['offset']:row['offset'] + row['size']] for row in rows}


def assets(path):
    with path.open('rb') as stream:
        reader = DiscReader(stream, path.stat().st_size)
        rows = {r['name'].split(';')[0]: r for r in reader.inspect()['files']
                if r['name'].split(';')[0] in NAMES}
        require(set(rows) == set(NAMES), 'Missing US game resource')
        return {name: reader.read(row['lba'], row['size']) for name, row in rows.items()}


def validate_assets(old, new):
    require(set(old) == set(new) == set(NAMES), 'Unexpected resource scope')
    require(old['SLUS_005.61'] == new['SLUS_005.61'], 'EXE changes are not supported')
    report = {}
    for name in NAMES[1:]:
        before, after = old[name], new[name]
        require(len(before) == len(after), 'ARC length changed: ' + name)
        rows, new_rows = psx_arc(before), psx_arc(after)
        layout = lambda records: [(r['index'], r['type'], r['offset'], r['size']) for r in records]
        require(layout(rows) == layout(new_rows), 'ARC layout changed: ' + name)
        old_entries, new_entries = entries(before), entries(after)
        require(set(old_entries) == set(new_entries), 'ARC entry set changed')
        texture_row = next(r for r in rows if int(r['type'], 16) == TEXTURE_KIND)
        start, end = texture_row['offset'], texture_row['offset'] + texture_row['size']
        require(len(old_entries[TEXTURE_KIND]) == len(new_entries[TEXTURE_KIND]) == ATLAS_SIZE,
                'Unsupported static atlas size')
        require(before[:start] == after[:start] and before[end:] == after[end:],
                'Target changes data outside static texture: ' + name)
        require(all(old_entries[k] == new_entries[k] for k in old_entries if k != TEXTURE_KIND),
                'Nontexture entry changed: ' + name)
        report[name] = dict(before_sha256=sha(before), after_sha256=sha(after),
            texture_before_sha256=sha(old_entries[TEXTURE_KIND]),
            texture_after_sha256=sha(new_entries[TEXTURE_KIND]),
            changed_texture_bytes=sum(a != b for a, b in zip(old_entries[TEXTURE_KIND], new_entries[TEXTURE_KIND])),
            archive_layout_and_every_other_byte_preserved=True)
    require(any(v['changed_texture_bytes'] for v in report.values()), 'No static atlas changes')
    return report


def atlas_offsets():
    # Native 11 transfers of 64 PSX words by 80 rows: x320..1023, y176..255.
    return [VR + (176 + row % 80) * 2048 + 640 + (row // 80) * 128
            for row in range(ATLAS_SIZE // 128)]


def read_atlas(raw):
    return b''.join(raw[at:at + 128] for at in atlas_offsets())


def refresh(raw, old, new):
    validate_assets(old, new)
    require(len(raw) == STATE_SIZE and raw.startswith(b'ePSXe\x06\x00SLUS_005.61'),
            'Unsupported checkpoint format')
    ram = raw[RP:RP + 0x200000]
    player = ram[0x1418c8:0x1418c8 + 228]
    require(player[2] in (0, 1), 'Unsupported current player')
    require(ram[0x1721f7] in (0, 1), 'Unsupported Ultimate flag')
    for address in (0x233c8, 0x23400, 0xea20c, 0x3dc1c):
        offset = address - 0x10000 + 2048
        require(ram[address:address + 64] == old['SLUS_005.61'][offset:offset + 64],
                'Source EXE/RAM anchor differs: ' + hex(address))
    name = 'PL01_U.ARC' if player[2] else 'PL02_U.ARC' if ram[0x1721f7] else 'PL00_U.ARC'
    before_entries, after_entries = entries(old[name]), entries(new[name])
    resident = {}
    for kind in (2, 3, 9):
        data = before_entries[kind]
        at = ram.find(data)
        require(at >= 0 and ram.find(data, at + 1) < 0, 'Missing or ambiguous resident player resource')
        resident[hex(kind)] = dict(ram_offset=at, sha256=sha(data), size=len(data))
    before, after = before_entries[TEXTURE_KIND], after_entries[TEXTURE_KIND]
    require(ram.find(before) < 0 and ram.find(after) < 0,
            'A RAM-resident static texture requires separate cache mapping')
    current = read_atlas(raw)
    require(current in (before, after), 'Stale or unknown complete static GPU atlas')
    result = bytearray(raw)
    changed = []
    mapped = set()
    for row, start in enumerate(atlas_offsets()):
        require(VR <= start and start + 128 <= VR + 1048576, 'Atlas address outside VRAM')
        for x in range(128):
            index = row * 128 + x
            if before[index] == after[index]:
                continue
            at = start + x
            require(at not in mapped, 'Duplicate atlas mapping')
            mapped.add(at)
            if result[at] != after[index]:
                changed.append(at)
                result[at] = after[index]
    result = bytes(result)
    actual_changes = [i for i, (a, b) in enumerate(zip(raw, result)) if a != b]
    require(actual_changes == sorted(changed), 'Unrecorded checkpoint change')
    require(all(i in mapped for i in actual_changes), 'Non-HUD byte changed')
    require(result[RP:RP + 0x200000] == ram, 'RAM or gameplay progress changed')
    require(raw[:VR] == result[:VR] and raw[VR + 1048576:] == result[VR + 1048576:],
            'Non-VRAM state or SPU state changed')
    require(read_atlas(result) == after, 'Final complete static GPU atlas differs')
    proof = dict(scope='Authenticated HUD texture cache only; not fresh disc or live runtime proof',
        source_player_archive=name, ram_offset=RP, vram_offset=VR, resident_resources=resident,
        texture_before_sha256=sha(before), texture_after_sha256=sha(after),
        source_atlas_sha256=sha(current), output_atlas_sha256=sha(read_atlas(result)),
        changed_vram_bytes=len(changed), allowed_vram_bytes=len(mapped), changed_state_offsets=sorted(changed),
        all_other_state_bytes_identical=True, entire_RAM_progress_and_EXE_preserved=True,
        all_palettes_preserved=True, all_SPU_and_decoder_bytes_preserved=True,
        already_current=current == after,
        player=dict(character=player[2], hp=player[0x5c], armor=player[0xa7], weapon=player[0x93],
            ultimate=ram[0x1721f7], stage=ram[0x1721cc], area=ram[0x1721cd], frame=player[0x47],
            world=[struct.unpack_from('<i', player, o)[0] / 65536 for o in (8, 12)]))
    return result, proof


def validate_paths(source, old_bin, new_bin, output):
    source, old_bin, new_bin, output = (Path(p).absolute() for p in (source, old_bin, new_bin, output))
    require(all(p.resolve().is_relative_to(ROOT) for p in (source, old_bin, new_bin)), 'Input outside project')
    require(source.resolve().is_relative_to(ROOT / 'work'), 'Expected a separate working checkpoint')
    require('sstates' not in source.parts, 'Copy active emulator state to an isolated checkpoint first')
    require(output.resolve().is_relative_to(OUTPUT_ROOT) and output.resolve() != OUTPUT_ROOT,
            'Output must be a fresh directory inside the dedicated checkpoint area')
    require(not output.exists(), 'Output directory already exists')
    for candidate in (source, old_bin, new_bin):
        require(candidate.is_file() and candidate.stat().st_nlink == 1, 'Input link or missing file')
        require(output.resolve() != candidate.resolve(), 'Input/output collision')
    require(old_bin.resolve() != new_bin.resolve(), 'Source and target BIN are the same')
    for path in (source, old_bin, new_bin, output):
        for parent in (path, *path.parents):
            if parent == ROOT.parent:
                break
            if parent.exists():
                require(not parent.is_symlink() and not (getattr(parent.lstat(), 'st_file_attributes', 0) & 0x400),
                        'Links/junctions are not supported')
    return tuple(p.resolve() for p in (source, old_bin, new_bin, output))


def negative_checks(raw, old, new, proof):
    rejects = []
    cases = [('format', 0), ('EXE_anchor', RP + 0x233c8),
        ('static_atlas', atlas_offsets()[0]),
        ('resident_graphics', RP + proof['resident_resources']['0x2']['ram_offset']),
        ('resident_palette', RP + proof['resident_resources']['0x9']['ram_offset'])]
    for label, at in cases:
        invalid = bytearray(raw)
        invalid[at] ^= 1
        try:
            refresh(bytes(invalid), old, new)
        except ValueError:
            rejects.append(label)
        else:
            raise AssertionError('Corrupt state accepted: ' + label)
    for label, resource, kind in [('target_EXE', 'SLUS_005.61', None),
                                  ('target_composition', 'PL02_U.ARC', 3),
                                  ('target_palette', 'PL01_U.ARC', 9)]:
        invalid = dict(new)
        blob = bytearray(new[resource])
        at = 2048 if kind is None else next(r['offset'] for r in psx_arc(blob) if int(r['type'], 16) == kind)
        blob[at] ^= 1
        invalid[resource] = bytes(blob)
        try:
            refresh(raw, old, invalid)
        except ValueError:
            rejects.append(label)
        else:
            raise AssertionError('Unsupported target accepted: ' + label)
    return rejects


def main(args):
    source, old_bin, new_bin, output = validate_paths(args.source, args.source_bin, args.target_bin, args.output)
    require(digest(source) == args.source_sha256, 'Source checkpoint hash differs')
    require(digest(old_bin) == args.source_bin_sha256, 'Source BIN hash differs')
    require(digest(new_bin) == args.target_bin_sha256, 'Target BIN hash differs')
    old, new = assets(old_bin), assets(new_bin)
    resource_proof = validate_assets(old, new)
    require(source.stat().st_size < 8 * 1024 * 1024, 'Oversized compressed checkpoint')
    raw = gzip.decompress(source.read_bytes())
    result, proof = refresh(raw, old, new)
    repeated, _ = refresh(raw, old, new)
    require(repeated == result, 'Independent refresh differs')
    again, again_proof = refresh(result, old, new)
    require(again == result and again_proof['changed_vram_bytes'] == 0, 'Refresh is not idempotent')
    rejected = negative_checks(raw, old, new, proof)
    for label, override in [('same_source_output', source), ('existing_output', source.parent),
                            ('outside_output_area', ROOT / 'work/unexpected_checkpoint_output')]:
        try:
            validate_paths(source, old_bin, new_bin, override)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError('Unsafe output accepted: ' + label)
    packed = gzip.compress(result, mtime=0)
    require(digest(source) == args.source_sha256 and digest(old_bin) == args.source_bin_sha256
            and digest(new_bin) == args.target_bin_sha256, 'An input changed during preparation')
    output.mkdir(parents=True, exist_ok=False)
    path = output / source.name
    with path.open('xb') as stream:
        stream.write(packed)
    require(gzip.decompress(path.read_bytes()) == result, 'Output readback differs')
    proof.update(source=source.relative_to(ROOT).as_posix(), source_sha256=args.source_sha256,
        source_bin=old_bin.relative_to(ROOT).as_posix(), source_bin_sha256=args.source_bin_sha256,
        target_bin=new_bin.relative_to(ROOT).as_posix(), target_bin_sha256=args.target_bin_sha256,
        output=path.relative_to(ROOT).as_posix(), output_sha256=sha(packed),
        raw_before_sha256=sha(raw), raw_after_sha256=sha(result), resource_verification=resource_proof,
        reproduced_identical=True, idempotent=True, rejected_invalid_inputs=rejected,
        source_BINs_and_checkpoint_preserved=True, active_F1_written=False, memory_cards_written=False,
        process_memory_written=False, keys_sent=False, runtime_verified=False)
    (output / 'manifest.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({k: proof[k] for k in ('output', 'output_sha256', 'changed_vram_bytes', 'player',
        'all_other_state_bytes_identical', 'rejected_invalid_inputs', 'runtime_verified')}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--source-bin', type=Path, required=True)
    parser.add_argument('--source-bin-sha256', required=True)
    parser.add_argument('--target-bin', type=Path, required=True)
    parser.add_argument('--target-bin-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
