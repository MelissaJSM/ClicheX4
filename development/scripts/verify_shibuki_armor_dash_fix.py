"""Verify final relocated assets, every partial dash combination and protected frames."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_armor_dash_fix import PARENT,FRAMES
from scripts.analyze_shibuki_armor import entries
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_shibuki_text import rename_shibuki

def verify(build):
    manifest=json.loads((build/'manifest.json').read_text('utf8'));recipe=json.loads((build/'recipe.json').read_text('utf8'));fix=ROOT/recipe['dash_recipe'];layers=fix.parent
    new=(build/'modified.arc').read_bytes()
    if sha256(new)!=manifest['modified_archive_sha256'] or sha256(fix.read_bytes())!=recipe['dash_recipe_sha256']:raise ValueError('Build hash mismatch')
    before=entries((PARENT/'modified.arc').read_bytes());after=entries(new)
    for kind in before:
        if kind not in (2,3,21) and before[kind]!=after[kind]:raise ValueError('Protected UI entry changed')
    for name in ['PL00_U.ARC','PL02_U.ARC']:
        data=entries((build/name).read_bytes())[21];again,report=rename_shibuki(data)
        if again!=data or report['name_count']:raise ValueError('Dialogue is not idempotent')
    def raster(es,n,b):
        f=graphics_bank(es[2],0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data
        return canvas_from_parts(raw,f['tile_count'],composition_frame(es[3],b,n))
    protected=0
    for n in sorted(set(range(237))-{105,*range(175,183)}):
        for b in [0,5,6,7,8]:
            a=raster(before,n,b);z=raster(after,n,b)
            if n in FRAMES and b in [6,7,8]:
                if not np.array_equal(z,np.array(Image.open(layers/f'bank{b}_{n:03}.png'))):raise ValueError('Relocation changed target art')
            else:
                if not np.array_equal(a,z):raise ValueError('Non-target player layer changed')
                protected+=1
    palettes=[np.array(struct.unpack_from('<16H',after[9],i*32),np.uint16) for i in range(3)];checks=[];independent=[]
    for n in range(67,85):
        actual={b:raster(after,n,b) for b in [0,5,6,7,8]}
        expected={b:np.array(Image.open(layers/f'bank{b}_{n:03}.png')) if n in FRAMES and b in [6,7,8] else raster(before,n,b) for b in actual}
        for armtype in [1,2]:
            for mask in range(16):
                outputs=[]
                for source in [actual,expected]:
                    image=palettes[0][source[0]].copy()
                    for bit,b in [(8,8),(1,5),(4,7),(2,6)]:
                        if mask&bit:
                            m=source[b]>0;image[m]=palettes[2 if b==7 and armtype==2 else 1][source[b][m]]
                    outputs.append(image)
                for flipped in [False,True]:
                    a,z=[v[:,::-1] if flipped else v for v in outputs]
                    if not np.array_equal(a,z):raise ValueError('Partial armor combination mismatch')
                    checks.append([n,mask,armtype,flipped])
        if n in FRAMES:
            for bit,b,minpixels in [(1,5,50),(2,6,200),(4,7,25),(8,8,100)]:
                if np.count_nonzero(actual[b])<minpixels:raise ValueError('Dash armor part missing')
                other=palettes[0][actual[0]];equipped=other.copy();m=actual[b]>0;equipped[m]=palettes[1][actual[b][m]]
                if np.count_nonzero(equipped!=other)<20:raise ValueError('Equipped part is invisible')
                independent.append([n,bit,int(m.sum()),int(np.count_nonzero(equipped!=other))])
    report={'build_sha256':manifest['modified_bin']['sha256'],'protected_player_layers_equal':protected,'dash_combinations_verified':len(checks),'native_source_layers_equal':True,'dialogue_old_names_remaining':0,'individual_part_visibility':independent,'checks':checks,'runtime_verified':False}
    (build/'static_verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ['checks','individual_part_visibility']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args();verify(a.build.resolve())
