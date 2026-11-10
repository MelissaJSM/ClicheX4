"""피격13의 승인 검토 입력과 손실 없는 물리 배치를 별도 잠금으로 연결."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write

def main():
    dest=H/'hurt_locked_inputs01';need(not dest.exists(),'Fresh lock required');dest.mkdir()
    p=H/'hurt_pack_probe06/report.json';report=json.loads(p.read_text('utf8'));need(report['passed'],'Unverified pack')
    recipe={'parent_sha256':report['before'],'candidate_sha256':report['after'],'probe_report_sha256':sha(p.read_bytes()),'groups':{str(g['refs'][0]):g['tile_permutation']for g in report['groups']},'policy':'새 후보 타일 바이트를 그대로 순열 재배치. 원효과 슬롯과 GPU 경계 슬롯은 고정.'}
    write(dest/'tile_recipe.json',recipe)
    files={}
    dirs=('hurt_inputs01','hurt_native01','hurt_native02','hurt_common_probe02','hurt_effect_probe01')
    for name in dirs:
        for f in sorted((H/name).rglob('*')):
            if f.is_file():files[f.relative_to(ROOT).as_posix()]=sha(f.read_bytes())
    sources=('prepare_shibuki_hurt_inputs.py','prepare_shibuki_hurt_page02.py','register_shibuki_hurt_probe.py','register_shibuki_hurt_page02.py','probe_shibuki_hurt_common.py','prepare_shibuki_hurt_effects.py','optimize_hurt_tile_storage.py')
    for name in sources:
        f=H/name;files[f.relative_to(ROOT).as_posix()]=sha(f.read_bytes())
    effect=json.loads((H/'hurt_effect_probe01/manifest.json').read_text('utf8'))
    for name,expected in effect['source_arrays'].items():
        f=ROOT/name;need(sha(f.read_bytes())==expected,'Independent effect source changed');files[name]=expected
    audit=ROOT/'work/sprite_style_unification_20261107/zero_audit/shibuki_hurt_sources01/report.json';need(sha(audit.read_bytes())==effect['independent_source_report_sha256'],'Independent report changed');files[audit.relative_to(ROOT).as_posix()]=sha(audit.read_bytes())
    files[(dest/'tile_recipe.json').relative_to(ROOT).as_posix()]=sha((dest/'tile_recipe.json').read_bytes())
    write(dest/'LOCK.json',{'parent_sha256':report['before'],'candidate_sha256':report['after'],'refs':report['refs'],'files':files,'source_scope':'원화2페이지·고정등록·새 공통머리 및 소유층·부모별 원효과·무손실 물리 타일 순서','pending':'원MIPS/독립 최종 reader/루트 미술 및 새 실기는 별도'})
    print(json.dumps({'lock_sha256':sha((dest/'LOCK.json').read_bytes()),'files':len(files),'recipe_sha256':sha((dest/'tile_recipe.json').read_bytes())}))
if __name__=='__main__':main()
