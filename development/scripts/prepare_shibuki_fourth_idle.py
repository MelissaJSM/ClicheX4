"""완성 기본형 위에 포스 아머 대기6참조를 별도 파츠로 적용하는 시험 ARC."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,load_project,inspect_references
from scripts.discover_inputs import psx_arc,sha256
from scripts.analyze_shibuki_armor import PARENT
from scripts.prepare_shibuki_weapon_palette import WEAPON_ROWS,FLASHES
from src.psx_armor_palette import replace_armor_palette_rows
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_tile_layout import pack_rectangles
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank

FRAMES=(0,115,116,117,118,119)
LAYERS={'head':5,'body':6,'arm':7,'leg':8}

def rectangles(v,kind):
    ys,xs=np.nonzero(v)
    if not len(xs):raise ValueError('Empty armor layer')
    if kind=='arm':
        rects=[]
        for mask in (np.indices(v.shape)[1]<80,np.indices(v.shape)[1]>=80):
            sy,sx=np.nonzero((v>0)&mask)
            if not len(sx) or sx.max()-sx.min()>=16 or sy.max()-sy.min()>=16:raise ValueError('Arm artwork does not fit original parts')
            rects.append([int(sx.min()),int(sy.min())])
        return rects
    if ys.max()-ys.min()>=16:raise ValueError('Layer exceeds tile height')
    return [[int(left),int(ys.min())] for left in range(int(xs.min()),int(xs.max())+1,16)]

def prepare(artdir,parent):
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());pm=json.loads((parent/'manifest.json').read_text());arc=(parent/'modified.arc').read_bytes()
    if sha256(arc)!='f8f1d567e612b5e60f5911a1b2930993a76951a1840d15821bafb0725fec2903' or pm['modified_bin']['sha256']!='6a8e7519a229994bbb831be74d77324ce3ffd0afaefc370329208cd3f38a05a9':raise ValueError('Parent differs from approved base')
    art=json.loads((artdir/'layers.json').read_text());words=art['palette_words']
    if art['frames']!=list(FRAMES) or art['canvas_size']!=[160,160] or art['origin']!=[80,80]:raise ValueError('Unexpected armor art scope')
    entries=psx_arc(arc);meta={int(e['type'],16):e for e in entries};es={t:arc[e['offset']:e['offset']+e['size']] for t,e in meta.items()};g,c,pal=es[2],es[3],es[9]
    bank=graphics_bank(g,0,allow_bank_aliases=True);nc=bytearray(c);replacements={};expected={};allowed=set();reports=[];hashes={};selected_pixels={}
    for representative,refs in ((0,[0]),(115,[115,116,117,118]),(119,[119])):
        f=bank['frames'][representative];old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128);raw=old.data
        aliases=[r['index'] for r in bank['frames'] if r['offset']==f['offset']]
        if aliases!=refs:raise ValueError('Unexpected shared armor stream')
        base_tiles={q['tile'] for n in refs for q in composition_frame(c,0,n)['parts']};all_armor=set()
        for kind,bi in LAYERS.items():
            cp=composition_frame(c,bi,representative);tiles=sorted({q['tile'] for n in refs for q in composition_frame(c,bi,n)['parts']})
            if base_tiles&set(tiles) or all_armor&set(tiles):raise ValueError('Armor ownership conflict')
            all_armor.update(tiles)
            paths=[artdir/f'{kind}_{n:03}.png' for n in refs]
            for path in paths:hashes[path.name]=sha256(path.read_bytes())
            images=[Image.open(path) for path in paths]
            if any(im.mode!='P' or im.size!=(160,160) or max(im.tobytes())>15 or im.info.get('transparency')!=0 for im in images):raise ValueError('Invalid armor raster')
            vs=[np.array(im) for im in images];v=vs[0]
            if any(not np.array_equal(x,v) for x in vs):raise ValueError('Shared armor raster conflict')
            rects=rectangles(v,kind);safe=[t for t in tiles if t%16!=0]
            if len(rects)>len(cp['parts']) or len(rects)>len(safe):raise ValueError('Armor requires additional parts')
            ids=safe[:len(rects)];raw=pack_rectangles(raw,f['tile_count'],v.tobytes(),(160,160),rects,ids,tiles)
            for n in refs:
                parts=composition_frame(c,bi,n)['parts']
                if len(parts)<len(rects):raise ValueError('Not enough shared part slots')
                for i,q in enumerate(parts):
                    k=min(i,len(rects)-1);x,y=rects[k]
                    if q['page'] or q['unknown_flags'] or q['clut']:raise ValueError('Unexpected armor flags')
                    struct.pack_into('<BBbb',nc,q['record_offset'],0,ids[k],x-80,y-80);allowed.update(range(q['record_offset'],q['record_offset']+4))
                rebuilt=canvas_from_parts(raw,f['tile_count'],composition_frame(nc,bi,n))
                if not np.array_equal(rebuilt,v):raise ValueError('Armor raster mismatch')
                selected_pixels[bi,n]=v
            reports.append({'frame':representative,'aliases':refs,'layer':kind,'tiles':tiles,'used_tiles':ids,'rectangles':rects,'raster_exact':True})
        # Preserve all base/eye/effect texels, including those hidden in a pose.
        old_atlas,_,_=indexed_atlas(old.data,f['tile_count']);new_atlas,_,_=indexed_atlas(raw,f['tile_count'])
        for t in range(f['tile_count']):
            if t in all_armor:continue
            for y in range(16):
                start=(t//16*16+y)*256+t%16*16
                if old_atlas[start:start+16]!=new_atlas[start:start+16]:raise ValueError('Base/eye tile changed')
        code=encode_stream(raw)
        for n in refs:replacements[n]=code;expected[n]=raw
    changed_bytes={i for i,(a,b) in enumerate(zip(c,nc)) if a!=b}
    if not changed_bytes<=allowed:raise ValueError('Composition write escaped selected parts')
    others=0
    for bi,offset in enumerate(bank_offsets(c)):
        count=struct.unpack_from('<I',c,offset)[0]>>16
        for n in range(count):
            if bi in LAYERS.values() and n in FRAMES:continue
            if composition_frame(c,bi,n)!=composition_frame(nc,bi,n):raise ValueError('Unselected composition changed')
            others+=1
    # Reuse the already verified same-bank compaction method only if necessary.
    fits=all(len(replacements[n])<=bank['frames'][n]['limit']-bank['frames'][n]['offset'] for n in (0,115,119))
    ng=g;compression=[];repack=None
    if fits:
        for n in (0,115,119):ng,report=replace_stream(ng,bank['frames'][n],expected[n]);compression.append(report)
    else:ng,repack=repack_graphics_bank(g,0,replacements)
    total=0;changed=[];base_exact=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        a=graphics_bank(g,bi,allow_bank_aliases=True);b=graphics_bank(ng,bi,allow_bank_aliases=True)
        if (a['base'],a['end'],len(a['frames']))!=(b['base'],b['end'],len(b['frames'])):raise ValueError('Graphics bank boundary changed')
        for f,nf in zip(a['frames'],b['frames']):
            before=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;after=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;n=f['index'];total+=1
            if f['tile_count']!=nf['tile_count']:raise ValueError('Tile count changed')
            want=expected[n] if bi==0 and n in expected else before
            if after!=want:raise ValueError('Unselected bitmap changed')
            if before!=after:changed.append([bi,n])
            if bi==0 and n in FRAMES:
                if not np.array_equal(canvas_from_parts(before,f['tile_count'],composition_frame(c,0,n)),canvas_from_parts(after,f['tile_count'],composition_frame(nc,0,n))):raise ValueError('Accepted base changed')
                base_exact+=1
    if changed!=[[0,n] for n in FRAMES]:raise ValueError('Incomplete armor changes')
    npal,palette_rows=replace_armor_palette_rows(pal,words,[0,*FLASHES],FLASHES,weapon_rows=WEAPON_ROWS)
    result=bytearray(arc)
    for t,v in ((2,ng),(3,nc),(9,npal)):
        e=meta[t]
        if len(v)!=e['size']:raise ValueError('ARC entry size changed')
        result[e['offset']:e['offset']+e['size']]=v
    if len(result)!=len(arc):raise ValueError('ARC length changed')
    recipe={'task':'fourth_armor_shibuki','scope':'fourth_armor_idle_6','parent_build':str(parent.relative_to(ROOT)),'parent_bin_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha256(arc),'original_arc_sha256':cfg['archive']['sha256'],'modified_arc_sha256':sha256(result),'arc_size':len(result),'source_art':str(artdir.relative_to(ROOT)),'art_manifest_sha256':sha256((artdir/'layers.json').read_bytes()),'art_hashes':hashes,'armor_layers':reports,'edited_frame_references':list(FRAMES),'compression':compression,'repack':repack,'resources_relocated_within_bank':repack is not None,'archive_size_and_lba_preserved':True,'palette_rows':palette_rows,'base_and_effect_palette_rows_preserved':True,'checked_bitmap_references':total,'checked_other_compositions':others,'base_idle_rasters_exact':base_exact,'base_tiles_preserved':True,'new_armor_rasters_exact':len(selected_pixels),'base_compositions_all_preserved':True,'shooting_body_uses_same_run_pose':False,'shooting_arm_art_pending':False,'run_frames_preserved':True,'runtime_verified':False,'armor_full_animation_complete':False,'unimplemented_armor_frames_use_original_bitmap_with_candidate_palette':True,'approval':{'date':'2026-10-27','scope':'Fourth armor production using existing same-bank resource method; cape outfit selected','user_quote':'포스아머부터 해보자…바로 작업에 들어가자'}}
    return bytes(result),recipe

def main():
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--parent',type=Path,default=ROOT/PARENT);args=p.parse_args();art=args.art.resolve();parent=args.parent.resolve()
    if not art.is_relative_to(ROOT/'work/ver_buki_riko/shibuki_art') or not parent.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Isolated inputs required')
    inspect_references(ROOT,load_project(ROOT,'ver_buki_riko'));arc,recipe=prepare(art,parent);out=new_run(ROOT,'ver_buki_riko','shibuki_fourth_idle');(out/'modified.arc').write_bytes(arc);write_json(out/'recipe.json',recipe)
    print(json.dumps({'output':str(out),'sha256':sha256(arc),'repacked':recipe['repack'] is not None,'compression':recipe['compression'],'palettes':len(recipe['palette_rows']),'armor_rasters_exact':recipe['new_armor_rasters_exact']}))

if __name__=='__main__':main()
