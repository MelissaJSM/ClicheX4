"""Record root's actual image inspection and freeze exact Zero UI copies."""
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[1]
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)}
def write(p, obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    if p.exists():
        assert p.read_text('utf8') == text, p
    else:
        p.write_text(text, 'utf8')

images = []
for who in ['riko', 'rin']:
    manifest = read(W / 'selection_sync01' / who / 'readback_manifest.json')
    assert len(manifest['pages']) == 4
    for row in manifest['pages']:
        p = ROOT / row['path']
        assert sha(p) == row['sha256']
        images.append({**bind(p), 'root_actually_viewed': True})
    p = W / 'selection_sync_audit01' / who / 'comparison_00.png'
    images.append({**bind(p), 'root_actually_viewed': True})
review = W / 'root_review_checkpoint36.json'
write(review, {
    'art_review_images': images,
    'findings': ['리코/린 최종 선택 사본32개씩을 재추출한8판 전체를 직접 검토했다.',
                 '기존/새 body 첫 비교판2장도 검토했다. 리코25개·린30개 사본의 구도트가 최신 플레이용 상세도와 동일해졌다.',
                 '눈/머리/옷 윤곽·회복과 복귀 실루엣 보존. 귀환의 의도된 백색 실루엣과 빛기둥은 캐릭터 미완성으로 세지 않는다.'],
    'limits': ['이 검토는 ARC 정적 재추출이다. 실제 선택 화면 재생은 다음 통합 빌드에서 수행한다.'],
    'final_user_accepted': False})
independent = W / 'zero_audit/selection_sync_independent01/report.json'
guard = W / 'selection_sync01/guard_checks.json'
assert read(independent)['passed'] and read(guard)['passed']
for who in ['riko', 'rin']:
    folder = W / 'selection_sync01' / who
    arc = folder / 'ST0E_U1.ARC'
    source = read(folder / 'report.json')
    assert sha(arc) == source['candidate_sha256']
    assert read(independent)['projects'][who]['candidate_sha256'] == sha(arc)
    paths = [arc, folder/'report.json', folder/'readback_manifest.json', independent, guard, review,
             W/'prepare_zero_selection_sync.py', W/'pack_selection_mirrors.py',
             W/'test_zero_selection_sync_guard.py', W/'review_zero_selection_sync.py',
             ROOT/'scripts/build_sprite_style_unification.py']
    paths += [ROOT / r['path'] for r in read(folder/'readback_manifest.json')['pages']]
    write(folder/'FROZEN.json', {
        'asset_sha256': sha(arc), 'files': [bind(p) for p in paths],
        'body_sha256_at_review': source['body_sha256'],
        'root_art_review_pending': False, 'independent_checked': True,
        'ready_for_checkpoint_integration': True, 'runtime_verified': False,
        'user_accepted': False, 'target_copies': 32,
        'scope': 'Zero 선택 사본만 최신 플레이용과 동일한 픽셀·원점으로 교체. 초상화/X/비대상/팔레트 보존.'})
print(json.dumps({'root_review': bind(review), 'frozen': [bind(W/'selection_sync01'/x/'FROZEN.json') for x in ['riko','rin']]}))
