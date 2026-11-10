"""현재 제로 계열 도트를 고정 원점의 무라벨 미술 입력으로 묶는다."""
import argparse
import hashlib
from pathlib import Path
import struct
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render, rgba
from scripts.prepare_riko_ui import entry
from scripts.prepare_sprite_style_unification import WORK, SOURCES, write
from src.psx_disc import file_hash


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--character', choices=('riko', 'rin'), required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--keys', nargs='+', required=True)
    p.add_argument('--crop', nargs=4, type=int, default=(112, 128, 208, 192))
    a = p.parse_args()
    mode = 'ver_buki_riko' if a.character == 'riko' else 'ver_rin_nana'
    stem, expected = SOURCES[mode]
    source = ROOT/'out'/mode/'sprite_reaudit_20261106_v1'/(stem+'.bin')
    assert file_hash(source) == expected
    data = read_disc(source, ('PL01_U.ARC',))[0]['PL01_U.ARC']
    palette = struct.unpack_from('<16H', entry(data, 9))
    out = (WORK/a.character/a.name).resolve()
    assert out.is_relative_to(WORK) and not out.exists()
    out.mkdir(parents=True)
    crop = tuple(a.crop)
    width, height = crop[2]-crop[0], crop[3]-crop[1]
    assert 0 < len(a.keys) <= 4 and width > 0 and height > 0
    columns, rows, scale = 2, (len(a.keys)+1)//2, 8
    sheet = Image.new('RGBA', (columns*width*scale, rows*height*scale))
    records = []
    idle = rgba(render(data, 0, 0, 147)[0], palette)
    idle.save(out/'idle_native.png')
    idle.crop((128,128,192,192)).resize((768,768), Image.Resampling.NEAREST).save(out/'idle_reference.png')
    for i, key in enumerate(a.keys):
        bank, ref = int(key[1]), int(key.split('_')[1])
        assert bank in (0,1)
        image = rgba(render(data, bank, bank*5, ref)[0], palette)
        bounds = image.getchannel('A').getbbox()
        assert bounds and bounds[0]>=crop[0] and bounds[1]>=crop[1] and bounds[2]<=crop[2] and bounds[3]<=crop[3], (key,bounds,crop)
        image.save(out/(key+'.png'))
        sheet.alpha_composite(image.crop(crop).resize((width*scale,height*scale),Image.Resampling.NEAREST), (i%2*width*scale,i//2*height*scale))
        records.append({'key':key,'bank':bank,'ref':ref,'cell':[i%2,i//2],'bounds':bounds})
    sheet.save(out/'targets.png')
    write(out/'inputs.json', {'source_bin':source.relative_to(ROOT).as_posix(),'source_sha256':expected,
          'archive_sha256':hashlib.sha256(data).hexdigest(),'character':a.character,'crop':list(crop),
          'native_cell':[width,height],'columns':columns,'rows':rows,'scale':scale,'palette_words':palette,'frames':records})
    print(out)


if __name__ == '__main__':
    main()
