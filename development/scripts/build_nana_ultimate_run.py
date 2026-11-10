"""이동·사격과 캡슐 자원을 독립 재현 후 별도 BIN에 적용한다."""
import argparse,json,shutil,struct,sys,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_ultimate_run import D,PARENT,PARENT_SHA,ARC_SHA,FRAMES,entry,require,write,verify
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks
from src.psx_ui_atlas import local_composition

def validate(folder,data=None,*,parent=PARENT,parent_sha=PARENT_SHA,arc_sha=ARC_SHA,frames=FRAMES,capsule_banks=tuple(range(10,14)),base_correction=None):
    recipe=json.loads((folder/'recipe.json').read_text('utf8'));require(recipe['parent_sha256']==parent_sha and recipe['parent_arc_sha256']==arc_sha and recipe['frames']==frames,'Wrong recipe scope')
    old=(parent/'PL02_U.ARC').read_bytes();require(sha256(old)==arc_sha,'Unsupported parent ARC')
    if base_correction is not None:
        old,correction=base_correction(old)
        require(json.loads(json.dumps(correction))==recipe['base_correction'],'Base correction proof differs')
    data=data if data is not None else (folder/'PL02_U.ARC').read_bytes();require(sha256(data)==recipe['files']['PL02_U.ARC'],'Prepared archive differs')
    targets={n:np.array(Image.open(folder/f'ultimate_{n:03}.png')) for n in frames};capsules={b:[np.array(Image.open(folder/f'capsule_{b}_{n:02}.png')) for n in range(12)] for b in capsule_banks};proof=verify(old,data,targets,capsules)
    g,c,p=[entry(data,k) for k in (2,3,9)];og,oc=[entry(old,k) for k in (2,3)];bank=graphics_bank(g,0,allow_bank_aliases=True);gpu=combos=0;preserved_native_edges=[]
    for n in frames:
        f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;size=(targets[n].shape[1],targets[n].shape[0]);layers={b:canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(c,b,n)),size=size) for b in (0,5,6,7,8)}
        atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
        for b in layers:
            for q in composition_frame(c,b,n)['parts']:
                t=q['tile'];patch=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                if t%16==0 and patch[:,0].any():
                    require(recipe['kind']=='ultimate_reaction' and (n,b,t,q['x'],q['y'],q['clut'])==(111,0,16,10,18,2),'Unsafe GPU U edge')
                    of=graphics_bank(og,0,allow_bank_aliases=True)['frames'][n];oraw=decode_stream(og,of['offset'],of['limit'],of['tile_count']*128).data;oa=np.frombuffer(indexed_atlas(oraw,of['tile_count'])[0],np.uint8).reshape(-1,256);original_parts=composition_frame(oc,b,n)['parts'];require(np.array_equal(patch,oa[t//16*16:t//16*16+16,t%16*16:t%16*16+16]) and any(all(q[k]==z[k]for k in('flags','tile','x','y','clut'))for z in original_parts),'Native effect edge changed');preserved_native_edges.append(dict(frame=n,bank=b,tile=t,x=q['x'],y=q['y'],clut=q['clut']))
                require(not q['flip_y'] or t//16%16!=0 or not patch[0].any(),'Unsafe GPU V edge');gpu+=1
        for mask in range(16):
            got=layers[0].copy()
            for bit,b in ((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:got=np.where(layers[b],layers[b],got)
            want=targets[n] if mask&1 else layers[0]
            for flip in (False,True):require(np.array_equal(got[:,::-1] if flip else got,want[:,::-1] if flip else want),'Part/direction combination differs');combos+=1
    pistol_pairs=0
    for q in recipe['registration']:
        n=q['frames'][1]
        if q.get('pistol_mode')=='authored_lowered':
            require(recipe['kind']=='ultimate_low_hp_shape' and n in range(120,126) and q['pistol_template_file']=='lowered_weapon_patch.png','Unsupported authored weapon scope')
            patch=np.array(Image.open(folder/q['pistol_template_file']));x,y,x2,y2=q['pistol_mask_bbox']
            require(patch.shape==(11,9) and np.array_equal(targets[n][y:y2,x:x2],patch),'Lowered Sarang-i differs between breathing frames');pistol_pairs+=1;continue
        if not q.get('pistol_present',True):
            nongun={'ultimate_nova':set(range(213,221)),'ultimate_vehicle':set(range(162,175))|set(range(184,204)),'ultimate_victory_edge':{204,205},'ultimate_air_transition':{93,94},'ultimate_reaction':{106,107,108,110,111,233,234,235,236},'ultimate_ladder':(set(range(143,156))|{183})-{150,155},'ultimate_ceremony':{141,142,156,157,204,205}}
            require(n in nongun.get(recipe['kind'],set()) and q['pistol_mask_bbox'] is None,'Unapproved gunless scope');continue
        x,y,x2,y2=q['pistol_mask_bbox'];native=raster(og,oc,0,0,n);require(np.array_equal(targets[n][y:y2,x:x2],native[y:y2,x:x2]),'Sarang-i pixels changed');pistol_pairs+=1
    proof.update(part_direction_combinations=combos,gpu_parts=gpu,pistol_pairs=pistol_pairs)
    if preserved_native_edges:proof['preserved_native_effect_edges']=preserved_native_edges
    return proof

def main(art,repro,base_path=None):
    base=(base_path or PARENT).resolve();supported={PARENT.resolve():PARENT_SHA,(ROOT/'out/ver_rin_nana/nana_ultimate_run_20261031T001440082551Z').resolve():'c68375672dbc6104f2ed9b8ff147cfa4183319bdefc58e4b9ef6dc39490a8865',(ROOT/'out/ver_rin_nana/nana_ultimate_run_20261031T002627736363Z').resolve():'e4c46d84e44c1df8ba5a4f997c0a7eb9d4c76697be8c2c9dc7a9b3989bb1b692'};require(base in supported,'Unsupported deployment parent');base_sha=supported[base]
    bm=json.loads((base/'manifest.json').read_text('utf8'));require(bm['task']=='ultimate_armor_nana' and bm['modified_bin']['sha256']==base_sha,'Unexpected deployment manifest');base_arc_sha=bm['modified_archive_sha256']
    art,repro=art.resolve(),repro.resolve();require(art.is_relative_to(D) and repro.is_relative_to(D) and art!=repro,'Isolated independent preparation required')
    names={p.name for p in art.iterdir()};require(names=={p.name for p in repro.iterdir()},'Reproduction set differs')
    for n in names:require((art/n).read_bytes()==(repro/n).read_bytes(),'Reproduction differs: '+n)
    proof=validate(art);v=bytearray((art/'PL02_U.ARC').read_bytes());v[len(v)//2]^=1
    try:validate(art,bytes(v))
    except ValueError:proof['corrupt_resource_rejected']=True
    else:raise ValueError('Corrupt resource accepted')
    suite=unittest.TestSuite()
    for pat in ('test_psx_bank_repack.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py','test_psx_tile_layout.py','test_psx_paired_layout.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pat))
    tests=unittest.TextTestRunner().run(suite);require(tests.wasSuccessful(),'Unit test failure');proof.update(unit_tests=tests.testsRun,independent_files=len(names))
    pointer=ROOT/'projects/ver_rin_nana/current_build.json';prior=pointer.read_bytes();require(json.loads(prior)['sha256']==base_sha,'Active build changed');protection=json.loads((base/'preservation.json').read_text('utf8'))
    def protect():
        require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent BIN changed')
        require(digest(base/'rin_nana.bin')==base_sha,'Deployment parent changed')
        for q in protection['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed: '+q['path'])
    protect();data=(art/'PL02_U.ARC').read_bytes()
    with (base/'rin_nana.bin').open('rb') as f:
        disc=DiscReader(f,(base/'rin_nana.bin').stat().st_size);rec=next(q for q in disc.inspect()['files'] if q['name']=='PL02_U.ARC;1');require(sha256(disc.read(rec['lba'],rec['size']))==base_arc_sha,'Disc source differs');rec={**rec,'sha256':base_arc_sha}
    out=ROOT/'out/ver_rin_nana'/('nana_ultimate_run_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();result=write_archive_copies(base/'rin_nana.bin',out/'rin_nana.bin',[(rec,data)],base_sha);changed={q['lba'] for q in result['changed_sectors']};total=result['size']//2352
    with (base/'rin_nana.bin').open('rb') as a,(out/'rin_nana.bin').open('rb') as b:
        for lba in range(total):
            x,y=a.read(2352),b.read(2352);require(len(x)==len(y)==2352 and (x!=y)==(lba in changed),'Unexpected sector change')
            if lba in changed:require(x[:24]==y[:24] and rec['lba']<=lba<rec['lba']+(rec['size']+2047)//2048,'Unexpected sector range');validate_checks(y)
        require(not b.read(1),'Output grew')
    with (out/'rin_nana.bin').open('rb') as f:
        disc=DiscReader(f,result['size']);require(disc.read(rec['lba'],rec['size'])==data,'Readback differs')
    protect();require(pointer.read_bytes()==prior,'Active pointer changed')
    for name in ('rin_nana.cue','modified.arc','PL01_U.ARC'):shutil.copyfile(base/name,out/name)
    shutil.copytree(base/'ultimate_start',out/'ultimate_start');shutil.copytree(art,out/'ultimate_run');(out/'PL02_U.ARC').write_bytes(data)
    proof.update(all_disc_sectors_compared=total,changed_sectors=sorted(changed),edc_ecc_checked=True,all_other_disc_bytes_preserved=True,protected_files=len(protection['files']),runtime_verified=False)
    m=json.loads((base/'manifest.json').read_text('utf8'));refs=sorted(set(m['implemented_ultimate_references'])|set(FRAMES));m.update(kind='nana_ultimate_run_capsule',parent=base.relative_to(ROOT).as_posix(),parent_sha256=base_sha,modified_bin=result,modified_archive_sha256=sha256(data),inherited_manifest=(base/'manifest.json').relative_to(ROOT).as_posix(),inherited_verification=m['verification'],verification=proof,implemented_ultimate_references=refs,ultimate_capsule_references=48,full_ultimate_complete=False,runtime_verified=False,ultimate_recipe=(out/'ultimate_run/recipe.json').relative_to(ROOT).as_posix());write(out/'manifest.json',m);write(out/'verification.json',proof);write(out/'preservation.json',protection);write(out/'previous_current_build.json',json.loads(prior))
    write(D/'run_build.json',{'build':out.relative_to(ROOT).as_posix(),'sha256':result['sha256'],'verification':proof});print(json.dumps({'build':out.relative_to(ROOT).as_posix(),'sha256':result['sha256'],'implemented':len(refs),'capsule':48,'verification':proof}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);p.add_argument('--parent',type=Path);a=p.parse_args();main(a.art,a.repro,a.parent)
