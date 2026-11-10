"""나나 기본/포스 라이징7의 기존 검증 증거를 동결한다. 게임 자원 쓰기 없음."""
from pathlib import Path
import hashlib
import json

D = Path(__file__).resolve().parent
ROOT = D.parents[3]
P = D / 'packed_base_candidate_v1'
FINAL = '3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'
PARENT = 'cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text('utf8'))
rel = lambda p: p.relative_to(ROOT).as_posix()


def main():
    out = P / 'FROZEN.json'
    assert not out.exists(), '기존 동결 기록 덮어쓰기 거부'
    assert sha(P / 'PL00_U.ARC') == FINAL
    proposal = read(P / 'proposal.json')
    assert proposal['files']['PL00_U.ARC']['after'] == FINAL
    assert proposal['working_parent_arc_sha256'] == PARENT
    independent = ROOT / 'work/sprite_style_unification_20261107/zero_audit/nana_rising7_independent01/report.json'
    assert sha(independent) == '3b3c7cad3ec2ca8f2702271097e9d116731423fe9d4fc386eda7a7068f93633d'
    ij = read(independent)
    assert ij['passed'] and ij['candidate_sha256'] == FINAL and ij['parent_sha256'] == PARENT
    lockpath = P / 'INPUT_FROZEN.json'
    assert sha(lockpath) == ij['input_frozen_sha256']
    lock = read(lockpath)
    assert lock['candidate_sha256'] == FINAL and len(lock['files']) == 316
    for item in lock['files']:
        assert sha(ROOT / item['path']) == item['sha256'], item['path']
    target = D / 'joint_layers_probe_v2/manifest.json'
    assert sha(target) == ij['target_manifest_sha256']
    checkpoints = []
    viewed = []
    for number, digest in [(65, '94cb2c11ca9b30be914631661f1d83eeacb1ce207549acad3b3b27d2b3e05ed9'),
                           (66, 'd858b9c1e2f45b31aee7c057cce3eb76097d5f555b8c5faf99ffaa98c0ff142c')]:
        p = ROOT / f'work/sprite_style_unification_20261107/root_review_checkpoint{number}.json'
        assert sha(p) == digest
        checkpoints.append(p)
        for item in read(p)['root_actually_viewed']:
            if 'nana_audit/rising_repaint/' in item['path']:
                q = ROOT / item['path']
                assert sha(q) == item['sha256']
                viewed.append(q)
    assert len(viewed) == 8
    proofs = [P / 'verification.json', P / 'weapon_effect_verification.json', P / 'reproduction.json',
              D / 'native_components_native_checks.json', D / 'native_cycle_v1/verification.json', independent]
    for p in proofs:
        assert read(p)['passed'], rel(p)
    native = read(D / 'native_components_native_checks.json')
    assert native['resources']['PL00_U.ARC']['candidate_sha256'] == FINAL
    assert read(P / 'reproduction.json')['candidate_sha256'] == FINAL
    assert read(D / 'native_cycle_v1/verification.json')['candidate_arc_sha256'] == FINAL
    files = [P / 'PL00_U.ARC', P / 'proposal.json', lockpath, target, *proofs, *checkpoints, *viewed,
             D / 'native_components.json', D / 'native_cycle_v1/manifest.json',
             D / 'native_cycle_v1/REVIEW.html', D / 'verify_reproduction.py',
             D / 'make_native_cycle.py', D / 'verify_native_cycle.py', Path(__file__).resolve()]
    result = {
        'frozen': True,
        'status': '나나 기본/포스 라이징7 준비 자원 동결. 기술·독립 검사와 루트 정적 미술 검토 완료, 새 게임 통합·실기는 별도.',
        'character': 'nana', 'forms': ['base', 'fourth_arm1', 'fourth_arm2', 'partial_masks'],
        'refs': [100, 101, 102, 103, 104, 231, 232],
        'asset_sha256': FINAL, 'parent_asset_sha256': PARENT,
        'original_active_asset_sha256': proposal['files']['PL00_U.ARC']['before'],
        'files': [{'path': rel(p), 'sha256': sha(p)} for p in files],
        'input_files_verified_unchanged': len(lock['files']),
        'independent_counts': ij['counts'],
        'root_art_review_checkpoints': [rel(p) for p in checkpoints],
        'root_static_art_direction_accepted': True,
        'original_MIPS_decode_and_GPU_upload_checked': True,
        'offline_canvas_play_pause_checked': True,
        'reproduction': '동일 프로세스 메모리 재제작 byte-identical, 12종 잘못된 입력 거부. 별도 프로세스 출력 재생성은 미실행.',
        '231_232_relation': '표시와 새 디코딩 데이터가 동일하지만 물리 스트림은 각각 133804/135064로 분리돼 있다. 원본도 별도 스트림이다.',
        'limits': ['원 효과 은행/초기 생성 좌표 보존과 실제 게임의 전시간표 불꽃 접점 검증을 구분한다.',
                   '권총은 수용된 85의 20텍셀 정본을 90도 회전한 8px 모듈이며 모든 옛 권총 모양 그대로 보존을 뜻하지 않는다.',
                   '독립 reader는 등록35층과 실제 자원 및 고정 입력 해시를 검사했고 생성 원화 전과정 재현은 하지 않았다.'],
        'runtime_verified': False, 'final_user_accepted': False,
        'all_nana_style_complete': False, 'game_BIN_pointer_save_written': False,
    }
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'frozen': True, 'asset_sha256': FINAL, 'freeze_sha256': sha(out)}))


if __name__ == '__main__':
    main()
