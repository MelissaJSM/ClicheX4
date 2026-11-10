"""Prepare fixed-origin, unlabeled four-pose continuation inputs; no new art."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'rin_extension/run_inputs';OUT.mkdir(exist_ok=True)
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
def sha(b):return hashlib.sha256(b).hexdigest()
source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';expected='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720';assert sha(source.read_bytes())==expected
arc=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,128,208,192);cw,ch=96,64;scale=8;worlds={n:render(arc,0,0,n)[0]for n in [147,*range(7,21),3,4]};art=ROOT/'work/sprite_style_unification_20261107/rin/locomotion01/native'
for n in (8,14):worlds[n]=np.array(Image.open(art/f'b0_{n:03d}_indices.png'))
groups=[[7,9,10,11],[12,13,15,16],[17,18,19,20]];meta=[]
for i,ns in enumerate(groups,1):
 folder=OUT/f'run{i:02d}';folder.mkdir(exist_ok=True);sheet=Image.new('RGBA',(cw*2,ch*2));records=[]
 for k,n in enumerate(ns):
  a=worlds[n];pic=rgba(a,pal);cut=pic.crop(crop);assert np.count_nonzero(np.array(cut.getchannel('A')))==np.count_nonzero(a)
  x,y=k%2,k//2;sheet.alpha_composite(cut,(x*cw,y*ch));pic.save(folder/f'b0_{n:03d}_native.png');Image.fromarray(a).save(folder/f'b0_{n:03d}_indices.png');records.append({'key':f'b0_{n:03d}','bank':0,'ref':n,'cell':[x,y],'bounds':pic.getbbox()})
 sheet.resize((cw*2*scale,ch*2*scale),Image.Resampling.NEAREST).save(folder/'input.png');info={'source_bin':str(source.relative_to(ROOT)),'source_sha256':expected,'archive_sha256':sha(arc),'character':'rin','crop':crop,'native_cell':[cw,ch],'columns':2,'rows':2,'scale':scale,'palette_words':list(pal),'frames':records,'origin':[160,160],'already_redrawn_cycle_refs':[8,14],'keep_timing_and_foot_anchors':True,'old_head_override':False};(folder/'inputs.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n','utf8');meta.append(str(folder.relative_to(ROOT)))
style=Image.new('RGBA',(cw*2,ch*2))
for k,n in enumerate((147,8,14,95)):
 a=worlds[n]if n!=95 else np.array(Image.open(art/'b0_095_indices.png'));style.alpha_composite(rgba(a,pal).crop(crop),(k%2*cw,k//2*ch))
style.resize((1536,1024),Image.Resampling.NEAREST).save(OUT/'accepted_style_8x.png')
cycle=Image.new('RGB',(384*4,280*4),'#64717b');draw=ImageDraw.Draw(cycle)
for k,n in enumerate(range(7,21)):
 pic=rgba(worlds[n],pal).crop(crop).resize((384,256),Image.Resampling.NEAREST);x=k%4*384;y=k//4*280;cycle.paste(pic,(x,y+24),pic);draw.text((x+5,y+5),str(n)+(' accepted new'if n in(8,14)else' pending redraw'),fill='white')
cycle.save(OUT/'cycle_reference.png');(OUT/'manifest.json').write_text(json.dumps({'pages':meta,'new_generation_needed_refs':sum(groups,[]),'existing_new_keys':[8,14],'native_cell':[cw,ch],'crop':crop,'scale':scale,'source_bin_sha256':expected,'fixed_world_origin':[160,160],'generation_not_performed':True},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'pages':meta,'refs':sum(groups,[])}))
