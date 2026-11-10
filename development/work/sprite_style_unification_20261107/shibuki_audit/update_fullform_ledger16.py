"""보행32 동결 완료를 전체 진행표에 반영하되 새 게임 실기와 구별."""
from pathlib import Path
from collections import Counter
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    out=H/'fullform_ledger16.json';need(not out.exists(),'Fresh ledger');j=json.loads((H/'fullform_ledger15.json').read_text('utf8'));u=json.loads((H/'unique_art_keys15.json').read_text('utf8'));d=H/'prepared_base_run01';f=json.loads((d/'FROZEN.json').read_text('utf8'));need(f['frozen'],'Not frozen')
    for n,h in f['files'].items():need(sha((d/n).read_bytes())==h,'Changed frozen output')
    j['current_candidates']['PL00_U.ARC']={**ev(d/'PL00_U.ARC'),'frozen_record':ev(d/'FROZEN.json'),'independent_and_full_native_pending':False,'new_run32_gameplay_verified':False}
    j['prepared_run32'].update(independent_static_pending=False,final_verification=ev(d/'final_verification.json'),frozen=ev(d/'FROZEN.json'),directory_native=ev(ROOT/'work/sprite_style_unification_20261107/zero_audit/shibuki_run32_directory_native01/report.json'))
    for r in j['references']:
        if r['form']in('base','fourth')and 1<=r['ref']<=32:
            r.update(status='new_art_frozen_for_integration',decision=('1은 수용 대기0의 전체층/도트 재사용. 0/141/142 원형 보호.'if r['ref']==1 else'새 원화/의상층·독립 재독출·원디렉터리 MIPS·루트 실제12판 열람 통과하여 통합용 동결. 새 부팅/사용자 최종수용은 별도.'),frozen_evidence=ev(d/'FROZEN.json'))
    j['next_generation'].update(status='첫6표시 생성·고정1/8 등록.144/146 뒤통수 선글라스 오류로 보류, 국소 편집 준비.',generated=True,source=ev(H/'ultimate_ladder_inputs01/page01/generated.png'),native_report=ev(H/'ultimate_ladder_native01/report.json'),packed=False)
    counts=Counter(r['status']for r in j['references']);j['counts']['status_counts']=dict(counts)
    for g in j['groups']:g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
    write(out,j)
    for k in u['keys']:
        k['status_by_ref']={n:next(r['status']for r in j['references']if r['form']==k['form']and r['ref']==int(n))for n in k['status_by_ref']};ss=set(k['status_by_ref'].values());k['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status'
    u.update(source_ledger=ev(out),note='고유키 묶음은 동형을 확인한 기존 자원 기준으로 유지.32참조 동결은 새64장 원화·전체 완료·실기 완료의 뜻이 아니다.1은 대기 재사용.')
    u['counts']['unique_key_status_counts']=dict(Counter(k['status']for k in u['keys']));u['counts']['reference_status_counts']=dict(counts)
    for form,row in u['forms'].items():row['unique_key_status_counts']=dict(Counter(k['status']for k in u['keys']if k['form']==form));row['reference_status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==form))
    write(H/'unique_art_keys16.json',u);print(json.dumps(u['counts'],ensure_ascii=True))
if __name__=='__main__':main()
