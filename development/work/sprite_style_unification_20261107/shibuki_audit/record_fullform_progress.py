from pathlib import Path
import json
H=Path(__file__).resolve().parent
for p in (H/'FULLFORM_LEDGER.md',H/'update_fullform_ledger.py'):
 s=p.read_text('utf8').replace('시작1/2 및85~87/97은','시작1/2 및 기본/포스의85~87/97은')
 p.write_text(s,'utf8')
p=H/'findings.json';f=json.loads(p.read_text('utf8'))
f['ultimate_lowhp_pilot']['reason']='세부묘사는 개선됐으나51px로 대기47px보다 크고 정면화되었다. after19px가 before밖에 있어 불투명 오버레이 조건 미완료. 전체축소 대신3/4 피로자세·어깨각도/체형 재편집을 준비했다.'
p.write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n','utf8')
p=H/'REPORT.md';s=p.read_text('utf8');bad='## ? ? ?? ??? Ultimate ??? ???';head='## 전 폼 잔여 장부와 Ultimate 저체력 보류안'
if bad in s:s=s.split(bad)[0].rstrip()+'\n'
if head not in s:
 s+='''
## 전 폼 잔여 장부와 Ultimate 저체력 보류안

`fullform_ledger01.json`과 `FULLFORM_LEDGER.md`에4폼×237참조948슬롯을 빠짐없이 배정했다. 복원912개·빈예약36개이며, 이번 새 동결156폼별 그림과 남은 동작군552폼별 참조를 구분한다.552개 독립 원화가 필요하다는 뜻은 아니며 동일몸체·사격짝·효과 파생을 함께 처리할 범위다. 수용상세52,효과/연결72,탑승머리80은 근거를 남겨 보존 또는 조건부검토한다. 기존64주요시트 전부 실제열람 근거를 유지했고 이번에는24시트를 다시 대기와 대조했다. 모든 부분마스크를 개별 미술 수용했다고 확대하지 않는다.

Ultimate 특수·호버·체이서·라이드아머 머리와 전체 등장/승리/귀환을 장부에 포함했다. 기본/포스48새참조와 Ultimate30새참조만으로 전체완료라고 말하지 않는다. 선택18~21 누적4개가 변경되어 전체25개 중 비대상21개이며, 부모 승리 단계의 다른24개 보존 수치와 구분한다.

다음 독립 PL02 저체력120~125를 위해 기존6참조/16스텝·공유3스트림·팔레트·발접지를 수집했다. builtin 새 양의상 한페이지를 생성했지만 고정 축척으로51px/정면화가 확인되어 패킹하지 않았다. 원화의 세밀한 옷/머리 표현은 유지하며3/4피로 굽힘과47px 대기 비율을 교정하는 별도 편집 입력을 `ultimate_lowhp_edit01`에 준비했다. 게임/BIN/포인터/사용자저장은 변경하지 않았다.
'''
p.write_text(s,'utf8')
assert bad not in s
print('UTF8 progress records saved')
