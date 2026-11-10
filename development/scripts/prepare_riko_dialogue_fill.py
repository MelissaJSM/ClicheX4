"""대화 초상화 하단만 생성 원화로 보완하고 기존 일러스트 레시피에 결합한다."""
import argparse, json, shutil, struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scripts.prepare_riko_illustrations import RGB, WORDS, repack_one_bank, save
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.discover_inputs import psx_arc, sha256, DiscReader
from scripts.project import digest

ROOT = Path(__file__).resolve().parents[1]


def prepare(source, generated, output):
    source, generated, output = source.resolve(), generated.resolve(), output.resolve()
    if not all(p.is_relative_to(ROOT/'work/ver_buki_riko') for p in (source, generated, output)):
        raise ValueError('Expected project work paths')
    recipe = json.loads((source/'recipe.json').read_text('utf8'))
    for rec in recipe['files']:
        if digest(source/rec['file']) != rec['sha256']:
            raise ValueError('Source recipe candidate changed')
    output.mkdir(exist_ok=False)
    for p in source.iterdir():
        if p.suffix.lower() in ('.arc', '.png', '.bin'):
            shutil.copyfile(p, output/p.name)
    im = Image.open(generated).convert('RGBA').resize((112, 94), Image.Resampling.LANCZOS)
    a = np.array(im)
    colors = np.array(RGB[1:], np.int32)
    delta = ((a[:, :, :3].astype(np.int32)[:, :, None, :]-colors)**2).sum(3)
    fill = np.zeros((96, 112), dtype='uint8')
    fill[:94] = np.where(a[:, :, 3] >= 128, delta.argmin(2)+1, 0).astype('uint8')
    targets = {}
    metrics = []
    for n in range(3):
        old = np.array(Image.open(source/f'dialogue_{n}.png'))
        new = old.copy()
        new[80:84] = np.where(old[80:84], old[80:84], fill[80:84])
        new[84:] = fill[84:]
        # Live frame: panel spans y24..117 inclusive, while the part canvas is 96px.
        # End the bust at panel row93, leaving the two outside-canvas rows transparent.
        new[94:] = 0
        if np.count_nonzero(new[93]) != 112:
            raise ValueError('Generated lower edge still has excessive transparent space')
        assert np.array_equal(new[:80], old[:80])
        save(new, output/f'dialogue_{n}.png')
        targets[n] = (new.tobytes(), (112, 96))
        metrics.append({'frame': n, 'preserved_top_rows': 80,
                        'panel_last_row': 93,
                        'old_panel_edge_opaque': int(np.count_nonzero(old[93])),
                        'new_panel_edge_opaque': int(np.count_nonzero(new[93])),
                        'outside_panel_opaque': int(np.count_nonzero(new[94:])),
                        'changed_pixels': int(np.count_nonzero(new != old))})
    base = (source/'ST00_00.ARC').read_bytes()
    oldp = entry(base, 0xa)
    oldhead = entry(base, 0x10102)[217088:223232]
    head, parts, pack = repack_one_bank(oldhead, oldp, 13, targets)
    offset = struct.unpack_from('<I', oldp, 13*4)[0]
    oldbank, newbank = oldp[offset:], parts[offset:]
    changed = []
    parent = Path(recipe['parent_build'])
    parent_manifest = json.loads((parent/'manifest.json').read_text('utf8'))
    with (parent/parent_manifest['bin_file']).open('rb') as f:
        disc = DiscReader(f, (parent/parent_manifest['bin_file']).stat().st_size)
        for rec in recipe['files']:
            path = output/rec['file']; raw = path.read_bytes(); new = raw
            if path.name.startswith('ST'):
                for e in psx_arc(raw):
                    data = raw[e['offset']:e['offset']+e['size']]
                    if int(e['type'], 16) >> 16 == 1 and oldhead in data:
                        if data.count(oldhead) != 1:
                            raise ValueError('Ambiguous dialogue atlas')
                        new = replace_entry(new, int(e['type'], 16), data.replace(oldhead, head))
                    elif e['type'] == '0xa' and oldbank in data:
                        if data.count(oldbank) != 1:
                            raise ValueError('Ambiguous dialogue parts')
                        new = replace_entry(new, 0xa, data.replace(oldbank, newbank))
            if new != raw:
                changed.append(path.name); path.write_bytes(new)
            assert len(new) == len(raw)
            before = disc.read(rec['source']['lba'], rec['source']['size'])
            rec['sha256'] = sha256(new)
            rec['changed_bytes_from_parent'] = sum(a != b for a, b in zip(new, before))
    recipe['checks']['dialogue'] = pack
    recipe['dialogue_fill'] = {'source_recipe': str(source/'recipe.json'),
        'source_recipe_sha256': digest(source/'recipe.json'), 'generated': str(generated),
        'generated_sha256': digest(generated), 'metrics': metrics,
        'changed_files_from_previous_illustrations': changed}
    (output/'recipe.json').write_text(json.dumps(recipe, indent=2), encoding='utf8')
    sheet = Image.new('RGB', (3*448, 420), (48, 29, 18))
    draw = ImageDraw.Draw(sheet)
    for n in range(3):
        for j, folder in enumerate((source, output)):
            im = Image.open(folder/f'dialogue_{n}.png').convert('RGBA')
            im = im.resize((224, 192), Image.Resampling.NEAREST)
            sheet.paste(im, (n*448+j*224, 25), im)
        draw.text((n*448+8, 5), f'Frame {n}: before / after', fill='white')
    sheet.save(output/'comparison.png')
    print(json.dumps({'output': str(output), 'changed_files': changed, 'metrics': metrics, 'pack': pack}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('source', 'generated', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    prepare(a.source, a.generated, a.output)
