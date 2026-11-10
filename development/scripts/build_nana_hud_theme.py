"""나나 토끼귀 과녁 HUD와 메뉴 테마를 누적하고 원본·전투를 보존한다."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_hud_theme import ART,PARENT,PARENT_SHA,sources,make_overlay,patch
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks
def validate(art,reproduced):
    if art.resolve()==reproduced.resolve()or any(not q.resolve().is_relative_to(ART)for q in(art,reproduced)):raise ValueError('Invalid independent art paths')
    r=json.loads((art/'recipe.json').read_text('utf8'));r2=json.loads((reproduced/'recipe.json').read_text('utf8'))
    if r!=r2 or r['kind']!='nana_hud_theme'or r['parent_sha256']!=PARENT_SHA or r['parent_manifest_sha256']!=digest(PARENT/'manifest.json'):raise ValueError('Parent/reproduction binding differs')
    if r['inputs']!={n:digest(ART/n)for n in('generated.png','prompt.txt','refine_prompt.txt')}or r['reference_sha256']!=digest(ROOT/'character/ver_rin_nana/nana(X)_mark.webp'):raise ValueError('Art/prompt/reference source changed')
    names={p.name for p in art.iterdir()if p.is_file()}
    if names!={p.name for p in reproduced.iterdir()if p.is_file()}or any((art/n).read_bytes()!=(reproduced/n).read_bytes()for n in names):raise ValueError('Independent reproduction differs')
    m,records,raw,pal=sources();arc_names=sorted(raw)
    if [q['file']for q in r['files']]!=arc_names:raise ValueError('ARC scope differs')
    new={};replacements=[]
    for q in r['files']:
        n=q['file'];rec=records[n];data=(art/n).read_bytes()
        if q['source']!=rec or len(data)!=rec['size']or sha256(data)!=q['sha256']:raise ValueError('Resource binding/hash differs')
        new[n]=data;replacements.append((rec,data))
    expected,info=make_overlay(raw['PL00_U.ARC'],pal);im=Image.open(art/'overlay.png');actual=np.array(im)
    if im.mode not in('P','L')or im.size!=(23,13)or not np.array_equal(expected,actual)or info!=r['art']or digest(art/'overlay.png')!=r['overlay_sha256']:raise ValueError('Native emblem differs from art')
    if(art/'native_hud_palette.bin').read_bytes()!=pal or sha256(pal)!=r['palette_sha256']:raise ValueError('HUD palette differs')
    v={}
    for n in arc_names:
        want,v[n]=patch(raw[n],actual)
        if want!=new[n]:raise ValueError('Unowned player bytes changed')
    if json.loads(json.dumps(v))!=r['verification']:raise ValueError('Verification claims differ')
    return m,r,replacements,v,sorted(names)
def build(art,reproduced):
    m,r,replacements,v,names=validate(art,reproduced);protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Parent changed')
        for q in protection['files']:
            if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected input changed: '+q['path'])
    protect();out=ROOT/'out/ver_rin_nana'/('nana_hud_theme_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA);changed={q['lba']for q in result['changed_sectors']};count=0
    with(PARENT/'rin_nana.bin').open('rb')as a,(out/'rin_nana.bin').open('rb')as b:
        while True:
            x,y=a.read(2352),b.read(2352)
            if not x:
                if y:raise ValueError('Output longer')
                break
            if len(x)!=len(y)or(x!=y)!=(count in changed):raise ValueError('Undeclared sector change')
            if count in changed:
                if x[:24]!=y[:24]or not any(q['lba']<=count<q['lba']+(q['size']+2047)//2048 for q,data in replacements):raise ValueError('Change outside HUD sectors')
                validate_checks(y)
            count+=1
    with(out/'rin_nana.bin').open('rb')as f:
        d=DiscReader(f,result['size']);iso={q['path']:q for q in d.inspect()['files']}
        for q,data in replacements:
            if d.read(q['lba'],q['size'])!=data:raise ValueError('HUD readback differs')
        q=iso['/ARC/PL01_U.ARC;1']
        if d.read(q['lba'],q['size'])!=(PARENT/'PL01_U.ARC').read_bytes():raise ValueError('Rin ARC changed')
    protect()
    for n in('rin_nana.cue','PL01_U.ARC'):shutil.copyfile(PARENT/n,out/n)
    shutil.copyfile(art/'PL00_U.ARC',out/'modified.arc');shutil.copyfile(art/'PL02_U.ARC',out/'PL02_U.ARC')
    for n in('menu_icon','inherited_small_ui','portrait','hunter','dialogue','pause','weapon_get'):shutil.copytree(PARENT/n,out/n)
    shutil.copytree(art,out/'hud_theme');v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,all_other_parent_sectors_exact=True,readback_identical=True,rin_arc_exact=True,protected_files=len(protection['files']),independent_preparation_files=names)
    manifest={**m,'kind':'nana_hud_theme','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,'modified_archive_sha256':digest(out/'modified.arc'),'verification':v,'inherited_verification':m['verification'],'inherited_manifest':(PARENT/'manifest.json').relative_to(ROOT).as_posix(),'hud_theme_overlay':{'recipe':(out/'hud_theme/recipe.json').relative_to(ROOT).as_posix(),'runtime_verified':False,'user_accepted':False},'runtime_verified':False}
    for n,data in(('manifest.json',manifest),('verification.json',v),('preservation.json',protection),('reproducibility.json',{'candidate':art.relative_to(ROOT).as_posix(),'reproduced':reproduced.relative_to(ROOT).as_posix(),'files_identical':names})):(out/n).write_text(json.dumps(data,indent=2)+'\n','utf8')
    pointer={'project':'ver_rin_nana','task':'x_nana','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'cumulative_base_references':220,'ui_user_accepted':True,'selection_portrait_user_accepted':True,'hunter_user_accepted':True,'dialogue_user_accepted':True,'pause_user_accepted':True,'weapon_get_user_accepted':True,'hud_theme_user_accepted':False,'runtime_verified':False,'user_vehicle_accepted':True};(ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed),'protected':len(protection['files']),'independent_files':len(names)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);a=p.parse_args();build(a.art.resolve(),a.reproduced.resolve())
