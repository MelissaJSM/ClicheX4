"""실제 열람한12판과 별도 Root MIPS의 최종해시를 결속한다."""
from pathlib import Path
import hashlib,json,sys
N=Path(__file__).resolve().parent;W=N.parent;ROOT=W.parents[1];O=N/'base_hover_final_independent01';R=W/'root_nana_hover'
sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from src.psx_player import decode_stream
sha=lambda b:hashlib.sha256(b).hexdigest();digest=lambda p:sha(p.read_bytes());rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
report=read(O/'report.json');assert report['candidate_sha256']==digest(ROOT/report['candidate'])=='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c'
assert not(O/'visual_review.json').exists()
for q in report['readback_sheets']:assert digest(ROOT/q['path'])==q['sha256']
visual={'candidate_sha256':report['candidate_sha256'],'technical_report_sha256':digest(O/'report.json'),'actually_viewed':report['readback_sheets'],'sheet_count':12,'findings':[
 '실제 ARC 재추출221/222·223/224에서는 새 머릿결·모자/베일 명암과 굽힌 앞팔의 밝은 윗면/어두운 아랫면이 이어진다. 수평 권총과 피부 손목이 구별되며 새확정 절단은 찾지 못했다.',
 '225/226·227/228은 얼굴 가까이 접은 사격팔과 늘어뜨린 두 다리를 구분할 수 있고, 목~어깨와 손목/신발에 새로 떨어진 조각은 보이지 않는다.',
 '229/230의 새 굽힌 뒤발은 무릎 아래의 발목과 붉고 검은 신발끝이 연결되어 읽힌다. 같은 다리층이 비사격/사격 및 유효마스크8..15에서 유지된다. 두 권총이나 남은 아래손은 보이지 않는다.',
 '원제트15위상 중립점유판에서229/230 뒤신발이 jet12의 위쪽 시작부분에 이어지고, jet13/14에서도 발이 크게 떨어진 인상은 없다. 다른 네 쌍에서도 추가 확정 추진원점 이탈을 찾지 못했다.',
 '원첫탄환188픽셀의 중립점유와 실제signedXY 표를 함께 그린10표시에서 총구 두행과 발사점이 연결된다. 새로운 떠 있는 총구는 보이지 않는다.'
 ],'limits':['정적12판의 시각적 검토이다. 실제게임·60Hz연속관찰·실제 효과 CLUT/블렌딩·앞뒤 렌더순서 판정이 아니다.','유효부분층 전체160조건은 기술 단일몸체 검사이며 실제 직접본 부분판은229/230 mask8..15 16표시이다.','무아머 호버의 실제게임 도달성을 새로 검증한 것은 아니다.']}
write(O/'visual_review.json',visual)
nativepath=R/'native_components01_native_checks.json';native=read(nativepath);res=native['resources']['PL00_U.ARC'];assert native['passed']and res['candidate_sha256']==report['candidate_sha256'];arc=Archive((ROOT/report['candidate']).read_bytes());rows=[]
for bank in res['banks']:
 for q in bank['native_decoder_checks']:
  f=arc.banks[bank['bank']]['frames'][q['frame']];raw=decode_stream(arc.g,f['offset'],f['limit'],f['tile_count']*128).data
  assert sha(raw)==q['decoded_sha256']and q['buffer_outside_and_unused_tail_preserved'];rows.append({'bank':bank['bank'],'ref':q['frame'],'decoded_sha256':sha(raw),'native_buffer_guard_preserved':True})
assert len(rows)==15
write(O/'native_binding.json',{'scope':'별도 Root 원MIPS 결과의 최종후보/15decoded 해시만 독립 결속. 새 원MIPS 실행 아님.','candidate_sha256':report['candidate_sha256'],'producer_native_report':rel(nativepath),'producer_native_report_sha256':digest(nativepath),'decoder_bindings':rows,'new_MIPS_executed':False,'runtime_verified':False})
files=[p for p in O.rglob('*')if p.is_file()and p.name!='READER_LOCK.json']+[N/'verify_base_hover_final01.py',Path(__file__).resolve()]
write(O/'READER_LOCK.json',{'candidate_sha256':report['candidate_sha256'],'report_sha256':digest(O/'report.json'),'visual_sha256':digest(O/'visual_review.json'),'files':[{'path':rel(p),'sha256':digest(p)}for p in sorted(files)]})
assert digest(ROOT/report['candidate'])==report['candidate_sha256']
print(json.dumps({'report':digest(O/'report.json'),'visual':digest(O/'visual_review.json'),'native_binding':digest(O/'native_binding.json'),'lock':digest(O/'READER_LOCK.json')}))
