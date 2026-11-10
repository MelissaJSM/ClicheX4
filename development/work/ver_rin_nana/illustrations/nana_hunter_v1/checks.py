"""헌터베이스 보조 CLUT·다른 자원·표정 이동의 잘못된 입력을 거부한다."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_hunter import ART,sources,verify,entry,replace_entry,aliased_composition
from scripts.build_nana_hunter import validate
art=ART/'native03';repro=ART/'repro03';m,records,original=sources();new={n:(art/n).read_bytes()for n in original};world={n:np.array(Image.open(art/f'world_{n:02}.png'))for n in range(12)};results=[]
def reject(label,fn):
 try:fn()
 except ValueError as e:results.append({'case':label,'rejected':True,'reason':str(e)})
 else:raise AssertionError(label)
def change(n,e,pos):
 d=new.copy();a=bytearray(entry(d[n],e));a[pos]^=1;d[n]=replace_entry(d[n],e,bytes(a));return d
for name,n,e,pos in [('other_texture','ST0D_0X.ARC',0x10102,0),('next_texture','ST0D_0X.ARC',0x10102,75776),('other_palette','COL0D_0X.ARC',5,36*32+2),('animation_header','ST0D_0X.ARC',10,0)]:reject(name,lambda n=n,e=e,pos=pos:verify(original,change(n,e,pos),world))
p=entry(new['ST0D_0X.ARC'],10)
for n in [0,4,7,9]:
 d=new.copy();a=bytearray(p);off=aliased_composition(p,2,n)['parts'][0]['record_offset'];a[off]|=4;d['ST0D_0X.ARC']=replace_entry(d['ST0D_0X.ARC'],10,bytes(a));reject('auxiliary_clut_'+str(n),lambda d=d:verify(original,d,world))
off=aliased_composition(p,0,0)['parts'][0]['record_offset']+2;reject('other_character_parts',lambda:verify(original,change('ST0D_0X.ARC',10,off),world))
w={n:a.copy()for n,a in world.items()};w[2][80,128]^=1;reject('blink_body_drift',lambda:verify(original,new,w))
w={n:a.copy()for n,a in world.items()};w[9]=np.roll(w[9],1,axis=1);reject('departure_anchor_drift',lambda:verify(original,new,w))
reject('different_preparation',lambda:validate(ART/'native01',repro));reject('wrong_art_folder',lambda:validate(ROOT/'out',repro));validate(art,repro)
(ART/'checks.json').write_text(json.dumps({'passed':len(results),'negative_checks':results,'valid_recipe_verified':True,'disk_writes':False},indent=2)+'\n','utf8');print(json.dumps({'passed':len(results)}))
