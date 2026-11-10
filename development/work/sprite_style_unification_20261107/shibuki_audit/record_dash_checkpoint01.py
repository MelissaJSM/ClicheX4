"""새 대시 원화2페이지와 공중22검사완료 상태를 혼동 없이 기록한다."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def item(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    d=H/'dash_detail_inputs02';p=d/'prompt_used.txt';need(not p.exists(),'Receipt exists');p.write_text((d/'prompt.txt').read_text('utf8').strip()+'\n','utf8')
    need(sha((d/'generated.png').read_bytes())=='e7fa7a7e6a454309e7728a658a9ae840d7522a5cf7c60bf5c939eee8d9271f11','Changed second page')
    write(d/'generation_receipt.json',{'tool':'builtin image_gen','source_saved_from':'<LOCAL_PATH>','workspace_art':item(d/'generated.png'),'prompt':item(p),'inputs':[item(q)for q in(d/'page02_poses.png',d/'accepted_style.png',d/'generated_first_page.png')],'original_sources_modified':False})
    images=[H/f'dash_detail_native02/{form}_comparison.png'for form in('base','fourth')]+[H/f'dash_detail_contacts01/{form}_comparison_{n:02}.png'for form in('base','fourth')for n in(0,1)]
    write(H/'dash_detail_contacts01/visual_review.json',{'actual_view_image':[item(p)for p in images],'native_displays':12,'review':'새귀안쪽/머릿결·소매주름·신사기본옷과검보라포스의상분리가구형보다명확하다. 실제원화색상표본을복구한금색눈이각자세에서읽힌다. 각신체관절연결에서새목/허리단절은찾지못했다.','limits':'아직공통머리·포스장식의소유정합/16부분마스크/사격·총구·속도선패킹은미완료. 79는구형대비머리최고점4px낮으며총높이만으로결함단정하지않고다음81·83과연속자세검토를해야한다. 전체작업·사용자수용·실기완료아님.','root_visual_acceptance':False,'resource_written':False,'runtime_verified':False})
    independent=ROOT/'work/sprite_style_unification_20261107/zero_audit/shibuki_ultimate_air_independent.json'
    need(sha(independent.read_bytes())=='7eef88f19b48524eeecbf32a1259443f931c1ce5a1fedf6a6458e3bd2c7ccab0','Independent report changed')
    need(sha((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes())=='3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7','Air candidate changed')
    write(H/'dash_work_checkpoint01.json',{'ultimate_air22':{'candidate':item(H/'prepared_ultimate_air01/proposal.json'),'archive':item(H/'prepared_ultimate_air01/PL02_U.ARC'),'independent':item(independent),'own_visual_review':item(H/'ultimate_air_final_visual_review01.json'),'frozen_for_integration':False,'pending':'루트원MIPS/GPU와최종8재독출판미술검토. 통과알림후FROZEN생성;현시점게임미적용.'},'dash_audit':{'80displays_12sheets':item(H/'dash_followup_audit01/visual_review.json'),'original_streak_readback':item(H/'dash_speed_streak_audit02/report.json'),'streak_visual':item(H/'dash_speed_streak_audit02/visual_review.json')},'dash_new_art':{'body_refs':[67,69,71,75,77,79],'forms':['base','fourth'],'first_page':item(H/'dash_detail_inputs01/generated.png'),'second_page':item(H/'dash_detail_inputs02/generated.png'),'contact_registration':item(H/'dash_detail_contacts01/report.json'),'actual_visual':item(H/'dash_detail_contacts01/visual_review.json'),'archive_prepared':False},'next_steps':['새기본/포스6자세의공통머리·의상별장식/팔/다리소유를분리하고기본도트노출을검사한다.','대시기본/포스81·83및공중대시93·94의서로다른2자세원화입력을준비한다. 사격짝으로오인하지않는다.','새사격팔과기존수용총열을원총구에맞추고73/74속도선54픽셀·가림순서를보존한다.','Ultimate전후대시전체20은아직새원화미제작. 기존후폼73/74의효과밖다리/팔30·56픽셀차이와효과11·12픽셀차이는새몸+원속도선으로동기화할대상.'],'remaining_other_groups':'기본/포스이동3..32및모든폼기타희귀모션·피격·Ultimate사다리/등장/승리귀환/호버/탑승등기존전수장부잔여유지. 대시원화12표시를전체완료로집계하지않음.','game_bin_pointer_saves_modified':False})
    print({'checkpoint':str(H/'dash_work_checkpoint01.json'),'dash_native_art':12,'air_prepared_displays':44})
if __name__=='__main__':main()
