"""미술 관찰과 재제작 순서를 기록한다. 게임/설정화는 읽지 않거나 읽기 전용이다."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
def load(p):return json.loads(p.read_text('utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def ids(bank,ns):return [f'b{bank}_{n:03d}'for n in ns]
PRIORITIES={
 'riko':[
  {'id':'R1','priority':1,'name':'3타 부츠 명암·망토 주름','representatives':ids(0,[111,113,117,121,125]),'target_refs':ids(0,range(111,128,2)),'observation':'대기는 종아리 회청색 면, 발목 절곡, 발등 하이라이트가 구별되지만 3타의 펴진 부츠는 흰 내부와 짙은 테두리로 단순해진다. 망토도 넓은 청록 평면과 흰 띠로 읽힌다.','action':'기존 자세와 발 접점은 보존하고 부츠의 전면·측면·발등을 따로 묘사한다. 망토 접힘 뿌리와 끝의 명암을 연결한다. 중간색→흰색 강제 매핑을 재사용하지 않는다.','evidence':'riko_third_saber_6x.png'},
  {'id':'R2','priority':1,'name':'뒤·뒤3/4 머리 마스터','representatives':ids(0,[164,174])+ids(1,[148]),'target_refs':ids(0,[160,162,164,166,168,170,172,*range(174,191)])+ids(1,[148,150,152,154]),'observation':'대기의 가르마·겹친 앞머리·밝은 머리 끝에 비해 뒤쪽은 큰 연두 면에 분리된 녹색 점 몇 개가 놓인다. 같은 간략한23×19 머리가 사다리·질풍아·용염인으로 전파됐다.','action':'뒷머리의 방향과 묶음 뿌리를 명암으로 새로 설계하고 머리 끝은 선택적인 녹색/남색 윤곽을 쓴다. 앞머리나 눈을 후면에 복사하지 않는다. 세 기술에 같은 후면 마스터를 등록하되 손·어깨는 별도 보호한다.','evidence':'riko_normal_rare_rear.png'},
  {'id':'R3','priority':2,'name':'이동·공중·벽의 옷과 부츠','representatives':ids(0,[8,14,21,27,39,49,213,229])+ids(1,[54,132]),'target_groups':['run','jump','dash','wall','wall_saber','air_saber','hyouretsuzan'],'observation':'정면 머리의 세부는 비교적 유지되지만 흰 상의/소매와 길게 편 부츠에서 내부 회청색 면이 줄고 팔·주먹 경계가 흰 덩어리로 합쳐진다. 최신 벽 머리도 대기와 다른 큰 녹색 덩어리가 남는다.','action':'자세별 어깨/소매 끝/허리/발목 명암을 대기와 같은 규칙으로 다시 그린다. 머리 크기 수정만으로 이 묶음을 완료 처리하지 않는다.','evidence':'riko_normal_locomotion.png'},
  {'id':'R4','priority':2,'name':'회전 각도별 픽셀 정리','representatives':ids(1,[161,163,167,169]),'target_groups':['air_spin'],'observation':'대각으로 돌아간 얼굴·장갑·부츠의 픽셀 덩어리가 세로 자세보다 들쭉날쭉해진다.','action':'회전의 중심·자세·타이밍은 보존하고 각 각도의 눈/턱/장갑 및 부츠 외곽을 별도 검수·재도트화한다. 자동 회전만으로 최종화하지 않는다.','evidence':'riko_normal_rare_rear.png'},
  {'id':'R5','priority':2,'name':'승리·탑승·앉기 자세의 재질','representatives':ids(1,[1,5,20,66,183]),'target_groups':['victory_return_body','ride_chaser','ride_armor_head','rakuhouha'],'observation':'승리의 길게 선 부츠와 좁은 상의가 단색 띠로 읽힌다. 탑승의 압축된 얼굴/소매, 낙봉파의 펼친 다리에도 대기보다 재질 구분이 적다.','action':'측면 폭이나 탑승 공간을 일괄 확대하지 않고 발목·옷단·턱과 머리결의 식별 정보를 회복한다. 낙봉파 정적 몸체도 본체 확정 후 파생 갱신한다.','evidence':'riko_normal_rare_rear.png'}
 ],
 'rin':[
  {'id':'L1','priority':1,'name':'이동·대시의 얼굴/소매/가슴띠','representatives':ids(0,[8,14,44,49]),'target_groups':['run','dash'],'observation':'대기147의 앞머리 경계-눈-볼-턱 분리가 달리기에서 매끈한 흰 머리 면과 넓은 볼로 단순해진다. 소매 안쪽 회색과 장갑 경계가 합쳐지고 가슴 흰 세로띠도 줄어든다.','action':'대기의 얼굴/손목/가슴띠 규칙을 각 자세에 새로 그린다. 얼굴을 둥글게 줄이거나 기존 둥근 손을 덮개로 보존하지 않는다.','evidence':'rin_face_cuff_6x.png'},
  {'id':'L2','priority':1,'name':'지상 공격의 얼굴과 팔/몸통','representatives':ids(0,[95,97,99,101]),'target_groups':['ground_saber'],'observation':'95/97은 눈 주변과 가슴띠가 대기보다 단순하고 전완/주먹은 회백색 큰 덩어리이다. 앞치마 내부는 큰 청색 면으로 읽힌다.','action':'동작을 유지한 채 대기처럼 소매-손목-손의 세 경계, 목/가슴띠, 앞치마 접힘을 도트로 명확히 한다. 공유95←97,101←99 관계까지 동기화한다.','evidence':'rin_face_cuff_6x.png'},
  {'id':'L3','priority':2,'name':'공중·벽·빙열참의 표정과 의상','representatives':ids(0,[21,27,35,39,229])+ids(1,[54,132]),'target_groups':['jump','wall','wall_saber','air_saber','hyouretsuzan'],'observation':'작은 얼굴과 소매가 둥근 단순 형태로 묶이고 목/몸통 분리가 약해진다. 하늘로 든 주먹의 회색 띠가 손가락/손목 구분을 대신한다.','action':'들어올린 팔과 몸통 사이 경계, 턱 아래 그림자, 얼굴과 앞머리 결을 대기 수준으로 재구성한다. 원래 도구 자루와 검기 연결점 유지.','evidence':'rin_normal_saber_special.png'},
  {'id':'L4','priority':2,'name':'뒤쪽 머리·상체','representatives':ids(0,[174,196])+ids(1,[148]),'target_groups':['ladder','ryuenjin','shippuuga'],'observation':'뒷머리에 회색 결 자체는 있으나 위쪽의 넓은 흰 면과 아래쪽 톱니 회색 띠로 나뉘며 대기의 가는 면 전환과 다르다. 등/앞치마 뒤쪽도 검정과 흰 띠 위주다.','action':'뒤쪽 머리의 흐름·보닛/리본 뿌리와 목덜미를 같은 마스터로 설계하고 옷 주름을 더한다. 시점 차이를 이유로 유지 판정하지 않는다.','evidence':'rin_normal_rare_rear.png'},
  {'id':'L5','priority':2,'name':'회전 중 도트 보존','representatives':ids(1,[161,163,165,169,173]),'target_groups':['air_spin'],'observation':'45도 회전 뒤 가느다란 옷선·장갑·얼굴 명암이 거친 흰 점 배열로 변한다.','action':'161 한 장의 NEAREST 회전은 배치 초안으로만 쓰고 모든 각도의 내부 선과 윤곽을 수작업 재검수한다. 기준 대기와 같은 선택적 어두운 윤곽을 사용한다.','evidence':'rin_normal_rare_rear.png'},
  {'id':'L6','priority':2,'name':'앉기·승리·탑승의 머리와 의상','representatives':ids(1,[1,5,20,66,183]),'target_groups':['victory_return_body','ride_chaser','ride_armor_head','rakuhouha'],'observation':'낙봉파183과 탑승20은 동그란 흰 머리 면과 넓은 볼, 단순 흰 소매가 눈에 띈다. 승리 옆모습의 몸통과 긴 다리는 대기보다 면 구분이 적다.','action':'얼굴·앞치마·커프스 세부를 다시 그리되 차량 접점과 바닥 원점은 유지한다. 낙봉파 static6_023/024는 확정된 새 본체로 파생한다.','evidence':'rin_normal_rare_rear.png'}
 ]}
GROUP_ACTION={
 'idle':'수정 기준으로 고정. 눈감음·호흡까지 원래 기준을 유지한다.',
 'run':'얼굴/소매/발목과 옷 재질을 대기 기준으로 통일한다.',
 'jump':'공중 기울기에 맞춰 목·소매·신발 내부 명암을 다시 배치한다.',
 'wall':'머리·목·소매·발목을 대기와 비교해 세부 묘사를 통일한다.',
 'dash':'기존 무게중심과 길이를 유지하면서 얼굴/팔/부츠 평면화를 고친다.',
 'ground_saber':'모든 공격 키포즈의 재질을 정리하고 공통/공유 후속 참조에 전달한다.',
 'air_saber':'검기와 자루 접점을 보존하면서 얼굴·소매·의상 내부 명암을 정리한다.',
 'wall_saber':'벽 마스터의 얼굴/몸 재질을 공격 자세에도 동기화한다.',
 'hurt':'섬광 자체는 유지하고 보이는 두 몸체 자세의 소매/얼굴/다리 디테일을 통일한 뒤 섬광을 파생한다.',
 'low_hp':'대기와 가까운 얼굴·옷 디테일은 유지하며 숙인 목/소매/무릎 명암의 수준을 맞춘다.',
 'ladder':'뒤쪽 머리 마스터와 등/옷단 면을 재설계하고 오르기·이탈·공격까지 적용한다.',
 'raijingeki_shared':'대기와 같은86은 보존하고 찌르기 몸체의 팔·부츠·얼굴 정보를 공격 마스터와 통일한다.',
 'hyouretsuzan':'머리·소매·공중 신발 명암을 통일한다. 별도 얼음 무기 객체는 이 몸체 PNG만으로 판단하지 않는다.',
 'ryuenjin':'회전 후면 머리·등/소매 정보를 새 후면 마스터와 통일한다. 원래 불꽃 접점을 보존한다.',
 'shippuuga':'전면/후면 전환 모두 같은 머리결·옷 주름 규칙을 적용한다.',
 'air_spin':'자세 기준을 보존하고 각도별 윤곽/눈/의상 선을 별도로 마무리한다.',
 'rakuhouha':'앉은 얼굴과 옷/펼친 다리의 재질 묘사를 통일한다.',
 'rakuhouha_static_body':'새 본체 확정 뒤 정적 몸체에만 동기화한다. 에너지 면의 단순함은 결함으로 세지 않는다.',
 'arrival_body':'등장 몸체의 얼굴/팔/상의 재질을 정리한 뒤 원래 섬광 실루엣을 동기화한다.',
 'victory_return_body':'측면 머리·상의·부츠의 세부를 보강하고 귀환 몸체 파생도 함께 확인한다.',
 'ride_chaser':'차량 접점은 유지하고 숙인 얼굴·소매·신발의 압축된 세부를 다시 묘사한다.',
 'ride_armor_head':'현재 head-only 공간 안에서 대기와 같은 얼굴/앞머리 구분을 확보한다.',
 'arrival_light':'빛 전용. 세부 묘사 통일을 이유로 변경하지 않는다.',
 'return_light':'빛 전용. 세부 묘사 통일을 이유로 변경하지 않는다.',
 'ride_partial_unknown':'b1_42..49는 이전 VRAM에 의존한다. 독립 이미지 누락을 단순화 결함으로 판정하지 않으며 실제 합성 확보 뒤 검수한다.'
}
def main():
 source=load(OUT/'sources.json');viewed=load(OUT/'viewed.json')
 viewed['additional_detail']=['riko_third_saber_6x.png','rin_face_cuff_6x.png']
 viewed['ui']={c:['save.png','selection_00.png','selection_01.png']for c in ('riko','rin')}
 viewed['sources']+=['work/ver_rin_nana/style_revision/v3/ground/generated_2.png','work/ver_buki_riko/art_pilot/ground_slash_v2/generated_keyposes_v1.png','work/ver_buki_riko/art_pilot/ground_slash_v2/generated_lunge_v3.png']
 viewed['full_sheet_root']='work/sprite_reaudit_20261106/zero/<character>/normal/sheets/'
 viewed['ui_root']='work/sprite_reaudit_20261106/zero/<character>/ui/'
 save(OUT/'viewed.json',viewed)
 result={'status':'미술 원인 조사 및 적극 수정 그룹 확정; 아트/게임 수정은 미실행','previous_assessment_correction':'11/06의 연결·재질 누락 중심 감사로는 대기 대비 디테일 저하를 충분히 평가하지 못했다. 확정 결함 없음이라는 이전 결론을 이번 미술 판단에 재사용하지 않는다.','reference':'각 캐릭터 b0_147 및 같은 대기 애니메이션','sources':{c:{k:v for k,v in source[c].items()if k not in ('native_paths','detail_sheets')}for c in source},'priorities':PRIORITIES,'group_map':{},'limitations':['실제 새 게임 플레이·변경 아트는 없다.','일반 전체동작 시트62장,일반/블랙 확대12장,우선예시2장,선택/저장6장 실제 열람. 블랙 전체62장을 별도로 전수 재열람하지는 않았다. 공유 비트맵의 일반 결함은 블랙에도 적용되며 블랙은 확대 대표의 색 가독성도 확인했다.','b1_42..49 이전 VRAM 의존 프레임과 external weapon121 완전 합성은 미복원이다.','표현 결함 평가는 육안 판단이다. 세부 색 수/알파 연결/타일 제한 통과를 미술 품질 증거로 대신하지 않는다.','정적 효과/비기본CLUT 색은 기존 감사 렌더의 역사 팔레트 미리보기 한계가 있다.','수정 그룹 범위는 전파·검수 범위이며 범위의 모든 픽셀/프레임을 반드시 다시 그리라는 뜻은 아니다. 대기와 같은 좋은 부위는 보존하되 관찰된 단순화는 적극 교정한다.'],'source_lineage':'source_lineage_checks.json','actual_viewed':'viewed.json'}
 for c in ('riko','rin'):
  manifest=load(ROOT/'out/sprite_consistency_20261105'/c/'manifest.json');groups={}
  for g in sorted(GROUP_ACTION):
   records=[r for r in manifest['frames']if r['group']==g]
   groups[g]={'action':GROUP_ACTION[g],'body_or_head_refs':[r['id']for r in records if r['classification'].startswith('body')or r['classification']=='head_only'],'effect_or_blank_refs':[r['id']for r in records if not(r['classification'].startswith('body')or r['classification']=='head_only')],'native_geometry_timing_preserved':True}
  result['group_map'][c]=groups
 save(OUT/'report.json',result)
 save(OUT/'group_map.json',result['group_map'])
 print(json.dumps({'normal_sheets_viewed':sum(len(v)for v in viewed['full'].values()),'variant_detail_sheets':len(viewed['detail']),'additional_detail':2,'UI_sheets':6,'repair_groups':{k:len(v)for k,v in PRIORITIES.items()}}))
if __name__=='__main__':main()
