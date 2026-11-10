"""단일 자세 재작화를 원래 셀 좌표·CLUT에 고정 배율로 등록할 입력만 준비."""
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
source = HERE / 'zero_audit/rin_extension/run_inputs/run03/inputs.json'
meta = json.loads(source.read_text('utf8'))
generated = Path('<LOCAL_PATH>')
files = {17: 'exec-4a4d63a7-c68d-4380-9fb3-3822685f70d1.png',
         18: 'exec-e0c76dd1-b6fc-4363-9740-7125a12ded61.png'}
for ref, name in files.items():
    out = HERE / 'zero_audit/rin_extension/targeted_fixes_registered' / f'pose{ref}'
    out.mkdir(parents=True, exist_ok=False)
    frame = next(f for f in meta['frames'] if f['ref'] == ref)
    item = {**meta, 'columns': 1, 'rows': 1, 'scale': 16, 'frames': [{**frame, 'cell': [0, 0]}]}
    (out / 'inputs.json').write_text(json.dumps(item, indent=2)+'\n', 'utf8')
    shutil.copyfile(generated / name, out / 'generated.png')
    print(out)
