"""기존 검토기 형식을 재사용하되 PL00의 실제0/15 표시와 원표를 명시한다."""
from pathlib import Path
D=Path(__file__).resolve().parent;N=D.parent
s=(N/'ultimate_nova_repaint/make_native_cycle.py').read_text('utf8')
repls={
 'from prepare_targets import PARENT,REFS':'from pack_candidate import PARENT\nREFS=tuple(range(213,221))',
 "PL02_U.ARC":"PL00_U.ARC",
 "'RN39'":"'RN41'",
 "['ultimate_after']['animations']":"['base']['animations']",
 'postmask=15 if n>=217 else 0':'postmask=15',
 'ims=[old.composite(n,15)[0],new.composite(n,15)[0],old.composite(n,postmask)[0],new.composite(n,postmask)[0]':'ims=[old.composite(n,0)[0],new.composite(n,0)[0],old.composite(n,postmask)[0],new.composite(n,postmask)[0]',
 '((old,15),(new,15),(old,15 if n>=217 else 0),(new,15 if n>=217 else 0))':'((old,0),(new,0),(old,15),(new,15))',
 "'before_mask':15":"'before_mask':0",
 'OLD BEFORE / NEW BEFORE / OLD AFTER / NEW AFTER':'OLD BASE / NEW BASE / OLD FOURTH / NEW FOURTH',
 'Nana Ultimate Nova native review':'Nana base Fourth Nova native review',
 '나나 Ultimate 노바8 · ARC 재추출':'나나 기본/포스 노바 · ARC 재추출',
 '각 줄: 기존 전폼 / 새 전폼 / 기존 후폼 / 새 후폼 / 기존5층 / 새5층. 213~216은 재킷15·맨팔0, 217~220은 양폼 모두 실제 mask15다.':'각 줄: 기존 기본0 / 새 기본0 / 기존 포스15 / 새 포스15 / 기존5층 / 새5층. PL00의 실제 기본0·포스15를 유지하며 Ultimate 강제마스크 정책을 가져오지 않는다.',
 '214=213·216=215는 현재 Nana 제작정책으로 원US 섬광 복원 주장이 아니다.':'214는 새213+기존채택 원US외부124셀 효과이며 원US내부19셀까지 복원한 것은 아니다.216은 새215별칭,218/219는부모의별도에너지 그대로,220은새217 Y+1+효과다.',
 "'changed_refs':list(REFS)":"'changed_refs':[213,214,215,216,217,220]",
 '준비215→217 전환과218~220 효과루프':'준비213/215→217 전환과218~220 효과루프',
 '"""노바 원표106의 준비→돌진/효과 순서를 실제자원에서 읽어 검토한다."""':'"""PL00 노바 원표106의 준비→돌진/효과 순서와 실제기본/포스 표시를 읽는다."""'
}
for old,new in repls.items():
 assert old in s,old;s=s.replace(old,new)
p=D/'make_native_cycle.py';assert not p.exists();p.write_text(s,'utf8')
v=(N/'ultimate_nova_repaint/verify_native_cycle.py').read_text('utf8').replace('탑승 원표12개와 실제 canvas78개의 오프라인 재생을 확인한다.','PL00 노바 원표1개와 실제 canvas48개의 오프라인 재생을 확인한다.').replace('원표65~76 오프라인 canvas 재생/정지.','원표106 오프라인 canvas 재생/정지.').replace('실제게임 차량물리·입력·손잡이/페달·caller 실행 아님.','실제게임 노바물리·입력·caller·CLUT변화 실행 아님.')
p=D/'verify_native_cycle.py';assert not p.exists();p.write_text(v,'utf8')
