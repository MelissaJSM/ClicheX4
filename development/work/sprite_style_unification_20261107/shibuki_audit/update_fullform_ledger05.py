"""네 폼98/99 동결과 다음 라이징 파이어 후보를 전수 장부에 반영한다."""
from pathlib import Path
from collections import Counter
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write

def main():
    q=json.loads((H/'fullform_ledger04.json').read_text('utf-8'))
    arcs={}
    for key,name in [('base','PL00_U.ARC'),('ultimate','PL02_U.ARC')]:
        folder=H/f'prepared_double_cyclone_{key}01';lock=json.loads((folder/'FROZEN.json').read_text('utf8'))
        need(lock['frozen']and sha((folder/name).read_bytes())==lock['files'][name],'Candidate not frozen')
        arcs[name]=Archive((folder/name).read_bytes())
        q['current_candidates'][name]={'path':(folder/name).relative_to(ROOT).as_posix(),'sha256':lock['files'][name],
                                      'frozen_record':(folder/'FROZEN.json').relative_to(ROOT).as_posix()}
    for row in q['references']:
        if row['ref']in(98,99):
            arc=arcs['PL02_U.ARC'if row['form'].startswith('ultimate')else'PL00_U.ARC']
            mask=15 if row['form']in('fourth','ultimate_before')else 0
            im=arc.composite(row['ref'],mask)[0]
            row.update({'status':'new_art_frozen_for_integration','changed_from_reviewed_parent':True,
                        'current_rgba_sha256':sha(im.tobytes()),'opaque_pixels':sum(im.getchannel('A').point(lambda v:1 if v else 0).getdata()),
                        'decision':'새98 네 의상 상세화와99의 수용된1px 이동을 동결. 손 접점·고정은행·부분조합·원MIPS/GPU·독립감사 통과. 실기/사용자수용 별도.'})
    status=Counter(r['status']for r in q['references'])
    q['counts']['status_counts']=dict(status);q['counts']['new_frozen_form_images']=status['new_art_frozen_for_integration']
    need(status['new_art_frozen_for_integration']==244 and status['art_rework_group_pending']==464,'Unexpected coverage count')
    for group in q['groups']:
        group['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==group['form']and r['ref']in group['refs']))
    q['priority_next'][0]={'rank':1,'forms':['base','fourth','ultimate_before','ultimate_after'],
        'refs':[100,101,102,103,104,231,232],
        'why':'기본/포스6키 원화 생성·native 검토 완료,104 팔 원효과 접점 교정 완료. Ultimate 두 페이지 의상 입력 준비. 파츠정합·패킹은 미완료.'}
    q['priority_next'][1]['refs']=[93,94,95,96]
    q['new_targeted_findings']=[r for r in q['new_targeted_findings']if r['refs']not in([98,99],)]
    q['new_targeted_findings'].insert(0,{'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':[98,99],
        'status':'frozen_verified','observation':'네 의상 새 상세도트/맨팔 복원과 원몸체 크기·손 접점 반영. 거부된 긴 다리 시안은 미적용.244개 동결 표시에 포함.'})
    q['new_targeted_findings'].insert(1,{'forms':['base','fourth'],'refs':[100,101,102,103,104,231,232],
        'status':'new_art_native_registration_in_progress','observation':'생성된 새6키는 머리 분할·칼라·치마/망토 명암을 보완했다.104 주먹이 왼쪽으로 밀린 최초안은 국소 생성+신규손35/37px 평행등록으로 원위치/원불꽃거리 복구. 아직 파츠 분리·패킹 미완료.'})
    q['review_basis']['new_rising_fire_actual_viewed_sheets']=[
        (H/p).relative_to(ROOT).as_posix() for p in [
        'rising_fire_native01/base_comparison.png','rising_fire_native01/fourth_comparison.png',
        'rising_fire_native02/base_comparison.png','rising_fire_native02/fourth_comparison.png',
        'rising104_arm_native02/base_comparison.png','rising104_arm_native02/fourth_comparison.png',
        'rising_fire_contact_probe02/contact_spatial_probe.png']]
    q['review_basis']['rising_fire_effect_limitations']='원래 초기화 MIPS8조건/효과원점·알파 마스크 진단만.차지 몸/효과의 시간위상과실기 재생은 미검증.'
    q['full_art_unification_complete']=False;q['new_candidate_emulator_test']=False
    write(H/'fullform_ledger05.json',q)
    print(json.dumps(q['counts'],ensure_ascii=False))
if __name__=='__main__':main()
