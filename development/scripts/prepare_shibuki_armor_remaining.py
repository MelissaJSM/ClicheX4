"""기본형 타일을 보존하고 남은 아머 파츠를 원래 슬롯에 재삽입한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json
from scripts.discover_inputs import psx_arc,sha256
from scripts.analyze_shibuki_armor import entries
from scripts.prepare_shibuki_armor_motion import fit,identical,variants
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank
LAYERS={'head':5,'body':6,'arm':7,'leg':8}
PARENT='out/ver_buki_riko/shibuki_fourth_run_20261027T010834425294Z'
PARENT_HASH='5ed5b83cb1288264f238028778d3aa798ece2823152b3d7097f841d6140018e6'

def pack_many_patterns(raw,count,images,tiles,parts):
    if all(np.array_equal(images[0],x) for x in images):
        result,records=identical(raw,count,images[0],tiles,min(parts));return result,[[(t,x,y,0) for t,x,y in records] for _ in images]
    unique=[];indices=[]
    for im in images:
        k=next((i for i,v in enumerate(unique) if np.array_equal(v,im)),None)
        if k is None:k=len(unique);unique.append(im)
        indices.append(k)
    # Deduplicate normalized tile rasters, allowing translation and horizontal flip.
    patterns=[];records=[]
    for image,limit in zip(images,parts):
        rects=fit(image>0,limit)
        if rects is None:raise ValueError('Layer exceeds original composition part count')
        remaining=image.copy();rr=[]
        for left,top in rects:
            patch=remaining[top:top+16,left:left+16].copy();remaining[top:top+16,left:left+16]=0
            ys,xs=np.nonzero(patch)
            if not len(xs):continue
            x0,y0,x1,y1=int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)
            compact=patch[y0:y1,x0:x1];key=(compact.shape,compact.tobytes());flipped=(compact.shape,compact[:,::-1].tobytes())
            if key in patterns:k=patterns.index(key);flag=0
            elif flipped in patterns:k=patterns.index(flipped);flag=64
            else:k=len(patterns);patterns.append(key);flag=0
            rr.append([k,left+x0,top+y0,flag])
        if not rr:
            key=((1,1),bytes(1))
            if key not in patterns:patterns.append(key)
            rr=[[patterns.index(key),64,64,0]]
        records.append(rr)
    if len(patterns)>len(tiles):raise ValueError(f'Unique tile patterns {len(patterns)} exceed {len(tiles)}')
    ids=sorted(tiles,key=lambda t:(t%16==0,t));chosen={};used=set()
    for k,(shape,data) in sorted(enumerate(patterns),key=lambda v:v[1][0][1],reverse=True):
        flip_used=any(r[0]==k and r[3] for rr in records for r in rr)
        t=next((t for t in ids if t not in used and (t%16!=0 or (shape[1]<16 and not flip_used))),None)
        if t is None:raise ValueError('Tile pattern requires unsafe page-edge source')
        used.add(t);chosen[k]=(t,1 if t%16==0 else 0)
    _,locations,_=indexed_atlas(raw,count);out=bytearray(raw)
    for t in tiles:
        for y in range(16):
            for x in range(16):
                pos,shift=locations[(t//16*16+y)*256+t%16*16+x];out[pos]&=~(15<<shift)
    for k,(shape,data) in enumerate(patterns):
        t,pad=chosen[k];v=np.frombuffer(data,np.uint8).reshape(shape)
        for y,x in np.argwhere(v):
            pos,shift=locations[(t//16*16+int(y))*256+t%16*16+int(x)+pad];out[pos]|=int(v[y,x])<<shift
    result=[]
    for rr in records:
        result.append([(chosen[k][0],x-(16-patterns[k][0][1] if flag else chosen[k][1]),y,flag) for k,x,y,flag in rr])
    return bytes(out),result

def pack_many(raw,count,images,tiles,parts):
    try:return pack_many_patterns(raw,count,images,tiles,parts)
    except ValueError as first_error:
        unique=[];indices=[]
        for im in images:
            k=next((i for i,v in enumerate(unique) if np.array_equal(v,im)),None)
            if k is None:k=len(unique);unique.append(im)
            indices.append(k)
        if len(unique)!=2:raise first_error
        nr,ns=[min(parts[i] for i,k in enumerate(indices) if k==j) for j in range(2)]
        try:result,a,b=variants(raw,count,*unique,tiles,nr,ns)
        except ValueError:raise first_error
        return result,[[(t,x,y,0) for t,x,y in (a,b)[k]] for k in indices]

def prepare(artdir,audit=False):
    parent=ROOT/PARENT;pm=json.loads((parent/'manifest.json').read_text(encoding='utf-8'));arc=(parent/'modified.arc').read_bytes()
    if sha256(arc)!=PARENT_HASH or pm['modified_bin']['sha256']!='32c5ed5485de9598113b0207ed0118aa7ba5f567c225d996dd92bc2056efffcb':raise ValueError('Changed armor parent')
    meta=json.loads((artdir/'layers.json').read_text(encoding='utf-8'));frames=meta['frames'];expected_scope=sorted(set(range(237))-{0,*range(1,33),*range(115,120),105,*range(175,183),198})
    if frames!=expected_scope or meta['canvas_size']!=[160,160] or meta['origin']!=[80,80]:raise ValueError('Wrong remaining scope')
    es=entries(arc);g,c=es[2],es[3]
    if list(struct.unpack_from('<16H',es[9],32))!=meta['palette_words']:raise ValueError('Wrong armor palette')
    bank=graphics_bank(g,0,allow_bank_aliases=True);groups={}
    for n in frames:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
    nc=bytearray(c);allowed={};expected={};reports=[];failures=[];targets={};hashes={}
    for offset,aliases in groups.items():
        f=bank['frames'][aliases[0]]
        allrefs=[v['index'] for v in bank['frames'] if v['offset']==offset]
        if set(allrefs)-set(aliases) not in (set(),{198}):raise ValueError('Sharing escapes selected scope')
        before=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;raw=before;all_armor=set();base_tiles={q['tile'] for n in allrefs for q in composition_frame(c,0,n)['parts']};details=[]
        effects={17,18} if aliases[0]==106 else set()
        armor_pool={q['tile'] for n in aliases for bi in LAYERS.values() for q in composition_frame(c,bi,n)['parts']}-base_tiles-effects
        atlas,_,_=indexed_atlas(before,f['tile_count']);atlas=np.frombuffer(atlas,np.uint8).reshape(-1,256)
        armor_pool={t for t in armor_pool if np.any(atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16])}
        free=set(armor_pool)
        try:
            for kind,bi in LAYERS.items():
                fullcomps=[composition_frame(c,bi,n) for n in aliases]
                comps=[{**cp,'parts':[q for q in cp['parts'] if q['tile'] not in effects]} for cp in fullcomps]
                images=[]
                for n in aliases:
                    path=artdir/f'{kind}_{n:03}.png';im=Image.open(path);hashes[path.name]=sha256(path.read_bytes())
                    if im.mode!='P' or im.size!=(160,160) or max(im.tobytes())>15 or im.info.get('transparency')!=0:raise ValueError('Invalid armor raster')
                    v=np.array(im);images.append(v);targets[bi,n]=v
                if all(not np.any(v) for v in images) and all(not np.any(canvas_from_parts(before,f['tile_count'],cp)) for cp in fullcomps):continue
                # Preserve original armor-specific electrical effects verbatim.
                for i,(n,cp) in enumerate(zip(aliases,fullcomps)):
                    effectparts=[q for q in cp['parts'] if q['tile'] in effects]
                    if effectparts:
                        fx=canvas_from_parts(before,f['tile_count'],{**cp,'parts':effectparts})
                        images[i]=np.where(fx,0,images[i]).astype(np.uint8)
                        targets[bi,n]=np.where(fx,fx,images[i]).astype(np.uint8)
                if not free:raise ValueError('No armor tile capacity')
                tiles=set(free)
                raw,assignments=pack_many(raw,f['tile_count'],images,tiles,[len(cp['parts']) for cp in comps])
                used={r[0] for rr in assignments for r in rr};free-=used;all_armor|=tiles
                for n,cp,records in zip(aliases,comps,assignments):
                    if not records or len(records)>len(cp['parts']):raise ValueError('Part count increased')
                    for i,q in enumerate(cp['parts']):
                        if q['page'] or q['clut'] or q['unknown_flags']:raise ValueError('Unsupported part flags')
                        t,x,y,flag=records[min(i,len(records)-1)];value=struct.pack('<BBbb',flag,t,x-80,y-80);pos=q['record_offset']
                        if pos in allowed and allowed[pos]!=value:raise ValueError('Shared composition record conflict')
                        allowed[pos]=value;nc[pos:pos+4]=value
                    if not np.array_equal(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,bi,n)),targets[bi,n]):raise ValueError('Inserted armor raster differs')
                details.append({'layer':kind,'tiles':sorted(used),'records':assignments})
            old_atlas,_,_=indexed_atlas(before,f['tile_count']);new_atlas,_,_=indexed_atlas(raw,f['tile_count'])
            for t in range(f['tile_count']):
                if t in all_armor:continue
                for y in range(16):
                    pos=(t//16*16+y)*256+t%16*16
                    if old_atlas[pos:pos+16]!=new_atlas[pos:pos+16]:raise ValueError('Non-armor tile changed')
            for n in allrefs:expected[n]=raw
            for n in set(allrefs)-set(aliases):
                for bi in (0,5,6,7,8):
                    if not np.array_equal(canvas_from_parts(before,f['tile_count'],composition_frame(c,bi,n)),canvas_from_parts(raw,f['tile_count'],composition_frame(nc,bi,n))):raise ValueError('Shared blank frame changed')
            code=encode_stream(raw);reports.append({'frame':aliases[0],'aliases':aliases,'encoded_bytes':len(code),'capacity':f['limit']-f['offset'],'layers':details,'changed':raw!=before})
        except ValueError as error:
            failures.append({'frames':aliases,'layer':kind,'error':str(error)})
            if not audit:raise ValueError(f'{aliases}/{kind}: {error}') from error
    if audit:return None,{'failures':failures,'passed_groups':len(reports),'total_groups':len(groups),'reports':reports}
    ng=g;compression=[];repack=None
    if all(r['encoded_bytes']<=r['capacity'] for r in reports):
        for r in reports:
            if r['changed']:ng,v=replace_stream(ng,bank['frames'][r['frame']],expected[r['frame']]);compression.append(v)
    else:ng,repack=repack_graphics_bank(g,0,{n:encode_stream(raw) for n,raw in expected.items()})
    checked=0;base_exact=0;changed=[]
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        ba=graphics_bank(g,bi,allow_bank_aliases=True);bb=graphics_bank(ng,bi,allow_bank_aliases=True)
        if (ba['base'],ba['end'],len(ba['frames']))!=(bb['base'],bb['end'],len(bb['frames'])):raise ValueError('Bank boundary changed')
        for a,b in zip(ba['frames'],bb['frames']):
            if a['tile_count']!=b['tile_count']:raise ValueError('Tile count changed')
            old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data
            if new!=(expected.get(a['index'],old) if bi==0 else old):raise ValueError('Unselected bitmap changed')
            checked+=1
            if old!=new:changed.append([bi,a['index']])
            if bi==0 and a['index'] not in {105,*range(175,183)}:
                if not np.array_equal(canvas_from_parts(old,a['tile_count'],composition_frame(c,0,a['index'])),canvas_from_parts(new,b['tile_count'],composition_frame(nc,0,b['index']))):raise ValueError('Base frame changed')
                base_exact+=1
                for ci in LAYERS.values():
                    if (ci,a['index']) in targets and not np.array_equal(canvas_from_parts(new,b['tile_count'],composition_frame(nc,ci,b['index'])),targets[ci,a['index']]):raise ValueError('Final armor differs')
    others=0
    for bi,offset in enumerate(bank_offsets(c)):
        count=struct.unpack_from('<I',c,offset)[0]>>16
        for n in range(count):
            if bi in LAYERS.values() and n in frames:continue
            if composition_frame(c,bi,n)!=composition_frame(nc,bi,n):raise ValueError('Unselected composition changed')
            others+=1
    result=bytearray(arc)
    for t,v in ((2,ng),(3,nc)):
        e=next(e for e in psx_arc(arc) if int(e['type'],16)==t)
        if len(v)!=e['size']:raise ValueError('Entry length changed')
        result[e['offset']:e['offset']+e['size']]=v
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text())
    recipe={'task':'fourth_armor_shibuki','scope':'fourth_armor_remaining_189','parent_build':PARENT,'parent_bin_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':PARENT_HASH,'original_arc_sha256':cfg['archive']['sha256'],'modified_arc_sha256':sha256(result),'source_art':str(artdir.relative_to(ROOT)),'art_manifest_sha256':sha256((artdir/'layers.json').read_bytes()),'art_hashes':hashes,'edited_frame_references':frames,'changed_bitmap_references':changed,'armor_layers':reports,'checked_bitmap_references':checked,'checked_other_compositions':others,'base_rasters_exact':base_exact,'new_armor_rasters_exact':len(targets),'base_tiles_preserved':True,'base_compositions_all_preserved':True,'palette_preserved':True,'compression':compression,'repack':repack,'resources_relocated_within_bank':repack is not None,'archive_size_and_lba_preserved':True,'run_frames_preserved':True,'shooting_body_uses_same_run_pose':True,'shooting_arm_art_pending':False,'runtime_verified':False,'armor_full_animation_complete':False,'armor_frames_cumulative':sorted(set(frames)|set(pm['armor_frames_cumulative'])),'approval':{'date':'2026-10-27','scope':'승인 망토 의상의 전체 스프라이트 제작','user_quote':'좋아 잘만들어지고있는거같으니 계속 진행하자. 그냥 스프라이트 전체를 한번에 완성해도될정도로 잘나오고있어'}}
    return bytes(result),recipe
def main():
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--audit',action='store_true');a=p.parse_args();art=a.art.resolve()
    if not art.is_relative_to(ROOT/'work/ver_buki_riko/shibuki_art'):raise ValueError('Isolated artwork required')
    arc,report=prepare(art,a.audit)
    if a.audit:
        out=new_run(ROOT,'ver_buki_riko','shibuki_armor_audit');write_json(out/'packing_audit.json',{'source_art':str(art.relative_to(ROOT)),**report});print(json.dumps({'output':str(out),'passed_groups':report['passed_groups'],'failures':report['failures']}));return
    out=new_run(ROOT,'ver_buki_riko','shibuki_fourth_remaining');(out/'modified.arc').write_bytes(arc);write_json(out/'recipe.json',report);print(json.dumps({'output':str(out),'sha256':sha256(arc),'repacked':report['repack'] is not None}))
if __name__=='__main__':main()
