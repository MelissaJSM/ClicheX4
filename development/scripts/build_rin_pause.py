"""린 일시정지 얼굴을 고정 UI 타일에 적용한다. 전투와 다른 UI 바이트는 보존한다."""
import argparse,json,shutil,struct,sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_rin_dialogue import WORDS,PALETTE
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static,patch_static
from src.psx_ui_render import render_static_rgba
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

PARENT=ROOT/'out/ver_rin_nana/rin_dialogue_20261029T023808548418Z'
PARENT_SHA='f7803c51619a24a23590121282446c5980b52a1394ec2ca9b124ddb4da45b055'
ART=ROOT/'work/ver_rin_nana/illustrations/pause_v1'

def sources():
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Accepted dialogue parent differs')
    m=json.loads((PARENT/'manifest.json').read_text('utf8'));old=(PARENT/'modified.arc').read_bytes()
    if sha256(old)!=m['modified_archive_sha256']:raise ValueError('Parent player differs')
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size)
        rec=next(r for r in d.inspect()['files'] if r['path']=='/ARC/PL01_U.ARC;1')
        if d.read(rec['lba'],rec['size'])!=old:raise ValueError('Parent player readback differs')
    return m,{**rec,'sha256':sha256(old)},old

def composition(raw):
    return aliased_composition(struct.pack('<I',4)+entry(raw,0x12),0,10)

def verify(old,new,indices):
    g=entry(old,0x10007);ng=entry(new,0x10007);c=composition(old)
    expected_g=patch_static(g[12288:],{10:local_composition(c)},{10:(indices,(64,80))})
    pal=entry(old,0x11);npal=pal[:320]+PALETTE+pal[352:]
    if new!=replace_entry(replace_entry(old,0x10007,g[:12288]+expected_g),0x11,npal):raise ValueError('Unowned player/menu bytes changed')
    if composition(new)!=c:raise ValueError('Pause coordinates/flags changed')
    oldpx,size,bounds,cov=compose_static(g[12288:],local_composition(c))
    px,ns,nb,_=compose_static(ng[12288:],local_composition(c))
    if (px,ns,nb)!=(indices,size,bounds) or size!=(64,80):raise ValueError('Pause portrait readback differs')
    if bytes(bool(v) for v in indices)!=bytes(bool(v) for v in oldpx):raise ValueError('Original portrait border/silhouette changed')
    actual,rb=render_static_rgba(ng[12288:],c,{0:WORDS})
    a=np.frombuffer(indices,np.uint8).reshape(80,64);expected=np.zeros((80,64,4),np.uint8)
    for i,w in enumerate(WORDS[1:],1):expected[a==i]=[*(int(w>>s&31)*255//31 for s in (0,5,10)),255]
    if rb!=bounds or not np.array_equal(expected,np.array(actual)):raise ValueError('Actual menu CLUT rendering differs')
    parts_tiles={96+q['page']*256+q['tile'] for q in c['parts']}
    untouched=[]
    for e in psx_arc(old):
        kind=int(e['type'],16)
        if kind not in (0x10007,0x11):
            if entry(old,kind)!=entry(new,kind):raise ValueError('Non-UI player entry changed')
            untouched.append(kind)
    return {'portrait_frame':10,'size':list(size),'bounds':list(bounds),'fixed_texture_base_tile':96,
        'portrait_tiles':sorted(parts_tiles),'palette_row':10,
        'part_count':19,'all_parts_coordinates_and_timing_exact':True,'original_border_mask_exact':True,
        'actual_clut_render_equal':True,'protected_player_entries':untouched,
        'non_portrait_texture_bytes_exact':True,'other_palette_rows_exact':True,'runtime_verified':False}

def prepare(out):
    m,rec,old=sources();c=composition(old);g=entry(old,0x10007)
    px,size,bounds,coverage=compose_static(g[12288:],local_composition(c))
    mask=np.frombuffer(px,np.uint8).reshape(80,64)>0;ys,xs=np.nonzero(mask);box=(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)
    w,h=box[2]-box[0],box[3]-box[1];im=Image.open(ART/'generated.png').convert('RGB')
    scale=max(w/im.width,h/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    dx=(im.width-w)//2;dy=(im.height-h)//2;im=im.crop((dx,dy,dx+w,dy+h))
    canvas=np.zeros((80,64,3),np.uint8);canvas[box[1]:box[3],box[0]:box[2]]=np.array(im)
    colors=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in WORDS[1:]],np.int32)
    distance=((canvas.astype(np.int32)[:,:,None,:]-colors)**2).sum(3)
    a=np.where(mask,distance.argmin(2)+1,0).astype(np.uint8);indices=a.tobytes()
    ng=patch_static(g[12288:],{10:local_composition(c)},{10:(indices,size)})
    pal=entry(old,0x11);new=replace_entry(replace_entry(old,0x10007,g[:12288]+ng),0x11,pal[:320]+PALETTE+pal[352:])
    v=verify(old,new,indices);out.mkdir(parents=True,exist_ok=False)
    (out/'PL01_U.ARC').write_bytes(new);(out/'palette.bin').write_bytes(PALETTE)
    preview=save_image(indices,size,WORDS,out/'portrait.png');preview.resize((384,480),Image.Resampling.NEAREST).save(out/'portrait_6x.png')
    r={'kind':'rin_pause','parent_sha256':PARENT_SHA,'source':rec,'tool':'built-in image_gen',
        'art':(ART/'generated.png').relative_to(ROOT).as_posix(),'art_sha256':digest(ART/'generated.png'),
        'prompt':(ART/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(ART/'prompt.txt'),
        'portrait_sha256':digest(out/'portrait.png'),'modified_archive_sha256':sha256(new),
        'uniform_scale':scale,'target_box':box,'verification':v}
    (out/'recipe.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'prepared':str(out),'verification':v}))

def build(art):
    art=art.resolve()
    if not art.is_relative_to(ART):raise ValueError('Unexpected art directory')
    m,rec,old=sources();r=json.loads((art/'recipe.json').read_text('utf8'))
    if r['parent_sha256']!=PARENT_SHA or r['source']!=rec:raise ValueError('Parent binding changed')
    for key in ('art','prompt'):
        path=(ROOT/r[key]).resolve()
        if not path.is_relative_to(ART) or digest(path)!=r[key+'_sha256']:raise ValueError('Source image/prompt changed')
    new=(art/'PL01_U.ARC').read_bytes()
    if sha256(new)!=r['modified_archive_sha256'] or len(old)!=len(new) or digest(art/'portrait.png')!=r['portrait_sha256']:raise ValueError('Prepared art changed')
    v=verify(old,new,Image.open(art/'portrait.png').tobytes())
    protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        for q in protection['files']:
            if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected input changed: '+q['path'])
    protect();out=ROOT/'out/ver_rin_nana'/('rin_pause_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',[(rec,new)],PARENT_SHA)
    (out/'modified.arc').write_bytes(new);shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue')
    for folder in ('ui','portrait','hunter','dialogue'):shutil.copytree(PARENT/folder,out/folder)
    shutil.copytree(art,out/'pause')
    changed={q['lba'] for q in result['changed_sectors']};count=0
    with (PARENT/'rin_nana.bin').open('rb') as f,(out/'rin_nana.bin').open('rb') as g:
        while True:
            a,b=f.read(2352),g.read(2352)
            if not a:
                if b:raise ValueError('Output grew')
                break
            if len(a)!=len(b) or (a!=b)!=(count in changed):raise ValueError('Unexpected sector difference')
            if count in changed:validate_checks(b)
            count+=1
    with (out/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,result['size'])
        if d.read(rec['lba'],rec['size'])!=new:raise ValueError('Player readback differs')
    protect();v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,
        other_parent_sectors_exact=True,protected_files=len(protection['files']),readback_equal=True,
        embedded_static_bodies=m['verification']['embedded_static_bodies'])
    manifest={**m,'kind':'rin_pause','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,
        'modified_bin':result,'modified_archive_sha256':sha256(new),'verification':v,'inherited_verification':m['verification'],
        'pause_overlay':{'recipe':(out/'pause/recipe.json').relative_to(ROOT).as_posix(),'recipe_sha256':digest(out/'pause/recipe.json'),'runtime_verified':False},'runtime_verified':False}
    for name,data in [('manifest.json',manifest),('verification.json',v),('preservation.json',protection)]:
        (out/name).write_text(json.dumps(data,indent=2)+'\n','utf8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),
        'sha256':result['sha256'],'frames':m['cumulative_frames'],'bank1_frames':m['cumulative_bank1_frames'],'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','build']);p.add_argument('--art',type=Path,required=True);a=p.parse_args();(prepare if a.action=='prepare' else build)(a.art)
