"""C04 나나 포스 노바의 원작 X 본체 누락을 기존 파츠/이펙트 구조 안에서 교정한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt,binary_dilation,binary_fill_holes
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_inventory import BUILDS,load,entry
from scripts.prepare_riko_ui import replace_entry
from scripts.overhaul_sprites_audit import sha
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.prepare_shibuki_armor_remaining import pack_many
from scripts.prepare_nana_fourth_run import pack_layers
from scripts.overhaul_ui_nova_art import D,EYES
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,bank_offsets,indexed_atlas
from src.psx_compress import encode_stream,replace_stream
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition

FRAMES=[213,214,215,216,217,220]
SIZE=(256,160)
def require(value,msg):
    if not value:raise ValueError(msg)
def image(arc,b,n):return raster(entry(arc,2),entry(arc,3),0,b,n,SIZE)

def pack_effect_original_grid(raw,count,target,comp):
    """Reuse native wide-effect rectangles, including vertical pattern sharing."""
    patterns=[];records=[]
    for p in comp['parts']:
        x,y=p['x']+80,p['y']+80;v=target[y:y+16,x:x+16]
        variants=[(v.tobytes(),0),(v[:,::-1].tobytes(),64),(v[::-1].tobytes(),128),(v[::-1,::-1].tobytes(),192)]
        key,flag=min(variants)
        if key not in patterns:patterns.append(key)
        records.append((patterns.index(key),x,y,flag))
    ids=[t for t in range(count)if t%16][:len(patterns)]
    require(len(ids)==len(patterns),'Native effect pattern capacity exceeded')
    changed=bytearray(raw);_,locations,_=indexed_atlas(raw,count)
    for key,t in zip(patterns,ids):
        v=np.frombuffer(key,np.uint8).reshape(16,16)
        for y in range(16):
            for x in range(16):
                pos,shift=locations[(t//16*16+y)*256+t%16*16+x]
                changed[pos]=(changed[pos]&~(15<<shift))|(int(v[y,x])<<shift)
    return bytes(changed),[[(ids[k],x,y,flag)for k,x,y,flag in records]]

def targets(arc):
    meta=json.loads((D/'prepared.json').read_text('utf8'))
    require(meta['source_sha256']==sha((D/'generated.png').read_bytes()),'Generated source changed')
    require(meta['palette_words']==list(struct.unpack_from('<16H',entry(arc,9),32)),'Art palette changed')
    for name,expected in meta['images'].items():
        require(sha((D/name).read_bytes())==expected,'Indexed art changed')
        im=Image.open(D/name)
        require(im.mode=='P'and im.size==SIZE and im.info.get('transparency')==0 and max(im.tobytes())<=15,'Invalid indexed art')
    original={n:image(arc,0,n)for n in range(213,221)}
    base={};full={};proof=[]
    for n in (213,215,217):
        b=np.array(Image.open(D/f'base_{n}.png'));f=np.array(Image.open(D/f'fourth_{n}.png'))
        dist,idx=distance_transform_edt(b==0,return_indices=True)
        outside=(b>0)&(f==0);missing=(f>0)&(b==0)
        require(float(dist[missing].max(initial=0))<=6,'Paired body silhouettes disagree excessively')
        # Both clothing variants must cover the same body: transparent armor
        # cannot erase the underlying basic layer. Register the basic texture
        # on the accepted Fourth silhouette and retain exact eye/face anchor.
        boundary=b[tuple(idx[:,missing])].copy();b[outside]=0;b[missing]=boundary
        require(np.array_equal(b>0,f>0),'Common native silhouette mismatch')
        base[n]=b;full[n]=f
        proof.append({'frame':n,'common_silhouette':'approved Fourth pose','basic_pixels_outside_removed':int(outside.sum()),
                      'basic_boundary_pixels_registered':int(missing.sum()),'max_boundary_distance':float(dist[missing].max(initial=0)),'eye':EYES[n]})
    for n in (214,216):base[n]=base[n-1].copy();full[n]=full[n-1].copy()
    # Native windup arc is separate from the body, retain its exact positions.
    arc_mask=(original[213]==0)&(original[214]>0)
    for dest in (base,full):dest[214][arc_mask]=original[214][arc_mask]
    # Conform the tiny close-fitting charge outline to the new body. The outer
    # high-speed streak frames218/219 are left entirely unchanged.
    body=base[217]>0;ring=binary_dilation(body,iterations=1)&~body
    for dest in (base,full):dest[217][ring]=9
    # Locate native body217 inside220 by exact indexed overlap, then remove
    # that old body only. Keep every outer effect pixel outside its mask.
    scores=[]
    for dy in range(-4,5):
        for dx in range(-16,17):
            shifted=np.roll(np.roll(original[217],dy,0),dx,1)
            scores.append((int(np.count_nonzero((shifted>0)&(shifted==original[220]))),-abs(dx)-abs(dy),dx,dy))
    _,_,dx,dy=max(scores)
    oldmask=binary_dilation(np.roll(np.roll(original[217]>0,dy,0),dx,1),iterations=1)
    envelope=binary_fill_holes(original[220]>0)
    for dest in (base,full):
        newbody=np.roll(np.roll(dest[217],dy,0),dx,1);target=original[220].copy()
        target[oldmask]=0;target[oldmask&envelope]=9;target[newbody>0]=newbody[newbody>0];dest[220]=target
        keep=~oldmask&(newbody==0)
        require(np.array_equal(target[keep],original[220][keep]),'Outer Nova streak changed')
        require(not np.any(envelope&(target==0)),'Nova effect envelope has a gap')
    layers={};yy,xx=np.indices(base[213].shape)
    for n in FRAMES:
        source=213 if n==214 else 215 if n==216 else 217 if n==220 else n
        ex,ey=EYES[source];ex+=dx if n==220 else 0;ey+=dy if n==220 else 0
        # Headwear is one native16x16 tile in the preparation frames.
        head=(xx>=ex-7)&(xx<ex+9)&(yy>=ey-12)&(yy<ey+4)
        leg=((yy>=ey+17)|((xx>=ex+9)&(yy>=ey-12)))if source!=217 else((xx>=ex+21)&(yy>=ey+5))|((xx>=ex+9)&(yy<ey+6))
        arm=(xx<ex+1)&(yy>=ey+3)&(yy<ey+19)
        if source==215:arm|=(xx<ex+1)&(yy<ey-3)
        remaining=np.where(full[n]!=base[n],full[n],0).astype(np.uint8)
        layers[n]={k:np.zeros_like(remaining)for k in(5,6,7,8)}
        for k,mask in ((5,head),(8,leg),(7,arm)):
            layers[n][k][mask]=remaining[mask];remaining[mask]=0
        layers[n][6]=remaining
        merge=base[n].copy()
        for k in(8,5,7,6):merge=np.where(layers[n][k],layers[n][k],merge)
        require(np.array_equal(merge,full[n]),'Partial layer split does not reproduce full form')
    return base,full,layers,{'registration':proof,'frame214_outer_arc_exact':True,'frame216_shared_preparation_body':215,
        'nova220_body_translation':[dx,dy],'nova218_219_entirely_preserved':True}

def patch(arc):
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);base,full,layers,proof=targets(arc)
    nc=bytearray(c);groups={};raws={};packing=[]
    for n in FRAMES:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
    for offset,ids in groups.items():
        print(json.dumps({'packing_frames':ids}),flush=True)
        f=bank['frames'][ids[0]];require([q['index']for q in bank['frames']if q['offset']==offset]==ids,'Unselected graphics alias')
        raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
        original_pool={p['tile']for n in ids for p in composition_frame(c,0,n)['parts']}
        pool=set(sorted(range(f['tile_count']),key=lambda t:(t%16==0,t))[:max(11,len(original_pool))])
        limits=[len(composition_frame(c,0,n)['parts'])for n in ids]
        if ids==[220]:raw,rr=pack_effect_original_grid(raw,f['tile_count'],base[220],composition_frame(c,0,220))
        else:raw,rr=pack_many(raw,f['tile_count'],[base[n]for n in ids],pool,limits)
        allocated=[('base',0,rr,{t for r in rr for t,x,y,flag in r})]
        free=set(range(f['tile_count']))-allocated[0][3]
        if ids==[220]:
            require(free=={0,16,24,25,26,27,28},'Nova effect free tile layout changed')
            others=[]
            for name,k,tiles in [('head',5,{0}),('body',6,{24,25,26}),('arm',7,{16}),('leg',8,{27,28})]:
                raw,r=pack_many(raw,f['tile_count'],[layers[220][k]],tiles,[len(composition_frame(c,k,220)['parts'])])
                others.append((name,k,r,{t for rr in r for t,x,y,fl in rr}))
        else:raw,others=pack_layers(raw,f['tile_count'],layers,ids,free,c)
        allocated+=others
        for name,k,records,tiles in allocated:
            for n,parts in zip(ids,records):
                co=composition_frame(c,k,n);require(len(parts)<=len(co['parts']),'Part count expanded')
                for i,p in enumerate(co['parts']):
                    t,x,y,fl=parts[min(i,len(parts)-1)];pos=p['record_offset']
                    nc[pos:pos+4]=struct.pack('<BBbb',fl,t,x-80,y-80)
                expected=base[n]if k==0 else layers[n][k]
                a=canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(nc,k,n)),size=SIZE)
                require(np.array_equal(a,expected),f'Packed layer differs {n}/{k}')
        raws[offset]=raw
        packing.append({'frames':ids,'tiles':f['tile_count'],'allocation':[{'bank':k,'parts':[len(r)for r in records],'tiles':sorted(tiles)}for _,k,records,tiles in allocated]})
    # Prefer exact slots. If a new body needs extra capacity, only the compact
    # contiguous Nova region is eligible; all earlier locomotion slots stay put.
    changes=bytearray(g);compression=[];needs_repack=False
    for start,raw in raws.items():
        f=next(q for q in bank['frames']if q['offset']==start);code=encode_stream(raw)
        old=decode_stream(g,start,f['limit'],f['tile_count']*128)
        if len(code)>f['limit']-start:needs_repack=True
        compression.append({'frames':groups[start],'old_offset':start,'new_bytes':len(code),'capacity':f['limit']-start,'old_bytes':old.end-start})
    if not needs_repack:
        for start,raw in raws.items():
            f=next(q for q in bank['frames']if q['offset']==start);changes=bytearray(replace_stream(bytes(changes),f,raw,allocated_limit=f['limit'])[0])
    else:
        start=bank['frames'][213]['offset'];end=bank['frames'][220]['limit'];cursor=start;locations={}
        for f in bank['frames'][213:221]:
            old=f['offset']
            if old in locations:continue
            dec=decode_stream(g,old,f['limit'],f['tile_count']*128)
            code=encode_stream(raws[old])if old in raws else g[old:dec.end]
            require(cursor+len(code)<=end,'Native Nova region capacity exceeded')
            changes[cursor:cursor+len(code)]=code;locations[old]=cursor;cursor+=len(code)
        for f in bank['frames'][213:221]:struct.pack_into('<I',changes,bank['base']+4*f['index'],f['tile_count']<<20|(locations[f['offset']]-bank['base']))
        proof['limited_repack']={'region':[start,end],'used':cursor-start,'free':end-cursor,'locations':locations}
    result=replace_entry(replace_entry(arc,2,bytes(changes)),3,bytes(nc));ng=entry(result,2);newparts=entry(result,3)
    preserved=checked=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        for a,b in zip(graphics_bank(g,bi,allow_bank_aliases=True)['frames'],graphics_bank(ng,bi,allow_bank_aliases=True)['frames']):
            old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data;checked+=1
            require(a['tile_count']==b['tile_count'],'Tile count changed')
            if bi==0 and a['index']in FRAMES:require(new==raws[a['offset']],'New selected stream differs')
            else:require(old==new,'Protected stream differs');preserved+=1
            if bi!=0 or not 213<=a['index']<=220:require(a['offset']==b['offset'],'Unrelated stream moved')
    compcount=0
    for k in range(len(bank_offsets(c))):
        for n in range(composition_frame(c,k,0)['bank_frame_count']):
            if k in(0,5,6,7,8)and n in FRAMES:continue
            require(composition_frame(c,k,n)==composition_frame(newparts,k,n),'Protected composition changed');compcount+=1
    for n in FRAMES:
        for k in(0,5,6,7,8):require(np.array_equal(image(result,k,n),base[n]if k==0 else layers[n][k]),'Final layer differs')
    require(entry(result,9)==entry(arc,9)and len(result)==len(arc),'Palette/size changed')
    proof.update(decoded_references_checked=checked,decoded_references_preserved=preserved,changed_references=FRAMES,
        protected_compositions=compcount,packing=packing,compression=compression,part_counts_unchanged=True,
        runtime_verified=False,palette_timing_logic_preserved=True,art_provenance=json.loads((D/'prepared.json').read_text('utf8')),
        source_prompt=(D/'prompt.txt').relative_to(ROOT).as_posix())
    return result,proof,base,full,layers

def main(output):
    out=output.resolve();require(out.is_relative_to(D.parent)and not out.exists(),'Fresh isolated output required')
    assets,records=load('ver_rin_nana');arc=assets['PL00_U.ARC'];result,proof,base,full,layers=patch(arc)
    out.mkdir();(out/'PL00_U.ARC').write_bytes(result)
    words=struct.unpack_from('<16H',entry(arc,9),32);board=Image.new('RGB',(3*384,3*352),(28,34,45));draw=ImageDraw.Draw(board)
    for i,n in enumerate(FRAMES):
        im=save_image(full[n].tobytes(),SIZE,words,out/f'full_{n}.png').convert('RGBA')
        pic=im.crop((32,40,128,128)).resize((384,352),Image.Resampling.NEAREST);board.paste(pic,((i%3)*384,(i//3)*352),pic);draw.text(((i%3)*384+4,(i//3)*352+4),str(n),fill='white')
        for k in(0,5,6,7,8):save_image((base[n]if k==0 else layers[n][k]).tobytes(),SIZE,words,out/f'layer{k}_{n}.png')
    board.save(out/'packed_review.png')
    proposal={'project':'ver_rin_nana','baseline':BUILDS['ver_rin_nana'][0],'baseline_sha256':BUILDS['ver_rin_nana'][1],
        'files':{'PL00_U.ARC':{'before':sha(arc),'after':sha(result),'size':len(result),'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),
                             'record':records['PL00_U.ARC'],'changed_bytes':sum(a!=b for a,b in zip(arc,result))}},
        'issues':['C-04'],'checks':proof,'runtime_verified':False}
    for name,obj in [('proposal.json',proposal),('verification.json',proof)]: (out/name).write_text(json.dumps(obj,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(out),'sha256':sha(result),'checks':proof}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
