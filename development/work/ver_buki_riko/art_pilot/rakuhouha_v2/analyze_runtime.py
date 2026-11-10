from pathlib import Path
import sys,json,struct,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.epsxe_state import framebuffer,match_sprite
from scripts.extract_zero import save_image
D=Path(__file__).parent;L=Path(json.loads((D/'runtime_layers_path.json').read_text())['output']);j=json.loads((L/'identification.local.json').read_text());B=Path(j['source_build']);arc=(B/'modified.arc').read_bytes();es=psx_arc(arc)
def ent(k):
 e=next(e for e in es if e['type']==k);return arc[e['offset']:e['offset']+e['size']]
gfx=ent('0x2');parts=ent('0x3');pal=ent('0x9')[:32];tex=ent('0x10206');bank=graphics_bank(gfx,1);body={};screens={};samples={};raws={}
for i,r in enumerate(j['rows']):
 raw=(L/f'vram_{i:02d}.bin').read_bytes();raws[i]=raw;screens[i]=[framebuffer(raw,0,p) for p in (0,256)];samples.setdefault(r['frame'],[]).append(i)
for n in range(177,190):
 f=bank['frames'][n];expected=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;data,size,b,_=compose_indices(expected,f['tile_count'],composition_frame(parts,5,n));im=save_image(data,size,struct.unpack('<16H',pal),L/f'expected_body_{n}.png');passed=[];hits=[]
 for i in samples.get(n,[]):
  v=raws[i];actual=bytearray()
  for first in range(0,f['tile_count'],16):
   width=min(f['tile_count']-first,16)*8
   for y in range(16):
    pos=(first//16*16+y)*2048+640;actual+=v[pos:pos+width]
  if bytes(actual)==expected and v[480*2048:480*2048+32]==pal:passed.append(i)
 near=sorted({k for i in samples.get(n,[]) for k in (i,i+1) if k in screens})
 for i in near:
  for page,screen in zip((0,256),screens[i]):
   for hit in match_sprite(screen,im):hits.append({'snapshot':i,'page':page,**hit})
 body[str(n)]={'observed':n in samples,'vram_palette_matching_snapshots':passed,'screen_matches':hits}
fx={}
for n in (23,24):
 expected=Image.open(D/f'effect_{n}.png').convert('RGBA');old=Image.open(D/f'original_effect_{n}.png').convert('RGBA');seen=[];vram=[];new_hits=[];old_hits=[]
 for i,r in enumerate(j['rows']):
  if any(o['id']==3 and o['subtype']==13 and o['frame']==n for o in r['visuals']):seen.append(i)
 isolated=Image.open(L/f'isolated_3_{n}.png').convert('RGBA');assert np.array_equal(np.array(isolated),np.array(expected))
 for i in sorted({k for i in seen for k in range(max(0,i-1),min(len(j['rows']),i+4))}):
  for page,screen in zip((0,256),screens[i]):
   for hit in match_sprite(screen,expected):new_hits.append({'snapshot':i,'page':page,**hit})
   for hit in match_sprite(screen,old):old_hits.append({'snapshot':i,'page':page,**hit})
 fx[str(n)]={'observed_snapshots':seen,'isolated_vram_pixels_equal':True,'new_screen_matches':new_hits,'old_zero_screen_matches':old_hits}
report={'build':str(B),'bin_sha256':j['bin_sha256'],'runtime':str(L),'body':body,'embedded_effects':fx,'process_memory_written':False,'input_plan':'identify_input_plan.json','source_user_report':'Zero body remains inside Rakuhouha'}
(D/'runtime_summary.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps({'bodies_vram':[n for n,r in body.items() if r['vram_palette_matching_snapshots']],'bodies_screen':[n for n,r in body.items() if r['screen_matches']],'effects':fx}))
board=Image.new('RGB',(960,620),(32,36,48));d=ImageDraw.Draw(board)
for col,n in enumerate((23,24)):
 hits=fx[str(n)]['new_screen_matches'];i=hits[0]['snapshot'] if hits else fx[str(n)]['observed_snapshots'][-1]+1;page=hits[0]['page'] if hits else 0;im=screens[i][int(page==256)];im.save(D/f'actual_effect_{n}.png');crop=im.crop((40,130,180,230)).resize((420,300),Image.Resampling.NEAREST);board.paste(crop,(col*480,30));d.text((col*480+10,10),f'ACTUAL GAME - effect {n}',fill='white')
 im=Image.open(D/f'original_effect_{n}.png').convert('RGBA');im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);board.paste(im,(col*480+10,360),im);d.text((col*480+10,340),'ORIGINAL EFFECT - ZERO INSIDE',fill='white')
board.save(D/'actual_fix_review.png')
