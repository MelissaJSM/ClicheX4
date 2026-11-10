"""호버 양발 접점을 각각 등록한다. 기존 인덱스 도트와 상체를 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.spatial import Delaunay
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_ultimate_hover_reference import CUTS
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_hover_20261104T120316558213Z'
PARENT_SHA='54169838524b72f87639236292c7e7a246902712c18e9eb3080133d465a04abe'
ARC_SHA='4a1c0066990f0ba3517a14a97b005dc0bc6a8c53fa7874858d7f6dca2d5acc55'
FRAMES=list(range(221,225));ORDER=FRAMES[::2]
# Each compact sneaker is registered independently against the visible core
# start and original Ultimate heel in hover_alignment_v1 comparison evidence.
FEET={221:[([81,92,87,99],[0,-2]),([92,99,99,106],[-2,-8])],
      223:[([83,92,90,99],[-5,-3]),([92,99,99,106],[-1,-8])]}

def registered_lower(old,n):
    cut=CUTS[n];src=[[0,cut-1],[159,cut-1],[0,159],[159,159]];dst=[p.copy()for p in src]
    for x in range(56,113,4):src.append([x,cut-1]);dst.append([x,cut-1])
    for box,delta in FEET[n]:
        x,y,x2,y2=box;dx,dy=delta
        for px,py in((x,y),(x2-1,y),(x,y2-1),(x2-1,y2-1)):
            src.append([px,py]);dst.append([px+dx,py+dy])
    src=np.array(src,float);dst=np.array(dst,float);tri=Delaunay(dst);yy,xx=np.indices(old.shape);points=np.c_[xx.ravel(),yy.ravel()];ids=tri.find_simplex(points);valid=(ids>=0)&(points[:,1]>=cut);q=points[valid];simp=ids[valid];b=np.einsum('ijk,ik->ij',tri.transform[simp,:2],q-tri.transform[simp,2]);weights=np.c_[b,1-b.sum(1)];mapped=np.einsum('ij,ijk->ik',weights,src[tri.simplices[simp]]);coords=np.rint(mapped).astype(int);require(np.all((coords>=0)&(coords<160)),'Lower registration outside canvas');result=old.copy();result[cut:]=0;result.reshape(-1)[np.flatnonzero(valid)]=old[coords[:,1],coords[:,0]]
    for box,delta in FEET[n]:
        x,y,x2,y2=box;dx,dy=delta;require(np.array_equal(result[y+dy:y2+dy,x+dx:x2+dx],old[y:y2,x:x2]),'Shoe detail changed')
    require(np.array_equal(result[:cut],old[:cut]),'Upper changed');return result,dict(source_points=src.tolist(),destination_points=dst.tolist(),shoes=[dict(source_box=box,translation=delta)for box,delta in FEET[n]])

def artwork(out):
    arc=(PARENT/'PL02_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.uint8);targets={};proof=[];oldmeta=json.loads((PARENT/'ultimate_hover/registration.json').read_text('utf8'))
    for n in ORDER:
        old=full(arc,n);new,reg=registered_lower(old,n);cut=CUTS[n];shot=full(arc,n+1);require(np.array_equal(old[cut:],shot[cut:]),'Source legs not shared');targets[n]=new;targets[n+1]=shot.copy();targets[n+1][cut:]=new[cut:]
        for f in(n,n+1):save_image(targets[f].tobytes(),(160,160),words,out/f'ultimate_{f:03}.png')
        box=next(q for q in oldmeta if q['frames'][0]==n)['pistol_mask_bbox'];proof.append(dict(frames=[n,n+1],upper_preserved_before_y=cut,pistol_present=True,pistol_mask_bbox=box,registration=reg,changed_lower_pixels=int(np.count_nonzero(new!=old))))
    board=Image.new('RGB',(640,760),'#34414a');draw=ImageDraw.Draw(board)
    for i,n in enumerate(ORDER):
        jets=Image.open(D/f'hover_alignment_v1/jets_{n}.png').convert('RGBA')
        for j,v in enumerate((full(arc,n),targets[n])):
            body=Image.fromarray(np.concatenate((rgb[v],((v>0)*255).astype(np.uint8)[...,None]),2));canvas=Image.new('RGBA',(160,160));canvas.alpha_composite(jets);canvas.alpha_composite(body);im=canvas.crop((48,44,112,116)).resize((320,360),Image.Resampling.NEAREST);board.paste(im,(i*320,j*380+20),im);draw.text((i*320+4,j*380+4),str(n)+(' BEFORE'if not j else' AFTER (jet composite)'),fill='white')
    board.save(out/'hover_alignment_review.png');return targets,proof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack_resources((PARENT/'PL02_U.ARC').read_bytes(),targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_hover_alignment',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,frames=FRAMES,registration=proof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
