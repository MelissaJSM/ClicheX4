"""보행 준비 ARC와 원경로 검사, 루트 차량/특수 실제 열람 분류를 결합."""
from pathlib import Path
from collections import Counter
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write

def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}

def main():
    out=H/'fullform_ledger15.json'; need(not out.exists(),'Fresh ledger')
    j=json.loads((H/'fullform_ledger14.json').read_text('utf8'));u=json.loads((H/'unique_art_keys14.json').read_text('utf8'))
    arc=H/'prepared_base_run01/PL00_U.ARC'; need(sha(arc.read_bytes())=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce','Candidate changed')
    rr=ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint72.json'; root=json.loads(rr.read_text('utf8'))
    native=ROOT/'work/sprite_style_unification_20261107/zero_audit/shibuki_run32_directory_native01/report.json'
    need(json.loads(native.read_text('utf8'))['passed'],'Native failure')
    for r in j['references']:
        if r['form']in('base','fourth')and 1<=r['ref']<=32:
            r.update(status='new_art_prepared_pending_independent',decision=('1은 수용 대기0 전체층을 정확히 재사용. 0/141/142 보호.'if r['ref']==1 else'새 머리/옷/팔/총구160층의 ARC 재추출 일치. 원디렉터리 MIPS 통과. 독립 전체 정적 마감 및 새 부팅 전.'),prepared_evidence=ev(arc))
        n=r['ref']
        if 162<=n<=174:
            r['latest_root_visual_observation']={'evidence':ev(rr),'decision':'세부 재작화 필요','detail':'밝은 큰 앞머리 면과 적은 소매/가슴/옆머리 층. 앉은 관절·손·좌석 기준점은 보존.'}
        elif 184<=n<=203:
            r['latest_root_visual_observation']={'evidence':ev(rr),'decision':'198은 빈 참조, 나머지는 머리 전용. Ultimate 금색 장식 위치·식별성 국소 대조 필요. 전신 높이와 비교하거나 늘리지 않음.'}
        elif 213<=n<=230:
            ultimate=r['form'].startswith('ultimate')
            kind=('effect_only'if n==219 or (n==218 and not ultimate) else'body_and_effect'if n in(217,218,220) else'body')
            r['latest_root_visual_observation']={'evidence':ev(rr),'content_kind':kind,'decision':'몸체 있는 자세의 머리/소매/가슴 세부 보완. 원효과와 분리하여 재작화. 동일번호의 PL00/PL02 내용 차이를 보존.'}
            if ultimate and n>=217:
                r['latest_root_visual_observation']['effective_mask']=15
                r['latest_root_visual_observation']['logical_costume_check']='원래 표시정책mask15는 유지. 획득 후 수영복 의상의 일관성은 별도 후속 대조. 전후 같은그림 자체만으로 결함 판정하지 않음.'
    j['unpacked_art_in_progress']['historical']=True
    j['unpacked_art_in_progress']['superseded_by']='prepared_run32'
    j['prepared_run32']={'archive':ev(arc),'proposal':ev(H/'prepared_base_run01/proposal.json'),'verification':ev(H/'prepared_base_run01/verification.json'),'directory_native':ev(native),'root_art_review':ev(ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint75.json'),'agent_art_review':ev(H/'base_run_readback_review01.json'),'scope':'32참조×5층. 1은 수용 대기 재사용, 나머지31은 새몸체/사격팔. 별도 시험 ARC이며 전체 완료/사용자수용/게임 실기 완료 아님.','entry2_fixed_length':186228,'bank0_growth_bytes':672,'unconsumed_tail_trim':{'10':344,'11':328},'art_reduced':False,'source_raw_non_targets_preserved':476,'render_layers_preserved':980,'partial_combinations':1024,'same_builds':3,'negative_tests':12,'independent_static_pending':True,'fresh_gameplay_verified':False,'authorization':'전체 승인된 스프라이트 재작화·재삽입 범위에서 루트가 가역 시험 구현으로 판단. 사용자가 새offset을 직접 승인했다고 기록하지 않음.'}
    j['latest_vehicle_review']={'evidence':ev(rr),'source_disc':root['current_discs']['shibuki'],'findings':[v for v in root['findings']if v['character']=='shibuki'],'limits':root['limits'],'observer':'root','agent_repeated_visual_review':False}
    j['next_generation']={'manifest':ev(H/'ultimate_ladder_inputs01/manifest.json'),'refs':[143,144,146],'forms':['ultimate_before','ultimate_after'],'status':'입력3장 실제 열람 완료, 나나 피격 생성 이후 순서 대기','generated':False}
    counts=Counter(r['status']for r in j['references']);j['counts']['status_counts']=dict(counts)
    for g in j['groups']:g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
    j['full_art_unification_complete']=False;write(out,j)
    for k in u['keys']:
        k['status_by_ref']={n:next(r['status']for r in j['references']if r['form']==k['form']and r['ref']==int(n))for n in k['status_by_ref']};s=set(k['status_by_ref'].values());k['status']=next(iter(s))if len(s)==1 else'mixed_review_status'
    u.update(source_ledger=ev(out),note='고유키 묶음은 원 동결 자원의 정확동형 기준이다. 새32는 prepared 상태로 분리하며 아직 새 실기/독립 동결 완료에 합산하지 않는다.')
    u['counts']['unique_key_status_counts']=dict(Counter(k['status']for k in u['keys']));u['counts']['reference_status_counts']=dict(counts)
    for form,row in u['forms'].items():row['unique_key_status_counts']=dict(Counter(k['status']for k in u['keys']if k['form']==form));row['reference_status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==form))
    write(H/'unique_art_keys15.json',u);print(json.dumps(u['counts'],ensure_ascii=True))
if __name__=='__main__':main()
