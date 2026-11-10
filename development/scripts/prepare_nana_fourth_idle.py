"""수용 포스아머 원화를 기존 얼굴/발/권총에 등록하고 대기·사격 파츠를 패킹한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.prepare_nana_fourth_pilot import PARENT,PARENT_SHA,render,entry,require,write
from scripts.project import digest
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_armor_remaining import pack_many
from scripts.prepare_shibuki_weapon_palette import WEAPON_ROWS,FLASHES
from src.psx_armor_palette import replace_armor_palette_rows
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank

PILOT=ROOT/'out/ver_rin_nana/nana_fourth_pilot_v2'
REDRAW=ROOT/'work/ver_rin_nana/nana_fourth_armor/redraw_masters_v2'
FRAMES=[0,85,86,87,92,115,116,117,118,119]
LAYERS={'head':5,'body':6,'arm':7,'leg':8}


def desired_pose(arc,n,masters):
    _,base,_,_=render(arc,n)
    dy=1 if n in (115,116,117,118) else -1 if n==119 else 0
    target=masters[115 if dy==1 else 119 if dy==-1 else 0].copy()
    yy,xx=np.indices(base.shape)
    # The native face and eyelid are shared with the accepted unarmored Nana.
    face=((yy>=65+dy)&(yy<74+dy)&(xx>=74)&(xx<83))|((yy<74+dy)&(xx<75))
    target[face]=base[face]
    # Keep the accepted pistol, hand, recoil and recovery trajectory exactly.
    gun=(xx<74)&(yy>=66)&(yy<86)
    if n in (85,86,87):target[gun]=base[gun]
    # Match the already accepted native Nana's complete leg silhouettes in
    # EACH pose, not a fixed calf joined to a translated thigh. Replace the
    # old stocking interior by continuous skin with a single outer contour.
    for y in range(90,101):
        for lo,hi in ((66,78),(80,96)):
            xs=np.flatnonzero(base[y,lo:hi])+lo
            if not len(xs):continue
            left,right=int(xs.min()),int(xs.max())
            if lo==66 or y>=94:target[y,lo:hi]=0
            target[y,left:right+1]=1
            if right-left>=2:
                target[y,left+1:right]=12
                if right-left>=4:target[y,right-1]=11
    # The accepted native contact footprint is retained, with burgundy shoes.
    for y in (101,102):
        target[y]=np.where(base[y],1,0)
        if y==101:
            for lo,hi in ((64,79),(80,98)):
                xs=np.flatnonzero(base[y,lo:hi])+lo
                if len(xs)>2:target[y,xs[1:-1]]=5
    # Opaque armor cannot erase the underlying native silhouette. Extend only
    # its small exposed boundary using the nearest accepted costume texel.
    sy,sx=np.nonzero(target)
    missing=np.argwhere((base!=0)&(target==0))
    distances=[]
    for y,x in missing:
        dist=(sy-y)**2+(sx-x)**2;k=int(dist.argmin())
        require(dist[k]<=9,'Registration needs a larger artwork revision')
        target[y,x]=target[sy[k],sx[k]];distances.append(int(dist[k]))
    target[face]=base[face]
    if n in (85,86,87):target[gun]=base[gun]
    require(not np.any((base>0)&(target==0)),'Underlying sprite escapes target')
    delta=np.where(target!=base,target,0).astype(np.uint8)
    masks={5:(yy<73+dy)&(xx>=75)&(xx<91),8:(yy>=85+dy)|((xx>=90)&(yy>=66+dy)),
           7:((xx<74)&(yy>=66+dy)&(yy<85+dy))|((xx>=88)&(yy>=79+dy)&(yy<85+dy))}
    layers={b:np.zeros_like(base) for b in (5,6,7,8)}
    remaining=delta.copy()
    for b in (5,8,7):
        layers[b][masks[b]]=remaining[masks[b]];remaining[masks[b]]=0
    layers[6]=remaining
    merged=base.copy()
    for b in (8,5,7,6):merged=np.where(layers[b]!=0,layers[b],merged)
    require(np.array_equal(merged,target),'Layer partition differs')
    return base,target,layers,{'native_face_and_blink_preserved':True,'pistol_preserved':n in (85,86,87),
           'boundary_pixels_registered':len(missing),'maximum_boundary_squared_distance':max(distances,default=0),
           'base_pixels_outside_target':0,'breath_delta':dy}


def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh variant work path required')
    approval=json.loads((ROOT/'projects/ver_rin_nana/nana_fourth_candidate.json').read_text('utf8'))
    require(approval['art_user_approved'] and approval['full_animation_production_approved'],'Style approval required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent differs')
    arc=(PARENT/'modified.arc').read_bytes();g,c,p=entry(arc,2),entry(arc,3),entry(arc,9)
    masters={n:np.array(Image.open(REDRAW/f'master_{n:03}.png')) for n in (0,115,119)};words=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()))
    require((PILOT/'palette.bin').read_bytes()[:30]==p[:30],'Base face/hair palette differs')
    bank=graphics_bank(g,0,allow_bank_aliases=True);targets={};bases={};full={};registration={}
    for n in FRAMES:bases[n],full[n],targets[n],registration[n]=desired_pose(arc,n,masters)
    from scipy.ndimage import label
    for n in FRAMES:
        # Bare thighs and ankles must be connected through the knee/calf.
        for lo,hi in ((66,77),(80,93)):
            skin=np.isin(full[n][90:101,lo:hi],(11,12))
            components,_=label(skin,np.ones((3,3)))
            connected=(set(components[0])- {0}) & (set(components[-1])-{0})
            require(bool(connected),'Knee/calf skin continuity failed')
    nc=bytearray(c);changed_records={};expected={};reports=[]
    groups={}
    for n in FRAMES:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
    for offset,aliases in groups.items():
        f=bank['frames'][aliases[0]];allrefs=[q['index'] for q in bank['frames'] if q['offset']==offset]
        require(allrefs==aliases,'Unselected stream aliases')
        before=decode_stream(g,offset,f['limit'],f['tile_count']*128).data;raw=before
        base_tiles={q['tile'] for n in aliases for q in composition_frame(c,0,n)['parts']}
        armor_pool={q['tile'] for n in aliases for b in LAYERS.values() for q in composition_frame(c,b,n)['parts']}
        require(not base_tiles&armor_pool,'Base and armor tile conflict')
        free=armor_pool.copy();allocation=[]
        for name,b in LAYERS.items():
            comps=[composition_frame(c,b,n) for n in aliases]
            try:raw,records=pack_many(raw,f['tile_count'],[targets[n][b] for n in aliases],free,[len(cp['parts']) for cp in comps])
            except ValueError as e:raise ValueError(f'Frame {aliases} / {name}: {e}') from e
            used={r[0] for rr in records for r in rr};free-=used
            for n,comp,rr in zip(aliases,comps,records):
                require(len(rr)<=len(comp['parts']),'Part count expansion')
                for i,q in enumerate(comp['parts']):
                    require(not(q['page'] or q['clut'] or q['unknown_flags']),'Unsupported armor flags')
                    t,x,y,flag=rr[min(i,len(rr)-1)];value=struct.pack('<BBbb',flag,t,x-80,y-80);pos=q['record_offset']
                    require(pos not in changed_records or changed_records[pos]==value,'Shared record conflict')
                    changed_records[pos]=value;nc[pos:pos+4]=value
                require(np.array_equal(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,b,n)),targets[n][b]),'Layer roundtrip differs')
            allocation.append({'bank':b,'tiles':sorted(used),'parts':records})
        old_atlas=np.frombuffer(indexed_atlas(before,f['tile_count'])[0],np.uint8).reshape(-1,256)
        new_atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
        for t in range(f['tile_count']):
            if t not in armor_pool:require(np.array_equal(old_atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16],new_atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]),'Base/effect tile changed')
        for n in aliases:
            require(np.array_equal(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,0,n)),bases[n]),'Base render changed')
            expected[n]=raw
        reports.append({'frames':aliases,'allocation':allocation,'encoded_bytes':len(encode_stream(raw)),'capacity':f['limit']-offset})
    compressed={n:encode_stream(raw) for n,raw in expected.items()};ng=g;repack=None;compression=[]
    if all(len(compressed[ns[0]])<=bank['frames'][ns[0]]['limit']-off for off,ns in groups.items()):
        for ns in groups.values():ng,check=replace_stream(ng,bank['frames'][ns[0]],expected[ns[0]]);compression.append(check)
    else:ng,repack=repack_graphics_bank(g,0,compressed)
    checked=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        old_bank=graphics_bank(g,bi,allow_bank_aliases=True);new_bank=graphics_bank(ng,bi,allow_bank_aliases=True)
        require((old_bank['base'],old_bank['end'])==(new_bank['base'],new_bank['end']),'Bank boundary changed')
        for f,nf in zip(old_bank['frames'],new_bank['frames']):
            raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            actual=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
            require(actual==(expected[f['index']] if bi==0 and f['index'] in expected else raw),'Unexpected compressed reference change');checked+=1
    other_comps=0
    for bi,off in enumerate(bank_offsets(c)):
        count=struct.unpack_from('<I',c,off)[0]>>16
        for n in range(count):
            if bi in LAYERS.values() and n in FRAMES:continue
            require(composition_frame(c,bi,n)==composition_frame(nc,bi,n),'Other composition changed');other_comps+=1
    allowed={pos+i for pos in changed_records for i in range(4)}
    require(all(i in allowed for i,(a,b) in enumerate(zip(c,nc)) if a!=b),'Unexpected composition bytes')
    npal,rows=replace_armor_palette_rows(p,words,[0,*FLASHES],FLASHES,weapon_rows=WEAPON_ROWS)
    result=bytearray(arc)
    for kind,data_ in ((2,ng),(3,bytes(nc)),(9,npal)):
        e=next(e for e in psx_arc(arc) if int(e['type'],16)==kind);require(len(data_)==e['size'],'Entry length changed');result[e['offset']:e['offset']+e['size']]=data_
    out.mkdir(parents=True)
    for n,master in masters.items():save_image(master.tobytes(),(160,160),words,out/f'redraw_master_{n:03}.png')
    (out/'modified.arc').write_bytes(result);(out/'palette.bin').write_bytes(struct.pack('<16H',*words))
    pictures={}
    for n in FRAMES:
        for name,b in LAYERS.items():save_image(targets[n][b].tobytes(),(160,160),words,out/f'{name}_{n:03}.png')
        for mask in range(16):
            merged=bases[n].copy()
            for bit,b in ((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:merged=np.where(targets[n][b],targets[n][b],merged)
            pic=save_image(merged.tobytes(),(160,160),words,out/f'frame_{n:03}_mask{mask:02}.png').convert('RGBA');pictures[n,mask]=pic
        require(np.array_equal(np.array(Image.open(out/f'frame_{n:03}_mask15.png')),full[n]),'Full suit differs')
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    board=Image.new('RGB',(5*232,2*270),'#242934');draw=ImageDraw.Draw(board)
    for i,n in enumerate(FRAMES):
        x,y=i%5*232,i//5*270;draw.text((x+8,y+8),f'포스 나나 {n:03}',font=font,fill='white')
        im=pictures[n,15].crop((48,52,106,108)).resize((232,224),Image.Resampling.NEAREST);board.paste(im,(x,y+32),im)
    board.save(out/'family_4x.png')
    grid=Image.new('RGB',(4*240,4*256),'#242934');draw=ImageDraw.Draw(grid)
    for mask in range(16):
        x,y=mask%4*240,mask//4*256;draw.text((x+8,y+6),f'장착 {mask:04b}',font=font,fill='white')
        im=pictures[0,mask].crop((48,52,108,108)).resize((240,224),Image.Resampling.NEAREST);grid.paste(im,(x,y+30),im)
    grid.save(out/'partial_armor_proposal.png')
    inv=json.loads((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json').read_text('utf8'))
    seq=inv['idle_animation']['steps'];ims=[]
    for q in seq:
        im=Image.new('RGB',(288,240),'#242934');sprite=pictures[q['frame'],15].crop((48,52,120,112)).resize((288,240),Image.Resampling.NEAREST);im.paste(sprite,(0,0),sprite);ims.append(im)
    ims[0].save(out/'idle_preview.gif',save_all=True,append_images=ims[1:],duration=[max(20,round(q['duration_ticks']*1000/60)) for q in seq],loop=0)
    recipe={'task':'fourth_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,
            'parent_arc_sha256':sha256(arc),'modified_arc_sha256':sha256(result),'frames':FRAMES,'registration':registration,
            'allocation':reports,'palette_rows':rows,'compression':compression,'repack':repack,'checked_bitmap_references':checked,
            'other_compositions_preserved':other_comps,'base_tiles_rasters_and_palettes_preserved':True,
            'all_other_arc_entries_preserved':True,'partial_outfit_assignment':approval['partial_outfit_assignment'],
            'runtime_verified':False,'art_user_quote':approval['style_approval_quote'],
            'native_art_revision':'three whole-figure breathing drawings; native Nana leg silhouettes and continuous skin; no split-body shift',
            'knee_continuity_checks':len(FRAMES)*2,'redraw_sources':str(REDRAW.relative_to(ROOT)),
            'split_body_warp_used':False,'native_leg_silhouettes_preserved':True}
    write(out/'recipe.json',recipe)
    print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'sha256':sha256(result),'frames':len(FRAMES),'repacked':repack is not None,'registration':registration}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();prepare(args.output)
