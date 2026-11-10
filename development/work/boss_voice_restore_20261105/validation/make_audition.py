"""복구 12개 음성의 로컬 비교 재생표. 게임 실제 청취 증거와 구별한다."""
from pathlib import Path
import json
import html

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / 'work/boss_voice_restore_20261105/assets/prepared_combat_v1'
names = {1: '웹 스파이더', 2: '프로스트 월러스', 3: '스플릿 머쉬룸',
         5: '제트 스팅레이', 6: '사이버 피콕', 7: '스톰 아울', 8: '슬래시 비스트'}
data = json.loads((D / 'audition_manifest.json').read_text('utf8'))
rows = []
for pair in data['pairs']:
    cells = [f"<th>{names[pair['stage']]}<br>원본 파형 {pair['jp_wave']}</th>"]
    for key in ('original', 'restored'):
        item = pair[key]
        path = ROOT / item['wav_path']
        assert path.is_file() and path.is_relative_to(D)
        url = html.escape(path.relative_to(D).as_posix(), quote=True)
        cells.append(f'<td><audio controls preload="none" src="{url}"></audio>'
                     f'<br>{item["sample_rate_exact"]:.1f} Hz · {item["seconds"]:.3f}초</td>')
    kind = '최소 재표본화' if pair['reencoded'] else '원본 ADPCM / 재생 구간 보존'
    cells.append(f'<td>{kind}<br>길이 차이 {abs(pair["duration_error_seconds"])*1000:.3f} ms</td>')
    rows.append('<tr>' + ''.join(cells) + '</tr>')
page = '''<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>보스 전투 보이스 복구 비교</title>
<style>body{font:16px/1.65 system-ui;margin:2rem;background:#151a24;color:#eee}table{border-collapse:collapse;width:100%}
th,td{border:1px solid #586173;padding:1rem;text-align:left}audio{max-width:100%}a{color:#9cf}</style>
<h1>추가 복구한 보스 전투 음성 12개</h1>
<p>왼쪽은 제공 일본판, 오른쪽은 수정본에 넣은 음성입니다. 실제 게임 SDK의 음높이를 적용한 비교용 WAV입니다.
게임의 ADSR·동시 효과음·스테레오 혼합은 재현하지 않았습니다. 실제 전투 녹음은 아닙니다.</p>
<p>주인공 무음, 기존 효과음, 이전에 복구한 네 발화는 유지했습니다. 개전 대사 23개는 원본 음원 그대로 호출만 복구하여 이 표에서 제외했습니다.</p>
<table><thead><tr><th>보스</th><th>일본판 원본</th><th>복구본</th><th>처리</th></tr></thead><tbody>'''
(D / 'AUDITION.html').write_text(page + '\n'.join(rows) + '</tbody></table></html>', 'utf8')
print(json.dumps({'pairs': len(rows), 'path': (D / 'AUDITION.html').relative_to(ROOT).as_posix()}))
