"""벽6사격의 실제 총구와 새 몸체를 같은 좌표로 제공한다. 그림 제작 아님."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'ultimate_air_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from check_first_geometry import full
def main():
 source=N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC';need(digest(source)=='122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18','Parent');a=Archive(source.read_bytes());out=D/'weapon_constraints_v1';out.mkdir(exist_ok=False);Y,X=np.indices((384,384));rows=[];allq=[]
 for n in range(56,67,2):
  v=full(a,n);yy,xx=np.nonzero(v);mx=int(xx.min());my=float(np.median(yy[xx==mx]));mask=(X>=mx)&(X<mx+8)&(Y>=int(np.floor(my))-2)&(Y<=int(np.ceil(my))+3);w=np.where(mask,v,0).astype(np.uint8);yy,xx=np.nonzero(mask);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];Image.fromarray(w).save(out/f'case_{n:03}.png');vis=a.rgba(v,16);ImageDraw.Draw(vis).rectangle(box,outline=(255,80,40,255));rows.append((f'Original firing {n}',[('original actual case window',vis),('original case only',a.rgba(w,16)),('current after missing arm evidence',a.composite(n,0)[0])]))
  gy,gx=np.nonzero((v==14)&(Y<160));eye=[int(np.median(gx))-160,int(np.median(gy))-160];allq.append({'ref':n,'paired_body_ref':n-1,'muzzle_x':mx-160,'gun_window_world':[q-160 for q in box],'eye_world':eye,'muzzle_left_from_eye':eye[0]-(mx-160),'barrel_pixels':int((w>0).sum()),'barrel_index_sha256':sha(w.tobytes())})
 for i in(0,3):helper.grid(rows[i:i+3],out/f'review_{i//3+1}.png',6)
 write(out/'manifest.json',{'source_arc_sha256':digest(source),'frames':allq,'gun_window_width':8,'actual_native_firing_position':True,'after_missing_arm_is_static_observation':True})
 for page,refs in [('a',(56,58,60)),('b',(62,64,66))]:
  dest=D/f'firing_{page}_inputs_v1';dest.mkdir(exist_ok=False);boards={k:Image.new('RGBA',(1280,1280))for k in('before_fixed_body_and_weapon','after_fixed_body_and_weapon','original_shot_geometry','original_weapon_only')};recs=[]
  for i,n in enumerate(refs):
   bp=D/'canonical_cases_probe_v2'/f'before_{n-1:03}.png';ap=D/'costume_pair_probe_v2'/f'after_{n-1:03}.png';b=np.array(Image.open(bp));p=np.array(Image.open(ap));held=np.array(Image.open(D/'canonical_cases_probe_v2'/f'case_{n-1:03}.png'));w=np.array(Image.open(out/f'case_{n:03}.png'));b[held>0]=0;p[held>0]=0;b[w>0]=w[w>0];p[w>0]=w[w>0]
   ims={'before_fixed_body_and_weapon':a.rgba(b,16),'after_fixed_body_and_weapon':a.rgba(p,0),'original_shot_geometry':a.composite(n,15)[0],'original_weapon_only':a.rgba(w,16)}
   for k,im in ims.items():boards[k].alpha_composite(im.crop((112,112,208,208)).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640))
   q=next(x for x in allq if x['ref']==n);recs.append({**q,'before_body_sha256':digest(bp),'after_body_sha256':digest(ap),'held_gun_removed_for_input':True,'tucked_hand_is_to_be_redrawn':True})
  for k,im in boards.items():
   if k!='original_weapon_only':im.alpha_composite(a.composite(85,0 if k.startswith('after')else 15)[0].crop((112,112,208,208)).resize((640,640),Image.Resampling.NEAREST),(640,640))
   im.save(dest/f'{k}.png')
  style=Image.new('RGBA',(1280,1280))
  for i,(n,m)in enumerate(((0,15),(85,15),(34,15),(50,15))):style.alpha_composite(a.composite(n,m)[0].crop((112,112,208,208)).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640))
  style.save(dest/'accepted_before_style.png')
  style=Image.new('RGBA',(1280,1280))
  for i,(n,m)in enumerate(((0,0),(85,0),(34,0),(50,0))):style.alpha_composite(a.composite(n,m)[0].crop((112,112,208,208)).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640))
  style.save(dest/'accepted_after_style.png')
  write(dest/'manifest.json',{'frames':recs,'cell':[640,640],'window_world':[-48,-48,48,48],'fourth_cell_style_only':True,'input_hashes':{p.name:digest(p)for p in dest.glob('*.png')},'native_packed':False,'runtime_verified':False})
 print(json.dumps(allq))
if __name__=='__main__':main()
