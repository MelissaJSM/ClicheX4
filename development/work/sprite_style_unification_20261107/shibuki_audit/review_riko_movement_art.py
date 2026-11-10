"""다른 작업자의 리코 이동 후보를 실제 열람한 미술 의견만 기록한다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import write,sha,need
I=H.parent/'riko/movement_clothes14/contacts_probe01';O=H/'riko_movement_art_review01'
def main():
    need(not O.exists(),'Fresh review required');O.mkdir()
    sheets=[I/f'normal_comparison_{i:02}.png'for i in range(4)]
    write(O/'review.json',{'scope':'원화 등록/접점 후보의 정적 미술 열람. ARC 또는 연속 실제 플레이 검증이 아니다.','actual_viewed_sheets':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in sheets],'refs':[3,4,7,9,10,11,12,13,15,16,17,18,19,20],'art_review_passed':True,'observations':['3/4의 소매와 허리, 뒤로 흐르는 옷단은 기존 큰 흰 면보다 구조가 명확해졌고, 머리와 목이 분리되어 보이지 않는다.','7~13은 굽힌 무릎/지면에 닿는 발에 따라 몸 높이가 달라지는 정상 자세다. 허리부터 허벅지·부츠까지 이어지는 색면을 읽을 수 있다.','15/16의 하체 상향 등록 후 앞쪽 허벅지가 옷단에 일부 더 가려지지만, 정적 비교에서 허벅지가 잘리거나 부츠가 떨어진 틈은 보이지 않는다. 좁은 피부 띠와 겹치는 흰 옷단은 유지되어 연결을 해석할 수 있다.','17~20의 뒤로 접힌 다리/옷단에 명암이 생겼고, 몸통 폭이나 머리 크기가 갑자기 얇아지거나 커지는 확정 결함은 이 4장에서는 보이지 않는다.'],'limits':['이번 기록은 정상색 4장만 직접 열람한 결과다. 블랙 팔레트는 미열람이다.','15/16 앞 허벅지의 노출 면이 줄어든 인상은 연속 재생으로 다시 볼 항목이다. 이 정적 열람으로 보행의 부드러움까지 합격 처리하지 않는다.','공유 별칭·원래 접지·머리316px 및 비대상 보존은 이 미술 검토에서 새로 계산하지 않았다. 독립 기술 검증 또는 제작 기록과 구분한다.'],'game_written':False})
    print(O/'review.json')
if __name__=='__main__':main()
