"""전진 호버4참조의 하체만 수정하고 원래 슬롯과 다른 동작을 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,digest
from scripts.analyze_shibuki_armor import entries
from scripts.discover_inputs import psx_arc,sha256
from scripts.prepare_shibuki_armor_remaining import pack_many
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import encode_stream
PARENT='out/ver_buki_riko/shibuki_fourth_remaining_20261027T014647676089Z'
PARENT_ARC='3bfb6a9390a0b826672dd8f06e9527e73a139b0b3210a76b65564a084f2d94fe'
PARENT_BIN='6b5597f8c27d0e84cb664a2d11f9f879b0029892361e977e28ebe3eb2ed2decd'
FRAMES=[221,222,223,224]

def replace_reserved_slot(graphics, descriptor, packed):
    start,limit=descriptor['offset'],descriptor['limit'];size=descriptor['tile_count']*128
    if not 0<=start<limit<=len(graphics) or len(packed)!=size:raise ValueError('Invalid reserved stream slot')
    old=decode_stream(graphics,start,limit,size)
    encoded=encode_stream(packed,max_bytes=limit-start)
    result=bytearray(graphics);result[start:start+len(encoded)]=encoded
    decoded=decode_stream(result,start,limit,size)
    if decoded.data!=packed or decoded.end!=start+len(encoded):raise ValueError('Reserved slot readback mismatch')
    return bytes(result),{'start':start,'limit':limit,'old_encoded_bytes':old.end-start,'encoded_bytes':len(encoded),'slot_capacity':limit-start,'used_preexisting_tail_bytes':max(0,start+len(encoded)-old.end),'offset_unchanged':True}

def prepare(art):
    arc=(ROOT/PARENT/'modified.arc').read_bytes();pm=json.loads((ROOT/PARENT/'manifest.json').read_text(encoding='utf-8'))
    if sha256(arc)!=PARENT_ARC or pm['modified_bin']['sha256']!=PARENT_BIN:raise ValueError('Unsupported hover parent')
    meta=json.loads((art/'layers.json').read_text(encoding='utf-8'))
    if meta['frames']!=FRAMES or meta['canvas_size']!=[160,160] or meta['origin']!=[80,80]:raise ValueError('Unexpected hover scope')
    es=entries(arc);g,c=es[2],es[3];bank=graphics_bank(g,0,allow_bank_aliases=True);ng=g;nc=bytearray(c);targets={};hashes={};streams={};report=[];allowed_records={}
    for first in [221,223]:
        aliases=[first,first+1];f=bank['frames'][first]
        if [v['index'] for v in bank['frames'] if v['offset']==f['offset']]!=aliases:raise ValueError('Unexpected hover stream sharing')
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;before=raw;cut=84 if first==221 else 87
        fixed_tiles={q['tile'] for n in aliases for bi in [5,6,7] for q in composition_frame(c,bi,n)['parts']}
        mutable={q['tile'] for n in aliases for bi in [0,8] for q in composition_frame(c,bi,n)['parts']}
        if fixed_tiles&mutable:raise ValueError('Upper armor shares lower-body storage')
        free=set(range(f['tile_count']))-fixed_tiles;used_all=set();details=[]
        for bi in [0,8]:
            images=[];comps=[composition_frame(c,bi,n) for n in aliases]
            for n in aliases:
                path=art/f'bank{bi}_{n:03}.png';im=Image.open(path)
                if im.mode!='P' or im.size!=(160,160) or max(im.tobytes())>15 or im.info.get('transparency')!=0:raise ValueError('Invalid hover indexed raster')
                words=struct.unpack_from('<16H',es[9],0 if bi==0 else 32)
                colors=[v for w in words for v in ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31)]
                if im.getpalette()[:48]!=colors:raise ValueError('Hover palette differs from parent')
                v=np.array(im);old=canvas_from_parts(before,f['tile_count'],composition_frame(c,bi,n))
                if not np.array_equal(v[:cut],old[:cut]):raise ValueError('Hover upper body changed')
                images.append(v);targets[bi,n]=v;hashes[path.name]=digest(path)
            raw,assignments=pack_many(raw,f['tile_count'],images,free,[len(cp['parts']) for cp in comps])
            used={r[0] for rr in assignments for r in rr};used_all|=used;free-=used
            for n,cp,rr in zip(aliases,comps,assignments):
                if not rr or len(rr)>len(cp['parts']):raise ValueError('Part count increased')
                for i,q in enumerate(cp['parts']):
                    if q['page'] or q['clut'] or q['unknown_flags']:raise ValueError('Unsupported hover part flags')
                    t,x,y,flip=rr[min(i,len(rr)-1)];value=struct.pack('<BBbb',flip,t,x-80,y-80);pos=q['record_offset']
                    if pos in allowed_records and allowed_records[pos]!=value:raise ValueError('Shared composition conflict')
                    allowed_records[pos]=value;nc[pos:pos+4]=value
            details.append({'bank':bi,'tiles':sorted(used),'records':assignments})
        for n in aliases:
            for bi in [0,5,6,7,8]:
                old=canvas_from_parts(before,f['tile_count'],composition_frame(c,bi,n));new=canvas_from_parts(raw,f['tile_count'],composition_frame(nc,bi,n))
                if not np.array_equal(new,targets.get((bi,n),old)):raise ValueError('Hover raster roundtrip mismatch')
        code=encode_stream(raw)
        if len(code)>f['limit']-f['offset']:raise ValueError('Hover exceeds original compressed slot; no repack authorized')
        ng,compression=replace_reserved_slot(ng,f,raw)
        for n in aliases:streams[n]=raw
        report.append({'aliases':aliases,'cut_y':cut,'layers':details,'compression':compression})
    checked=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        a=graphics_bank(g,bi,allow_bank_aliases=True);b=graphics_bank(ng,bi,allow_bank_aliases=True)
        if (a['base'],a['end'],len(a['frames']))!=(b['base'],b['end'],len(b['frames'])):raise ValueError('Bank boundary changed')
        for old,new in zip(a['frames'],b['frames']):
            if old['tile_count']!=new['tile_count']:raise ValueError('Tile count changed')
            v=decode_stream(g,old['offset'],old['limit'],old['tile_count']*128).data;nv=decode_stream(ng,new['offset'],new['limit'],new['tile_count']*128).data
            if nv!=(streams.get(old['index'],v) if bi==0 else v):raise ValueError('Unselected bitmap changed')
            checked+=1
    untouched=0
    for bi,offset in enumerate(bank_offsets(c)):
        count=struct.unpack_from('<I',c,offset)[0]>>16
        for n in range(count):
            if bi in [0,8] and n in FRAMES:continue
            if composition_frame(c,bi,n)!=composition_frame(nc,bi,n):raise ValueError('Unselected composition changed')
            untouched+=1
    result=bytearray(arc)
    for t,data in [(2,ng),(3,nc)]:
        e=next(e for e in psx_arc(arc) if int(e['type'],16)==t)
        if len(data)!=e['size']:raise ValueError('Entry size changed')
        result[e['offset']:e['offset']+e['size']]=data
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text())
    recipe={'task':'fourth_armor_shibuki','scope':'fourth_armor_hover_alignment_4','parent_build':PARENT,'parent_bin_sha256':PARENT_BIN,'parent_arc_sha256':PARENT_ARC,'original_arc_sha256':cfg['archive']['sha256'],'modified_arc_sha256':sha256(result),'source_art':str(art.relative_to(ROOT)),'art_hashes':hashes,'edited_frame_references':FRAMES,'changed_composition_banks':[0,8],'checked_bitmap_references':checked,'checked_other_compositions':untouched,'upper_body_rasters_preserved':True,'other_frames_and_armor_layers_preserved':True,'palette_preserved':True,'resources_relocated_within_bank':False,'archive_size_and_lba_preserved':True,'run_frames_preserved':True,'shooting_body_uses_same_run_pose':True,'shooting_arm_art_pending':False,'armor_frames_cumulative':pm['armor_frames_cumulative'],'compression':report,'runtime_verified':False,'approval':{'date':'2026-10-27','scope':'전진 호버의 발과 추진 불꽃 연결 수정','user_quote':'양발이 다 앞에있어서 불꽃이 그냥 공중에 떠있는걸로보여 이거 수정만 부탁할게'}}
    return bytes(result),recipe

def main():
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);a=p.parse_args();art=a.art.resolve()
    if not art.is_relative_to(ROOT/'work/ver_buki_riko/shibuki_hover_alignment'):raise ValueError('Isolated hover artwork required')
    arc,recipe=prepare(art);out=new_run(ROOT,'ver_buki_riko','shibuki_fourth_hover_alignment');(out/'modified.arc').write_bytes(arc);write_json(out/'recipe.json',recipe);print(json.dumps({'output':str(out),'sha256':sha256(arc),'streams':recipe['compression']}))
if __name__=='__main__':main()
