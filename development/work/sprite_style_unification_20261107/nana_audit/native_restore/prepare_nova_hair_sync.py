"""기존 대시73의 원화 머리 명암만 노바의 동일 텍스처 위치로 전파."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(Path(__file__).parent)]
from preview_restore import Archive,sha,write,helper,need
from prepare_native import native_write,verify
from scipy.ndimage import label
from PIL import Image
import numpy as np
D=Path(__file__).parent
BASE='4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa'
PARENT='2de8bf62a13a4b61a53143f5be7b6b6e9e34de9208f4ec60edbaaa75f767217f'
def shift(a,dx,dy):
    out=np.zeros_like(a);y,x=np.nonzero(a);need(np.all((x+dx>=0)&(x+dx<384)&(y+dy>=0)&(y+dy<384)),'Shift outside');out[y+dy,x+dx]=a[y,x];return out
def targets(original,parent):
    need(sha(original.data)==BASE and sha(parent.data)==PARENT,'Source ARC guard')
    before=original.layer(73,0)[0];after=parent.layer(73,0)[0];need(np.array_equal(before>0,after>0),'Restored hair alpha changed')
    lab,_=label(before>0,np.ones((3,3),bool));sizes=np.bincount(lab.flat);sizes[0]=0;body=lab==sizes.argmax();oldbody=np.where(body,before,0).astype(np.uint8)
    changed=before!=after;need(np.all(body[changed]),'Changed source is not body');need(np.all(np.isin(before[changed],(5,6,7,8,9)))and np.all(np.isin(after[changed],(5,6,7,8,9))),'Nonhair color included')
    sy,sx=np.nonzero(oldbody);result={};proof=[]
    for n in(217,218,220):
        old=parent.layer(n,0)[0];need(np.array_equal(original.layer(n,0)[0],old),'Nova already changed')
        y,x=np.nonzero(old);dx,dy=int(x.min()-sx.min()),int(y.min()-sy.min());expected=shift(oldbody,dx,dy);need(np.array_equal(expected,old),f'Whole old body translation not exact {n}')
        ys,xs=np.nonzero(changed);desty,destx=ys+dy,xs+dx;new=old.copy();need(np.array_equal(old[desty,destx],before[ys,xs]),'Old texture mismatch')
        new[desty,destx]=after[ys,xs];result[n,0]=new
        need(np.array_equal(old>0,new>0),'Nova alpha changed')
        proof.append({'ref':n,'parts_bank':0,'source_ref':73,'source_parts_bank':0,'translation':[dx,dy],'whole_old_body_translation_exact':True,'changed_hair_pixels':len(ys),'source_coordinates':[[int(x-160),int(y-160),int(after[y,x])]for y,x in zip(ys,xs)],'all_nonhair_pixels_exact':True,'native_effect_overlay_untouched':True})
    return result,proof
def build(original_bytes,parent_bytes,overrides=None):
    original,parent=Archive(original_bytes),Archive(parent_bytes);expected,proof=targets(original,parent)
    use=expected if overrides is None else overrides
    need(set(use)==set(expected),'Unexpected target references')
    for k in expected:need(np.array_equal(use[k],expected[k]),'Target is not the exact translated hair delta')
    result,raw,counts,streams,repack=native_write(parent,use)
    return result,use,proof,raw,counts,streams,repack
def main():
    out=D/'nova_sync_v1';need(not out.exists(),'Fresh output required')
    original=Archive((ROOT/'work/sprite_style_unification_20261107/nana_audit/provenance/PL02_U.ARC').read_bytes()) if (ROOT/'work/sprite_style_unification_20261107/nana_audit/provenance/PL02_U.ARC').exists() else None
    if original is None:
        from preview_restore import data
        assets,_=data();original=Archive(assets['PL02_U.ARC'])
    parent=Archive((D/'prepared_v1/PL02_U.ARC').read_bytes());tt,proof=targets(original,parent)
    out.mkdir();write(out/'registration.json',{'source_arc_sha256':BASE,'parent_arc_sha256':PARENT,'frames':proof,'scope':'대시73 머리 명암 변화만 노바217/218/220의 정확히 같은 몸체 좌표로 전파. 원화/효과/알파/좌표 변경 없음.'})
    for(n,pb),v in tt.items():Image.fromarray(v).save(out/f'target_{n:03}.png')
    result,tt,proof,raw,counts,streams,repack=build(original.data,parent.data);after=Archive(result);check=verify(parent,after,tt,raw)
    need(np.array_equal(parent.layer(219,5)[0],after.layer(219,5)[0]),'Flash changed');need(parent.c==after.c and parent.p==after.p,'Parts/palette changed')
    (out/'PL02_U.ARC').write_bytes(result);check.update(parent_sha256=PARENT,after_sha256=sha(result),registration=proof,streams=streams,repack=repack)
    write(out/'verification.json',check)
    helper.grid([(f'노바 {n}',[('복원 대시73',parent.composite(73,0)[0]),('이전 노바',parent.composite(n,15)[0]),('머리만 동기화',after.composite(n,15)[0])])for n in(217,218,219,220)],out/'comparison.png',4)
    print(json.dumps({'after':sha(result),'proof':[{k:v for k,v in q.items()if k!='source_coordinates'}for q in proof],'checks':check['mask_arm_combinations']}))
if __name__=='__main__':main()
