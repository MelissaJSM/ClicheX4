from pathlib import Path
import json,struct,sys
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path.cwd()))
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.extract_zero import save_image
B=Path('out/ver_rin_nana/nana_special_20261030T004646283984Z');arc=(B/'modified.arc').read_bytes();es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True);pal=list(struct.unpack('<48H',es[9][:96]));plan=json.loads(Path('work/ver_rin_nana/nana_art/special_v1/plan.json').read_text());images={}
ns=sorted(set([0,81,85,86,87,92]+plan['frames']))
for n in ns:
 f=bank['frames'][n];v=canvas_from_parts(decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'],composition_frame(es[3],0,n));save_image(v.tobytes(),(160,160),pal,B/'art'/f'preview_full_{n:03d}.png');images[n]=Image.open(B/'art'/f'preview_full_{n:03d}.png').convert('RGBA')
for aid,name in((91,'charge'),(104,'cyclone')):
 ims=[];times=[]
 for step in plan['animations'][str(aid)]['steps']:
  pic=Image.new('RGB',(160,160),'#222630');im=images[step['frame']];pic.paste(im,(0,0),im);ims.append(pic.resize((480,480),Image.Resampling.NEAREST));times.append(round(step['duration_ticks']*1000/60))
 ims[0].save(B/(name+'_preview.gif'),save_all=True,append_images=ims[1:],duration=times,loop=0)
board=Image.new('RGB',(800,352),'#222630');dr=ImageDraw.Draw(board)
for i,n in enumerate([0,85,88,89,90,91,97,81,98,99]):
 x,y=i%5*160,i//5*176;board.paste(images[n],(x,y+16),images[n]);dr.text((x+3,y+2),str(n),fill='white')
board.save(B/'final_review_1x.png');board.resize((1600,704),Image.Resampling.NEAREST).save(B/'final_review_2x.png')
(B/'preview_notes.json').write_text(json.dumps({'evidence_kind':'offline reconstruction; event branches and world movement not simulated','timing':plan['animations'],'frame88_trail_shares_body_clut0_and_retains_parent_index_pixels':True},indent=2),'utf8');print('saved full-color previews')
