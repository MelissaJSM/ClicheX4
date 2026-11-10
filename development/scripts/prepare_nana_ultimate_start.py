"""얼티밋 수용 시안을 대기·사격10참조와 전용 저장 그림에 재삽입한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
from scripts.analyze_nana_ultimate import PARENT,PARENT_SHA
from scripts.prepare_nana_fourth_pilot import entry,require,write,render
from scripts.prepare_riko_ui import replace_entry
from scripts.prepare_shibuki_ui import transfer_geometry,actual
from scripts.prepare_rin_ui_small import protected_repack
from scripts.prepare_shibuki_ultimate_save_ui import render as save_icon
from scripts.verify_shibuki_save_icon import rgba
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.prepare_shibuki_weapon_palette import WEAPON_ROWS,FLASHES
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition,place_frame,tile_pixels
from src.psx_static_effect import compose_static
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_armor_palette import replace_armor_palette_rows
D=ROOT/'work/ver_rin_nana/nana_ultimate_armor'
PILOT=ROOT/'out/ver_rin_nana/nana_ultimate_pilot_v1'
FRAMES=[0,85,86,87,92,115,116,117,118,119]
BASE_SHA='2fb980f21027125ad3de7f2e88073a2982c3e5495cfc4c05da33a8a9ef78b91e'

def targets(source):
    masters={n:np.array(Image.open(PILOT/f'ultimate_{n:03}_indexed.png')) for n in (0,85)};full={};overlays={};proofs=[]
    for n in FRAMES:
        _,base,_,_=render(source,n);dy=1 if 115<=n<=118 else -1 if n==119 else 0;master=masters[85 if n in (85,86) else 0];target=np.zeros_like(master)
        for y in range(160):
            shift=dy if y<90 else round(dy*max(0,98-y)/8);sy=y-shift
            if 0<=sy<160:target[y]=master[sy]
        require(np.array_equal(target[98:],master[98:]),'Breathing moves soles')
        yy,xx=np.indices(target.shape)
        if n in (85,86,87):
            gun=(xx<70)&(yy>=66)&(yy<85);target[gun]=base[gun]
        dist,where=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0)
        require(float(dist[missing].max(initial=0))<=5,'Boundary registration needs new artwork')
        target[missing]=target[where[0][missing],where[1][missing]]
        # 은행5의115..118은 같은 조립을 쓴다. 눈 한 픽셀만 기본형에서 받아 깜빡인다.
        eye=(68+dy,76);target[eye]=base[eye];full[n]=target.copy();overlay=target.copy();overlay[eye]=0;overlays[n]=overlay
        require(not np.any((base>0)&(full[n]==0)),'Base silhouette escapes Ultimate')
        require(np.array_equal(np.where(overlay,overlay,base),target),'Underlying eye composition differs')
        proofs.append({'frame':n,'breath_delta':dy,'eye_window':[eye[1],eye[0]],'boundary_pixels_registered':int(missing.sum()),'max_boundary_distance':float(dist[missing].max(initial=0)),'pistol_pixels_preserved':n in (85,86,87),'base_pixels_outside_target':0})
    require(all(np.array_equal(overlays[115],overlays[n]) for n in (116,117,118)),'Blink overlay aliases differ')
    return full,overlays,proofs

def prepare(out):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh task output required')
    approval=json.loads((ROOT/'projects/ver_rin_nana/nana_ultimate_candidate.json').read_text('utf8'));require(all(approval[k] for k in ('art_user_approved','full_animation_production_approved','pre_acquisition_design_confirmed')),'Approval missing')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(D/'base_v1/PL02_U.ARC')==BASE_SHA,'Source differs')
    source=(PARENT/'modified.arc').read_bytes();arc=(D/'base_v1/PL02_U.ARC').read_bytes();g,c,p=[entry(arc,k) for k in (2,3,9)];bank=graphics_bank(g,0,allow_bank_aliases=True)
    full,overlays,registration=targets(source);replacements={};changes={};groups={};reports=[]
    for n in FRAMES:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
    for off,ns in groups.items():
        f=bank['frames'][ns[0]];require([q['index'] for q in bank['frames'] if q['offset']==off]==ns,'Unselected shared stream')
        old=decode_stream(g,off,f['limit'],f['tile_count']*128).data
        keep={q['tile'] for n in ns for b in (0,6,7,8) for q in composition_frame(c,b,n)['parts']};pool=set(range(f['tile_count']))-keep
        limits=[len(composition_frame(c,5,n)['parts']) for n in ns]
        raw,rr=pack_shared(old,f['tile_count'],[overlays[n] for n in ns],pool,limits)
        for n,parts,limit in zip(ns,rr,limits):
            require(0<len(parts)<=limit,'Part budget exceeded');parts=parts+[parts[-1]]*(limit-len(parts));changes[n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80) for t,x,y,fl in parts);replacements[n]=raw
            for b in (0,6,7,8):
                cp=local_composition(composition_frame(c,b,n));require(np.array_equal(canvas_from_parts(old,f['tile_count'],cp),canvas_from_parts(raw,f['tile_count'],cp)),'Protected layer changed')
        reports.append({'frames':ns,'tile_count':f['tile_count'],'writable_tiles':sorted(pool),'parts':[len(q) for q in rr],'encoded_bytes':len(encode_stream(raw))})
    nc,slack=repack_parts(c,5,changes);ng,repack=repack_graphics_bank(g,0,{n:encode_stream(v) for n,v in replacements.items()})
    checked=0;other=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        old,new=graphics_bank(g,bi,allow_bank_aliases=True),graphics_bank(ng,bi,allow_bank_aliases=True)
        require((old['base'],old['end'],len(old['frames']))==(new['base'],new['end'],len(new['frames'])),'Bank dimensions changed')
        for a,b in zip(old['frames'],new['frames']):
            require(a['tile_count']==b['tile_count'],'Tile count changed');before=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;after=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data;require(after==(replacements.get(a['index'],before) if bi==0 else before),'Other graphic changed');checked+=1
    for b in range(len(bank_offsets(c))):
        for n in range(composition_frame(c,b,0)['bank_frame_count']):
            if b==5 and n in FRAMES:continue
            require(records(c,b,n)==records(nc,b,n),'Other composition changed');other+=1
    words=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));bp=entry(source,9);npal=bytearray(p);base_rows=[0,*WEAPON_ROWS,*FLASHES]
    for row in base_rows:npal[row*32:(row+1)*32]=bp[row*32:(row+1)*32]
    npal,armor_rows=replace_armor_palette_rows(bytes(npal),words,[0,*FLASHES],FLASHES,weapon_rows=WEAPON_ROWS)
    allowed={i for r in base_rows+armor_rows for i in range(r*32,(r+1)*32)};require(all(i in allowed for i,(a,b) in enumerate(zip(p,npal)) if a!=b),'Effect palette changed')
    result=replace_entry(replace_entry(replace_entry(arc,2,ng),3,nc),9,npal);nb=graphics_bank(ng,0,allow_bank_aliases=True)
    for n in FRAMES:
        f=nb['frames'][n];raw=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data;over=canvas_from_parts(raw,f['tile_count'],composition_frame(nc,5,n));base=canvas_from_parts(raw,f['tile_count'],composition_frame(nc,0,n));require(np.array_equal(over,overlays[n]),'Inserted overlay differs');require(np.array_equal(np.where(over,over,base),full[n]),'Final display differs')
    # 전용 저장52만 재패킹. 기본44·포스45..48·린43 및 바탕 타일 보호.
    menu=(PARENT/'fourth_ui/MOJIPAT.ARC').read_bytes();load=(PARENT/'fourth_ui/LOAD_U.ARC').read_bytes();tex=entry(load,0x10008);nm=transfer_geometry(menu,2,52,composition_frame(nc,5,0));target=place_frame(actual(result,0,5),composition_frame(nm,2,52),tex);nt,nm,uip=protected_repack(tex,menu,nm,2,{52:target});nm=bytearray(nm);po=struct.unpack_from('<I',menu,4)[0];nm[po+30*32:po+31*32]=npal[32:64];nm[po+31*32:po+32*32]=npal[:32];nm=bytes(nm);nl=replace_entry(load,0x10008,nt)
    base=render(source,0)[1];basewords=np.array(struct.unpack_from('<16H',bp),np.uint16);awords=np.array(words,np.uint16)
    for mask in range(16):
        want=np.where(overlays[0],awords[overlays[0]],basewords[base]) if mask else basewords[base];require(np.array_equal(save_icon(nm,nt,mask),want),'Ultimate save differs')
    others=0
    for n in range(composition_frame(menu,2,0)['bank_frame_count']):
        if n==52:continue
        a,b=composition_frame(menu,2,n),composition_frame(nm,2,n);require(a==b and compose_static(tex,local_composition(a))[:3]==compose_static(nt,local_composition(b))[:3],'Other save frame changed');others+=1
    uiallow={i for q in composition_frame(menu,2,52)['parts'] for i in range(q['record_offset'],q['record_offset']+4)}|set(range(po+30*32,po+32*32));require(all(i in uiallow for i,(a,b) in enumerate(zip(menu,nm)) if a!=b),'Other menu changed')
    out.mkdir(parents=True)
    for name,data in [('PL02_U.ARC',result),('MOJIPAT.ARC',nm),('LOAD_U.ARC',nl)]: (out/name).write_bytes(data)
    for n in FRAMES:
        save_image(full[n].tobytes(),(160,160),words,out/f'ultimate_{n:03}.png');save_image(overlays[n].tobytes(),(160,160),words,out/f'overlay_{n:03}.png')
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);board=Image.new('RGB',(1280,600),'#252c3c');dr=ImageDraw.Draw(board)
    for i,n in enumerate(FRAMES):
        im=Image.open(out/f'ultimate_{n:03}.png').convert('RGBA').crop((48,48,112,108)).resize((256,240),Image.Resampling.NEAREST);x=i%5*256;y=i//5*280;board.paste(im,(x,y+24),im);dr.text((x+8,y),str(n),font=font,fill='white')
    dr.text((8,572),'대기·사격 재삽입 정적 검수 · 아직 전체 얼티밋 완성본이 아님',font=font,fill='white');board.save(out/'review_4x.png')
    images=[];dur=[];steps=json.loads((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json').read_text())['idle_animation']['steps']
    for s in steps:
        im=Image.open(out/f"ultimate_{s['frame']:03}.png").convert('RGBA');canvas=Image.new('RGB',(160,160),'#252c3c');canvas.paste(im,(0,0),im);images.append(canvas.crop((48,48,112,108)).resize((384,360),Image.Resampling.NEAREST));dur.append(max(20,round((s['duration_ticks']+1)*1000/60)))
    images[0].save(out/'idle.gif',save_all=True,append_images=images[1:],duration=dur,loop=0,disposal=2)
    for mask in (0,15):rgba(save_icon(nm,nt,mask)).save(out/f'save_mask{mask}.png')
    report={'task':'ultimate_armor_nana','kind':'ultimate_start','parent_sha256':PARENT_SHA,'base_arc_sha256':BASE_SHA,'frames':FRAMES,'base_references_copied':214,'registration':registration,'packing':reports,'graphics_repack':repack,'parts_bank5_remaining':slack,'base_palette_rows':base_rows,'armor_palette_rows':armor_rows,'checked_graphics':checked,'protected_compositions':other,'save_combinations':16,'other_save_frames':others,'save_packing':uip,'files':{n:sha256((out/n).read_bytes()) for n in ('PL02_U.ARC','MOJIPAT.ARC','LOAD_U.ARC')},'full_ultimate_complete':False,'unimplemented_armor_references':218,'runtime_verified':False,'timing_logic_preserved':True}
    write(out/'recipe.json',report);print(json.dumps({'output':str(out),'frames':FRAMES,'hash':report['files']['PL02_U.ARC'],'graphics_slack':repack['remaining_slack'],'parts_slack':slack}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
