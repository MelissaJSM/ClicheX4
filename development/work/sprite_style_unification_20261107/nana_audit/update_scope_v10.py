"""RN17 후폼 실기와 다음 피격 원화 진행을 이전 불변 장부 뒤에 연결한다."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent;ROOT=N.parents[2]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rec=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}
def main():
    old=N/'scope_summary_v9/manifest.json';j=json.loads(old.read_text('utf8'));out=N/'scope_summary_v10';out.mkdir(exist_ok=False)
    j['previous_immutable_manifest']=rec(old)
    j['scope']='v9 불변 유지. RN17 Ultimate 라이징 후폼 실기 증거와 기본/포스 피격 첫4 원화 진행을 연결한다. 전체 미술 완료율이 아니다.'
    r=ROOT/'work/sprite_style_unification_20261107/runtime/nana_ultimate_rising17_summary.json'
    runtime=json.loads(r.read_text('utf8'))
    assert runtime['new_asset_sha256']=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
    j['root_rn17_ultimate_rising_runtime']={**rec(r),'scope':'루트 새부팅/RN17 후폼만. actual351/WebP351·27고유참조, 새7 RAM/GPU 확인. 12판 실제열람 추가확정절단 없음. 전폼·부분전수실기 아님.',
        'review':rec(ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint76.json')}
    j['root_vehicle_hover_review']['nana_display_reference_form_pairs']=204
    j['root_vehicle_hover_review']['nana_viewed_sheets']=11
    j['root_vehicle_hover_review']['whole_two_x_characters_reference_form_pairs']=408
    j['root_vehicle_hover_review']['whole_two_x_characters_viewed_sheets']=22
    j['root_vehicle_hover_review']['count_note']='408표시/22판은 두 X 캐릭터 합계. 나나 단독은51ref×4폼=204표시/11판.'
    p=j['current_production'];p['stage']='first_four_sources_fixed_registered_geometry_review'
    p['generation']=rec(N/'hurt_repaint/first_v1/generation.json')
    p['registration']=rec(N/'hurt_repaint/first_registered_v1/registration.json')
    p['next_source_refs']=[233,234];p['native_prepared_arc']=None
    p['limits']='기본/포스106/110 네 원화만 고정셀 등록. 기존 감긴눈과 새 열린눈 차이 기록, 효과/양폼 공통층·패킹 미완료. 다른 모션 및 Ultimate 피격은 제작 완료 아님.'
    j['reviewed_now']=['hurt_repaint/first_v1/generated.png','hurt_repaint/first_registered_v1/comparison_1.png','hurt_repaint/first_registered_v1/comparison_2.png']
    j['frozen_reference_count_unchanged']=True
    p=out/'manifest.json';p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'manifest':str(p),'sha256':digest(p)}))
if __name__=='__main__':main()
