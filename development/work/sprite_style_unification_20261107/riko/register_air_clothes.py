"""새 의상 원화를 기존 정밀 머리와 게임 접점에 등록한다. BIN은 쓰지 않는다."""
from pathlib import Path
import hashlib,json,sys,struct
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=HERE.parent
Z=W/'zero_audit'
SRC=Z/'riko_restore/prepared_cloth_v1/PL01_U.ARC'
A=HERE/'air_wall_cloth01'
OUT=A/'registered02'
sha=lambda b:hashlib.sha256(b).hexdigest()
arc=SRC.read_bytes()
assert sha(arc)=='6ebb0239f27253bdd37b16c54b66a5b2044ba8191f41b8cc9f29cfbe15a440dc'
assert not OUT.exists()
OUT.mkdir()
inv=json.loads((Z/'shared_masters/inventory.json').read_text('utf8'))
heads={r['id']:r for r in inv['riko']['head_masters'][0]['matches']}
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
wall_root=ROOT/'work/sprite_consistency_20261105/zero/riko/wall_fix'
wall_info=json.loads((wall_root/'reproduced_v1/proposal.json').read_text('utf8'))
wall_head=np.array(Image.open(ROOT/wall_info['head_file']))
targets={};rows=[]
for n in (21,39,49,229):
    old=render(arc,0,0,n)[0]
    authored=np.array(Image.open(A/'native'/f'b0_{n}_indices.png'))
    if n==39:
        r=next(r for r in wall_info['frames'] if r['id']=='b0_039')
        hx,hy=r['new_head_anchor'];head=wall_head.copy()
        for x,y in r['occluded_world_pixels']:
            head[y-hy,x-hx]=0
    else:
        hx,hy=heads[f'b0_{n:03d}']['origin_world'];head=front
    h,w=head.shape
    mask=np.zeros_like(old,bool)
    mask[160+hy:160+hy+h,160+hx:160+hx+w]=head>0
    assert np.array_equal(old[mask],head[head>0]),('head mismatch',n)
    # The transparent slots between hair/face clusters are part of the accepted
    # head too. Preserve the original underlying value instead of leaving newly
    # generated dark/white specks in those slots.
    inner=np.zeros_like(head,bool)
    for yy,row in enumerate(head):
        xs=np.where(row>0)[0]
        if len(xs):inner[yy,int(xs.min()):int(xs.max())+1]=True
    negative=inner&(head==0)
    mask[160+hy:160+hy+h,160+hx:160+hx+w]|=negative
    green=np.isin(head,[4,8,14]);opts=[]
    for dy in range(-5,6):
        for dx in range(-5,6):
            p=authored[160+hy+dy:160+hy+dy+h,160+hx+dx:160+hx+dx+w]
            error=int(np.count_nonzero(p[green]!=head[green]))
            extra=int(np.count_nonzero(np.isin(p,[4,8,14])&~green))
            opts.append((error+extra,abs(dx)+abs(dy),dx,dy))
    _,_,dx,dy=min(opts)
    removal=np.roll(np.roll(mask,dy,axis=0),dx,axis=1)
    box=np.zeros_like(mask)
    box[160+hy+dy:160+hy+dy+h,160+hx+dx:160+hx+dx+w]=True
    removal|=box&np.isin(authored,[4,8,14])
    target=authored.copy();target[removal]=0;target[mask]=old[mask]
    seam=np.zeros_like(mask)
    seam[160+hy+h-2:160+hy+h+max(0,dy)+2,160+hx-2:160+hx+w+2]=True
    gaps=seam&(target==0)&(old>0)&~mask
    target[gaps]=old[gaps]
    # Preserve the hand/forearm/grip that touches the wall or the saber effect.
    # These bounded regions intentionally exclude the new lower sleeve/torso.
    contact=np.zeros_like(mask)
    if n==39: contact[128:149,163:178]=True
    if n==229: contact[130:149,159:171]=True
    target[contact]=old[contact]
    assert np.array_equal(target[mask],old[mask])
    assert np.array_equal(target[contact],old[contact])
    targets[n]=target
    path=OUT/f'b0_{n:03d}_indices.png'
    Image.fromarray(target).save(path)
    Image.fromarray(mask.astype(np.uint8)*255).save(OUT/f'b0_{n:03d}_head_mask.png')
    Image.fromarray(contact.astype(np.uint8)*255).save(OUT/f'b0_{n:03d}_contact_mask.png')
    rows.append({'ref':n,'source_native':str((A/'native'/f'b0_{n}_indices.png').relative_to(ROOT)),
                 'source_native_sha256':sha((A/'native'/f'b0_{n}_indices.png').read_bytes()),
                 'head_source_shape':[w,h],'head_offset':[dx,dy],
                 'head_preserved_pixels':int(mask.sum()),'neck_gap_pixels':int(gaps.sum()),
                 'head_negative_space_preserved':int(negative.sum()),
                 'protected_contact_pixels':int(np.count_nonzero(old[contact])),
                 'head_exact':True,'contact_exact':True,'target':str(path.relative_to(ROOT)),
                 'target_sha256':sha(path.read_bytes())})
for label,row in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),row*32)
    for start in (0,2):
        sheet=Image.new('RGB',(1200,856),'#64717b');draw=ImageDraw.Draw(sheet)
        for iy,n in enumerate(list(targets)[start:start+2]):
            for ix,(title,pixels) in enumerate([('before',render(arc,0,0,n)[0]),('authored',np.array(Image.open(A/'native'/f'b0_{n}_indices.png'))),('registered',targets[n])]):
                pic=rgba(pixels,pal).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST)
                sheet.paste(pic,(ix*400,iy*428+28),pic);draw.text((ix*400+5,iy*428+5),f'{n} {title}',fill='white')
        sheet.save(OUT/f'{label}_comparison_{start//2}.png')
(OUT/'registration.json').write_text(json.dumps({'source_arc':str(SRC.relative_to(ROOT)),
    'source_sha256':sha(arc),'source_generated_sha256':sha((A/'generated.png').read_bytes()),
    'frames':rows,'packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(rows))
