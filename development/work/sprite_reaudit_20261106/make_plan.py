"""동결된 준비본을 기존 범위 제한 BIN 빌더 계획으로 연결한다."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('proposal', type=Path)
    args = parser.parse_args()
    args.proposal = args.proposal.resolve()
    proposal = json.loads(args.proposal.read_text('utf8'))
    mode = proposal['project']
    assert mode in ('ver_buki_riko', 'ver_rin_nana')
    path = WORK / (mode + '_plan.json')
    assert not path.exists()
    plan = {'project': mode, 'source_bin': proposal['baseline'], 'source_sha256': proposal['baseline_sha256'],
            'resources': proposal['files'], 'output': f'out/{mode}/sprite_reaudit_20261106_v1', 'review_images': []}
    name = 'shibuki' if mode == 'ver_buki_riko' else 'nana'
    sheets = sorted(p for p in args.proposal.parent.glob('*_after_*.png') if p.stem.split('_')[0] in ('run', 'air', 'wall', 'dash')) if name == 'shibuki' else []
    for sheet in sheets:
        plan['review_images'].append({'character': name, 'path': sheet.relative_to(ROOT).as_posix(), 'label': sheet.stem})
    if name == 'nana':
        for item, label in [('nana/prepared_v1/comparison.png', '부분 아머 베일 도트 소유권 수정'), ('nana/prepared_frost_v1/comparison.png', '프로스트 실드 다리 명암 전후')]:
            sheet = WORK / item
            assert sheet.exists()
            plan['review_images'].append({'character': name, 'path': sheet.relative_to(ROOT).as_posix(), 'label': label})
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', 'utf8')
    print(path)


if __name__ == '__main__':
    main()
