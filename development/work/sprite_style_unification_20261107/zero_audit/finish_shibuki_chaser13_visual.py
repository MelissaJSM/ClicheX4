"""직접 열람한12판을 독립 결과와 결속한다. 기존 증거 덮어쓰기 금지."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[2];O=D/'shibuki_chaser13_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
rp=O/'report.json';assert sha(rp)=='177bb4cf5552cd6a1976288675d1e0fed9875061b55c4f05a1e80bce0aae86c7'
r=json.loads(rp.read_text('utf8'));assert r['passed']and not(O/'visual_review.json').exists()and not(O/'READER_LOCK.json').exists()
viewed=[f'comparison_{n}.png'for n in(162,166,170,174)]+[f'partial_{n}.png'for n in(162,166,170,174)]+[f'alias_{n}.png'for n in range(4)]
for q in r['readback_sheets']:assert Path(q['path']).name in viewed and sha(ROOT/q['path'])==q['sha256']
visual={'scope':'시부키 체이서13 독립 재추출 실제 정적 열람','candidate_sha256':r['candidate_sha256'],'report':{'path':rel(rp),'sha256':sha(rp)},'actually_viewed':[{'path':rel(O/p),'sha256':sha(O/p)}for p in viewed],'observations':['기본/포스4자세 비교판에서 새 머릿결·장식·소매·부츠 명암이 기존보다 분리되어 보이며, 이 정적판에서 새 손목이나 무릎·발목의 명백한 단절은 발견하지 못했다.','166의 앞으로 뻗은 손과 낮은 몸,170의 굽힌 다리,174의 세운 몸과 아래 신발이 각각 이어진다.170의 호박색 홍채1셀을 단순 의상 빨강과 분리한 근거도 source reader에서 확인했다.','4부분판의 머리·몸·팔·다리·몸+다리에서 땋은머리/장식과 소매·부츠의 소유 전환이 이어지며 떨어진 옛 조각이나 새 두번째 팔 같은 추가 확정 결함은 보이지 않았다.','13참조 별칭4판에서 머리/몸/장식이 같은 Y만큼 함께 이동한다. 원래2/6/96 호출 시간과 실제 차량 접촉은 이 정지판의 시각 통과로 대신하지 않는다.'],'technical_connection':'65층·416부분이 독립 합성 목표와exact이고 모든 부분은8이웃 단일성분. 이 수치는 미술적 자연스러움의 단독 판정이 아니다.','runtime_verified':False,'actual_vehicle_handle_or_footrest_contact_observed':False,'game_or_user_files_modified':False,'overall_complete':False}
vp=O/'visual_review.json';vp.write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf8')
inputs=dict(r['inputs'])
for p,h in inputs.items():assert sha(ROOT/p)==h,p
for p in [rp,vp,D/'verify_shibuki_chaser13_independent.py',Path(__file__),D/'verify_shibuki_ultimate_hurt13_independent.py',D/'verify_pl00_directory_native.py',ROOT/'scripts/export_x_consistency.py',ROOT/'scripts/discover_inputs.py',ROOT/'scripts/c01_audio_build.py',ROOT/'src/psx_player.py',ROOT/'src/psx_ui_atlas.py']:
 inputs[rel(p)]=sha(p)
for q in r['readback_sheets']:inputs[q['path']]=q['sha256']
lock={'scope':'독립 reader/실제열람/입력 불변 잠금','candidate_sha256':r['candidate_sha256'],'report_sha256':sha(rp),'visual_sha256':sha(vp),'files':inputs,'producer_functions_called':False,'runtime_verified':False}
lp=O/'READER_LOCK.json';lp.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report':sha(rp),'visual':sha(vp),'lock':sha(lp),'locked_files':len(inputs)}))
