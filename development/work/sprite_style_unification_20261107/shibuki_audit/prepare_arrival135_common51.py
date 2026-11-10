"""생성 원화의 공통 신체를 기존 게임 조립 방식으로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page,metrics
from probe_ultimate_arrival_common import regions
from inspect_ultimate_hurt_common import grid
SOURCE=H/'ultimate_arrival135_alpha51';OUT=H/'ultimate_arrival135_common51'
def main():
 need(not OUT.exists(),'Fresh output required');OUT.mkdir()
 src=json.loads((H.parent/'staging_br_v31.json').read_text('utf8'))['resources']['PL02_U.ARC'];p=ROOT/src['path'];need(sha(p.read_bytes())==src['after'],'Parent changed');a=Archive(p.read_bytes())
 b=np.array(Image.open(SOURCE/'before_135_indices.png'));v=np.array(Image.open(SOURCE/'after_135_indices.png'))
 rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8)
 yy,xx=np.indices(b.shape);x=xx-160;y=yy-160
 head=(y < -3)|(x>=8)
 legs=regions([[(-12,9),(-7,9),(-6,12),(-9,15),(-9,19),(-6,20),(-6,24),(-16,24),(-16,17),(-14,14)],[(-1,9),(4,9),(8,13),(11,17),(11,24),(1,24),(1,18),(-1,15)]])
 hands=np.zeros_like(head)
 for x0,y0,x1,y1 in [(-13,-3,-8,1),(0,4,4,8)]:hands[160+y0:160+y1,160+x0:160+x1]=True
 hands &= np.isin(b,[10,11,12,13])
 common=head|legs|hands;after=v.copy();after[common]=lut[b][common]
 outside=(after>0)&(b==0);oy,ox=np.where(outside)
 for name,m in [('head',head),('legs',legs),('hands',hands),('common',common),('outside',outside)]:Image.fromarray(m.astype('uint8')*255).save(OUT/f'{name}_mask.png')
 for form,z,pal,mask in [('before',b,16,15),('after',after,0,0)]:
  Image.fromarray(z).save(OUT/f'{form}_135_indices.png');a.rgba(z,pal).save(OUT/f'{form}_135.png');page([(f'135 old {form}',a.composite(135,mask)[0]),(f'135 new {form}',a.rgba(z,pal))],a.composite(0,mask)[0],OUT/f'{form}_comparison.png',cols=2,scale=5)
 grid([a.rgba(b,16),a.rgba(after)],OUT/'135_grid.png',['new jacket135','new bare-arm135 shared anatomy'])
 write(OUT/'report.json',{'parent':src,'source_files':{str((SOURCE/f'{f}_135_indices.png').relative_to(ROOT)):sha((SOURCE/f'{f}_135_indices.png').read_bytes())for f in ['before','after']},'palette_map':lut.tolist(),'outside_before':[[int(x)-160,int(y)-160]for y,x in zip(oy,ox)],'common_pixels':int(common.sum()),'changed_after_pixels':int((v!=after).sum()),'before_exact':True,'noncommon_exact':bool(np.array_equal(after[~common],v[~common])),'new_art_only':True,'wholebody_resized':False,'palette_changed':False,'visual_review_pending':True,'runtime_verified':False})
 print(json.dumps({'outside':int(outside.sum()),'before':metrics(a.rgba(b,16)),'after':metrics(a.rgba(after))}))
if __name__=='__main__':main()
