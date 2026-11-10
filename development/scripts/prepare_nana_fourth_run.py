"""수용 대기를 보존하고 이동·이동 사격32참조의 아머 타일만 패킹한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_run_art import PARENT,PARENT_SHA,LAYERS
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.project import digest
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_armor_remaining import pack_many
from scripts.prepare_shibuki_armor_motion import fit
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank

FRAMES=list(range(1,33))


def pack_layers(raw,count,targets,aliases,pool,c,frozen=None,active_banks=None):
    """Reserve space for later layers before accepting an eager pair layout."""
    specs=[]
    for name,b in LAYERS.items():
        if active_banks is not None and b not in active_banks:continue
        images=[targets[n][b] for n in aliases]
        counts=[len(composition_frame(c,b,n)['parts'])-len((frozen or {}).get((n,b),[])) for n in aliases]
        fits=[fit(im>0,limit) for im,limit in zip(images,counts)]
        require(all(r is not None for r in fits),f'Frames {aliases}, {name}: part count exceeded')
        specs.append((name,b,images,counts,max(1,max(map(len,fits)))))
    def visit(i,current,free):
        if i==len(specs):return current,[]
        name,b,images,counts,lower=specs[i]
        upper=len(free)-sum(s[4] for s in specs[i+1:])
        for budget in range(upper,lower-1,-1):
            slots=set(sorted(free,key=lambda t:(t%16==0,t))[:budget])
            try:changed,records=pack_many(current,count,images,slots,counts)
            except ValueError:continue
            used={r[0] for rr in records for r in rr}
            result=visit(i+1,changed,free-used)
            if result is not None:return result[0],[(name,b,records,used)]+result[1]
        return None
    result=visit(0,raw,pool)
    require(result is not None,f'Frames {aliases}: no shared tile layout within original capacity')
    return result


def prepare(art,out,profile='run'):
    require(profile in ('run','air','wall','dash','reaction','hurt_extra','ladder','ceremony','special','elemental','hover','vehicle'),'Unsupported motion profile')
    parent,parent_sha,frames=PARENT,PARENT_SHA,FRAMES
    if profile=='air':
        from scripts.prepare_nana_fourth_air_reference import PARENT as ap,PARENT_SHA as ah,FRAMES as af
        parent,parent_sha,frames=ap,ah,af
    if profile=='wall':
        from scripts.prepare_nana_fourth_wall_reference import PARENT as wp,PARENT_SHA as wh,FRAMES as wf
        parent,parent_sha,frames=wp,wh,wf
    if profile=='dash':
        from scripts.prepare_nana_fourth_dash_reference import PARENT as dp,PARENT_SHA as dh,FRAMES as df
        parent,parent_sha,frames=dp,dh,df
    if profile=='reaction':
        from scripts.prepare_nana_fourth_reaction_reference import PARENT as rp,PARENT_SHA as rh,FRAMES as rf
        parent,parent_sha,frames=rp,rh,rf
    if profile=='hurt_extra':
        from scripts.prepare_nana_fourth_hurt_extra_reference import PARENT as hp,PARENT_SHA as hh,FRAMES as hf
        parent,parent_sha,frames=hp,hh,hf
    if profile=='ladder':
        from scripts.prepare_nana_fourth_ladder_reference import PARENT as lp,PARENT_SHA as lh,FRAMES as lf
        parent,parent_sha,frames=lp,lh,lf
    if profile=='ceremony':
        from scripts.prepare_nana_fourth_ceremony_reference import PARENT as cp,PARENT_SHA as ch,FRAMES as cf
        parent,parent_sha,frames=cp,ch,cf
    if profile=='special':
        from scripts.prepare_nana_fourth_special_reference import PARENT as sp,PARENT_SHA as sh,FRAMES as sf
        parent,parent_sha,frames=sp,sh,sf
    if profile=='elemental':
        from scripts.prepare_nana_fourth_elemental_reference import PARENT as ep,PARENT_SHA as eh,FRAMES as ef
        parent,parent_sha,frames=ep,eh,ef
    if profile=='hover':
        from scripts.prepare_nana_fourth_hover_reference import PARENT as hp,PARENT_SHA as hh,FRAMES as hf
        parent,parent_sha,frames=hp,hh,hf
    if profile=='vehicle':
        from scripts.prepare_nana_fourth_vehicle_reference import PARENT as vp,PARENT_SHA as vh,FRAMES as vf
        parent,parent_sha,frames=vp,vh,vf
    art,out=art.resolve(),out.resolve();require(art.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh variant paths required')
    approval=json.loads((ROOT/'projects/ver_rin_nana/nana_fourth_candidate.json').read_text('utf8'))
    require(approval['art_user_approved'] and approval['full_animation_production_approved'] and approval['partial_outfit_assignment'],'Armor production approval required')
    require(digest(parent/'rin_nana.bin')==parent_sha,'Unsupported parent')
    meta=json.loads((art/'layers.json').read_text('utf8'));require(meta['frames']==frames and meta['parent_sha256']==parent_sha,'Art scope differs')
    arc=(parent/'modified.arc').read_bytes();g,c,p=entry(arc,2),entry(arc,3),entry(arc,9);words=struct.unpack_from('<16H',p,32)
    require(meta['palette_words']==list(words),'Art palette differs')
    bank=graphics_bank(g,0,allow_bank_aliases=True);targets={};hashes={}
    for n in frames:
        targets[n]={}
        for name,b in LAYERS.items():
            path=art/f'{name}_{n:03}.png';im=Image.open(path)
            require(im.mode=='P' and im.size==(160,160) and im.info.get('transparency')==0 and max(im.tobytes())<=15,'Unsupported layer image')
            targets[n][b]=np.array(im);hashes[path.name]=digest(path)
    nc=bytearray(c);changed_records={};expected={};reports=[];groups={};base_slot_shifts={}
    for n in frames:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
    for offset,aliases in groups.items():
        f=bank['frames'][aliases[0]];require([q['index'] for q in bank['frames'] if q['offset']==offset]==aliases,'Unselected stream aliases')
        before=decode_stream(g,offset,f['limit'],f['tile_count']*128).data;raw=before
        corrected_base_tiles=set();base_targets={}
        if profile=='hover' and aliases[0]>=221:
            from scripts.prepare_nana_fourth_hover_art import clear_base_below,CUTS
            raw,corrected_base_tiles,base_targets=clear_base_below(raw,f['tile_count'],c,aliases,CUTS)
            for n,v in base_targets.items():require(np.array_equal(v,np.array(Image.open(art/f'base_{n:03}.png'))),'Hover base erasure differs')
        if profile in ('wall','dash'):
            from scripts.prepare_nana_fourth_wall_gun import patch_base,fit_pistol_coverage
            for regular,shoot in zip(aliases[::2],aliases[1::2]):
                reg=next(q for q in meta['registration'] if q['frame']==(71 if regular==73 else regular))
                target=np.array(Image.open(art/f'base_{shoot:03}.png'))
                rc,sc=composition_frame(nc,0,regular),composition_frame(nc,0,shoot)
                if profile=='dash' and shoot==74:
                    require(np.array_equal(canvas_from_parts(raw,f['tile_count'],sc),target),'Speed-line pistol alias differs')
                    base_targets[shoot]=target
                    continue
                if profile=='dash':
                    raw,sc,shifts=fit_pistol_coverage(raw,f['tile_count'],rc,sc,target)
                    for q in shifts:
                        pos=q['record_offset'];value=struct.pack('<BBbb',q['flags'],q['tile'],q['x'],q['y'])
                        require(pos not in changed_records,'Base part shift conflict');changed_records[pos]=value;nc[pos:pos+4]=value;corrected_base_tiles.add(q['tile'])
                    if shifts:base_slot_shifts[str(shoot)]=shifts
                raw,tiles=patch_base(raw,f['tile_count'],rc,sc,target,reg['wall_pistol_adjustment']['registered_box'])
                corrected_base_tiles.update(tiles);base_targets[shoot]=target
        base_tiles={q['tile'] for n in aliases for q in composition_frame(c,0,n)['parts']}
        pool={q['tile'] for n in aliases for b in LAYERS.values() for q in composition_frame(c,b,n)['parts']}
        head_only=profile=='vehicle' and aliases[0]>=184
        if head_only:
            # 탑승 머리는 세 타일뿐이다. 공용 빈 타일과198은 쓰지 않는다.
            pool={q['tile'] for n in aliases if n!=198 for q in composition_frame(c,5,n)['parts']}
        require(not base_tiles&pool,'Armor/base tile collision');allocation=[];frozen={};storage_targets=targets
        if profile=='reaction':
            from scripts.prepare_nana_fourth_reaction_art import effect_parts
            storage_targets={n:{} for n in aliases}
            for n in aliases:
                for name,b in LAYERS.items():
                    frozen[n,b]=effect_parts(c,b,n)['parts'];pool-={q['tile'] for q in frozen[n,b]}
                    storage_targets[n][b]=np.array(Image.open(art/f'{name}_costume_{n:03}.png'))
        packing_aliases=[n for n in aliases if n!=198] if head_only else aliases;ladder_mirrors={}
        if profile=='ladder':
            from scripts.prepare_nana_fourth_ladder_art import MIRRORS
            ladder_mirrors={alias:(source,total) for source,(alias,total) in MIRRORS.items() if alias in aliases}
            packing_aliases=[n for n in aliases if n not in ladder_mirrors]
            # Store mirrored partners once, with identical source pixels.
            # A mirrored GPU quad must not start at texture-page column zero.
            if ladder_mirrors:pool={t for t in pool if t%16!=0}
        raw,packed=pack_layers(raw,f['tile_count'],storage_targets,packing_aliases,pool,c,frozen,{5} if head_only else None)
        if ladder_mirrors:
            expanded=[]
            for name,b,records,used in packed:
                mapping=dict(zip(packing_aliases,records))
                for alias,(source,total) in ladder_mirrors.items():
                    mapping[alias]=[(t,total-x-15,y,flag^64) for t,x,y,flag in mapping[source]]
                expanded.append((name,b,[mapping[n] for n in aliases],used))
            packed=expanded
        for name,b,records,used in packed:
            write_aliases=packing_aliases if head_only else aliases
            comps=[composition_frame(c,b,n) for n in write_aliases]
            for n,comp,rr in zip(write_aliases,comps,records):
                editable=[q for q in comp['parts'] if q not in frozen.get((n,b),[])]
                require(0<len(rr)<=len(editable),'Part count expansion')
                for i,q in enumerate(editable):
                    require(not(q['page'] or q['clut'] or q['unknown_flags']),'Unknown part flags')
                    t,x,y,flag=rr[min(i,len(rr)-1)];value=struct.pack('<BBbb',flag,t,x-80,y-80);pos=q['record_offset']
                    require(pos not in changed_records or changed_records[pos]==value,'Shared part record conflict');changed_records[pos]=value;nc[pos:pos+4]=value
                require(np.array_equal(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,b,n)),targets[n][b]),'Layer readback differs')
            allocation.append({'bank':b,'tiles':sorted(used),'parts':records})
        oa=np.frombuffer(indexed_atlas(before,f['tile_count'])[0],np.uint8).reshape(-1,256);na=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
        for t in range(f['tile_count']):
            if t not in pool|corrected_base_tiles:require(np.array_equal(oa[t//16*16:t//16*16+16,t%16*16:t%16*16+16],na[t//16*16:t//16*16+16,t%16*16:t%16*16+16]),'Base/effect tile changed')
        for n in aliases:
            target=base_targets.get(n,canvas_from_parts(before,f['tile_count'],composition_frame(c,0,n)))
            require(np.array_equal(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,0,n)),target),'Base render changed outside correction');expected[n]=raw
        reports.append({'frames':aliases,'allocation':allocation,'encoded_bytes':len(encode_stream(raw)),'capacity':f['limit']-offset})
        print(json.dumps({'frames':aliases,'packed_bytes':reports[-1]['encoded_bytes'],'capacity':reports[-1]['capacity']}),flush=True)
    compressed={n:encode_stream(raw) for n,raw in expected.items()};ng=g;repack=None;compression=[]
    if all(len(compressed[ns[0]])<=bank['frames'][ns[0]]['limit']-off for off,ns in groups.items()):
        for ns in groups.values():
            descriptor=bank['frames'][ns[0]]
            ng,check=replace_stream(ng,descriptor,expected[ns[0]],allocated_limit=descriptor['limit'] if profile=='vehicle' else None);compression.append(check)
    else:
        require(profile not in ('ladder','ceremony','special','elemental','hover','vehicle'),'This profile must fit existing stream slots; no automatic bank relocation')
        ng,repack=repack_graphics_bank(g,0,compressed)
    checked=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        ob=graphics_bank(g,bi,allow_bank_aliases=True);nb=graphics_bank(ng,bi,allow_bank_aliases=True)
        require((ob['base'],ob['end'],len(ob['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Bank boundaries changed')
        for f,nf in zip(ob['frames'],nb['frames']):
            require(f['tile_count']==nf['tile_count'],'Tile count changed')
            old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;actual=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
            require(actual==(expected[f['index']] if bi==0 and f['index'] in expected else old),'Unexpected bitmap reference change');checked+=1
    other=0
    for bi,off in enumerate(bank_offsets(c)):
        for n in range(struct.unpack_from('<I',c,off)[0]>>16):
            if (bi in LAYERS.values() and n in frames) or (bi==0 and str(n) in base_slot_shifts):continue
            require(composition_frame(c,bi,n)==composition_frame(nc,bi,n),'Other composition changed');other+=1
    allowed={pos+i for pos in changed_records for i in range(4)};require(all(i in allowed for i,(a,b) in enumerate(zip(c,nc)) if a!=b),'Composition write outside selected records')
    result=bytearray(arc)
    for kind,data in ((2,ng),(3,bytes(nc))):
        e=next(e for e in psx_arc(arc) if int(e['type'],16)==kind);require(len(data)==e['size'],'Entry length changed');result[e['offset']:e['offset']+e['size']]=data
    out.mkdir(parents=True);(out/'modified.arc').write_bytes(result)
    for n in frames:
        f=bank['frames'][n];base=canvas_from_parts(expected[n],f['tile_count'],composition_frame(nc,0,n))
        for mask in range(16):
            merged=base.copy()
            for bit,b in ((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:merged=np.where(targets[n][b],targets[n][b],merged)
            save_image(merged.tobytes(),(160,160),words,out/f'frame_{n:03}_mask{mask:02}.png')
        require(np.array_equal(np.array(Image.open(out/f'frame_{n:03}_mask15.png')),np.array(Image.open(art/f'full_{n:03}.png'))),'Combined armor differs')
    recipe={'task':'fourth_armor_nana','parent':parent.relative_to(ROOT).as_posix(),'parent_sha256':parent_sha,'parent_arc_sha256':sha256(arc),'modified_arc_sha256':sha256(result),'frames':frames,'art':art.relative_to(ROOT).as_posix(),'art_hashes':hashes,'allocation':reports,'compression':compression,'repack':repack,'checked_bitmap_references':checked,'other_compositions_preserved':other,'base_tiles_rasters_and_palettes_preserved':True,'palette_bytes_identical':True,'partial_outfit_assignment':approval['partial_outfit_assignment'],'runtime_verified':False}
    if profile in ('wall','dash'):
        recipe['base_tiles_rasters_and_palettes_preserved']=False
        recipe['base_'+profile+'_pistol_correction']={str(q['shot']):q['wall_pistol_adjustment'] for q in meta['registration']}
        recipe['all_other_base_pixels_preserved']=True
        recipe['base_pistol_slot_shifts']=base_slot_shifts
    if profile=='hover':
        recipe.update(base_tiles_rasters_and_palettes_preserved=False,base_lower_cut=meta['base_lower_cut'],base_upper_and_all_other_frames_preserved=True,hover_requires_leg_armor=True)
    if profile=='vehicle':
        recipe.update(edited_frames=meta['edited_frames'],blank_preserved=[198],head_only_frames=[n for n in frames if n>=184 and n!=198])
    write(out/'recipe.json',recipe);print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'sha256':sha256(result),'frames':len(frames),'repacked':repack is not None}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--profile',choices=('run','air','wall','dash','reaction','hurt_extra','ladder','ceremony','special','elemental','hover','vehicle'),default='run');a=p.parse_args();prepare(a.art,a.output,a.profile)
