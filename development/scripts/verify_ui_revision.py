"""Read-only regression checks against the accepted UI parent and original assets."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_ui_revision import load,D
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from scripts.project import digest
from scripts.prepare_ui_revision import rename_gangzi,DEATH_LUT,ULTIMATE_DEATH_LUT
from scripts.prepare_gangzi_capsule import native_body
from scripts.build_ui_revision import patch_death_exe,DEATH_OFFSET
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

def run(candidate,repro):
    records,original,parent=load();recipe=json.loads((candidate/'recipe.json').read_text());items={i['file']:i for i in recipe['files']};new={**parent,**{n:(candidate/n).read_bytes() for n in items}};result={}
    for n in items:
        if new[n]!=(repro/n).read_bytes():raise AssertionError('Repeat preparation differs')
        if len(new[n])!=len(parent[n]):raise AssertionError('Archive resized')
    result['reproducible_archives']=len(items)
    checked=0
    for name in ('PL00_U.ARC','PL02_U.ARC','PL01_U.ARC'):
        allowed={3,0x11} if name=='PL01_U.ARC' else {3,0x11,0x10007,0x10206,0x15}
        for e in psx_arc(parent[name]):
            if int(e['type'],16) not in allowed and entry(parent[name],int(e['type'],16))!=entry(new[name],int(e['type'],16)):raise AssertionError('Unrequested player entry changed')
        a,b=entry(parent[name],3),entry(new[name],3);ga,gb=entry(parent[name],0x10206),entry(new[name],0x10206)
        for bank in range(struct.unpack_from('<I',a)[0]//4):
            for frame in range(aliased_composition(a,bank,0)['bank_frame_count']):
                ca,cb=aliased_composition(a,bank,frame),aliased_composition(b,bank,frame)
                target=bank==1 and (105<=frame<=113 or (name!='PL01_U.ARC' and 69<=frame<=77))
                if bank in (0,5,6,7,8):
                    if ca!=cb:raise AssertionError('Gameplay composition changed')
                    checked+=1;continue
                try:pa=compose_static(ga,local_composition(ca))[:3];pb=compose_static(gb,local_composition(cb))[:3]
                except ValueError:
                    if ca!=cb:raise AssertionError('Unknown composition changed')
                    continue
                if not target and (pa!=pb or [q['clut'] for q in ca['parts']]!=[q['clut'] for q in cb['parts']]):raise AssertionError('Protected static frame changed')
                if target and 105<=frame<=113:
                    if name=='PL01_U.ARC':
                        if pa!=pb or any(0x7802+q['clut']!=0x7800+r['clut'] for q,r in zip(ca['parts'],cb['parts'])):raise AssertionError('Riko death colors/geometry changed')
                    else:
                        px,sz,bb,_=compose_static(entry(original[name],0x10206),local_composition(aliased_composition(entry(original[name],3),1,frame)));lut=DEATH_LUT if name=='PL00_U.ARC' else ULTIMATE_DEATH_LUT
                        if pb!=(bytes(lut[v] for v in px),sz,bb) or any(q['clut'] for q in cb['parts']):raise AssertionError('Death geometry/color mapping mismatch')
                checked+=1
    result['player_compositions_checked']=checked;result['riko_death_final_clut']='0x7803 (unchanged)'
    for name in ('PL00_U.ARC','PL02_U.ARC'):
        text,changes=rename_gangzi(entry(parent[name],0x15))
        if text!=entry(new[name],0x15) or rename_gangzi(text)[1] or len(changes)!=58:raise AssertionError('GangZi name replacement mismatch')
    result['gangzi_name_replacements']=116
    name='ST0D_0X.ARC';ga,gb=entry(parent[name],0x10102),entry(new[name],0x10102);a,b=entry(parent[name],10),entry(new[name],10)
    if ga[:63488]!=gb[:63488] or ga[75776:]!=gb[75776:]:raise AssertionError('Other HQ texture changed')
    frames=[]
    for n in range(12):
        pa=compose_static(ga[63488:75776],local_composition(aliased_composition(a,2,n)))[:3];pb=compose_static(gb[63488:75776],local_composition(aliased_composition(b,2,n)))[:3]
        if n not in (6,7,8) and pa[:2]!=pb[:2]:raise AssertionError('Preserved HQ pose pixels changed')
        if n in (0,1,2,9,11) and pa!=pb:raise AssertionError('Preserved HQ anchor changed')
        px,sz,bb=pb;arr=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);yy,xx=np.nonzero(arr);feet_y=int(yy.max())+bb[1]+1;fy,fx=np.nonzero(arr[-9:]);center=bb[0]+(int(fx.min())+int(fx.max()))/2
        frames.append({'frame':n,'feet_y':feet_y,'sole_center_x':center,'bounds':bb})
    for f in frames:
        if f['frame']==9:continue
        if abs(f['feet_y']-frames[0]['feet_y'])>1 or abs(f['sole_center_x']-frames[0]['sole_center_x'])>0.5:raise AssertionError('HQ grounded registration inconsistent')
    result['hq_registration']=frames
    for info in recipe['checks']['gangzi']['copies']:
        name=info['file'];bank=info['bank'];lo=info['texture_offset'];ga,gb=entry(parent[name],0x10102),entry(new[name],0x10102);a,b=entry(parent[name],10),entry(new[name],10)
        if ga[:lo]!=gb[:lo] or ga[lo+10240:]!=gb[lo+10240:]:raise AssertionError('Other stage sprite changed')
        for n in range(58):
            ca,cb=aliased_composition(a,bank,n),aliased_composition(b,bank,n)
            if n not in (6,7,21):
                if compose_static(ga[lo:lo+10240],local_composition(ca))[:3]!=compose_static(gb[lo:lo+10240],local_composition(cb))[:3]:raise AssertionError('Capsule animation changed')
            else:
                if ca['parts'][:26]!=cb['parts'][:26]:raise AssertionError('Machine parts changed')
                if n==6:
                    px,sz,bb,_=compose_static(gb[lo:lo+10240],local_composition({**cb,'parts':cb['parts'][26:]}));native=native_body();x,y=bb[0]+16,bb[1]+58
                    if px!=native[y:y+sz[1],x:x+sz[0]].tobytes():raise AssertionError('GangZi capsule pixels clipped or overwritten')
    result['capsule_protected_frames']=4*55;result['capsule_body_roundtrips']=4
    rejected=0
    exe=(ROOT/'work/ver_buki_riko/shibuki_ui_v1/US_EXE.bin').read_bytes();patched=patch_death_exe(exe)
    for bad in (exe[:-1],patched,exe[:8]+b'bad'+exe[11:]):
        try:patch_death_exe(bad)
        except ValueError:rejected+=1
        else:raise AssertionError('Wrong executable accepted')
    result['invalid_executables_rejected']=rejected;result['exe_changed_bytes']=[i for i,(a,b) in enumerate(zip(exe,patched)) if a!=b]
    if result['exe_changed_bytes']!=[DEATH_OFFSET]:raise AssertionError('Unexpected EXE byte')
    for rec in json.loads((D/'user_backup/manifest.json').read_text()):
        if digest(ROOT/rec['path'])!=rec['sha256']:raise AssertionError('User savedata changed')
    result['user_save_hashes_preserved']=4;result['passed']=True
    (candidate/'regression.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);a=p.parse_args();run(a.candidate,a.repro)
