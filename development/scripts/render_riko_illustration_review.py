"""이미 삽입한 인덱스 이미지와 원본의 오프라인 검토표를 만든다."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'work/ver_buki_riko/art_pilot/illustrations_v1'
C = D / 'candidate05'
U = D.parent / 'ui_zero_v1'


def main():
    canvas = Image.new('RGB', (1520, 1090), (24, 30, 43))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 28)
    small = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 20)
    draw.text((24, 18), 'Riko 일러스트 교체 — Mega Man X4', font=font, fill='white')
    draw.text((24, 60), '오프라인 자산 비교 · 실제 게임 캡처 아님 · 최근접 정수 배율 · 사용자 최종 검토 전', font=small, fill=(170, 196, 215))
    items = [
        (U/'portrait_zero_row5.png', '선택 화면 원본 · 2배', 24, 140, 2),
        (C/'select_portrait.png', '선택 화면 Riko · 2배', 440, 140, 2),
        (D/'dialogue_zero_col63.png', '대화 원본 · 2배', 870, 140, 2),
        (C/'dialogue_1.png', '대화 Riko · 2배', 1150, 140, 2),
        (D/'base_zero_original.png', '베이스 원본 · 2배', 870, 450, 2),
        (C/'base_00.png', '베이스 Riko · 2배', 1080, 450, 2),
        (C/'pause_portrait.png', '메뉴 얼굴 · 2배', 1300, 450, 2),
        (C/'base_07.png', '대화 자세 · 2배', 24, 620, 2),
        (C/'base_10.png', '반응 자세 · 2배', 240, 620, 2),
        (C/'base_13.png', '출발 자세 · 2배', 460, 620, 2),
        (C/'dialogue_0.png', '입 모양 0 · 1배', 24, 945, 1),
        (C/'dialogue_1.png', '입 모양 1 · 1배', 220, 945, 1),
        (C/'dialogue_2.png', '입 모양 2 · 1배', 420, 945, 1),
        (C/'title_portrait.png', '타이틀·기술 획득용 · 1배', 1090, 780, 1),
        (C/'name_7.png', '이름 그림 · 2배', 640, 930, 2),
    ]
    for path, label, x, y, scale in items:
        im = Image.open(path).convert('RGBA')
        im = im.resize((im.width*scale, im.height*scale), Image.Resampling.NEAREST)
        draw.text((x, y-34), label, font=small, fill=(204, 224, 234))
        canvas.paste(im, (x, y), im)
    canvas.save(D/'final_review.png')
    print(D/'final_review.png')


if __name__ == '__main__':
    main()
