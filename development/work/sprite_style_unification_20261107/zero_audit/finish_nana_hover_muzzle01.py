"""총구표 주변 원US 실제 총입구와 정적 합성의 열람 결과를 추가 보존한다."""
from pathlib import Path
import hashlib,json,sys,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;O=D/'nana_ultimate_hover_muzzle01'
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((O/'report.json').read_text('utf8'));z,_=read_disc(ROOT/'MegaMan X4.bin',['PL02_U.ARC']);a=Archive(z['PL02_U.ARC']);rows=[]
for q in report['origins']:
 n=q['ref'];x,y=q['direction0_xy'];old=np.array(a.composite(n,15)[0]);p=ROOT/f'work/sprite_style_unification_20261107/nana_audit/ultimate_hover_repaint/shot_joint_probe_v1/body_{n}_indices.png';new=np.array(Image.open(p));detail=[]
 assert sha(p)==report['input_png_hashes'][p.relative_to(ROOT).as_posix()]
 for wy in range(y-2,y+3):
  xx=np.flatnonzero(old[160+wy,:160+x+8,3]);nx=np.flatnonzero(new[160+wy,:160+x+8]);assert len(xx)and int(xx.min())-160==x+1
  detail.append({'y':wy,'original_muzzle_left_x':int(xx.min())-160,'new_left_x_in_same_window':None if not len(nx)else int(nx.min())-160})
 rows.append({'ref':n,'original_muzzle_front_adjacent_to_engine_origin_x_plus1':True,'original_muzzle_5_rows':detail})
out={'scope':'원US 실제 총입구 정적 비교와 실제열람. 새게임실행 아님.','parent_report_sha256':sha(O/'report.json'),'actually_viewed':{'path':(O/'first_flash_static_comparison.png').relative_to(ROOT).as_posix(),'sha256':sha(O/'first_flash_static_comparison.png')},'original_muzzle_rows':rows,'observations':['원US 다섯 사격의 총입구는 탄환 원점X+1에서 Y−2..Y+2 다섯 행에 연속된다. 이는 원코드 발사점과 원그림의 직접 접점 근거다.','222/224의 현재나나·새중간안은 총구가 원US 접점보다 위·오른쪽에 있다. 합성판에서도 첫효과와총의접점이얕고224는알파겹침0이다. 이차이는새그림만의신규오류가아니라옛나나그림에도있다.','228은 실제 탄환 중심표시가 총열/손 쪽에 겹친다.226/230은첫효과와연결돼보이나원점과총끝의정합은각자세별로판단해야한다.','기존8열그림을형태로보존하는검사는게임발사점일치검사와분리한다. 권총·피부손을국소정합하고원래전신·발/추진효과·발사코드·타이밍은보호하는방향으로제작자에게전달했다.'],'limits':['중립색 정적 효과를 먼저 그린 뒤 몸체를 얹은 진단이며 실제 글로벌CLUT/렌더순서/프레임갱신상태를 캡처한 것이 아니다.','현재 생기는 실기 결함이라고 단정하지 않으며 양방향실기·탄환이동은 미실행이다.','원점부근 원그림의 접점은 입증했지만 새로운 손/팔의 최종 자세나 자동 이동량을 정하지 않았다.'],'producer_art_or_resource_modified':False,'new_MIPS_executed':False,'runtime_verified':False,'new_art_accepted':False}
p=O/'visual_findings.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
