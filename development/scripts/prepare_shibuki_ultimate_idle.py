"""Same-slot Ultimate standing pilot; protects all other frames and accepted PL00."""
import argparse,json,struct,sys,random
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D,PARENT,PARENT_SHA,SOURCE_SHA,load
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_idle import breathe
from scripts.prepare_shibuki_weapon_palette import WEAPON_ROWS,FLASHES
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from src.psx_tile_layout import pack_rectangles,remap_tiles
from src.psx_compress import replace_stream,encode_stream
from src.psx_armor_palette import replace_armor_palette_rows

FRAMES=(0,115,116,117,118,119)
BASE_ROWS=[0,*WEAPON_ROWS,*FLASHES]

def fit_tiles(raw,count,tiles,budget):
    """Try lossless tile storage orders/flips; never simplify art to fit."""
    tiles=sorted(tiles);rng=random.Random(27027);initial=len(encode_stream(raw));best=initial
    if initial<=budget:return raw,{t:t for t in tiles},{},initial,0
    for attempt in range(160):
        dst=tiles.copy()
        if attempt>=2:rng.shuffle(dst)
        flips={t:64 for t in tiles} if attempt%3==0 else ({t:64 for t in tiles if rng.getrandbits(1)} if attempt%3==1 else {})
        mapping=dict(zip(tiles,dst))
        try:candidate=remap_tiles(raw,count,mapping,flips)
        except ValueError:continue
        size=len(encode_stream(candidate));best=min(best,size)
        if size<=budget:return candidate,mapping,flips,size,attempt+1
    raise ValueError(f'Lossless tile layouts still exceed slot: best {best}, budget {budget}')

def copy_tiles(source,source_count,target,target_count,tiles):
    sa,_,_=indexed_atlas(source,source_count);_,positions,_=indexed_atlas(target,target_count);out=bytearray(target)
    for tile in tiles:
        for y in range(16):
            for x in range(16):
                k=(tile//16*16+y)*256+tile%16*16+x;off,shift=positions[k];out[off]=(out[off]&~(15<<shift))|(sa[k]<<shift)
    return bytes(out)

def prepare(output,art):
    output=output.resolve();art=art.resolve()
    if not output.is_relative_to(D) or not art.is_relative_to(D):raise ValueError('Expected isolated work paths')
    if output.exists():raise ValueError('Refuse output overwrite')
    records,arcs=load();parent=arcs['parent']['PL02_U.ARC'];basearc=arcs['parent']['PL00_U.ARC'];g,c,pal=(entry(parent,k) for k in (2,3,9));bg,bc,bp=(entry(basearc,k) for k in (2,3,9))
    norm=json.loads((art/'normalization.json').read_text());im=Image.open(art/'outfit.png');words=norm['palette_words']
    if im.mode!='P' or im.size!=(160,160) or im.info.get('transparency')!=0 or max(im.tobytes())>15:raise ValueError('Expected indexed artwork')
    v=np.array(im);original_art=v.copy();bank=graphics_bank(g,0,allow_bank_aliases=True);basebank=graphics_bank(bg,0,allow_bank_aliases=True);base={};base_raw={}
    for n in FRAMES:
        f=basebank['frames'][n];raw=decode_stream(bg,f['offset'],f['limit'],f['tile_count']*128).data;base_raw[n]=raw;base[n]=canvas_from_parts(raw,f['tile_count'],composition_frame(bc,0,n))
    # Extend only the generated edge colors needed by the engine's overlay silhouette.
    # Record every registration pixel, rather than silently retaining red base clothes.
    filled=[];coords=np.argwhere(v>0)
    for y,x in np.argwhere((base[0]>0)&(v==0)):
        distance=((coords-[y,x])**2).sum(1);i=int(np.argmin(distance));sy,sx=coords[i]
        if distance[i]>17:raise ValueError('Generated silhouette requires a new art correction')
        v[y,x]=original_art[sy,sx];filled.append({'destination':[int(x),int(y)],'source':[int(sx),int(sy)],'distance_squared':int(distance[i])})
    # The generated ornament retains some reference pink. Palette-register that
    # accessory only to the requested navy flower; ears/skin/glasses are excluded.
    ornament=[]
    for y,x in np.argwhere((np.indices(v.shape)[1]>=83)&(np.indices(v.shape)[1]<=89)&(np.indices(v.shape)[0]>=62)&(np.indices(v.shape)[0]<=67)&np.isin(v,[10,11,12])):
        ornament.append([int(x),int(y),int(v[y,x])]);v[y,x]=4 if v[y,x]==10 else 1
    expected={};armor_expected={};eye_windows={}
    for n,delta in ((0,0),(115,1),(116,1),(117,1),(118,1),(119,-1)):
        target=np.zeros_like(v);target[55:103,61:109]=breathe(v[55:103,61:109],delta)
        if np.any((base[n]>0)&(target==0)):raise ValueError('Underlying accepted base leaks through')
        # Ultimate's armor composition aliases all four blink frames. Preserve
        # the accepted base eye underneath a tiny transparent armor window.
        mask=np.zeros_like(v,dtype=bool);mask[70+delta:73+delta,75:78]=True
        if np.any(base[n][mask]==0):raise ValueError('Eye window exposes empty base')
        target[mask]=0;armor_expected[n]=target;eye_windows[n]=mask
        expected[n]=np.where(target>0,target,base[n]).astype(np.uint8)
        basewords=struct.unpack_from('<16H',bp)
        if any(words[int(i)]!=basewords[int(i)] for i in np.unique(base[n][mask])):raise ValueError('Eye palette differs from armor face')
    nc=bytearray(c);ng=g;compression=[];allowed=set();changed_raw={};base_tile_proofs=[]
    for representative,refs in ((0,[0]),(115,[115,116,117,118]),(119,[119])):
        f=bank['frames'][representative];bf=basebank['frames'][representative];old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        if [q['index'] for q in bank['frames'] if q['offset']==f['offset']]!=refs:raise ValueError('Unexpected shared stream')
        base_tiles={q['tile'] for n in refs for q in composition_frame(bc,0,n)['parts']};armor_tiles={q['tile'] for n in refs for q in composition_frame(c,5,n)['parts']};other_tiles={q['tile'] for n in refs for bi in (6,7,8) for q in composition_frame(c,bi,n)['parts']}
        if base_tiles&armor_tiles or base_tiles&other_tiles or armor_tiles&other_tiles:raise ValueError('Tile ownership conflict')
        raw=copy_tiles(base_raw[representative],bf['tile_count'],old,f['tile_count'],base_tiles)
        rects=[[64,y] for y in (55,71,87)]+[[80,y] for y in (55,71,87)];ids=sorted(t for t in armor_tiles if t%16)[:6]
        if len(ids)!=6:raise ValueError('Not enough safe armor tiles')
        raw=pack_rectangles(raw,f['tile_count'],armor_expected[representative].tobytes(),(160,160),rects,ids,armor_tiles)
        eye_id=None
        for n in refs:
            source_parts=composition_frame(bc,0,n)['parts'];target_parts=composition_frame(c,0,n)['parts']
            if len(source_parts)!=len(target_parts):raise ValueError('Base part count differs')
            for src,dst in zip(source_parts,target_parts):
                struct.pack_into('<BBbb',nc,dst['record_offset'],src['flags'],src['tile'],src['x'],src['y']);allowed.update(range(dst['record_offset'],dst['record_offset']+4))
            parts=composition_frame(c,5,n)['parts']
            if len(parts)<6:raise ValueError('Armor part shortage')
            for i,q in enumerate(parts):
                j=min(i,5);tile=ids[j];x,y=rects[j]
                struct.pack_into('<BBbb',nc,q['record_offset'],0,tile,x-80,y-80);allowed.update(range(q['record_offset'],q['record_offset']+4))
            if not np.array_equal(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,0,n)),base[n]):raise ValueError('Accepted base copy mismatch')
            if not np.array_equal(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,5,n)),armor_expected[n]):raise ValueError('New outfit does not roundtrip')
            changed_raw[n]=raw
        # Blank body/arm/leg layers must remain byte-for-byte untouched.
        oa,_,_=indexed_atlas(old,f['tile_count']);na,_,_=indexed_atlas(raw,f['tile_count'])
        for t in set(range(f['tile_count']))-base_tiles-armor_tiles:
            for y in range(16):
                off=(t//16*16+y)*256+t%16*16
                if oa[off:off+16]!=na[off:off+16]:raise ValueError('Non-target texel changed')
        budget=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).end-f['offset']
        raw,mapping,flips,_,attempts=fit_tiles(raw,f['tile_count'],set(ids)|({eye_id} if eye_id is not None else set()),budget)
        visited=set()
        for n in refs:
            for q in composition_frame(nc,5,n)['parts']:
                if q['record_offset'] not in visited and q['tile'] in mapping:struct.pack_into('<BB',nc,q['record_offset'],q['flags']^flips.get(q['tile'],0),mapping[q['tile']]);visited.add(q['record_offset'])
        for n in refs:
            if not np.array_equal(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,5,n)),armor_expected[n]):raise ValueError('Lossless storage transform changed pixels')
            changed_raw[n]=raw
        ng,r=replace_stream(ng,f,raw);r['lossless_layout_attempts']=attempts;r['tile_mapping']=mapping;r['tile_flips']=flips;compression.append(r);base_tile_proofs.append({'refs':refs,'base_tiles':sorted(base_tiles),'armor_tiles':sorted(armor_tiles),'untouched_other_tiles':sorted(other_tiles)})
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(c,nc))):raise ValueError('Composition mutation escaped selected records')
    others=0
    for bi,offset in enumerate(bank_offsets(c)):
        for n in range(struct.unpack_from('<I',c,offset)[0]>>16):
            if bi in (0,5) and n in FRAMES:continue
            if composition_frame(c,bi,n)!=composition_frame(nc,bi,n):raise ValueError('Protected composition modified')
            others+=1
    decoded=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        ob=graphics_bank(g,bi,allow_bank_aliases=True);nb=graphics_bank(ng,bi,allow_bank_aliases=True)
        if ob!=nb:raise ValueError('Stream addresses or tile counts changed')
        for f in ob['frames']:
            before=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;after=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data
            want=changed_raw[f['index']] if bi==0 and f['index'] in FRAMES else before
            if after!=want:raise ValueError('Protected compressed asset differs')
            decoded+=1
    npal=bytearray(pal)
    for row in BASE_ROWS:npal[row*32:(row+1)*32]=bp[row*32:(row+1)*32]
    npal,armor_rows=replace_armor_palette_rows(bytes(npal),words,[0,*FLASHES],FLASHES,weapon_rows=WEAPON_ROWS)
    result=parent
    for kind,data in ((2,ng),(3,bytes(nc)),(9,npal)):result=replace_entry(result,kind,data)
    if len(result)!=len(parent):raise ValueError('ARC resized')
    output.mkdir();(output/'PL02_U.ARC').write_bytes(result);pictures=[]
    for n in FRAMES:
        save_image(base[n].tobytes(),(160,160),struct.unpack_from('<16H',bp),output/f'base_{n:03}.png')
        save_image(armor_expected[n].tobytes(),(160,160),words,output/f'overlay_{n:03}.png')
        pic=save_image(expected[n].tobytes(),(160,160),words,output/f'ultimate_{n:03}.png').convert('RGBA');pictures.append(pic)
    sheet=Image.new('RGB',(1020,620),'#253546');dr=ImageDraw.Draw(sheet)
    for i,(path,label) in enumerate([(output/'base_000.png','Accepted Shibuki'),(D/'analysis/parent_PL00_U.ARC_full_000.png','Accepted Fourth'),(output/'ultimate_000.png','Ultimate - jacket pilot')]):
        pic=Image.open(path).convert('RGBA');small=pic.crop((50,50,110,110));sheet.paste(small,(i*340+135,45),small);large=small.resize((300,300),Image.Resampling.NEAREST);sheet.paste(large,(i*340+20,130),large);dr.text((i*340+12,12),label,fill='white')
    dr.text((20,465),'Native 1x + nearest 5x | Same standing bounds: 26 x 47 | Sole row 102',fill='white');dr.text((20,490),'Static reconstruction from patched ARC; not an in-game capture.',fill='white');sheet.save(output/'review.png')
    steps=json.loads((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json').read_text())['idle_animation']['steps'];ims=[];dur=[]
    for step in steps:
        pic=pictures[list(FRAMES).index(step['frame'])];canvas=Image.new('RGB',(160,160),'#253546');canvas.paste(pic,(0,0),pic);ims.append(canvas.crop((50,50,110,110)).resize((360,360),Image.Resampling.NEAREST));dur.append(max(20,round((step['duration_ticks']+1)*1000/60)))
    ims[0].save(output/'idle.gif',save_all=True,append_images=ims[1:],duration=dur,loop=0,disposal=2)
    recipe={'task':'ultimate_armor_shibuki','kind':'ultimate_idle_pilot','source_sha256':SOURCE_SHA,'parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_SHA,'parent_arc_sha256':sha256(parent),'accepted_base_arc_sha256':sha256(basearc),'modified_arc_sha256':sha256(result),'source_record':records['PL02_U.ARC'],'source_art':str(art.relative_to(ROOT)),'source_art_sha256':sha256((art/'outfit.png').read_bytes()),'frames':list(FRAMES),'compression':compression,'tile_ownership':base_tile_proofs,'registered_edges':filled,'navy_ornament_palette_registration':ornament,'body_palette_rows':BASE_ROWS,'armor_palette_rows':armor_rows,'palette_words':words,'checked_bitmap_refs':decoded,'protected_compositions':others,'native_size':[26,47],'foot_center':79,'sole_y':102,'resources_relocated':False,'exe_changed':False,'timing_changed':False,'runtime_verified':False,'full_ultimate_complete':False,'unimplemented_frames_still_original_x_with_changed_palette':True,'pre_capsule_base_copy_only_these_six_frames':True}
    (output/'recipe.json').write_text(json.dumps(recipe,indent=2));print(json.dumps({'output':str(output),'sha256':sha256(result),'compression':compression,'protected_compositions':others,'bitmap_refs':decoded}));return recipe

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art',type=Path,default=D/'normalized03');a=p.parse_args();prepare(a.output,a.art)
