from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
out = Path(__file__).parent
card = Image.new('RGB', (900, 380), (30, 33, 40))
draw = ImageDraw.Draw(card)
font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 18)
items = [
    ('out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png', '선택한 v2 대기'),
    ('work/ver_buki_riko/pose_samples/20261023T103048720382Z/frame_007.png', '이동 · 검토용 샘플'),
    ('work/ver_buki_riko/pose_samples/20261023T100704762342Z/frame_022.png', '점프 · 검토용 샘플'),
]
for i, (path, label) in enumerate(items):
    picture = Image.open(ROOT/path).convert('RGBA')
    enlarged = picture.resize((picture.width*4, picture.height*4), Image.Resampling.NEAREST)
    draw.text((i*300+12, 10), label, font=font, fill='white')
    card.paste(enlarged, (i*300+12, 65), enlarged)
    card.paste(picture, (i*300+230, 300), picture)
draw.text((12, 350), '4배 최근접 확대 / 오른쪽 아래 1배 · 이동과 점프는 게임 미적용', font=font, fill='white')
card.save(out/'review_1x_4x.png')
