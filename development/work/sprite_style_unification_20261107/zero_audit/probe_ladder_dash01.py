"""고정 원화 셀의 눈 표본/전신 평행이동만 진단한다. 게임에는 쓰지 않는다."""
from pathlib import Path
import sys,json,hashlib,struct
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'ladder_dash01';O=A/'anchor_probe';assert not O.exists();O.mkdir()
info=json.loads((A/'inputs.json').read_text('utf8'));P=ROOT/info['actual_input_arc'];arc=P.read_bytes();pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)==info['archive_sha256']
assert sha(A/'generated.png')=='8b0421d987948cee062ceac6f545db0161647561f62d9978317859fb44b0b8cf'
im=np.array(Image.open(A/'generated.png').convert('RGBA'));cw=im.shape[1]//2
shifts={199:(3,-2),202:(4,-3),155:(1,7),156:(3,7)}
records=[];items={k:[]for k in('normal','black')};font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
for i,f in enumerate(info['frames']):
 key=f['key'];n=f['ref'];old=render(arc,0,0,n)[0];p=A/'native_fixed'/(key+'_indices.png');v=np.array(Image.open(p));src=im[(i//2)*cw:(i//2+1)*cw,(i%2)*cw:(i%2+1)*cw];r,g,b,a=np.moveaxis(src.astype(float),-1,0)
 yy,xx=np.where((r<g*.6)&(g>90)&(g/(b+1)>.6)&(g/(b+1)<1.15)&(a>=128));counts=Counter((112+int(x*96/cw),104+int(y*96/cw)) for x,y in zip(xx,yy));eye,ct=counts.most_common(1)[0];ex,ey=eye
 assert ct>=15 and v[ey,ex]>0
 eye_change=[]
 if n in(199,156):
  eye_change=[{'point':list(eye),'old_index':int(v[ey,ex]),'new_index':15,'cyan_source_sample_count':ct}];v[ey,ex]=15
 dx,dy=shifts[n];z=np.roll(np.roll(v,dy,axis=0),dx,axis=1);assert int(np.count_nonzero(z))==int(np.count_nonzero(v));Image.fromarray(z).save(O/(key+'_indices.png'))
 for form,words in [('normal',pal),('black',black)]:items[form].extend([(key+' old',rgba(old,words)),(key+f' translated {dx:+},{dy:+}',rgba(z,words))])
 bounds=(120,120,205,190);scale=12;board=Image.new('RGB',((bounds[2]-bounds[0])*scale*2,(bounds[3]-bounds[1])*scale+26),(27,33,43));d=ImageDraw.Draw(board)
 for j,(label,arr) in enumerate([('old',old),('translated',z)]):
  pic=rgba(arr,pal).crop(bounds).resize(((bounds[2]-bounds[0])*scale,(bounds[3]-bounds[1])*scale),Image.Resampling.NEAREST);board.paste(pic,(j*pic.width,26),pic);d.text((j*pic.width+3,3),key+' '+label,fill='white',font=font)
  for x in range(125,205,5):q=j*pic.width+(x-bounds[0])*scale;d.line((q,26,q,board.height),fill=(55,61,71));d.text((q+1,28),str(x),fill=(210,170,120),font=font)
  for y in range(125,190,5):q=26+(y-bounds[1])*scale;d.line((j*pic.width,q,(j+1)*pic.width,q),fill=(55,61,71));d.text((j*pic.width+1,q+1),str(y),fill=(210,170,120),font=font)
 board.save(O/(key+'_grid.png'))
 records.append({'key':key,'source_native_sha256':sha(p),'translation':[dx,dy],'cyan_eye_registration':eye_change,'source_eye_sample':list(eye),'registered_eye_sample':[ex+dx,ey+dy],'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'old_floor':int(np.nonzero(old)[0].max()),'new_floor':int(np.nonzero(z)[0].max()),'output_sha256':sha(O/(key+'_indices.png'))})
for form,words in [('normal',pal),('black',black)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/(form+'_comparison.png'),cols=2,scale=5)
(O/'registration.json').write_text(json.dumps({'source_art_sha256':sha(A/'generated.png'),'records':records,'candidate_only':True,'part_or_game_coordinates_changed':False,'wholebody_scale':False,'invented_art':False,'old_head_override':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(records))
