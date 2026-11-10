"""실제로 본 정지 비교판의 범위와 공통권총·접지 측정을 기록한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def bbox(z):
 y,x=np.nonzero(z);return[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]
def main():
 d=D/'packed_standing_candidate_v1';cp=d/'PL02_U.ARC';a=Archive(cp.read_bytes());src=D/'common_probe_v3';m=json.loads((src/'manifest.json').read_text('utf8'));frames=[]
 for n,box in((89,(-19,-30,-11,-21)),(97,(-15,-14,-7,-5))):
  b=np.array(Image.open(src/f'before_{n:03}_indices.png'));v=np.array(Image.open(src/f'after_{n:03}_indices.png'));x0,y0,x1,y1=box;bs=b[y0+160:y1+160,x0+160:x1+160];vs=v[y0+160:y1+160,x0+160:x1+160];need(np.array_equal(bs,vs),'권총과손 공통창');need(bbox(b)[3]==23 and bbox(v)[3]==23,'접지')
  # Only the new-source semantic window is compared here. It is not the
  # canonical 85 module or an assertion about the runtime projectile origin.
  frames.append({'ref':n,'source_weapon_hand_window':box,'world_indices_exact_between_costumes':True,'window_sha256':sha(bs.tobytes()),'window_opaque_pixels':int((bs>0).sum()),'before_bbox':bbox(b),'after_bbox':bbox(v),'floor_world_exclusive':23,'eye_original_world_preserved':[-4,-12 if n==89 else -11],'canonical85_module_substituted':False,'runtime_projectile_origin_claimed':False})
 pics=[d/'readback_1.png',d/'readback_2.png']+[D/'native_cycle_v2'/f'timeline_{i}.png'for i in(91,104,105)]+[D/'common_probe_v3/comparison.png',D/'a_v1/generated.png']
 report={'candidate_arc_sha256':digest(cp),'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in pics],'source_contact_metrics':frames,'observations':['89 맨팔 커프 경계8셀을 같은 새후폼 원화의 투명 틈·귀/머리 경계로 등록한 v3에서 밝은 소매띠가 사라졌다.','새 뒤머리 가닥·피부/의상 분리가 유지되며 이 정지판에서 새 명백한 손목·발목 분리를 찾지 못했다.','89 허리 아래 회백색 면은 원 생성부터 존재하고 대기보다 벌린 자세에서 넓게 보인다. 단순 면적 맞춤으로 자르지 않았으며 독립/root 미술판정과 구분한다.','88 원83texel은 새머리 위로 지나가는 원래 효과 위치다. 과거 after의 효과밖 몸105셀은 가져오지 않았다.','원표91/104/105의90/91·98/99는 이전 그림으로 남아 상세 수준이 낮다. 현재3참조 검사를 전체 특수기 완성으로 집계하지 않는다.'],'limits':'정지판 실제 열람과 기계적 브라우저 재생/원MIPS 검사만 있다. 인간의 실시간 동작관찰이나 실제 게임 실행으로 표현하지 않는다. 사선 권총은 생성된 새 비사격 자세의 형태이며 정본85를 회전한20texel 모듈이 아니다.','runtime_verified':False}
 out=d/'producer_visual_review.json';need(not out.exists(),'새기록');write(out,report);print(json.dumps({'sha256':digest(out),'viewed':len(pics),'contact_frames':len(frames)}))
if __name__=='__main__':main()
