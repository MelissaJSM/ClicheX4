"""Read back HQ frames and guard against mouth motion in the standby loop."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry
from scripts.project import digest,write_json
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static


def verify(previous,build,recipe,output):
    with (previous/'riko_motion.bin').open('rb') as a,(build/'riko_motion.bin').open('rb') as b:
        da=DiscReader(a,(previous/'riko_motion.bin').stat().st_size);db=DiscReader(b,(build/'riko_motion.bin').stat().st_size)
        rec=next(r for r in da.inspect()['files'] if r['path']=='/ARC/ST0D_0Z.ARC;1')
        before,after=da.read(rec['lba'],rec['size']),db.read(rec['lba'],rec['size'])
        if after!=(recipe/'ST0D_0Z.ARC').read_bytes():raise ValueError('HQ BIN differs from candidate')
        allowed=range(rec['lba'],rec['lba']+(rec['size']+2047)//2048)
        a.seek(0);b.seek(0);lba=0;changed=[]
        while x:=a.read(2352*256):
            y=b.read(len(x))
            if len(x)!=len(y):raise ValueError('BIN size differs')
            if x!=y:
                for i in range(0,len(x),2352):
                    if x[i:i+2352]!=y[i:i+2352]:
                        if lba+i//2352 not in allowed:raise ValueError('Non-HQ raw sector changed')
                        changed.append(lba+i//2352)
            lba+=len(x)//2352
        if b.read(1):raise ValueError('Trailing output data')
    g,h=entry(before,0x10102),entry(after,0x10102);p,q=entry(before,10),entry(after,10)
    if g[:63488]!=h[:63488] or g[81920:]!=h[81920:]:raise ValueError('Other HQ texture changed')
    frames={}
    for n in range(14):
        c=aliased_composition(q,2,n);px,size,_,_=compose_static(h[63488:81920],local_composition(c))
        im=Image.open(recipe/f'base_{n:02d}.png')
        if px!=im.tobytes() or size!=im.size:raise ValueError('HQ native PNG readback mismatch')
        frames[n]=np.frombuffer(px,dtype='uint8').reshape(size[1],size[0])
        old=aliased_composition(p,2,n)
        if [(v['x'],v['y'],v['flags']&~3) for v in old['parts']]!=[(v['x'],v['y'],v['flags']&~3) for v in c['parts']]:
            raise ValueError('HQ part geometry/CLUT changed')
    mask=np.zeros_like(frames[0],dtype=bool);mask[20:23,36:42]=True;mask[21:23,44:46]=True
    for n in range(6):
        if np.any((frames[n]!=frames[0])&~mask) or not np.array_equal(frames[n][24:29],frames[0][24:29]):
            raise ValueError('Standby frame changed mouth or protected face')
    if (previous/'modified.arc').read_bytes()!=(build/'modified.arc').read_bytes():raise ValueError('Player ARC changed')
    pngs=list(previous.glob('*.png'))
    if not all(digest(p)==digest(build/p.name) for p in pngs):raise ValueError('Accepted player PNG changed')
    result={'previous_bin_sha256':digest(previous/'riko_motion.bin'),'bin_sha256':digest(build/'riko_motion.bin'),
        'changed_file':rec['path'],'changed_raw_sectors':changed,'native_frames_readback_matched':14,
        'standby_closed_mouth_frames':list(range(6)),'part_geometry_flags_and_palette_preserved':True,
        'player_archive_name_death_and_other_assets_unchanged':True,'preserved_pngs':len(pngs)}
    write_json(output,result);print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('previous','build','recipe','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();verify(a.previous,a.build,a.recipe,a.output)
