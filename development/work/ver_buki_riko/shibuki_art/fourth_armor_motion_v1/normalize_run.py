"""생성 이동 시트의 공통 축척·팔레트·기준점 정규화. 승인 몸의 포즈를 대조한다."""
from collections import deque
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.extract_zero import save_image

D = Path(__file__).resolve().parent
OUT = D / 'normalized01'
OUT.mkdir(exist_ok=False)
source = Image.open(D / 'run_generated.png').convert('RGBA')
words = json.loads((D.parent / 'fourth_armor_v1/layers03/layers.json').read_text())['palette_words']
rgb = np.array([[(v & 31)*255//31, ((v>>5)&31)*255//31, ((v>>10)&31)*255//31] for v in words], np.int32)
order = json.loads((D / 'run_pose_order.json').read_text())


def main_component(alpha):
    available = alpha >= 200
    best = []
    height, width = available.shape
    while available.any():
        y, x = np.argwhere(available)[0]
        points = [(int(y), int(x))]
        queue = deque(points)
        available[y, x] = False
        while queue:
            y, x = queue.popleft()
            for yy, xx in ((y-1,x), (y+1,x), (y,x-1), (y,x+1)):
                if 0 <= yy < height and 0 <= xx < width and available[yy, xx]:
                    available[yy, xx] = False
                    queue.append((yy, xx))
                    points.append((yy, xx))
        if len(points) > len(best):
            best = points
    mask = np.zeros_like(available)
    for y, x in best:
        mask[y, x] = True
    return mask


cells = []
for i, n in enumerate(order):
    box = (round(i % 4 * source.width / 4), round(i // 4 * source.height / 4),
           round((i % 4 + 1) * source.width / 4), round((i // 4 + 1) * source.height / 4))
    im = source.crop(box)
    rgba = np.array(im)
    mask = main_component(rgba[:, :, 3])
    ys, xs = np.nonzero(mask)
    bb = (int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1))
    rgba[:, :, 3] = np.where(mask, rgba[:, :, 3], 0)
    cells.append((n, Image.fromarray(rgba).crop(bb), box, bb))

scale = 47 / cells[0][1].height
sheet = Image.new('RGB', (4*440, 4*420), '#253546')
draw = ImageDraw.Draw(sheet)
reports = []
for i, (n, im, cell, bb) in enumerate(cells):
    width, height = round(im.width*scale), round(im.height*scale)
    rgba = np.array(im)
    labels = np.zeros(rgba.shape[:2], np.uint8)
    for y in range(im.height):
        delta = rgba[y, :, :3].astype(np.int32)[:, None, :] - rgb[1:][None, :, :]
        labels[y] = np.argmin((delta*delta).sum(2), axis=1)+1
    votes = [np.array(Image.fromarray(np.where(labels == k, rgba[:, :, 3], 0).astype(np.uint8)).resize((width, height), Image.Resampling.BOX)) for k in range(1,16)]
    pixels = (np.argmax(np.stack(votes), axis=0)+1).astype(np.uint8)
    alpha = np.array(im.getchannel('A').resize((width,height), Image.Resampling.BOX))
    pixels[alpha < 128] = 0
    base = Image.open(D / f'base_{n:03}.png').convert('RGBA')
    ba = np.array(base)
    by, bx = np.nonzero(ba[:,:,3])
    # Ears/head center are the placement anchor, never a separate pose-size fit.
    target_top = int(by.min())
    bhx = np.nonzero(ba[target_top:target_top+17, :, 3])[1]
    gy, gx = np.nonzero(pixels[:17])
    left = round((bhx.min()+bhx.max())/2 - (gx.min()+gx.max())/2)
    canvas = np.zeros((160,160), np.uint8)
    canvas[target_top:target_top+height, left:left+width] = pixels
    pic = save_image(canvas.tobytes(), (160,160), words, OUT / f'costume_{n:03}.png').convert('RGBA')
    for j, art in enumerate((base,pic)):
        tile = art.crop((50,45,105,112)).resize((220,268), Image.Resampling.NEAREST)
        sheet.paste(tile, (i%4*440+j*220, i//4*420+32), tile)
    draw.text((i%4*440+10,i//4*420+10), f'{n:03} base / generated costume', fill='white')
    reports.append({'frame': n, 'source_cell': cell, 'source_bbox': bb, 'native_size':[width,height], 'position':[left,target_top],
                    'base_bbox':[int(bx.min()),int(by.min()),int(bx.max()+1),int(by.max()+1)]})
sheet.save(OUT/'comparison.png')
(OUT/'normalization.json').write_text(json.dumps({'scale':scale,'palette_words':words,'frames':reports,'runtime_verified':False},indent=2))
print(json.dumps({'output':str(OUT),'common_scale':scale,'frames':reports}))
