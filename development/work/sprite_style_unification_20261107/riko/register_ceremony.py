"""새 의상과 기존 정밀 머리/손 접점의 원점을 맞춘 검토용 등록본."""
from pathlib import Path
import hashlib, json, struct, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';A=W/'riko/ceremony_cloth02';OUT=A/'registered02'
P=W/'riko/prepared_head_spaces_v1/PL01_U.ARC';arc=P.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='488b679ed027fd8916e0f48716c9e3fa65d03ff42d4ac21d38dffb6ed0a7edaf'
assert not OUT.exists();OUT.mkdir()
inv=json.loads((W/'zero_audit/shared_masters/inventory.json').read_text('utf8'))
heads={r['id']:r for r in inv['riko']['head_masters'][0]['matches']}
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
targets={};rows=[]
sources={n:A/'native'/f'b1_{n}_indices.png' for n in(1,20,183)}
sources[5]=W/'riko/victory_reverse03/native/b1_5_indices.png'
for n in (1,5,20,183):
    old=render(arc,1,5,n)[0];authored=np.array(Image.open(sources[n]))
    if n==20:
        # The vehicle pose uses its own accepted tilted head, not the upright template.
        hx,hy=-16,-19;head=old[141:160,144:168].copy()
    else:
        r=heads[f'b1_{n:03d}'];hx,hy=r['origin_world'];head=front[:,::-1] if r['view']=='mirror' else front
    h,w=head.shape;mask=np.zeros_like(old,bool);inner=np.zeros_like(head,bool)
    for y,row in enumerate(head):
        xs=np.where(row>0)[0]
        if len(xs):inner[y,xs.min():xs.max()+1]=True
    mask[160+hy:160+hy+h,160+hx:160+hx+w]=inner
    green=np.isin(head,[4,8,14]);options=[]
    for dy in range(-4,5):
        for dx in range(-4,5):
            q=authored[160+hy+dy:160+hy+dy+h,160+hx+dx:160+hx+dx+w]
            error=int(np.count_nonzero(q[green]!=head[green]));extra=int(np.count_nonzero(np.isin(q,[4,8,14])&~green))
            options.append((error+extra,abs(dx)+abs(dy),dx,dy))
    _,_,dx,dy=min(options)
    remove=np.roll(np.roll(mask,dy,axis=0),dx,axis=1)
    box=np.zeros_like(mask);box[160+hy+dy:160+hy+dy+h,160+hx+dx:160+hx+dx+w]=True
    remove|=box&np.isin(authored,[4,8,14])
    target=authored.copy();target[remove]=0;target[mask]=old[mask]
    seam=np.zeros_like(mask);seam[160+hy+h-2:160+hy+h+max(0,dy)+2,160+hx-2:160+hx+w+2]=True
    gap=seam&(target==0)&(old>0)&~mask;target[gap]=old[gap]
    contact=np.zeros_like(mask)
    if n==20:contact[156:164,139:150]=True  # front glove at the control
    if n==183:contact[177:185,136:145]=True # grounded glove contact
    target[contact]=old[contact]
    assert np.array_equal(target[mask],old[mask]) and np.array_equal(target[contact],old[contact])
    path=OUT/f'b1_{n:03d}_indices.png';Image.fromarray(target).save(path)
    Image.fromarray(mask.astype('uint8')*255).save(OUT/f'b1_{n:03d}_head_mask.png')
    Image.fromarray(contact.astype('uint8')*255).save(OUT/f'b1_{n:03d}_contact_mask.png')
    targets[n]=target;rows.append({'bank':1,'ref':n,'source_native':str(sources[n].relative_to(ROOT)),
        'source_native_sha256':sha(sources[n].read_bytes()),
        'head_origin':[hx,hy],'generated_head_offset':[dx,dy],'preserved_head_region_pixels':int(mask.sum()),
        'head_exact':True,'contact_exact':True,'contact_region_pixels':int(contact.sum()),
        'target':str(path.relative_to(ROOT)),'target_sha256':sha(path.read_bytes())})
for label,row in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),row*32)
    sheet=Image.new('RGB',(1200,428*len(targets)),'#64717b');d=ImageDraw.Draw(sheet)
    for iy,(n,target) in enumerate(targets.items()):
        for ix,(name,a) in enumerate([('before',render(arc,1,5,n)[0]),('authored',np.array(Image.open(sources[n]))),('registered',target)]):
            im=rgba(a,pal).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST)
            sheet.paste(im,(ix*400,iy*428+28),im);d.text((ix*400+4,iy*428+6),f'{n} {name}',fill='white')
    sheet.save(OUT/f'{label}_comparison.png')
(OUT/'registration.json').write_text(json.dumps({'source_arc':str(P.relative_to(ROOT)),'source_sha256':sha(arc),
    'source_generated_sha256':sha((A/'generated.png').read_bytes()),'frames':rows,'review_only':True,
    'replacement_pose_5_generated_sha256':sha((W/'riko/victory_reverse03/generated.png').read_bytes()),
    'rejected_previous_pose_5':'첫 원화에서 시선과 발 방향이 바뀌어 원래 오른쪽 시선으로 새로 제작함'},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(rows))
