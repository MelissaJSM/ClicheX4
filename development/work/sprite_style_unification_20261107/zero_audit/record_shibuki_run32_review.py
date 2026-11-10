from pathlib import Path
import hashlib,json
D=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
np=D/'shibuki_run32_directory_native01/report.json';n=json.loads(np.read_text('utf8'))
# Terminology-only correction. Frame161/190 are absent from this traced table,
# which does not establish that they are reserved or unreachable.
old='native_player_wrapper_then_reserved_frame_fixture';new='native_player_wrapper_then_frame_not_in_traced_table_fixture'
if old in n['stats']:n['stats'][new]=n['stats'].pop(old)
for row in n['references']:
 if row['pointer_origin']==old:row['pointer_origin']=new
n['limits'][2]='모든 효과 및 추적한144표에 없는105/161/190 ref의 frame byte는 주소 초기화 후 독립시험 입력이다. 사용하지 않는그림 또는 실제게임순서라는 판정이 아니다.'
np.write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n','utf8')
p=D/'shibuki_run32_independent01/report.json';r=json.loads(p.read_text('utf8'))
ROOT=Path(__file__).resolve().parents[3]
for row in r['readback_sheets']:assert sha(ROOT/row['path'])==row['sha256']
r['native_directory_report_sha256']=sha(np)
r['actual_visual_reviewed']=True
r['visual_review']={'reviewer':'hud_checkpoint','method':'view_image로 독립 readback_00..07 여덟 판 전부 열람',
 'coverage':'기본/포스 1..32 전체, 이전그림·새그림·대기0을 같은원점/4배로 비교',
 'observations':['새 이동의 머릿결·옷주름·부츠 명암이 이전의 넓은 단색면보다 대기 상세에 가까워졌다.',
 '서서사격2의 소매~몸통과 새32참조의 목·손목·무릎·발목에서 정적 판으로 확정할 새 단절을 찾지 못했다.',
 '포스1은 실제 수용대기0과 같아졌고, 양폼의 이동/사격 짝 세부가 서로 이어진다.'],
 'limits':['원순서 재생과 실제 게임의 속도·충돌·부분VRAM 이력은 이 정적 미술판독에 포함하지 않는다.','root 미술수용·사용자수용과 별도로 기록한다.']}
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'native':sha(np),'independent':sha(p)}))
