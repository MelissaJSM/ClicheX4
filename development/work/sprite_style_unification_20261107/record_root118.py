from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[H/'ultimate_victory_pack01'/f'{form}_readback_{i:02}.png' for form in ('before','after') for i in range(2)]
paths += [H/'ultimate_victory_pack01'/f'partial_{n}.png' for n in range(204,208)]
paths += [H/'ultimate_victory_sequence01'/f'{form}_id39_ordered.png' for form in ('before','after')]
out=W/'root_review_checkpoint118.json';assert not out.exists()
result={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],
 'arc_sha256':'ec7a6847ec8de42a3b25c1d0b87fdc96330bc61488c2296426ab24cbe9cfa9b8',
 'findings':['시부키 Ultimate 승리204..207 두 의상의 재추출4판·부분파츠4판·원표39 순서2판을 직접 열람했다.',
 '대기의 귀·고글·땋은 머리와 비교해 새 포즈에서도 머릿결 명암·소매 가장자리·복장 장식이 유지된다. 두 의상의 머리/사지 위치와 맨팔 손목 연결을 확인했다.',
 '207의 높이 증가는 치켜든 주먹에 따른 것이며 몸통을 길게 늘린 그림으로 보이지 않는다. 204~207 부분파츠 판에서 추가 확정 단절이나 소매 누출을 찾지 못했다.',
 '승리 진입81은 이전 통합 그림이다. 이번10판 검토는 새204..207 범위이며 귀환156..158, 전체 미술 및 실제 클리어 검증을 뜻하지 않는다.'],
 'runtime_verified':False,'continuous_animation_actually_watched_by_model':False,'all_character_art_complete':False,'final_user_accepted':False}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
