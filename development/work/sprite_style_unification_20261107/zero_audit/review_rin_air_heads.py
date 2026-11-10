"""Separate same-angle authored head registration from the frozen native ARC."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
OUT=D/'rin_extension/air_wall_head_candidate_v4';OUT.mkdir(exist_ok=True)
source=ROOT/'work/sprite_style_unification_20261107/rin/locomotion01/native/b0_008_indices.png'
master=np.array(Image.open(source));master[152,144]=0 # left glove edge, not a head pixel
arc=(D/'rin_extension/prepared_run_v1/PL01_U.ARC').read_bytes()
assert hashlib.sha256(arc).hexdigest()=='61ce28a47ad537a9d9d6661af764fd97461d6584272a42e20f76c79049263078'
mask=np.zeros_like(master,bool)
mask[140:148,142:168]=True
mask[148:153,144:162]=True
mask[153:154,147:157]=True
mask &= master>0
records=[];targets={}
for n,dx,dy in [(21,4,-4),(27,8,-10),(35,8,-7),(39,-2,1)]:
    path=D/f'rin_extension/air_wall01/native/b0_{n:03d}_indices.png';old=np.array(Image.open(path));target=old.copy()
    # Explicit same-view semantic ROI excludes wrists and trailing ribbon.
    roi=np.zeros_like(old,bool)
    roi[140+dy:148+dy,142+dx:168+dx]=True
    roi[148+dy:153+dy,144+dx:162+dx]=True
    roi[153+dy:154+dy,147+dx:157+dx]=True
    translated=np.roll(np.roll(master,dx,axis=1),dy,axis=0)
    tm=np.roll(np.roll(mask,dx,axis=1),dy,axis=0)
    protected=np.zeros_like(old,bool)
    if n==27:protected[140:147,138:155]=True
    if n==35:protected[134:145,138:154]=True
    if n==39:protected[138:146,158:178]=True
    protected &= old>0
    target[roi]=0;target[tm]=translated[tm]
    target[protected]=old[protected]
    assert np.array_equal(target[~roi],old[~roi])
    Image.fromarray(target).save(OUT/f'b0_{n:03d}_indices.png')
    Image.fromarray(roi.astype(np.uint8)*255).save(OUT/f'b0_{n:03d}_edit_mask.png')
    records.append({'ref':n,'master_translation':[dx,dy],'changed_pixels':int(np.count_nonzero(target!=old)),
                    'outside_roi_exact':True,'master_opaque_pixels':int(mask.sum()),'protected_foreground_hand_pixels':int(np.count_nonzero(protected&roi)),'source':str(path.relative_to(ROOT))})
    targets[n]=target
for label,row in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),row*32);sheet=Image.new('RGB',(1600,428*len(targets)),'#64717b');draw=ImageDraw.Draw(sheet)
    for iy,(n,target) in enumerate(targets.items()):
        prior=np.array(Image.open(D/f'rin_extension/air_wall01/native/b0_{n:03d}_indices.png'))
        for ix,(title,a)in enumerate([('accepted run8',master),('parent pose',render(arc,0,0,n)[0]),('authored air',prior),('same-angle head candidate',target)]):
            pic=rgba(a,pal).crop((120,120,200,200)).resize((400,400),Image.Resampling.NEAREST);sheet.paste(pic,(ix*400,iy*428+28),pic);draw.text((ix*400+4,iy*428+5),f'{n} {title}',fill='white')
    sheet.save(OUT/f'{label}_comparison.png')
(OUT/'registration.json').write_text(json.dumps({'master':str(source.relative_to(ROOT)),'master_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'records':records,'applied':False,'art_accepted':False},indent=2)+'\n','utf8')
print(json.dumps(records))
