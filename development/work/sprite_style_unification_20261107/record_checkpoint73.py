from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
D=W/'nana_audit/rising_repaint/packed_ultimate_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'PL02_U.ARC')=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
pages=[D/f'readback_{i}.png' for i in (1,2,3)]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
   'packed_asset_sha256':sha(D/'PL02_U.ARC'),
   'findings':['Ultimate100..104/231의 전후 의상을 최종 ARC에서 재추출한3판을 대기와 비교했다. v6의 맨팔 목/어깨 잔여 정리와 지상231접지 보완을 유지하고 새 머릿결/소매/다리 묘사가 남은 것을 확인했다.',
               '이번 판에서 새 확정 손·팔·발목 절단을 찾지 못했다. 분홍 재킷 전폼/맨팔 후폼을 구별한 채 기술 검사와 실제 플레이로 진행한다.'],
   'limits':['232는231재사용이며 별도 그림으로 실제 열람한 수에 중복 합산하지 않는다.','정적6키×2의상 열람이고 아직 사용자 수용이나 새 Ultimate 라이징 실기 완료가 아니다.'],
   'final_user_accepted':False}
p=W/'root_review_checkpoint73.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
