"""Independent regressions for the cropped HUD and the two departure assets."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_hud_departure import load,D
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc,sha256
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static

def verify(candidate,repro):
    records,original,current=load();recipe=json.loads((candidate/'recipe.json').read_text());checks={'reproducible_archives':0,'player_compositions':0,'hud_alpha_masks':0,'restored_hud_pixels_per_frame':[],'hq_protected_frames':0,'departure_pixel_roundtrips':0,'gpu_page_edges':0};edited={}
    for item in recipe['files']:
        name=item['file'];data=(candidate/name).read_bytes();edited[name]=data
        if data!=(repro/name).read_bytes() or sha256(data)!=item['sha256'] or len(data)!=len(current[name]):raise AssertionError('Reproducibility/hash/size failed')
        checks['reproducible_archives']+=1;allowed={3,0x10206} if name.startswith('PL') else {10,0x10102}
        for e in psx_arc(current[name]):
            kind=int(e['type'],16)
            if kind not in allowed and entry(data,kind)!=entry(current[name],kind):raise AssertionError('Non-target entry changed')
    for name in ('PL00_U.ARC','PL02_U.ARC'):
        a,b=entry(current[name],3),entry(edited[name],3);ga,gb=entry(current[name],0x10206),entry(edited[name],0x10206)
        for bank in range(struct.unpack_from('<I',a)[0]//4):
            for n in range(aliased_composition(a,bank,0)['bank_frame_count']):
                ca,cb=aliased_composition(a,bank,n),aliased_composition(b,bank,n);target=bank==1 and n in range(69,78)
                if bank in (0,5,6,7,8):
                    if ca!=cb:raise AssertionError('Gameplay/armor composition changed')
                else:
                    try:before=compose_static(ga,local_composition(ca))[:3];after=compose_static(gb,local_composition(cb))[:3]
                    except ValueError:
                        if ca!=cb:raise AssertionError('Unknown static composition changed')
                        continue
                    if not target and (before!=after or [q['clut'] for q in ca['parts']]!=[q['clut'] for q in cb['parts']]):raise AssertionError('Protected static graphic changed')
                    if target:
                        old=compose_static(entry(original[name],0x10206),local_composition(aliased_composition(entry(original[name],3),bank,n)))[:3]
                        if before[1:]!=after[1:] or old[1:]!=after[1:]:raise AssertionError('HUD size/anchor changed')
                        oa=np.frombuffer(old[0],np.uint8).reshape(old[1][1],old[1][0]);na=np.frombuffer(after[0],np.uint8).reshape(oa.shape);pa=np.frombuffer(before[0],np.uint8).reshape(oa.shape);ys,xs=np.indices(oa.shape);bb=old[2];allow=(ys+bb[1]>=26)&(ys+bb[1]<=38)&(xs+bb[0]>=-19)&(xs+bb[0]<=3)
                        if np.any((oa>0)!=(na>0)) or np.any((oa!=na)&~allow):raise AssertionError('HUD frame or count bezel damaged')
                        checks['hud_alpha_masks']+=1;checks['restored_hud_pixels_per_frame'].append(int(np.count_nonzero((na>0)&(pa==0))))
                        for q in cb['parts']:
                            tile=q['page']*256+q['tile'];px=np.frombuffer(tile_pixels(gb,tile),np.uint8).reshape(16,16)
                            if q['flip_y'] and (tile//16)%16==0 and px[0].any():raise AssertionError('HUD flipped UV page boundary')
                            checks['gpu_page_edges']+=1
                checks['player_compositions']+=1
    for suffix,hi,n,label in [('X',75776,9,'shibuki'),('Z',81920,13,'riko')]:
        name=f'ST0D_0{suffix}.ARC';a,b=entry(current[name],10),entry(edited[name],10);ga,gb=entry(current[name],0x10102),entry(edited[name],0x10102);lo=63488
        if ga[:lo]!=gb[:lo] or ga[hi:]!=gb[hi:]:raise AssertionError('Other HQ atlas modified')
        for bank in range(struct.unpack_from('<I',a)[0]//4):
            for f in range(aliased_composition(a,bank,0)['bank_frame_count']):
                ca,cb=aliased_composition(a,bank,f),aliased_composition(b,bank,f)
                if bank==2 and f==n:continue
                if ca!=cb:raise AssertionError('Protected HQ frame record modified')
                if bank==2:
                    if compose_static(ga[lo:hi],local_composition(ca))[:3]!=compose_static(gb[lo:hi],local_composition(cb))[:3]:raise AssertionError('HQ idle/talk pixels changed')
                    checks['hq_protected_frames']+=1
        actual=compose_static(gb[lo:hi],local_composition(aliased_composition(b,2,n)))[:3];im=Image.open(candidate/f'{label}_departure.png')
        if actual[:2]!=(im.tobytes(),im.size):raise AssertionError('Departure pixels do not roundtrip')
        arr=np.frombuffer(actual[0],np.uint8).reshape(actual[1][1],actual[1][0]);yy,xx=np.nonzero(arr);last=int(yy.max());_,fx=np.nonzero(arr[last-3:last+1]);foot=actual[2][0]+(int(fx.min())+int(fx.max()))/2;floor=actual[2][1]+last+1;expected=recipe['checks'][name]
        if abs(foot-expected['original_front_foot_center'])>.5 or floor!=expected['original_front_foot_y']:raise AssertionError('Departure foot registration mismatch')
        checks['departure_pixel_roundtrips']+=1
    checks['exe_and_animation_changes']=False;checks['passed']=True
    (candidate/'regression.json').write_text(json.dumps(checks,indent=2),encoding='utf8');print(json.dumps(checks))
    return checks

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);a=p.parse_args();verify(a.candidate,a.repro)
