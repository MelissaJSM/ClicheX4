"""새 벽 원화4를 균일 native 변환하고 기존 세밀한 머리 위치에 등록한다."""
from pathlib import Path
import sys,json,struct,hashlib,argparse
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
p=argparse.ArgumentParser();p.add_argument('--page2',action='store_true');args=p.parse_args()
D=Path(__file__).resolve().parent/'wall_clothes10'
if args.page2:D=D/'page2'
OUT=D/'registered01';OUT.mkdir(exist_ok=False)
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['parent']).read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==info['sha256']
pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in pal],np.int32)
im=Image.open(D/'generated.png').convert('RGBA');gx,gy=info['grid'];width=96*gx;scale=im.width/width;nh=round(im.height/scale)
assert abs(nh-gy*96)<=1,(im.size,nh,gy)
sample=np.array(im.resize((width,nh),Image.Resampling.NEAREST));idx=1+((sample[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8);idx[sample[:,:,3]<128]=0
rects={37:(152,133,176,153),38:(142,128,167,148),**{n:(145,131,170,152)for n in [39,40,41,42,43]}}
rows=[];targets={}
for r in info['frames']:
    n=r['ref'];i=r['cell'];old=render(arc,0,0,n)[0];a=np.zeros_like(old)
    cell=idx[96*(i//gx):96*(i//gx+1),96*(i%gx):96*(i%gx+1)]
    a[112:112+cell.shape[0],112:208]=cell
    x0,y0,x1,y1=rects[n];head=old[y0:y1,x0:x1];green=np.isin(head,[4,8,14]);options=[]
    for dy in range(-10,11):
        for dx in range(-8,9):
            q=a[y0-dy:y1-dy,x0-dx:x1-dx]
            error=np.count_nonzero(q[green]!=head[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green)
            options.append((int(error),abs(dx)+abs(dy),dx,dy))
    _,_,dx,dy=min(options);authored=np.zeros_like(old);yy,xx=np.nonzero(a);authored[yy+dy,xx+dx]=a[yy,xx]
    mask=np.zeros_like(old,bool)
    for y,row in enumerate(head):
        xs=np.flatnonzero(row)
        if len(xs):mask[y0+y,x0+xs.min():x0+xs.max()+1]=True
    out=authored.copy();window=np.zeros_like(mask);window[y0-2:y1+2,x0-2:x1+2]=True
    out[window&np.isin(authored,[4,8,14])&~mask]=0;out[mask]=old[mask]
    assert np.array_equal(out[mask],old[mask])
    for label,q in [('indices',out),('authored',authored),('head_mask',mask.astype('uint8')*255)]:Image.fromarray(q).save(OUT/f'b0_{n:03}_{label}.png')
    bbox=lambda q:[int(v)for v in(np.where(q>0)[1].min(),np.where(q>0)[0].min(),np.where(q>0)[1].max()+1,np.where(q>0)[0].max()+1)]
    rows.append(dict(bank=0,ref=n,generated_translation=[dx,dy],head_rect=rects[n],head_mask_pixels=int(mask.sum()),head_exact=True,hand_contact_exact=None,before_bounds=bbox(old),after_bounds=bbox(out),target=str((OUT/f'b0_{n:03}_indices.png').relative_to(ROOT)),target_sha256=sha((OUT/f'b0_{n:03}_indices.png').read_bytes())))
    targets[n]=out
for label,pr in [('normal',0),('black',13)]:
    palette=struct.unpack_from('<16H',entry(arc,9),pr*32);sheet=Image.new('RGB',(1200,400*len(targets)),'#64717b');draw=ImageDraw.Draw(sheet)
    for row,(n,out)in enumerate(targets.items()):
        for col,(title,q)in enumerate([('idle',render(arc,0,0,147)[0]),('before',render(arc,0,0,n)[0]),('candidate',out)]):
            pic=rgba(q,palette).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);sheet.paste(pic,(col*400,row*400+40),pic);draw.text((col*400+4,row*400+8),f'b0_{n:03} {title}',fill='white')
    sheet.save(OUT/f'{label}_comparison.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_arc=info['parent'],source_sha256=sha(arc),generated_sha256=sha((D/'generated.png').read_bytes()),generated_dimensions=im.size,uniform_source_scale=scale,native_canvas=[width,nh],frames=rows,candidate_only=True,game_applied=False,contact_review_pending=True),indent=2)+'\n','utf8')
print(json.dumps(rows))
