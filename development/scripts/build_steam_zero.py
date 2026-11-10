"""Build separate Japanese Rin / English Riko ARC outputs from current PS1 BINs."""
import hashlib
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_player import dynamic_texture,static_texture

WORK=ROOT/'work/steam_port_20261109'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',default='v2')
    args=parser.parse_args()
    if args.version not in ('v1','v2','v3'):raise ValueError('Unknown build version')
    inventory=json.loads((ROOT/'work/steam_port_research_20261109/inventory.json').read_text(encoding='utf-8'))
    original_bin=Path(inventory['ps1_original']['path'])
    with original_bin.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=inventory['ps1_original']['sha256']:raise ValueError('PS1 original changed')
    originals,_=read_disc(original_bin,['PL01_U.ARC'])
    original=originals['PL01_U.ARC']
    reports=[]
    for mode,target in [('ver_rin_nana','pl01.arc'),('ver_buki_riko','pl01_eng.arc')]:
        pointer=json.loads((ROOT/'projects'/mode/'current_build.json').read_text(encoding='utf-8'))
        source_bin=(ROOT/pointer['cue']).with_suffix('.bin')
        with source_bin.open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=pointer['sha256']:raise ValueError('Current PS1 BIN mismatch')
        source_arcs,_=read_disc(source_bin,['PL01_U.ARC']);source=source_arcs['PL01_U.ARC']
        source_hash=sha(source)
        base=WORK/'original/nativeDX10/X4/romPC'/target
        arc=SteamArc(base.read_bytes(),inventory['archives'][target]['sha256'])
        updates={};rows=[]
        def find(name,magic):
            return next(e for e in arc.entries if e.name==name and e.payload[:4]==magic)
        pat=find('X4\\pat\\pl\\PL01',b'PAT\0')
        if pat_from_ps1(entry(original,3))!=pat.payload:raise ValueError('Original PAT correspondence failed')
        updates[pat.key]=pat_from_ps1(entry(source,3))
        for bank in (0,1):
            name=f'X4\\chr\\pl\\pl01\\pl01_{bank:03d}'
            tex,cof=find(name,b'TEX\0'),find(name,b'COF\0')
            new_tex,new_cof,report=dynamic_texture(tex.payload,cof.payload,entry(source,2),bank)
            updates[tex.key]=new_tex;updates[cof.key]=new_cof;rows.append(report)
        tex=find('X4\\chr\\com\\COM01_000',b'TEX\0')
        updates[tex.key]=static_texture(tex.payload,entry(original,0x10206),entry(source,0x10206))
        col=find('X4\\col\\pl\\charge01',b'COL\0')
        if col.payload[12:]!=entry(original,9):raise ValueError('Original COL correspondence failed')
        updates[col.key]=col.payload[:12]+entry(source,9)
        result=arc.rebuild(updates)
        out=ROOT/'out'/mode/f'steam_zero_20261109_{args.version}/nativeDX10/X4/romPC'/target
        out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists() and out.read_bytes()!=result:raise ValueError('Output exists with different data')
        out.write_bytes(result)
        changes=[{'name':e.name,'type':hex(e.kind),'before':sha(e.payload),'after':sha(updates[e.key])}
                 for e in arc.entries if e.key in updates and e.payload!=updates[e.key]]
        report={'mode':mode,'source_bin':str(source_bin.relative_to(ROOT)),'source_bin_sha256':pointer['sha256'],
                'source_arc_sha256':source_hash,'target_arc':target,'original_sha256':sha(arc.raw),
                'output':str(out.relative_to(ROOT)),'output_sha256':sha(result),'size':len(result),
                'changed_entries':changes,'dynamic_banks':rows,'unchanged_entries_verified':len(arc.entries)-len(changes),
                'game_runtime_verified':False,'scope':'all Zero dynamic body frames + static COM01 + PAT + player COL; other UI/audio/code pending'}
        (out.parents[3]/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        reports.append(report)
    (WORK/'zero_builds.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{'mode':r['mode'],'output':r['output'],'changes':len(r['changed_entries']),'banks':r['dynamic_banks']} for r in reports]))


if __name__=='__main__':main()
