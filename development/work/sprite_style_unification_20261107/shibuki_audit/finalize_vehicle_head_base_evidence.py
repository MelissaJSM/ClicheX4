"""기본 작은머리19의 실제 열람·원표 읽기·원MIPS 결과를 고정후보에 결속한다."""
from pathlib import Path
import json
import struct
import sys

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write
from scripts.c01_audio_build import read_disc

FINAL = '4ceab054c4fa9170a0e785fb00baa01f05afaceb4d2dfc2dcc4e80eab30ee36f'


def ev(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())}


def main():
    d = H / 'prepared_vehicle_head_base01'
    need(not (d / 'post_lock_evidence.json').exists(), '추가 근거 보호')
    need(sha((d / 'PL00_U.ARC').read_bytes()) == FINAL, '후보 변경')
    views = [d / n for n in ('base_readback_00.png', 'base_readback_01.png', 'fourth_readback_00.png', 'fourth_readback_01.png', 'ownership_184.png', 'ownership_196.png')]
    views += [H / 'vehicle_head_base_native02/comparison.png']
    write(d / 'author_visual_review.json', {
        'actually_viewed': True, 'candidate_sha256': FINAL, 'images': [ev(p) for p in views], 'actual_images': 7,
        'findings': ['19원점의 최종 기본/포스4판에서 새 머릿결과 각 의상 장식이 같은13×15 크기에 남는다. 늘어난 귀나 새 얼굴 절단은 발견하지 못했다.', '포스 검보라 옆장식과 금색3셀이 대기와 연결되며 공통 금색 눈은 가리지 않는다.', '184/196 부분16조합2판에서 머리 bit의 장식만 바뀌고 다른 아머 bit가 머리색이나 외곽을 바꾸지 않는다.', '등록 비교판에서 옛 중앙 단색면이 새 세로 가닥/명암으로 나뉜 것을 확인했다.'],
        'new_confirmed_defect': False,
        'limits': ['실제 차량 조종석의 가림·반전은 이 정적판에 없으며 게임실기는 수행하지 않았다.', '현재19동형 정책을 유지하며 원US5/6고유 머리 복원으로 주장하지 않는다.', '새 원화의 외곽추가3/5셀은 입력에서 정한 내부 편집 범위 밖으로 제외했으며 기존144alpha 안 결손은 없다.'],
        'root_review_pending': True, 'independent_pending': True, 'runtime_verified': False,
    })
    metadata_path = ROOT / 'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json'
    metadata = json.loads(metadata_path.read_text('utf8'))
    sequences = [r for r in metadata['animations'] if any(184 <= q['frame'] <= 203 for q in r['steps'])]
    current_bin = ROOT / 'out/ver_buki_riko/sprite_style_unification_20261107_v30/shibuki_riko.bin'
    current = read_disc(current_bin, ('SLUS_005.61',))[0]['SLUS_005.61']
    original = read_disc(ROOT / 'MegaMan X4.bin', ('SLUS_005.61',))[0]['SLUS_005.61']
    offset = lambda address: address - 0x80010000 + 2048
    for row in sequences:
        pos = offset(int(metadata['table_address'], 16)) + row['id'] * 4
        need(current[pos:pos + 4] == original[pos:pos + 4] and struct.unpack_from('<I', current, pos)[0] == int(row['address'], 16), '원표 포인터')
        for step in row['steps']:
            pos = offset(int(step['address'], 16))
            need(current[pos:pos + 4] == original[pos:pos + 4] and current[pos:pos + 4].hex() == step['bytes'], '원표 스텝')
    write(d / 'original_sequence_read.json', {
        'scope': '원US/BR30 실제 EXE의 작은머리 소비표 포인터·4바이트 스텝 읽기. 재생 또는 원caller 실행이 아니다.',
        'candidate_sha256': FINAL, 'original_EXE_sha256': sha(original), 'current_EXE_sha256': sha(current), 'metadata': ev(metadata_path),
        'animation_ids': [row['id'] for row in sequences], 'table_count': len(sequences), 'step_count': sum(len(row['steps']) for row in sequences),
        'all_pointer_step_bytes_exact': True, 'sequences': sequences, 'changes_to_EXE': False,
        'limits': ['96호출 self-loop는 외부상태 변경 전 유지이며 전체 동작 시간으로 세지 않는다.', '빈198이 포함된 표50/51을 보존한다. 선형표에서 관측하지 않은190도 삭제하지 않는다.', '실제 차량 입력·카메라·조종석 가림·좌우반전·게임실기는 별도다.'], 'runtime_verified': False,
    })
    peer = H.parent / 'nana_audit/shibuki_vehicle_head_base_semantic_read01'
    native_path = H / 'vehicle_head_base_components_native_checks.json'
    native = json.loads(native_path.read_text('utf8'))
    need(native['passed'] and native['resources']['PL00_U.ARC']['candidate_sha256'] == FINAL, '원MIPS 후보')
    rows = [v for bank in native['resources']['PL00_U.ARC']['banks'] for v in bank['native_decoder_checks']]
    need(len(rows) == 19 and all(v['buffer_outside_and_unused_tail_preserved'] for v in rows), '원MIPS19 경계')
    evidence = [d / 'author_visual_review.json', d / 'original_sequence_read.json', H / 'vehicle_head_base_components.json', native_path, peer / 'report.json', peer / 'READER_LOCK.json', Path(__file__)]
    write(d / 'post_lock_evidence.json', {'candidate_sha256': FINAL, 'evidence': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in evidence}, 'candidate_unchanged': True, 'new_runtime_execution': False, 'semantic_source_peer_scope': '패킹 전2셀 원화→기본공통/포스39소유 직접재구성.19별칭·ARC독립은 후속이다.'})
    print(json.dumps({'author': sha((d / 'author_visual_review.json').read_bytes()), 'tables': len(sequences), 'steps': sum(len(row['steps']) for row in sequences), 'native': sha(native_path.read_bytes()), 'post': sha((d / 'post_lock_evidence.json').read_bytes())}))


if __name__ == '__main__':
    main()
