"""새 대시71의 머리 의미영역만 노바의 확인된(+3,-6) 좌표로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
def main():
 src=N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';a=Archive(src.read_bytes());need(sha(a.data)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031','Parent');inp=D/'nova_head_source_audit_v2';old=np.array(Image.open(inp/'old73body.png'));new=np.array(Image.open(inp/'new71.png'));meta=json.loads((inp/'report.json').read_text('utf8'));need(sha(old.tobytes())==meta['old_body_index_sha256'],'Old body');out=D/'nova_head_registered_v1';out.mkdir(exist_ok=False)
 Y,X=np.indices(old.shape);Y-=160;X-=160
 # 얼굴/귀/머리 하단을 실제 색인 판에서 구획. 낮은 권총·허리·다리 영역은 제외.
 oldmask=(Y<=9)|((Y==10)&(X<=10))|((Y==11)&(X==6))
 newmask=(Y<=8)|((Y==9)&((X<=-9)|(X>=-3)))|((Y==10)&((X<=-16)|(X>=-2)|((X<=-10)&np.isin(new,(1,2)))))|((Y==11)&((X<=-20)|(X>=4)))|((Y==12)&(X>=10))
 protected=(X>=0)&(Y>=8)&np.isin(old,(10,11,12))
 oldmask&=~protected;newmask&=~protected
 target=old.copy();target[oldmask]=0;target[newmask]=new[newmask];allowed=oldmask|newmask;need(np.array_equal(target[~allowed],old[~allowed]),'Body outside semantic head');need(np.array_equal(target[protected],old[protected]),'Old rear hand')
 for key,v in(('old_head',np.where(oldmask,old,0)),('new_head',np.where(newmask,new,0)),('old_head_mask',oldmask*255),('new_head_mask',newmask*255),('protected_hand',protected*255),('target_source_coords',target)):
  Image.fromarray(v.astype(np.uint8)).save(out/f'{key}.png')
 rows=[];records=[]
 for n in(217,218,220):
  q=next(q for q in meta['frames']if q['ref']==n);need(q['old73_body_translation_exact']and q['translation']==[3,-6],'Native translation');shift=np.roll(old,(-6,3),(0,1));need(np.array_equal(shift,a.layer(n)[0]),'Target old base');t=np.roll(target,(-6,3),(0,1));Image.fromarray(t).save(out/f'target_{n:03}.png');im=a.rgba(t)
  for pb in(8,5,7,6):im.alpha_composite(a.rgba(a.layer(n,pb)[0],32 if pb==7 else 16))
  rows.append((f'Nova {n}',[('new73 head source',a.rgba(new)),('old Nova',a.composite(n,15)[0]),('head only candidate',im)]));records.append({'ref':n,'translation':[3,-6],'target_index_sha256':sha(t.tobytes()),'changed_pixels':int(np.count_nonzero(target!=old)),'non_head_body_exact':True,'old_rear_hand_exact':True,'all_original_effect_layers_exact':True})
 helper.grid(rows,out/'comparison.png',5);helper.grid([('semantic head',[('old head only',a.rgba(np.where(oldmask,old,0))),('new head only',a.rgba(np.where(newmask,new,0))),('remaining original body',a.rgba(np.where(oldmask,0,old))),('combined body',a.rgba(target))])],out/'mask_review.png',7)
 write(out/'registration.json',{'source_arc_sha256':sha(a.data),'new_head_source_path':meta['new_source'],'new_head_source_sha256':meta['new_source_sha256'],'source_body_sha256':sha(old.tobytes()),'new_head_pixels':int(np.count_nonzero(new[newmask])),'old_head_pixels':int(np.count_nonzero(old[oldmask])),'frames':records,'scope':'노바 몸체 전체를 새 대시로 교체하지 않고, 실제 색인판으로 분리한 머리/얼굴/귀만 새 원화로 등록. 219 실루엣 효과·원 손/하체/원효과는 그대로.','native_packed':False,'art_review_pending':True,'runtime_verified':False});print(out)
if __name__=='__main__':main()
