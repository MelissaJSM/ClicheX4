from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
groups=[(90,[W/'nana_audit/ultimate_hurt_repaint/extra_registered_v1'/f'comparison_{i}.png' for i in (1,2)],
 ['Ultimate 233/234 전후4표시 비교2판을 직접 열람했다. 대기와 비교하여 머릿결·옷 주름이 더 뚜렷해졌고 이전 큰 단색 덩어리가 줄었다.'],
 ['234 발목/발바닥 국소 정합과 공통층/효과 파생·패킹·실기는 남아 있다.']),
 (91,[W/'shibuki_audit/ultimate_ladder_shots_registered01'/f'{form}_comparison.png' for form in ('before','after')],
 ['사다리 사격150/155 전후2판을 직접 열람했다. 옛 총열의 흰색 혼입이 사라지고 소매·얼굴·머릿결이 대기 디테일에 가까워졌다.'],
 ['155는 원US와 다른 수용 기본형의 몸체 정책을 계승한 후보이며 원155 몸체 완전복원이라고 하지 않는다. 짧은 반동의 연속재생·공통층 최종정합·패킹·실기는 별도다.'])]
for n,paths,findings,limits in groups:
 p=W/f'root_review_checkpoint{n}.json';assert not p.exists()
 p.write_text(json.dumps({'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in paths],
 'findings':findings,'limits':limits,'final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8')
 print(n,hashlib.sha256(p.read_bytes()).hexdigest())
