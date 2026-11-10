"""새 질풍아 원화를 원 발바닥에 전신 평행이동하여 접점을 검토한다."""
from pathlib import Path
import argparse,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,choices=(1,2),default=1);args=ap.parse_args()
D=Path(__file__).parent/'rin_extension'/f'dash_saber_followup{args.page:02}';O=D/'anchor_probe';assert not O.exists();O.mkdir()
info=json.loads((D/'inputs.json').read_text('utf8'));src=ROOT/info['actual_input_arc'];arc=src.read_bytes();assert hashlib.sha256(arc).hexdigest()==info['archive_sha256']
pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32)
shifts={158:(0,-4),160:(0,-4),162:(0,2),164:(0,1)} if args.page==1 else {166:(0,-3),168:(0,-2),170:(3,-1),172:(2,-1)}
rows=[];items={k:[] for k in('normal','black')};font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
for f in info['frames']:
 key=f['key'];ref=f['ref'];old=render(arc,0,0,ref)[0];a=np.array(Image.open(D/'native_fixed'/(key+'_indices.png')));dx,dy=shifts[ref];v=np.roll(np.roll(a,dy,axis=0),dx,axis=1)
 assert np.count_nonzero(v)==np.count_nonzero(a);Image.fromarray(v).save(O/(key+'_indices.png'))
 for name,words in [('normal',pal),('black',black)]:items[name].extend([(key+' original',rgba(old,words)),(key+f' shift {dx:+},{dy:+}',rgba(v,words))])
 bounds=(120,128,200,190);scale=12;board=Image.new('RGB',(80*scale*2,62*scale+24),(27,33,43));draw=ImageDraw.Draw(board)
 for j,(label,b) in enumerate([('old',old),('new',v)]):
  pic=rgba(b,pal).crop(bounds).resize((80*scale,62*scale),Image.Resampling.NEAREST);board.paste(pic,(j*960,24),pic);draw.text((j*960+4,4),key+' '+label,font=font,fill='white')
  for x in range(120,201,5):q=j*960+(x-120)*scale;draw.line((q,24,q,board.height),fill=(55,61,71));draw.text((q+1,25),str(x),font=font,fill=(230,180,130))
  for y in range(130,191,5):q=24+(y-128)*scale;draw.line((j*960,q,(j+1)*960,q),fill=(55,61,71));draw.text((j*960+1,q+1),str(y),font=font,fill=(230,180,130))
 board.save(O/(key+'_grid.png'))
 rows.append({'key':key,'translation':[dx,dy],'old_bbox':rgba(old,pal).getbbox(),'new_bbox':rgba(v,pal).getbbox(),'old_floor':int(np.nonzero(old)[0].max()),'new_floor':int(np.nonzero(v)[0].max()),'old_cyan':np.argwhere(old==15)[:,::-1].tolist(),'new_cyan':np.argwhere(v==15)[:,::-1].tolist()})
for name,words in [('normal',pal),('black',black)]:page(items[name],rgba(render(arc,0,0,147)[0],words),O/(name+'_comparison.png'),cols=2,scale=5)
(O/'registration.json').write_text(json.dumps({'records':rows,'scope':'전신 정수 평행이동 후보. 아트/게임 원점/타이밍 미변경.'},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
