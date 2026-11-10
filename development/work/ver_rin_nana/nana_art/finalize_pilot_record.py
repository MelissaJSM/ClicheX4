from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
p=ROOT/'AGENTS.md';s=p.read_text('utf8')
s=s.replace('사용자 후속 요청에 따라 두 번째 버전 제작을 시작했으며 현재 대상은 `ver_rin_nana/zero_rin`이다.','두 번째 버전의 린과 공통 통합 수용 후 현재 대상은 `ver_rin_nana/x_nana` 기준안이다.')
s=s.replace('| `ver_rin_nana` | `zero_rin` | 제로 | `rin(zero).webp` | 두 번째 버전, 현재 제작 |','| `ver_rin_nana` | `zero_rin` | 제로 | `rin(zero).webp` | 현재 제작 범위 사용자 수용 |')
s=s.replace('| `ver_rin_nana` | `x_nana` | X 기본형 | `nana(X).webp` | 두 번째 버전, 제작 보류 |','| `ver_rin_nana` | `x_nana` | X 기본형 | `nana(X).webp` | 현재 기준안 제작·검토 |')
p.write_text(s,'utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8')
a=s.index('앞선 특수기술 관련35개 단위 검사 통과.');b=s.index('\n\n## 다음 작업과 미확인',a)
s=s[:a]+'''앞선 특수기술 관련35개 단위 검사 통과. 수용 특수기술판의 [대기147 RAM/VRAM/1026픽셀 일치](../work/ver_rin_nana/live_poc/20261029T003459638537Z/verification.local.json). 최신 적용 세션은 `work/ver_rin_nana/emulator_sessions/20261029T051617976097Z`다. 공통 통합판에서 새 부팅했고 제목·선택을 관찰했다. 이전 진행·F1·카드는 `checkpoints/before_common_korean_20261029`에 보관했다. 사용자 수용 후 추가 메뉴 조작은 하지 않았다. 이전 HUD판의 새 부팅/카드 로드 검사와 그래픽만 갱신한 잔기 앞 F3 검사는 해당 이력에 구분한다. [F3 잔류 이력](RIN_HUD_THEME.md).'''+s[b:]
a=s.index('선택·저장 작은 스프라이트와 큰 선택 그림,');b=s.index('\n\n## 보호 기준',a)
s=s[:a]+'''선택·저장 작은 스프라이트와 큰 선택 그림, 헌터베이스 출발 디자인, 대화·일시정지 초상화, 기술 획득 그림과 HUD·개인 메뉴 색상, 잔기·등장/복귀 빛 및 공통 한글·이름·ClichéX4 통합을 사용자 수용했다. 블랙 팔레트·음성 정책은 미확정이다. 선택창·화자명·출격에는 아오쿠모 린/하나코 나나 풀네임, 대사 속 호칭에는 린/나나를 사용한다. 오래된 F3는 이전 그래픽과 프로그램을 복원하므로 새 부팅 검사와 그래픽 갱신 체크포인트 검사를 구별한다.

다음 대상 나나의 대기0·사격85 기준안을 [원작과 1배/4배 비교](../out/ver_rin_nana/nana_pilot_v9/review_1x_4x.png)로 준비했다. 두 자세 높이45픽셀, 원래 파츠 밖 픽셀0, 압축1226/1322·1238/1298바이트, 전체508참조 중 후보2개만 변경, 아머 타일 유지, 독립16파일 동일, 관련15단위 검사 통과. 게임에는 아직 적용하지 않았다. 나나 미술 수용, 총구/실제 섬광 연결과 모든 애니메이션은 미검증이다. [기준안·제약·다음 순서](NANA_PILOT.md).'''.replace('\n+','\n')+s[b:]
s=s.replace('그래픽 갱신 체크포인트 검증이며 새 디스크 재로딩·전송 재생 실기는 미완료다.','해당 자동 검사는 그래픽 갱신 체크포인트를 사용했다. 후속 전송 재생은 사용자 수용했고 공통 통합판은 새 부팅했다.')
s=s.replace('전체 린 UI/일러스트까지 완료로 보고하지 않는다.','이 감사만으로 미사용 참조 전체나 실기 전수를 완료로 판단하지 않는다.')
p.write_text(s,'utf8')
p=ROOT/'docs/NANA_PILOT.md';s=p.read_text('utf8');s=s.replace('독립 재생성16파일은 바이트 동일했다.','프레임 편집·압축 관련15단위 검사가 통과했다. 독립 재생성16파일은 바이트 동일했다.');s=s.replace('이미 있는 출력은 재사용을 거부한다.','추가 실행: `python -m unittest tests.test_psx_frame_edit tests.test_psx_compress` (15검사 통과).\n\n이미 있는 출력은 재사용을 거부한다.');p.write_text(s,'utf8')
print('Active scope and current records finalized.')
