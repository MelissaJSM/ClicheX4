"""남은 특수 동작4 자세를 실제 좌표와 원무기 길이를 유지한 입력으로 준비한다."""
from pathlib import Path
import sys,json,hashlib,struct
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_dash_clothes_v1/PL01_U.ARC';arc=P.read_bytes();D=W/'riko/special_clothes13';D.mkdir(exist_ok=False)
assert hashlib.sha256(arc).hexdigest()=='93844db97721cc95c89ece5a81eb48d9135f1e0f2c5aafb172d2890b11bff1b5'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(80,104,208,200);refs=[50,57,108,128];sheet=Image.new('RGBA',(2048,1536));rows=[]
for i,n in enumerate(refs):
    pic=rgba(render(arc,1,5,n)[0],pal);pic.save(D/f'b1_{n:03}_source.png');sheet.paste(pic.crop(crop).resize((1024,768),Image.Resampling.NEAREST),(i%2*1024,i//2*768));rows.append(dict(bank=1,ref=n,cell=i))
sheet.save(D/'targets.png');style=Image.new('RGBA',(2304,768))
for i,n in enumerate([147,33,39]):
    pic=rgba(render(arc,0,0,n)[0],pal);style.paste(pic.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i*768,0))
style.save(D/'accepted_style.png')
prompt='''Refine FIRST reference: exactly FOUR existing Riko Mega Man X4 action sprites, TWO rows by TWO columns. Transparent background. Each cell has native128x96 canvas shown8x. Preserve all four precise poses and pixel-grid body scale, head location, hand/weapon endpoint, leg length, foot position. The bottom two lunges must stay forward leaning with a short handle extending to the left at its current exact location; NO long new sword. Top two maintain the raised forearm/extended forearm difference and bent suspended legs. SECOND reference is accepted idle and newly detailed landing/wall outfits: match their fine white fitted jacket collar/cuffs/seams, gray cloth planes, short white pleated skirt, detailed white knee boots with gray ankles/heels and selective one-pixel navy edges. Enrich blank white fabric surfaces with crisp coherent folds without bulk, larger boots, longer torso or moving limbs. Original detailed green bob hairstyle and violet eye must remain same silhouette/angle/scale. Keep teal-white cape attached and flowing exactly as in each first-reference pose. No pose substitution, no text, no effects, no floor, no background, no extra particles, no blur or rounded smooth illustration. Native sprite craftsmanship consistent with accepted idle.'''
(D/'prompt.txt').write_text(prompt+'\n','utf8');(D/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=hashlib.sha256(arc).hexdigest(),native_cell=[128,96],grid=[2,2],crop=crop,frames=rows),indent=2)+'\n','utf8')
print(D)
