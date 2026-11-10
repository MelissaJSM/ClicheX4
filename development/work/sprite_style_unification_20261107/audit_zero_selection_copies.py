"""Read-only compare Zero character-select copies with current player art."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,SELECTION_MAPPING,actual_frame
from scripts.prepare_rin_ui_small import world
from scripts.build_sprite_style_album import selection_image,zero_image,zero_palettes
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition
W=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
results=[]
for mode,char in [('br','riko'),('rn','rin')]:
 plan=json.loads((W/f'staging_{mode}_v12.json').read_text('utf8'))
 source=ROOT/plan['source_bin'];assert sha(source.read_bytes())==plan['source_sha256']
 assets=read_disc(source,('PL01_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0]
 for name in list(assets):
  if name in plan['resources']:
   q=plan['resources'][name];b=(ROOT/q['path']).read_bytes();assert sha(b)==q['after'];assets[name]=b
 if char=='rin':
  b=(W/'zero_audit/rin_extension/prepared_bank1_recovery128/PL01_U.ARC').read_bytes()
  assert sha(b)=='07ec6077969f17d08c51ffd8e4326b476e1c6ab5635bea8420faee9528b39a89';assets['PL01_U.ARC']=b
 out=W/'selection_sync_audit01'/char;assert not out.exists() or not any(out.iterdir());out.mkdir(parents=True,exist_ok=True)
 texture=entry(assets['ST0E_U1.ARC'],0x10102)[:40960];parts=entry(assets['ST0E_U1.ARC'],10)
 pal=zero_palettes(assets['PL01_U.ARC'])
 rows=[];images=[]
 for n,(bank,ref) in SELECTION_MAPPING.items():
  old=world(compose_static(texture,local_composition(composition_frame(parts,0,n))))
  new=world(actual_frame({'built_arc':assets['PL01_U.ARC']},bank,ref))
  ui=selection_image(assets,{'bank':0,'ref':n})
  body=zero_image(assets['PL01_U.ARC'],char,{'id':f'{char}:normal:b{bank}_{ref:03d}','bank':bank,'ref':ref,'form':'normal'},pal)
  a,b=np.array(ui),np.array(body)
  row={'ui_ref':n,'body_bank':bank,'body_ref':ref,'index_world_exact':old==new,'rgba_exact':bool(np.array_equal(a,b)),'rgba_changed_pixels':int(np.any(a!=b,axis=2).sum())}
  rows.append(row)
  if not row['rgba_exact']:images.append((row,ui,body))
 pages=[]
 for start in range(0,len(images),4):
  sample=images[start:start+4];board=Image.new('RGB',(960,len(sample)*354),'#384553');d=ImageDraw.Draw(board)
  for j,(row,ui,body) in enumerate(sample):
   for c,im in enumerate((ui,body)):
    pic=im.crop((80,90,240,200)).resize((480,330),Image.Resampling.NEAREST)
    board.paste(pic,(c*480,j*354+24),pic)
   d.text((5,j*354+5),f"select {row['ui_ref']} current | body {row['body_bank']}:{row['body_ref']} latest",fill='white')
  p=out/f'comparison_{start//4:02}.png';board.save(p);pages.append(p.relative_to(ROOT).as_posix())
 report={'character':char,'source_bin':plan['source_bin'],'source_sha256':plan['source_sha256'],'asset_hashes':{k:sha(v)for k,v in assets.items()},'selection_normal_palette_matches_player':entry(assets['COL0E_U1.ARC'],5)[:32]==entry(assets['PL01_U.ARC'],9)[:32],'mapping_source':'scripts/prepare_riko_ui.py::SELECTION_MAPPING','rows':rows,'mismatched':sum(not r['rgba_exact']for r in rows),'comparisons':pages,'game_data_modified':False,'runtime_verified':False,'root_images_viewed':False}
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 results.append({'character':char,'mapped':len(rows),'mismatched':report['mismatched'],'pages':len(pages)})
print(json.dumps(results))
