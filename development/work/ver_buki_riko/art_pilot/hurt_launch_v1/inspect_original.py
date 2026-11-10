"""Inspect indices only; this sheet is NOT an accurate multi-CLUT preview."""
import json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.repack_zero import read_inputs
from src.psx_player import graphics_bank, composition_frame, decode_stream, compose_indices
from scripts.extract_zero import save_image
from PIL import Image,ImageDraw
D=Path(__file__).parent
E=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
_,_,arc,gm,gfx,parts,words=read_inputs(E)
bank=graphics_bank(gfx,0)
board=Image.new('RGBA',(8*256,300),(32,36,48));dr=ImageDraw.Draw(board);audit=[]
for i,n in enumerate([135,*range(139,146)]):
 f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 cc={**c,'parts':[{**p,'clut':0,'flags':p['flags']&~12} for p in c['parts']]}
 ix,sz,b,_=compose_indices(raw,f['tile_count'],cc);im=save_image(ix,sz,words,D/f'original_{n:03d}_index_layout_only.png')
 cell=Image.new('RGBA',(64,70));cell.alpha_composite(im.convert('RGBA'),(32+b[0],35+b[1]));board.alpha_composite(cell.resize((256,280),Image.Resampling.NEAREST),(i*256,20));dr.text((i*256+3,3),f'{n} INDEX LAYOUT ONLY',fill='white')
 audit.append({'frame':n,'stream':f,'parts':c['parts'],'index_values':sorted(set(ix)),'bounds':b})
board.save(D/'original_index_layout_only.png');(D/'input_audit.json').write_text(json.dumps(audit,indent=2),'utf8')
v=ROOT/'work/ver_buki_riko/hurt_runtime/20261024T083240245441Z/vram_135.bin'
if v.exists():
 data=v.read_bytes();print('Runtime palette rows y480',[[hex(x) for x in struct.unpack_from('<16H',data,480*2048+j*32)] for j in range(4)])
d=json.loads((ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z/inventory.json').read_text());print('inventory keys',list(d))
for a in d.get('animations',[]):
 if a.get('id',a.get('animation_id')) in range(33,38):print(a)
print('Board',D/'original_index_layout_only.png')
