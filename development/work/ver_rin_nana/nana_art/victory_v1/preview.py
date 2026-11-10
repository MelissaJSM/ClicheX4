import json,sys,struct
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.extract_zero import save_image
B=ROOT/'out/ver_rin_nana/nana_victory_20261030T002449610350Z';arc=(B/'modified.arc').read_bytes();es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True);pal=list(struct.unpack('<16H',es[9][:32]));plan=json.loads((ROOT/'work/ver_rin_nana/nana_art/victory_v1/plan.json').read_text());frames=plan['frames']
for n in(0,81):
 f=bank['frames'][n];raw=decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data;v=canvas_from_parts(raw,f['tile_count'],composition_frame(es[3],0,n));save_image(v.tobytes(),(160,160),pal,B/'art'/f'context_{n:03d}.png')
board=Image.new('RGB',(800,352),'#222630');dr=ImageDraw.Draw(board)
for i,n in enumerate(frames):
 im=Image.open(B/'art'/f'frame_{n:03d}.png').convert('RGBA');x,y=i%5*160,i//5*176;board.paste(im,(x,y+16),im);dr.text((x+3,y+2),str(n),fill='white')
board.save(B/'final_review_1x.png');board.resize((1600,704),Image.Resampling.NEAREST).save(B/'final_review_2x.png')
for aid,name in((39,'victory'),(3,'return')):
 ims=[];times=[]
 for step in plan['animations'][str(aid)]['steps']:
  n=step['frame'];im=Image.open(B/'art'/('%s_%03d.png'%('context'if n==81 else'frame',n))).convert('RGBA');pic=Image.new('RGB',(160,160),'#222630');pic.paste(im,(0,0),im);ims.append(pic.resize((480,480),Image.Resampling.NEAREST));times.append(round(step['duration_ticks']*1000/60))
 ims[0].save(B/(name+'_preview.gif'),save_all=True,append_images=ims[1:],duration=times,loop=0)
(B/'preview_notes.json').write_text(json.dumps({'evidence_kind':'offline reconstruction; event branches and world motion not simulated','steps':plan['animations']},indent=2),'utf8');print('Saved review and two reconstruction GIFs')
