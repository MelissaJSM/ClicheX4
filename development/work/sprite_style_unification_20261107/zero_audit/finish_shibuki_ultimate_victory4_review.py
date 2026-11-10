from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import raw
O=D/'shibuki_ultimate_victory4_independent01';H=D.parent/'shibuki_audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
assert sha(O/'report.json')=='f1bf8472108dc19fc42af5ba28ae3cce51dac2e3172a54c14cc81562a9fffe04'
p=H/'ultimate_victory_components_native_checks.json';n=json.loads(p.read_text('utf8'))
assert sha(p)=='4e40640e79923b4e6b9652a5894890a93db0a0b2e35425fac84f8a69a57686ff'and n['passed']
q=n['resources']['PL02_U.ARC'];assert q['candidate_sha256']==r['candidate_sha256']
a=Archive((ROOT/r['candidate']).read_bytes());assert sha(ROOT/r['candidate'])==r['candidate_sha256']
checks=next(z for z in q['banks']if z['bank']==0)['native_decoder_checks']
for ref in(204,205,206,207):
 z=next(z for z in checks if z['frame']==ref)
 assert z['decoded_sha256']==hashlib.sha256(raw(a,0,ref)).hexdigest() and z['buffer_outside_and_unused_tail_preserved']
v={'candidate_sha256':r['candidate_sha256'],'independent_report_sha256':sha(O/'report.json'),
 'actually_viewed':r['readback_sheets'],
 'observations':[
 '최종 ARC를 별도 reader로 재추출한204/205와206/207 두 비교판,총8새의상표시를 실제 열람했다.',
 '새 안경·귀·머리카락 층과 재킷 여밈/소매가 구형보다 구분된다.204 뻗은 팔과205 관자놀이 옆 손은 양폼의 어깨/손목과 이어져 보인다.',
 '206 손을 머리 옆에 든 자세와207 높이 든 팔에서 맨팔 피부와 재킷 소매가 각각 구분된다. 공통머리와 앞팔이 겹치는 경계에서 새 확정 절단이나 흰 소매 잔재를 찾지 못했다.',
 '206/207의 발목·샌들1px 등록과207 주먹1px 등록 뒤 접속이 보이며, 아래발이 따로 떠 있는 확정 분리를 찾지 못했다.'
 ],'new_confirmed_visual_defects':[],
 'existing_native_evidence':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'candidate_and_four_decoded_hashes_exact':True,'executed_by_this_reader':False},
 'runtime_verified':False,'user_accepted':False,
 'limits':['이 기록은 정적 두 비교판의 미술 의견이다. 원표39 실제 재생·브라우저202canvas는 제작자 별도 근거이며 여기서 재실행하지 않았다.','새원화 최초양자화/게임실기/전체캐릭터완료를 주장하지 않는다.']}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'locked_inputs':r['locked_inputs']}))
