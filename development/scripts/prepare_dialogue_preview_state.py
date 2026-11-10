"""보존한 대화 저장 사본의 초상화 VRAM만 교체. BIN 로딩 검증과 구별하는 실기 미술 검토용."""
import argparse, gzip, json
from pathlib import Path
from scripts.prepare_riko_ui import entry
from scripts.project import digest
from src.epsxe_state import framebuffer

ROOT = Path(__file__).resolve().parents[1]


def prepare(source, before, after, output):
    source, before, after, output = (p.resolve() for p in (source, before, after, output))
    if not all(p.is_relative_to(ROOT/'work/ver_buki_riko') for p in (source, before, after, output)):
        raise ValueError('Expected local test paths')
    state = gzip.decompress(source.read_bytes())
    oldarc, newarc = before.read_bytes(), after.read_bytes()
    old = entry(oldarc, 0x10102)[217088:223232]
    new = entry(newarc, 0x10102)[217088:223232]
    if entry(oldarc, 0xa) != entry(newarc, 0xa):
        raise ValueError('Preview path requires unchanged composition')
    vram, x, y = 2569183, 960, 112
    if len(state) != 4254418:
        raise ValueError('Unexpected ePSXe state layout')
    out = bytearray(state); changed = []
    for row in range(48):
        pos = vram+(y+row)*2048+x*2
        if state[pos:pos+128] != old[row*128:(row+1)*128]:
            raise ValueError('Checkpoint does not contain expected old dialogue texture')
        out[pos:pos+128] = new[row*128:(row+1)*128]
        changed.extend(i for i in range(pos, pos+128) if state[i] != out[i])
    if out[:vram] != state[:vram] or out[vram+1048576:] != state[vram+1048576:]:
        raise AssertionError('Changed non-VRAM state data')
    if not changed:
        raise ValueError('Preview contains no texture change')
    output.parent.mkdir(exist_ok=False)
    with output.open('xb') as f:
        f.write(gzip.compress(bytes(out), mtime=0))
    for page in (0, 256):
        framebuffer(state, vram, page).save(output.parent/f'before_framebuffer_{page}.png')
    report = {'source': str(source), 'source_sha256': digest(source), 'output': str(output),
        'output_sha256': digest(output), 'changed_vram_bytes': len(changed),
        'ram_and_gameplay_state_preserved': True, 'composition_preserved': True,
        'expected_after_arc': str(after), 'expected_after_sha256': digest(after),
        'purpose': 'Graphics-only save-copy preview; not proof of fresh BIN resource loading'}
    (output.parent/'preview.local.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('source', 'before', 'after', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    prepare(a.source, a.before, a.after, a.output)
