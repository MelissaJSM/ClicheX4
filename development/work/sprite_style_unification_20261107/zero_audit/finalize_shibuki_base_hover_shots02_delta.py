"""3셀 소유정정의 실제 열람과 증분 읽기 잠금."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;S=W/'root_shibuki_hover';O=D/'shibuki_base_hover_shots02_delta01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(R).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def write(name,obj):
 with(O/name).open('x',encoding='utf8')as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
r=read(O/'report.json');assert sha(O/'report.json')=='2847592ab425bdbe4faa468155f739cff2403c2aa50e8c914f983f5f88539618';files=r['inputs'].copy()
def track(p):files[rel(p)]=sha(p);return{'path':rel(p),'sha256':sha(p)}
for p,h in files.items():assert sha(R/p)==h,p
viewed=[track(S/f'shot_composed02/comparison_{n}.png')for n in(224,230)]+[track(O/f'delta_{n}.png')for n in(224,230)]
write('visual_review.json',{'actually_viewed':True,'boards':viewed,'count':4,'observations':['224/230의새02전체비교2판과01→02독립국소비교2판을실제열람했다.','224 포스손목의아래한셀이원화피부색으로이어지고230가슴앞흰색/빨강2셀도피부색으로복구됐다. 새로확정된손목틈이나목·팔절단은찾지못했다.','기본형은01과시각·RGBA불변이며포스의소매/몸통/얼굴/총·하체는수치로세좌표밖불변이다.','앞서본222/226/228의완성및부분그림은02에서색인전체exact이므로반복열람하지않았다.'],'limits':['4판은3셀증분미술검토이며최종ARC재추출이나게임실기가아니다.','01의기술·원화10셀재구성/시각11판은별도보고를보존해연결한다.'],'input_modified':False})
write('conclusions.json',{'passed':True,'scope':'PL00 Shibuki호버사격02의피부공통3셀소유정정','report':track(O/'report.json'),'visual':track(O/'visual_review.json'),'checks':r['checks'],'changed_cells':r['changed_cells'],'finding':'224의1셀과230의2셀에만동일Fourth원화9를arm7에복구했다.01의잘못된OR피부선택문제는해소됐다.기본형과공통얼굴·하체·정본총·알파는불변.','prior_report':r['prior_report'],'prior_lock':r['prior_final_lock'],'producer_functions_imported_or_called':False,'source_or_resource_modified':False,'new_MIPS_execution':False,'runtime_verified':False,'next_scope':'최종50층패킹과저장공유·비대상·원MIPS는별도후속이다.'})
for p in(O/'conclusions.json',D/'read_shibuki_base_hover_shots02_delta.py',Path(__file__)):track(p)
for p,h in files.items():assert sha(R/p)==h,p
write('READER_LOCK.json',{'files':dict(sorted(files.items())),'original01_preserved':True,'source_or_resource_writes':False})
print(json.dumps({k:sha(O/k)for k in('report.json','visual_review.json','conclusions.json','READER_LOCK.json')}))
