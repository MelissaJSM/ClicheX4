"""Combine already verified PS1 Ultimate graphics with installed Korean dialogue."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.steam_arc import SteamArc
W=ROOT/'work/steam_port_20261109'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8')

def main():
    graphics=json.loads((W/'x_builds_prepared.json').read_text('utf8'))
    dialogue=json.loads((W/'dialogue_builds.json').read_text('utf8'));reports=[]
    spec=json.loads((W/'dialogue_runtime_patch.json').read_text('utf8'))
    oldspec=W/'dialogue_before_ultimate_runtime_patch.json'
    if not oldspec.exists():oldspec.write_bytes((W/'dialogue_runtime_patch.json').read_bytes())
    for g in [r for r in graphics if r['player']=='pl02']:
        mode=g['mode'];ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'))
        if ptr['sha256']!=g['source_bin_sha256']:raise ValueError('Prepared graphics source is stale')
        with ((ROOT/ptr['cue']).with_suffix('.bin')).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=ptr['sha256']:raise ValueError('PS1 source mismatch')
        d=next(r for r in dialogue if r['target_arc']==g['target_arc'])
        gb=(ROOT/g['output']).read_bytes();db=(ROOT/d['output']).read_bytes()
        if sha(gb)!=g['output_sha256'] or sha(db)!=d['output_sha256']:raise ValueError('Prepared input hash mismatch')
        ga=SteamArc(gb);da=SteamArc(db);updates={}
        for e in ga.entries:
            if e.payload[:4] in (b'TEX\0',b'COF\0',b'PAT\0',b'COL\0'):updates[e.key]=e.payload
        result=da.rebuild(updates);back=SteamArc(result);back.validate_stream_order()
        if list(da.by_key)!=list(back.by_key):raise ValueError('Entry order changed')
        for e in da.entries:
            if back.by_key[e.key].payload!=updates.get(e.key,e.payload):raise ValueError('Non-graphics resource changed')
        out=ROOT/'out'/mode/'steam_ultimate_20261109_v1/nativeDX10/X4/romPC'/g['target_arc'];out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists() and out.read_bytes()!=result:raise ValueError('Output collision')
        out.write_bytes(result)
        reports.append({'mode':mode,'target_arc':g['target_arc'],'source_bin_sha256':ptr['sha256'],'output':out.relative_to(ROOT).as_posix(),'output_sha256':sha(result),'graphics_parent':g['output'],'dialogue_parent':d['output'],'korean_dialogue_preserved':True,'non_graphics_preserved':True,'install_eligible':True,'runtime_verified':False})
        spec['installed_requirements']['nativeDX10/X4/romPC/'+g['target_arc']]=sha(result)
    write(W/'ultimate_builds.json',reports)
    write(W/'ultimate_runtime.json',{'installed_requirements':{'nativeDX10/X4/romPC/'+r['target_arc']:r['output_sha256'] for r in reports},'mask_rule':'special X: 15 before acquisition or frame217..230; otherwise 0. Normal X unchanged.'})
    write(W/'dialogue_runtime_patch.json',spec)
    print({'archives':len(reports),'dialogue_preserved':True})
if __name__=='__main__':main()
