from pathlib import Path
import json,hashlib,html,sys
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_ultimate_vehicle13_independent01'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import raw
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'));assert sha(O/'report.json')=='a45fef0eed2b62d70f95b2df709bfbbfd482bfb8e7987482c545ebd4f2f384e2'
np=D.parent/'nana_audit/ultimate_vehicle_repaint/native_components_v1_native_checks.json';nm=json.loads(np.read_text('utf8'));assert nm['passed']
resource=nm['resources']['PL02_U.ARC'];assert resource['candidate_sha256']==r['candidate_sha256']
candidate=ROOT/r['candidate'];assert sha(candidate)==r['candidate_sha256'];a=Archive(candidate.read_bytes());checks=next(q for q in resource['banks']if q['bank']==0)['native_decoder_checks']
for n in range(162,175):
 q=next(q for q in checks if q['frame']==n);assert hashlib.sha256(raw(a,0,n)).hexdigest()==q['decoded_sha256']and q['buffer_outside_and_unused_tail_preserved']
notes={
'full_162.png':'新 머릿결/귀/앞머리·재킷/맨팔 명암이 선명하고 앞손과 접힌 무릎·뒤 발목이 이어진다. 새 확정 단절은 보이지 않았다.',
'full_166.png':'낮게 접힌 허벅지와 종아리, 손목 연결을 확인했다. 새 허리 분홍 면은 donor에도 있는 표본이며 이 판만으로 소매 잔재라고 단정하지 않는다.',
'full_170.png':'앞팔·목·신발의 새 명암을 확인했다. 머리의 큰 윤곽과 아래로 뻗은 다리는 양폼 공통이고 추가 확정 단절은 보이지 않았다.',
'full_174.png':'앞에 모인 두 손과 두 신발이 구별된다. 눈/목·팔꿈치·무릎이 연결되고 새 의상 전환에서 분리된 조각을 찾지 못했다.',
'partial_162.png':'머리 비트 선택 때만 재킷이 복원되는 현재 Ultimate 의상 정책을 다섯 조합에서 보았다. 미선택 몸/팔/다리 판에 재킷 조각이 새로 떠 있지 않았다.',
'partial_166.png':'다섯 부분 판에서 몸체와 의상 전환을 확인했다. 옛 개별등록의 다리 흔들림을 복사하지 않은 새 공통몸체가 이어진다.',
'partial_170.png':'다섯 조합에서 앞손/몸과 발목의 연결을 확인했다. 새 의상 경계가 팔 전체를 가르는 모습은 보이지 않았다.',
'partial_174.png':'다섯 조합에서 새 머리와 두 팔·다리가 함께 유지된다. 부분 아머를 실제 게임에서 장착했다는 뜻은 아니다.',
'alias_162.png':'162~165 양폼에서 머리·손·발이 함께 +1/+3/−1행 이동한다. 별도 신체 조각만 흔들리는 정적 오류는 보이지 않았다.',
'alias_166.png':'166~169 양폼 상하 위상에서 같은 접힌 다리와 앞손이 유지된다. 원표 실시간 재생의 시각 판정은 별도다.',
'alias_170.png':'170~173 양폼의 +1/+2/−1행 위상이 보존된다. 손과 발이 몸에서 따로 움직이는 모습은 보이지 않았다.'}
seen=[]
for q in r['readback_sheets']:
 p=ROOT/q['path'];assert sha(p)==q['sha256'];seen.append({**q,'actually_viewed':True,'finding':notes[p.name].replace('新','새')})
assert len(seen)==11
v={'candidate_sha256':r['candidate_sha256'],'technical_report_sha256':sha(O/'report.json'),'scope':'독립 재추출 완성4·부분4·Y별칭3 총11판 정적 실제 열람','sheets':seen,'new_confirmed_art_defect_found':False,'native_existing_evidence':{'path':np.relative_to(ROOT).as_posix(),'sha256':sha(np),'13_decoded_hashes_independently_rebound':True,'executed_here':False},'limits':['이 판은 차량 몸체와 합성하지 않아 실제 손잡이/페달 접점 또는 게임 실행을 증명하지 않는다.','기계검사416부분 중 실제 육안은 기록한 다섯 조합×4판과 완성/별칭이다.','원MIPS는 제작자가 별도 실행한 결과와 디코드13해시를 결속했다. 이 종료 스크립트가 새 MIPS를 실행한 것은 아니다.','9개 Y별칭은 원US/현재 재킷 근거를 새 두폼에 적용한 정책이다. 옛 후폼 개별등록의 완전 복원으로 표현하지 않는다.'],'runtime_verified':False,'overall_complete':False,'user_accepted':False}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
page=['<!doctype html><meta charset="utf-8"><title>나나 Ultimate 차량13 독립 읽기</title><style>body{font:16px sans-serif;background:#182333;color:#eee;margin:24px}img{max-width:100%}a{color:#9cddff}</style><h1>나나 Ultimate 차량13 독립 읽기</h1><p>후보94326933. 생성8셀 재양자화, 국소정합, 65층 및416부분, 비대상을 독립 대조했습니다. 실제 게임 탑승 접점은 별도입니다.</p><p><a href="report.json">기술 보고</a> · <a href="visual_review.json">실제 열람11판·원MIPS 해시 결속</a></p>']
for q in seen:page.append(f'<p>{html.escape(q["finding"])}</p><img src="{Path(q["path"]).name}">')
(O/'INDEX.html').write_text('\n'.join(page),'utf8')
print(json.dumps({'report':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'native':sha(np),'viewed':len(seen)}))
