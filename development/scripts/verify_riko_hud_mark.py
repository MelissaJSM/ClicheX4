"""Read back the HUD overlay and reject unintended player/disc edits."""
import argparse
import json
from pathlib import Path
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.project import digest, write_json
from src.psx_hud_mark import replace_hud_mark
from src.psx_player import composition_frame
from src.psx_ui_atlas import local_composition
from src.psx_static_effect import compose_static


def verify(previous, build, output):
    before, after = (previous/'modified.arc').read_bytes(), (build/'modified.arc').read_bytes()
    expected, report = replace_hud_mark(before)
    if after != expected:
        raise ValueError('Player archive contains edits outside the HUD recipe')
    pngs = list(previous.glob('*.png'))
    if not all(digest(p) == digest(build/p.name) for p in pngs):
        raise ValueError('Accepted player PNG changed')
    p, q = entry(before, 3), entry(after, 3)
    for bank in (0, 5):
        for n in range(composition_frame(p, bank, 0)['bank_frame_count']):
            if composition_frame(p, bank, n) != composition_frame(q, bank, n):
                raise ValueError('Compressed body/effect composition changed')
    for n in range(69, 78):
        old, size, bounds, _ = compose_static(entry(before,0x10206),local_composition(composition_frame(p,1,n)))
        new, ns, nb, _ = compose_static(entry(after,0x10206),local_composition(composition_frame(q,1,n)))
        if size != ns or bounds != nb:
            raise ValueError('HUD geometry changed')
        for i,(a,b) in enumerate(zip(old,new)):
            x,y=i%size[0]+bounds[0],i//size[0]+bounds[1]
            if a != b and not (-18 <= x <= 3 and 26 <= y <= 38):
                raise ValueError('HP bar, lives ring or other HUD pixels changed')
    rejected=[]
    corrupt=bytearray(entry(before,0x10206));corrupt[(76//16*16)*128+76%16*8]^=1
    cases={'already_patched':after,'wrong_source_tile':replace_entry(before,0x10206,bytes(corrupt)),
           'truncated_archive':before[:100]}
    for label, data in cases.items():
        try:
            replace_hud_mark(data)
        except (ValueError, StopIteration, IndexError):
            rejected.append(label)
        else:
            raise ValueError('Invalid HUD input accepted: '+label)
    with (previous/'riko_motion.bin').open('rb') as a,(build/'riko_motion.bin').open('rb') as b:
        da=DiscReader(a,(previous/'riko_motion.bin').stat().st_size);db=DiscReader(b,(build/'riko_motion.bin').stat().st_size)
        rec=next(r for r in da.inspect()['files'] if r['path']=='/ARC/PL01_U.ARC;1')
        if db.read(rec['lba'],rec['size']) != after:
            raise ValueError('HUD BIN readback mismatch')
        allowed=range(rec['lba'],rec['lba']+(rec['size']+2047)//2048)
        a.seek(0);b.seek(0);lba=0;changed=[]
        while x:=a.read(2352*256):
            y=b.read(len(x))
            if len(x)!=len(y):raise ValueError('BIN size changed')
            for i in range(0,len(x),2352):
                if x[i:i+2352]!=y[i:i+2352]:
                    if lba+i//2352 not in allowed:raise ValueError('Non-player raw sector changed')
                    changed.append(lba+i//2352)
            lba+=len(x)//2352
        if b.read(1):raise ValueError('Trailing output bytes')
    result={'previous_bin_sha256':digest(previous/'riko_motion.bin'),'bin_sha256':digest(build/'riko_motion.bin'),
        'hud':report,'changed_raw_sectors_vs_previous':changed,'preserved_pngs':len(pngs),
        'body_and_compressed_effect_compositions_unchanged':True,'all_other_disc_files_unchanged':True,
        'all_nine_hp_gauges_checked':True,'negative_inputs_rejected':rejected}
    write_json(output,result);print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('previous','build','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();verify(a.previous,a.build,a.output)
