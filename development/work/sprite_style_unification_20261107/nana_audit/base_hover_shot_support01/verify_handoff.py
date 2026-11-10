"""8 사격팔 지원후보의 원화출처·몸체 보호·원점 접점 자체검사."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def main():
 src=D/'arm_joint_probe_v2';out=D/'handoff01';out.mkdir(exist_ok=True);meta=json.loads((src/'manifest.json').read_text('utf8'));imeta=json.loads((D/'inputs_a01/manifest.json').read_text('utf8'));parent=ROOT/imeta['parent_arc'];a=Archive(parent.read_bytes());need(digest(parent)==imeta['parent_sha256'],'parent');canonical_parent=N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';ca=Archive(canonical_parent.read_bytes());coords=meta['canonical_source_texels'];need(all(int(ca.layer(85)[0][y+160,x+160])==v for x,y,v in coords),'실제 정본85 20셀')
 fxpath=W/'zero_audit/nana_ultimate_hover_muzzle01/lemon_first_frame.npy';fx=np.load(fxpath);need(int((fx>0).sum())==188,'원 첫효과188');rows=[];frames=[]
 for q in meta['frames']:
  n,form,start=q['ref'],q['form'],q['palette_start'];key=f'{form}_{n}';body=np.array(Image.open(ROOT/q['body_source']));z=np.array(Image.open(src/f'{key}_indices.png'));mask=np.array(Image.open(src/f'{key}_edit_mask.png'))>0;skin=np.array(Image.open(src/f'{key}_skin_mask.png'))>0;gun=np.array(Image.open(src/f'{key}_gun_indices.png'));arms=np.array(Image.open(src/f'{key}_arm_indices.png'));donor=np.array(Image.open(D/'registered_sources01'/f'{key}_indices.png'));dx,dy=q['arm_rigid_translation'];shifted=np.roll(np.roll(donor,dy,axis=0),dx,axis=1);ox,oy=q['engine_origin'];need(np.array_equal(z[~mask],body[~mask]),'mask 밖 exact');need(np.array_equal(z[Y>=3],body[Y>=3]),'하체 exact');need(np.array_equal(z[(X>=1)],body[(X>=1)]),'뒤팔/후면 exact');need(np.array_equal(z[(Y<=-9)&(X>=-11)&~(gun>0)],body[(Y<=-9)&(X>=-11)&~(gun>0)]),'얼굴/머리 exact');need(np.array_equal(z[(gun>0)&~skin],gun[(gun>0)&~skin]),'정본 가시셀');need(all(z[oy-1+160,ox+1+160]==gun[oy-1+160,ox+1+160]for _ in [0]),'입구윗행');need(z[oy+160,ox+1+160]==gun[oy+160,ox+1+160],'입구아랫행');need(int(label(z>0,np.ones((3,3)))[1])==1,'1몸체')
  source_links=[]
  for y,x in np.argwhere(z!=body):
   if skin[y,x]:kind='new_skin';source=[int(x-dx-160),int(y-dy-160)];need(z[y,x]==shifted[y,x],'피부source')
   elif gun[y,x]>0:kind='canonical85';source=[int(x-(ox+23)-160),int(y-(oy+9)-160)];need(z[y,x]==gun[y,x],'정본source')
   elif z[y,x]==0:kind='clear_old_arm_or_generated_barrel';source=None
   else:kind='new_sleeve';source=[int(x-dx-160),int(y-dy-160)];need(z[y,x]==shifted[y,x],'소매source')
   source_links.append({'world':[int(x-160),int(y-160)],'from':int(body[y,x]),'to':int(z[y,x]),'source_type':kind,'source_world':source})
  effect=np.roll(np.roll(fx,oy,axis=0),ox,axis=1);pic=a.rgba(z,start);neutral=np.zeros((384,384,4),np.uint8);neutral[effect>0]=(255,210,30,125);overlay=Image.fromarray(neutral);overlay.alpha_composite(pic);dr=ImageDraw.Draw(overlay);dr.line((160+ox-1,160+oy,160+ox+1,160+oy),fill='#00eeff');rows.append((f'{form} {n} origin {ox},{oy}',[('source 85 thickness',a.composite(85,0 if start==0 else 15)[0]),('new arm/body candidate',pic),('original first188 neutral overlay',overlay)]));face_overlap=[{'world':[int(x-160),int(y-160)],'body':int(body[y,x]),'gun':int(gun[y,x])}for y,x in np.argwhere((body>0)&(gun>0)&(X>=-11)&(Y<=-9)&(z!=body))]
  frames.append({'ref':n,'form':form,'root_body_source':q['body_source'],'root_body_source_sha256':digest(ROOT/q['body_source']),'candidate':str((src/f'{key}_indices.png').relative_to(ROOT)).replace('\\','/'),'candidate_file_sha256':digest(src/f'{key}_indices.png'),'candidate_indices_sha256':sha(z.tobytes()),'edit_mask':str((src/f'{key}_edit_mask.png').relative_to(ROOT)).replace('\\','/'),'arm_indices':str((src/f'{key}_arm_indices.png').relative_to(ROOT)).replace('\\','/'),'local_translation':q['arm_rigid_translation'],'original_projectile_origin':[ox,oy],'canonical_mouth':[ox+1,[oy-1,oy]],'canonical20_visible':q['canonical_visible'],'skin_occlusion':q['skin_occludes_canonical'],'finger_gun_contact4':q['skin_gun_contacts4'],'original_body_face_occluded_by_gun_only':face_overlap,'outside_edit_exact':True,'legs_y3_and_below_exact':True,'back_side_x1_and_right_exact':True,'source_links':source_links,'first_flash_overlap_diagnostic_only':int(((effect>0)&(z>0)).sum())})
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'muzzle_contacts_{i//2+1}.png',6)
 report={'scope':'기본/포스 호버 새 사격팔 222/224/226/228 8표시 지원후보. 230은 루트 소유/미편집.','passed':True,'parent':{'path':imeta['parent_arc'],'sha256':digest(parent)},'canonical_actual_archive':{'path':str(canonical_parent.relative_to(ROOT)).replace('\\','/'),'sha256':digest(canonical_parent),'ref':85,'texels':coords},'frames':frames,'original_first_flash':{'path':str(fxpath.relative_to(ROOT)).replace('\\','/'),'sha256':digest(fxpath),'opaque':188,'display':'중립 노랑 합성; 원게임 CLUT/렌더순서/실기 아님'},'root_sources_unchanged':all(digest((ROOT/q['body_source']))==q['body_source_sha256']for q in meta['frames']),'native_packed':False,'new_MIPS_execution':False,'runtime_executed':False,'final_art_accepted':False,'remaining':['루트 최종 몸체 공통층에 edit_mask/arm_indices 적용 및 양폼 공통손 검토','부분마스크/최종패킹/원MIPS와 실기는 루트 후속 범위']}
 write(out/'report.json',report);print(json.dumps({'passed':True,'report_sha256':digest(out/'report.json'),'gun_head_overlap':{str(q['ref'])+q['form']:q['original_body_face_occluded_by_gun_only']for q in frames}}))
if __name__=='__main__':main()

