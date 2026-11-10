"""승리4의 독립 재추출8판을 실제 열람한 결과를 별도로 고정한다."""
from pathlib import Path
import hashlib, json
O = Path(__file__).resolve().parent/'nana_base_victory4_independent01'
ROOT = O.parents[3]
sha = lambda b: hashlib.sha256(b).hexdigest()
p = O/'report.json'
expected = 'ecdd70532a316932432295222d414364d369d61ed85b6ead29f437bcc58819a5'
assert sha(p.read_bytes()) == expected
r = json.loads(p.read_text('utf8'))
for s in r['readback_sheets']:
    assert sha((ROOT/s['path']).read_bytes()) == s['sha256']
notes = {
    204:'새 앞머리의 명암과 앞가슴/커프가 기존보다 구분되며 두 손이 팔과 이어진다. 부분조합에서 머리 장식·베일/팔·치마/다리의 새 고립 조각은 확인하지 못했다.',
    205:'얼굴 앞 손과 소매가 이어지고 머리 뒤 베일의 내부 명암이 보인다. 머리만/몸만/팔만/다리만을 실제 보았으며 옛 기본형 머리 장식이 엉뚱한 별도 조각으로 남는 새 확정 문제는 찾지 못했다.',
    206:'가슴 앞 접힌 팔과 반대 허리 손이 분리되어 읽힌다. 포스 다리가 기본 부츠보다 밝게 드러나는 것은 의상 차이이며 무릎/발목에서 새 단절을 보지 못했다.',
    207:'높이 든 권총·손·긴 소매가 연결되고 모자와 머리가 대기 계열로 읽힌다. 새 포스의 하체/구두 폭과 새 머리 위치는 옛 그림과 다르나, 이번 그림의 같은행 다리 등록 및 전체y−5 정합 정책과 구분해 기록한다. 숫자만으로 옛 체형 동일 또는 실기 수용을 주장하지 않는다.',
}
out = {
    'candidate_sha256':r['candidate_sha256'],
    'independent_report':{'path':p.relative_to(ROOT).as_posix(),'sha256':expected},
    'actual_viewed':[dict(s,actual_viewed=True) for s in r['readback_sheets']],
    'findings':[{'ref':n,'static_observation':note}for n,note in notes.items()],
    'assessment':'독립 완성4판·부분4판에서 추가 확정 끊김/떠 있는 아머 조각을 발견하지 못했다. 최종 root 미술 판단과 실기는 별도다.',
    'weapon_scope':'새 base 원화의 손/권총 의미범위를 두 의상에 공유한 출처를 확인했다. 정본85의20texel 동일성 또는 원래 발사총구8열 exact를 이 비발사 승리 그림에 추가 주장하지 않는다.',
    'new_native_execution':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,
}
q=O/'visual_review.json';q.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
page='<!doctype html><meta charset="utf-8"><title>나나 승리4 독립 검토</title><style>body{background:#17212b;color:#eee;font:16px/1.6 sans-serif;margin:24px}a{color:#a9daff}img{max-width:100%;image-rendering:pixelated}</style><h1>나나 기본/포스 승리4 독립 검토</h1><p>원화8셀→20층→후보 자원·비대상 보존·128부분RGBA 읽기 통과. 실제 재추출8판을 열람했다. 새 MIPS/실기 실행은 없으며 전체 완료 판정이 아니다.</p><p><a href="report.json">기술 보고</a> · <a href="visual_review.json">실제 열람 기록</a></p>'
for n,note in notes.items():
    page+=f'<p>{n}: {note}</p><img src="full_{n}.png"><img src="partial_{n}.png">'
(O/'INDEX.html').write_text(page,'utf8')
print(json.dumps({'visual_sha256':sha(q.read_bytes()),'report_sha256':expected,'viewed':len(out['actual_viewed'])}))
