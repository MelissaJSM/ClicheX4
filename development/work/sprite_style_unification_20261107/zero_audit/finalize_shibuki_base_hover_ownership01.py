"""독립 읽기 결과/직접 열람을 별도 파일에 결속. 원자원 수정 없음."""
from pathlib import Path
import hashlib,json
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;O=D/'shibuki_base_hover_ownership01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(R).as_posix()
def write(name,data):
 p=O/name;assert not p.exists(),p
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return p
r=json.loads((O/'report.json').read_text(encoding='utf8'))
assert sha(O/'report.json')=='4a09339f0f6e270c89d75963c9676b38fdc896abe51abd4ecb8bb302fe5191af'
for p,h in r['inputs'].items():assert sha(R/p)==h,p
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
for row in r['code_ranges']:
 p=O/(row['name']+'_mips.txt');assert not p.exists()
 p.write_text('\n'.join(f'{i.address:08x}: {i.mnemonic:<8} {i.op_str}' for i in md.disasm(bytes.fromhex(row['bytes']),row['start']))+'\n',encoding='utf8')
summary={
 'scope':'시부키 PL00 기본/포스 호버221..230의 기존 소유 정책과 정합 기준. 새 원화 수용/후보 감사 아님.',
 'report':{'path':rel(O/'report.json'),'sha256':sha(O/'report.json')},
 'parent':{'path':r['parent'],'sha256':r['parent_sha256']},
 'runtime_entry':[
  '원US player_check_hover 0x8003751c는 player+A7의 bit8과 점프입력0x80을 검사한다. 일반 호버의 기본형은 다리 아머를 소유한 mask8이며 무아머 mask0를 정상 진입 상태로 간주하지 않는다.',
  'BR28 원코드와 현재36d4의 호버50층/raw/조립 일치를 확인했다. 수용된 아머 wrapper의 engine+37=0 분기는 player+A7를 그대로 쓴다. PL00에는 Ultimate 전용217..230 강제15를 적용하지 않는다.',
  '본체0 후 부분층은8→5→7→6 순으로 그린다. 비트8/1/4/2가 각각 bank8/5/7/6을 선택한다. 5/6/8은 CLUT16,7은 팔종류에 따라16/32이다.',
  '원상태0x21/air_action4, 시작시간180 및 이동/정지 애니메이션21..26을 유지한다. 사격 애니메이션은+0x70인133..138이며 자세/타이밍 관계를 변경할 근거가 없다.'
 ],
 'new_layer_ownership_guidance':[
  {'layer':0,'role':'공통 본체 및 사격의 총열/공통 손','constraint':'현재221/223은 상체만 있고 다리는8에 있다.225/227/229의 기존0에 일부 하체 밑그림이 있지만8이 덮는다.0만 전신으로 평가하거나 PL02 upper0/lower5를 이식하지 않는다.'},
  {'layer':5,'role':'머리 옆 장식/머리카락 아머 영역','constraint':'현재 각 자세78px의 머리 옆 부분층이다. 새 공통 얼굴/머리 형태를0에 두고 머리 파츠가 선택할 의상 영역을5에 배정한다.하체 전체층이 아니다.'},
  {'layer':6,'role':'몸통 의상','constraint':'기본 몸통과 포스 몸통 차이를 선택한다. 다리/손 전체를 임의로 소유시키지 않는다.'},
  {'layer':7,'role':'팔/커프 의상','constraint':'사격 전후 변화가 있는 부분층이며 armtype1/2의 팔레트 차이도 검증한다. 총·손 색을 아머색으로 바꾸지 않도록 각 마스크의 실제RGBA를 검사한다.'},
  {'layer':8,'role':'호버의 공통 다리/신발','constraint':'진입 필수 bit8이다. 각5쌍의8층과 그 점유영역 실제RGBA는 전후 및 mask8..15에서 exact다. 두 폼의 발/종아리를 독립 생성한 모양으로 다르게 두면 기존 정책과 달라진다.'}
 ],
 'pairs':[{'refs':p['refs'],'head5_torso6_legs8_exact':True,'body0_and_arms7_differ':True,'lower8_all_masks_and_pair_RGBA_exact':p['lower8_footprint_RGBA_all_valid_masks_and_shot_exact'],'lowest_y':p['first_mask8_lowest_y']}for p in r['pairs']],
 'raw_shared_groups':[{'refs':x['raw_owners'],'tiles':x['tile_count']}for x in r['frames']if x['ref']%2],
 'composition_scope':'221..230의 현재0/5/6/7/8 실제레코드에 비대상 소비자는 없다. 향후 다른 머리 레코드를 재사용하는 새 패커의 공유관계는 별도 검증해야 한다.',
 'jet_constraints':{
  'origin':'visual0x21는 플레이어 X/Y/facing을 그대로 사용한다. bank12/static0x10206, CLUT0x7802. 새 발은 이 고정 원점을 기준으로 세 위상 모두 검사한다.',
  'source':'원US PL00/PL02/현재PL00 15프레임·30파트의 의미 조립과 소비504..509 전체256nibble 타일이 exact다. 물리 record_offset이 같다는 주장은 아니다.',
  'pairs_to_frames':{'221/222':[0,1,2],'223/224':[3,4,5],'225/226':[6,7,8],'227/228':[9,10,11],'229/230':[12,13,14]},
  '229_230_reference':'현재 하체8 최저Y19. jet12 왼효과 bbox[-10,13,2,23), 오른효과[2,19,14,29). 왼효과는 하체8에13px 겹치고 오른효과와의 최소Chebyshev거리는1이다.13/14도 왼겹침17/22px·오른거리1. 전체 하체 최소거리이므로 개별 발목/뒤꿈치가 모두 정확하다는 판정은 아니다.',
  'acceptance':'최저발Y만으로 두 신발의 접점을 통과시키지 않는다.221..230 각 원점과 양발 위치, 각3위상, 사격짝을 함께 검토한다. 원불꽃을 새발로 이동시키지 않는다.'
 },
 'muzzle_constraints':{
  'table':'원US와 BR28의0x8011B230+ref*2 signed x/y를 직접 대조했다. 방향1은X 부호반전. type별 추가오프셋0x80108768 중 일반type0=[0,0].',
  'direction0':{str(v['ref']):v['direction0']for v in r['muzzles']},
  'first_bullet':'원7프레임/소비전체타일/조립 exact. 첫188px의 자체 bbox[-7,-10,7,10)이며 해당 탄환 원점에 번역해 비교했다.',
  'constraint':'새 총열은 위 발사점과 실제 첫 탄환을 기준으로 정합한다. 현재 그림의 왼쪽8열/최외곽을 보존하는 것만으로 발사점 일치를 증명하지 않는다. 나나20px 권총 정본의 origin+1 규칙을 시부키 총열에 자동 적용하지 않는다.'
 },
 'limits':['원코드 읽기/정적 복원이며 새MIPS 실행·실기검증 없음.','새 root_shibuki_hover 원화의 손/발/의상 수용 여부는 이 보고에서 판정하지 않았다.','원US 정책과 현재 수용된 그림의 소유를 구분했다. 층별 현재그림이 원US 외형과 동일하다는 주장은 아니다.']
}
write('conclusions.json',summary)
observations={
 'ownership':'5개 소유판을 실제 열람.221/223 본체0은 허리 아래가 없고8이 양폼 하체를 제공한다.5는 머리 옆 장식,6은 몸통,7은 커프/팔,8은 신발 포함 하체로 읽힌다.225/227/229도8 선택 뒤 양폼 신발 형태가 같다.',
 'jets':'5개 불꽃판을 실제 열람.221/223은 두 갈래 신발 주변,225/227은 겹친 하체 아래,229는 굽힌 하체 뒤와 아래 두 불꽃으로 읽힌다.229의12위상에는 두 효과 사이 빈 틈이 있으며 다른 위상은 넓어진다. 이는 현재그림의 정적 기준이며 새그림의 정확성 판정이 아니다.',
 'muzzle':'5행 총구판을 실제 열람.특히222/224 현재 총열이 원발사점과 첫효과보다 화면 오른쪽에 남는 것이 보인다. 새팔을 현재 총열 끝만 기준으로 고정하면 원발사점 정합을 증명할 수 없다.226/228도 총열 윤곽과 원점은 별개로 대조해야 한다.',
 'rendering_limit':'청록 제트/황색 탄환은 위치를 분리해 보는 중립색 합성이다.원게임의 팔레트/투명도/그리기 순서를 재현한 실기 캡처가 아니다.'
}
write('visual_review.json',{'actually_viewed':True,'sheets':r['readback_sheets'],'observations':observations,'new_art_accepted':False,'runtime_verified':False})
inputs={**r['inputs'],rel(D/'read_shibuki_base_hover_ownership01.py'):sha(D/'read_shibuki_base_hover_ownership01.py'),rel(Path(__file__)):sha(Path(__file__))}
outputs={rel(p):sha(p)for p in sorted(O.iterdir())if p.is_file()}
write('READ_LOCK.json',{'inputs':inputs,'outputs':outputs,'report_initial_visual_flag':'report.json의 actually_viewed=false는 열람 전 읽기 스냅샷이다. 후속 visual_review.json에 실제11판 열람을 결속했다.','no_resource_or_art_mutation':True})
print(json.dumps({p.name:sha(p)for p in(O/'report.json',O/'conclusions.json',O/'visual_review.json',O/'READ_LOCK.json')}))
