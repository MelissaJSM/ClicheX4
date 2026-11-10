import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from scripts.prepare_shibuki_run import world_canvas
from scripts.extract_zero import save_image
d=Path(__file__).parent
parent=ROOT/'out/ver_buki_riko/shibuki_run_20261026T082418920727Z'
arc=(parent/'modified.arc').read_bytes();es=psx_arc(arc)
def entry(t):
 e=next(e for e in es if int(e['type'],16)==t);return arc[e['offset']:e['offset']+e['size']]
gfx,parts=entry(2),entry(3);bank=graphics_bank(gfx,0,allow_bank_aliases=True)
words=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/idle_chubby_v2/candidate09/candidate.json').read_text())['palette_words']
sheet=Image.new('RGB',(5*256,2*320),'#222630');draw=ImageDraw.Draw(sheet)
for i,n in enumerate((0,85,86,87,92)):
 desc=bank['frames'][n];raw=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128).data
 arr=world_canvas(raw,desc['tile_count'],composition_frame(parts,0,n));save_image(arr.tobytes(),(96,80),words,d/f'parent_{n:03d}.png')
 orig=Image.open(ROOT/f'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/base_{n:03d}.png').convert('RGBA')
 p=orig.resize((orig.width*4,orig.height*4),Image.Resampling.NEAREST)
 sheet.paste(p,(i*256+20,40),p);draw.text((i*256+12,12),f'Original X {n}',fill='white')
 p=Image.open(d/f'parent_{n:03d}.png').convert('RGBA').resize((384,320),Image.Resampling.NEAREST)
 sheet.paste(p,(i*256-64,320),p)
sheet.save(d/'original_reference.png')
for fn in ('current_build.json','shibuki_current_build.json'):
 p=ROOT/'projects/ver_buki_riko'/fn;o=json.loads(p.read_text(encoding='utf-8'))
 (d/('accepted_previous_'+fn)).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
 o.update(current_movement_style_accepted=True,user_style_accepted=True,new_animation_user_review_pending=False,movement_acceptance_quote='좋아 이 분위기로 이어서 작업하자')
 p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
print(d/'original_reference.png')
