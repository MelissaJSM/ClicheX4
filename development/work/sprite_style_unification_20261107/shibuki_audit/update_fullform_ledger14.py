"""보행32의 완성 원화·등록과 아직 실패한 자원 패킹을 구별해 집계한다."""
from pathlib import Path
from collections import Counter
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    out=H/'fullform_ledger14.json';need(not out.exists(),'Fresh output')
    j=json.loads((H/'fullform_ledger13.json').read_text('utf8'));u=json.loads((H/'unique_art_keys13.json').read_text('utf8'))
    lock=H/'base_run_complete_targets01/LOCK.json';need(sha(lock.read_bytes())=='44170f9268ab8df6d1aefb26fdaec75981533e16477fa16f1897d7d1d29f3e65','Changed target lock')
    for r in j['references']:
        if r['form']in('base','fourth') and r['ref']in range(1,33):
            r.update(status='new_art_registered_capacity_pending',decision=('ref1은 수용 대기0 전체층 재사용 후보. 0/141/142는 변경 대상 아님.' if r['ref']==1 else '새 세부 원화와 발/눈·원총열 정합 및 부분층 등록 완료. 자원 용량 초과로 ARC 미생성, 독립 패킹·실기 미완료.'),registered_target_evidence=ev(lock))
    counts=Counter(r['status']for r in j['references']);j['counts']['status_counts']=dict(counts)
    for g in j['groups']:g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
    j['unpacked_art_in_progress']={'forms':['base','fourth'],'refs':list(range(1,33)),'accepted_idle_reuse_refs':[1],'newly_drawn_moving_body_keys':list(range(3,32,2)),'new_shooting_arm_keys':list(range(2,33,2)),'target_lock':ev(lock),'scope':'32참조×5층 등록. 64의상 표시 중 ref1 두 표시는 대기 재사용이며 새 그림64장이라는 뜻이 아님. 최종 ARC 없음. 그림 손실 없는 저장 구조를 조사 중.','structural_partial_combinations':1024,'whole_bank_capacity_deficit_before_global_dedup':4984,'capacity_deficit_after_optimal_reencode_exact_raw_dedup':3202,'other_banks_readonly_potential_slack_with_reencode':1234,'art_cut_or_bank_move_applied':False,'root_review_evidence':[ev(ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint63.json')],'probe_files':[ev(H/'pl00_graphics_slack_audit.json'),ev(H/'pl00_other_bank_reencode_audit.json'),ev(H/'base_run_complete_pack05/report.json')]}
    j['next_groups_after_run']=[{'priority':1,'forms':['ultimate_before','ultimate_after'],'refs':list(range(143,156))+[183],'scope':'후면 사다리 의상·머릿결. 기존 기본/포스 상세 원화의 동일 접점 의상 편집 가능성부터 조사.'},{'priority':2,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(106,115))+list(range(233,237)),'scope':'일반 피격·넉백. 저체력120..125 동결과 구분.'},{'priority':3,'forms':['ultimate_before','ultimate_after'],'refs':list(range(126,143))+list(range(156,162))+list(range(204,208)),'scope':'등장·정면·귀환·승리. 광선/빈프레임과 body 재작화 범위를 구분.'},{'priority':4,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(162,175)),'scope':'체이서 몸체·공통 머리 크기, 원기체 보호.'},{'priority':5,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(85,98))+list(range(213,231))+list(range(184,204)),'scope':'특수/정지사격/탑승. 실제 사용·효과층·빈참조를 구별 후 필요한 몸체만 수정.'}]
    j['full_art_unification_complete']=False;write(out,j)
    for k in u['keys']:
        k['status_by_ref']={n:next(r['status']for r in j['references']if r['form']==k['form']and r['ref']==int(n))for n in k['status_by_ref']};s=set(k['status_by_ref'].values());k['status']=next(iter(s))if len(s)==1 else'mixed_review_status'
    u.update(source_ledger=ev(out),note='고유키 동형 묶음은 현재 동결 자원 기준이며 미패킹 새32를 실제 적용된 새 키로 세지 않는다.')
    u['counts']['unique_key_status_counts']=dict(Counter(k['status']for k in u['keys']));u['counts']['reference_status_counts']=dict(counts)
    for form,row in u['forms'].items():row['unique_key_status_counts']=dict(Counter(k['status']for k in u['keys']if k['form']==form));row['reference_status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==form))
    write(H/'unique_art_keys14.json',u);print(json.dumps(u['counts'],ensure_ascii=True))
if __name__=='__main__':main()
