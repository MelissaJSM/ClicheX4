"""Ultimate 대시 동결 증거와 새 기본/포스 이동 작업을 분리해 기록한다."""
from pathlib import Path
from collections import Counter
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    out=H/'fullform_ledger13.json';need(not out.exists(),'Fresh output only')
    j=json.loads((H/'fullform_ledger12.json').read_text('utf8'));u=json.loads((H/'unique_art_keys12.json').read_text('utf8'))
    freeze=H/'prepared_ultimate_dash01/FROZEN.json';need(sha(freeze.read_bytes())=='d8e13ddb5d8b726cdd36187b0086e9d3d43b557a5579d9723f1d4eaec6046bf4','Frozen evidence changed')
    for r in j['references']:
        if r['status']=='new_art_prepared_pending_independent' and r['form'].startswith('ultimate') and r['ref'] in list(range(67,85))+[93,94]:
            r.update(status='new_art_frozen_for_integration',decision='새 대시 양의상40표시 동결. 제작/독립 reader·원 MIPS/GPU·루트8재추출판 실제 열람 통과. 원본 속도선9레코드54px와 원총열 보존. 새 Ultimate 대시 실기 및 사용자 최종 수용은 별도 미확인.',frozen_evidence=ev(freeze))
    for k in u['keys']:
        k['status_by_ref']={n:next(r['status'] for r in j['references'] if r['form']==k['form'] and r['ref']==int(n)) for n in k['status_by_ref']}
        ss=set(k['status_by_ref'].values());k['status']=next(iter(ss)) if len(ss)==1 else 'mixed_review_status'
    counts=Counter(r['status'] for r in j['references']);j['counts']['status_counts']=dict(counts);j['counts']['new_frozen_form_images']=counts['new_art_frozen_for_integration'];j['counts']['new_prepared_form_images']=counts['new_art_prepared_pending_independent']
    for g in j['groups']:g['status_counts']=dict(Counter(r['status'] for r in j['references'] if r['form']==g['form'] and r['ref'] in g['refs']))
    j['current_candidates']['PL02_U.ARC'].update(frozen=ev(freeze),independent_and_native_pending=False,runtime_verified=False)
    j['unpacked_art_in_progress']={'forms':['base','fourth'],'refs':[3,11,19],'source':ev(H/'base_run_followup02/generated.png'),'native':ev(H/'base_run_native01/report.json'),'common_head_probe':ev(H/'base_run_common_probe01/report.json'),'scope':'새 6표시의 고정배율 등록·새 머리 공통화 후보. 의상 경계·아머 소유·패킹 미완료. 전체31참조 중 첫3몸체이며 완료로 집계하지 않음.'}
    j['full_art_unification_complete']=False;write(out,j)
    u.update(source_ledger=ev(out),candidates=j['current_candidates']);u['counts']['unique_key_status_counts']=dict(Counter(k['status'] for k in u['keys']));u['counts']['reference_status_counts']=dict(counts)
    for form,row in u['forms'].items():
        row['unique_key_status_counts']=dict(Counter(k['status'] for k in u['keys'] if k['form']==form));row['reference_status_counts']=dict(Counter(r['status'] for r in j['references'] if r['form']==form))
    write(H/'unique_art_keys13.json',u);print(json.dumps(u['counts'],ensure_ascii=False))
if __name__=='__main__':main()
