"""최종 ARC의 총구/손·원15추진위상과 최초 탄환 점유를 재독출한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
def main():
 out=D/'packed_contacts_v1';out.mkdir(exist_ok=False);p=D/'packed_hover_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());parent=Archive((N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC').read_bytes());ja=N.parent/'zero_audit/nana_ultimate_hover_relations01';j=json.loads((ja/'conclusions.json').read_text('utf8'));ma=N.parent/'zero_audit/nana_ultimate_hover_muzzle01';m=json.loads((ma/'report.json').read_text('utf8'));jm=json.loads((D/'muzzle_joint_probe_v1/manifest.json').read_text('utf8'));static=entry(a.data,0x10206);need(static==entry(parent.data,0x10206),'정적효과 전체 항목 보존');jets=[];pal=np.zeros((16,4),np.uint8)
 for i in range(1,16):pal[i]=[65+i*10,85+i*8,115+i*6,255]
 for n in (221,223,225,227,229):
  rows=[(f'{n} new held / original FX',[]),(f'{n+1} new shot / original FX',[])];need(np.array_equal(a.layer(n,5)[0],a.layer(n+1,5)[0]),'사격짝 하체 exact')
  for q in j['effect_frames']:
   if n not in q['player_refs']:continue
   f=q['effect_frame'];cp=composition_frame(a.c,12,f);need(cp['parts']==q['parts'],'원추진기록 exact');px,sz,bb,_=compose_static(static,local_composition(cp));jet=np.zeros((384,384),np.uint8);jet[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);need(sha(jet.tobytes())==q['indexed_sha256'],'원15위상 색인 exact')
   for ri,ref in enumerate((n,n+1)):
    im=Image.fromarray(pal[jet]);im.alpha_composite(a.composite(ref,15)[0]);rows[ri][1].append((f'neutral FX{f}',im))
   jets.append({'frame':f,'player_refs':[n,n+1],'indexed_sha256':sha(jet.tobytes()),'original_parts_exact':True,'transform':[0,0]})
  helper.grid(rows,out/f'jets_{n}.png',6)
 for q in j['whole_tiles']:need(sha(tile_pixels(static,q['tile']))==q['sha256'],'원6소비전체타일 exact')
 fx=np.load(ma/'lemon_first_frame.npy');need(sha(fx.tobytes())==m['first7_effect_frames'][0]['indexed_sha256'],'원첫188효과');shots=[];rows=[];origins={q['ref']:q['direction0_xy']for q in m['origins']}
 for q in jm['frames']:
  n=q['ref'];ox,oy=origins[n];base=a.layer(n,0)[0];gun=np.array(Image.open(D/f'muzzle_joint_probe_v1/canonical_{n:03}_indices.png'));placed=np.array(Image.open(D/f'muzzle_joint_probe_v1/placed_arm_{n:03}_indices.png'));Y,X=np.indices(base.shape);X-=160;Y-=160;skin=(X>=ox+4)&(X<ox+11)&(Y>=oy)&(Y<oy+6)&np.isin(placed,[10,11,12,13]);visible=(gun>0)&~skin;need(np.array_equal(base[visible],gun[visible]),'정본가시총 exact');need(np.array_equal(base[(gun>0)&skin],placed[(gun>0)&skin]),'피부손 가림 exact');need(np.all(base[[oy-1+160,oy+160],ox+1+160]==gun[[oy-1+160,oy+160],ox+1+160]),'총앞2행 exact')
  for mask in range(16):
   for arm in (1,2):
    rgba=np.array(a.composite(n,mask,arm)[0]);expect=np.array(a.rgba(base));need(np.array_equal(rgba[gun>0],expect[gun>0]),'32조건 총손 exact')
  world=np.roll(np.roll(fx,oy,0),ox,1);area=np.zeros((384,384,4),np.uint8);area[world>0]=[173,154,40,255];im=Image.fromarray(area);im.alpha_composite(a.composite(n,15)[0]);dr=ImageDraw.Draw(im);dr.point((ox+160,oy+160),fill=(0,245,230,255));rows.append((f'{n} origin({ox},{oy})',[('packed body',a.composite(n,15)[0]),('packed / original first188 occupancy',im)]));shots.append({'ref':n,'origin':[ox,oy],'muzzle_x':ox+1,'muzzle_rows':[oy-1,oy],'source_texels':20,'visible':int(visible.sum()),'skin_occluded':int(((gun>0)&skin).sum()),'partial_conditions':32,'first_effect_exact':True})
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'muzzle_{i//2+1}.png',7)
 write(out/'report.json',{'passed':True,'candidate_sha256':digest(p),'jet_source_sha256':digest(ja/'conclusions.json'),'muzzle_source_sha256':digest(ma/'report.json'),'jet_phases':jets,'original_effect_whole_tiles':j['whole_tiles'],'shots':shots,'scope':'최종ARC 실제재독출. 원추진15위상/6전체타일과 정본100셀/새피부손을 원발사표 위치에서 확인했다. 효과는 중립색 점유판이며 실제CLUT·블렌딩·draw order·발사시점/물리 실행은 아니다.','runtime_verified':False});print(json.dumps({'passed':True,'jet_phases':len(jets),'muzzle_partial_checks':160}))
if __name__=='__main__':main()
