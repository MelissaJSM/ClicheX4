"""Contact sheets from captured emulator frames; no sprite editing."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

R = Path('work/sprite_style_unification_20261107/runtime')
play = R / 'shibuki_rising11_play'
out = R / 'shibuki_rising11_review'
out.mkdir(exist_ok=False)
record = json.loads((play / 'evidence.json').read_text('utf8'))
im = Image.open(play / 'play.webp')
groups = {
    'normal_right': (1.0,1.9),
    'jump_right': (3.15,4.1),
    'charged_right': (7.75,8.8),
    'normal_left': (11.0,11.9),
    'charged_left': (14.75,15.8),
    'jump_left': (18.15,19.1),
}
box = (120, 40, 470, 560)
cw, ch = box[2] - box[0], box[3] - box[1]
pages = []
for name, (lo, hi) in groups.items():
    ids = [i for i, t in enumerate(record['capture_times']) if lo <= t <= hi]
    for part, start in enumerate(range(0, len(ids), 12)):
        selected = ids[start:start + 12]
        board = Image.new('RGB', (cw * 4, (ch + 24) * math.ceil(len(selected) / 4)), '#202630')
        draw = ImageDraw.Draw(board)
        for j, index in enumerate(selected):
            im.seek(index)
            x, y = j % 4 * cw, j // 4 * (ch + 24)
            board.paste(im.convert('RGB').crop(box), (x, y + 24))
            draw.text((x + 4, y + 5), f'{name} {index} / {record["capture_times"][index]:.3f}s', fill='white')
        dest = out / f'{name}_{part:02}.png'
        board.save(dest)
        pages.append({'path': dest.as_posix(), 'indices': selected, 'crop': box})
(out / 'manifest.json').write_text(json.dumps({
    'source': (play / 'play.webp').as_posix(), 'actual_window_crops': True,
    'sprite_pixels_edited': False, 'resampled': False, 'pages': pages,
}, indent=2) + '\n', 'utf8')
print(json.dumps({'pages': len(pages), 'out': out.as_posix()}))
