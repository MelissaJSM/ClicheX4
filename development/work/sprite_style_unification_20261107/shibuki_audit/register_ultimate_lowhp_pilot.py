"""새 저체력2의상을 페이지 고정 축척/접지로 등록한다. 패킹 및 게임 쓰기 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import sha,need,write
I=H/'ultimate_lowhp_inputs01';P=H/'prepared_run_complete03/PL02_U.ARC';O=H/'ultimate_lowhp_native01'
PSHA='c7eb1c7998a6780d04f4397a64af653265e3d83985c3c05768dd3de46eae5265'
GEN='24a216ae930580ed2938cd956540ee99a753d8d05b404d5de86745d2f569a6ba'
def sole(q):
 yy,xx=np.nonzero(q);ym=int(yy.max());s=xx[yy>=ym-1];return int(round(float(s.mean()))),ym
def move(q,dx,dy):
 y,x=np.nonzero(q);out=np.zeros_like(q);out[y+dy,x+dx]=q[y,x];return out
def main():
 need(not O.exists(),'Fresh output required');need(sha(P.read_bytes())==PSHA,'Parent changed');need(sha((I/'generated.png').read_bytes())==GEN,'Source art changed')
 a=Archive(P.read_bytes());im=Image.open(I/'generated.png').convert('RGBA');h=round(im.height*128/im.width)
 need(h==64,'Unexpected page ratio');sample=np.array(im.resize((128,h),Image.Resampling.NEAREST));O.mkdir()
 result={};records=[]
 for col,name,mask,start in((0,'before',15,16),(1,'after',0,0)):
  colors=np.array([[(int(v)>>s&31)*255//31 for s in(0,5,10)]for v in a.words[start:start+16]],np.int32)
  rgb=sample[:,col*64:(col+1)*64];d=((rgb[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3)
  idx=(d.argmin(2)+1).astype(np.uint8);idx[rgb[:,:,3]<128]=0
  q=np.zeros((384,384),np.uint8);q[128:192,128:192]=idx
  oldim=a.composite(120,mask)[0];oldalpha=np.array(oldim.getchannel('A'))
  x,y=sole(q);ox,oy=sole(oldalpha);dx,dy=ox-x,oy-y;v=move(q,dx,dy);out=a.rgba(v,start)
  Image.fromarray(q).save(O/f'{name}_raw_indices.png');Image.fromarray(v).save(O/f'{name}_indices.png');out.save(O/f'{name}.png');result[name]=v
  page([('120 current',oldim),('120 generated',out)],a.composite(0,mask)[0],O/f'{name}_comparison.png',cols=2,scale=5)
  records.append({'form':name,'palette_start':start,'translation':[dx,dy],'source_unregistered_metrics':metrics(a.rgba(q,start)),'registered_metrics':metrics(out),'old_metrics':metrics(oldim),'ground_y_exact':y+dy==oy,'old_sole_center_world':[ox-160,oy-160],'target_sole_center_world':[x+dx-160,y+dy-160]})
 board=Image.new('RGBA',(1024,512))
 for col,name in enumerate(('before','after')):board.alpha_composite(Image.open(O/f'{name}.png').crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,0))
 board.save(O/'pair.png')
 outside=(result['after']>0)&(result['before']==0);Image.fromarray(outside.astype(np.uint8)*255).save(O/'outside_after_alpha.png')
 info={'source':str((I/'generated.png').relative_to(ROOT)),'source_sha256':GEN,'source_dimensions':im.size,'native_page':[128,h],'fixed_uniform_scale':128/im.width,'individual_bbox_resize':False,'old_head_or_body_copied':False,'forms':records,'new_after_outside_before_alpha':int(outside.sum()),'native_pixels_repainted':False,'packed':False,'accepted':False,'next':'실제 비교를 보고 대기 체형/총높이·새머리/다리공유·의상알파 정합 판정. 임의 잘라내기로 맞추지 않는다.'}
 write(O/'registration.json',info);print(json.dumps(info,ensure_ascii=False))
if __name__=='__main__':main()
