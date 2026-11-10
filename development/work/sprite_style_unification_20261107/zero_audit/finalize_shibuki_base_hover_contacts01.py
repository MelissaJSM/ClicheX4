"""새10몸 제트·공통화 경계 읽기 마감. 입력/원화는 수정하지 않는다."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;O=D/'shibuki_base_hover_contacts01';A=W/'nana_audit/base_hover_root_art_read01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(R).as_posix()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(name,data):
 p=O/name;assert not p.exists();p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
r=read(O/'report.json');lock=read(O/'INPUT_LOCK.json');assert sha(O/'report.json')=='51897caf2527ed1ebeb0b0b861fdb5a0b561276811c7f475445388aeeadba5b0'
for p,h in lock['inputs'].items():assert sha(R/p)==h,p
peer=read(A/'report.json');assert sha(A/'report.json')=='c05059d03f59d4188a7a4fbd53b11d6bd3c2f6c1105e6768e14da650c0f662b5'
for q in peer['inputs']:assert lock['inputs'][q['path']]==q['sha256']
for q in read(A/'READER_LOCK.json')['files']:assert sha(R/q['path'])==q['sha256'],q['path']
findings=[
 {'ref':221,'observed':'새 양폼의 양발은 jet0/1/2와 이어져 읽히며 큰 추가 분리나 과도한 종아리 길이 변화는 발견하지 못했다. 새 명암은 늘었지만 양폼 하체의 색/끝점 몇 셀은 서로 다르다.','size':'최저발Y24는 기존과 같다. 전체상단은 기존−28에서−26으로2행 낮지만 이를 전신 축소나 발맞춤 문제로 단정하지 않는다.','action':'공통하체8 선정과 양폼 손/턱의 의미경계 정합을 먼저 한다. 제트를 옮길 근거는 없다.'},
 {'ref':223,'observed':'화면 왼쪽 굽힌 발과 오른쪽 뻗은 발 모두 jet3/4/5 영역과 이어진다. 새 오른쪽 발의 끝이 기존보다1행 낮게 읽히지만 큰 빈 틈이 생긴 것은 아니다.','size':'두 폼 최저발Y25, 기존Y24. 전체bbox상단도−24→−23으로1행 낮으며 아직 전신 강체이동을 권할 충분한 앵커 검증은 없다.','action':'공통8 결정 때 새 발의 같은좌표/같은색을 먼저 맞추고 원15위상을 다시 본다. 가슴앞 손과 커프는 별도 정합 대상이다.'},
 {'ref':225,'observed':'겹쳐 보이는 신발 아래의 jet6/7/8은 두 폼 모두 접한다. 새 기본 발끝이 포스보다1행 더 내려와 있으며 형태가 조금 다르다.','size':'기본최저Y21, 포스Y20, 기존Y20. 폼 전환 시 공통8인데 신발 높이가 달라지는 점은 실제 정합 대상이다.','action':'전체몸/효과를 움직이지 말고 한 새수용 하체로 공통8을 정할 때 이 차이를 해결한다. 어느 그림을 채택할지는 별도 미술 선택이다.'},
 {'ref':227,'observed':'jet9/10/11에 새 신발이 연결되며 새 큰 분리를 찾지 못했다. 하체의 굽힘/두께는 기존 포즈와 이어져 읽힌다.','size':'두 폼 최저Y21은 기존과 같다. 새 두폼 하체 외곽4셀은 서로 다르므로 아직 common8 exact가 아니다.','action':'턱/칼라1행 차이와 함께 공통 영역 정합 후 부분조합을 검토한다.'},
 {'ref':229,'observed':'보완한 높은 두 손과 짧아진 귀가 구별되며 하체는 원jet12/13/14에 이어져 읽힌다. 작은12위상의 두 불꽃 사이 빈 틈은 기존에도 존재한다. 새 오른쪽 불꽃과의 큰 추가 간격은 확인되지 않았다.','size':'최저Y19는 기존과 같다. 왼불꽃/하체 겹침13/17/22→8/12/17, 오른불꽃 최소거리1은동일. 이 수치는 각 발목 전체접점 판정이 아니라 Y>=8 하체 진단이다.','action':'현재 판만으로 뒤굽힌 신발 재생성이나 제트 이동을 요구할 근거가 없다. 공통8 적용 뒤 원점고정 세 위상을 다시 확인한다.'}
]
write('visual_review.json',{'actually_viewed':True,'input_lock_sha256':sha(O/'INPUT_LOCK.json'),'viewed_by_this_agent':r['sheets'],'view_count':11,'coverage':'원15위상×신규10몸/기존10몸 비교5판+그하체확대5판+전신비교1판','findings':findings,'limits':['청록은 원불꽃 점유와 좌표를 표시하는 중립 합성색이며 실제 CLUT/그리기 순서·게임 캡처가 아니다.','전후차이 자체를 결함으로 간주하지 않았다. 손·얼굴 두 번째 독립 의견은 Audio 보고의 별도10판 열람 범위이며 내가 그10판도 직접 보았다고 합산하지 않는다.','새 부분층/사격팔/최종ARC가 아직 없으므로 부분조합/사격짝의 접점·실기 수용은 미검증이다.']})
recommendations={
 'source_scope':'registered_neutral01/02 nearest 8몸 및 reach229_registered01 local2몸을 원점160/384창 그대로 읽음. 픽셀/원화/자원 수정·생성 없음.',
 'source_hash_lock':{'path':rel(O/'INPUT_LOCK.json'),'sha256':sha(O/'INPUT_LOCK.json')},
 'boundary_policy':[
  {'layer':0,'recommendation':'공통 얼굴/맨손과 기본 몸체의 기준. 높은221/229 손은 머리 위 Y에 있어도 손/커프 의미 영역이며 큰머리사각형5에 함께 넣지 않는다. 공통 얼굴·손은 새원화에서 정한 한 형태를 사용하고 옛얼굴/손으로 되돌리지 않는다.'},
  {'layer':5,'recommendation':'선택 머리장식/머리 옆 의상 영역. 현재 머리5 bbox는221[2,−22,9,−8),223[0,−18,7,−4),225[1,−19,8,−5),227[0,−18,7,−4),229[3,−21,10,−7). 이는 기존 범위 참고이며 새머리를 강제로 같은 사각형에 자르라는 뜻이 아니다.'},
  {'layer':6,'recommendation':'몸통/상의·칼라. 얼굴 공통화 뒤 턱/흰칼라 연결과 허리의 드리운 옷자락을 검사한다. 의상 차이를 숨기기 위해 다리나 손 전체를 몸통으로 배정하지 않는다.'},
  {'layer':7,'recommendation':'팔 의상/커프. 피부의 단일 밝은색만 손 전체로 간주하지 말고 실제 새 피부그늘/커프의 가림 경계를 함께 정한다.225 오른손1행/1열 차이,223 작은 가슴앞 손,229 오른손목이 우선검토 영역이다.'},
  {'layer':8,'recommendation':'다리 아머 bit8은 호버 진입 필수이며 기본mask8와포스15에 같은 신발/다리를 그려야 한다. 현재등록 두전신의 하체를 그대로 별개로 둘 수 없다. 한 새수용 하체를 CLUT16 공통8로 만들고 모든 마스크8..15 및 사격짝에 유지하는 것이 기존 정책과 맞는다.'}
 ],
 'lower_boundary_reference':{'221':4,'223':7,'225':6,'227':6,'229':5,'meaning':'기존layer8의최상단Y이며 새층의 고정수평절단선이 아니다. 새 허벅지/상의끝/가림 경계를 의미영역으로 선택해야 한다.'},
 'palette_constraint':{'opaque_exact_base_to_fourth_RGB_mapping':[[13,9]],'meaning':'입력base_legs전신은CLUT0,Fourth전신은CLUT16 양자화이다. 피부13↔9 외에는 불투명 동일RGB 매핑이 없으므로 전체색인 복사나 raw색인동일성을 공통형상 검사로 사용하지 않는다. 얼굴/손과 다리의 공통층 배정에는 해당 층의 실제 팔레트 역할도 필요하다.'},
 'form_difference_metrics':{'source':rel(O/'report.json'),'meaning':'Y>=8 alpha차5/5/5/4/1은 직접측정한 외곽 차이다. RGBA차187/213/126/128/90에는 팔레트/명암 차이가 섞이며 전부 기하결함이나 layer8 최종차이로 계산하지 않는다.'},
 'confirmed_size_items':{'223':'양폼발끝1행낮음','225':'기본발끝이포스보다1행낮음','221_229':'전체상단2행낮지만 손/귀/머리 의미에 의한 차이와 전신 크기를 구분해야 함','no_forced_global_scaling':'이판에서전신과대생성이나공통축소필요를확정하지않았다.'},
 'peer_face_hand_read':{'path':rel(A/'report.json'),'sha256':sha(A/'report.json'),'reader_lock':{'path':rel(A/'READER_LOCK.json'),'sha256':sha(A/'READER_LOCK.json')},'summary':peer['summary'],'scope':'Audio가실제로본10판/피부RGB성분측정. 초기양폼index9가정 진단은배제하고v2만사용.'},
 'next_acceptance_checks':['공통얼굴/손/하체를정한후0/5/6/7/8의각선택과순서를읽어부분아머연결확인','원15jet의좌표/전체타일유지와신규5사격짝의동일하체확인','총구5좌표/원첫탄환과새팔접점은사격원화후별도확인','최종ARC의고정범위/비대상/원MIPS/재현과실기는후속단계'],
 'new_MIPS_or_gameplay':False,'art_or_resource_mutation':False,'final_art_acceptance_claimed':False
}
write('conclusions.json',recommendations)
for p,h in lock['inputs'].items():assert sha(R/p)==h,p
inputs={**lock['inputs'],lock['reader']['path']:lock['reader']['sha256'],rel(Path(__file__)):sha(Path(__file__)),rel(A/'report.json'):sha(A/'report.json'),rel(A/'READER_LOCK.json'):sha(A/'READER_LOCK.json')}
outputs={rel(p):sha(p)for p in sorted(O.iterdir())if p.is_file()}
write('READ_LOCK.json',{'inputs':inputs,'outputs':outputs,'report_visual_flag':'report는열람전 스냅샷이며후속visual_review에실제11판열람결속','source_mutation':False})
print(json.dumps({p.name:sha(p)for p in(O/'report.json',O/'conclusions.json',O/'visual_review.json',O/'READ_LOCK.json')}))
