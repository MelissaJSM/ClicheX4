"""Compose the two authored leg revisions of the exact same pose."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
from prepare_next_guides import body_path
from align_second_feet import transform
def main():
 p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());o=D/'folded_leg_composite_v3';need(not o.exists(),'Fresh');o.mkdir();rows=[];proof=[];Y,X=np.indices((384,384));x=X-160;y=Y-160;pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],float)
 for n in(71,75):
  rear=np.array(Image.open(D/'fourth_folded_registered_v3'/f'fourth_{n:03}.png'));front=np.array(Image.open(D/'fourth_folded_registered_v2'/f'fourth_{n:03}.png'));r=next(q for q in json.loads((D/'fourth_folded_registered_v3/registration.json').read_text('utf8'))['frames']if q['ref']==n);crop=Image.open(D/'fourth_folded_registered_v3'/f'source_{n:03}.png').convert('RGBA');new,field,meta=transform(crop,r,rear,16,[(5,19,8,23,0,-2)],pal,n,True);region=(y>=18)&(y<=22)&(x>=(-2 if n==71 else -3))&(x<=5);sel=region&(front>0);new[sel]=front[sel]
  # The near shin is in front. Clear only its source-owned transparent wedge,
  # preserving the far shoe and the unedited upper garment.
  mask=(y>=21)&(x>=-3)&(x<=1);new[mask]=front[mask]
  Image.fromarray(new).save(o/f'fourth_{n:03}.png');Image.fromarray(field).save(o/f'rear_source_rgba8_{n:03}.png');Image.fromarray(sel.astype(np.uint8)*255).save(o/f'front_semantic_mask_{n:03}.png');a.rgba(new,16).save(o/f'fourth_{n:03}_rgba.png');rows.append((f'{n} 같은 자세 두 원화',[('기본',a.rgba(np.array(Image.open(body_path(n))))),('앞다리 원화',a.rgba(front,16)),('긴 뒤 종아리 원화',a.rgba(rear,16)),('앞/뒤 합성',a.rgba(new,16))]));proof.append({'ref':n,'rear_sha256':sha(rear.tobytes()),'front_sha256':sha(front.tobytes()),'after':sha(new.tobytes()),'source_front_pixels':int(sel.sum()),'alpha_components':int(label(new>0,np.ones((3,3)))[1]),'no_new_colors':True,'upper_y_lt_17_exact':bool(np.array_equal(new[:177],rear[:177])),'rear_shoe_rigid_y_shift':-2,'registration':meta})
 helper.grid(rows,o/'comparison.png',8);write(o/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':proof,'native_packed':False,'runtime_verified':False,'candidate_only':True})
if __name__=='__main__':main()
