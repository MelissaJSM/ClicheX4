import json,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame
d=Path(__file__).parent;out=d/'production01';out.mkdir(exist_ok=True)
parent=ROOT/'out/ver_buki_riko/shibuki_weapon_palette_20261026T170706783998Z';arc=(parent/'modified.arc').read_bytes();es=psx_arc(arc);gfx,parts,pal=[arc[e['offset']:e['offset']+e['size']] for t in [2,3,9] for e in es if int(e['type'],16)==t];bank=graphics_bank(gfx,0,allow_bank_aliases=True);words=struct.unpack('<16H',pal[:32]);rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
old=json.loads((d.parent/'remaining_v1/production14/art.json').read_text());groups=[q for q in old['groups'] if q['frame'] in [89,90,91,97,98]]
for q in groups:
    f=bank['frames'][q['frame']];q['budget']=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).end-f['offset'];q['effect_tiles']=[]
src=Image.open(d/'generated_v1.png').convert('RGBA');scale=47/369;records=[];targets={}
for i,n in enumerate([89,90,91,97,98,0]):
    cell=src.crop((i%3*512,i//3*512,(i%3+1)*512,(i//3+1)*512));alpha=np.array(cell)[:,:,3];yy,xx=np.nonzero(alpha>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));im=cell.crop(bb);size=tuple(round(v*scale) for v in im.size);arr=quantize(im,size,rgb,128);yy,xx=np.nonzero(arr);ey,ex=np.nonzero((arr==7)&(np.indices(arr.shape)[0]<arr.shape[0]*.6));left=round(75-float(np.median(ex)));top=102-int(yy.max());canvas=np.zeros((160,160),np.uint8);canvas[top:top+size[1],left:left+size[0]]=arr;targets[n]=canvas;records.append({'frame':n,'source_cell':i,'source_crop':bb,'scale':scale,'offset':[left,top],'size':size})
for q in groups:
    n=q['frame']
    for k in q['aliases']:
        dx,dy=q['translations'][str(k)];v=np.zeros((160,160),np.uint8);yy,xx=np.nonzero(targets[n]);v[yy+dy,xx+dx]=targets[n][yy,xx];targets[k]=v
for n,v in targets.items():save_image(v.tobytes(),(160,160),words,out/f'frame_{n:03}.png')
frames=sorted({n for q in groups for n in q['aliases']});art={**old,'parent':str(parent.relative_to(ROOT)),'groups':groups,'remaining_frames':frames,'frames':[{'frame':n,'image':f'frame_{n:03}.png'} for n in frames],'revision_source_sha256':sha256((d/'generated_v1.png').read_bytes()),'normalization':records}
(out/'art.json').write_text(json.dumps(art,indent=2));sheet=Image.new('RGB',(6*256,3*288),'#253546');dr=ImageDraw.Draw(sheet)
items=[('ACCEPTED',d/'parent_000.png'),('ACCEPTED FIRE',d/'parent_085.png'),('GENERATED SCALE',out/'frame_000.png')]+[(f'NEW {n}',out/f'frame_{n:03}.png') for n in [89,90,91,97,98]]+[(f'OLD {n}',d/f'parent_{n:03}.png') for n in [89,90,91,97,98]]
for i,(label,path) in enumerate(items):
    im=Image.open(path).convert('RGBA').crop((48,40,112,104)).resize((256,256),Image.Resampling.NEAREST);x=i%6*256;y=i//6*288;sheet.paste(im,(x,y+25),im);dr.text((x+6,y+6),label,fill='white')
sheet.save(out/'comparison.png');print([(r['frame'],r['size'],r['offset']) for r in records]);print([(q['frame'],q['budget'],q['translations']) for q in groups])
