"""현재 리코 몸체 참조 전수를 원점/배율을 바꾸지 않고 대기 옆에 모은다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';OUT=W/'riko/all_unique_review_v8';OUT.mkdir(exist_ok=False)
source=W/'riko/prepared_ground_boots_v13/PL01_U.ARC';arc=source.read_bytes()
assert hashlib.sha256(arc).hexdigest()=='026dd3d47ff05e7a7e9b6ef2330ab06d6be3c617586b6d3aa124a295aee74391'
groups=json.loads((W/'zero_audit/group_map.json').read_text('utf8'))['riko']
allrefs=sorted({ref for value in groups.values()for ref in value.get('body_or_head_refs',[])})
refs=[ref for ref in allrefs if ref.startswith(('b0_','b1_'))]
unique={};frames={};reference_groups={}
for ref in refs:
    b,n=int(ref[1]),int(ref[3:]);a=render(arc,b,b*5,n)[0]
    y,x=np.nonzero(a)
    if not len(x):continue
    box=(int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1)
    im=a[box[1]:box[3],box[0]:box[2]]
    key=hashlib.sha256(im.tobytes()+str(im.shape).encode()).hexdigest()
    unique.setdefault(key,[]).append(ref);frames[ref]=(a,box)
    reference_groups[ref]=[name for name,g in groups.items()if ref in g.get('body_or_head_refs',[])]
pal=struct.unpack_from('<64H',entry(arc,9));idle=render(arc,0,0,147)[0]
rows=list(unique.values());pages=[]
for start in range(0,len(rows),9):
    selected=rows[start:start+9];items=[['b0_147']]+selected
    sheet=Image.new('RGB',(1200,270*((len(items)+3)//4)),'#64717b');draw=ImageDraw.Draw(sheet)
    evidence=[]
    for i,aliases in enumerate(items):
        ref=aliases[0];a=idle if i==0 else frames[ref][0]
        ys,xs=np.nonzero(a);bbox=(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)
        crop=(112,110,208,192)
        assert crop[0]<=bbox[0]and crop[1]<=bbox[1]and crop[2]>=bbox[2]and crop[3]>=bbox[3],(ref,bbox)
        x=i%4*300;y=i//4*270
        label='IDLE147' if i==0 else ref+(' +'+str(len(aliases)-1)+' aliases'if len(aliases)>1 else '')
        draw.text((x+4,y+3),label,fill='white')
        pic=rgba(a,pal).crop(crop).resize((288,246),Image.Resampling.NEAREST)
        sheet.paste(pic,(x+6,y+24),pic)
        evidence.append(dict(ref=ref,aliases=aliases,groups=reference_groups.get(ref,[]),bbox=bbox))
    name=f'page_{start//9:02}.png';sheet.save(OUT/name);pages.append(dict(file=name,frames=evidence,viewed=False))
report={'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(arc).hexdigest(),
        'body_refs_in_groups':len(refs),'static_refs_reviewed_separately':[r for r in allrefs if r not in refs],'nonempty_refs':len(frames),'translation_identical_groups':len(rows),
        'world_origin':[160,160],'scale':3,'pages':pages,'all_visually_reviewed':False}
(OUT/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({k:v for k,v in report.items()if k!='pages'}))
