"""실제 열람한 범위와 나나 미술 수정 우선순위를 기록한다."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from collect import SOURCE,OUT,EXPECTED,digest
from scripts.discover_inputs import DiscReader
from scripts.export_x_consistency import Archive,GROUPS
from src.psx_player import composition_frame
def write(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 assert digest(SOURCE)==EXPECTED
 with SOURCE.open('rb')as f:
  d=DiscReader(f,SOURCE.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']};assets={n:d.read(rs[n]['lba'],rs[n]['size'])for n in('PL00_U.ARC','PL02_U.ARC')}
 chosen=[0,7,12,33,41,62,69,73,77,85,95,98,100,120,133,144,148,150,156,162,184,217,223,231]
 constraints={}
 for name,data in assets.items():
  a=Archive(data);bank=a.banks[0];frames=[]
  for ref in chosen:
   g=bank['frames'][ref]
   frames.append({'ref':ref,'tiles':g['tile_count'],'compressed_offset':g['offset'],'slot_limit':g['limit'],'stream_aliases':[f['index']for f in bank['frames']if(f['offset'],f['tile_count'])==(g['offset'],g['tile_count'])],'parts':{str(pb):composition_frame(a.c,pb,ref)['parts']for pb in(0,5,6,7,8)}})
  constraints[name]={'sha256':hashlib.sha256(data).hexdigest(),'gfx_bank0_base':bank['base'],'gfx_bank0_end':bank['end'],'palette_rgb555':a.words[:48].tolist(),'selected_frames':frames}
 write('native_constraints.json',constraints)
 findings=[
 {'id':'N-STYLE-01','priority':1,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(2,33,2)),
  'issue':'이동사격 팔의 내부 명암이 긴 수평 띠로 늘어나 정지사격85·대기0의 짧은 소매 주름과 불일치. 기본/포스가 가장 강하고 재킷도 분홍 직사각형으로 단순함. 수영복 팔은 맨살이므로 소매 장식 없이 손목/팔꿈치 음영만 비교.',
  'action':'우선 2·12·26을 대기/85와 같은 윤곽 밀도로 다시 도트화. 원래 총구·손·어깨 연결점을 고정하고 팔꿈치와 소매 폭 변화/안쪽 그림자를 배치. 승인된 작은 팔 모듈을 보간 없이 각 이동짝에 등록.',
  'source':'work/ver_rin_nana/nana_art/run_v1/firing_generated.png',
  'code':['scripts/prepare_nana_run_pairs.py:19','scripts/prepare_nana_run_pairs.py:28','scripts/prepare_nana_fourth_run_art.py:134','scripts/prepare_nana_ultimate_shot_arm.py:93'],
  'basis':'실제 시각 비교 및 색 제한·가로 확대 코드 확인. 포스는 기본 사격창을 복사함.',
  'sheet':'focus/shoot_arm.png','reuse':'원화의 손목·소매 주름 참고 가능. 기존 얇은 팔 PNG를 그대로 늘리는 방식은 폐기해야 함.'},
 {'id':'N-STYLE-02','priority':1,'forms':['base','fourth'],'refs':list(range(1,33)),
  'issue':'달리기 앞머리가 매끈한 분홍 뚜껑, 뒷머리가 한두 넓은 면으로 읽힘. 대기0의 앞머리 층·밝은 가닥·얼굴 경계와 밀도가 다름. 검은 몸통/치마도 넓은 면에 주름이 줄어듦.',
  'action':'대표1·7·15·25·31의 눈/머리 외곽 크기는 유지하고 가르마와 가닥 방향의 1픽셀 명암을 복원. 몸통은 소매와 구분되는 어깨·허리 음영, 치맛단 접힘을 같은 기준으로 보강. 홀수 몸체와 짝수 사격을 한 쌍으로 작업.',
  'source':'work/ver_rin_nana/nana_art/run_v1/stride_revision.png',
  'code':['scripts/normalize_nana_run.py:13','scripts/normalize_nana_run.py:61'],
  'basis':'현재7은 normalized05/run_007.png와 RGBA 정확 일치. 원화에는 앞머리 광점·치마 주름이 남아 있어 등록 이전 디테일 참고 가능.',
  'sheet':'focus/run_face.png','reuse':'원화 재사용 + 네이티브에서 남길 명암을 수동 선택. 45px/0.9배 다수결 축소만 다시 실행하면 같은 손실 재발.'},
 {'id':'N-STYLE-03','priority':1,'forms':['ultimate_before','ultimate_after'],'refs':list(range(67,85))+[217,218,220],
  'issue':'대시 뒷머리가 밝은 분홍 윗띠와 큰 암적색 아래 면으로 나뉘어 대기의 여러 가닥·굽은 명암보다 단조로움. 특히69·71·75·77. 얼굴/귀는 대기에서 가져와 상대적으로 세밀하여 뒤쪽의 평탄함이 더 도드라짐.',
  'action':'얼굴·귀·손·총·발·현재 연결 외곽을 유지하고 뒷머리 내부만 가닥 방향에 맞게 재도트화. 69·73·77을 먼저 제작한 뒤18참조와 노바 공유 몸체에 전파.',
  'source':'work/ver_rin_nana/nana_ultimate_armor/dash_hair_v1/generated.png',
  'code':['scripts/prepare_nana_ultimate_dash_hair.py:25','scripts/prepare_nana_ultimate_dash_hair.py:30','scripts/ultimate_costume_swap.py:86'],
  'basis':'현재69가 dash_hair_packed_v3/ultimate_069.png와 RGBA 정확 일치. 이전 dash_v1보다 최신 hair_v1이 실제 출처. 등록 시 뒷머리 사각형을 다시 확대하고 비는 곳을 가장 가까운 분홍색으로 채움.',
  'sheet':'focus/air_dash.png','reuse':'최신 hair_v1의 가닥 분리와 초기 dash_v1의 음영을 참고 가능. 초기 짧은 머리 외곽을 그대로 가져오면 연결/범위 회귀이므로 복원본으로 바로 채택하지 않음.'},
 {'id':'N-STYLE-04','priority':2,'forms':['base','fourth'],'refs':list(range(33,85))+[93,94],
  'issue':'공중·벽·대시의 기본 머리 가닥과 소매·몸통 내부 선이 대기보다 단순함. 41/53/69/77은 뒷머리 분홍 면이 두드러지고, 사격 짝은 길어진 회색 팔을 함께 사용.',
  'action':'N-STYLE-01/02의 네이티브 기준을 먼저 확정한 다음33·41·53·62·69·77로 동작별 얼굴 방향/가닥 곡선을 제작. 대기 얼굴을 모든 회전에 그대로 붙이지 말고 눈 크기·앞머리 음영 밀도만 유지.',
  'source':'work/ver_rin_nana/nana_art/air_v1/generated.png',
  'code':['scripts/normalize_nana_air.py:27','scripts/normalize_nana_dash.py','scripts/normalize_nana_wall.py'],
  'basis':'실제 전 참조 시트 열람. 개별 등록 손실량까지 전부 역산하지 않았으므로 모든 파생 프레임이 같은 한 줄 때문이라고 단정하지 않음.',
  'sheet':'focus/air_dash.png','reuse':'기존 공중/대시/벽 원화와 현재 포즈·총구를 재사용하는 부분 미술 보강.'},
 {'id':'N-STYLE-05','priority':2,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':[98,99],
  'issue':'양팔을 편 특수자세에서 소매가 검은/분홍 직사각형에 가까워지고 앞머리·가슴과 치마 면도 대기보다 단순함. 수영복은 맨팔과 검은 상의의 경계가 기준.',
  'action':'N-STYLE-01의 팔 규칙을 양팔 방향에 맞게 적용하고 어깨-소매의 꺾임, 손목 경계, 허리/치맛단 대비를 보강. 무기 발사점과 양팔 방향은 보존.',
  'source':'work/ver_rin_nana/nana_art/special_v1/generated.png',
  'code':['scripts/normalize_nana_special.py:25'],
  'basis':'현재 기본98은 production01/frame_098.png와 RGBA 정확 일치. 원화에는 소매 접힘/벨트/가슴 절개가 있으나 최종 크기에서 약해짐.',
  'sheet':'focus/special.png','reuse':'원화의 소재 경계를 작은 도트에서 선택적으로 복구. 전면 재생성보다 두 팔/상체 부분 수정 우선.'},
 {'id':'N-STYLE-06','priority':2,'forms':['base','fourth'],'refs':list(range(143,156))+[183],
  'issue':'후면 사다리144..147/151..152에서 기본 머리카락이 넓은 분홍 판, 포스 베일이 넓은 회색 면으로 보임. 포스 다리는 내부가 한 색 세로 띠로 되어 대기의 관절·겹침 명암보다 단조로움.',
  'action':'후면144·146·151과 측면149/150부터 가르마/가닥/베일의 굴곡 명암을 재배치. 폭이 있는 다리 내부에만 무릎/종아리의 피부11·12 분포 복원; 1픽셀 폭 구간을 억지로 꾸미거나 전체 다리를 늘리지 않음. 원래 손·발 사다리 접점 유지.',
  'source':'work/ver_rin_nana/nana_fourth_armor/ladder_v1/generated.png',
  'code':['scripts/prepare_nana_fourth_ladder_art.py:52','scripts/prepare_nana_fourth_ladder_art.py:59'],
  'basis':'현재 기본144/포스144는 보관된 production01/ladder_art_v5 PNG와 각각 RGBA 정확 일치. 원화의 다리 명암을 코드가 피부12/경계1 행 채우기로 덮음.',
  'sheet':'focus/ladder_vehicle.png','reuse':'기본·포스 사다리 원화의 실제 후면 가닥/옷 주름을 재사용. 포스 뒤 베일의 leg8 소유는 사용자 수용 배분이므로 유지.'},
 {'id':'N-STYLE-07','priority':2,'forms':['base','fourth'],'refs':[95,96,100,101,102,103,104,231,232],
  'issue':'특수기에서 앞머리·뒷머리의 세부 경계와 검은 소매/치마의 내부 대비가 대기보다 줄어든다. 95의 치마,100/103의 앞머리와 웅크린 소매,231의 위로 뻗은 소매가 비교 지점.',
  'action':'95·100·103·231 네 대표의 헤어/소매/치마 명암부터 보강하고 대응96/232 및중간101/102/104로 확장. 웅크린 자세의 bbox높이 감소를 캐릭터 축소로 오인하지 않음.',
  'source':'work/ver_rin_nana/nana_art/special_remaining_v1/generated.png',
  'code':['scripts/normalize_nana_special_remaining.py:25','scripts/prepare_nana_fourth_elemental_art.py:49'],
  'basis':'현재 전모션과 확대 시트 시각 확인. 원화 일부를 추가 네이티브 등록하는 작업은 아직 안 했음.',
  'sheet':'focus/special.png','reuse':'기존 자세 원화와 포스 elemental_v2. 이미 수정한 얼티밋95/96 피부는 손대지 않음.'},
 {'id':'N-STYLE-08','priority':3,'forms':['base','fourth'],'refs':[106,107,108,110,120,121,122,123,124,125,133,134,135,136,137,138,139,156,157,158,162,163,164,165,166,167,168,169,170,171,172,173,174,204,205,206,207,233,234,235,236],
  'issue':'피격/저체력/등장/승리/탑승에도 같은 분홍 면·어두운 옷 단순화가 있으나 앞 우선군보다 화면 노출·차이가 작다. 133·156·162·204와120은 각각 확인할 대표.',
  'action':'달리기/공중의 헤어·옷 명암 기준 확정 후 동일한 머리 방향의 기존 픽셀을 참고하여 연결 프레임을 맞춘다. 효과 전용 참조의 색 단순화는 미술 결함으로 처리하지 않음.',
  'source':None,'code':[],'basis':'현재 전체 시트 실제 열람. 각 원화→최종 색 변환을 전부 역추적하지 않았으므로 개별 원인 확인은 제작 직전 수행.',
  'sheet':'focus/ceremony.png','reuse':'기존 손발·실루엣·색 효과·타이밍을 보존하며 부분 보강.'}
 ]
 coverage=[]
 for group,rr in GROUPS.items():
  for form in('base','fourth','ultimate_before','ultimate_after'):
   tasks=[q['id']for q in findings if form in q['forms']and set(rr)&set(q['refs'])]
   coverage.append({'form':form,'group':group,'refs':rr,'priority_tasks':tasks,'disposition':'미술 보강 목록 포함'if tasks else'현재 확대 검토에서 우선 재제작 항목 없음; 미술 완전 통일 판정 아님'})
 write('priority_map.json',{'baseline_sha256':EXPECTED,'findings':findings,'coverage':coverage,'runtime_playback_this_pass':False,'source_registrations_exact_rgba':5,'all_checked_refs_per_form':237,'partial_visual_refs':16,'partial_visual_masks':16,'armtype_exact_pairs':3648})
 m=json.loads((OUT/'manifest.json').read_text('utf8'));viewed=[{'path':q['path'],'sha256':q['sha256'],'kind':'현재 BIN 직접 복원 시트','refs':q['refs']}for q in m['sheets']]
 for p in sorted((OUT/'provenance').glob('*_comparison.png')):viewed.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'kind':'원화/현재/대기 비교'})
 for p in ['work/ver_rin_nana/nana_art/run_v1/generated.png','work/ver_rin_nana/nana_art/run_v1/firing_generated.png','work/ver_rin_nana/nana_ultimate_armor/dash_v1/generated.png','work/ver_rin_nana/nana_art/ladder_v1/generated.png','work/ver_rin_nana/nana_ultimate_armor/dash_hair_v1/generated.png','work/ver_rin_nana/nana_art/run_v1/stride_revision.png','work/ver_rin_nana/nana_fourth_armor/ladder_v1/generated.png','work/ver_rin_nana/nana_art/special_v1/generated.png']:
  viewed.append({'path':p,'sha256':digest(ROOT/p),'kind':'수정하지 않은 생성 원화 직접 열람'})
 for category,num in(('selection_all',4),('save_all',2)):
  for i in range(num):
   p=f'work/sprite_reaudit_20261106/nana/focus/{category}_{i:02}.png';viewed.append({'path':p,'sha256':digest(ROOT/p),'kind':'과거 시트이나 최신 UI4자원 바이트 동일 확인 후 재열람'})
 write('review_log.json',{'actually_viewed_images':len(viewed),'view_tool':'view_image','sheets':viewed,'not_performed':['이 턴의 실제 게임 조작/모션 재생','모든 무기 팔레트/좌우/실제 배경 대조','부분16마스크×228참조의 개별 육안 관찰','새 그림 제작/네이티브 교체/BIN 변경'],'notes':['948은 4폼×237물리참조로, 독립 애니메이션948개라는 뜻이 아니다.','38현재 시트=전체27+확대7+부분4. 각효과/예약참조도 구분하여 확인.','부분16대표×16마스크256이미지를 실제 열람, 모든 3648 arm1/2쌍은 픽셀 동일만 검사했다.']})
 assert digest(SOURCE)==EXPECTED
 print(json.dumps({'priority_groups':len(findings),'viewed':len(viewed),'current_bin_preserved':True}))
if __name__=='__main__':main()
