"""Original sequence traversal with the packed boot material revision; offline only."""
from pathlib import Path
import sys, json, hashlib, base64, io, struct
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.export_sprite_playback import read_disc, parse_sequence, TABLES, at, ZERO_SELECTOR
from scripts.overhaul_sprites_audit import render, rgba
from scripts.prepare_riko_ui import entry

D = Path(__file__).resolve().parent
O = D / 'ground_boots_cycle04'
O.mkdir(exist_ok=False)
sha = lambda b: hashlib.sha256(b).hexdigest()
old = (D / 'prepared_spin_clothes_v1/PL01_U.ARC').read_bytes()
new = (D / 'prepared_ground_boots_v13/PL01_U.ARC').read_bytes()
assert sha(new) == '026dd3d47ff05e7a7e9b6ef2330ab06d6be3c617586b6d3aa124a295aee74391'
targets = set()
for folder in ('prepared_ground_boots_v3', 'prepared_ground_boots_v4', 'prepared_ground_boots_v13'):
    q = json.loads((D / folder / 'proposal.json').read_text('utf8'))
    targets.update((int(s[1]), int(s[3:])) for s in q['target_references'])
disc = ROOT / 'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin'
exe = read_disc(disc, ['SLUS_005.61'])['SLUS_005.61']
assert sha(exe) == '93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616'
sequences, cases = {}, {}
for aid in range(144):
    bank = at(exe, ZERO_SELECTOR + aid, 1)[0]
    sequence = parse_sequence(exe, TABLES['zero'], aid)
    if not any((bank, s['frame_ref']) in targets for s in sequence['steps']):
        continue
    assert bank in (0, 1)
    sequences[str(aid)] = dict(bank=bank, **sequence)
    cases[f'{aid} / bank {bank}'] = {
        'steps': [{'ref': f'{bank}:{s["frame_ref"]}', 'calls': s['duration_calls']} for s in sequence['steps']],
        'loop': sequence['loop_start_index'],
    }
refs = sorted({s['ref'] for c in cases.values() for s in c['steps']})
data = {}
crop = (112, 112, 208, 192)
for name, row in [('normal', 0), ('black', 13)]:
    data[name] = {}
    palette = struct.unpack_from('<16H', entry(new, 9), row * 32)
    for key in refs:
        bank, ref = map(int, key.split(':'))
        uris = []
        for arc in (old, new):
            im = rgba(render(arc, bank, 5 if bank else 0, ref)[0], palette).crop(crop)
            buf = io.BytesIO()
            im.save(buf, format='PNG')
            uris.append('data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode())
        data[name][key] = uris
    for aid, sequence in sequences.items():
        bank = sequence['bank']
        for start in range(0, len(sequence['steps']), 6):
            sheet = Image.new('RGB', (1728, 540), '#64717b')
            draw = ImageDraw.Draw(sheet)
            for j, s in enumerate(sequence['steps'][start:start + 6]):
                for side, arc in enumerate((old, new)):
                    im = rgba(render(arc, bank, 5 if bank else 0, s['frame_ref'])[0], palette)
                    im = im.crop(crop).resize((288, 240), Image.Resampling.NEAREST)
                    sheet.paste(im, (j * 288, side * 270 + 25), im)
                    draw.text((j * 288 + 4, side * 270 + 4), f'{bank}:{s["frame_ref"]} / {s["duration_calls"]} calls / ' + ('before' if not side else 'candidate'), fill='white')
            sheet.save(O / f'{name}_{aid}_{start:02}.png')
html = (D / 'ground_boots_cycle_template.html').read_text('utf8')
html = html.replace('DATA', json.dumps(data, separators=(',', ':'))).replace('CASES', json.dumps(cases, separators=(',', ':')))
(O / 'REVIEW.html').write_text(html, 'utf8')
(O / 'manifest.json').write_text(json.dumps({
    'before_arc_sha256': sha(old), 'after_arc_sha256': sha(new), 'exe_sha256': sha(exe),
    'sequences': sequences, 'html_sha256': sha(html.encode()), 'runtime_verified': False,
    'target_refs': sorted(targets), 'clock_assumption': '60 animate calls/sec',
}, indent=2), 'utf8')
print(json.dumps({'output': str(O), 'animations': len(sequences), 'refs': len(refs)}))
