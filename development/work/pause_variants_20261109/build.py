"""Build and read back pause-only candidates from the authenticated current BINs."""
import json, struct, shutil
from prepare import ROOT,H,MODES,entry,sha,save_json,off,HOOK,hook,aliased_composition,local_composition,compose_static,source_x
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash,write_archive_copies
from src.psx_sector import validate_checks

def load(p):return json.loads(p.read_text('utf8'))

protected=load(ROOT/'work/illustration_variants_20261108/protection_before_black.json')['files']
snapshot={name:{'size':(ROOT/name).stat().st_size,'sha256':file_hash(ROOT/name)}for name in protected}
save_json(H/'protection_before.json',{'files':snapshot})
results=[]
for mode in MODES:
    d=H/mode;ptr=load(d/'pointer.json');assert load(ROOT/'projects'/mode/'current_build.json')==ptr
    source=ROOT/ptr['cue'];source=source.with_suffix('.bin');assert file_hash(source)==ptr['sha256']
    prep=d/'prepared';ver=load(prep/'verification.json');cpu=load(prep/'cpu_verification.json')
    replacements={n:(prep/n).read_bytes()for n in ['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','SLUS_005.61']}
    assert cpu['passed'] and cpu['exe_sha256']==sha(replacements['SLUS_005.61'])
    originals,records=read_disc(source,list(replacements)+['ST00_00.ARC','COL00_0X.ARC'])
    for n in replacements:assert originals[n]==(d/'originals'/n).read_bytes()
    # Authenticate reusable face pixels against the active BIN, including Ultimate.
    st=originals['ST00_00.ARC'];parts=entry(st,10);g=entry(st,0x10102)[198656:]
    bankoffset=struct.unpack_from('<I',parts,11*4)[0]
    for n in [0,1,2,3,8,9]:
        p=parts if n<8 else struct.pack('<I',4)+parts[bankoffset+1376:]
        c=aliased_composition(p,11 if n<8 else 0,n if n<8 else n-8)
        px,size,_,_=compose_static(g,local_composition(c));im,path=source_x(mode,n)
        assert px==im.tobytes() and size==im.size,(mode,n,'Source portrait no longer current')
    if mode=='ver_buki_riko':
        r=ROOT/'work/illustration_variants_20261108/ver_buki_riko/regions_v2'
        assert entry(st,0x10102)[217088:217088+12288]==(r/'dialogue_texture.bin').read_bytes()
        zoff=struct.unpack_from('<I',parts,13*4)[0];zb=(r/'dialogue_parts.bin').read_bytes()
        assert parts[zoff:zoff+len(zb)]==zb
    exe=replacements['SLUS_005.61'];oe=originals['SLUS_005.61']
    assert exe[:off(HOOK)]==oe[:off(HOOK)] and exe[off(HOOK)+len(hook()):]==oe[off(HOOK)+len(hook()):]
    for q in ver['arcs']:assert q['before']==sha(originals[q['file']]) and q['after']==sha(replacements[q['file']])
    stem='rin_nana' if mode==MODES[0] else 'shibuki_riko'
    out=ROOT/'out'/mode/'pause_variants_20261109_v1';out.mkdir(exist_ok=False);target=out/(stem+'.bin')
    result=write_archive_copies(source,target,[({**records[n],'sha256':sha(originals[n])},b)for n,b in replacements.items()],ptr['sha256'])
    declared={q['lba']for q in result['changed_sectors']};actual=set()
    permitted={lba for n in replacements for lba in range(records[n]['lba'],records[n]['lba']+(records[n]['size']+2047)//2048)}
    with source.open('rb')as f,target.open('rb')as t:
        for lba in range(result['size']//2352):
            a,b=f.read(2352),t.read(2352)
            if a!=b:
                assert lba in declared and lba in permitted and a[:24]==b[:24]
                validate_checks(b);actual.add(lba)
    assert actual==declared and read_disc(target,list(replacements))[0]==replacements
    assert file_hash(source)==ptr['sha256']
    (out/(stem+'.cue')).write_bytes((ROOT/ptr['cue']).read_bytes())
    save_json(out/'sector_changes.json',result)
    manifest={'project':mode,'task':'pause_variants_20261109','parent_cue':ptr['cue'],'parent_sha256':ptr['sha256'],
        'modified_bin':{k:v for k,v in result.items()if k!='changed_sectors'},'changed_files':list(replacements),
        'changed_sectors':len(actual),'all_disc_sectors_compared':result['size']//2352,'EDC_ECC_checked':True,
        'readback_exact':True,'other_parent_sectors_exact':True,'gameplay_sprite_audio_dialogue_HQ_bytes_unchanged':True,
        'static':ver,'cpu':cpu,'source_art_matches_current_BIN':True,'runtime_verified':False,'user_accepted':False,
        'x_hunter_armor_outfits_implemented':False}
    save_json(out/'manifest.json',manifest)
    review=out/'review';review.mkdir()
    for p in prep.glob('*.png'):shutil.copyfile(p,review/p.name)
    recipe=review/'recipe';recipe.mkdir()
    for p in H.glob('*.py'):shutil.copyfile(p,recipe/p.name)
    for name in ['verification.json','cpu_verification.json']:shutil.copyfile(prep/name,review/name)
    resultptr={'mode':mode,'cue':(out/(stem+'.cue')).relative_to(ROOT).as_posix(),'sha256':result['sha256'],'changed_sectors':len(actual)}
    results.append(resultptr);print(json.dumps(resultptr),flush=True)
for name,q in snapshot.items():assert file_hash(ROOT/name)==q['sha256'],name
save_json(H/'builds.json',results)
