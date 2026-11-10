"""실제 생성/열람과 아직 남은 파츠 검증 범위를 구분해서 기록한다."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    rows=[]
    for page in range(1,5):
        d=H/f'air_shot_inputs02/page{page:02}';src=d/'generated.png';prompt=d/('prompt_used.txt'if(d/'prompt_used.txt').exists()else'prompt.txt')
        rows.append({'page':page,'path':src.relative_to(H).as_posix(),'sha256':sha(src),'prompt':prompt.relative_to(H).as_posix(),'prompt_sha256':sha(prompt),'status':'세 팔 오류로 반려, 별도 국소 교정본 사용'if page==2 else'원화 생성 완료, 신규 팔만 국소 등록','source_is_not_final_game_asset':True})
    retry=H/'air_shot_extra_hand_retry01';v=json.loads((retry/'inputs.json').read_text('utf8'));v.update(problem='새 발사팔 외에 기존 들린 앞팔이 남아 세 팔로 나온 생성 오류. 올바른 두 팔 참조로 국소 재생성했다.',generation_started=True,generation_completed=True,generated_sha256=sha(retry/'generated.png'),generated_file='generated.png',imagegen_mode='builtin',visually_two_arms_in_six_source_poses=True,native_registered_candidate='air_shot_arms_registered06',game_written=False);save(retry/'inputs.json',v)
    data={'rows':rows,'local_retry':{'path':(retry/'generated.png').relative_to(H).as_posix(),'sha256':sha(retry/'generated.png')},'native_sources':'air_shot_native_probe02/source.json','registered_candidate':'air_shot_arms_registered06/registration.json','source_pages_seen':4,'regenerated_anatomy_page_seen':1,'registered_form_reference_count':22,'body_reference_count':22,'native_viewed_sheets':['air_shot_arms_registered04/base_comparison_00.png','air_shot_arms_registered04/base_comparison_01.png','air_shot_arms_registered04/fourth_comparison_00.png','air_shot_arms_registered04/fourth_comparison_01.png','air_shot_arms_registered06/base_comparison_02.png','air_shot_arms_registered05/base_comparison_03.png','air_shot_arms_registered05/fourth_comparison_02.png','air_shot_arms_registered05/fourth_comparison_03.png'],'remaining':['포스 Head 단독 파츠에서 기본 빨간 꽃 잔류를 막는 소유 영역 정합','부분 파츠 16조합×양쪽 팔 전수 미술 검토','새 몸체/사격 공유 32타일과 고정 은행 경계 패킹','실제 재독출·원래 MIPS/GPU 검증','실제 게임 검증'],'not_all_sprite_unification_complete':True,'game_or_current_bin_changed':False}
    save(H/'air_shot_status.json',data)
    print('recorded',len(rows),'source pages; final resource not written')
if __name__=='__main__':main()
