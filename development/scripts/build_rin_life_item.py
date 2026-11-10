"""수용된 린 머리를 잔기 아이템의 기존 4bpp 팔레트/애니메이션에 등록한다."""
import argparse,json,struct,sys,shutil
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_hud_emblems import all_compositions,composed,render_pixels,require
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from src.psx_ui_atlas import local_composition,tile_pixels,write_tile
from src.psx_static_effect import patch_static
from src.psx_ui_render import render_static_rgba
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

PARENT=ROOT/'out/ver_rin_nana/rin_hud_theme_20261029T035610236628Z'
PARENT_SHA='1d0a206e42c1e6eadda4ffec3d509e5c054f49f6772d018cfae1b6b9f46c3e16'
ART=ROOT/'work/ver_rin_nana/life_item_v1'
HEAD=ROOT/'work/ver_rin_nana/ride_armor_head/v2/approved_head_reference.png'
# Explicit palette-category reduction keeps pale skin separate from white hair.
COLOR_MAP={(16,24,49):11,(255,255,255):8,(189,197,222):9,(222,238,246):8,
    (16,65,230):3,(255,230,197):12,(32,41,82):11,(131,148,172):10,
    (8,32,148):11,(90,98,139):10,(255,205,156):13,(24,197,238):3}
BUBBLE_TILES={513,514,515}

def sources():
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Accepted HUD parent differs')
    m=json.loads((PARENT/'manifest.json').read_text('utf8'));raw=(PARENT/'modified.arc').read_bytes()
    require(sha256(raw)==m['modified_archive_sha256'],'Parent player differs')
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size);rec=next(r for r in d.inspect()['files'] if r['path']=='/ARC/PL01_U.ARC;1')
        require(d.read(rec['lba'],rec['size'])==raw,'Parent readback differs')
    return m,{**rec,'sha256':sha256(raw)},raw

def head_indices():
    a=np.array(Image.open(HEAD).convert('RGBA'));require(a.shape==(16,16,4),'Accepted head size changed')
    result=np.zeros((16,16),np.uint8)
    for y,x in zip(*np.where(a[:,:,3]>128)):
        color=tuple(a[y,x,:3]);require(color in COLOR_MAP,'Unknown accepted head color');result[y,x]=COLOR_MAP[color]
    require(np.array_equal(result>0,a[:,:,3]>128),'Head alpha differs')
    return result

def patch(raw,head):
    require(head.shape==(16,16) and head.dtype==np.uint8 and int(head.max())<=15,'Invalid head input')
    texture=entry(raw,0x10206);parts=entry(raw,3);comps=all_compositions(parts);cps={};targets={};details=[]
    for n in range(89,99):
        cp=comps[3,n];face=[p for p in cp['parts'] if p['page']*256+p['tile'] not in BUBBLE_TILES]
        if not face:continue
        require(all(p['clut']==0 for p in cp['parts']),'Unexpected pickup CLUT')
        cp=local_composition({**cp,'parts':face});before,size,bb,cov=composed(texture,cp)
        side=16 if n in (89,96,97,98) else 14 if n<=92 else 10 if n==93 else 6
        small=np.array(Image.fromarray(head).resize((side,side),Image.Resampling.NEAREST))
        a=np.zeros_like(before);x=max(0,min(size[0]-side,-side//2-bb[0]));y=max(0,min(size[1]-side,-side//2-bb[1]))
        a[y:y+side,x:x+side]=small;coverage=np.array([bool(v) for v in cov]).reshape(a.shape)
        require(not np.any((a>0)&~coverage),'Life head clipped by existing parts')
        cps[n]=cp;targets[n]=(a.tobytes(),size)
        details.append({'frame':n,'head_size':[side,side],'bounds':list(bb),'offset_in_bounds':[x,y],'opaque_pixels':int(np.count_nonzero(a))})
    require(set(cps)=={89,90,91,92,93,94,96,97,98},'Unexpected pickup frame set')
    ng=patch_static(texture,cps,targets)
    changed={t for t in range(len(texture)//128) if tile_pixels(texture,t)!=tile_pixels(ng,t)}
    allowed={p['page']*256+p['tile'] for c in cps.values() for p in c['parts']}
    require(changed<=allowed and not changed&BUBBLE_TILES,'Edit escaped face tiles')
    count=0
    for key,cp in comps.items():
        if key[0]==3 and key[1] in cps:
            a,size,bb,_=composed(ng,cps[key[1]]);require((a.tobytes(),size)==targets[key[1]],'Pickup readback differs')
        else:
            used={p['page']*256+p['tile'] for p in cp['parts']}
            require(not used&changed,'Shared pickup tile affects another bank/frame')
            if key[0] in {1,2,3,4,6}:
                a,sz,bb,_=composed(texture,cp);b,ns,nb,_=composed(ng,cp)
                require(np.array_equal(a,b) and sz==ns and bb==nb,'Protected static frame changed');count+=1
    result=replace_entry(raw,0x10206,ng);e=next(e for e in psx_arc(raw) if e['type']=='0x10206');lo,hi=e['offset'],e['offset']+e['size']
    require(len(raw)==len(result) and raw[:lo]==result[:lo] and raw[hi:]==result[hi:],'Nontexture player data changed')
    return result,{'faces':details,'changed_tiles':sorted(changed),'all_compositions_scanned':len(comps),
        'protected_static_compositions':count,'bubble_tiles_exact':True,'blank_bubble_frame95_exact':True,
        'all_parts_coordinates_clut_flips_timing_exact':True,'all_palette_bytes_exact':True,
        'hud_menu_and_existing_body_exact':True,'only_static_face_tiles_changed':True,'runtime_verified':False}

def blue_bubbles(raw):
    texture,parts=entry(raw,0x10206),entry(raw,3);comps=all_compositions(parts)
    selected={(3,n) for n in range(89,99)}
    used={p['page']*256+p['tile'] for c in comps.values() for p in c['parts']}
    free=iter(sorted(set(range(len(texture)//128))-used));mapping={}
    # Original red/pink/yellow ramp -> white/blue/slate/navy/silver.
    remap={4:8,5:3,6:10,7:11,12:8,13:3,14:10,15:9};ng=bytearray(texture);np_=bytearray(parts);expected=bytearray(texture);allowed=set()
    for tile in sorted(BUBBLE_TILES):
        dest=next(free,None);require(dest is not None,'No private bubble tile slots');mapping[tile]=dest
        px=tile_pixels(texture,tile);newpx=bytes(remap.get(v,v) for v in px)
        require(bytes(bool(v) for v in newpx)==bytes(bool(v) for v in px),'Bubble alpha changed')
        write_tile(ng,dest,newpx);write_tile(expected,tile,newpx)
    changed_records=set();target_frames=[]
    for key in sorted(selected):
        touched=False
        for p in comps[key]['parts']:
            tile=p['page']*256+p['tile']
            if tile not in mapping:continue
            off=p['record_offset'];dest=mapping[tile];np_[off:off+2]=bytes(((p['flags']&~3)|dest//256,dest%256));allowed.update((off,off+1));changed_records.add(off);touched=True
        if touched:target_frames.append(key[1])
    newparts=bytes(np_);ng=bytes(ng);newcomps=all_compositions(newparts);count=0
    for key,cp in comps.items():
        nc=newcomps[key]
        if key not in selected:require(nc==cp,'Bubble clone aliases another part record')
        if key[0] in {1,2,3,4,6}:
            a,sz,bb,_=composed(expected if key in selected else texture,cp);b,ns,nb,_=composed(ng,nc)
            require(sz==ns and bb==nb and np.array_equal(a,b),'Bubble clone changes another display');count+=1
    require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(parts,newparts))),'Bubble clone changed non-UV parts')
    for tile in range(len(texture)//128):
        if tile not in mapping.values():require(tile_pixels(texture,tile)==tile_pixels(ng,tile),'Original shared texture tile changed')
    result=replace_entry(replace_entry(raw,0x10206,ng),3,newparts)
    return result,{'bubble_frames':target_frames,'private_tile_mapping':{str(k):v for k,v in mapping.items()},
        'index_remap':{str(k):v for k,v in remap.items()},'changed_part_records':len(changed_records),'static_compositions_checked':count,
        'original_shared_tiles_preserved':True,'all_other_effects_preserved':True,'bubble_alpha_geometry_clut_flip_timing_preserved':True}

def prepare(out,rin_bubble=False):
    out=out.resolve();require(out.is_relative_to(ART) and out!=ART and not out.exists(),'New candidate subdirectory required')
    m,rec,old=sources();head=head_indices();new,v=patch(old,head)
    if rin_bubble:
        new,bubble=blue_bubbles(new);v.update(personal_bubble=bubble,blank_bubble_frame95_exact=False,bubble_tiles_exact=False,
            original_shared_bubble_tiles_exact=True,only_static_face_tiles_changed=False)
    out.mkdir();Image.fromarray(head).save(out/'head_indices.png')
    (out/'PL01_U.ARC').write_bytes(new);pal=entry(old,9)[11*32:12*32];render_pixels(head,pal).save(out/'native_head.png')
    board=Image.new('RGB',(600,260),'#263347');dr=ImageDraw.Draw(board)
    for i,n in enumerate(range(89,99)):
        cp=all_compositions(entry(new,3))[3,n];a,sz,bb,_=composed(entry(new,0x10206),cp);im=render_pixels(a,pal)
        actual,actual_bb=render_static_rgba(entry(new,0x10206),cp,{0:struct.unpack('<16H',pal)})
        require(actual_bb==bb and np.array_equal(np.array(actual),np.array(im)),'Actual pickup CLUT rendering differs')
        im.save(out/f'pickup_{n}.png');im=im.resize((sz[0]*3,sz[1]*3),Image.Resampling.NEAREST)
        x,y=i%5*120,i//5*130;board.paste(im,(x,y+24),im);dr.text((x+3,y+4),str(n),fill='white')
    board.save(out/'pickups.png')
    r={'kind':'rin_life_item','rin_bubble':rin_bubble,'parent_sha256':PARENT_SHA,'source':rec,'input_head':HEAD.relative_to(ROOT).as_posix(),
        'input_head_sha256':digest(HEAD),'method':'reuse accepted 16x16 head; explicit color-category conversion; uniform nearest scaling per native pickup phase',
        'palette_row':11,'modified_archive_sha256':sha256(new),'head_indices_sha256':digest(out/'head_indices.png'),'verification':v}
    (out/'recipe.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'faces':len(v['faces']),'changed_tiles':v['changed_tiles']}))

def build(art):
    art=art.resolve();require(art.is_relative_to(ART) and art!=ART,'Wrong candidate path');m,rec,old=sources();r=json.loads((art/'recipe.json').read_text('utf8'))
    require(r['parent_sha256']==PARENT_SHA and r['source']==rec and r['input_head_sha256']==digest(HEAD),'Input binding differs')
    head=head_indices();require(np.array_equal(head,np.array(Image.open(art/'head_indices.png'))) and digest(art/'head_indices.png')==r['head_indices_sha256'],'Head changed')
    new,v=patch(old,head)
    if r.get('rin_bubble',False):
        new,bubble=blue_bubbles(new);v.update(personal_bubble=bubble,blank_bubble_frame95_exact=False,bubble_tiles_exact=False,
            original_shared_bubble_tiles_exact=True,only_static_face_tiles_changed=False)
    require(new==(art/'PL01_U.ARC').read_bytes() and sha256(new)==r['modified_archive_sha256'] and v==r['verification'],'Candidate reproduction differs')
    protection=json.loads((PARENT/'preservation.json').read_text('utf8'));protection['files'].append({'path':HEAD.relative_to(ROOT).as_posix(),'expected_sha256':digest(HEAD)})
    def protect():
        for q in protection['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed: '+q['path'])
    protect();out=ROOT/'out/ver_rin_nana'/('rin_life_item_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',[(rec,new)],PARENT_SHA);(out/'modified.arc').write_bytes(new);shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue')
    for folder in ('ui','portrait','hunter','dialogue','pause','weapon_get','hud_theme'):shutil.copytree(PARENT/folder,out/folder)
    shutil.copytree(art,out/'life_item');changed={q['lba'] for q in result['changed_sectors']};count=0
    with (PARENT/'rin_nana.bin').open('rb') as f,(out/'rin_nana.bin').open('rb') as g:
        while True:
            a,b=f.read(2352),g.read(2352)
            if not a:require(not b,'Output grew');break
            require(len(a)==len(b) and (a!=b)==(count in changed),'Unexpected sector change')
            if count in changed:validate_checks(b)
            count+=1
    with (out/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,result['size']);require(d.read(rec['lba'],rec['size'])==new,'Readback differs')
    protect();v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,readback_equal=True,
        other_parent_sectors_exact=True,protected_files=len(protection['files']),embedded_static_bodies=m['verification']['embedded_static_bodies'])
    manifest={**m,'kind':'rin_life_item','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,
        'modified_archive_sha256':sha256(new),'verification':v,'inherited_verification':m['verification'],
        'life_item_overlay':{'recipe':(out/'life_item/recipe.json').relative_to(ROOT).as_posix(),'recipe_sha256':digest(out/'life_item/recipe.json'),'runtime_verified':False},'runtime_verified':False}
    for name,data in [('manifest.json',manifest),('verification.json',v),('preservation.json',protection)]:(out/name).write_text(json.dumps(data,indent=2)+'\n','utf8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),
        'sha256':result['sha256'],'frames':m['cumulative_frames'],'bank1_frames':m['cumulative_bank1_frames'],'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'sectors':len(changed)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','build']);p.add_argument('--art',type=Path,required=True);p.add_argument('--rin-bubble',action='store_true');a=p.parse_args()
    prepare(a.art,a.rin_bubble) if a.action=='prepare' else build(a.art)
