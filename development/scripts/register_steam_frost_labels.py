"""Prepare/apply cumulative pointers without dropping earlier Steam changes."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_steam_frost_labels import W,D,sha,save
from scripts.steam_runtime import EXE

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','apply']);args=p.parse_args()
    builds=json.loads((W/'frost_labels_builds.json').read_text('utf8'));by={r['target_arc']:r for r in builds}
    for name in ['asset_verification.json','native_frost_verification.json']:
        if not json.loads((D/name).read_text('utf8'))['passed']:raise ValueError('Required verification missing')
    if args.action=='prepare':
        if (D/'registration.json').exists():raise ValueError('Already registered')
        updates={};replacement={r['parent_sha256']:r['output_sha256'] for r in builds}
        for name in ['pause_builds.json','audio_pause_builds.json','audio_builds.json','portrait_builds.json','hq_variant_builds.json']:
            rows=json.loads((W/name).read_text('utf8'))
            for row in rows:
                target=row.get('target_arc',row.get('relative_path','').split('/')[-1]);new=by.get(target)
                if new:
                    if row['output_sha256']!=new['parent_sha256']:raise ValueError('Current cumulative parent mismatch: '+name+' '+target)
                    row.update(output=new['output'],output_sha256=new['output_sha256'],frost_labels_parent_sha256=new['parent_sha256'],frost_labels_manifest='frost_labels_builds.json')
            updates[name]=rows
        def replace(v):
            if isinstance(v,str):return replacement.get(v,v)
            if isinstance(v,list):return [replace(x)for x in v]
            if isinstance(v,dict):return {k:replace(x)for k,x in v.items()}
            return v
        for name in ['portrait_routes.json','dialogue_variant_runtime.json','audio_runtime.json','menu_outfits_runtime.json','ultimate_runtime.json','effect_colors_runtime.json','dialogue_runtime_patch.json']:
            old=json.loads((W/name).read_text('utf8'));new=replace(old)
            if new!=old:updates[name]=new
        parents=D/'parents';ready=D/'registered';parents.mkdir(exist_ok=True);ready.mkdir(exist_ok=True)
        records=[]
        for name,data in updates.items():
            raw=(W/name).read_bytes();backup=parents/name
            if backup.exists() and backup.read_bytes()!=raw:raise ValueError('Parent collision')
            backup.write_bytes(raw);save(ready/name,data)
            records.append({'name':name,'before':sha(raw),'after':sha((ready/name).read_bytes())})
        save(D/'registration_prepared.json',{'files':records,'build_manifest_sha256':sha((W/'frost_labels_builds.json').read_bytes())});print({'prepared':len(records)})
    else:
        plan=json.loads((D/'registration_prepared.json').read_text('utf8'))
        if sha((W/'frost_labels_builds.json').read_bytes())!=plan['build_manifest_sha256']:raise ValueError('Build manifest changed')
        for r in builds:
            if sha((EXE.parent/r['relative_path']).read_bytes())!=r['output_sha256']:raise ValueError('Apply assets first')
        for r in plan['files']:
            if sha((W/r['name']).read_bytes())!=r['before'] or sha((D/'registered'/r['name']).read_bytes())!=r['after']:raise ValueError('Pointer changed after preparation')
        done=[]
        try:
            for r in plan['files']:(W/r['name']).write_bytes((D/'registered'/r['name']).read_bytes());done.append(r['name'])
        except Exception:
            for n in reversed(done):(W/n).write_bytes((D/'parents'/n).read_bytes())
            raise
        save(D/'registration.json',plan);print({'registered':len(done)})

if __name__=='__main__':main()
