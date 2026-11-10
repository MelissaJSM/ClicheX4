"""Create a new PS1 image; validate every sector and preserve both old builds."""
import json
import shutil
from pathlib import Path
from sync import ROOT, D, W, STEAM, INSTALLED, source, read_disc, file_hash, sha, save, entry, psx_arc, write_archive_copies, validate_checks


def load(path):
    return json.loads(path.read_text('utf8'))


prep = load(D/'preparation.json')
cpu = load(D/'native_verification.json')
assert prep['passed'] and cpu['passed'] and load(D/'player_audit.json')['passed']
assert load(D/'scope_verification.json')['passed']
ptr, parent = source('ver_buki_riko')
rnptr, rnparent = source('ver_rin_nana')
assert ptr == load(D/'parent_pointer.json')
paths = {parent, rnparent, ROOT/'MegaMan X4.bin', ROOT/'Rockman X4.bin'}
paths.update(p for p in (ROOT/'character').rglob('*') if p.is_file())
for folder in [ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator', ROOT/'work/ver_rin_nana/emulator']:
    for name in ['memcards', 'sstates']:
        if (folder/name).exists():
            paths.update(p for p in (folder/name).rglob('*') if p.is_file())
protected = {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sorted(paths)}
save(D/'protected_before.json', protected)
replacements = {name:(D/'prepared'/name).read_bytes() for name in prep['changed_arcs']}
assert all(sha(value)==prep['prepared_sha256'][name] for name,value in replacements.items())
assert sha(replacements['ST0D_0X.ARC'])==cpu['prepared_hq_sha256']
original, records = read_disc(parent, list(replacements)+['SLUS_005.61','PL01_U.ARC'])
for name,value in replacements.items():
    assert len(original[name])==len(value)
    for e in psx_arc(original[name]):
        kind = int(e['type'],16)
        if kind not in prep['changed_arcs'][name]:
            assert entry(original[name],kind)==entry(value,kind)
out = ROOT/'out/ver_buki_riko/ps1_latest_20261110_v1'
out.mkdir(exist_ok=False)
target = out/'shibuki_riko.bin'
result = write_archive_copies(parent,target,[({**records[name],'sha256':sha(original[name])},value) for name,value in replacements.items()],ptr['sha256'])
declared = {v['lba'] for v in result['changed_sectors']}
actual = set()
with parent.open('rb') as old, target.open('rb') as new:
    for lba in range(result['size']//2352):
        a,b = old.read(2352),new.read(2352)
        if a!=b:
            assert lba in declared and a[:24]==b[:24]
            validate_checks(b)
            actual.add(lba)
assert actual==declared
back,_ = read_disc(target,list(original))
assert all(back[name]==replacements.get(name,value) for name,value in original.items())
cue = out/'shibuki_riko.cue'
cue.write_bytes((ROOT/ptr['cue']).read_bytes())
assert cue.read_text('ascii').startswith('FILE "shibuki_riko.bin" BINARY')
shutil.copytree(D/'review',out/'review')
for name,expected in protected.items():
    assert file_hash(ROOT/name)==expected,name
for name,expected in INSTALLED.items():
    assert file_hash(STEAM/name)==expected,name
manifest = {
    'task':'ps1_latest_sync_20261110', 'parent':ptr['cue'], 'parent_sha256':ptr['sha256'],
    'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},
    'changed_files':list(replacements), 'changed_sectors':len(actual),
    'all_disc_sectors_compared':result['size']//2352, 'EDC_ECC_checked':True,
    'all_other_parent_sectors_exact':True, 'archive_lengths_LBA_and_layout_preserved':True,
    'native_decoder_and_loader_verified':True, 'rendered_frames_compared':prep['frames_compared'],
    'exe_gameplay_sprites_audio_palettes_timing_text_saves_preserved':True,
    'steam_installed_files_preserved':len(INSTALLED), 'protected_files_preserved':len(protected),
    'nana_rin_no_missing_sprite_update_found':True, 'nana_rin_current_cue':rnptr['cue'],
    'runtime_verified':False, 'user_accepted':False,
}
save(out/'manifest.json',manifest)
save(out/'sector_changes.json',result)
save(D/'build.json',{'cue':cue.relative_to(ROOT).as_posix(),'sha256':result['sha256'],'changed_sectors':len(actual),'rn_cue':rnptr['cue'],'rn_sha256':rnptr['sha256']})
for name in ['preparation.json','player_audit.json','native_verification.json','scope_verification.json']:
    shutil.copyfile(D/name,out/'review'/name)
print(json.dumps({'cue':str(cue),'sha256':result['sha256'],'changed_sectors':len(actual),'protected':len(protected)},ensure_ascii=False),flush=True)
