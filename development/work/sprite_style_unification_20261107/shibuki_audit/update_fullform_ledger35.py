"""BR24 실제재독출·체이서13 준비본·Ultimate첫입력을 분리한 장부."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.c01_audio_build import read_disc
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger35.json').exists(),'새 장부 필요');q=json.loads((H/'fullform_ledger34.json').read_text('utf8'));b=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v24/shibuki_riko.bin';digest=hashlib.sha256()
    with b.open('rb')as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
    need(digest.hexdigest()=='45b5e019396f37aaa623e2c23bd4b91ceff344826ef95b6496c41e3d55b91644','BR24 변경')
    expected={'PL00_U.ARC':'4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175','PL02_U.ARC':'26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce','ST0E_U1.ARC':'47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'}
    need({n:sha(v)for n,v in read_disc(b,tuple(expected))[0].items()}==expected,'실제 재독출 차이')
    write(H/'br24_readback01.json',{'bin':ev(b),'resources':expected,'actual_disc_readback':True,'new_gameplay_execution_here':False})
    q['active_integration']={'project':'ver_buki_riko','build':'sprite_style_unification_20261107_v24','bin_sha256':digest.hexdigest(),'PL00_sha256':expected['PL00_U.ARC'],'PL02_sha256':expected['PL02_U.ARC'],'ST0E_sha256':expected['ST0E_U1.ARC'],'new_independent_bin_readback_here':True,'proof':ev(H/'br24_readback01.json'),'unaccepted_generated_art_included':False,'new_gameplay_execution_here':False}
    q['selection_standing8_prepared'].update(integrated=True,integrated_build='BR24',runtime_by_root=ev(H.parent/'runtime/br24_selection_summary.json'))
    d=H/'prepared_chaser_base01';v=json.loads((d/'verification.json').read_text('utf8'))
    q['chaser_base13_prepared_scope']={'refs':list(range(162,175)),'forms':['base','fourth'],'candidate':ev(d/'PL00_U.ARC'),'proposal':ev(d/'proposal.json'),'input_lock':ev(d/'INPUT_LOCK.json'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'verification':ev(d/'verification.json'),'author_visual_review':ev(d/'author_visual_review.json'),'sequence':ev(H/'chaser_base_sequence01/report.json'),'browser':ev(H/'chaser_base_sequence01/browser_verification.json'),'directory_native':ev(H.parent/'zero_audit/shibuki_chaser13_directory_native01/report.json'),'storage_only_refs':v['storage_only_refs'],'new_layers':65,'new_partials':416,'storage_partials':512,'candidate_frozen':False,'independent_static_pending':True,'root_final_art_pending':True,'integrated':False,'runtime_verified':False,'status':'고정은행 새13+기존16 저장순열734B. 재현3회/거부16·전체508 원directory/MIPS 통과, 정적독립/루트 최종 검토 대기. 미동결 후보를완료수에넣지않음.'}
    q['next_generation']={'forms':['ultimate_before','ultimate_after'],'in_progress_refs':[162,166],'input':ev(H/'chaser_ultimate_inputs01/input.json'),'status':'별개 Ultimate 체이서 첫2자세4표시 입력3판 실제열람. 이미지 호출 전.','frozen':False,'arc_written':False,'all_forms_done':False,'unchanged_blocked':'Ultimate135 거부 편집은 재시도하지 않고 부모 유지'}
    for r in q['references']:
        if 162<=r['ref']<=174 and r['form']in('base','fourth'):r['in_progress_unapplied_art']=q['chaser_base13_prepared_scope']
        if r['ref']in(162,166)and r['form'].startswith('ultimate'):r['in_progress_unapplied_art']=q['next_generation']
    write(H/'fullform_ledger35.json',q)
    keys=json.loads((H/'unique_art_keys34.json').read_text('utf8'));keys.update(scope='동결PL004fe717/PL021f271의 표시키. BR24실제재독출/체이서3e11 미동결/Ultimate입력은 따로 기록. 원화수나 완료율 아님.',source_ledger=ev(H/'fullform_ledger35.json'),integration=q['active_integration'],next_unfrozen_art=q['next_generation'],prepared_chaser=q['chaser_base13_prepared_scope'],selection_copy_candidate=q['selection_standing8_prepared']);write(H/'unique_art_keys35.json',keys)
    print(json.dumps({'ledger':ev(H/'fullform_ledger35.json'),'keys':ev(H/'unique_art_keys35.json'),'readback':ev(H/'br24_readback01.json')}))
if __name__=='__main__':main()
