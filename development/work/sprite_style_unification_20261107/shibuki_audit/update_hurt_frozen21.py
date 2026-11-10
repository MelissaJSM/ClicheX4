"""20의 실제 복원 픽셀은 그대로 두고 Ultimate 피격 동결 상태만 갱신한다."""
from pathlib import Path
from collections import Counter
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    o=H/'fullform_ledger21.json';need(not o.exists(),'Fresh ledger')
    d=H/'prepared_ultimate_hurt02';f=d/'FROZEN.json';fr=json.loads(f.read_text('utf8'))
    for n,h in fr['files'].items():need(sha((d/n).read_bytes())==h,'Frozen asset changed')
    j=json.loads((H/'fullform_ledger20.json').read_text('utf8'));u=json.loads((H/'unique_art_keys20.json').read_text('utf8'))
    for name,r in j['current_candidates'].items():need(sha((ROOT/r['path']).read_bytes())==r['sha256'],'Counts source changed')
    for obj in(j,u):
        c=obj['current_candidates']if'current_candidates'in obj else obj['candidates'];c['PL02_U.ARC'].update(frozen=True,frozen_record=ev(f),final_verification=ev(d/'final_verification.json'),integrated=False)
    for r in j['references']:
        if r['status']=='new_art_prepared_pending_final_review':r.update(status='new_art_frozen_for_integration',frozen_evidence=ev(f),decision='Ultimate피격13 새8의상몸체+실제부모효과65층 동결.독립/MIPS/root14판/원표710canvas 통과.실기·사용자최종수용은별도.',candidate_progress={'frozen':True,'candidate':j['current_candidates']['PL02_U.ARC'],'whole_project_complete':False})
    counts=Counter(r['status']for r in j['references']);j['counts'].update(status_counts=dict(counts),new_frozen_form_images=counts['new_art_frozen_for_integration'],new_prepared_form_images=0)
    for g in j['groups']:g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
    j['hurt13_new_scope']['ultimate']=j['current_candidates']['PL02_U.ARC'];j['new_root_review_evidence'].append(ev(H.parent/'root_review_checkpoint109.json'));write(o,j)
    for k in u['keys']:
        k['status_by_ref']={n:('new_art_frozen_for_integration'if s=='new_art_prepared_pending_final_review'else s)for n,s in k['status_by_ref'].items()};ss=set(k['status_by_ref'].values());k['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status'
    u['source_ledger']=ev(o);u['counts']['reference_status_counts']=dict(counts);u['counts']['unique_key_status_counts']=dict(Counter(k['status']for k in u['keys']))
    for form,f in u['forms'].items():f['reference_status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==form));f['unique_key_status_counts']=dict(Counter(k['status']for k in u['keys']if k['form']==form))
    pending=[]
    for old in u['pending_motion_groups']:
        ks=[k for k in u['keys']if k['form']==old['form']and old['group']in k['groups']and'art_rework_group_pending'in k['status_by_ref'].values()]
        if ks:pending.append({**old,'unique_keys':len(ks),'refs':sorted(set(n for k in ks for n in k['refs']))})
    u['pending_motion_groups']=pending;u['pixel_inventory_reused_from20_exact_asset_hashes']=True;write(H/'unique_art_keys21.json',u);print(json.dumps(u['counts']['unique_key_status_counts']))
if __name__=='__main__':main()
