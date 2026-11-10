"""새156 팔 donor 및 발목/샌들 강체등록. 새 도트 제작/전신변형 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
 out=H/'ultimate_return_contacts02';need(not out.exists(),'Fresh probe');out.mkdir();s=H/'ultimate_return_native01';d=H/'ultimate_return_arm_native02';arc=Archive((H/'prepared_ultimate_victory01/PL02_U.ARC').read_bytes());rgb=np.array([[(int(w)>>z&31)*255//31 for z in (0,5,10)]for w in arc.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);yy,xx=np.indices((384,384));yy-=160;xx-=160
 source={f:np.array(Image.open(s/f'{f}_156_indices.png'))for f in ('before','after')};donor={f:np.array(Image.open(d/f'{f}_156_indices.png'))for f in source}
 arms=((xx<=-4)|(xx>=5))&(yy>=-3)&(yy<=5);v={f:a.copy()for f,a in source.items()}
 for f in v:v[f][arms]=donor[f][arms]
 # 손 아래 뒷머리 외곽 한 셀은 첫 새 원화의 두폼 모두에 존재한다.
 # 팔 donor의 before에만 빠진 이 끝점을 첫 새 원화에서 보존한다.
 hair_tip=(xx==11)&(yy==5);need(int(source['before'][165,171])==2 and int(source['after'][165,171])==2,'New source hair edge changed');v['before'][hair_tip]=source['before'][hair_tip]
 # 첫 원화에 이미 존재하는 발목/샌들 조각만 이동한다. 원행은 접속용으로 보존.
 base=v['before'].copy();left=(xx>=-5)&(xx<=0)&(yy>=16)&(yy<=21);right=(xx>=1)&(xx<=6)&(yy>=16)&(yy<=21);v['before'][left|right]=0
 for mask,dx,dy in ((right,0,-1),(left,1,1)):
  y,x=np.nonzero(mask&(base>0));v['before'][y+dy,x+dx]=base[y,x]
 seam=(xx>=-4)&(xx<=0)&(yy==16);v['before'][seam]=base[seam]
 # 후폼은 동일한 새 머리/사지 모듈을 원래 CLUT0에 대응시킨다.
 head=(yy<=-4);hair=(yy>=6)&(yy<=12)&((xx<=-6)|(xx>=6));legs=(yy>=9)&(xx>=-5)&(xx<=6);hands=((xx<=-11)|(xx>=12))&(yy>=-2)&(yy<=3);common=head|hair|legs|hands;v['after'][common]=lut[v['before']][common]
 for name,m in [('arms_donor',arms),('first_new_hair_tip',hair_tip),('left_ankle_module',left),('right_ankle_module',right),('left_join_row',seam),('head',head),('hair',hair),('legs',legs),('hands',hands),('common',common)]:Image.fromarray(m.astype(np.uint8)*255).save(out/f'{name}_mask.png')
 outside=(v['after']>0)&(v['before']==0);Image.fromarray(outside.astype(np.uint8)*255).save(out/'outside_before_mask.png');oy,ox=np.nonzero(outside);rows=[]
 for f,pal,mask in [('before',16,15),('after',0,0)]:
  a=v[f];Image.fromarray(a).save(out/f'{f}_156_indices.png');im=arc.rgba(a,pal);im.save(out/f'{f}_156.png');lab,n=label(a>0,np.ones((3,3)));page([(f'156 parent {f}',arc.composite(156,mask)[0]),(f'156 first new {f}',arc.rgba(source[f],pal)),(f'156 contact probe {f}',im)],arc.composite(0,mask)[0],out/f'{f}_comparison.png',cols=3,scale=5);rows.append({'form':f,'metrics':metrics(im),'components':sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True),'head_source_exact':bool(np.array_equal(a[head],source[f][head]))if f=='before'else bool(np.array_equal(a[head],lut[v['before']][head])),'donor_changed_pixels':int(((donor[f]!=source[f])&arms).sum()),'first_new_torso_exact':bool(np.array_equal(a[(xx>=-3)&(xx<=4)&(yy>=-3)&(yy<=8)],source[f][(xx>=-3)&(xx<=4)&(yy>=-3)&(yy<=8)]))})
 write(out/'report.json',{'status':'static_probe_not_accepted','sources':{str(p.relative_to(ROOT)):sha(p.read_bytes())for p in [s/'report.json',d/'report.json',s/'before_156_indices.png',s/'after_156_indices.png',d/'before_156_indices.png',d/'after_156_indices.png']},'rows':rows,'after_outside_before':[[int(x)-160,int(y)-160,int(v['after'][y,x])]for y,x in zip(oy,ox)],'leg_transforms':[{'module':'right_ankle_and_sandal','dx':0,'dy':-1},{'module':'left_ankle_and_sandal','dx':1,'dy':1,'preserved_join_row':16}],'before_to_after_lut':lut.tolist(),'new_pixel_painting':False,'old_art_copied':False,'global_resize':False,'arc_written':False,'limitations':['손 위치는 수용기본156보다 안쪽2px/위2px이며 실제귀환 접점 의무와 미술 판단을 분리하여 검토한다.','발 앞뒤등록은 새 원화의 기존도트 강체이동. 원US 전신 완전복원이 아니다.','after의 공통부 밖 원화 실루엣/색 차이는 후속 부분레이어 정합 대상이다.']});print(json.dumps({'rows':rows,'outside_count':int(outside.sum()),'outside':[[int(x)-160,int(y)-160,int(v['after'][y,x])]for y,x in zip(oy,ox)]}))
if __name__=='__main__':main()
