"""Compare non-target native compositions after all Korean components merge."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D
from scripts.prepare_riko_ui import entry
from scripts.prepare_korean_ui import MENU
from scripts.discover_inputs import sha256
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

def main(candidate):
    report=json.loads((candidate/'proposal.json').read_text('utf-8'));checks=[]
    def load(name):
        path=D/'inventory'/name
        if not path.exists():path=D/'ui_inventory'/name
        a,z=path.read_bytes(),(candidate/name).read_bytes();meta=report['files'][name]
        if sha256(a)!=meta['before'] or sha256(z)!=meta['after']:raise ValueError('Resource hash mismatch')
        return a,z
    def compare(label,oldg,oldp,newg,newp,bank,changed):
        count=aliased_composition(oldp,bank,0)['bank_frame_count'];checked=0
        if aliased_composition(newp,bank,0)['bank_frame_count']!=count:raise ValueError('Frame count changed')
        for n in range(count):
            if n in changed:continue
            a=aliased_composition(oldp,bank,n);z=aliased_composition(newp,bank,n)
            pa=compose_static(oldg,local_composition(a))[:3];pz=compose_static(newg,local_composition(z))[:3]
            if pa!=pz:raise ValueError(f'Protected surface changed {label}/{bank}/{n}')
            if [p['clut'] for p in a['parts']]!=[p['clut'] for p in z['parts']]:raise ValueError('Protected CLUT changed')
            checked+=1
        checks.append({'resource':label,'bank':bank,'protected_frames':checked})
    a,z=load('ST0E_U0.ARC');compare('title',entry(a,0x10002),struct.pack('<I',4)+entry(a,0x12),entry(z,0x10002),struct.pack('<I',4)+entry(z,0x12),0,{2,4,5,6,29,30})
    for name,target_bank,changed in [('ST0E_U1.ARC',1,{2,3,4,5,7}),('ST0D_0X.ARC',1,set(range(10))),('ST0D_0Z.ARC',1,set(range(10))),('ST0F_UX.ARC',0,set(range(21))),('ST0F_UZ.ARC',0,set(range(21)))]:
        a,z=load(name);offsets=struct.unpack('<'+'I'*(len(entry(a,12))//4),entry(a,12));oldg,newg=entry(a,0x10102),entry(z,0x10102)
        for b,start in enumerate(offsets):
            end=min((v for v in offsets if v>start),default=len(oldg))
            compare(name,oldg[start:end],entry(a,10),newg[start:end],entry(z,10),b,changed if b==target_bank else set())
    oldload,newload=load('LOAD_U.ARC');oldmenu,newmenu=load('MOJIPAT.ARC');compare('load sprites',entry(oldload,0x10008),oldmenu,entry(newload,0x10008),newmenu,2,set(MENU))
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        a,z=load(name);changed=set(range(8 if name=='PL01_U.ARC' else 10))|{11,12}
        compare(name+' pause',entry(a,0x10007)[96*128:],struct.pack('<I',4)+entry(a,0x12),entry(z,0x10007)[96*128:],struct.pack('<I',4)+entry(z,0x12),0,changed)
    result={'protected_compositions':sum(c['protected_frames'] for c in checks),'checks':checks,'native_indices_bounds_and_cluts_preserved':True,'runtime_verified':False}
    (candidate/'surface_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();main(a.candidate)
