"""Prepare separate next-batch art inputs without altering the frozen run ARC."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
OUT=D/'rin_extension/air_wall01';OUT.mkdir(exist_ok=True)
source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720'
arc=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,128,208,192);sheet=Image.new('RGBA',(192,128));rows=[]
for i,n in enumerate((21,27,35,39)):
    a=render(arc,0,0,n)[0];pic=rgba(a,pal);cut=pic.crop(crop);assert int(np.count_nonzero(np.array(cut.getchannel('A'))))==int(np.count_nonzero(a))
    sheet.alpha_composite(cut,((i%2)*96,(i//2)*64));key=f'b0_{n:03d}';pic.save(OUT/(key+'_native.png'));Image.fromarray(a).save(OUT/(key+'_indices.png'))
    rows.append({'key':key,'bank':0,'ref':n,'cell':[i%2,i//2],'bounds':pic.getbbox()})
sheet.resize((1536,1024),Image.Resampling.NEAREST).save(OUT/'input.png')
style=Image.new('RGBA',(192,64));style.alpha_composite(rgba(render(arc,0,0,147)[0],pal).crop(crop),(0,0));new=np.array(Image.open(ROOT/'work/sprite_style_unification_20261107/rin/locomotion01/native/b0_008_indices.png'));style.alpha_composite(rgba(new,pal).crop(crop),(96,0));style.resize((1536,512),Image.Resampling.NEAREST).save(OUT/'style.png')
(OUT/'inputs.json').write_text(json.dumps({'source_bin':str(source.relative_to(ROOT)),'source_sha256':sha(source),'archive_sha256':hashlib.sha256(arc).hexdigest(),'character':'rin','crop':crop,'native_cell':[96,64],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'frames':rows,'palette_words':list(pal),'game_changed':False,'separate_from_frozen_run_batch':True},ensure_ascii=False,indent=2)+'\n','utf8')
print(OUT)
