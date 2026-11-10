"""Read-only all-sector verification of audited sprite resources."""
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).parent))
from verify_prepared import PARENT, OUT, need, sha, digest, write
from scripts.discover_inputs import DiscReader
from src.psx_sector import rebuild_checks, validate_checks

def read(path,names=None):
    with path.open('rb') as f:
        disc=DiscReader(f,path.stat().st_size)
        rows=disc.inspect()['files']
        by_name={r['name'].split(';')[0]:r for r in rows if not r['directory']}
        data={} if names is None else {n:disc.read(by_name[n]['lba'],by_name[n]['size']) for n in names}
    return rows,by_name,data

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--character',choices=tuple(PARENT),required=True)
    p.add_argument('--bin',type=Path,required=True)
    p.add_argument('--sha256',required=True)
    p.add_argument('--proposal',type=Path,action='append',required=True)
    args=p.parse_args()
    mode,stem,expected=PARENT[args.character]
    parent=ROOT/f'out/{mode}/hurt_capsule_fix_20261106_v1/{stem}.bin'
    target=args.bin.resolve()
    need(target.is_relative_to(ROOT/'out'/mode),'Output outside mode')
    need(target!=parent.resolve() and not target.samefile(parent),'Parent/output alias')
    need(digest(parent)==expected and digest(target)==args.sha256,'Disc hash mismatch')
    replacements={};evidence=[]
    for path in args.proposal:
        proposal=json.loads(path.read_text('utf8'))
        need(proposal['baseline_sha256']==expected,'Proposal parent mismatch')
        for name,spec in proposal['files'].items():
            need(name not in replacements,'Overlapping proposals need a separately audited merged ARC')
            need(name in ('PL00_U.ARC','PL02_U.ARC'),'Only permitted player graphic ARC')
            data=(ROOT/spec['path']).read_bytes()
            need(sha(data)==spec['after'],'Prepared ARC hash mismatch')
            replacements[name]=(data,spec)
        evidence.append({'path':str(path.resolve().relative_to(ROOT)),'sha256':digest(path)})
    names=set(replacements)|{'SLUS_005.61'}
    rows,records,old=read(parent,names)
    newrows,_,new=read(target,names)
    need(rows==newrows,'ISO metadata changed')
    need(old['SLUS_005.61']==new['SLUS_005.61'],'EXE changed')
    payloads={}
    for name,(data,spec) in replacements.items():
        need(new[name]==data and sha(old[name])==spec['before'],'Final ARC not exact prepared')
        need(len(data)==records[name]['size']==len(old[name]),'Resource length change')
        r=records[name]
        for offset in range(0,len(data),2048):
            lba=r['lba']+offset//2048
            need(lba not in payloads,'Overlapping ISO extents')
            payloads[lba]=data[offset:offset+2048]
    total=0;changed=[]
    with parent.open('rb') as source,target.open('rb') as output:
        while before:=source.read(2352):
            after=output.read(2352)
            need(len(before)==len(after)==2352,'Truncated disc')
            if before!=after:
                need(total in payloads,'Unexpected changed raw sector')
                payload=payloads[total]
                want=rebuild_checks(before[:24]+payload+before[24+len(payload):])
                need(after==want,'Unexpected sector header/payload/checksum/padding')
                validate_checks(after);changed.append(total)
            total+=1
        need(not output.read(1),'Extra target bytes')
    cue=target.with_suffix('.cue').read_bytes()
    need(cue==parent.with_suffix('.cue').read_bytes() and f'FILE "{stem}.bin" BINARY'.encode() in cue,'CUE structure/link changed')
    result={'passed':True,'project':mode,'bin':str(target.relative_to(ROOT)),'bin_sha256':args.sha256,
            'parent_sha256':expected,'EXE_sha256':sha(new['SLUS_005.61']),'EXE_exact':True,
            'all_sectors_compared':total,'changed_sector_count':len(changed),'changed_lbas':changed,
            'only_prepared_graphics_ARCs_changed':True,'EDC_ECC_exact':True,'ISO_CUE_layout_exact':True,
            'all_other_raw_sectors_exact':True,'original_input_or_state_written':False,
            'audited_proposals':evidence,'runtime_checked_by_this_audit':False,
            'protected_scope':'원본 음성·주인공 무음·X6 효과·낙봉파·타이틀·텍스트·HUD·UI·다른 그림 및 EXE 전체 보존'}
    write(OUT/(mode+'_disc_independent.json'),result)
    print(json.dumps({'passed':True,'mode':mode,'changed_sectors':len(changed),'sectors':total}),flush=True)

if __name__=='__main__':main()
