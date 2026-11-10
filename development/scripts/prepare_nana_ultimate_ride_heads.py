"""조종석의19머리를 수용 얼티밋 머리로 교체하고 공유 빈198을 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full
from scripts.prepare_nana_ultimate_run import verify
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts
from scripts.prepare_nana_fourth_vehicle_art import translate
from scripts.prepare_riko_ui import replace_entry
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_hover_alignment_20261104T122102313560Z'
PARENT_SHA='c7d7ec32e7887ddb778762001303fdea399f686add25210909d13ab1e19cae9d'
ARC_SHA='0ded0624f058e39cc417c94c626fb6a98c85f3caeead63e987dd5100096d42ec'
FRAMES=list(range(184,204));EDITED_FRAMES=[n for n in FRAMES if n!=198]
HEADS={184:0,193:37,195:94,196:0,199:0}

def artwork(out):
    arc=(PARENT/'PL02_U.ARC').read_bytes();c,g=entry(arc,3),entry(arc,2);bank=graphics_bank(g,0,allow_bank_aliases=True);words=struct.unpack_from('<16H',entry(arc,9),32);targets={};overlays={};proof=[];yy,xx=np.indices((160,160))
    for n,source in HEADS.items():
        base=render(arc,n)[1];by,bx=np.nonzero(base==14);ex,ey=round(float(bx.mean())),round(float(by.mean()));sb=full(arc,source);sy,sx=np.nonzero((sb==14)&(yy<74));sx,sy=round(float(np.median(sx))),round(float(np.median(sy)));head=full(arc,source)[sy-16:sy+8,sx-9:sx+13];piece=np.array(Image.fromarray(head).resize((15,16),Image.Resampling.NEAREST));cx,cy=round(9*15/22),round(16*16/24);piece[cy,cx]=14;dx,dy=ex-cx,ey-cy;overlay=np.zeros_like(base);overlay[dy:dy+16,dx:dx+15]=piece;f=bank['frames'][n];aliases=[q['index']for q in bank['frames']if q['offset']==f['offset']];p0=composition_frame(c,0,n)['parts'][0]
        for v in aliases:
            native=render(arc,v)[1]
            if v==198:
                require(not full(arc,v).any(),'Shared198 not blank');targets[v]=native;overlays[v]=np.zeros_like(base);proof.append(dict(frames=[v,v],blank_preserved=True,pistol_present=False,pistol_mask_bbox=None));continue
            p=composition_frame(c,0,v)['parts'][0];tx,ty=p['x']-p0['x'],p['y']-p0['y'];require(np.array_equal(native,translate(base,tx,ty)),'Head alias is not translation');ov=translate(overlay,tx,ty);targets[v]=np.where(ov,ov,native).astype(np.uint8);overlays[v]=ov;proof.append(dict(frames=[v,v],accepted_head_source=source,shared_head_frame=n,translation=[tx,ty],head_source_box=[sx-9,sy-16,sx+13,sy+8],head_size=[15,16],head_box=[dx+tx,dy+ty,dx+tx+15,dy+ty+16],eye=[ex+tx,ey+ty],pistol_present=False,pistol_mask_bbox=None))
    board=Image.new('RGB',(1600,640),'#46545c');draw=ImageDraw.Draw(board)
    for n in FRAMES:save_image(targets[n].tobytes(),(160,160),words,out/f'ultimate_{n:03}.png');save_image(overlays[n].tobytes(),(160,160),words,out/f'head_overlay_{n:03}.png')
    for i,n in enumerate(HEADS):
        for j,v in enumerate((full(arc,n),targets[n])):
            im=save_image(v.tobytes(),(160,160),words,out/f'review_{n}_{j}.png').convert('RGBA');ys,xs=np.nonzero(render(arc,n)[1]);cx,cy=round(float(xs.mean())),round(float(ys.mean()));pic=im.crop((cx-20,cy-24,cx+20,cy+16)).resize((320,320),Image.Resampling.NEAREST);board.paste(pic,(i*320,j*320),pic);draw.text((i*320+4,j*320+4),str(n)+(' BEFORE'if not j else' AFTER'),fill='white')
    board.save(out/'ride_heads_review.png');return targets,overlays,sorted(proof,key=lambda q:q['frames'][0])

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,overlays,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    arc=(PARENT/'PL02_U.ARC').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};changes={};packing=[]
    for n in HEADS:
        f=bank['frames'][n];ns=[q['index']for q in bank['frames']if q['offset']==f['offset']];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;keep={p['tile']for v in ns for b in(0,6,7,8)for p in composition_frame(c,b,v)['parts']};keep|={p['tile']for v in ns if v==198 for p in composition_frame(c,5,v)['parts']};pool={t for t in range(f['tile_count'])if t not in keep and t%16!=0};new,rr=pack_shared(raw,f['tile_count'],[overlays[n]],pool,[len(pool)])
        for v in ns:
            replacements[v]=encode_stream(new)
            if v==198:continue
            q=next(q for q in proof if q['frames'][0]==v);dx,dy=q['translation'];changes[v]=b''.join(struct.pack('<BBbb',fl,t,x+dx-80,y+dy-80)for t,x,y,fl in rr[0])
        packing.append(dict(frames=ns,free_tiles=len(pool),parts=len(rr[0])))
    nc,slack=repack_parts(c,5,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc);check=verify(arc,result,targets,{});require(np.array_equal(full(arc,198),full(result,198)),'Blank198 changed');(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_ride_heads',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,frames=FRAMES,edited_frames=EDITED_FRAMES,registration=proof,packing=packing,graphics_repack=rep,parts_bank5_remaining=slack,verification=check,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=check)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
