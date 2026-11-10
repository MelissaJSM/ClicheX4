"""새 BIN으로 불러온 블랙 상태의 실제 RAM/VRAM을 읽기 전용 대조한다."""
import argparse, json, struct, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import digest
from scripts.prepare_riko_ui import entry
from scripts.prepare_rin_common import read_disc
from scripts.overhaul_sprites_audit import render, rgba
from src.epsxe_state import framebuffer, match_sprite


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--capture', type=Path, required=True)
    a = p.parse_args()
    folder = a.capture.resolve()
    report = json.loads((folder / 'evidence.json').read_text('utf8'))
    session = json.loads((Path(report['session']) / 'session.local.json').read_text('utf8'))
    game = Path(session['cue']).with_suffix('.bin')
    if digest(game) != report['bin_sha256']:
        raise ValueError('Captured and mounted BIN differ')
    if len(report['ram_bases']) != 1 or len(report['vram_bases']) != 1:
        raise ValueError('Ambiguous memory capture')
    ram = (folder / f"ram_{report['ram_bases'][0]}.bin").read_bytes()
    vram = (folder / f"vram_{report['vram_bases'][0]}.bin").read_bytes()
    assets, _ = read_disc(game, ['PL01_U.ARC'])
    arc = assets['PL01_U.ARC']
    pal = entry(arc, 9)
    frame = ram[0x1418c8 + 0x47]
    indexed, _ = render(arc, 0, 0, frame)
    picture = rgba(indexed, struct.unpack_from('<64H', pal))
    picture = picture.crop(picture.getbbox())
    matches = {str(y): match_sprite(framebuffer(vram, 0, y), picture) for y in (0, 240)}
    result = dict(special_mode=ram[0x1721f7], character=ram[0x1418ca], frame=frame,
                  palette_ram_offset=ram.find(pal), black_row_equals_normal=pal[13*32:14*32] == pal[:32],
                  vram_clut_matches=vram[480*2048:480*2048+32] == pal[13*32:14*32],
                  screen_matches=matches, bin_sha256=report['bin_sha256'],
                  state_loaded=False, note='별도 시험 메모리카드의 블랙 플래그를 새 BIN에서 읽음; 치트 키 입력 검증과 구분')
    if not (result['special_mode'] == result['character'] == 1 and result['black_row_equals_normal']
            and result['vram_clut_matches'] and all(matches.values())):
        raise ValueError(f'Black rendering mismatch: {result}')
    (folder / 'black_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
