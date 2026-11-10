"""85/89/90/91 미패킹 원화 실제열람과 접점 잔여를 기록한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    dst=H/'standing_fire_visual_review01.json';need(not dst.exists(),'Fresh review')
    paths=['standing_fire_native01/base_comparison.png','standing_fire_native01/fourth_comparison.png','standing_fire_sleeves_inspection01/085_grid.png','standing_fire_sleeves_inspection01/089_grid.png','standing_fire_native02/fourth_comparison.png','standing_fire_native02/sleeve_comparison.png','standing_fire_contacts_probe01/gun_modules.png','standing_fire_contacts_probe01/fourth_comparison.png','standing_fire_followthrough_native01/base_comparison.png','standing_fire_followthrough_native01/fourth_comparison.png']
    write(dst,{'actually_viewed':[ev(H/p)for p in paths],'scope':'새 기본/포스85/89/90/91 미패킹 원화 및 고정캔버스 등록 실제열람. 전체 게임 미술/실기/최종수용 아님.','observations':[
      '85/89 첫 네이티브는 머릿결·땋은머리·칼라·허리옷의 분할과 명암이 기존 단색면보다 세밀하다.',
      '85/89 첫 포스 원화의 앞소매가 흰색/붉은점으로 남은 문제를 국소 builtin 원화44ea9f8a로 다시 제작했다. 소매 좌표만 등록한 native02에서 검보라 접힘/금색 소매끝이 보이고 나머지 새 원화 및 전체 알파는 동일하다.',
      '85/89 원총열 시각 창을 다시 올린 probe는 총열 끝과 새 팔이 대체로 연결돼 보인다. 이 창은 임시 시각범위이며 독립 원파트/손·소매 소유 조사 전 정본으로 확정하지 않았다.',
      '90/91 네이티브 두 비교판은 각각의 다리 벌림/팔 방향을 유지하면서 머릿결·옷깃·부츠 윤곽이 세밀해졌다. 포스 앞팔은 처음부터 검보라 재질로 읽히고 옛 큰 흰 소매가 사라졌다.',
      '90/91 새 네 표시의 전체 바닥은 y23(배타끝)으로 동일하지만 뒤발 x범위는 원래보다 오른쪽으로1~3px 넓다. 발목과 실제 발바닥을 분리해 후속 접점 검토가 필요하다.',
      '85 새 기본 왼발과 포스 양발은 원래보다1px 높다. 전신 축소/늘림이나 옛 부츠 복사로 해결하지 않고 새 발 모듈의 접점/연속성 검토 후 결정한다.'
    ],'confirmed_unresolved':['원총열 정확 semantic 범위와 원CLUT0 공통소유','발목·발바닥 국소 정합','새 머리 공통/포스 장식·소매 소유 및16부분조합','86/87/92 개별 새원화','88 원효과83px 전체타일과 앞뒤 순서','ARC 패킹/재추출/독립/원MIPS/실기'],
    'source_relation':ev(H.parent/'zero_audit/shibuki_standing85_92_relations01/report.json'),'accepted_idle_unchanged':True,'art_deleted_for_capacity':False,'arc_written':False,'full_art_unification_complete':False})
    print(ev(dst))
if __name__=='__main__':main()
