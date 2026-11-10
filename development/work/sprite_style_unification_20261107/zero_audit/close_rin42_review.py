"""Record reviewed native checkpoint and the next evidence-based art priorities."""
from pathlib import Path
import json,hashlib,sys,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'rin_extension'
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank
P=OUT/'prepared_air_continuation2_v2/PL01_U.ARC';arc=P.read_bytes();sha=hashlib.sha256(arc).hexdigest()
assert sha=='ffca3087c17c883e6383b0ff38417b003138d1614c8add8edb1b99199bf322df'
read=json.loads((OUT/'final42_readback_audit.json').read_text('utf8'));native=json.loads((OUT/'rin42_components_native_checks.json').read_text('utf8'))
assert read['passed'] and native['passed']
pal=struct.unpack_from('<16H',entry(arc,9),0);idle=render(arc,0,0,147)[0]
choices=[(0,61,'지상 베기 준비/초반','넓은 흰 앞머리와 회색 한 면으로 얼굴 결이 뭉치고 눈·턱 구분이 약하다. 흰 커프/앞치마 안쪽의 작은 명암 단계가 대기보다 적다.'),
 (0,174,'사다리 후면','뒷머리가 큰 흰 덩어리와 톱니형 아랫단으로 읽힌다. 옆뒤 머릿결과 귀 뒤 그늘, 후면 상의·앞치마 접힘 묘사를 같은 해상도에서 다시 그릴 필요가 있다. 정면 머리를 붙이지 않는다.'),
 (1,5,'승리/귀환 직전 옆면','얼굴의 중앙 한 줄 음영과 검은 상의 면이 단순하고 손목·가슴·치맛단 경계가 대기의 세밀한 셀렉티브 윤곽보다 둔하다. 옆면 자세로 좁아진 폭 자체는 유지한다.'),
 (1,183,'낙봉파 웅크린 몸체','머리·리본의 넓은 면과 흰 몸체 덩어리에서 앞치마·소매·무릎의 재질 구분이 약하다. 손/발 지면 접점을 고정한 채 주름과 면을 다시 구분해야 한다.')]
def tight(a):
 y,x=np.nonzero(a)
 if not len(x):return None
 bb=(int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1);v=a[bb[1]:bb[3],bb[0]:bb[2]]
 return v.shape,v.tobytes(),bb[:2]
allposes={}
for b in (0,1):
 for f in graphics_bank(entry(arc,2),b)['frames']:
  n=f['index']
  if b==1 and 42<=n<=49:continue
  a=render(arc,b,b*5,n)[0];allposes[(b,n)]=tight(a)
rows=[];sheet=Image.new('RGB',(1152,600*len(choices)),'#64717b');dr=ImageDraw.Draw(sheet)
for row,(b,n,label,reason)in enumerate(choices):
 a=render(arc,b,b*5,n)[0];key=tight(a);aliases=[]
 for (bb,nn),v in allposes.items():
  if v and v[:2]==key[:2]:aliases.append({'bank':bb,'ref':nn,'offset_from_master':[v[2][0]-key[2][0],v[2][1]-key[2][1]]})
 for col,(name,v)in enumerate([('accepted idle147',idle),(f'current b{b}_{n:03d}',a)]):
  pic=rgba(v,pal).crop((112,104,208,200)).resize((576,576),Image.Resampling.NEAREST)
  assert np.count_nonzero(np.array(pic.getchannel('A')))==np.count_nonzero(v)*36
  sheet.paste(pic,(col*576,row*600+24),pic);dr.text((col*576+5,row*600+5),name,fill='white')
 rows.append({'priority':row+1,'bank':b,'ref':n,'label':label,'reason':reason,'exact_shape_aliases':aliases,'same_angle_only':True,'new_art_made':False})
dest=OUT/'next_priority_review';sheet.save(dest/'selected_four.png')
(dest/'findings.json').write_text(json.dumps({'source_arc_sha256':sha,'viewed_sheets':[f'groups_{i:02d}.png'for i in range(6)],'viewed_representatives':36,'selected_keys':rows,'next_after_four':['b0_229 공중공격','b1_150 용염인 후면','b1_165/171 회전','b0_149 저체력','b0_034/036/037/038/041/045 이동 연결 잔여'],'limitations':['이번 추가 육안 비교는 36대표 자세이다. 315참조 전체를 새로 열람했다고 주장하지 않는다.','315 몸체/머리 분류에는 동일 표시 사본과 일부 효과 참조가 섞인 기존 분류 한계가 있다. b0_200은 실제 열람에서 독립 효과 조각으로 확인했으므로 새 몸체 제작 수로 세지 않는다.','일반/블랙은 같은 비트맵이며 새 작품은 일반 원팔레트로 제작하고 블랙 팔레트로 별도 미리보기한다.']},ensure_ascii=False,indent=2)+'\n','utf8')
report=OUT/'REPORT.md';old=report.read_text('utf8');old=old.replace('## 현재 동결 단위: 총36참조','## 이전 동결 단위: 총36참조',1)
head='''## 현재 동결 단위: 총42참조

최신 자원은 `prepared_air_continuation2_v2/PL01_U.ARC`, SHA-256 `ffca3087c17c883e6383b0ff38417b003138d1614c8add8edb1b99199bf322df`이다. 이전36에 공중28/29/30/31/32/33을 더했다. 새 원화4장의 전체 native 그림을 사용했으며 옛 머리를 덮지 않았다. 29/30과31/32는 기존 동일 표시 공유를 유지한다. 타일·파트 수는 변하지 않았고 28과29/30의 샘플링 창만 조정해 새 소매 픽셀을 잘라내지 않았다. 은행 여유4,236바이트, 조립 여유416바이트이다.

실제 재디코드 normal_readback_00/01과 black_readback_00/01 네 장을 직접 보았다. 앞머리·눈/턱 분리, 커프의 안쪽 그늘, 치마 주름이 기존 넓은 면보다 분명해졌다. 목·팔 및 발의 단절은 보이지 않았으나 연속 게임 움직임의 수용은 아직 확인하지 않았다. 28/29/31의 원래 눈은 청록색 인덱스만으로 특정할 수 없으므로 새 눈 좌표가 원래와 완전히 같다고 단정하지 않는다. 기존 발바닥 y는 대부분 같고 29의 화면 왼쪽 발 분할 측정에서1px 차이가 있어 실제 동작에서 함께 확인한다.

`verify_rin42_readback.py`는 제작/등록/패킹 함수를 부르지 않고 실제 부모 BIN에서 다시 읽었다. 444raw/436표시 중42개 등록 PNG가 정확히 일치하며 비대상402raw/394표시/402조립, 대기6, 부분VRAM8, 나머지 entry/팔레트/음향, 은행 경계를 보존한다. 원화·등록 입력5개 manifest도 다시 해시 확인했다. 근거는 `final42_readback_audit.json`이다.

`rin42_components_native_checks.json`은 실제 부모 EXE의 원래 MIPS 디코더와 업로드 경로를 격리 실행한 결과다. 누적42개와385 GPU 파츠 경계 검사를 통과했다. 이는 실제 에뮬레이터 플레이 검증이 아니며 게임/BIN/저장파일은 쓰지 않았다. 제작기 자체의 반복 동일/4종 잘못된 입력 거부도 proposal에 보존한다.

남은 모션 대표36자세를 대기와 다시 나란히 열람했다. 다음 핵심4개는 `next_priority_review/selected_four.png`와 `findings.json`의 지상베기61, 사다리후면174, 승리옆면bank1_5, 낙봉파bank1_183이다. 얼굴의 흰 덩어리·후면 머릿결·커프와 치맛단의 명암 단순화를 우선한다. 기존315분류의 남은273은 대기·사본·분류 오류도 포함하므로 새로 그려야 할 그림273장이라는 뜻은 아니다.

'''
marker='## 이전 동결 단위: 총36참조'
assert marker in old
old=old.replace(marker,head+marker,1);report.write_text(old,'utf8')
print(json.dumps({'candidate':sha,'next_keys':[(b,n)for b,n,_,_ in choices]}))
