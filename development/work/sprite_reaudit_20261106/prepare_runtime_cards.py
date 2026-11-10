"""기존 검증용 Ultimate 카드에서 이번 실행 전용 사본만 만든다."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'work/ver_buki_riko/shibuki_art/ultimate_v1/test_save'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    info = json.loads((SOURCE / 'unlock.json').read_text('utf8'))
    backup = SOURCE / 'original_backup'
    assert sha(backup / 'epsxe001.mcr') == info['source_card_sha256']
    assert sha(backup / 'epsxe000.mcr') == info['originals'][0]['sha256']
    base = (backup / 'epsxe001.mcr').read_bytes()
    target_card = bytearray(base)
    assert base[8788:8830].hex() == info['source_slot_hex'] and base[8829] == 0
    target_card[8829] = 1
    assert hashlib.sha256(target_card).hexdigest() == info['output_sha256']
    report = {'method': '보존된 원본 백업에서 검증용 카드만 생성. DATA3 Ultimate 한 바이트 변경. F1/F3 및 현재 사용자 카드 사용 없음.',
              'old_fixture_hash_changed': sha(SOURCE / 'card2_ultimate.mcr') != info['output_sha256'], 'projects': {}}
    for mode in ('ver_buki_riko', 'ver_rin_nana'):
        dest = ROOT / 'work' / mode / 'sprite_reaudit_20261106/cards'
        assert not dest.exists()
        dest.mkdir(parents=True)
        cards = {}
        for index, name in enumerate(('epsxe000.mcr', 'epsxe001.mcr')):
            source, target = backup / name, dest / f'card{index}.mcr'
            if index == 0:
                shutil.copyfile(source, target)
            else:
                target.write_bytes(target_card)
            expected = info['output_sha256'] if index else info['originals'][0]['sha256']
            assert sha(target) == expected and target.stat().st_size == 131072
            cards[str(index)] = {'source': source.relative_to(ROOT).as_posix(), 'path': target.relative_to(ROOT).as_posix(), 'sha256': sha(target)}
        report['projects'][mode] = cards
    (Path(__file__).parent / 'runtime_cards.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'cloned_cards': 4, 'original_cards_written': False}))


if __name__ == '__main__':
    main()
