"""승인된 기본 몸을 보존하며 포스 아머 이동/사격32참조를 같은 은행에 넣는다."""
import argparse
import json
from pathlib import Path
import struct
import sys
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,inspect_references,load_project
from scripts.discover_inputs import psx_arc,sha256
from scripts.analyze_shibuki_armor import entries
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_tile_layout import pack_rectangles
from src.psx_paired_layout import pack_variant_pair

LAYERS={'head':5,'body':6,'arm':7,'leg':8}
PARENT='out/ver_buki_riko/shibuki_fourth_idle_20261027T002313205126Z'
PARENT_HASH='b165f3d33528605ffdcec209c413ce135b29bfd498c4d095de97b6e6f2929188'


def fit(mask,count):
    ys,xs=np.nonzero(mask)
    if not len(xs):return []
    if count<=0:return None
    if xs.max()-xs.min()<16 and ys.max()-ys.min()<16:
        return [[max(0,int(xs.max())-15),max(0,int(ys.max())-15)]]
    if count==1:return None
    if ys.max()-ys.min()<16:
        columns=sorted(set(int(v) for v in xs));rects=[]
        while columns:
            left=min(columns[0],mask.shape[1]-16);rects.append([left,max(0,int(ys.max())-15)])
            columns=[x for x in columns if x>=left+16]
        if len(rects)<=count:return rects
    from scripts.solve_sprite_cover import cover
    result=cover(mask,count,1.5)
    return result['rects'] if result['fits'] else None


def identical(raw,count,target,tiles,parts):
    rects=fit(target>0,min(len(tiles),parts))
    if rects is None:raise ValueError('Identical armor layer needs more part slots')
    ids=sorted(tiles,key=lambda t:(t%16==0,t))[:len(rects)]
    if any(t%16==0 for t in ids):
        if sum(t%16==0 for t in ids)>1:raise ValueError('Multiple page-edge tiles require a layout review')
        chosen=None
        for index,rect in enumerate(rects):
            others=[r for j,r in enumerate(rects) if j!=index]
            remaining=target.copy()
            for x,y in others:remaining[y:y+16,x:x+16]=0
            x,y=rect
            for dx in (0,-1,1):
                left=x+dx
                if not 0<=left<=target.shape[1]-16 or np.any(remaining[y:y+16,left]):continue
                rest=remaining.copy();rest[y:y+16,left:left+16]=0
                if not np.any(rest):chosen=others+[[left,y]];break
            if chosen is not None:break
        if chosen is None:raise ValueError('Page-edge armor tile has opaque first column')
        rects=chosen
    result=pack_rectangles(raw,count,target.tobytes(),(target.shape[1],target.shape[0]),rects,ids,tiles)
    records=[(t,*r) for t,r in zip(ids,rects)]
    if not records:
        records=[(min(tiles),64,64)]
    return result,records


def variants(raw,count,a,b,tiles,nr,ns):
    # Try independent one-part variants before introducing shared pixels.
    ar,br=fit(a>0,nr),fit(b>0,ns)
    if ar is not None and br is not None and len(ar)+len(br)<=len(tiles):
        try:
            result,r,s,_,_=pack_variant_pair(raw,count,a,b,[],ar,br,tiles)
            return result,r,s
        except ValueError:
            pass
    if min(nr,ns)<2:raise ValueError('Armor variants cannot fit independent slots')
    common=(a==b)&(a>0);ys,xs=np.nonzero(common)
    choices=[]
    if len(xs):
        for x in range(max(0,int(xs.min())-15),min(144,int(xs.max()))+1):
            for y in range(max(0,int(ys.max())-15),min(144,int(ys.min()))+1):
                c=np.zeros_like(a);region=common[y:y+16,x:x+16]
                c[y:y+16,x:x+16]=np.where(region,a[y:y+16,x:x+16],0)
                aa=np.where(c,a*0,a);bb=np.where(c,b*0,b)
                ra,rb=fit(aa>0,nr-1),fit(bb>0,ns-1)
                if ra is None or rb is None or 1+len(ra)+len(rb)>len(tiles):continue
                choices.append((int(np.count_nonzero(c)),[x,y],ra,rb))
    for _,cr,ar,br in sorted(choices,reverse=True):
        try:
            result,r,s,_,_=pack_variant_pair(raw,count,a,b,[cr],ar,br,tiles)
            return result,r,s
        except ValueError:
            continue
    raise ValueError('Shared armor variants need a different garment split')


def prepare(artdir,parent):
    pm=json.loads((parent/'manifest.json').read_text(encoding='utf-8'))
    arc=(parent/'modified.arc').read_bytes()
    if sha256(arc)!=PARENT_HASH or pm['modified_bin']['sha256']!='7d2d80d9254a3971ceb6541d3d28c2a3ec4fdb952953b2868ec8a6938547c593':raise ValueError('Parent differs from armor pilot')
    meta=json.loads((artdir/'layers.json').read_text(encoding='utf-8'))
    if meta['frames']!=list(range(1,33)) or meta['canvas_size']!=[160,160] or meta['origin']!=[80,80]:raise ValueError('Unexpected armor motion scope')
    es=entries(arc);g,c=es[2],es[3]
    if list(struct.unpack_from('<16H',es[9],32))!=meta['palette_words']:raise ValueError('Armor art palette differs')
    bank=graphics_bank(g,0,allow_bank_aliases=True)
    nc=bytearray(c);expected={};replacements={};targets={};reports=[];allowed=set();hashes={}
    for n in range(1,33,2):
        desc=bank['frames'][n];aliases=[f['index'] for f in bank['frames'] if f['offset']==desc['offset']]
        if aliases!=[n,n+1]:raise ValueError('Unexpected armor stream sharing')
        before=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128).data;raw=before
        base_tiles={q['tile'] for f in aliases for q in composition_frame(c,0,f)['parts']}
        all_armor=set();details=[]
        for kind,bi in LAYERS.items():
            comps=[composition_frame(c,bi,f) for f in aliases]
            tiles={q['tile'] for cp in comps for q in cp['parts']}
            if tiles&base_tiles or tiles&all_armor:raise ValueError('Armor ownership conflict')
            all_armor|=tiles;images=[]
            for f in aliases:
                path=artdir/f'{kind}_{f:03}.png';hashes[path.name]=sha256(path.read_bytes());im=Image.open(path)
                if im.mode!='P' or im.size!=(160,160) or max(im.tobytes())>15 or im.info.get('transparency')!=0:raise ValueError('Invalid armor raster')
                v=np.array(im);targets[bi,f]=v;images.append(v)
            a,b=images;nr,ns=[len(cp['parts']) for cp in comps]
            try:
                if np.array_equal(a,b):
                    raw,records=identical(raw,desc['tile_count'],a,tiles,min(nr,ns));assignments=[records,records]
                else:
                    raw,r,s=variants(raw,desc['tile_count'],a,b,tiles,nr,ns);assignments=[r,s]
            except ValueError as exc:
                raise ValueError(f'Frame {n}, layer {kind}: {exc}') from exc
            for f,cp,records in zip(aliases,comps,assignments):
                if len(records)>len(cp['parts']) or not records:raise ValueError('Part count changed')
                for i,q in enumerate(cp['parts']):
                    if q['page'] or q['clut'] or q['unknown_flags']:raise ValueError('Unexpected armor part flags')
                    t,x,y=records[min(i,len(records)-1)]
                    struct.pack_into('<BBbb',nc,q['record_offset'],0,t,x-80,y-80);allowed.update(range(q['record_offset'],q['record_offset']+4))
                if not np.array_equal(canvas_from_parts(raw,desc['tile_count'],composition_frame(nc,bi,f)),targets[bi,f]):raise ValueError(f'Armor raster differs {f}/{kind}')
            details.append({'layer':kind,'tiles':sorted(tiles),'records':assignments})
        old_atlas,_,_=indexed_atlas(before,desc['tile_count']);new_atlas,_,_=indexed_atlas(raw,desc['tile_count'])
        for t in range(desc['tile_count']):
            if t in all_armor:continue
            for y in range(16):
                pos=(t//16*16+y)*256+t%16*16
                if old_atlas[pos:pos+16]!=new_atlas[pos:pos+16]:raise ValueError('Base/effect tile changed')
        code=encode_stream(raw)
        for f in aliases:expected[f]=raw;replacements[f]=code
        report={'frame':n,'aliases':aliases,'encoded_bytes':len(code),'capacity':desc['limit']-desc['offset'],'layers':details}
        reports.append(report);print(json.dumps({k:report[k] for k in ('frame','encoded_bytes','capacity')}),flush=True)
    changes={i for i,(a,b) in enumerate(zip(c,nc)) if a!=b}
    if not changes<=allowed:raise ValueError('Composition writes escaped selected records')
    other_comps=0
    for bi,offset in enumerate(bank_offsets(c)):
        count=struct.unpack_from('<I',c,offset)[0]>>16
        for n in range(count):
            if bi in LAYERS.values() and n in expected:continue
            if composition_frame(c,bi,n)!=composition_frame(nc,bi,n):raise ValueError('Unselected composition alias changed')
            other_comps+=1
    fits=all(r['encoded_bytes']<=r['capacity'] for r in reports);ng=g;compression=[];repack=None
    if fits:
        for n in range(1,33,2):ng,r=replace_stream(ng,bank['frames'][n],expected[n]);compression.append(r)
    else:
        ng,repack=repack_graphics_bank(g,0,replacements)
    checked=0;changed=[]
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        ba=graphics_bank(g,bi,allow_bank_aliases=True);bb=graphics_bank(ng,bi,allow_bank_aliases=True)
        if (ba['base'],ba['end'],len(ba['frames']))!=(bb['base'],bb['end'],len(bb['frames'])):raise ValueError('Bank layout changed')
        for a,b in zip(ba['frames'],bb['frames']):
            if a['tile_count']!=b['tile_count']:raise ValueError('Tile count changed')
            old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data
            want=expected.get(a['index'],old) if bi==0 else old
            if new!=want:raise ValueError('Unselected pixels changed')
            checked+=1
            if old!=new:changed.append([bi,a['index']])
            if bi==0 and a['index'] in expected:
                for kind,ci in LAYERS.items():
                    if not np.array_equal(canvas_from_parts(new,b['tile_count'],composition_frame(nc,ci,b['index'])),targets[ci,b['index']]):raise ValueError('Final armor mismatch')
                if not np.array_equal(canvas_from_parts(old,a['tile_count'],composition_frame(c,0,a['index'])),canvas_from_parts(new,b['tile_count'],composition_frame(nc,0,b['index']))):raise ValueError('Base motion changed')
    if changed!=[[0,n] for n in range(1,33)]:raise ValueError('Wrong changed frame set')
    result=bytearray(arc)
    for t,value in ((2,ng),(3,nc)):
        e=next(e for e in psx_arc(arc) if int(e['type'],16)==t)
        if len(value)!=e['size']:raise ValueError('Entry length changed')
        result[e['offset']:e['offset']+e['size']]=value
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text())
    recipe={'task':'fourth_armor_shibuki','scope':'fourth_armor_run_32','parent_build':str(parent.relative_to(ROOT)),
        'parent_bin_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha256(arc),'original_arc_sha256':cfg['archive']['sha256'],
        'modified_arc_sha256':sha256(result),'arc_size':len(result),'source_art':str(artdir.relative_to(ROOT)),
        'art_manifest_sha256':sha256((artdir/'layers.json').read_bytes()),'art_hashes':hashes,'edited_frame_references':list(range(1,33)),
        'armor_layers':reports,'compression':compression,'repack':repack,'resources_relocated_within_bank':repack is not None,
        'archive_size_and_lba_preserved':True,'palette_preserved':True,'checked_bitmap_references':checked,'checked_other_compositions':other_comps,
        'base_tiles_preserved':True,'base_compositions_all_preserved':True,'new_armor_rasters_exact':len(targets),
        'run_frames_preserved':True,'shooting_body_uses_same_run_pose':False,'shooting_arm_art_pending':False,'runtime_verified':False,
        'armor_full_animation_complete':False,'armor_frames_cumulative':[0,*range(1,33),115,116,117,118,119],
        'approval':{'date':'2026-10-27','user_quote':'그럼 본격적으로 진행해보자','style_quote':'일단 디자인은 되게 마음에 들어 이걸로 작업 계속해나가면될듯한데','scope':'승인 망토 시안의 포스 아머 제작 확대; 기존 같은 은행 저장 방식'}}
    return bytes(result),recipe


def main():
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--parent',type=Path,default=ROOT/PARENT);args=p.parse_args()
    art=args.art.resolve();parent=args.parent.resolve()
    if not art.is_relative_to(ROOT/'work/ver_buki_riko/shibuki_art') or not parent.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Isolated inputs required')
    inspect_references(ROOT,load_project(ROOT,'ver_buki_riko'))
    arc,recipe=prepare(art,parent);out=new_run(ROOT,'ver_buki_riko','shibuki_fourth_run');(out/'modified.arc').write_bytes(arc);write_json(out/'recipe.json',recipe)
    print(json.dumps({'output':str(out),'sha256':sha256(arc),'repacked':recipe['repack'] is not None}))


if __name__=='__main__':main()
