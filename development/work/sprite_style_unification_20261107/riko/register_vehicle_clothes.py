"""새 탑승 의상을 균일 축소·원래 기울어진 머리/조종손에 등록한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).resolve().parent/'vehicle_clothes09';OUT=D/'registered01';OUT.mkdir(exist_ok=False)
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['parent']).read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==info['sha256']
pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in pal],np.int32)
im=Image.open(D/'generated.png').convert('RGBA');scale=im.width/288;nh=round(im.height/scale)
assert abs(im.height/scale-nh)<0.3 and 64<=nh<=96
sample=np.array(im.resize((288,nh),Image.Resampling.NEAREST))
idx=1+((sample[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8);idx[sample[:,:,3]<128]=0
head_rects={25:(140,142,171,160),33:(142,136,173,153),41:(148,134,178,154)}
hand_rects={25:(140,160,150,167),33:(141,153,151,160),41:(144,152,154,159)}
rows=[];targets={}
for r in info['frames']:
    n=r['ref'];old=render(arc,1,5,n)[0];a=np.zeros_like(old);a[112:112+nh,112:208]=idx[:,r['cell']*96:(r['cell']+1)*96]
    x0,y0,x1,y1=head_rects[n];head=old[y0:y1,x0:x1];green=np.isin(head,[4,8,14]);hh,hw=head.shape
    candidates=[]
    for dy in range(-16,17):
        for dx in range(-5,6):
            q=a[y0-dy:y1-dy,x0-dx:x1-dx]
            error=np.count_nonzero(q[green]!=head[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green)
            candidates.append((int(error),abs(dx)+abs(dy),dx,dy))
    _,_,dx,dy=min(candidates);authored=np.zeros_like(old);yy,xx=np.nonzero(a);authored[yy+dy,xx+dx]=a[yy,xx]
    mask=np.zeros_like(old,bool)
    for row,v in enumerate(head):
        xs=np.flatnonzero(v)
        if len(xs):mask[y0+row,x0+xs[0]:x0+xs[-1]+1]=True
    out=authored.copy();window=np.zeros_like(mask);window[y0-2:y1+2,x0-2:x1+2]=True
    extra_green=window&np.isin(authored,[4,8,14])&~mask
    out[extra_green]=0;out[mask]=old[mask]
    xx0,yy0,xx1,yy1=hand_rects[n];contacts=np.zeros_like(mask);contacts[yy0:yy1,xx0:xx1]=True;out[contacts]=old[contacts]
    assert np.array_equal(out[mask],old[mask])and np.array_equal(out[contacts],old[contacts])
    for label,q in [('indices',out),('authored',authored),('head_mask',mask.astype('uint8')*255),('hand_mask',contacts.astype('uint8')*255)]:Image.fromarray(q).save(OUT/f'b1_{n:03}_{label}.png')
    bbox=lambda q:[int(v)for v in(np.where(q>0)[1].min(),np.where(q>0)[0].min(),np.where(q>0)[1].max()+1,np.where(q>0)[0].max()+1)]
    rows.append(dict(bank=1,ref=n,generated_translation=[dx,dy],head_rect=head_rects[n],head_mask_pixels=int(mask.sum()),hand_rect=hand_rects[n],hand_contact_exact=True,head_exact=True,cleared_generated_extra_green=int(extra_green.sum()),before_bounds=bbox(old),after_bounds=bbox(out),target=str((OUT/f'b1_{n:03}_indices.png').relative_to(ROOT)),target_sha256=sha((OUT/f'b1_{n:03}_indices.png').read_bytes())))
    targets[n]=out
for label,pr in [('normal',0),('black',13)]:
    palette=struct.unpack_from('<16H',entry(arc,9),pr*32);sheet=Image.new('RGB',(1200,400*len(targets)),'#64717b');draw=ImageDraw.Draw(sheet)
    for row,(n,out)in enumerate(targets.items()):
        for col,(title,q)in enumerate([('idle',render(arc,0,0,147)[0]),('before',render(arc,1,5,n)[0]),('candidate',out)]):
            pic=rgba(q,palette).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);sheet.paste(pic,(col*400,row*400+40),pic);draw.text((col*400+4,row*400+8),f'b1_{n:03} {title}',fill='white')
    sheet.save(OUT/f'{label}_comparison.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_arc=info['parent'],source_sha256=sha(arc),generated_sha256=sha((D/'generated.png').read_bytes()),generated_dimensions=im.size,uniform_source_scale=scale,native_canvas=[288,nh],frames=rows,candidate_only=True,game_applied=False),indent=2)+'\n','utf8')
print(json.dumps(rows))
