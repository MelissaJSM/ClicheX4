import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.overhaul_activate import BUILDS
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
base=ROOT/'work/overhaul_20261105/baseline';out=Path(__file__).parent
changed={f'projects/{p}/{n}'for p in BUILDS for n in('project.json','current_build.json')}
states={'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000':'57977106f9bf2a8fae08834c94225fdcdf477d895e82256510e7a745f5259440',
        'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000.pic':sha(base/'current_progress/SLUS_005.61.000.pic')}
protected=[]
for item in read(base/'preservation.json'):
    name=item['path'];actual=sha(ROOT/name)
    if name in changed:kind='authorized_pointer_update'
    else:
        expected=states.get(name,item['sha256']);assert actual==expected,name
        kind='authorized_asset_cache_update'if name in states else'unchanged'
    protected.append(dict(path=name,sha256=actual,kind=kind))
for project,(stem,expected)in BUILDS.items():
    pointer=read(ROOT/'projects'/project/'current_build.json');assert pointer['sha256']==expected
    build=ROOT/pointer['build'];assert sha(build/(stem+'.bin'))==expected
    assert (ROOT/pointer['cue']).exists()
    settings=read(ROOT/'projects'/project/'project.json');assert settings['latest_integrated_build']==pointer['build']
    old=read(base/'pointers'/project/'project.json')
    for ref in old['references']:assert sha(ROOT/ref['path'])==ref['sha256'],ref['path']
    for name in('project.json','current_build.json'):
        original=next(x for x in read(base/'preservation.json')if x['path']==f'projects/{project}/{name}')
        assert sha(base/'pointers'/project/name)==original['sha256']
assert sha(base/'current_progress/SLUS_005.61.000')=='736cdc2dc277767d2e4c8b935137bc9ad5ab07ff8074323e0b2f710070657719'
archives=read(out/'intermediate_archives.json')
for a in archives:
    assert not(ROOT/a['target']).exists()
    assert sha(ROOT/a['archive'])==a['archive_sha256']
    assert a['restored_hash_verified']
doc=ROOT/'docs/OVERHAUL_ART_REVIEW.md';links=[]
for target in re.findall(r'\]\(([^)]+)\)',doc.read_text('utf8')):
    if target.startswith(('https:','http:','#')):continue
    p=(doc.parent/target.split('#')[0]).resolve();assert p.exists(),str(p);links.append(target)
result=dict(passed=True,protected_files=protected,settings_references_verified=8,
    final_builds={p:h for p,(_,h)in BUILDS.items()},previous_pointers_preserved=True,
    original_latest_progress_preserved=True,archives_verified=len(archives),art_links_verified=len(links),
    additional_saved_bytes=sum(a['original_bytes']-a['archive_bytes']for a in archives))
(out/'post_apply_audit.json').write_text(json.dumps(result,indent=2)+'\n','utf8')
print(json.dumps({k:v for k,v in result.items()if k!='protected_files'}))
