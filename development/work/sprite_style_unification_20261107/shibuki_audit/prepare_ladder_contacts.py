"""사다리 신규 원화의 접점만 교정하기 위한 입력과 수치 근거를 만든다."""
from pathlib import Path
import json
import numpy as np
from PIL import Image

H = Path(__file__).resolve().parent
OUT = H / 'ladder_contact_inputs01'
OUT.mkdir(exist_ok=True)
board = Image.new('RGBA', (1536, 1024))
for row, form in enumerate(('base', 'fourth')):
    for col, ref in enumerate((149, 151, 153)):
        im = Image.open(H / f'ladder_native_page02/{form}_{ref:03}.png')
        board.alpha_composite(im.crop((128,128,192,192)).resize((512,512), Image.Resampling.NEAREST), (512*col,512*row))
board.save(OUT / 'new_native_page02.png')
spec = {
    'input_page': 'ladder_native_page02',
    'native_origin': [160,160],
    'cell_world_origin': [32,32],
    'fixed_scale': 8,
    'scope': '생성 원화 접점 교정 입력이며 게임 적용본이 아님',
    'forbidden': ['전체 몸 크기 변경', '팔 또는 소매 직사각형 늘리기', '옛 머리·몸체 덮어쓰기'],
    'refs': {
        '149': {'upper_hand': {'source_skin_bbox': [0,-26,4,-23], 'desired_top': -28, 'desired_left': -1},
                'base_lowest_foot_y': 22, 'fourth_lowest_foot_y': 23, 'desired_lowest_foot_y': 22},
        '151': {'upper_hand': {'source_skin_bbox': [-9,-26,-5,-23], 'desired_top': -27},
                'lower_hand': {'source_skin_bbox': [11,-10,13,-7], 'desired_top': -11},
                'base_lowest_foot_y': 21, 'fourth_lowest_foot_y': 23, 'desired_lowest_foot_y': 21},
        '153': {'base_lowest_foot_y': 11, 'fourth_lowest_foot_y': 12, 'desired_lowest_foot_y': 11}
    },
    'note': '손 크기 자체를 옛 피부 사각형에 맞추지 않는다. 손끝 접점과 신체 관절만 유지하며 신규 소매 주름으로 자연스럽게 연결한다.'
}
(OUT / 'contact_targets.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
prompt = '''Edit this exact transparent 1536x1024 sprite sheet, six sprites in a 3-column by 2-row grid of 512x512 cells. Each cell is a 64x64 native canvas magnified exactly eight times, with world origin at (32,32). Top row shrine outfit, bottom row black/gold Fourth outfit. Preserve all newly detailed hair, ears, head angle, face, torso, clothing details, silhouette, pose and scale except the precise small contact repairs below. Do not redraw the character broadly or recenter any cell.

First column, pose149, both outfits: the raised hand currently starts at world y=-26, x=0. Its fingertips must reach world y=-28 and x=-1. Move/re-articulate the existing raised hand and short wrist/upper sleeve locally to achieve that reach, with a naturally connected bent sleeve. Do not move the head or shoulder, do not stretch the whole sleeve, and do not insert any long rectangular strip. The skin, cuff and sleeve must form a single connected anatomically short arm. In the lower-row Fourth sprite only, raise the lowest boot toe by exactly one native pixel, to the same ground/contact height as the top-row sprite, world y=22. Keep the knee and hip fixed and resolve the small ankle transition naturally.

Second column, pose151, both outfits: shift the raised hand's top to world y=-27 (one native pixel higher) and the lower right hand's top to world y=-11 (one native pixel higher), with natural wrist/cuff articulation and unchanged shoulders. In the lower-row Fourth sprite only, raise the lowest boot/toe by two native pixels to world y=21, matching the top-row pose. Preserve knee/hip and keep a short natural boot; do not move the whole body or tail.

Third column, pose153: preserve both hands, head and body. The lower-row Fourth sprite's lowest boot/toe is one native pixel too low; locally bring its bottom to world y=11 matching the top-row sprite, retaining the newly drawn boot shape and texture. All other parts of this column remain unchanged.

Maintain crisp native one-pixel outlines and the existing light/mid/shadow pixel clusters. No new facial or costume redesign, no extra limbs, no ladder/background/grid/labels/guide markers. True transparent background. Preserve the exact six cell placements, original height and scale. Only the named small hand/boot regions may differ; adjacent wrist/ankle connectors may be locally re-articulated, never stretched.'''
(OUT/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
print(str(OUT))
