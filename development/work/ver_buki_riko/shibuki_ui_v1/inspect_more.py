import sys,struct,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.inventory_shibuki_ui import *
from src.psx_player import graphics_bank,decode_stream,compose_indices,composition_frame
records,o,cur=load();items=[];meta=[]
def add(title,px,size,pal):
 im=save_image(px,size,struct.unpack('<16H',pal),D/'original'/f'{title}.png').convert('RGBA');items.append((title,im))
raw=o['PL00_U.ARC'];p=entry(raw,3);g=entry(raw,0x10206);pal=entry(o['COL00_0X.ARC'],5)
for b in range(struct.unpack_from('<I',p)[0]//4):
 for n in range(aliased_composition(p,b,0)['bank_frame_count']):
  if b in (0,5,6,7,8):continue
  try:
   c=aliased_composition(p,b,n);px,size,bounds,_=compose_static(g,local_composition(c))
   meta.append({'b':b,'n':n,'bounds':bounds,'size':size,'clut':sorted({v['clut'] for v in c['parts']})})
   if b==1:add(f'pl00_b{b}_f{n}',px,size,pal[64:96])
  except ValueError:pass
sheet(items,D/'static_inventory.png',10,(115,130));items=[]
(D/'static_inventory.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
p=struct.pack('<I',4)+entry(raw,0x12);g=entry(raw,0x10007);pal=entry(raw,0x11)
for n in range(aliased_composition(p,0,0)['bank_frame_count']):
 try:
  c=aliased_composition(p,0,n);px,size,bounds,_=compose_static(g[96*128:],local_composition(c));add(f'pause_{n}',px,size,pal[10*32:11*32])
  print('pause',n,size,bounds,len(c['parts']))
 except ValueError as ex:print('pause error',n,str(ex))
sheet(items,D/'pause_inventory.png',6,(140,130));items=[]
name='ST0D_0X.ARC';raw=o[name];g=entry(raw,0x10102);p=entry(raw,10);pal=entry(o['COL0D_0X.ARC'],5)
for n in range(12):
 c=aliased_composition(p,2,n);px,size,bounds,_=compose_static(g[63488:75776],local_composition(c));add(f'base_{n}',px,size,pal[35*32:36*32]);print('hq',n,size,bounds)
sheet(items,D/'hq_all.png',6,(150,140));items=[]
raw=o['ST0E_U1.ARC'];g=entry(raw,0x10102)[90112:];p=entry(raw,10);x=o['PL00_U.ARC'];gg=entry(x,2);pp=entry(x,3);frames=[]
for n in range(237):
 try:
  f=graphics_bank(gg,0,allow_bank_aliases=True)['frames'][n];dec=decode_stream(gg,f['offset'],f['limit'],f['tile_count']*128).data;fr=compose_indices(dec,f['tile_count'],composition_frame(pp,0,n));frames.append((n,fr[:3]))
 except ValueError:pass
def bboxframe(fr):
 px,size,b=fr;im=Image.frombytes('L',size,px);box=im.getbbox()
 return im.crop(box).tobytes(),im.crop(box).size if box else None
mapping={}
for n in range(25):
 c=aliased_composition(p,2,n);fr=compose_static(g,local_composition(c));matches=[j for j,v in frames if bboxframe(v)==bboxframe(fr[:3])];mapping[n]=matches
 add(f'select_x_{n}',fr[0],fr[1],entry(o['COL0E_U1.ARC'],5)[32:64])
sheet(items,D/'select_x_correct.png',6,(140,130));(D/'selection_mapping.json').write_text(json.dumps(mapping,indent=2),encoding='utf8');print('mapping',mapping)
for name in ('PL00_U.ARC','PL01_U.ARC'):
 raw=cur[name];text=entry(raw,21);from src.psx_text import message_ranges,ALPHABET
 matches=[];lines=[]
 for mi,(a,b) in enumerate(message_ranges(text)):
  w=struct.unpack('<'+'H'*((b-a)//2),text[a:b]);page=[]
  for v in w:
   ch=ALPHABET[(v&511)-64] if 64<=v&511<126 else ' ' if v&511==511 else '<%03x>'%(v&511)
   page.append(ch)
   if v&0x4000:page.append('\n')
   if v&0xa000:
    s=''.join(page);lines.append(f'{mi}: '+s);matches.extend([(mi,s)] if 'X' in s or 'MEGAMAN' in s.upper() else []);page=[]
 (D/f'{name}_pages.txt').write_text('\n---\n'.join(lines),encoding='utf8');(D/f'{name}_name_pages.json').write_text(json.dumps(matches,indent=2),encoding='utf8')
 print(name,'pages with name',len(matches))
