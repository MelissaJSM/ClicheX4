"""Compare all HQ frames with real part palettes; protect unrelated assets."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.project import digest,write_json
from src.psx_ui_atlas import aliased_composition
from src.psx_ui_render import render_static_rgba


def mismatched_frames(arc,palette_arc,expected):
    parts=entry(arc,10);texture=entry(arc,0x10102)[63488:81920];pal=entry(palette_arc,5)
    palettes={i:struct.unpack('<16H',pal[(35+i)*32:(36+i)*32]) for i in range(4)}
    mismatches=[]
    for n in range(14):
        actual,_=render_static_rgba(texture,aliased_composition(parts,2,n),palettes)
        with Image.open(expected/f'base_{n:02d}.png') as reference:
            if actual.tobytes()!=reference.convert('RGBA').tobytes():mismatches.append(n)
    return mismatches


def verify(previous,build,recipe,output):
    with (previous/'riko_motion.bin').open('rb') as a,(build/'riko_motion.bin').open('rb') as b:
        da=DiscReader(a,(previous/'riko_motion.bin').stat().st_size);db=DiscReader(b,(build/'riko_motion.bin').stat().st_size)
        files={r['path']:r for r in da.inspect()['files']}
        rec=files['/ARC/ST0D_0Z.ARC;1'];col=files['/ARC/COL0D_0Z.ARC;1']
        before,after=da.read(rec['lba'],rec['size']),db.read(rec['lba'],rec['size'])
        palettes=db.read(col['lba'],col['size'])
        if palettes!=da.read(col['lba'],col['size']):raise ValueError('HQ palette bytes changed')
        if after!=(recipe/'ST0D_0Z.ARC').read_bytes():raise ValueError('HQ candidate BIN readback differs')
        p,q=entry(before,10),entry(after,10)
        if replace_entry(before,10,q)!=after:raise ValueError('Non-parts HQ bytes changed')
        changed=[i for i,(x,y) in enumerate(zip(p,q)) if x!=y]
        allowed={t['record_offset'] for n in range(14) for t in aliased_composition(p,2,n)['parts']}
        if not changed or any(i not in allowed or (p[i]^q[i])&~12 or q[i]&12 for i in changed):
            raise ValueError('Changes exceed palette selector bits')
        for bank in (0,1,3,4):
            for n in range(aliased_composition(p,bank,0)['bank_frame_count']):
                if aliased_composition(p,bank,n)!=aliased_composition(q,bank,n):raise ValueError('Other HQ actor/UI changed')
        old_bad=mismatched_frames(before,palettes,recipe);new_bad=mismatched_frames(after,palettes,recipe)
        if old_bad!=[7,8,9] or new_bad:raise ValueError('Native CLUT regression/readback check differs')
        allowed_sectors=range(rec['lba'],rec['lba']+(rec['size']+2047)//2048)
        a.seek(0);b.seek(0);lba=0;sectors=[]
        while x:=a.read(2352*256):
            y=b.read(len(x))
            if len(y)!=len(x):raise ValueError('BIN length changed')
            for i in range(0,len(x),2352):
                if x[i:i+2352]!=y[i:i+2352]:
                    if lba+i//2352 not in allowed_sectors:raise ValueError('Other raw sector changed')
                    sectors.append(lba+i//2352)
            lba+=len(x)//2352
        if b.read(1):raise ValueError('Trailing output bytes')
    if (previous/'modified.arc').read_bytes()!=(build/'modified.arc').read_bytes():raise ValueError('Player/HUD archive changed')
    pngs=list(previous.glob('*.png'))
    if not all(digest(p)==digest(build/p.name) for p in pngs):raise ValueError('Accepted player PNG changed')
    result={'previous_bin_sha256':digest(previous/'riko_motion.bin'),'bin_sha256':digest(build/'riko_motion.bin'),
        'changed_clut_flag_bytes':len(changed),'old_bad_native_frames':old_bad,'fixed_native_frames_checked':14,
        'changed_raw_sectors':sectors,'texture_palette_geometry_and_timing_unchanged':True,
        'all_other_disc_bytes_unchanged':True,'preserved_pngs':len(pngs),'hud_mark_and_player_arc_unchanged':True}
    write_json(output,result);print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('previous','build','recipe','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();verify(a.previous,a.build,a.recipe,a.output)
