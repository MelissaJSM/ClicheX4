"""공중 동결 범위와 실제 열람/남은 작업을 구별하여 전체 장부를 갱신한다."""
from pathlib import Path
import json,sys
from collections import Counter
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive

def main():
    old=json.loads((H/'fullform_ledger03.json').read_text('utf8'));a=Archive((H/'prepared_air01/PL00_U.ARC').read_bytes());need(sha(a.data)=='c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be','Changed air candidate')
    for r in old['references']:
        if r['form']in('base','fourth') and 33<=r['ref']<=54:
            r.update(status='new_art_frozen_for_integration',proposal='prepared_air01/proposal.json',decision='공중 새 머릿결/귀/의상22자세와 새 사격팔을 같은32타일 스트림으로 정확 패킹. 원총구·16부분마스크·팔1/2 보존. 원MIPS/GPU와 독립검사 통과. 실제게임 플레이는 별도.',changed_from_reviewed_parent=True,current_rgba_sha256=sha(a.composite(r['ref'],15 if r['form']=='fourth'else 0)[0].tobytes()))
    old['current_candidates']['PL00_U.ARC']={'path':(H/'prepared_air01/PL00_U.ARC').relative_to(ROOT).as_posix(),'sha256':sha(a.data)}
    counts=Counter(r['status']for r in old['references']);old['counts']['status_counts']=dict(counts);old['counts']['new_frozen_form_images']=counts['new_art_frozen_for_integration']
    for g in old['groups']:
        g['status_counts']=dict(Counter(r['status']for r in old['references']if r['form']==g['form']and r['group']==g['group']))
        if g['form']in('base','fourth')and g['group']=='air':g['observation']='33~54 공중과 사격은 새 상세화로 동결. 별도 특수 공중93/94는 기존 상체가 남아 있어 새 공중과의 연결을 후속 검토한다.'
    reviews=json.loads((H/'special_after_air01/manifest.json').read_text('utf8'))['sheets'];old['review_basis']['additional_special_after_air_actual_view']=reviews;old['review_basis']['air_actual_and_partial_and_sequence_review']='prepared_air01/verification.json';old['review_basis']['air_all_22_refs_16_masks_actually_viewed']=True
    old['counts']['pending_meaning']='재검토 대상과 실제 추가 그림 필요 여부를 분리한다. 수치 보존 검사를 미술 수용으로 대체하지 않는다.'
    old['partial_armor']['capacity_head5_bytes']=36;old['partial_armor']['capacity_arm7_bytes']=44
    old['partial_armor']['actually_viewed_targeted_partial_refs']=sorted(set(old['partial_armor']['actually_viewed_targeted_partial_refs'])|set(range(33,55)))
    findings=[
      {'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':[98,99],'status':'new_art_in_progress','observation':'기존 앞머리는 큰 연보라면이고 벌린 소매는 주름 없는 삼각면이다. 현재 작업은 네 의상98 한 원형을 만들고99의 기존+1px 위상을 유지한다. 기본/포스 새원화는44px 높이로 일치. Ultimate 새원화는54px여서 하체비율 교정 전 보류한다.'},
      {'forms':['ultimate_after'],'refs':[98,99],'status':'confirmed_old_costume_feature','observation':'수용 대기와 설정화는 맨팔인데 실제PL02 base98/99에는 넓은 흰 소매가 남음. 두 새 원화는 맨팔로 교정했으나 하체가 길어 아직 패킹하지 않음.99의 기존158px 재질변동은 별도기록.'},
      {'forms':['base','fourth'],'refs':[93,94,95,96,100,101,102,103,104,231,232],'status':'specific_detail_rework_pending','observation':'93/94의 뒤머리 큰면,95/96의 가슴 단색면과 주름 감소,100~104/231/232의 넓은 앞머리·얼굴 둥근면·칼라 소실이 대기보다 명확하다. 몸숙임/다리굽힘 자체를 결함으로 보지 않으며 원자세를 유지해 상세화한다.'},
      {'forms':['ultimate_before','ultimate_after'],'refs':[88,89,90,91,92,93,94,95,96,100,101,102,103,104,231,232],'status':'specific_detail_rework_pending','observation':'대기의 금테 선글라스와 소매/칼라·샌들 대비가 줄고 거친 옛몸 명암이 남음. 설정화 잔존소매/재킷경계를 각 자세에서 다시 확인한다. 일괄 재색상이나 기존머리로 덮기를 하지 않는다.'},
      {'forms':['base','fourth'],'refs':[88,89,90,91,92],'status':'lower_priority_preserve_pose','observation':'일부는 대기 머리선과 연결되어 보존 가치가 있다.88 고정 흰호 이펙트는 몸체단순함과 분리한다.옷주름 추가는98/99와 비교해 필요한 구간만 선정한다.'}]
    old['new_targeted_findings']=findings;old['priority_next']=[{'rank':1,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':[98,99],'why':'진행 중인 소규모 네의상 특수동작. 수영복 구소매와 큰 단색머리 교정.'},{'rank':2,'forms':['base','fourth'],'refs':[93,94,95,96,100,101,102,103,104,231,232],'why':'새공중과 대기 대비 질감 차이가 큰 특수 본체.'},{'rank':3,'forms':['ultimate_before','ultimate_after'],'refs':list(range(33,55))+list(range(143,159))+[183]+list(range(204,208))+list(range(213,231)),'why':'전폼 장부에서 공중/사다리/정면귀환/승리/호버를 누락하지 않고 순차 비교·정합.'}]
    old['unverified']=['남은 동작군의 미술 상세화 또는 보존 판단','모든237참조×32부분조합의 개별 미술 수용','새공중의 실제 조작/물리 전환과 게임 표시','98/99 새원화의 부분마스크·공유패킹(아직미진행)'];old['full_art_unification_complete']=False;old['new_candidate_emulator_test']=False
    write(H/'fullform_ledger04.json',old)
    own=json.loads((H/'findings.json').read_text('utf8'));own['whole_form_ledger']='fullform_ledger04.json';own['whole_form_ledger_counts']=old['counts'];own['air_frozen_proposal']='prepared_air01/proposal.json';own['latest_targeted_special_findings']=findings;own['full_art_unification_complete']=False;write(H/'findings.json',own)
    lines=['# 시부키 전체 폼 작업 장부','','기본/포스 공중33~54를 누적 후보에 동결했다. 새 원화·사격팔·실제 타일 재추출, 원MIPS/GPU, 독립 감사는 통과했으며 사용자 수용/실기 검사는 별도이다. 전체 통일화 완료가 아니다.','',f"전체 948 폼/참조 슬롯 중 912개가 복원된다. 현재 새 그림 동결 {counts['new_art_frozen_for_integration']}개, 후속 미술 검토 {counts['art_rework_group_pending']}개. 36개 빈 예약슬롯은 그림을 채우지 않는다.",'','| 폼 | 동작군 | 새그림 동결 | 미술 후속 | 보존·효과·예약 |','|---|---|---:|---:|---:|']
    for g in old['groups']:
        c=g['status_counts'];n=c.get('new_art_frozen_for_integration',0);p=c.get('art_rework_group_pending',0);lines.append(f"| {g['form']} | {g['group']} | {n} | {p} | {len(g['refs'])-n-p} |")
    lines+=['','최근 실제 열람은 공중 재추출6장, 모든22참조×16마스크6장, 원애니표 순서6장, 특수18참조×4폼12장이다. 이전64개 주요 시트의19+루트45 실제열람 기록을 유지한다. 그림 순서 WEBP는 실제 게임 플레이가 아니다.','','다음은98/99의 네 의상이다. 기본/포스 생성물은 크기가 맞지만 Ultimate 생성물은 다리가10px 길어져 보류했다. 이후93~104·231/232, 얼티밋 공중/사다리/등장/정면귀환/승리/호버/탑승도 기존 장부에서 계속 다룬다. 원래 굽힘/원근과 이펙트를 무조건 새 그림으로 바꾸지 않는다.','','상세 원점·자원 해시·개별 상태·미확인은 `fullform_ledger04.json`, 공중 동결 증거는 `prepared_air01/FROZEN.json`을 따른다.']
    (H/'FULLFORM_LEDGER.md').write_text('\n'.join(lines)+'\n','utf8')
    with(H/'REPORT.md').open('a',encoding='utf8')as f:f.write('\n\n## 기본/포스 공중22 동결 및 다음 특수군\n\n`prepared_air01`의 PL00 c580b371…를 동결했다. 목표110층, 비대상486 raw/1677조립, 부분704조건, 총구352조건, 원MIPS/GPU와 독립 감사가 통과했다. 추가 팔 실패 원화는 국소 재생성으로 해결했으며 전체32타일과 은행경계를 유지했다. 실제 플레이/사용자 수용은 아직 별도다.\n\n`special_after_air01` 12시트에서18참조×4폼을 실제 대조했다.98/99가 다음 제작이며 Ultimate 수영복에 남은 흰소매는 설정화/대기와 맞지 않아 교정 대상이다. 생성 Ultimate는 다리가 길어져 현재 보류한다. 전체 남은범위는 `fullform_ledger04.json`에 유지한다.\n')
    print(json.dumps(old['counts'],ensure_ascii=False))
if __name__=='__main__':main()
