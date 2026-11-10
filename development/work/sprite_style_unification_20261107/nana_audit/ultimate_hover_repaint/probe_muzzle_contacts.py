"""원 첫탄환 점유/발사표와 새 국소 정본총의 정적 접점을 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
def main():
 out=D/'muzzle_contacts_probe_v1';out.mkdir(exist_ok=False);audit=N.parent/'zero_audit/nana_ultimate_hover_muzzle01';r=json.loads((audit/'report.json').read_text('utf8'));fx=np.load(audit/'lemon_first_frame.npy');need(sha(fx.tobytes())==r['first7_effect_frames'][0]['indexed_sha256'],'원188효과 hash');need(fx.shape==(384,384),'384원점');a=Archive((N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC').read_bytes());m=json.loads((D/'muzzle_joint_probe_v1/manifest.json').read_text('utf8'));rows=[];proof=[]
 for q in m['frames']:
  n=q['ref'];ox,oy=q['engine_projectile_origin'];old=np.array(Image.open(D/f'shot_joint_probe_v2/body_{n:03}_indices.png'));new=np.array(Image.open(D/f'muzzle_joint_probe_v1/body_{n:03}_indices.png'));gun=np.array(Image.open(D/f'muzzle_joint_probe_v1/canonical_{n:03}_indices.png'));world=np.roll(np.roll(fx,oy,0),ox,1);need(int((world>0).sum())==188,'효과클립없음');need(np.all(gun[[oy-1+160,oy+160],ox+1+160]>0),'정본총 앞2행 원점X+1');need(np.all(new[[oy-1+160,oy+160],ox+1+160]==gun[[oy-1+160,oy+160],ox+1+160]),'총앞표본 가림없음');ims=[]
  for name,z in [('prior diagnostic / held8 policy',old),('new original-muzzle joint',new)]:
   # Neutral occupancy color only: do not claim actual CLUT/draw-order.
   im=Image.new('RGBA',(384,384));area=np.zeros((384,384,4),np.uint8);area[world>0]=[173,154,40,255];im.alpha_composite(Image.fromarray(area));im.alpha_composite(a.rgba(z));d=ImageDraw.Draw(im);d.line((ox+159,oy+160,ox+161,oy+160),fill=(0,245,230,255));d.line((ox+160,oy+159,ox+160,oy+161),fill=(0,245,230,255));ims.append((name,im))
  ims.append(('new body without effect',a.rgba(new)));rows.append((str(n)+f' origin({ox},{oy})',ims));proof.append({'ref':n,'engine_projectile_origin':[ox,oy],'canonical_muzzle_x':ox+1,'canonical_muzzle_rows':[oy-1,oy],'canonical_source_texels':20,'canonical_visible':q['canonical_visible'],'skin_occlusion':q['canonical_skin_occluded'],'first_effect_opaque':188,'prior_overlap':int(((old>0)&(world>0)).sum()),'new_overlap':int(((new>0)&(world>0)).sum()),'overlap_count_is_not_acceptance_criterion':True,'new_indexed_sha256':sha(new.tobytes()),'muzzle_before_projectile_x_distance':1})
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'report.json',{'source_report':{'path':(audit/'report.json').relative_to(ROOT).as_posix(),'sha256':digest(audit/'report.json')},'source_visual_findings':{'path':(audit/'visual_findings.json').relative_to(ROOT).as_posix(),'sha256':digest(audit/'visual_findings.json')},'frames':proof,'scope':'원US 코드/표 읽기 근거와 첫 탄환188px 점유를 동일원점에 겹친 정적 후보. 실제CLUT·렌더순서·게임/원MIPS 실행 검증은 아님. 겹침수 일치 자체를 수용조건으로 사용하지 않는다.','runtime_verified':False});print(json.dumps(proof))
if __name__=='__main__':main()
