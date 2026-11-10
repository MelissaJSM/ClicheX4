"""All436 standalone references, exact translated-shape groups, normal+black boards."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;O=D/'rin_extension/all_unique_review303';O.mkdir(exist_ok=True)
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank
source=D/'rin_extension/prepared_burst_remaining02/PL01_U.ARC';arc=source.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
groups=json.loads((D/'group_map.json').read_text('utf8'))['rin'];pal=list(struct.unpack_from('<64H',entry(arc,9)));hist=(ROOT/'out/sprite_consistency_20261105/rin/normal/preview_palettes.bin').read_bytes();historical=struct.unpack('<64H',hist);assert pal[:16]==list(historical[:16]);pal[16:]=historical[16:]
rows={};unique={};partial=[]
for b in(0,1):
 for f in graphics_bank(entry(arc,2),b)['frames']:
  n=f['index'];key=f'b{b}_{n:03}'
  if b==1 and 42<=n<=49:partial.append(key);continue
  a=render(arc,b,b*5,n)[0];y,x=np.nonzero(a%16);bb=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]if len(x)else None
  cropped=a[bb[1]:bb[3],bb[0]:bb[2]]if bb else a[:0,:0];k=sha(cropped.tobytes()+str(cropped.shape).encode());unique.setdefault(k,[]).append(key)
  memberships=[{'group':g,'provisional_kind':'body_or_head'if key in v['body_or_head_refs']else'effect_or_blank'}for g,v in groups.items()if key in v['body_or_head_refs']or key in v['effect_or_blank_refs']]
  rows[key]={'bank':b,'ref':n,'bbox':bb,'pixels':len(x),'max_index':int(a.max()),'exact_shape_hash':k,'provisional_groups':memberships};np.save(O/(key+'.npy'),a)
assert len(rows)==436 and len(partial)==8
boxes=[v['bbox']for v in rows.values()if v['bbox']];scale=4;grouped=list(unique.values());pages=[]
for start in range(0,len(grouped),11):
 selected=grouped[start:start+11];items=[['b0_147']]+selected
 pageboxes=[rows[v[0]]['bbox']for v in items if rows[v[0]]['bbox']];crop=[min(v[0]for v in pageboxes)-3,min(v[1]for v in pageboxes)-3,max(v[2]for v in pageboxes)+3,max(v[3]for v in pageboxes)+3];cw,ch=crop[2]-crop[0],crop[3]-crop[1];cellw=cw*scale+16;cellh=ch*scale+32
 for variant in('normal','black'):
  words=pal.copy()
  if variant=='black':words[:16]=struct.unpack_from('<16H',entry(arc,9),13*32)
  sheet=Image.new('RGB',(cellw*4,cellh*((len(items)+3)//4)),'#3e4956');draw=ImageDraw.Draw(sheet)
  for j,aliases in enumerate(items):
   key=aliases[0];a=np.load(O/(key+'.npy'));x=j%4*cellw;y=j//4*cellh;label=('IDLE147'if j==0 else key)+(' +'+str(len(aliases)-1)if len(aliases)>1 else'');draw.text((x+4,y+5),label,fill='white');pic=rgba(a,words).crop(crop).resize((cw*scale,ch*scale),Image.Resampling.NEAREST);sheet.paste(pic,(x+8,y+28),pic)
  name=f'{variant}_{start//11:02}.png';sheet.save(O/name)
  pages.append({'file':name,'variant':variant,'fixed_crop_for_every_cell_on_page':crop,'world_origin':[160,160],'groups':[{'representative':v[0],'aliases':v,'metadata':rows[v[0]]}for v in selected],'viewed':False})
result={'source':str(source.relative_to(ROOT)),'source_sha256':sha(arc),'standalone_display_refs':436,'partial8':partial,'shape_groups':len(grouped),'world_origin':[160,160],'crop_rule':'각 페이지 내 모든 칸은 동일한 월드crop. 원점/정수4배 유지, 포즈별 확대축소/센터정렬 없음.','scale':scale,'pages':pages,'references':rows,'palette_scope':'0/13은 현재몸체. 나머지3 CLUT는 역사캡처 프리뷰로 현재실기색 증거가 아니다.','all_visually_reviewed':False,'full_art_unification_complete':False}
(O/'inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'display':436,'groups':len(grouped),'normal_pages':len(pages)//2,'crop':crop,'sheet_size':[cellw*4,cellh*3]}))
