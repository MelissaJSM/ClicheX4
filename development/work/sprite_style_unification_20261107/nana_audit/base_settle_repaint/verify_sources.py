"""새138 고정셀2개→권총/공통손·다리 표본→139파생10층 제작자재구성."""
from pathlib import Path
import sys,json,importlib.util,argparse
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
spec=importlib.util.spec_from_file_location('source_quantizer',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
Y,X=np.indices((384,384));Y-=160;X-=160
read=lambda p:json.loads(p.read_text('utf8'))
def check(z,p):need(np.array_equal(z,np.array(Image.open(p))),str(p));return z
def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--hair',action='store_true');args=ap.parse_args()
 meta=read(D/'body_inputs_v1/manifest.json');a=Archive((ROOT/meta['art_parent_arc']).read_bytes());need(sha(a.data)==meta['art_parent_arc_sha256'],'원화부모')
 art=D/'body_v1/generated.png';need(digest(art)==read(art.parent/'generation.json')['sha256'],'생성원화');im=Image.open(art).convert('RGBA');bodies={};cells=[]
 for q in read(D/'body_registered_v1/registration.json')['frames']:
  form=q['form'];start=16 if form=='fourth'else 0;pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[96:224,112:208]=reg.register(im.crop(q['source_crop']),(96,128),pal,'area_vote');bodies[form]=check(z,D/f'body_registered_v1/{form}_138_indices.png');cells.append({'form':form,'crop':q['source_crop'],'native_sha256':sha(z.tobytes())})
 cm=read(D/'contacts_probe_v1/manifest.json');u=Archive((ROOT/cm['canonical_donor_path']).read_bytes());need(sha(u.data)==cm['canonical_donor_sha256'],'정본원천');z=u.layer(85)[0];mask=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10));coords=[[int(x-160),int(y-160),int(z[y,x])]for y,x in np.argwhere(mask)];need(coords==cm['canonical20']and len(coords)==20,'정본20')
 case=np.zeros_like(z)
 for sx,sy,v in coords:case[sx-9+160,sy+2+160]=v
 check(case,D/'contacts_probe_v1/canonical_case.png');weapons={}
 for q in cm['frames']:
  form=q['form'];src=bodies[form];target=src.copy();skin=(X>=-11)&(X<-4)&(Y>=-27)&(Y<-23)&np.isin(src,(10,11,12,13))
  for x,y,v in q['generated_weapon_removed']:need(int(src[y+160,x+160])==v,'무기제거표본');target[y+160,x+160]=0
  visible=(case>0)&~skin;target[visible]=case[visible];target[skin]=src[skin];weapons[form]=check(target,D/f'contacts_probe_v1/{form}_138_weapon.png')
 b=weapons['base'];f=weapons['fourth'].copy();shared=(X>=-11)&(X<-4)&(Y>=-32)&(Y<-23);f[shared]=b[shared];source=f.copy()
 for q in cm['fourth_same_leg_source_links']:
  x,y=q['destination'];sx,sy=q['source'];need(y==sy and abs(sx-x)<=2,'같은행/2픽셀한계');need(int(source[sy+160,sx+160])==q['index'],'새다리표본');f[y+160,x+160]=q['index']
 check(b,D/'contacts_probe_v1/base_138_indices.png');check(f,D/'contacts_probe_v1/fourth_138_indices.png');full=np.where(f,f,b).astype(np.uint8);check(full,D/'contacts_probe_v1/full_138_indices.png')
 hair_records=[]
 if args.hair:
  hm=read(D/'hair_registered_v1/manifest.json');hp=ROOT/hm['generated_path'];need(digest(hp)==hm['generated_sha256'],'새 머리 원화');hi=Image.open(hp).convert('RGBA');bodies={'base':b,'fourth':f}
  for q in hm['frames']:
   form=q['form'];start=16 if form=='fourth'else 0;pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);donor=np.zeros_like(b);donor[96:224,112:208]=reg.register(hi.crop(q['source_crop']),(96,128),pal,'area_vote');need(sha(donor.tobytes())==q['source_indices_sha256'],'새 머리 고정셀');old=bodies[form];mask=np.zeros_like(b,dtype=bool)
   for y,(lo,right) in q['spans'].items():mask[int(y)+160,lo+160:right+161]=True
   mask &= np.isin(old,(5,6,7,8,9));need(sha(mask.tobytes())==q['mask_sha256'],'머리 의미영역');new=old.copy();valid=mask&np.isin(donor,range(1,10));new[valid]=donor[valid];need(np.array_equal(new>0,old>0),'머리 알파 불변');need(np.array_equal(new[~mask],old[~mask]),'머리 밖 불변');links=[{'world':[int(x-160),int(y-160)],'before':int(old[y,x]),'source':int(donor[y,x])}for y,x in np.argwhere(new!=old)];need(links==q['source_links'],'머리 실제표본');bodies[form]=check(new,D/f'hair_registered_v1/{form}_138_indices.png');hair_records.append({'form':form,'changed':len(links),'alpha_exact':True,'outside_hair_exact':True})
  b=bodies['base'];f=bodies['fourth'];full=np.where(f,f,b).astype(np.uint8)
 own=np.full(b.shape,6,np.uint8);own[(Y>=2)|((X>=7)&(Y>=-10))]=8;own[(Y<-11)&(X>=-7)]=5;oldown=own.copy();own[(X>=6)&(Y>=-12)]=8;own[(X<=-7)&(Y<-10)]=7;arm=poly([(0,-12),(6,-10),(8,-5),(3,-4),(-1,-6)]);own[arm]=7;oldown[(X<=-7)&(Y<-10)]=7;oldown[arm]=7
 pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full];change=((full!=b)|((f>0)&pc))&(full>0);ls={0:b,**{pb:np.where(change&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}};changed=change&(own!=oldown)
 if args.hair:check(own,D/'joint_layers_probe_v2/owner_138.png')
 else:need(int(changed.sum())==10,'베일소유10셀')
 count=0
 for n,dy in((138,0),(139,-1)):
  for pb,z in ls.items():check(np.roll(z,dy,0),D/('joint_layers_probe_v3'if args.hair else'joint_layers_probe_v2')/f'layer{pb}_{n:03}.png');count+=1
 write(D/('source_reconstruction_v2.json'if args.hair else'source_reconstruction_v1.json'),{'passed':True,'generated_pages':2 if args.hair else 1,'generated_art_sha256':digest(art),'fixed_cells':cells,'hair_source_cells':hair_records,'target_layers_reconstructed':count,'canonical_ref':85,'canonical_texels':20,'same_hand_source':'new base138','same_leg_source_links':len(cm['fourth_same_leg_source_links']),'veil_owner_changed_cells':[{'world':[int(x-160),int(y-160)],'index':int(full[y,x]),'old_owner':int(oldown[y,x]),'new_owner':8}for y,x in np.argwhere(changed)],'old_bitmap_reused':False,'scope':'제작자RGB 고정셀 재양자화와정본/의미층 재구성.최종ARC/독립reader/원MIPS/실기는별도.','runtime_verified':False});print(json.dumps({'passed':True,'cells':2+len(hair_records),'layers':count,'same_leg_links':len(cm['fourth_same_leg_source_links']),'owner_cells':int(changed.sum())}))
if __name__=='__main__':main()
