"""강제mask15용 새217/218몸·219실루엣·220가림을20층 목표로 고정."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
P=H/'prepared_nova_ultimate01/PL02_U.ARC';PARENT='687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f';PBS=(0,5,6,7,8);REFS=(217,218,219,220);GROUPS=((217,),(218,),(219,),(220,));DY={n:0 for n in REFS};TD=H/'nova_strike_ultimate_targets01'
def main():
    need(not TD.exists(),'새목표');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모 변경');d=H/'nova_strike_ultimate_effects02';m=json.loads((d/'manifest.json').read_text('utf8'));need(sha((d/'manifest.json').read_bytes())=='29cd9cf2880db0cc7ec9be093989dddc1e1d3fa8b4a661b96206940ea578fc7f','효과근거변경')
    for name,h in m['source_files'].items():need(sha((ROOT/name).read_bytes())==h,'효과출처 변경')
    body=np.array(Image.open(d/'body_217_indices.png'));zero=np.zeros_like(body);targets={};rgba=0;TD.mkdir()
    for n in REFS:
        fx=np.array(Image.open(d/f'effect_{n}_indices.png'))if n!=217 else zero
        layers={0:zero if n==219 else body,5:fx,6:zero,7:zero,8:zero};targets[n]=layers
        for b,z in layers.items():Image.fromarray(z).save(TD/f'{n:03}_bank{b}_indices.png')
        compose(a,layers,15).save(TD/f'actual_{n:03}.png')
        for arm in(1,2):
            for mask in range(16):
                want=a.rgba(layers[0]);want.alpha_composite(a.rgba(fx,16)if mask&1 else a.rgba(zero));need(compose(a,layers,mask,arm).tobytes()==want.tobytes(),'0몸/5효과 소유');rgba+=1
    need(np.array_equal(targets[218][5],a.layer(218,5)[0]),'현재3점 전체보존')
    for i,ns in enumerate(((217,218),(219,220))):page([(f'{n} 현재',a.composite(n,15)[0])if k==0 else(f'{n} 새몸/새가림',compose(a,targets[n],15))for n in ns for k in(0,1)],a.composite(0,0)[0],TD/f'comparison_{i:02}.png',cols=2,scale=4 if i==0 else 3)
    files=[P,Path(__file__),H/'prepare_nova_strike_ultimate.py',H/'register_nova_strike_ultimate.py',H/'prepare_nova_strike_ultimate_effects02.py']
    for name in('nova_strike_ultimate_inputs01','nova_strike_ultimate_native01','nova_strike_ultimate_effects02'):files.extend(p for p in(H/name).rglob('*')if p.is_file())
    files.extend(ROOT/name for name in m['source_files']);files.extend(p for p in TD.iterdir()if p.is_file())
    write(TD/'manifest.json',{'parent_sha256':PARENT,'refs':list(REFS),'targets':{str(n):{str(b):sha(z.tobytes())for b,z in ll.items()}for n,ll in targets.items()},'source_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in sorted(set(files))},'actual_engine_mask':15,'actual_body_costume':'accepted Ultimate after','direct_partial_RGBA':rgba,'new_unique_bodies':1,'new_body_pixels':int((body>0).sum()),'body_origin_unchanged':True,'body_global_scaling':False,'aliases':{'217_218_220_body0_exact':True,'219_body0_empty':True},'effects218_current3_exact':True,'effect220_changed_cells':93,'effect219_new_silhouette':True,'source_reading':m,'scope':'한새몸776픽셀과새실루엣/원효과가림을4참조20층으로 파생.원217옛재킷에서after수용의상으로통일하는신규정책.실제engine는217~230mask15강제이므로diagnostic mask0을게임상태로오인하지않는다.','native_packed':False,'runtime_verified':False});print(json.dumps({'manifest':sha((TD/'manifest.json').read_bytes()),'source_files':len(set(files)),'partial':rgba}))
if __name__=='__main__':main()
