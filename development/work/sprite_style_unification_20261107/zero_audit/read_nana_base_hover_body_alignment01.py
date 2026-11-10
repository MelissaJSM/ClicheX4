"""새 호버10 정수정합 출처와 실제열람5판만 기록. 원화/ARC 변경 없음."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
P=W/'root_nana_hover/body_alignment01';O=D/'nana_base_hover_body_alignment_read01';assert not O.exists()
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();inputs={}
def blob(p):
 b=p.read_bytes();inputs[rel(p)]=sha(b);return b
def png(p):blob(p);return np.array(Image.open(p))
m=json.loads(blob(P/'manifest.json'));rows=[]
for q in m['frames']:
 source=ROOT/q['source'];a=png(source);assert sha(source.read_bytes())==q['source_sha256'];b=png(P/f"{q['form']}_{q['ref']}_indices.png");dx,dy=q['translation'];yy,xx=np.nonzero(a);assert min(xx+dx)>=0 and max(xx+dx)<a.shape[1]and min(yy+dy)>=0 and max(yy+dy)<a.shape[0]
 expected=np.zeros_like(a);expected[yy+dy,xx+dx]=a[yy,xx];assert np.array_equal(expected,b)
 by,bx=np.nonzero(b);bbox=[int(bx.min()),int(by.min()),int(bx.max()+1),int(by.max()+1)];assert bbox==q['bbox']and bbox[3]==q['old_bbox'][3]
 assert np.array_equal(np.bincount(a.flat,minlength=256),np.bincount(b.flat,minlength=256))
 rows.append({'ref':q['ref'],'form':q['form'],'source':rel(source),'translation':[dx,dy],'every_index_pixel_translation_exact':True,'color_counts_exact':True,'bbox':bbox,'lowest_y_matches_recorded_parent':True})
assert len(rows)==10
viewed=[]
for n in(221,223,225,227,229):
 p=P/f'comparison_{n}.png';blob(p);viewed.append({'path':rel(p),'sha256':sha(p.read_bytes())})
blob(W/'root_nana_hover/registered03_fit01/manifest.json');prior=D/'nana_base_hover_relations01/report.json';assert sha(blob(prior))=='6f1fbfdef566fff22ddc96e6bb73b1a0c0e704eef202c2e09d94fc420f389533'
v={'scope':'Nana 기본 legs/포스 호버5몸체×2폼 정수정합 후속 읽기','parent_sha256':m['parent_sha256'],'rows':rows,'actually_viewed':viewed,'observations':['221/223의 앞뒤 팔·머릿결·굽힌 다리에서 추가 확정 절단을 찾지 못했다. 얼굴각도에 따른 눈Y 차이를 무조건 같은행으로 밀어내는 수정은 이판에서 요구하지 않는다.','225/227은 전체강체 정합 후 허벅지부터 종아리/부츠로 이어지는 연결과 새 머리 세부를 유지한다. 양폼 다리/베일의 부분소유는 아직 이판만으로 검증하지 않았다.','229는 높은 손과 접힌무릎/아래발목을 보존하며, 균일75셀 등록 후의 몸체가 억지로 하체만 축소된 것 같은 확정 결함을 찾지 못했다. source→75셀 최초 재양자화를 이reader가 직접 재현한 것은 아니다.','정지 비교판은 전후 폼의 의상/체형 방향에 대한 제한된 의견이다. 원추진15위상·발사점과새총 연결은 후속정합판과최종자원에서 따로 확인해야 한다.'],'existing_original_hover_evidence':{'path':rel(prior),'sha256':sha(prior.read_bytes())},'original_jet_code_retested':False,'source_requantization_repeated':False,'producer_functions_called':False,'native_packed':False,'new_MIPS_execution':False,'runtime_verified':False,'final_art_acceptance':False,'inputs':inputs}
O.mkdir(exist_ok=False);p=O/'report.json';p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report_sha256':sha(p.read_bytes()),'source_files':len(inputs),'registered_bodies':len(rows)}))
