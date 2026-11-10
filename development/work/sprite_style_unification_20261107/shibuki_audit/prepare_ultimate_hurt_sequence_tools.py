"""기본형 검토기를 복제해 Ultimate 전후 원표 표시 검토기로 한정한다."""
from pathlib import Path
H=Path(__file__).resolve().parent

def main():
    p=H/'review_ultimate_hurt_sequence.py';assert not p.exists()
    s=(H/'review_shibuki_hurt_sequence.py').read_text('utf8')
    s=s.replace('hurt_base_sequence01','ultimate_hurt_sequence01').replace('prepared_hurt_base01/PL00_U.ARC','prepared_ultimate_hurt02/PL02_U.ARC').replace('87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b','b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94')
    s=s.replace("(('base',0),('fourth',15))","(('before',15),('after',0))").replace("ims['base_'","ims['before_'").replace("ims['fourth_'","ims['after_'")
    s=s.replace('왼쪽 기본·오른쪽 포스.','왼쪽 획득 전 재킷·오른쪽 획득 후 수영복.').replace('109는 원PL00 정책대로 기본106의 실루엣입니다.','109는 각 의상106의 실루엣이고,112..114는 기존 PL02 정책대로 공통 재킷110의 효과 실루엣입니다.')
    p.write_text(s,'utf8')
    p=H/'check_ultimate_hurt_browser.py';assert not p.exists()
    s=(H/'check_shibuki_hurt_browser.py').read_text('utf8').replace('hurt_base_sequence01','ultimate_hurt_sequence01').replace("((0,'base'),(96,'fourth'))","((0,'before'),(96,'after'))")
    p.write_text(s,'utf8')

if __name__=='__main__':main()
