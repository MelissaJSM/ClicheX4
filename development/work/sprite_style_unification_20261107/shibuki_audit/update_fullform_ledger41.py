"""BR30 실제 재추출과 작은머리19 준비 후보를 분리해 기록한다."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.c01_audio_build import read_disc
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger41.json').exists(),'새 장부 보호');q=json.loads((H/'fullform_ledger40.json').read_text('utf8'));u=json.loads((H/'unique_art_keys40.json').read_text('utf8'));bp=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v30/shibuki_riko.bin';h=hashlib.sha256()
    with bp.open('rb') as f:
        for block in iter(lambda:f.read(8388608),b''):h.update(block)
    need(h.hexdigest()=='ccdf6058c2f105057dbb105c71988d683ffca604492b60c665e5f2eab2f69875','BR30 hash')
    expected={'PL00_U.ARC':'36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e','PL02_U.ARC':'3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba','ST0E_U1.ARC':'47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'};actual=read_disc(bp,tuple(expected))[0];need({n:sha(b) for n,b in actual.items()}==expected,'BR30 재추출');write(H/'br30_readback01.json',{'bin':ev(bp),'resources':expected,'actual_disc_readback':True,'new_gameplay_execution_here':False})
    q['previous_ledger']=ev(H/'fullform_ledger40.json');q['active_integration']={'project':'ver_buki_riko','build':'sprite_style_unification_20261107_v30','bin_sha256':h.hexdigest(),'PL00_sha256':expected['PL00_U.ARC'],'PL02_sha256':expected['PL02_U.ARC'],'ST0E_sha256':expected['ST0E_U1.ARC'],'proof':ev(H/'br30_readback01.json'),'new_independent_bin_readback_here':True,'unaccepted_generated_art_included':False,'new_gameplay_execution_here':False};q['current_candidates']['PL02_U.ARC'].update(integrated=True,integrated_build='BR30');q['hover_frozen_ultimate'].update(integrated=True,integrated_build='BR30',status='3f168 동결을 BR30에서 직접 재추출하여 일치 확인. 실제게임실기는 Root별도 범위.')
    d=H/'prepared_vehicle_head_ultimate01';tiny={**q['tiny_vehicle_head_pending'],'candidate':ev(d/'PL02_U.ARC'),'input_lock':ev(d/'INPUT_LOCK.json'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'verification':ev(d/'verification.json'),'native':ev(H/'vehicle_head_ultimate_components_native_checks.json'),'author_visual':ev(d/'author_visual_review.json'),'original_tables':ev(d/'original_sequence_read.json'),'generated':True,'packed':True,'frozen':False,'integrated':False,'status':'새머리1셀의19위치×전후38표시 후보 a0629. 13x15/눈/144px,95층/608부분/493비대상raw,3재현11거부/원MIPS19 통과. Root최종미술·독립대기. 현재19동형은수용Shibuki정책이며원US5~6고유머리복원아님. 귀사이1추가1제거 기록.'};q['tiny_vehicle_head_pending']=tiny
    for r in q['references']:
        if r['form'].startswith('ultimate') and r['ref'] in tiny['refs']:r['in_progress_unapplied_art']=tiny
    q['next_generation']={'scope':'현재 UI 즉시 추가 생성 없음. Ultimate 작은머리19 후보의 독립/최종미술 결속 대기, 기본/포스호버는Root 제작 중.','blocked_unchanged':'Ultimate135 거부 팔은 재시도하지 않고 부모 보존.','all_forms_done':False};write(H/'fullform_ledger41.json',q)
    u.update(scope='BR30 실제재추출 동결 기준. 작은머리19 a0629는 아직독립/최종검토전 별도후보이며 완료로세지않음.',source_ledger=ev(H/'fullform_ledger41.json'),candidates=q['current_candidates'],integration=q['active_integration'],tiny_heads=tiny);write(H/'unique_art_keys41.json',u);print(json.dumps({'ledger':ev(H/'fullform_ledger41.json'),'keys':ev(H/'unique_art_keys41.json'),'readback':ev(H/'br30_readback01.json')}))
if __name__=='__main__':main()
