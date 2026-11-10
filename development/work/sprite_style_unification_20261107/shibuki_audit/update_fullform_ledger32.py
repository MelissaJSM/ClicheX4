"""BR23 실제 재독출과 UI8 준비, Ultimate 후속4를 별도 상태로 기록."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.c01_audio_build import read_disc
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger32.json').exists(),'새 장부 필요')
    q=json.loads((H/'fullform_ledger31.json').read_text('utf8'));b=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v23/shibuki_riko.bin';digest=hashlib.sha256()
    with b.open('rb')as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
    need(digest.hexdigest()=='cba70c5fee260a7e0d0e7751be9e8583ef2050696a3700add9cf06f6679b0724','BR23 해시')
    blobs=read_disc(b,('PL00_U.ARC','PL02_U.ARC','ST0E_U1.ARC'))[0]
    expected={'PL00_U.ARC':'4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175','PL02_U.ARC':'26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce','ST0E_U1.ARC':'ea2167e98f8ae045c4353cca18cc571614e34949160cd85cc14ac9a6cb8e1c54'}
    need({n:sha(v)for n,v in blobs.items()}==expected,'재독출 자원 불일치')
    proof={'bin':{'path':b.relative_to(ROOT).as_posix(),'sha256':digest.hexdigest()},'resources':expected,'actual_disc_readback':True,'native_by_root':ev(H.parent/'staging_br_v23_native_checks.json'),'new_gameplay_execution_here':False}
    write(H/'br23_readback01.json',proof)
    q['active_integration']={'project':'ver_buki_riko','build':'sprite_style_unification_20261107_v23','bin_sha256':digest.hexdigest(),'PL00_sha256':expected['PL00_U.ARC'],'PL02_sha256':expected['PL02_U.ARC'],'ST0E_sha256':expected['ST0E_U1.ARC'],'new_independent_bin_readback_here':True,'proof':ev(H/'br23_readback01.json'),'runtime_for_new_standing8':False,'unaccepted_generated_art_included':False}
    q['current_candidates']['PL00_U.ARC'].update(integrated=True,integrated_build='BR23');q['current_candidates']['PL00_U.ARC'].pop('integration_planned_by_root',None)
    q['standing_fire8_frozen_scope'].update(integration=True,integrated_build='BR23',runtime=False)
    q['selection_standing8_prepared']={'refs':list(range(1,9)),'body_refs':list(range(85,93)),'candidate':ev(H/'prepared_selection_standing01/ST0E_U1.ARC'),'proposal':ev(H/'prepared_selection_standing01/proposal.json'),'lock':ev(H/'prepared_selection_standing01/PREPARED_LOCK.json'),'source_readback':ev(H/'selection_standing_sync03/report.json'),'own_actual_review':ev(H/'prepared_selection_standing01/visual_review.json'),'frozen':False,'integrated':False,'independent_pending':True,'v4_guard_root_pending':True,'new_art':False}
    q['next_generation'].update(current_common=ev(H/'ultimate_standing_fire_common01/report.json'),followthrough=ev(H/'ultimate_standing_followthrough_native01/report.json'),generated_distinct_refs=[85,89,90,91],generated_form_images=8,in_progress_refs=[85,89,90,91],status='85/89 전후공통층·총열 후보10층,90/91 전후4 고정등록.후폼90 흰소매 국소교정 진행,86/87/92 원화와전체8패킹 미완료.',remaining_source_refs=[86,87,92],frozen=False,arc_written=False)
    for r in q['references']:
        if 85<=r['ref']<=92 and r['form']in('base','fourth'):r['decision']='새85..92 동결4fe717이 BR23에서 실제재독출 exact.원MIPS/독립/루트12판 완료.선택1..8은 별도47e5 준비본,실기 미검증.'
        if r['ref']in(85,89,90,91)and r['form'].startswith('ultimate'):r['in_progress_unapplied_art']=q['next_generation']
    q['pending_related_old_frames']=[135]
    q['full_art_unification_complete']=False;write(H/'fullform_ledger32.json',q)
    keys=json.loads((H/'unique_art_keys31.json').read_text('utf8'));keys.update(scope='BR23 실제PL004fe717/PL0226fd 네폼 표시키.원화장수/품질완료율아님.',source_ledger=ev(H/'fullform_ledger32.json'),candidates=q['current_candidates'],integration=q['active_integration'],next_unfrozen_art=q['next_generation'],selection_copy_candidate=q['selection_standing8_prepared']);write(H/'unique_art_keys32.json',keys)
    print(json.dumps({'ledger':ev(H/'fullform_ledger32.json'),'keys':ev(H/'unique_art_keys32.json'),'readback':ev(H/'br23_readback01.json')}))
if __name__=='__main__':main()
