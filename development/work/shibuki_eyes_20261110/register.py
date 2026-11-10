import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
D=Path(__file__).parent;W=ROOT/'work/steam_port_20261109'
def load(p):return json.loads(p.read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
rows=load(W/'shibuki_eyes_builds.json');by={r['target_arc']:r for r in rows};replacement={r['parent_sha256']:r['output_sha256']for r in rows}
def replace(v):
    if isinstance(v,str):return replacement.get(v,v)
    if isinstance(v,list):return [replace(x)for x in v]
    if isinstance(v,dict):return {k:replace(x)for k,x in v.items()}
    return v
if sys.argv[1]=='prepare':
    assert load(D/'asset_verification.json')['passed'];assert not (D/'registration.json').exists()
    updates={}
    # Only advance current pointers whose parent hash matches. Old history stays intact.
    for p in W.glob('*builds.json'):
        if p.name=='shibuki_eyes_builds.json':continue
        old=load(p);new=load(p)
        if not isinstance(new,list):continue
        for row in new:
            if not isinstance(row,dict):continue
            target=row.get('target_arc',row.get('relative_path','').split('/')[-1]);r=by.get(target)
            if r and row.get('output_sha256')==r['parent_sha256']:
                row.update(output=r['output'],output_sha256=r['output_sha256'],shibuki_eyes_parent_sha256=r['parent_sha256'])
        if new!=old:updates[p.name]=new
    for n in ['dialogue_display_patch','dialogue_runtime_patch','portrait_routes','dialogue_variant_runtime','ultimate_runtime','menu_outfits_runtime','audio_runtime','effect_colors_runtime']:
        p=W/(n+'.json');old=load(p);new=replace(old)
        if new!=old:updates[p.name]=new
    plan=[]
    for name,v in updates.items():
        before=(W/name).read_bytes();p=D/'parents'/name;p.parent.mkdir(exist_ok=True)
        if p.exists():assert p.read_bytes()==before
        else:p.write_bytes(before)
        save(D/'registered'/name,v);plan.append({'name':name,'before':sha(before),'after':sha((D/'registered'/name).read_bytes())})
    save(D/'registration_prepared.json',plan);print({'prepared':len(plan)})
elif sys.argv[1]=='apply':
    game=Path(load(W/'backup_manifest.json')['steam_root']);plan=load(D/'registration_prepared.json')
    for r in rows:assert sha((game/r['relative_path']).read_bytes())==r['output_sha256']
    for r in plan:assert sha((W/r['name']).read_bytes())==r['before'] and sha((D/'registered'/r['name']).read_bytes())==r['after']
    done=[]
    try:
        for r in plan:(W/r['name']).write_bytes((D/'registered'/r['name']).read_bytes());done.append(r['name'])
    except Exception:
        for n in reversed(done):(W/n).write_bytes((D/'parents'/n).read_bytes())
        raise
    save(D/'registration.json',plan);print({'registered':len(plan)})
