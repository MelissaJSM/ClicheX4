"""검토 장부에 새 Ultimate 벽 24표시와 남은 전 폼 우선순위를 기록한다."""
from pathlib import Path
import sys,json,hashlib
from collections import Counter
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    p=json.loads((H/'fullform_ledger02.json').read_text('utf8'));file=H/'prepared_ultimate_wall01/PL02_U.ARC';raw=file.read_bytes();assert sha(raw)=='c851fb17b2369281667970c414be63eb31fb1f02fe5641ad667bfb4b5c8507cf';a=Archive(raw)
    p['current_candidates']['PL02_U.ARC']={'path':file.relative_to(ROOT).as_posix(),'sha256':sha(raw)}
    new=0
    for r in p['references']:
        if not r['form'].startswith('ultimate')or not r['structural_decode']:continue
        actual=a.composite(r['ref'],r['effective_render_mask'])[0];s=sha(actual.tobytes())
        if r['ref']in range(55,67):
            assert r['status']=='art_rework_group_pending';r.update(status='new_art_frozen_for_integration',decision='새 원화·의상/팔 정합·무손실 패킹 및 정적 재현 완료. 실제 게임은 별도.',proposal='prepared_ultimate_wall01/proposal.json',current_rgba_sha256=s,opaque_pixels=sum(v>0 for v in actual.getchannel('A').getdata()),changed_from_reviewed_parent=True);new+=1
        else:assert s==r['current_rgba_sha256'],(r['form'],r['ref'],'non-target image changed')
        if r['status']=='new_art_frozen_for_integration':r['proposal']='prepared_ultimate_wall01/proposal.json'
    assert new==24
    c=Counter(r['status']for r in p['references']);assert c['new_art_frozen_for_integration']==192 and c['art_rework_group_pending']==516
    p['counts']['new_frozen_form_images']=192;p['counts']['status_counts']=dict(c)
    for g in p['groups']:
        g['status_counts']=dict(Counter(r['status']for r in p['references']if r['form']==g['form']and r['group']==g['group']))
        if g['form'].startswith('ultimate')and g['group']=='wall':g['focus']='새 양폼 벽/사격 동결';g['observation']='55..66의 새 머리·금테장식·칼라·재킷/민소매와 정확한 총구를 정합했다. 기존 단색 몸체를 덮지 않았다.'
    reviewed=json.loads((H/'remaining_after_wall01/manifest.json').read_text('utf8'))['sheets']
    p['review_basis']['remaining_after_wall_actually_viewed_sheets']=reviewed
    p['review_basis']['new_wall_actual_readback_sheets']=[(H/'prepared_ultimate_wall01'/f/f'actual_{i:02}.png').relative_to(ROOT).as_posix()for f in('before','after')for i in range(2)]
    p['priority_next']=[
        {'rank':1,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(33,55))+[93,94],'why':'빈번한 공중 본체가 대기보다 단순하다. 기본/포스 소매·후두부 큰 단색면, Ultimate 발/정강이 살색 덩어리·재킷39 가슴/배의 재질 구분 부족. 정상 웅크림은 유지하며 부위별 새 그림이 필요하다.','first_page':[33,35,39],'first_forms':['base','fourth']},
        {'rank':2,'forms':['base','fourth'],'refs':list(range(3,33)),'why':'보행의 옆면 머릿결·소매·치마 주름이 대기보다 빈약하다. Ultimate 새 보행을 기본/포스 완료로 세지 않는다. 총구와 기존 교차 보폭을 유지한다.'},
        {'rank':3,'forms':['ultimate_before','ultimate_after'],'refs':list(range(143,159))+[183]+list(range(204,208)),'why':'후면 단색머리와 소매/등, 평면 정면얼굴·의상·선글라스 누락. 사다리 접점 및 빛 속 몸체를 함께 동기화한다.'},
        {'rank':4,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(67,85))+list(range(162,175))+list(range(213,231)),'why':'대시·체이서·호버/노바의 머리·의상과 추진/좌석 접점 재검토. 표시mask 예외와 실제 능력 사용 가능을 구분한다.'},
        {'rank':5,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(88,105))+[106,108,110,231,232,233,234,235,236],'why':'특수/피격의 대기 대비 미술 차이와 몸체 연계 효과를 처리한다. 단색 번개 자체를 낮은 품질 본체로 세지 않는다.'}]
    p['unverified']=['잔여516폼/참조의 새 미술 상세화 또는 공유 파생 검토','모든237참조×32부분조합의 개별 육안 수용','새 Ultimate 벽의 게임 내 전환·물리·조준 실제 플레이','모든 희귀 동작 실기 접점·전환']
    (H/'fullform_ledger03.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8')
    f=json.loads((H/'findings.json').read_text('utf8'));f['whole_form_ledger']='fullform_ledger03.json';f['whole_form_ledger_counts']=p['counts'];f['full_art_unification_complete']=False;(H/'findings.json').write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n','utf8')
    print(p['counts'])
if __name__=='__main__':main()
