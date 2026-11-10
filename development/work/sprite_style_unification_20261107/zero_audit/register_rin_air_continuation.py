"""Register authored same-angle precise head on new connected airborne poses."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
SRC=D/'rin_extension/air_continuation01';OUT=D/'rin_extension/air_continuation_registered_v2';OUT.mkdir(exist_ok=True)
mp=ROOT/'work/sprite_style_unification_20261107/rin/locomotion01/native/b0_008_indices.png';master=np.array(Image.open(mp))
master[152,144]=0 # left glove at run8 is outside the semantic head
arc=(D/'rin_extension/prepared_air_wall_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));rows=[];targets={}
roi=np.zeros_like(master,bool);roi[140:148,144:168]=True;roi[148:153,144:162]=True;roi[153:154,147:157]=True
for n,dx,dy in [(22,6,-4),(24,5,-8),(25,5,-6),(26,5,-10)]:
    path=SRC/f'native/b0_{n:03d}_indices.png';new=np.array(Image.open(path));old=render(arc,0,0,n)[0]
    mask=np.roll(np.roll(roi,dx,axis=1),dy,axis=0);shifted=np.roll(np.roll(master,dx,axis=1),dy,axis=0)
    target=new.copy();target[mask]=shifted[mask]
    assert np.array_equal(target[~mask],new[~mask]);assert np.array_equal(target[mask],shifted[mask])
    targets[n]=target;Image.fromarray(target).save(OUT/f'b0_{n:03d}_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(OUT/f'b0_{n:03d}_head_roi.png')
    feet=[]
    for x0,x1 in [(130,163),(163,190)]:
        record=[]
        for v in (old,target):
            yy,xx=np.where(v[163:192,x0:x1]>0);yy+=163;xx+=x0;last=yy.max();xs=xx[yy>=last-1];record.append([int(xs.min()),int(last),int(xs.max())])
        assert record[0][1]==record[1][1] and max(abs(record[0][i]-record[1][i])for i in (0,2))<=1
        feet.append(record)
    rows.append({'ref':n,'head_translation':[dx,dy],'head_opaque_pixels':int(np.count_nonzero(master[roi])),'negative_space_exact':True,'new_body_outside_head_exact':True,'source_native':str(path.relative_to(ROOT)),'source_native_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'target_sha256':hashlib.sha256((OUT/f'b0_{n:03d}_indices.png').read_bytes()).hexdigest(),'feet_last_two_rows_before_after':feet})
for name,row in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),row*32);sheet=Image.new('RGB',(1200,428*4),'#64717b');draw=ImageDraw.Draw(sheet)
    for iy,(n,target)in enumerate(targets.items()):
        for ix,(title,a)in enumerate([('previous',render(arc,0,0,n)[0]),('new source',np.array(Image.open(SRC/f'native/b0_{n:03d}_indices.png'))),('same-angle precise head',target)]):
            pic=rgba(a,pal).crop((120,120,200,200)).resize((400,400),Image.Resampling.NEAREST);sheet.paste(pic,(ix*400,iy*428+28),pic);draw.text((ix*400+4,iy*428+5),f'{n} {title}',fill='white')
    sheet.save(OUT/f'{name}_comparison.png')
(OUT/'registration.json').write_text(json.dumps({'master':str(mp.relative_to(ROOT)),'master_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'generated_sha256':hashlib.sha256((SRC/'generated.png').read_bytes()).hexdigest(),'frames':rows,'game_changed':False,'runtime_verified':False},indent=2)+'\n','utf8')
print(json.dumps(rows))
