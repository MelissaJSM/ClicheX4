from pathlib import Path
import sys,json,struct,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from src.psx_player import composition_frame
D=Path(__file__).parent
L=Path(json.loads((D/'runtime_layers_path.json').read_text())['output'])
j=json.loads((L/'identification.local.json').read_text());arc=(Path(j['source_build'])/'modified.arc').read_bytes()
e=next(e for e in psx_arc(arc) if e['type']=='0x3');parts=arc[e['offset']:e['offset']+e['size']]
def render(raw,obj):
 comp=composition_frame(parts,6,obj['frame'])['parts']
 bounds=(min(p['x'] for p in comp),min(p['y'] for p in comp),max(p['x']+16 for p in comp),max(p['y']+16 for p in comp))
 im=np.zeros((bounds[3]-bounds[1],bounds[2]-bounds[0],4),dtype=np.uint8)
 for p in comp:
  tile=obj['texture_word']+p['page']*256+p['tile']
  if obj['active']&64:tile=(tile//176)*256+tile%176+0x600
  if obj['active']&32:tile=(tile//80)*256+tile%80+0x5b0
  page=tile>>8;tx=(page&15)*64+(tile&15)*4;ty=((page>>4)&1)*256+(tile&0xf0)
  clut=obj['clut_word']+p['clut']
  if clut&0x30:clut+=0x30
  words=struct.unpack_from('<16H',raw,((clut>>6)*1024+(clut&63)*16)*2)
  for y in range(16):
   for x in range(16):
    v=raw[(ty+y)*2048+tx*2+x//2];idx=(v>>(4*(x%2)))&15
    if not idx:continue
    w=words[idx];px=p['x']-bounds[0]+(15-x if p['flip_x'] else x);py=p['y']-bounds[1]+(15-y if p['flip_y'] else y)
    im[py,px]=[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255]
 return Image.fromarray(im),bounds
seen=set();imgs=[];records=[]
for i,r in enumerate(j['rows']):
 raw=(L/f'vram_{i:02d}.bin').read_bytes()
 for o in r['visuals']+r['weapons']:
  if o['exact_composition_banks']!=[6]:continue
  key=(o['id'],o['frame'])
  if key in seen:continue
  seen.add(key);im,bounds=render(raw,o);im.save(L/f'isolated_{key[0]}_{key[1]}.png');imgs.append((key,im));records.append({'key':key,'bounds':bounds,'snapshot':i,'object':o})
out=Image.new('RGB',(5*240,((len(imgs)+4)//5)*240),(35,40,50));d=ImageDraw.Draw(out)
for i,(key,im) in enumerate(imgs):
 x=i%5*240;y=i//5*240;im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);out.paste(im,(x+(240-im.width)//2,y+30),im);d.text((x+10,y+8),str(key),fill='white')
out.save(L/'isolated_effects_sheet.png');(L/'isolated_effects.json').write_text(json.dumps(records,indent=2),'utf8');print('effects',sorted(seen))
