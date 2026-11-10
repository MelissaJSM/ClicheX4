"""Freeze a checked sprite resource as an integration proposal, never a whole BIN."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import D,BASES,load,sha,write

def main(project,folder,destination):
    folder=Path(folder).resolve();destination=Path(destination).resolve()
    if not folder.is_relative_to(D.resolve()) or not destination.is_relative_to(D.resolve()):raise ValueError('Isolated sprite workspace required')
    if destination.exists():raise ValueError('New output directory required')
    assets,records=load(project);old=assets['PL02_U.ARC'];new=(folder/'PL02_U.ARC').read_bytes();checks=json.loads((folder/'packing.json').read_text('utf8'))
    if len(old)!=len(new) or sha(old)!=checks['before'] or sha(new)!=checks['after']:raise ValueError('Packing hashes differ')
    destination.mkdir(parents=True);path=destination/'PL02_U.ARC';path.write_bytes(new)
    write(destination/'packing.json',checks)
    proposal={'project':project,'baseline':BASES[project][0],'baseline_sha256':BASES[project][1],
      'files':{'PL02_U.ARC':{'before':sha(old),'after':sha(new),'size':len(new),'path':path.relative_to(ROOT).as_posix(),'record':records['PL02_U.ARC']}},
      'checks':checks,'runtime_verified':False}
    write(destination/'proposal.json',proposal)
    print(json.dumps({'proposal':str(destination/'proposal.json'),'frames':len(checks['frames']),'failures':checks['failures']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project');p.add_argument('folder');p.add_argument('destination');a=p.parse_args();main(a.project,a.folder,a.destination)
