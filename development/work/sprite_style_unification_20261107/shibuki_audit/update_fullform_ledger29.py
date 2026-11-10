"""BR22 통합과 서서 사격40층 미패킹 상태를 별도 장부로 남긴다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger29.json').exists(),'새 장부 필요')
    q=json.loads((H/'fullform_ledger28.json').read_text('utf8'));keys=json.loads((H/'unique_art_keys28.json').read_text('utf8'))
    q['active_integration'].update(build='sprite_style_unification_20261107_v22',bin_sha256='54e53da83b0255e6123dc3c9d6ffeab867bc5201107b1a0ed89c798038739e99',integration_reported_by='root 통합/원MIPS 보고 및 docs/STATUS.md, 이 장부 작성에서 BIN 새 재추출은 하지 않음',PL00_sha256=q['current_candidates']['PL00_U.ARC']['sha256'],PL02_sha256=q['current_candidates']['PL02_U.ARC']['sha256'],new_special3_included=True,new_independent_bin_readback_here=False)
    for c in q['current_candidates'].values():c.update(integrated=True,integrated_build='BR22');c.pop('integration_planned_by_root',None)
    q['standing_special3_frozen_scope']['integration']=True
    sources=['standing_fire_native02/report.json','standing_fire_followthrough_native01/report.json','standing_fire_recovery_native02/report.json','standing_fire_modules_probe02/report.json','standing_fire_layers_probe02/report.json','standing_fire_targets_probe01/manifest.json','standing_fire_capacity03/report.json','standing_fire_shared01/report.json','standing_fire_tileorder01/report.json']
    q['next_generation']={'in_progress_refs':list(range(85,93)),'forms':['base','fourth'],'new_body_keys':[85,86,87,89,90,91,92],'generated_form_images':14,'derived_ref88_original_effect_pixels':83,'target_layers':40,'evidence':[ev(H/p)for p in sources], 'status':'새 원화/40층 미패킹 후보. 첫 고정은행32타일배치가2,140B 초과하며 동일원화2쌍공유+물리순서로730B 절감 시험, 여전히1,410B 부족. 미완료 부분조합/발접점 검토와 압축조사 중. ARC 미생성.', 'ultimate85_92':'새원화 아직 없음','unchanged_blocked':'Ultimate135 도구 거부 국소편집은 재요청하지 않고 부모 유지','frozen':False,'arc_written':False,'all_visual_review_complete':False}
    q['priority_next'][0]['why']='85..92 기본/포스 새7몸체14원화 및40층, 원88효과83픽셀 보존 후보의 패킹·부분검토 진행. Ultimate85..92는 이후 별도 의상 제작 필요.'
    for r in q['references']:
        if r['ref']in(95,96,97):r['decision']='95/97 새 상세원화·96 x+1 파생, 독립/원MIPS/부분/원표/루트16판 검토 후 동결되어 BR22 통합. 새 실기/전체 수용 별도.'
        if r['ref']in range(85,93)and r['form']in('base','fourth'):r['in_progress_unapplied_art']=q['next_generation']
    q['full_art_unification_complete']=False;write(H/'fullform_ledger29.json',q)
    keys.update(scope='현재 BR22에 통합된 동결 PL00fdba/PL0226fd 네폼 표시 기준. 85..92 새 미패킹 원화는 품질완료 집계에 넣지 않음.',source_ledger=ev(H/'fullform_ledger29.json'),candidates=q['current_candidates'],integration=q['active_integration'],next_unfrozen_art=q['next_generation'])
    write(H/'unique_art_keys29.json',keys);print(json.dumps({'ledger':ev(H/'fullform_ledger29.json'),'keys':ev(H/'unique_art_keys29.json'),'counts':keys['counts']['unique_key_status_counts']}))
if __name__=='__main__':main()
