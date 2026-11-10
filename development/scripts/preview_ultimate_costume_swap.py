"""원본 픽셀을 편집하지 않는 얼티밋 전후 배정 비교표."""
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw, ImageFont
from scripts.ultimate_costume_swap_ui import read, SOURCES
from scripts.overhaul_sprites_audit import render, rgba
from scripts.prepare_riko_ui import entry


def main():
    out = ROOT / 'out/ultimate_costume_swap_review_20261105'
    out.mkdir(exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 20)
    small = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 16)
    sheet = Image.new('RGB', (1024, 734), '#1c2533')
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 14), '얼티밋 의상 교환안 · 정적 조립 미리보기 (게임 캡처 아님)', font=font, fill='white')
    proof = []
    for column, (project, label) in enumerate((('ver_buki_riko', '텐코 시부키'), ('ver_rin_nana', '하나코 나나'))):
        data, _ = read(project, ('PL02_U.ARC',))
        arc = data['PL02_U.ARC']
        words = struct.unpack_from('<64H', entry(arc, 9))
        draw.text((column * 512 + 180, 56), label, font=font, fill='#e3d5fa')
        for state, title in enumerate(('캡슐 전 · 재킷', '획득 후 · 수영복')):
            x = column * 512 + state * 256
            draw.text((x + 38, 93), title, font=small, fill='#dce5ef')
            for row, frame in enumerate((0, 1)):
                picture = Image.new('RGBA', (384, 384))
                for layer in ((0, 8, 5, 7, 6) if state == 0 else (0,)):
                    indices, _ = render(arc, 0, layer, frame)
                    palette = words if layer == 0 else words[32:48] if layer == 7 else words[16:32]
                    picture.alpha_composite(rgba(indices, palette))
                y = 130 + row * 276
                shown = picture.crop((124, 117, 188, 181)).resize((256, 256), Image.Resampling.NEAREST)
                sheet.paste(shown, (x, y), shown)
                draw.text((x + 80, y + 252), '대기' if frame == 0 else '사격 준비', font=small, fill='#b7c4d5')
        proof.append({'project': project, 'parent': SOURCES[project][0], 'parent_sha256': SOURCES[project][1],
                      'frames': [0, 1], 'capsule_before_layers': [0, 8, 5, 7, 6], 'acquired_layers': [0],
                      'art_pixels_reused_without_modification': True})
    draw.text((24, 700), '능력·파츠 소유·탄환은 유지하며 의상을 선택하는 순서만 교환합니다.', font=small, fill='#c9d6e7')
    sheet.save(out / 'overview.png')
    (out / 'overview.json').write_text(json.dumps({'kind': 'static_proposal_not_runtime', 'sources': proof}, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print((out / 'overview.png').relative_to(ROOT).as_posix())


if __name__ == '__main__':
    main()
