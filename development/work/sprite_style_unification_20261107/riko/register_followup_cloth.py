"""생성 캔버스 비율을 보존하고 새 의상을 기존 머리·접지 기준으로 등록한다."""
from pathlib import Path
import sys,json,struct,hashlib,argparse
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
parser=argparse.ArgumentParser();parser.add_argument('--saber-continuation',action='store_true');args=parser.parse_args()
W=ROOT/'work/sprite_style_unification_20261107';D=W/('riko/saber_continuation06'if args.saber_continuation else 'riko/followup_cloth05');OUT=D/('registered01'if args.saber_continuation else 'registered03');OUT.mkdir(exist_ok=False)
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['parent']).read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==info['sha256']
pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in pal],np.int32)
im=Image.open(D/'generated.png').convert('RGBA');a=np.asarray(im);scale=im.width/288;nh=round(im.height/scale)
assert nh==96 and abs(im.height/scale-nh)<1e-6,(im.size,scale,nh)
sample=np.array(im.resize((288,nh),Image.Resampling.NEAREST));indices=1+((sample[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8)
indices[sample[:,:,3]<128]=0
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
green=np.isin(front,[4,8,14]);h,w=front.shape;inside=np.zeros_like(front,bool)
for y,row in enumerate(front):
    xs=np.where(row>0)[0]
    if len(xs):inside[y,xs.min():xs.max()+1]=True
def head_anchor(a,lo,hi):
    choices=[]
    for y in range(lo,hi):
        for x in range(125,170):
            q=a[y:y+h,x:x+w]
            mismatch=np.count_nonzero(q[green]!=front[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green)
            choices.append((int(mismatch),x,y))
    return min(choices)
rows=[];targets={}
for r in info['frames']:
    b,n=r['bank'],r['ref'];old=render(arc,b,b*5,n)[0];generated=np.zeros_like(old)
    generated[112:112+nh,112:208]=indices[:,r['cell']*96:(r['cell']+1)*96]
    mismatch,hx,hy=head_anchor(old,115,155);assert mismatch==0,(n,mismatch)
    assert np.array_equal(old[hy:hy+h,hx:hx+w][front>0],front[front>0])
    _,gx,gy=head_anchor(generated,115,165)
    dx,dy=hx-gx,hy-gy
    authored=np.zeros_like(old);yy,xx=np.nonzero(generated);assert min(xx+dx)>=0 and max(xx+dx)<384 and min(yy+dy)>=0 and max(yy+dy)<384
    authored[yy+dy,xx+dx]=generated[yy,xx]
    mask=np.zeros_like(old,bool);mask[hy:hy+h,hx:hx+w]=inside
    out=authored.copy();out[mask]=old[mask]
    # Keep the exact original weapon hand only; no old garment/leg alpha overlay.
    contacts=np.zeros_like(mask)
    if n in (111,113,121,125):contacts[161:169,124:144]=True
    if n==230:contacts[153:159,137:145]=True
    out[contacts]=old[contacts]
    if args.saber_continuation:
        base=render(arc,0,0,111)[0]
        offset=-1 if n==113 else 0
        assert np.array_equal(old[169:],np.roll(base,offset,axis=1)[169:]), 'Different original lower-body pose'
        lower=np.array(Image.open(W/'riko/followup_cloth05/registered03/b0_111_indices.png'))
        out[169:]=np.roll(lower,offset,axis=1)[169:]
    Image.fromarray(out).save(OUT/f'b{b}_{n:03}_indices.png');Image.fromarray(authored).save(OUT/f'b{b}_{n:03}_authored.png');Image.fromarray(mask.astype('uint8')*255).save(OUT/f'b{b}_{n:03}_head_mask.png')
    bbox=lambda q:[int(v)for v in(np.where(q>0)[1].min(),np.where(q>0)[0].min(),np.where(q>0)[1].max()+1,np.where(q>0)[0].max()+1)]
    sole=lambda q:{str(y):np.where(q[y]>0)[0].tolist()for y in range(182,184)}
    rows.append(dict(bank=b,ref=n,source_head_anchor=[hx-160,hy-160],generated_translation=[dx,dy],head_preserved=True,head_mask_pixels=int(mask.sum()),
        hand_contact_mask_pixels=int(contacts.sum()),hand_contact_exact=bool(np.array_equal(out[contacts],old[contacts])),before_sole=sole(old),after_sole=sole(out),
        before_bounds=bbox(old),after_bounds=bbox(out),target=str((OUT/f'b{b}_{n:03}_indices.png').relative_to(ROOT)),target_sha256=sha((OUT/f'b{b}_{n:03}_indices.png').read_bytes())))
    targets[b,n]=out
for label,pr in [('normal',0),('black',13)]:
    palette=struct.unpack_from('<16H',entry(arc,9),pr*32);sheet=Image.new('RGB',(1200,1200),'#64717b');draw=ImageDraw.Draw(sheet)
    for row,((b,n),out)in enumerate(targets.items()):
        for col,(name,q)in enumerate([('idle',render(arc,0,0,147)[0]),('before',render(arc,b,b*5,n)[0]),('candidate',out)]):
            pic=rgba(q,palette).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST)
            sheet.paste(pic,(col*400,row*400+40),pic);draw.text((col*400+4,row*400+8),f'b{b}_{n:03} {name}',fill='white')
    sheet.save(OUT/f'{label}_comparison.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_arc=info['parent'],source_sha256=sha(arc),generated_sha256=sha((D/'generated.png').read_bytes()),generated_dimensions=im.size,uniform_source_scale=scale,native_canvas=[288,nh],frames=rows,candidate_only=True,game_applied=False),indent=2)+'\n','utf8')
print(json.dumps(rows))
