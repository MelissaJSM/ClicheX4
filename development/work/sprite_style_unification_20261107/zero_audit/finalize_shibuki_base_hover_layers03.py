"""실제 열람한 공통몸/부분/접점 판을 새 독립 기록에 결속한다."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
S=W/'root_shibuki_hover/body_layers_probe03';O=D/'shibuki_base_hover_layers03_read01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(R).as_posix()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(name,x):
 with(O/name).open('x',encoding='utf8')as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
r=read(O/'report.json');assert r['passed']and sha(O/'report.json')=='1e40958b92f5b4d1140336d81056cd90bf2a24f188d95adba0a2c191500b01c5'
files=read(O/'INPUT_LOCK.json')['files'].copy()
def track(p):files[rel(p)]=sha(p);return{'path':rel(p),'sha256':sha(p)}
for p,h in files.items():assert sha(R/p)==h,p
viewed=[track(S/f'{k}_{n}.png')for n in(221,223,225,227,229)for k in('comparison','partial')]
for q in r['sheets']:assert sha(R/q['path'])==q['sha256'];viewed.append(track(R/q['path']))
visual={'actually_viewed':True,'viewed_boards':viewed,'count':16,
 'observations':[
  '기존비교5·부분5·독립접점5·mask11/arm2 추가판1을 실제 열람했다. 새공통몸에서 추가 확정 팔/목/발목 절단이나 큰 전신 크기 변화는 찾지 못했다.',
  '221/229의 높은 두팔은 머리장식 선택과 분리돼 유지된다. 부분아머 선택 시 소매와 몸통의 색/외곽이 바뀌며 높은 손이 head5로 사라지지 않는다.',
  '223의 오른신발을 올린 뒤에도 발목~신발과 원불꽃의 큰 단절은 보이지 않는다. 기존 1px 낮았던 발끝은 Y24로 맞아졌으나 윗행8셀 가림을 포함한 등록이다.',
  '225는 Fourth에서 고른 하체를 두폼 모두 사용해 원형최저Y20을 유지한다.227 Y21/229 Y19 및221 Y24는 그대로다.',
  '229 옷자락(5,4)의 body6 소유를 확인했고 mask10/11에서 해당 1픽셀이 따로 떨어져 보이지 않는다.',
  '원15jet 고정원점의 접점5판에서 새 큰 간격을 찾지 못했다.229의 두 번째 제트와 하체 사이 최소1px는 부모도1px이며 모든 효과를 발에 강제로 붙일 근거는 아니다.'
 ],
 'peer_face_hand_review':{
  'observer':'/root/overhaul_audio','delivery':'협업 메시지; 새 파일은 작성하지 않음.','actually_viewed_by_peer':['223/225/227/229 comparison·partial 8파일'],
  'conclusions':['얼굴창 RGBA 차이0, 손 의미공통24/22/13/36셀 차이0, 공통창 위 아머불투명덮기0.','223 작은 가슴앞손은 커프와 이어지며 확정 절단 없음. 손창 피부7셀에는 턱이 포함되므로 손7px라고 세지 않음.','225 오른손 주피부4셀은 양폼 같은 bbox[3,-7,5,-5)로 이전위치차 해소.','227 턱은 공통, y-5/-4 차이는 body6/arm7 칼라이며 head5 덮기아님.','229 높은두주먹은 같은좌표이며 아래의 금빛커프/소매는 arm7 차이.창전체 RGBA차를 결함이나 피부차로 세지 않음.']},
 'limits':['5개 접점판의 crop은 world X[-30,25),Y[-32,31)이며 일부 긴 불꽃 꼬리는 판밖이다. 실제 전체타일/좌표보존은 기술읽기 근거와 분리한다.','청록은 원효과 점유의 중립색 정적합성이며 실제CLUT/반투명/게임실행이 아니다.','80부분조합을 수치로 검사했지만 모든80을 개별 이미지로 열람했다고 주장하지 않는다.'],
 'art_or_resource_modified':False,'new_art_generated':False,'runtime_verified':False}
write('visual_review.json',visual)
conclusion={'passed':True,'scope':'시부키 PL00 새호버 비사격5의 공통몸25층 읽기.최종패킹/사격/실기 이전 진단.',
 'report':track(O/'report.json'),'input_lock':track(O/'INPUT_LOCK.json'),'visual':track(O/'visual_review.json'),
 'source_manifest_sha256':r['manifest_sha256'],'producer_script_sha256':r['producer_script_sha256'],
 'checks':{'target_layers':25,'source_indices_and_owner_exact':True,'mask8_15_times_arm1_2':80,'all_8connected_components':1,'face_common0_RGBA_exact':True,'lower8_common_RGBA_exact_all80':True,'raised_arms_head5_overlap':0,'jet_frames_original_position':15},
 'registration_caveat':r['hand_and_registration_details'][1]['shoe_registration'],
 'policy_read':['원PL00는A7마스크를유지하고호버다리bit8이필수이므로기본8/포스15와부분8..15를검사했다.','단일Fourth CLUT16 하체8은이전정책과일치하고사격짝에도동일하체를유지해야한다.','높은팔은의미창7,얼굴/지정한피부명암창은공통0,머리장식5·몸통6·소매7의의상차이는별도이다.','새 owner5/6/7/8의실제불투명영역은서로중복없으며0underlay와의가림은의도된아머오버레이이다.'],
 'metadata_issue':'manifest 및 prepare_body_layers03.py의 shared_hand_rule 한국어 설명이 물음표로 깨져 있다. 픽셀/검사결과에 영향은 없으나 제작자가 최종출처 기록에서 실제 공통선택식을 온전한문장으로 기록할 필요가 있다.',
 'remaining':['사격5 팔/원총구와 공통하체의 동일성은 제작후 별도검사.','최종50층 ARC/공유/비대상/원MIPS/실기 검사는 아직 해당없음.','223 윗행가림8셀은 Root에게 전달했으며 미술수용을 픽셀수불변으로 대신하지 않음.'],
 'producer_functions_imported_or_called':False,'input_modified':False,'new_MIPS_execution':False,'runtime_verified':False}
write('conclusions.json',conclusion)
for p in(D/'read_shibuki_base_hover_layers03.py',Path(__file__),O/'conclusions.json'):track(p)
for p,h in files.items():assert sha(R/p)==h,p
write('READER_LOCK.json',{'files':dict(sorted(files.items())),'original_inputs_unchanged':True,'source_or_ARC_writes':False})
print(json.dumps({k:sha(O/k)for k in('report.json','visual_review.json','conclusions.json','READER_LOCK.json')}))
