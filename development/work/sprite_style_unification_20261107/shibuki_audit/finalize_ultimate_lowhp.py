"""저체력 누적 준비본과 전폼 잔여 장부를 동결 기록한다."""
from pathlib import Path
from collections import Counter
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive
O=H/'prepared_ultimate_lowhp01'

def main():
    v=json.loads((O/'repro_and_rejections.json').read_text('utf8'))
    need(v['passed'] and v['reproduced_sha256']=='3dd0d9a2cafd8e4d4355ef131c69c39f794698f6752524b39cf488f5b3bc737b','Final checks missing')
    names=['PL02_U.ARC','proposal.json','verification.json','repro_and_rejections.json','before/actual.png','after/actual.png']
    freeze={'frozen':True,'scope':'Ultimate 양 의상 저체력120~125, 기존 새 이동/사격3~32 누적','files':{n:sha((O/n).read_bytes())for n in names},'source_scripts':{n:sha((H/n).read_bytes())for n in ['register_ultimate_lowhp_edit.py','prepare_ultimate_lowhp_shared.py','prepare_ultimate_lowhp_targets.py','pack_ultimate_lowhp.py','verify_ultimate_lowhp.py']},'new_generated_sha256':'aae841c4de541d42afc625288db6b9d29b7f70d554ad8c8ffd9f5ee3615c9a86','source_generation_tool':'builtin imagegen','runtime_verified':False,'game_or_pointer_written':False,'note':'첫 정면51px 후보는 폐기하지 않고 보류 기록으로 보존. 이번48px 교정 원화의 키/발접점은 유지하며 기존2px 호흡·입1px 교대만 파생했다.'}
    write(O/'FROZEN.json',freeze)
    ledger=json.loads((H/'fullform_ledger01.json').read_text('utf8'))
    arc=Archive((O/'PL02_U.ARC').read_bytes())
    changed=0
    for r in ledger['references']:
        if r['form'] not in ('ultimate_before','ultimate_after') or r['ref'] not in range(120,126):continue
        mask=15 if r['form']=='ultimate_before' else 0
        im=arc.composite(r['ref'],mask)[0]
        r.update(status='new_art_frozen_for_integration',decision='새 피로 자세의 머리·칼라·소매·치마를 등록하고 양 의상 공통 머리/다리·손 정합, 원표3호흡/입교대 유지. 전체 키48/49/50과발y22를 기록; 실기 별도.',current_rgba_sha256=sha(im.tobytes()),opaque_pixels=sum(bool(x)for x in im.getchannel('A').tobytes()),changed_from_reviewed_parent=True,new_candidate=str((O/'PL02_U.ARC').relative_to(ROOT)))
        changed+=1
    need(changed==12,'Wrong ledger patch count')
    ledger['current_candidates']['PL02_U.ARC']={'path':str((O/'PL02_U.ARC').relative_to(ROOT)),'sha256':sha((O/'PL02_U.ARC').read_bytes())}
    counts=Counter(r['status']for r in ledger['references'])
    ledger['counts']['status_counts']=dict(counts)
    ledger['counts']['new_frozen_form_images']=counts['new_art_frozen_for_integration']
    for group in ledger['groups']:
        group['status_counts']=dict(Counter(r['status']for r in ledger['references']if r['form']==group['form'] and r['group']==group['group']))
        if group['form'].startswith('ultimate_') and group['group']=='hurt_lowhp':
            group['observation']='120~125 새 양 의상 후보를 동결했다. 피격106~114 및233~236의 본체/효과는 기존 잔여 검토 범위다.'
    ledger['priority_next']=ledger['priority_next'][1:]
    for i,p in enumerate(ledger['priority_next'],1):p['rank']=i
    ledger['review_basis']['new_lowhp_actual_readback_sheets']=[str((O/'before/actual.png').relative_to(ROOT)),str((O/'after/actual.png').relative_to(ROOT))]
    ledger['unverified'].append('새 Ultimate 저체력6참조의 원래 MIPS/GPU 및 실제 게임 연결')
    write(H/'fullform_ledger02.json',ledger)
    findings=json.loads((H/'findings.json').read_text('utf8'))
    findings['ultimate_lowhp_repaint']={'state':'frozen_for_integration','proposal':str((O/'proposal.json').relative_to(ROOT)),'sha256':sha((O/'PL02_U.ARC').read_bytes()),'runtime_verified':False,'ledger':'fullform_ledger02.json'}
    write(H/'findings.json',findings)
    text='''

## Ultimate 저체력 양 의상 교정 동결

`prepared_ultimate_lowhp01`은 새 이동/사격 `prepared_run_complete03` 위에120~125만 추가한 누적PL02다. 새3/4 피로 자세의 머리결·금테 선글라스·칼라·소매와 치마를 그대로 등록했다. 재킷형의 새 머리/다리/손을 민소매형과 공통으로 맞췄으며, 민소매의 새 몸통·전완은 보존했다. 기존 거친 저체력 그림을 덮어쓴 픽셀은0개다. 원팔레트1/4/11의 의상별 색 차이는 기존색 근사로 제한했다.

기준 자세는28×48px이며 기존0/-1/-2 호흡에 따라48/49/50px가 된다. 수용대기47px와 완전히 같은 bbox라는 주장은 하지 않는다. 머리를 낮춘 자세와 의상 디테일은 비교이미지에서 확인했고, 모든 단계의 발은world y18 이상 완전히 고정했다. 원래16step의ID6 시간표와입1px 교대를 유지한다. `ultimate_lowhp_targets01/*_simulation.webp`는60호출/초를 가정한 추출 프레임 재생이며 실제플레이 영상이 아니다.

재패킹 후30레이어·12폼표시가 목표와 정확히 같고512raw·444비대상폼표시, 앞서 완성한 이동/사격60표시, 팔레트·음향·나머지ARC항목을 보존했다.88GPU타일경계와384마스크/팔/방향 조합,6잘못된입력 거부,동일해시 재현검사를 통과했다. 실제게임·원MIPS/GPU실행은루트통합 이후 별도다.

최신 전폼 장부는`fullform_ledger02.json`이다. 총948폼/참조 중 새168표시를 동결했고 잔여그룹검토540표시가 남는다. 64기존주요시트 전수열람과 새후보 제작은 구별한다. 다음은Ultimate 벽/사다리/정면·승리,공중·대시·탑승·호버/특수의 상세화이며 전체미술통일 완료가 아니다.
'''
    with (H/'REPORT.md').open('a',encoding='utf8') as f:f.write(text)
    print(json.dumps({'frozen_sha256':sha((O/'FROZEN.json').read_bytes()),'new_frozen_form_images':168,'pending_group_images':counts['art_rework_group_pending']}))

if __name__=='__main__':main()
