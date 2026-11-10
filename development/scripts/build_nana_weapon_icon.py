"""나나 사랑이 메뉴 아이콘만 교체한다. 플레이어/탄환과 다른 메뉴 자원을 보존한다."""
import argparse,json,struct,sys,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_nana_idle_shot import write
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.extract_zero import save_image
from src.psx_ui_atlas import tile_pixels,write_tile,aliased_composition,local_composition
from src.psx_static_effect import compose_static
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks
PARENT=ROOT/'out/ver_rin_nana/nana_run_20261029T062150916963Z'
PARENT_SHA='fa7980ae0ca57eeb376408d541e275b9f30cfe5f56ed2ef6b4b42e87328e3b80'
ART=ROOT/'work/ver_rin_nana/nana_art/sarangi_menu_v1'
COLORS=[(20,20,28),(48,48,56),(88,88,96),(152,160,168),(232,240,240),(128,24,56),(192,40,88),(240,80,136),(255,144,184),(255,200,216),(24,120,144),(64,184,200),(144,224,224),(104,64,88),(184,136,160)]

def source():
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent game changed')
    result={}
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size);files=d.inspect()['files']
        for name in ('PL00_U.ARC','PL02_U.ARC'):
            rec=next(r for r in files if r['path']=='/ARC/'+name+';1');data=d.read(rec['lba'],rec['size']);result[name]=({**rec,'sha256':sha256(data)},data)
    if result['PL00_U.ARC'][1]!=(PARENT/'modified.arc').read_bytes():raise ValueError('Parent archive differs')
    return result

def prepare(out):
    if not out.resolve().is_relative_to(ART) or out.exists():raise ValueError('Fresh isolated icon preparation required')
    sources=source();im=Image.open(ART/'generated.png').convert('RGBA');bb=im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox();im=im.crop(bb)
    scale=min(14/im.width,12/im.height);size=(round(im.width*scale),round(im.height*scale));src=np.array(im);rgb=np.array(COLORS,np.int32);labels=np.zeros(src.shape[:2],np.uint8)
    for y in range(len(src)):
        delta=src[y,:,:3].astype(np.int32)[:,None,:]-rgb[None,:,:];labels[y]=(1+(delta*delta).sum(2).argmin(1)).astype(np.uint8)
    votes=np.stack([np.array(Image.fromarray(np.where(labels==i,src[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX)) for i in range(1,16)]);small=(1+votes.argmax(0)).astype(np.uint8);small[np.array(im.getchannel('A').resize(size,Image.Resampling.BOX))<128]=0
    target=np.zeros((16,16),np.uint8);x,y=(16-size[0])//2,(16-size[1])//2;target[y:y+size[1],x:x+size[0]]=small
    words=[0]+[0x8000|sum(((v*31+127)//255)<<(j*5) for j,v in enumerate(c)) for c in COLORS]
    dim=[0]+[0x8000|sum(((w>>s&31)//2)<<s for s in (0,5,10)) for w in words[1:]]
    out.mkdir();save_image(target.tobytes(),(16,16),words,out/'icon.png').convert('RGBA').resize((256,256),Image.Resampling.NEAREST).save(out/'icon_16x.png');save_image(target.tobytes(),(16,16),dim,out/'icon_dim.png');(out/'palette.bin').write_bytes(struct.pack('<16H',*words));proof={}
    for name,(rec,old) in sources.items():
        g=entry(old,0x10007);parts=struct.pack('<I',4)+entry(old,0x12);pal=entry(old,0x11);comps={n:aliased_composition(parts,0,n) for n in range(38)};c=comps[25]
        if [(p['tile'],p['flags'],p['x'],p['y']) for p in c['parts']]!=[(102,0,-8,-8)]:raise ValueError('Unexpected menu weapon tile')
        if any(p['tile']==102 and p['page']==0 for n,c0 in comps.items() if n!=25 for p in c0['parts']):raise ValueError('Menu weapon tile shared')
        bgmap=struct.unpack('<768H',entry(old,0x10))
        if any((v&255)==198 for v in bgmap[:512]):raise ValueError('Weapon tile shared with menu background')
        ng=bytearray(g);write_tile(ng,96+102,target.tobytes());npal=bytearray(pal);npal[12*32:13*32]=struct.pack('<16H',*dim);npal[22*32:23*32]=struct.pack('<16H',*words)
        new=replace_entry(replace_entry(old,0x10007,bytes(ng)),0x11,bytes(npal))
        for n,c0 in comps.items():
            before=compose_static(g[12288:],local_composition(c0))[:2];after=compose_static(ng[12288:],local_composition(c0))[:2]
            expected=(target.tobytes(),(16,16)) if n==25 else before
            if after!=expected:raise ValueError('Menu frame mismatch')
        for tile in range(len(g)//128):
            if tile!=198 and tile_pixels(g,tile)!=tile_pixels(ng,tile):raise ValueError('Other menu tile changed')
        for row in range(64):
            if row not in (12,22) and pal[row*32:row*32+32]!=npal[row*32:row*32+32]:raise ValueError('Other palette changed')
        for e in psx_arc(old):
            if int(e['type'],16) not in (0x10007,0x11) and old[e['offset']:e['offset']+e['size']]!=new[e['offset']:e['offset']+e['size']]:raise ValueError('Non-menu entry changed')
        (out/name).write_bytes(new);proof[name]={'record':rec,'sha256':sha256(new),'menu_frame':25,'texture_tile':198,'palette_rows':[12,22],'other_37_frames_preserved':True,'other_255_menu_tiles_preserved':True,'other_62_palette_rows_preserved':True,'all_compressed_body_effect_audio_text_entries_preserved':True}
    write(out/'recipe.json',{'task':'x_nana','scope':'sarangi_pause_icon','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'art_source_sha256':digest(ART/'generated.png'),'icon_sha256':digest(out/'icon.png'),'icon_size':list(size),'offset':[x,y],'opaque_pixels':int(np.count_nonzero(target)),'records':proof,'runtime_verified':False});print(out)

def build(a,b):
    for p in (a,b):
        if not p.resolve().is_relative_to(ART):raise ValueError('Icon candidate outside variant')
    r=json.loads((a/'recipe.json').read_text('utf8'))
    if r!=json.loads((b/'recipe.json').read_text('utf8')) or r['task']!='x_nana' or r['scope']!='sarangi_pause_icon' or r['parent_sha256']!=PARENT_SHA:raise ValueError('Icon recipe identity/reproduction differs')
    if digest(ART/'generated.png')!=r['art_source_sha256'] or digest(a/'icon.png')!=r['icon_sha256'] or digest(b/'icon.png')!=r['icon_sha256']:raise ValueError('Icon art differs')
    sources=source();updates=[]
    for name,(rec,old) in sources.items():
        raw=(a/name).read_bytes()
        if raw!=(b/name).read_bytes() or sha256(raw)!=r['records'][name]['sha256'] or rec!=r['records'][name]['record']:raise ValueError('Icon ARC reproduction differs')
        updates.append((rec,raw))
    preservation=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        for q in preservation['files']:
            if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected input changed')
        if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent changed')
    protect();out=ROOT/'out/ver_rin_nana'/('nana_run_icon_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',updates,PARENT_SHA);changes={q['lba'] for q in result['changed_sectors']};count=0
    with (PARENT/'rin_nana.bin').open('rb') as x,(out/'rin_nana.bin').open('rb') as y:
        while True:
            p,q=x.read(2352),y.read(2352)
            if not p:
                if q:raise ValueError('Disc grew')
                break
            if len(p)!=len(q) or (p!=q)!=(count in changes):raise ValueError('Unexpected sector difference')
            if count in changes:
                if p[:24]!=q[:24] or not any(rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048 for rec,_ in updates):raise ValueError('Change outside menu archives')
                validate_checks(q)
            count+=1
    with (out/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,result['size'])
        for rec,raw in updates:
            if d.read(rec['lba'],rec['size'])!=raw:raise ValueError('Disc readback differs')
    protect();shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue');shutil.copyfile(a/'PL00_U.ARC',out/'modified.arc');shutil.copyfile(a/'PL02_U.ARC',out/'PL02_U.ARC');shutil.copyfile(PARENT/'PL01_U.ARC',out/'PL01_U.ARC');shutil.copytree(PARENT/'art',out/'art');shutil.copytree(a,out/'menu_icon')
    v={'all_disc_sectors_compared':count,'changed_sectors':len(changes),'edc_ecc_checked':True,'readback_equal':True,'protected_files':len(preservation['files']),'independent_two_archive_reproduction':True,'player_motions_projectiles_charge_shots_preserved':True,'runtime_verified':False}
    m={'project':'ver_rin_nana','task':'x_nana','kind':'nana_run_and_sarangi_icon','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,'modified_archive_sha256':digest(out/'modified.arc'),'archive':sources['PL00_U.ARC'][0],'art':'art','menu_icon':'menu_icon','verification':v,'runtime_verified':False,'new_animation_user_accepted':False}
    for name,data in [('manifest.json',m),('verification.json',v),('preservation.json',preservation)]:write(out/name,data)
    write(ROOT/'projects/ver_rin_nana/current_build.json',{'project':'ver_rin_nana','task':'x_nana','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'art':(out/'art').relative_to(ROOT).as_posix(),'inherited_from':PARENT.relative_to(ROOT).as_posix(),'runtime_verified':False});print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changes)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','build'));p.add_argument('--output',type=Path);p.add_argument('--candidate',type=Path);p.add_argument('--reproduced',type=Path);a=p.parse_args()
    if a.command=='prepare':prepare(a.output.resolve())
    else:build(a.candidate.resolve(),a.reproduced.resolve())
