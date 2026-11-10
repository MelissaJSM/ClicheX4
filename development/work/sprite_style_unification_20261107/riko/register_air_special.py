"""공중 검/빙열참 새 의상을 기존 세부 머리·손잡이 접점에 등록한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';D=W/'riko/air_special_cloth04';OUT=D/'registered01'
assert not OUT.exists();OUT.mkdir()
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['parent']).read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==info['sha256']
pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in pal],np.int32)
im=Image.open(D/'generated.png').convert('RGBA');sample=np.array(im.resize((192,64),Image.Resampling.NEAREST))
labels=1+((sample[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8);labels[sample[:,:,3]<128]=0
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
wallroot=ROOT/'work/sprite_consistency_20261105/zero/riko/wall_fix';wallmeta=json.loads((wallroot/'reproduced_v1/proposal.json').read_text('utf8'))
wall=np.array(Image.open(ROOT/wallmeta['head_file']));targets={};rows=[]
for i,(b,n) in enumerate(((0,213),(1,54))):
    old=render(arc,b,b*5,n)[0];authored=np.zeros_like(old);authored[128:192,112:208]=labels[:,i*96:(i+1)*96]
    if b==0:hx,hy=-12,-23;head=front.copy()
    else:
        r=next(r for r in wallmeta['frames']if r['id']=='b1_054');hx,hy=r['new_head_anchor'];head=wall.copy()
        for x,y in r['occluded_world_pixels']:head[y-hy,x-hx]=0
    h,w=head.shape;inner=np.zeros_like(head,bool)
    for y,row in enumerate(head):
        xs=np.where(row>0)[0]
        if len(xs):inner[y,xs.min():xs.max()+1]=True
    mask=np.zeros_like(old,bool);mask[160+hy:160+hy+h,160+hx:160+hx+w]=inner
    assert np.array_equal(old[160+hy:160+hy+h,160+hx:160+hx+w][head>0],head[head>0])
    green=np.isin(head,[4,8,14]);options=[]
    for dy in range(-4,5):
        for dx in range(-4,5):
            q=authored[160+hy+dy:160+hy+dy+h,160+hx+dx:160+hx+dx+w]
            options.append((int(np.count_nonzero(q[green]!=head[green]))+int(np.count_nonzero(np.isin(q,[4,8,14])&~green)),abs(dx)+abs(dy),dx,dy))
    _,_,dx,dy=min(options);remove=np.roll(np.roll(mask,dy,axis=0),dx,axis=1)
    box=np.zeros_like(mask);box[160+hy+dy:160+hy+dy+h,160+hx+dx:160+hx+dx+w]=True
    remove|=box&np.isin(authored,[4,8,14]);out=authored.copy();out[remove]=0;out[mask]=old[mask]
    seam=np.zeros_like(mask);seam[160+hy+h-2:160+hy+h+max(0,dy)+2,160+hx-2:160+hx+w+2]=True
    gap=seam&(out==0)&(old>0)&~mask;out[gap]=old[gap]
    contact=np.zeros_like(mask)
    if b==0:contact[130:146,164:176]=True
    else:contact[130:145,163:179]=True;contact[147:155,136:147]=True
    out[contact]=old[contact]
    assert np.array_equal(out[mask],old[mask]) and np.array_equal(out[contact],old[contact])
    Image.fromarray(out).save(OUT/f'b{b}_{n:03d}_indices.png');Image.fromarray(authored).save(OUT/f'b{b}_{n:03d}_authored.png')
    Image.fromarray(mask.astype('uint8')*255).save(OUT/f'b{b}_{n:03d}_head_mask.png')
    targets[b,n]=out
    bbox=lambda a:[int(v)for v in (np.where(a>0)[1].min(),np.where(a>0)[0].min(),np.where(a>0)[1].max()+1,np.where(a>0)[0].max()+1)]
    rows.append({'bank':b,'ref':n,'head_exact':True,'contact_exact':True,'head_mask_pixels':int(mask.sum()),
        'before_bounds':bbox(old),'after_bounds':bbox(out),'generated_head_offset':[dx,dy],
        'target':str((OUT/f'b{b}_{n:03d}_indices.png').relative_to(ROOT)),
        'target_sha256':sha((OUT/f'b{b}_{n:03d}_indices.png').read_bytes())})
for label,palrow in(('normal',0),('black',13)):
    palette=struct.unpack_from('<16H',entry(arc,9),palrow*32);sheet=Image.new('RGB',(1200,856),'#64717b');draw=ImageDraw.Draw(sheet)
    for row,((b,n),out) in enumerate(targets.items()):
        for col,(title,a) in enumerate((('before',render(arc,b,b*5,n)[0]),('authored',np.array(Image.open(OUT/f'b{b}_{n:03d}_authored.png'))),('registered',out))):
            pic=rgba(a,palette).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST);sheet.paste(pic,(col*400,row*428+28),pic);draw.text((col*400+4,row*428+5),f'{b}:{n} {title}',fill='white')
    sheet.save(OUT/f'{label}_comparison.png')
(OUT/'registration.json').write_text(json.dumps({'source_arc':info['parent'],'source_sha256':sha(arc),'generated_sha256':sha((D/'generated.png').read_bytes()),'frames':rows,'review_only':True},indent=2)+'\n','utf8')
print(json.dumps(rows))
