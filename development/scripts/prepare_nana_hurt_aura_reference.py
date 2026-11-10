"""피격 외곽235/236과 나나 기본형/부분 아머 몸 윤곽을 추출한다."""
import argparse,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_player import composition_frame
from src.psx_sprite_batch import canvas_from_parts
PARENT=ROOT/'out/ver_rin_nana/nana_fourth_hurt_extra_20261030T094556276971Z'
PARENT_SHA='bb0244610e3a14bc774d24f27160750e2780f4aad375227e95924b79d638445a'
FRAMES=[235,236]

def bodies(arc):
    _,base,f,raw=render(arc,234);c=entry(arc,3);layers={b:canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,234)) for b in (5,6,7,8)}
    masks=[]
    for mask in range(16):
        v=base.copy()
        for bit,b in ((8,8),(1,5),(4,7),(2,6)):
            if mask&bit:v=np.where(layers[b],layers[b],v)
        masks.append(v)
    return masks

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh work required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent changed');arc=(PARENT/'modified.arc').read_bytes();out.mkdir(parents=True)
    variants=bodies(arc);union=np.logical_or.reduce([v>0 for v in variants]);np.save(out/'body_union.npy',union)
    words=struct.unpack_from('<16H',entry(arc,9),32);board=Image.new('RGBA',(1280,640));old=Image.new('RGBA',(1280,640));records=[]
    target=render(arc,234,True)[0]
    for i,n in enumerate(FRAMES):
        board.alpha_composite(target.crop((40,40,120,120)).resize((640,640),Image.Resampling.NEAREST),(i*640,0))
        im,v,f,raw=render(arc,n);old.alpha_composite(render(arc,n,True)[0].crop((40,40,120,120)).resize((640,640),Image.Resampling.NEAREST),(i*640,0));base=variants[0]
        require(np.array_equal(base[base>0],v[base>0]),'Hurt body mismatch')
        fx=np.where(base,0,v).astype(np.uint8);save_image(fx.tobytes(),(160,160),words,out/f'old_effect_{n}.png')
        comp=composition_frame(entry(arc,3),0,n);records.append({'frame':n,'stream':f,'base_parts':comp,'effect_pixels':int(np.count_nonzero(fx))})
    board.save(out/'body_reference.png');old.save(out/'old_aura_reference.png')
    save_image(variants[0].tobytes(),(160,160),words,out/'base_234.png');save_image(variants[15].tobytes(),(160,160),words,out/'full_234.png')
    write(out/'plan.json',{'parent_sha256':PARENT_SHA,'frames':FRAMES,'body_frame':234,'partial_variants':16,'records':records,'reference_crop':[40,40,120,120],'new_game_modified':False});print({'output':out.relative_to(ROOT).as_posix(),'frames':FRAMES})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
