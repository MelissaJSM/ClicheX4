"""Prepare four authored-character-only cells for a continuation art page."""
from pathlib import Path
import sys,json,struct,hashlib,argparse
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('refs',nargs=4,type=int);p.add_argument('--top',type=int,default=128);p.add_argument('--width',type=int,default=96);a=p.parse_args()
OUT=D/'rin_extension'/a.name;assert not OUT.exists();OUT.mkdir()
source=D/'rin_extension/prepared_air_continuation_v1/PL01_U.ARC';arc=source.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();pal=struct.unpack_from('<16H',entry(arc,9));crop=(160-a.width//2,a.top,160+a.width//2,192);height=192-a.top;sheet=Image.new('RGBA',(a.width*2,height*2));frames=[]
for i,n in enumerate(a.refs):
    q=render(arc,0,0,n)[0];pic=rgba(q,pal);cut=pic.crop(crop);assert np.count_nonzero(np.array(cut.getchannel('A')))==np.count_nonzero(q),'Crop would clip pose'
    sheet.alpha_composite(cut,((i%2)*a.width,(i//2)*height));Image.fromarray(q).save(OUT/f'b0_{n:03d}_indices.png');pic.save(OUT/f'b0_{n:03d}_native.png')
    frames.append({'key':f'b0_{n:03d}','bank':0,'ref':n,'cell':[i%2,i//2],'bounds':pic.getbbox()})
sheet.resize((a.width*16,height*16),Image.Resampling.NEAREST).save(OUT/'input.png')
style=Image.new('RGBA',(288,80))
for i,n in enumerate((147,8,21)):
    style.alpha_composite(rgba(render(arc,0,0,n)[0],pal).crop((112,112,208,192)),(96*i,0))
style.resize((1728,480),Image.Resampling.NEAREST).save(OUT/'style.png')
(OUT/'inputs.json').write_text(json.dumps({'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','archive_sha256':sha(arc),'actual_input_arc':str(source.relative_to(ROOT)),'character':'rin','crop':crop,'native_cell':[a.width,height],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'frames':frames,'palette_words':list(pal),'game_changed':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(OUT)
