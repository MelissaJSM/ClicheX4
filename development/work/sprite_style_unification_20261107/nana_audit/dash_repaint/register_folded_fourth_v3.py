"""71/75 새 발 원화의 하체만 등록하고 수용된 상체는 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
from refine_second_inputs import one
sys.path.insert(0,str(D))
from register_last_keys import horizontal_crop
from align_second_feet import transform
from prepare_next_guides import body_path
def main():
 p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());src=D/'fourth_folded_contacts_v3/generated.png';need(digest(src)=='42357e3afdcd284d5d6b48f1afd6b62298fa0a08f9575e9fba6a881407029178','Source');out=D/'fourth_folded_registered_v3';need(not out.exists(),'Fresh');out.mkdir();im=Image.open(src).convert('RGBA');im=im.crop((0,0,im.width,im.height//2));pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],float);rows=[];proof=[]
 for k,n in enumerate((71,75)):
  crop,box=horizontal_crop(im,k);q=next(q for q in p['frames']if q['ref']==n);z,r=one(crop,q,pal);crop.save(out/f'source_{n:03}.png');old=np.array(Image.open(D/'fourth_contacts_probe_v2'/f'fourth_{n:03}.png'));new=old.copy();new[176:]=z[176:];need(np.array_equal(old[:176],new[:176]),'Upper exact');need(label(new>0,np.ones((3,3)))[1]==1,'Connected legs');Image.fromarray(new).save(out/f'fourth_{n:03}.png');a.rgba(new,16).save(out/f'fourth_{n:03}_rgba.png');_,sample,_=transform(crop,r,z,35,[],pal,n);Image.fromarray(sample).save(out/f'source_rgba8_{n:03}.png');r.update(ref=n,source_crop=box,source_art_sha256=digest(src),world_y_gte_only=16,old_upper_exact=True,sha256=sha(new.tobytes()));proof.append(r);rows.append((f'{n} 하체 국소',[('기본',a.rgba(np.array(Image.open(body_path(n))))),('포스 원화',a.rgba(old,16)),('두 발 새 원화',a.rgba(new,16))]))
 helper.grid(rows,out/'comparison.png',8);write(out/'registration.json',{'source_arc_sha256':sha(a.data),'frames':proof,'native_packed':False,'runtime_verified':False});print(json.dumps(proof))
if __name__=='__main__':main()
