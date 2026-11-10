"""수용된 포스아머 도트를 저장 파츠와 캡슐 획득 잔상에 연결한다."""
import argparse,itertools,json,random,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import binary_fill_holes,binary_dilation,binary_erosion
from PIL import Image,ImageDraw
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_riko_ui import replace_entry
from scripts.prepare_shibuki_ui import actual,transfer_geometry
from scripts.prepare_rin_ui_small import protected_repack,world
from scripts.verify_shibuki_save_icon import icon,rgba
from scripts.prepare_shibuki_armor_remaining import pack_many
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.extract_zero import save_image
from src.psx_player import composition_frame,graphics_bank,decode_stream,bank_offsets
from src.psx_ui_atlas import place_frame,local_composition,tile_pixels
from src.psx_static_effect import compose_static
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import replace_stream,encode_stream
from src.psx_tile_layout import remap_tiles
PARENT=ROOT/'out/ver_rin_nana/nana_fourth_vehicle_20261030T120015393777Z'
PARENT_SHA='5618ee1ab54f16bfee9b0a1b4d3472be3508da4babd8dce2ac7676f7c66d0e6d'
SOURCES={'MOJIPAT.ARC':(271,11420,'2fdefecabc9ca78d3a452e1fe7b3fcc52982c2e025d198987fc532dac3b52b67'),'LOAD_U.ARC':(222,100352,'b3f9f78f97d56926ecbeb7e19739ee67a1aabd60836a883e777c6eec5b53d445'),'PL00_U.ARC':(1135,796672,'4b1e41c5865979c8ba4bd733d69ab316a1c2262cb0bbd5a4e51a4eefc04b078f')}
SAVE={45:5,46:6,47:7,48:8}

def read_sources():
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Unsupported parent');out={};records=[]
    with (PARENT/'rin_nana.bin').open('rb') as f:
        disc=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size);iso={q['name']:q for q in disc.inspect()['files']}
        for name,(lba,size,sha) in SOURCES.items():
            q=iso[name+';1'];require((q['lba'],q['size'])==(lba,size),'Resource moved');v=disc.read(lba,size);require(sha256(v)==sha,'Source changed');out[name]=v;records.append({**q,'sha256':sha})
    require(out['PL00_U.ARC']==(PARENT/'modified.arc').read_bytes(),'ARC extraction differs');return out,records

def save_targets(originals):
    arc=originals['PL00_U.ARC'];menu=originals['MOJIPAT.ARC'];tex=entry(originals['LOAD_U.ARC'],0x10008);changed=menu;targets={}
    for n,b in SAVE.items():
        changed=transfer_geometry(changed,2,n,composition_frame(entry(arc,3),b,0));targets[n]=place_frame(actual(arc,0,b),composition_frame(changed,2,n),tex)
    texture,changed,proof=protected_repack(tex,menu,changed,2,targets);po=struct.unpack_from('<I',menu,4)[0];pal=entry(arc,9);changed=bytearray(changed)
    require(menu[po+8*32:po+9*32]==pal[:32],'Base UI palette differs')
    for row,offset in ((9,32),(11,64)):changed[po+row*32:po+(row+1)*32]=pal[offset:offset+32]
    return bytes(changed),replace_entry(originals['LOAD_U.ARC'],0x10008,texture),proof

def capsule_targets(arc,gb):
    g,c=entry(arc,2),entry(arc,3);old=[raster(g,c,gb,gb+8,n) for n in range(11)]
    base=raster(g,c,0,0,0)>0;part=raster(g,c,0,gb-5,0)>0;body=binary_fill_holes(base|part);yy,xx=np.indices(body.shape)
    full=render(arc,0,True)[0];silhouette=np.array(full)[:,:,3]>0
    # 인게임 아머는 기본형과 다른 픽셀만 저장한다. 획득 잔상은 그 차분이
    # 아니라 수용된 완성 의상의 해당 영역을 표시해야 검은 옷이 비지 않는다.
    if gb==10:region=(yy>=58)&(yy<73)&(xx>=75)&(xx<91)
    elif gb==11:region=(yy>=73)&(yy<85)&(xx>=74)&(xx<90)
    elif gb==12:region=(yy>=73)&(yy<86)&(((xx>=68)&(xx<76))|((xx>=86)&(xx<92)))
    else:region=(yy>=85)|part
    pm=binary_fill_holes(part if gb==13 else silhouette&region);require(np.any(pm),'Empty acquired costume part')
    ys=np.nonzero(pm)[0];lo,hi=int(ys.min()),int(ys.max());oldpart=binary_dilation(binary_fill_holes(old[7]>0),iterations=2);out=[]
    for n in range(11):
        a=np.zeros(body.shape,np.uint8)
        if n==0:a[binary_dilation(body)&~body]=3
        elif n==1:
            a[binary_dilation(body,iterations=2)&~binary_dilation(body)]=3;a[binary_dilation(body)&~body]=1
        elif 4<=n<=6:
            cutoff=hi-round((hi-lo+1)*(n-3)/4);a[pm&(yy>=cutoff)&((xx+yy+n)%2==0)]=1
        elif n>=7:
            a[pm]=1
            if n==8:a[pm&~binary_erosion(pm)]=3;a[binary_erosion(pm)&~binary_erosion(pm,iterations=2)]=2
        if n>=3 and n!=8:
            sparks=old[n].copy();sparks[oldpart]=0
            if gb==13 and n>=9:
                # 원래 큰 X 부츠를 둘러싼 마지막 광선을 나나 하단 의상 폭에 등록.
                # 위로 길어진 베일 자체는 잘라내지 않고 전체 pm에 유지한다.
                oy,ox=np.nonzero(binary_fill_holes(old[7]>0));ny,nx=np.nonzero(pm&(yy>=oy.min()));mapped=np.zeros_like(sparks)
                for sy,sx in np.argwhere(sparks):
                    tx=round((sx-ox.min())*(nx.max()-nx.min())/(ox.max()-ox.min())+nx.min());ty=round((sy-oy.min())*(ny.max()-ny.min())/(oy.max()-oy.min())+ny.min());mapped[ty,tx]=sparks[sy,sx]
                sparks=mapped
            a[sparks>0]=sparks[sparks>0]
        out.append(a)
    return out

def optimize_storage(raw,count,records,budget):
    sys.path.insert(0,str(ROOT/'work/tools'));from psx_compress_cost import encoded_cost
    ids=[t for t in range(count) if t%16];mapping={t:t for t in ids};flips={};best=encoded_cost(raw);initial=best;rng=random.Random(301013);attempts=0
    require(best==len(encode_stream(raw)),'Cost estimator differs from encoder')
    for sweep in range(5):
        actions=[('swap',a,b) for a,b in itertools.combinations(ids,2)]+[('flip',a,flag) for a in ids for flag in (64,128,192)];rng.shuffle(actions);improved=False
        for action,a,b in actions:
            m,f=dict(mapping),dict(flips)
            if action=='swap':m[a],m[b]=m[b],m[a]
            else:f[a]=f.get(a,0)^b
            try:v=remap_tiles(raw,count,m,f)
            except ValueError:continue
            size=encoded_cost(v);attempts+=1
            if size<best:best,mapping,flips=size,m,f;improved=True
            if best<=budget:
                v=remap_tiles(raw,count,mapping,flips);require(len(encode_stream(v))==best,'Final encoder cost differs');rr=[[(mapping.get(t,t),x,y,flag^flips.get(t,0)) for t,x,y,flag in row] for row in records]
                return v,rr,{'method':'lossless_tile_order_flips','initial_bytes':initial,'encoded_bytes':best,'evaluated_layouts':attempts,'mapping':mapping,'flips':flips}
        print(json.dumps({'storage_sweep':sweep,'best':best,'budget':budget}),flush=True)
        if not improved:break
    raise ValueError(f'Lossless storage cannot fit: {best} > {budget}')

def prepare_capsules(arc):
    g,c=entry(arc,2),entry(arc,3);ng=g;nc=bytearray(c);proofs=[]
    for gb in range(10,14):
        bank=graphics_bank(g,gb,allow_bank_aliases=True);f=bank['frames'][0];require(len(bank['frames'])==11 and len({q['offset'] for q in bank['frames']})==1,'Unknown capsule stream')
        original=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128);old=original.data;images=capsule_targets(arc,gb);comps=[composition_frame(c,gb+8,n) for n in range(11)];limits=[len(q['parts']) for q in comps];raw,records=pack_many(old,f['tile_count'],images,set(range(f['tile_count'])),limits)
        layout=None
        if len(encode_stream(raw))>original.end-f['offset']:raw,records,layout=optimize_storage(raw,f['tile_count'],records,original.end-f['offset'])
        for n,(comp,rr) in enumerate(zip(comps,records)):
            require(0<len(rr)<=len(comp['parts']),'Capsule part budget exceeded')
            for i,q in enumerate(comp['parts']):
                require(not(q['page'] or q['clut'] or q['unknown_flags']),'Unknown capsule flags');t,x,y,flag=rr[min(i,len(rr)-1)];pos=q['record_offset'];nc[pos:pos+4]=struct.pack('<BBbb',flag,t,x-80,y-80)
            require(np.array_equal(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,gb+8,n)),images[n]),'Capsule packing differs')
        ng,p=replace_stream(ng,f,raw);proofs.append({'graphics_bank':gb,'parts_bank':gb+8,'frames':11,'lossless_shared_layout':layout,**p});print(json.dumps(proofs[-1]),flush=True)
    return replace_entry(replace_entry(arc,2,ng),3,bytes(nc)),proofs

def verify(originals,edited):
    require(set(edited)==set(SOURCES),'Wrong resource scope');require(all(len(edited[n])==len(originals[n]) for n in SOURCES),'Resource size changed')
    arc=originals['PL00_U.ARC'];new=edited['PL00_U.ARC'];menu=originals['MOJIPAT.ARC'];nm=edited['MOJIPAT.ARC'];tex=entry(originals['LOAD_U.ARC'],0x10008);nt=entry(edited['LOAD_U.ARC'],0x10008);po=struct.unpack_from('<I',menu,4)[0];pal=entry(arc,9)
    require(replace_entry(originals['LOAD_U.ARC'],0x10008,nt)==edited['LOAD_U.ARC'],'Non-atlas load bytes changed');allowed=set();owned={p['page']*256+p['tile'] for n in SAVE for p in composition_frame(menu,2,n)['parts']};others=0
    for n in range(composition_frame(menu,2,0)['bank_frame_count']):
        a,b=composition_frame(menu,2,n),composition_frame(nm,2,n)
        if n in SAVE:
            require(len(a['parts'])==len(b['parts']),'Save part count changed');require(world(compose_static(nt,local_composition(b)))==world(actual(arc,0,SAVE[n])),'Save part raster/anchor differs')
            for p,q in zip(a['parts'],b['parts']):
                require(p['clut']==q['clut'] and p['unknown_flags']==q['unknown_flags'],'UI palette binding changed');allowed.update(range(p['record_offset'],p['record_offset']+4));t=q['page']*256+q['tile'];pixels=tile_pixels(nt,t);require((t%16!=0 or not any(pixels[::16])) and (t%256>=16 or not any(pixels[:16])),'Unsafe mirrored UV edge')
        else:require(a==b and compose_static(tex,local_composition(a))[:3]==compose_static(nt,local_composition(b))[:3],'Other UI frame changed');others+=1
    for t in set(range(len(tex)//128))-owned:require(tile_pixels(tex,t)==tile_pixels(nt,t),'Unowned/direct UI tile changed')
    for row,offset in ((9,32),(11,64)):
        require(nm[po+row*32:po+(row+1)*32]==pal[offset:offset+32],'Wrong armor CLUT');allowed.update(range(po+row*32,po+(row+1)*32))
    require(all(i in allowed for i,(a,b) in enumerate(zip(menu,nm)) if a!=b),'Other menu bytes changed');require(nm[po+10*32:po+11*32]==menu[po+10*32:po+11*32],'Rin palette changed')
    _,base,f,raw=render(arc,0);c=entry(arc,3);layers={b:canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,0)) for b in (5,6,7,8)};combinations=0
    for arm in (1,2):
        for mask in range(16):
            expected=np.array(struct.unpack_from('<16H',pal,0),np.uint16)[base]
            for bit,b in ((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:
                    colors=np.array(struct.unpack_from('<16H',pal,64 if arm==2 and b==7 else 32),np.uint16);v=layers[b];expected=np.where(v,colors[v],expected)
            got=icon(nm,nt,mask,arm)
            for flip in (False,True):require(np.array_equal(got[:,::-1] if flip else got,expected[:,::-1] if flip else expected),'Save part combination differs');combinations+=1
    og,ng=entry(arc,2),entry(new,2);oc,nc=entry(arc,3),entry(new,3);require(replace_entry(replace_entry(arc,2,ng),3,nc)==new,'Non-graphic player data changed');bitmap=otherbitmap=0
    for bi in range(len(bank_offsets(og,allow_aliases=True))):
        a,b=graphics_bank(og,bi,allow_bank_aliases=True),graphics_bank(ng,bi,allow_bank_aliases=True);require(a==b,'Graphics stream addresses changed')
        for f in a['frames']:
            x=decode_stream(og,f['offset'],f['limit'],f['tile_count']*128).data;y=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data;bitmap+=1
            if bi not in range(10,14):require(x==y,'Other graphics changed');otherbitmap+=1
    allowed=set();othercomp=0
    for bi in range(len(bank_offsets(oc))):
        for n in range(composition_frame(oc,bi,0)['bank_frame_count']):
            a,b=composition_frame(oc,bi,n),composition_frame(nc,bi,n)
            if bi in range(18,22):
                require(len(a['parts'])==len(b['parts']),'Capsule composition count changed')
                for q in a['parts']:allowed.update(range(q['record_offset'],q['record_offset']+4))
            else:require(a==b,'Other composition changed');othercomp+=1
    require(all(i in allowed for i,(a,b) in enumerate(zip(oc,nc)) if a!=b),'Composition headers or other bytes changed')
    for gb in range(10,14):
        for n,target in enumerate(capsule_targets(arc,gb)):require(np.array_equal(raster(ng,nc,gb,gb+8,n),target),'Capsule readback differs')
    return {'save_combination_direction_arm_checks':combinations,'save_other_frames_preserved':others,'unowned_save_tiles_preserved':len(tex)//128-len(owned),'rin_palette10_preserved':True,'capsule_refs':44,'graphics_refs_checked':bitmap,'other_graphics_preserved':otherbitmap,'other_compositions_preserved':othercomp,'stream_addresses_and_headers_preserved':True,'all_playable_costume_refs_preserved':193,'base_and_ultimate_nova_unchanged':True,'only_graphics_changed':True,'runtime_verified':False}

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_ui') and not out.exists(),'Fresh Fourth UI output required');originals,records=read_sources();menu,load,save_proof=save_targets(originals);player,capsule_proof=prepare_capsules(originals['PL00_U.ARC']);edited={'MOJIPAT.ARC':menu,'LOAD_U.ARC':load,'PL00_U.ARC':player};proof=verify(originals,edited);out.mkdir(parents=True)
    for name,data in edited.items():(out/name).write_bytes(data)
    board=Image.new('RGB',(8*80,2*80),'#242934');draw=ImageDraw.Draw(board);tex=entry(load,0x10008)
    for mask in range(16):
        im=rgba(icon(menu,tex,mask,2)).crop((40,40,120,112));x,y=mask%8*80,mask//8*80;board.paste(im,(x,y+8),im);draw.text((x+1,y),str(mask),fill='white');im.save(out/f'save_mask{mask:02}.png')
    board.resize((1920,480),Image.Resampling.NEAREST).save(out/'save_combinations_3x.png')
    words=[0,0xffff,0xfdc8,0xe920]+[0x8000]*12;board=Image.new('RGB',(11*80,4*96),'#242934');draw=ImageDraw.Draw(board)
    for row,gb in enumerate(range(10,14)):
        for n,target in enumerate(capsule_targets(originals['PL00_U.ARC'],gb)):
            im=save_image(target.tobytes(),(160,160),words,out/f'capsule_{gb}_{n:02}.png').convert('RGBA').crop((40,32,120,112));board.paste(im,(n*80,row*96+16),im);draw.text((n*80+1,row*96+1),f'{gb}/{n}',fill='white')
    board.resize((1760,768),Image.Resampling.NEAREST).save(out/'capsule_review_2x.png');write(out/'recipe.json',{'task':'fourth_armor_nana','kind':'nana_fourth_save_capsule','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'sources':records,'files':{n:sha256(v) for n,v in edited.items()},'save_frames':list(SAVE),'save_atlas':save_proof,'capsule_streams':capsule_proof,'verification':proof,'new_illustration_generated':False});print(json.dumps({'output':str(out),'verification':proof}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
