"""특수4 원화의 균일 팔레트 변환, 기존 세밀한 머리·검 접점 고정."""
from pathlib import Path
import sys,json,hashlib,struct,argparse
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
parser=argparse.ArgumentParser();parser.add_argument('page',type=int);args=parser.parse_args()
W=ROOT/'work/sprite_style_unification_20261107';D=W/f'riko/ceremony_clothes16/page{args.page}';OUT=D/'registered01';OUT.mkdir(exist_ok=False)
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['parent']).read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==info['sha256']
pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in pal],np.int32)
im=Image.open(D/'generated.png').convert('RGBA');cw,ch=info['native_cell'];gx,gy=info['grid'];width=cw*gx;scale=im.width/width;nh=round(im.height/scale);assert abs(nh-ch*gy)<=1
sample=np.array(im.resize((width,nh),Image.Resampling.NEAREST));ix=1+((sample[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8);ix[sample[:,:,3]<128]=0
indices=np.zeros((max(nh,ch*gy),width),np.uint8);indices[:nh]=ix
rects={(0,249):(146,144,169,163),(0,250):(152,134,175,153),(0,251):(151,134,174,153),(0,252):(150,138,173,157),(0,253):(148,138,171,157),(1,2):(145,133,168,152),(1,3):(144,134,167,153),(1,4):(145,134,168,153),(1,6):(144,134,167,153)}
rows=[];targets={};xbase,ybase=info['crop'][:2]
for f in info['frames']:
    b=f['bank'];n=f['ref'];i=f['cell'];key=(b,n)
    if [b,n] not in info['apply_only_keys']:continue
    old=render(arc,b,b*5,n)[0];a=np.zeros_like(old);cell=indices[i//gx*ch:(i//gx+1)*ch,i%gx*cw:(i%gx+1)*cw];a[ybase:ybase+ch,xbase:xbase+cw]=cell
    x0,y0,x1,y1=rects[key];head=old[y0:y1,x0:x1];green=np.isin(head,[4,8,14]);opts=[]
    for dy in range(-8,9):
        for dx in range(-8,9):
            q=a[y0-dy:y1-dy,x0-dx:x1-dx];err=np.count_nonzero(q[green]!=head[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green);opts.append((int(err),abs(dx)+abs(dy),dx,dy))
    err,_,dx,dy=min(opts);authored=np.zeros_like(old);yy,xx=np.nonzero(a);assert (xx+dx).min()>=0 and (xx+dx).max()<384 and (yy+dy).min()>=0 and (yy+dy).max()<384;authored[yy+dy,xx+dx]=a[yy,xx]
    mask=np.zeros_like(old,bool)
    for y,row in enumerate(head):
        xs=np.flatnonzero(row)
        if len(xs):mask[y0+y,x0+xs.min():x0+xs.max()+1]=True
    out=authored.copy();window=np.zeros_like(mask);window[y0-2:y1+2,x0-2:x1+2]=True;out[window&np.isin(authored,[4,8,14])&~mask]=0;out[mask]=old[mask]
    contact=np.zeros_like(mask)
    if n in(108,128):contact[156:165,80:127]=True
    out[contact]=old[contact]
    for label,q in [('indices',out),('authored',authored),('head_mask',mask.astype('uint8')*255),('contact_mask',contact.astype('uint8')*255)]:Image.fromarray(q).save(OUT/f'b{b}_{n:03}_{label}.png')
    bbox=lambda q:[int(v)for v in(np.where(q>0)[1].min(),np.where(q>0)[0].min(),np.where(q>0)[1].max()+1,np.where(q>0)[0].max()+1)]
    p=OUT/f'b{b}_{n:03}_indices.png';rows.append(dict(bank=b,ref=n,generated_translation=[dx,dy],head_rect=rects[key],head_preserved=True,head_mask_pixels=int(mask.sum()),original_weapon_contact_exact=bool(np.array_equal(out[contact],old[contact]))if contact.any()else None,contact_mask_pixels=int(contact.sum()),before_bounds=bbox(old),after_bounds=bbox(out),target=str(p.relative_to(ROOT)),target_sha256=sha(p.read_bytes())))
    targets[key]=out
for label,pr in [('normal',0),('black',13)]:
    palette=struct.unpack_from('<16H',entry(arc,9),pr*32);sheet=Image.new('RGB',(1152,len(targets)*400),'#64717b');draw=ImageDraw.Draw(sheet)
    for row,((b,n),out)in enumerate(targets.items()):
        for col,(title,q)in enumerate([('idle',render(arc,0,0,147)[0]),('before',render(arc,b,b*5,n)[0]),('candidate',out)]):
            pic=rgba(q,palette).crop(info['crop']).resize((384,384),Image.Resampling.NEAREST);sheet.paste(pic,(col*384,row*400+16),pic);draw.text((col*384+4,row*400+5),f'b{b}_{n:03} {title}',fill='white')
    sheet.save(OUT/f'{label}_comparison.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_arc=info['parent'],source_sha256=sha(arc),generated_sha256=sha((D/'generated.png').read_bytes()),generated_dimensions=im.size,uniform_source_scale=scale,native_canvas=[width,nh],frames=rows,candidate_only=True,game_applied=False,contact_review_pending=True),indent=2)+'\n','utf8')
print(json.dumps(rows))
