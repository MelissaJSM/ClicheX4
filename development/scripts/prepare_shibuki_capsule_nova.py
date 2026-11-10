"""Repair capsule silhouettes and Nova gaps inside the existing PS1 banks."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,binary_erosion,binary_fill_holes
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_ultimate_production import fast_fit,repack_parts
from scripts.prepare_shibuki_armor_remaining import pack_many
from scripts.prepare_shibuki_ultimate_idle import fit_tiles
from src.psx_player import graphics_bank,composition_frame,decode_stream,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank

D=ROOT/'work/ver_buki_riko/shibuki_art/ultimate_v1/effects_revision01'
PARENT=ROOT/'out/ver_buki_riko/shibuki_ultimate_production_20261027T114113006661Z'
PARENT_SHA='938b5f8ce69e1bddd6badbf656171ef3ec9ec4dad4a9957814c90659d2fb5e0b'
SOURCE_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'

def raster(g,c,gb,cb,n,size=(160,160)):
    f=graphics_bank(g,gb,allow_bank_aliases=True)['frames'][n]
    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    return canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(c,cb,n)),size=size)

def silhouette_frames(g,c,gb,cb,body,part=None):
    count=len(graphics_bank(g,gb,allow_bank_aliases=True)['frames'])
    old=[raster(g,c,gb,cb,n) for n in range(count)]
    if count==11:
        return fourth_silhouettes(old,body,part,gb)
    if count!=12:raise ValueError('Unknown capsule sequence')
    oldbody=binary_fill_holes(old[5]>0)
    body=binary_fill_holes(body)
    yy,xx=np.indices(body.shape)
    out=[]
    for n in range(12):
        if n==0:
            # Initial 32-pixel particles are not a player silhouette.
            out.append(old[0].copy());continue
        a=np.zeros(body.shape,np.uint8)
        if n<5:
            # Reproduce the native bottom-to-top scan and alternating stipple.
            cutoff=(90,88,72,56,0)[n]
            mask=body&(yy>=cutoff)&((xx+yy)%2==0)
            a[mask]=2
        elif n<=8:a[body]=1
        elif n==9:a[binary_dilation(body)&~body]=3
        elif n==10:
            a[binary_dilation(body)&~body]=1
        if n<=8:
            if 6<=n<=8:
                f=graphics_bank(g,gb,allow_bank_aliases=True)['frames'][n]
                raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
                cp=composition_frame(c,cb,n);cp={**cp,'parts':cp['parts'][len(composition_frame(c,cb,5)['parts']):]}
                sparks=canvas_from_parts(raw,f['tile_count'],local_composition(cp))
            else:
                sparks=old[n].copy();sparks[binary_dilation(oldbody,iterations=2)]=0
            a[sparks>0]=sparks[sparks>0]
        out.append(a)
    return out

def fourth_silhouettes(old,body,part,gb):
    body=binary_fill_holes(body);yy,xx=np.indices(body.shape)
    # The normal route first outlines the full player, then highlights only
    # the acquired clothing region. Keep that sequence and its blank frame.
    if gb==10:region=yy<76
    elif gb==11:region=(yy>=76)&(yy<91)
    elif gb==12:region=(yy>=76)&(yy<94)&((xx<72)|(xx>87))
    else:region=yy>=90
    pm=binary_fill_holes(part)&region
    if not np.any(pm):pm=body&region
    ys=np.nonzero(pm)[0];lo,hi=int(ys.min()),int(ys.max())
    oldpart=binary_dilation(binary_fill_holes(old[7]>0),iterations=2)
    out=[]
    for n in range(11):
        a=np.zeros(body.shape,np.uint8)
        if n==0:a[binary_dilation(body)&~body]=3
        elif n==1:
            a[binary_dilation(body,iterations=2)&~binary_dilation(body)]=3
            a[binary_dilation(body)&~body]=1
        elif 4<=n<=6:
            cutoff=hi-round((hi-lo+1)*(n-3)/4)
            a[pm&(yy>=cutoff)&((xx+yy+n)%2==0)]=1
        elif n>=7:
            a[pm]=1
            if n==8:
                a[pm&~binary_erosion(pm)]=3
                a[binary_erosion(pm)&~binary_erosion(pm,iterations=2)]=2
        if n>=3 and n!=8:
            sparks=old[n].copy();sparks[oldpart]=0;a[sparks>0]=sparks[sparks>0]
        out.append(a)
    return out

def packed_bank(g,c,gb,cb,images):
    b=graphics_bank(g,gb,allow_bank_aliases=True);f=b['frames'][0]
    if len({x['offset'] for x in b['frames']})!=1:raise ValueError('Expected one capsule stream')
    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    limits=[len(composition_frame(c,cb,n)['parts']) for n in range(len(images))]
    if len(images)==12:
        inherited={}
        for n in (0,6,7,8):
            qs=composition_frame(c,cb,n)['parts']
            if n:qs=qs[len(composition_frame(c,cb,5)['parts']):]
            inherited[n]=[(q['tile'],q['x']+80,q['y']+80,c[q['record_offset']]&192) for q in qs]
        nr,assign=pack_capsule_patterns(raw,f['tile_count'],images,limits,inherited)
    else:nr,assign=pack_many(raw,f['tile_count'],images,set(range(f['tile_count'])),limits)
    budget=b['end']-b['base']-len(images)*4
    if len(encode_stream(nr))>budget:
        nr,mapping,flips,_,_=fit_tiles(nr,f['tile_count'],range(f['tile_count']),budget)
        assign=[[(mapping[t],x,y,flag^flips.get(t,0)) for t,x,y,flag in rr] for rr in assign]
    parts={}
    for n,(rr,limit) in enumerate(zip(assign,limits)):
        if not rr or len(rr)>limit:raise ValueError('Capsule part budget exceeded')
        if len(images)==12 and 6<=n<=8:
            extra=len(inherited[n]);bodyrr=rr[:-extra]
            rr=bodyrr+[bodyrr[-1]]*(limits[5]-len(bodyrr))+rr[-extra:]
        rr=rr+[rr[-1]]*(limit-len(rr))
        parts[n]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80) for t,x,y,flag in rr)
    nc,slack=repack_parts(c,cb,parts)
    code=encode_stream(nr)
    if len(code)>b['end']-b['base']-len(images)*4:raise ValueError(f'Capsule bank {gb} encoded {len(code)} > {b["end"]-b["base"]-len(images)*4}')
    ng,proof=repack_graphics_bank(g,gb,{n:code for n in range(len(images))})
    for n,a in enumerate(images):
        if not np.array_equal(raster(ng,nc,gb,cb,n),a):raise ValueError('Capsule pixels differ after packing')
    return ng,nc,{'bank':gb,'parts_bank':cb,'frames':len(images),'encoded_bytes':len(code),'graphics_slack':proof['remaining_slack'],'parts_slack':slack}

def pack_capsule_patterns(raw,count,images,limits,inherited):
    best=None;minimum=999;failed={}
    protected={r[0] for rr in inherited.values() for r in rr}
    for dy in range(16):
        for dx in range(16):
            patterns=[];records=[];valid=True
            for n,(a,limit) in enumerate(zip(images,limits)):
                layers=[] if n==0 else [images[5]] if 6<=n<=8 else [a]
                rr=[]
                for li,layer in enumerate(layers):
                    ys,xs=np.nonzero(layer)
                    if len(xs)==0:continue
                    if n==0 or li==1:
                        rects=fast_fit(layer>0,limit-len(rr))
                        if rects is None:valid=False;break
                    else:
                        cells=sorted(set(zip(((xs-dx)//16).tolist(),((ys-dy)//16).tolist())))
                        rects=[(tx*16+dx,ty*16+dy) for tx,ty in cells]
                    remain=layer.copy()
                    for x,y in rects:
                        patch=remain[y:y+16,x:x+16].copy();remain[y:y+16,x:x+16]=0
                        py,px=np.nonzero(patch)
                        if not len(px):continue
                        left,top,right,bottom=int(px.min()),int(py.min()),int(px.max()+1),int(py.max()+1)
                        compact=patch[top:bottom,left:right];key=(compact.shape,compact.tobytes())
                        if key not in patterns:patterns.append(key)
                        rr.append((patterns.index(key),x+left,y+top))
                if not rr and n!=0:
                    key=((1,1),b'\0')
                    if key not in patterns:patterns.append(key)
                    rr=[(patterns.index(key),64,64)]
                if len(rr)+len(inherited.get(n,[]))>limit or not valid:
                    failed[n]=failed.get(n,0)+1;valid=False;break
                records.append(rr)
            if valid:minimum=min(minimum,len(patterns))
            if valid and len(patterns)<=count-len(protected):
                try:candidate=store_capsule_patterns(raw,count,patterns,records,protected,inherited)
                except ValueError:continue
                score=(len(encode_stream(candidate[0])),len(patterns),sum(map(len,records)))
                if best is None or score<best[0]:best=(score,*candidate)
    if best is None:raise ValueError(f'Shared capsule grid does not fit: minimum patterns {minimum}, failed {failed}')
    return best[1],best[2]

def store_capsule_patterns(raw,count,patterns,records,protected,inherited):
    ids=sorted(set(range(count))-protected,key=lambda t:(t%16==0,t));chosen={};used=set()
    for k,(shape,data) in sorted(enumerate(patterns),key=lambda v:v[1][0][1],reverse=True):
        tile=next((t for t in ids if t not in used and (t%16 or shape[1]<16)),None)
        if tile is None:raise ValueError('Capsule unsafe texture edge')
        chosen[k]=(tile,0 if tile%16 else 1);used.add(tile)
    result=bytearray(raw);_,locations,_=indexed_atlas(raw,count)
    for tile in set(range(count))-protected:
        for y in range(16):
            for x in range(16):
                pos,shift=locations[(tile//16*16+y)*256+tile%16*16+x];result[pos]&=~(15<<shift)
    for k,(shape,data) in enumerate(patterns):
        tile,pad=chosen[k];a=np.frombuffer(data,np.uint8).reshape(shape)
        for y,x in np.argwhere(a):
            pos,shift=locations[(tile//16*16+int(y))*256+tile%16*16+int(x)+pad]
            result[pos]|=int(a[y,x])<<shift
    return bytes(result),[[(chosen[k][0],x-chosen[k][1],y,0) for k,x,y in rr]+inherited.get(n,[]) for n,rr in enumerate(records)]

def main(out):
    out=out.resolve()
    if not out.is_relative_to(D) or out.exists():raise ValueError('Fresh isolated output required')
    if digest(PARENT/'shibuki_riko.bin')!=PARENT_SHA or digest(ROOT/'MegaMan X4.bin')!=SOURCE_SHA:raise ValueError('Wrong source')
    inv=json.loads((ROOT/'work/ver_buki_riko/art_pilot/illustrations_v1/archive_inventory.json').read_text())
    records={r['name'].split(';')[0]:r for r in inv if r['name'].split(';')[0] in ('PL00_U.ARC','PL02_U.ARC')}
    with (PARENT/'shibuki_riko.bin').open('rb') as stream:
        reader=DiscReader(stream,(PARENT/'shibuki_riko.bin').stat().st_size)
        inputs={n:reader.read(r['lba'],r['size']) for n,r in records.items()}
    out.mkdir();proofs=[];previews=[];changed={}
    words=[0,0xffff,0xfdc8,0xe920]+[0x8000]*12
    for name,arc in inputs.items():
        ultimate=name=='PL02_U.ARC';g=entry(arc,2);c=entry(arc,3);oldg,oldc=g,c
        base=raster(g,c,0,0,0)
        full=base.copy()
        for bi in (8,5,7,6):
            layer=raster(g,c,0,bi,0);full[layer>0]=layer[layer>0]
        for gb in range(10,14):
            part=raster(oldg,oldc,0,{10:5,11:6,12:7,13:8}[gb],0)>0
            body=full>0 if ultimate else (base>0)|part
            targets=silhouette_frames(g,c,gb,gb+8,body,part)
            g,c,proof=packed_bank(g,c,gb,gb+8,targets);proof['file']=name;proofs.append(proof)
            for n,a in enumerate(targets):
                im=save_image(a.tobytes(),(160,160),words,out/f'{name}_b{gb}_{n:02}.png').convert('RGBA')
                if gb==10:previews.append((f'{name} capsule {n}',im))
        if ultimate:
            n=220;before=raster(g,c,0,5,n,(256,160));original=(D.parent/'analysis/original_PL02_U.ARC').read_bytes()
            original_shape=raster(entry(original,2),entry(original,3),0,5,n,(256,160))>0
            fill=(before==0)&binary_fill_holes(original_shape)
            generated=Image.open(D/'nova_gap_generated.png').convert('RGBA').resize((1024,640),Image.Resampling.NEAREST)
            pixels=np.array(generated);pal=struct.unpack_from('<16H',entry(arc,9),32)
            energy_ids=np.array([7,8,14]);rgb=np.array([[(pal[i]>>s&31)*255//31 for s in (0,5,10)] for i in energy_ids])
            target=before.copy()
            for y,x in np.argwhere(fill):
                gy,gx=min(639,int(y)*4+182),min(1023,int(x)*4+14)
                color=pixels[gy,gx,:3].astype(np.int32)
                target[y,x]=int(energy_ids[np.argmin(((rgb-color)**2).sum(1))]) if pixels[gy,gx,3]>=128 else 7
            if not np.array_equal(target[before>0],before[before>0]) or np.any(fill&(target==0)):raise ValueError('Nova body preservation or gap fill failed')
            f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            protected={q['tile'] for bi in (0,6,7,8) for q in composition_frame(c,bi,n)['parts']}
            limit=len(composition_frame(c,5,n)['parts'])
            nr,aa=pack_many(raw,f['tile_count'],[target],set(range(f['tile_count']))-protected,[limit]);rr=aa[0]
            rr=rr+[rr[-1]]*(limit-len(rr));cc=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80) for t,x,y,flag in rr)
            c,slack=repack_parts(c,5,{n:cc});g,rep=repack_graphics_bank(g,0,{n:encode_stream(nr)})
            if not np.array_equal(raster(g,c,0,5,n,(256,160)),target):raise ValueError('Nova roundtrip failed')
            for label,a in [('before',before),('after',target)]:
                im=save_image(a.tobytes(),(256,160),pal,out/f'nova_{label}.png').convert('RGBA');previews.append(('Nova '+label,im))
            proofs.append({'file':name,'nova_frame':220,'filled_pixels':int(fill.sum()),'old_opaque_pixels_preserved':int(np.count_nonzero(before)),'parts_slack':slack,'graphics_slack':rep['remaining_slack'],'generated_sha256':digest(D/'nova_gap_generated.png')})
        protected=decoded=0
        for bi in range(len(bank_offsets(oldg,allow_aliases=True))):
            ob=graphics_bank(oldg,bi,allow_bank_aliases=True);nb=graphics_bank(g,bi,allow_bank_aliases=True)
            for old,new in zip(ob['frames'],nb['frames']):
                a=decode_stream(oldg,old['offset'],old['limit'],old['tile_count']*128).data;b=decode_stream(g,new['offset'],new['limit'],new['tile_count']*128).data;decoded+=1
                if bi not in range(10,14) and not (ultimate and bi==0 and old['index']==220):
                    if a!=b:raise ValueError('Non-target graphics changed')
                    protected+=1
        for bi in range(len(bank_offsets(c))):
            count=composition_frame(c,bi,0)['bank_frame_count']
            for n in range(count):
                if bi in range(18,22) or (ultimate and bi==5 and n==220):continue
                def cpdata(src):return b''.join(src[p['record_offset']:p['record_offset']+4] for p in composition_frame(src,bi,n)['parts'])
                if cpdata(oldc)!=cpdata(c):raise ValueError('Non-target composition changed')
        result=replace_entry(replace_entry(arc,2,g),3,c)
        for e in psx_arc(arc):
            k=int(e['type'],16)
            if k not in (2,3) and entry(arc,k)!=entry(result,k):raise ValueError('Non-graphics entry changed')
        (out/name).write_bytes(result);changed[name]={'before':sha256(arc),'after':sha256(result),'decoded':decoded,'protected_graphics':protected,'size':len(result)}
    sheet=Image.new('RGB',(6*240,5*240),'#253546');draw=ImageDraw.Draw(sheet)
    for i,(label,im) in enumerate(previews):
        x=i%6*240;y=i//6*240;crop=im.crop((40,35,120 if im.width==160 else 185,120));crop.thumbnail((230,210),Image.Resampling.NEAREST);scale=min(230//crop.width,210//crop.height);crop=crop.resize((crop.width*max(1,scale),crop.height*max(1,scale)),Image.Resampling.NEAREST);sheet.paste(crop,(x,y+25),crop);draw.text((x+3,y+4),label,fill='white')
    sheet.save(out/'review.png')
    recipe={'kind':'capsule_silhouettes_and_nova_gap_fix','parent':str(PARENT.relative_to(ROOT)),'parent_sha256':PARENT_SHA,'files':changed,'records':records,'checks':proofs,'exe_changed':False,'timing_changed':False,'runtime_verified':False}
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2));print(json.dumps(recipe,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
