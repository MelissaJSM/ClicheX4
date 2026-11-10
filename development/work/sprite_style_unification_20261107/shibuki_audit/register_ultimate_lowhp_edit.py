"""교정 원화를 고정 페이지 축척과 접지 앵커로만 등록한다."""
from pathlib import Path
import json
import register_ultimate_lowhp_pilot as pilot

H = Path(__file__).resolve().parent
pilot.I = H / 'ultimate_lowhp_edit01'
pilot.O = H / 'ultimate_lowhp_native02'
pilot.GEN = 'aae841c4de541d42afc625288db6b9d29b7f70d554ad8c8ffd9f5ee3615c9a86'

if __name__ == '__main__':
    pilot.main()
    p = pilot.O / 'registration.json'
    report = json.loads(p.read_text(encoding='utf-8'))
    report['next'] = '대기 체형과 자세를 실제 비교하고 양폼 공통 머리·다리 및 의상 투명 범위를 정합한다. 임의 전신 축소나 옛 저체력 머리 덮기는 하지 않는다.'
    report['revision'] = '정면 및 과도한 키를 수정하는 국소 재작화'
    report['image_generation'] = {'tool': 'builtin imagegen', 'prompt': str((pilot.I / 'prompt.txt').relative_to(pilot.ROOT)), 'single_character_slot_returned_to': 'overhaul_audio / Nana75'}
    pilot.write(p, report)
    p = pilot.I / 'inputs.json'
    info = json.loads(p.read_text(encoding='utf-8'))
    info['reason'] = '첫 새 원화의 세부 표현은 보존하되 정면 자세와 51px 키를 교정하고, 3/4 피로 굽힘과 대기 비율로 맞춘다.'
    info['generation_started'] = True
    info['generation_completed'] = True
    info['generated_sha256'] = pilot.GEN
    info['queue'] = 'Shibuki lowHP edit completed; slot returned to Nana75'
    pilot.write(p, info)
