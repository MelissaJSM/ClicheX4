"""Create a fixed-size HUD overlay on the accepted illustration recipe."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from scripts.project import digest
from scripts.prepare_riko_ui import entry
from scripts.extract_zero import save_image
from src.psx_hud_mark import replace_hud_mark
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition


def prepare(source, output, palette):
    if output.exists():
        raise ValueError('Output already exists')
    before = (source/'PL01_U.ARC').read_bytes()
    after, report = replace_hud_mark(before)
    shutil.copytree(source, output)
    (output/'PL01_U.ARC').write_bytes(after)
    recipe = json.loads((output/'recipe.json').read_text('utf8'))
    recipe['hud_mark'] = report
    for item in recipe['files']:
        item['sha256'] = digest(output/item['file'])
    (output/'recipe.json').write_text(json.dumps(recipe, indent=2)+'\n', encoding='utf8')
    pal = struct.unpack('<16H', palette.read_bytes())
    for label, arc in [('before', before), ('after', after)]:
        for n in (69, 77):
            data, size, _, _ = compose_static(entry(arc,0x10206), local_composition(composition_frame(entry(arc,3),1,n)))
            im = save_image(data, size, pal, output/f'hud_{label}_{n}.png')
            im.resize((size[0]*6, size[1]*6)).save(output/f'hud_{label}_{n}_6x.png')
    print(json.dumps({'output': str(output), 'hud_mark': report}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for n in ('source', 'output', 'palette'):
        p.add_argument('--'+n, type=Path, required=True)
    a = p.parse_args()
    prepare(a.source, a.output, a.palette)
