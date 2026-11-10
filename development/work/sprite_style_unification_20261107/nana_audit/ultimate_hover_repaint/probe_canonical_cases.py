"""새 비사격 호버 손에 정본85의 권총20표본을 강체 정합한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
from probe_body_contacts import source as initial_source
def source(n):return D/'semantic_last_v1/body_229_indices.png' if n==229 else initial_source(n)
Y,X=np.indices((384,384));Y-=160;X-=160
# 각 입력판을 실제 열람해 총열/그립 범위와 실제 피부 손을 구분했다.
SPECS={221:{'hand':[-7,-4],'remove':[[-13,-5,-7,-1]]},223:{'hand':[-7,-2],'remove':[[-13,-5,-7,2]]},225:{'hand':[-7,-2],'remove':[[-13,-4,-7,2]]},227:{'hand':[-6,-3],'remove':[[-12,-4,-7,2]]},229:{'hand':[-7,-5],'remove':[[-13,-7,-7,-4],[-11,-4,-8,-1]]}}
def box(b):return (X>=b[0])&(Y>=b[1])&(X<b[2])&(Y<b[3])
def main():
 out=D/'canonical_cases_probe_v4';out.mkdir(exist_ok=False);p=N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());c=a.layer(85)[0];gm=box([-22,-11,-14,-5])&np.isin(c,range(1,10));need(int(gm.sum())==20,'정본20');coords=[[int(x-160),int(y-160),int(c[y,x])]for y,x in np.argwhere(gm)];rows=[];proof=[]
 for n,s in SPECS.items():
  v=np.array(Image.open(source(n)));z=v.copy();remove=np.zeros_like(v,dtype=bool)
  for b in s['remove']:remove|=box(b)
  removed=[[int(x-160),int(y-160),int(v[y,x])]for y,x in np.argwhere(remove&(v>0))];z[remove]=0;dx,dy=s['hand'][0]+16,s['hand'][1]+9;case=np.zeros_like(z)
  for x,y,i in coords:case[y+dy+160,x+dx+160]=i
  hand=box([s['hand'][0]-1,s['hand'][1],s['hand'][0]+3,s['hand'][1]+5])&np.isin(v,[10,11,12,13])&~remove;use=(case>0)&~hand;z[use]=case[use];need(np.array_equal(z[hand],v[hand]),'새 손 피부 보존');labs,ct=label(z>0,np.ones((3,3)));components=[{'size':int((labs==i).sum()),'cells':[[int(x-160),int(y-160),int(z[y,x])]for y,x in np.argwhere(labs==i)]if (labs==i).sum()<30 else None}for i in range(1,ct+1)];need(np.array_equal(z[~(remove|use)],v[~(remove|use)]),'몸체 보호')
  need(ct==1,'새 몸체/총 연결');Image.fromarray(z).save(out/f'body_{n:03}_indices.png');Image.fromarray(case).save(out/f'case_{n:03}_indices.png');Image.fromarray(remove.astype(np.uint8)*255).save(out/f'removal_{n:03}.png');Image.fromarray(hand.astype(np.uint8)*255).save(out/f'hand_{n:03}.png');proof.append({'ref':n,'body_source':source(n).relative_to(ROOT).as_posix(),'body_source_sha256':digest(source(n)),'hand_anchor':s['hand'],'translation':[dx,dy],'removal_boxes':s['remove'],'removed_source_cells':removed,'visible_case_texels':int(use.sum()),'skin_occluded_case_texels':int(((case>0)&hand).sum()),'hand_source_cells':[[int(x-160),int(y-160),int(v[y,x])]for y,x in np.argwhere(hand)],'target_sha256':sha(z.tobytes()),'components8':components,'scope':'정본85 총열/그립의 새 비사격 손 정합 진단. 연결성/미술 후속이며 원발사 좌표 증명과는 별개.'});rows.append((str(n),[('new source',a.rgba(v)),('same canonical pistol',a.rgba(z)),('accepted85',a.composite(85)[0])]))
 for k in range(0,len(rows),2):helper.grid(rows[k:k+2],out/f'comparison_{k//2+1}.png',7)
 write(out/'manifest.json',{'parent_arc_sha256':digest(p),'canonical_source_ref':85,'canonical_source_texels':coords,'frames':proof,'source_old_gun_area_copied':False,'native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'translation':q['translation'],'removed':len(q['removed_source_cells']),'visible':q['visible_case_texels'],'components':q['components8']}for q in proof]))
if __name__=='__main__':main()
