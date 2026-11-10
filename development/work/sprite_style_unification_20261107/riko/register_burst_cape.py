"""생성한 망토 끝만 원래 네이티브 캔버스에 등록한다."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';D=W/'riko/burst_cape_variants01';O=D/'native02'
assert not O.exists();O.mkdir()
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['parent']).read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)==info['parent_sha256']
pal=struct.unpack_from('<16H',entry(arc,9));rgb=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in pal],np.int32)
im=Image.open(D/'generated.png').convert('RGBA');sample=np.array(im.resize((192,64),Image.Resampling.NEAREST))
labels=1+((sample[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-rgb[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8)
labels[sample[:,:,3]<128]=0
base=render(arc,1,5,183)[0];targets={};rows=[]
for i,n in enumerate((182,185)):
    authored=np.zeros_like(base);authored[128:192,112:208]=labels[:,i*96:(i+1)*96]
    # Only the fluttering free tip above the head is admitted from the edit.
    # The common cape base and the accepted face/body stay byte-exact.
    mask=np.zeros_like(base,bool);mask[140:150,148:165]=True
    out=base.copy();out[mask]=authored[mask]
    assert np.array_equal(out[~mask],base[~mask])
    target=O/f'b1_{n:03d}_indices.png';Image.fromarray(out).save(target);targets[n]=out
    rows.append({'ref':n,'target':str(target.relative_to(ROOT)),'sha256':sha(target.read_bytes()),
                 'shared_body_ref':183,'body_outside_cape_tip_exact':True,'tip_bbox':[148,140,165,150],
                 'changed_from_new_183':int(np.count_nonzero(out!=base))})
for label,palrow in [('normal',0),('black',13)]:
    palette=struct.unpack_from('<16H',entry(arc,9),palrow*32)
    sheet=Image.new('RGB',(1200,856),'#64717b');dr=ImageDraw.Draw(sheet)
    for y,(n,new) in enumerate(targets.items()):
        for x,(name,a) in enumerate([('previous',render(arc,1,5,n)[0]),('common new183',base),('new cape',new)]):
            p=rgba(a,palette).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST)
            sheet.paste(p,(x*400,y*428+28),p);dr.text((x*400+4,y*428+5),f'{n} {name}',fill='white')
    sheet.save(O/f'{label}_comparison.png')
report={'generated_sha256':sha((D/'generated.png').read_bytes()),'generated_size':im.size,
        'parent_sha256':sha(arc),'frames':rows,'requires_static_23_24_sync':True,
        'variants_differ_pixels':int(np.count_nonzero(targets[182]!=targets[185])),
        'native_review_only':True,'packed':False}
(O/'registration.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))
