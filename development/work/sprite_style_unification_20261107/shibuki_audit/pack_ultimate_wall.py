"""새 얼티밋 벽12참조를 이동/저체력 누적본에 무손실 패킹한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,SOURCE_SHA
import pack_ultimate_lowhp as core
from scripts.export_x_consistency import Archive,page
P=H/'prepared_ultimate_lowhp01/PL02_U.ARC'
PSHA='3dd0d9a2cafd8e4d4355ef131c69c39f794698f6752524b39cf488f5b3bc737b'
BASELINE='98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e'
O=H/'prepared_ultimate_wall01';SELECTED=set(range(55,67))
LOCK=H/'ultimate_wall_target_lock01.json'
def target_path(form,n):
    if n%2==0:return H/'ultimate_wall_shots_final02'/form/f'{n:03}_indices.png'
    return H/('ultimate_wall_contacts_probe01' if n<61 else 'ultimate_wall_page02_contacts01')/form/f'{n:03}_indices.png'
def load_targets():
    lock=json.loads(LOCK.read_text('utf8'));values={};sources=[]
    need(set(lock['targets'])=={f'{f}/{n}'for f in ('before','after')for n in SELECTED},'Wrong target lock scope')
    for f in ('before','after'):
        values[f]={}
        for n in sorted(SELECTED):
            p=target_path(f,n);raw=p.read_bytes();rec=lock['targets'][f'{f}/{n}']
            need(sha(raw)==rec['sha256'],'Frozen target image changed')
            v=np.array(Image.open(p));need(v.shape==(384,384)and v.dtype==np.uint8 and int(v.max())<16,'Wrong target image')
            values[f][n]=v;sources.append({'form':f,'ref':n,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(raw)})
    return values['before'],values['after'],sources
def build(data,full,base):
    need(sha(data)==PSHA,'Wrong frozen wall parent');need(set(full)==set(base)==SELECTED,'Wrong wall scope')
    for n in SELECTED:need(not((base[n]>0)&(full[n]==0)).any(),'After alpha outside jacket')
    # Reuse the exact-layer packer with this process-local scope and guard.
    # No repository code or frozen prior output is modified.
    core.PSHA=PSHA;core.SELECTED=SELECTED
    return core.pack(data,full,base)
def main():
    need(not O.exists(),'Fresh wall output required');data=P.read_bytes();full,base,sources=load_targets()
    result,proof=build(data,full,base)
    again,second=build(data,full,base);need(result==again,'Repeat build differs')
    rejected=[]
    for name,d,f,b in [('wrong_parent',data[:-1]+bytes([data[-1]^1]),full,base),('missing_form_ref',data,{n:v for n,v in full.items()if n!=55},base)]:
        try:build(d,f,b)
        except ValueError:rejected.append(name)
        else:raise ValueError('Bad input accepted: '+name)
    leak={n:v.copy()for n,v in base.items()};leak[55][100,100]=13
    try:build(data,full,leak)
    except ValueError:rejected.append('new_uncovered_after_pixel')
    else:raise ValueError('Leaking costume accepted')
    O.mkdir();(O/'PL02_U.ARC').write_bytes(result);actual=Archive(result);old=Archive(data)
    barrel_info=json.loads((H/'ultimate_wall_inputs01/manifest.json').read_text('utf8'))['refs'];barrel_checks=[]
    for form,mask in [('before',15),('after',0)]:
        D=O/form;D.mkdir()
        for n in sorted(SELECTED):
            im=actual.composite(n,mask)[0];im.save(D/f'{n:03}.png')
            if n%2==0:
                r=next(x for x in barrel_info if x['body_ref']==n-1);x0,y0,x1,y1=r['barrel_rect_world'];box=(x0+160,y0+160,x1+160,y1+160)
                need(im.crop(box).tobytes()==old.composite(n,mask)[0].crop(box).tobytes(),'Readback barrel differs')
                barrel_checks.append({'ref':n,'form':form,'original_muzzle':r['original_muzzle_world'],'barrel_rgba_exact':True})
        for k in range(2):
            ns=sorted(SELECTED)[k*6:(k+1)*6]
            page([(f'{n} actual ARC',actual.composite(n,mask)[0])for n in ns],actual.composite(0,mask)[0],D/f'actual_{k:02}.png',cols=3,scale=5)
    proof.update({'source_art':sources,'target_lock_sha256':sha(LOCK.read_bytes()),'repeated_build_sha256':sha(again),'repeat_identical':True,'bad_inputs_rejected':rejected,'barrel_checks':barrel_checks,'new_wall_refs':sorted(SELECTED),'cumulative_refs':list(range(3,33))+list(range(55,67))+list(range(120,126)),'all_prior_run_lowhp_72_displays_preserved':True,'art_simplified':False,'old_head_body_overwrite':False,'runtime_verified':False,'visual_review_pending':True})
    write(O/'verification.json',proof)
    write(O/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL02_U.ARC':{'path':(O/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':BASELINE,'after':sha(result)}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PSHA},'supersedes':'prepared_ultimate_lowhp01; 누적 이동3..32, 벽55..66, 저체력120..125','source_art':sources,'runtime_verified':False})
    print({k:proof[k]for k in ('after_arc_sha256','parts_slack','raw_checked','non_target_composites_preserved','exact_target_composites','repeat_identical')})
if __name__=='__main__':main()
