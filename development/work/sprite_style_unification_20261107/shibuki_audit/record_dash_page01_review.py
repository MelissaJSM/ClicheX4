"""실제로 열람한 대시 첫 페이지의 범위와 미완료를 기록한다."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,write,need
def main():
    d=H/'dash_detail_inputs01';o=H/'dash_detail_native01';source=d/'generated.png'
    need(sha(source.read_bytes())=='390a5ff9080abd924ce2c9ccb161da0b28442602bfabff51be3fe4a5b00639fe','Changed art')
    p=d/'prompt_used.txt';need(not p.exists(),'Prompt receipt already exists');p.write_text((d/'prompt.txt').read_text('utf8').strip()+'\n','utf8')
    write(d/'generation_receipt.json',{'tool':'builtin image_gen','source_saved_from':'<LOCAL_PATH>','workspace_art':source.relative_to(ROOT).as_posix(),'sha256':sha(source.read_bytes()),'prompt_sha256':sha(p.read_bytes()),'inputs':{q.name:sha(q.read_bytes())for q in(d/'page01_poses.png',d/'accepted_style.png')},'original_sources_modified':False})
    paths=[d/'page01_poses.png',d/'accepted_style.png',o/'base_comparison.png',o/'fourth_comparison.png']
    write(o/'visual_review.json',{'reviewer':'overhaul_ui','actual_view_image':{q.relative_to(ROOT).as_posix():sha(q.read_bytes())for q in paths},'native_displays_reviewed':6,'findings':['기본67/69/71은 큰 단색 머리 대신 귀 안쪽·앞머리 갈래·옆머리 흐름이 읽히며, 소매주름·치마주름·끈과 신발 명암이 대기 기준에 가까워졌다.','포스67/69/71은 검보라 소매·금색 가장자리·흰 털 장식과 망토의 층이 구형보다 분명하다. 기본의 옅은 하늘색 소매로 혼동되지 않는다.','새 양폼은 같은 웅크림 단계와 짧은 신체 비율을 유지하고, 목·허리·무릎의 새 단절은 육안으로 찾지 못했다.'], 'remaining':['포스69의 최저 발바닥은 원래보다1px 위이며 공통 골격/신발 접점 정합을 해야 한다. 다른5표시는 최저 높이 동일이나 개별 손끝·발꿈치까지 검증한 것은 아니다.','새 원화끼리 공통 머리/얼굴과 포스 장식·의상의 소유 영역을 정합한 후16부분아머×양팔을 검사해야 한다.','사격팔·원총구와73/74의 원래 속도선은 아직 제작/합성하지 않았다.','이번 원화는6표시이며 남은 대시75..84·93/94 및Ultimate전후 전체는 미제작이다.'], 'art_direction_candidate':True,'root_acceptance_received':False,'resource_packed':False,'actual_game_test':False,'all_motion_complete':False})
    print({'review':str(o/'visual_review.json'),'new_art_sha256':sha(source.read_bytes())})
if __name__=='__main__':main()
