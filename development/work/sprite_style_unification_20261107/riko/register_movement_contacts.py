"""Register newly authored boot/lower-body modules to existing motion contact heights."""
from pathlib import Path
import json,hashlib,sys,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).resolve().parent/'movement_clothes14'
P=D.parent/'prepared_special_clothes_v1/PL01_U.ARC';arc=P.read_bytes()
OUT=D/'contacts_probe01';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Whole source pixels move together. No resampling, new pixels, or old boot copying.
adjust={4:(164,-2,0),12:(169,0,-2),13:(169,0,-2),15:(164,0,-3),16:(164,0,-3),17:(168,0,-1),19:(174,0,-1),20:(175,0,-1)}
targets={};rows=[]
for page in [2,3,4,5]:
    info=json.loads((D/f'page{page}'/'inputs.json').read_text('utf8'))
    reg=json.loads((D/f'page{page}'/'registered01'/'registration.json').read_text('utf8'))
    for r in reg['frames']:
        n=r['ref']
        if n not in info.get('apply_only_refs',[x['ref']for x in info['frames']]):continue
        p=ROOT/r['target'];assert sha(p)==r['target_sha256'];q=np.array(Image.open(p));out=q.copy();old=render(arc,0,0,n)[0]
        if n in adjust:
            y0,dx,dy=adjust[n];mask=np.indices(q.shape)[0]>=y0
            yy,xx=np.where(mask&(q>0));out[mask]=0;out[yy+dy,xx+dx]=q[yy,xx]
        else:y0=dx=dy=0
        path=OUT/f'b0_{n:03}_indices.png';Image.fromarray(out).save(path)
        row=dict(bank=0,ref=n,source=r['target'],source_sha256=r['target_sha256'],target=str(path.relative_to(ROOT)),target_sha256=sha(path),lower_module_rows_from=y0,lower_module_translation=[dx,dy],original_pixels_copied=0,original_sole_y=int(np.where(old>0)[0].max()),new_sole_y=int(np.where(out>0)[0].max()))
        rows.append(row);targets[n]=(old,q,out)
for label,pr in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),32*pr)
    ids=sorted(targets)
    for pg in range(0,len(ids),4):
        selected=ids[pg:pg+4];sheet=Image.new('RGB',(1200,400*len(selected)),'#64717b');dr=ImageDraw.Draw(sheet)
        for i,n in enumerate(selected):
            for j,(name,q)in enumerate(zip(['old','registered art','contact candidate'],targets[n])):
                pic=rgba(q,pal).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);sheet.paste(pic,(j*400,i*400+35),pic);dr.text((j*400+4,i*400+5),f'{n}: {name}',fill='white')
        sheet.save(OUT/f'{label}_comparison_{pg//4:02}.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_sha256=sha(P),frames=rows,candidate_only=True,needs_joint_and_loop_review=True),indent=2)+'\n','utf8')
print(json.dumps(rows))
