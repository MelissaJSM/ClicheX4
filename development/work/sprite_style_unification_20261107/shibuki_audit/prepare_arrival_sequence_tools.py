"""검증된 표시검토기에 등장2/공유95·96 원표와 미완료135 표시를 연결한다."""
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
 p=H/'review_ultimate_arrival_sequence.py';assert not p.exists()
 s=(H/'review_ultimate_hurt_sequence.py').read_text('utf8')
 s=s.replace('ultimate_hurt_sequence01','ultimate_arrival_sequence01').replace('prepared_ultimate_hurt02/PL02_U.ARC','prepared_ultimate_arrival_partial01/PL02_U.ARC').replace('b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94','3e55b972c007731a8446c8478336c6def303e0dc5ed4ab5d6a52856471327138')
 s=s.replace('from scripts.c01_audio_build import read_disc',"SOURCE=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v18/shibuki_riko.bin'\nSOURCE_SHA='b0bc7e3105966fbca46bb28b6dd8e2ae5daf4b785cd1ffb203b0bdfde6bfcc88'\nfrom scripts.c01_audio_build import read_disc")
 s=s.replace("s['id']in range(33,38)","s['id']in(2,95,96)").replace("seq['id']not in(33,34,35)","seq['id']not in(2,95,96)")
 s=s.replace('실제 EXE의 X 표33..37과 새 피격13','실제 BR18 EXE의 X 표2/95/96과 새 등장8').replace('시부키 피격 원순서 검토','시부키 등장8 부분후보 원순서 검토').replace('새 피격13 원표 재생 검토','새 등장8 부분후보 원표 재생 검토').replace('실제 EXE 표33..37','실제 BR18 EXE 표2/95/96')
 s=s.replace('게임의 이동·충돌·넉백·무적 깜빡임·소리·상태 종료 조건은 재현하지 않습니다.','실제 등장 중 임시 아머 마스크 전환·외부상태·이동·효과객체·소리·충돌을 재현하지 않습니다. 두 의상은 고정 마스크 비교이며 인게임 전체 등장 시뮬레이션이 아닙니다.')
 s=s.replace('109는 각 의상106의 실루엣이고,112..114는 기존 PL02 정책대로 공통 재킷110의 효과 실루엣입니다.235/236은 원시부키 오라 뒤에 새234를 그립니다.','135는 미완료로 부모 그림 그대로이며 이 순서판에도 구형 자세가 남습니다.130/131은 기존 공통 실루엣,134는 원 구체 뒤 새133,136/137은 새 몸체 앞 원 번개입니다.138/139는 등장 외95/96에도 쓰이며95/96의 나머지95/96 그림은 이번 변경 대상이 아닙니다.')
 s=s.replace('id:33,pos:0','id:2,pos:0')
 p.write_text(s,'utf8')
 p=H/'check_ultimate_arrival_browser.py';assert not p.exists();s=(H/'check_ultimate_hurt_browser.py').read_text('utf8').replace('ultimate_hurt_sequence01','ultimate_arrival_sequence01').replace('counts={33:40,34:45,35:35,36:10,37:220}','counts={2:120,95:50,96:30}').replace('((33,4),(34,22),(35,5))','((2,27),(2,39),(95,4))').replace('if aid in(34,36):','if aid in(2,95,96):').replace('review.reset(33)','review.reset(2)').replace('5개 원표','3개 원표').replace('물리/무적깜빡임/소리','물리/임시아머전환/효과객체/소리')
 p.write_text(s,'utf8')
if __name__=='__main__':main()
