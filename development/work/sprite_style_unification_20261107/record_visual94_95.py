from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
groups=[(94,[W/'shibuki_audit/ultimate_ladder_pack01'/f'{form}_readback_{i:02}.png' for form in ('before','after') for i in range(3)],
 ['Ultimate 사다리14참조의 전후 패킹 재추출6판을 직접 열람했다. 기준 대기에 비해 이전 단색 뒤머리·옷의 넓은 덩어리가 줄었고 정합된 손/소매에 추가 확정 분리를 찾지 못했다.'],
 ['원순서 반동·사다리 끝점 재생과 재현/독립검사·새 BIN 실기는 별도다.'],
 {'candidate_arc_sha256':sha(W/'shibuki_audit/ultimate_ladder_pack01/PL02_U.ARC')}),
 (95,[W/'nana_audit/ultimate_hurt_repaint/costume_pair_probe_v4'/f'comparison_{i}.png' for i in (1,2)],
 ['새 피격4몸체 공통층 정합2판을 직접 열람했다. 전후의 머리/다리와 국소 팔 정합에서 추가 확정 접합선을 찾지 못했다.'],
 ['파생 피격효과·실루엣/부분층·패킹·실기는 아직 별도 검토 대상이다.'],{})]
for n,paths,findings,limits,extra in groups:
 p=W/f'root_review_checkpoint{n}.json';assert not p.exists()
 p.write_text(json.dumps({'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)} for q in paths],
 'findings':findings,'limits':limits,'final_user_accepted':False,**extra},ensure_ascii=False,indent=2)+'\n','utf8')
 print(n,sha(p))
