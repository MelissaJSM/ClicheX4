"""검토용 기본/포스98·99 후보. 독립/실기 통과로 확대하지 않는다."""
from pathlib import Path
import sys,json,subprocess
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from scripts.discover_inputs import psx_arc
from native_pose_pack import need,sha,write
from pack_cyclone_base_probe import validate_inputs,LOCK_SHA
def main():
    out=H/'prepared_double_cyclone_base01';need(not out.exists(),'Fresh output required')
    parent=(H/'prepared_air01/PL00_U.ARC').read_bytes();p=H/'double_cyclone_base_pack02';candidate=(p/'PL00_U.ARC').read_bytes();expected='61495a2aaf002efc32492a4e12c3724a77c82b3f42464538ae1e2cc855da74c0';need(sha(candidate)==expected,'Candidate changed');d=H/'double_cyclone_layers_probe02';validate_inputs(parent,d)
    need(candidate==(H/'double_cyclone_base_reproduction02/PL00_U.ARC').read_bytes(),'Reproduction changed');need(len(parent)==len(candidate),'ARC length changed');allowed=np.zeros(len(parent),bool);entries=[]
    for typ in(2,3):
        e=next(q for q in psx_arc(parent)if q['type']==hex(typ));allowed[e['offset']:e['offset']+e['size']]=True;entries.append(e)
    delta=np.frombuffer(parent,np.uint8)!=np.frombuffer(candidate,np.uint8);need(not np.any(delta&~allowed),'Outside graphics/parts changed')
    rejects=[];bad=bytearray(parent);bad[-1]^=1
    try:validate_inputs(bytes(bad),d)
    except ValueError as e:rejects.append({'case':'wrong_parent','reason':str(e)})
    else:raise ValueError('Bad parent accepted')
    for label,path in [('wrong_lock',d/'LOCK.json'),('changed_native',d/'098_bank0_indices.png'),('changed_generation',H/'double_cyclone_inputs02/page01/generated.png')]:
        def read(p):
            b=p.read_bytes();return bytes([b[0]^1])+b[1:]if p==path else b
        try:validate_inputs(parent,d,read)
        except ValueError as e:rejects.append({'case':label,'reason':str(e)})
        else:raise ValueError('Changed input accepted')
    for label,path in[('output_escape','../outside_not_written'),('existing_output','double_cyclone_base_pack02')]:
        q=subprocess.run([sys.executable,'-B',str(H/'pack_cyclone_base_probe.py'),'--layers','double_cyclone_layers_probe02','--out',path],capture_output=True,text=True,cwd=ROOT);need(q.returncode!=0 and'ValueError'in q.stderr,'Invalid output accepted');rejects.append({'case':label,'reason':q.stderr.splitlines()[-1]})
    contact=json.loads((H/'double_cyclone_contact02/report.json').read_text('utf8'));need(contact['passed']and contact['candidate_sha256']==expected,'Wrong effect proof')
    # Every original initial-effect contact remains overlap or immediately adjacent.
    comparison=[]
    for charged in(False,True):
        for mask in(0,15):
            for ref in(98,99):
                old=next(r for r in contact['rows']if(r['charged'],r['mask'],r['ref'],r['version'])==(charged,mask,ref,'old'));new=next(r for r in contact['rows']if(r['charged'],r['mask'],r['ref'],r['version'])==(charged,mask,ref,'new'))
                for side in('left','right'):
                    a=next(x for x in old['contacts']if x['initial']and x['side']==side);b=next(x for x in new['contacts']if x['initial']and x['side']==side);need(b['nearest_hand_to_effect_distance']<=max(1,a['nearest_hand_to_effect_distance']),'Effect contact became farther');comparison.append({'charged':charged,'mask':mask,'ref':ref,'side':side,'before':a,'after':b})
    oldprop=json.loads((H/'prepared_air01/proposal.json').read_text('utf8'));prop={**oldprop};prop.update({'replaces':str((H/'prepared_air01/proposal.json').relative_to(ROOT)).replace('\\','/'),'selected_visual_refs':[98,99],'source_art_manifest':str((d/'LOCK.json').relative_to(ROOT)).replace('\\','/'),'source_art_manifest_sha256':LOCK_SHA,'parent_arc_sha256':sha(parent),'scope':'기본/포스 더블 사이클론98·99의 새 머리/옷 세부묘사. 공중22가 포함된 기존70참조 누적본에2참조 추가. 게임 시간표·효과·총구 수정 없음.','static_review_passed':True,'native_cpu_pending':True,'independent_review_pending':True,'actual_gameplay_pending':True})
    prop['files']={**oldprop['files'],'PL00_U.ARC':{**oldprop['files']['PL00_U.ARC'],'path':str((out/'PL00_U.ARC').relative_to(ROOT)).replace('\\','/'),'after':expected}}
    out.mkdir();(out/'PL00_U.ARC').write_bytes(candidate);write(out/'proposal.json',prop)
    proof={'passed':True,'candidate_sha256':expected,'parent_sha256':sha(parent),'reproduction_exact':True,'changed_bytes':int(delta.sum()),'outside_entries_exact_bytes':int((~allowed).sum()),'changed_entries':entries,'rejected':rejects,'effect_contact_preserved':comparison,'effect_mips_initializers':8,'effect_proof_sha256':sha((H/'double_cyclone_contact02/report.json').read_bytes()),'producer_verification':json.loads((p/'report.json').read_text('utf8')),'runtime_verified':False,'native_full_draw_pending':True,'independent_pending':True};write(out/'verification.json',proof)
    write(out/'INPUT_FROZEN.json',{'candidate_and_source_frozen':True,'files':{s:sha((out/s).read_bytes())for s in('PL00_U.ARC','proposal.json','verification.json')},'lock_sha256':LOCK_SHA,'producer_scripts':{s:sha((H/s).read_bytes())for s in('prepare_cyclone_layers_probe.py','align_cyclone_right_hand.py','pack_cyclone_base_probe.py','audit_cyclone_contact.py','finalize_cyclone_base.py')},'user_accepted':False,'actual_gameplay_verified':False})
    print(json.dumps({'path':str(out),'sha':expected,'rejections':len(rejects),'contact_cases':len(comparison)},ensure_ascii=False))
if __name__=='__main__':main()
