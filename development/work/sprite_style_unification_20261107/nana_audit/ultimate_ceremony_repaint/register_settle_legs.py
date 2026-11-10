"""138 새 종아리 원화를 고정셀로 읽고 국소 등록한다."""
from pathlib import Path
import sys,json,argparse,shutil
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
def main():
 ap=argparse.ArgumentParser();ap.add_argument('source');args=ap.parse_args();src=Path(args.source);artdir=D/'settle_legs_v1';artdir.mkdir(exist_ok=False);art=artdir/'generated.png';shutil.copyfile(src,art);im=Image.open(art).convert('RGBA');need(im.size==(1536,1024),'고정셀 실제크기');inp=D/'settle_legs_inputs_v1';write(artdir/'generation.json',{'tool':'builtin imagegen','source_output_path':str(src),'source_sha256':digest(src),'workspace_path':art.relative_to(ROOT).as_posix(),'workspace_sha256':digest(art),'size':list(im.size),'prompt_path':(inp/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(inp/'prompt.txt'),'input_manifest_sha256':digest(inp/'manifest.json'),'scope':'138 종아리와 옆구리 그늘만 국소 보완하는 새 원화. 기존 동결 자원 불변.'})
 a=Archive((N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC').read_bytes());out=D/'settle_legs_registered_v1';out.mkdir(exist_ok=False);fixed=[];bases=[];records=[]
 for i,(form,start)in enumerate((('before',16),('after',0))):
  cell=im.crop((i*768,0,(i+1)*768,1024));ar=np.array(cell);pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);z=np.zeros((384,384),np.uint8);z[96:224,112:208]=register(cell,(96,128),pal,'area_vote');fixed.append(z);bases.append(np.array(Image.open(D/f'common_hands_probe_v1/{form}_138.png')));Image.fromarray(z).save(out/f'{form}_fixed.png')
  records.append({'form':form,'source_crop':[i*768,0,(i+1)*768,1024],'alpha_ge128_count':int((ar[:,:,3]>=128).sum()),'native_components8':int(label(z>0,np.ones((3,3)))[1]),'native_fixed_sha256':sha(z.tobytes())})
 yy,xx=np.indices((384,384));yy-=160;xx-=160
 # Legs retain their source coordinates. The accepted shoes at y20..23 are protected.
 legs=(yy>=4)&(yy<20)&(xx>=-17)&(xx<15)
 # Only the small side-shadow region; raised/opposite arms, face, belt and hands are excluded.
 sides=(yy>=-6)&(yy<0)&(xx>=-7)&(xx<-3)
 mask=legs|sides;outputs=[];rows=[]
 for i,(form,start)in enumerate((('before',16),('after',0))):
  z=bases[i].copy();z[mask]=fixed[i][mask]
  if i==1:
   # Both forms share precisely the newly drawn legs from the jacket source.
   shared=fixed[0].copy();shared[shared==15]=13;z[legs]=shared[legs]
  need(np.array_equal(z[~mask],bases[i][~mask]),'원화 국소 밖 보호');need(np.array_equal(z[yy>=20],bases[i][yy>=20]),'기존 새 신발/바닥 보호');Image.fromarray(z).save(out/f'{form}_138.png');outputs.append(z)
  roi=(yy>=6)&(yy<20)&(xx>-18)&(xx<18);records[i].update({'changed_pixels':int((z!=bases[i]).sum()),'outside_local_change':0,'floor_protected_y':20,'legs_y6_19_opaque':int(((z>0)&roi).sum()),'legs_y6_19_dark1_4':int((np.isin(z,(1,2,3,4))&roi).sum()),'components8':int(label(z>0,np.ones((3,3)))[1]),'target_sha256':sha(z.tobytes())});rows.append((form,[('accepted idle',a.composite(0,15 if start else 0)[0]),('previous thin138',a.rgba(bases[i],start)),('new fixed source',a.rgba(fixed[i],start)),('local registration',a.rgba(z,start))]))
 Image.fromarray(mask.astype(np.uint8)*255).save(out/'edit_mask.png');Image.fromarray(legs.astype(np.uint8)*255).save(out/'shared_legs_mask.png');helper.grid(rows,out/'comparison.png',7);outside=(outputs[1]>0)&(outputs[0]==0);write(out/'manifest.json',{'source_art':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'fixed_native_size':[96,128],'full_body_rescale':False,'old_pixels_copied':0,'legs_mask_world':[-17,4,15,20],'side_mask_world':[-7,-6,-3,0],'common_legs_source':'before138 new local source','after_outside_before':[[int(x-160),int(y-160)]for y,x in np.argwhere(outside)],'frames':records,'native_packed':False,'runtime_verified':False});print(json.dumps({'source_sha256':digest(art),'frames':records,'after_outside_before':int(outside.sum())}))
if __name__=='__main__':main()
