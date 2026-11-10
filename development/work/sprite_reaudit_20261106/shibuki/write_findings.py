"""실제 열람 범위·네이티브 재질 근거·수정/보류 후보를 기록한다."""
from pathlib import Path
import json,hashlib,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(H))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from leg_material_expanded import SRC,SHA,REFS,material_masks
from scripts.overhaul_sprites_costume import base_palette_colors
def sha(b):return hashlib.sha256(b).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf8')

def main():
 m=json.loads((H/'prepared_manifest.json').read_text('utf8'));assets,_=read_disc(SRC,('PL00_U.ARC','PL02_U.ARC'));arc=Archive(assets['PL02_U.ARC'])
 legacy=[]
 for n in REFS:
  current=arc.layer(n)[0];old=base_palette_colors('ver_buki_riko',n,arc.words)
  skin,shoe,_=material_masks(n,current,arc);mask=skin|shoe
  legacy.append({'ref':n,'tested_material_pixels':int(mask.sum()),'legacy_rgb_remapped_exact_pixels':int(((current==old)&mask).sum()),'all_material_indices_equal':bool(np.array_equal(current[mask],old[mask]))})
 files=[ROOT/'character/ver_buki_riko/buki(ultimate armor).webp',ROOT/'scripts/prepare_shibuki_ultimate_base.py',ROOT/'scripts/register_shibuki_ultimate_production.py',ROOT/'scripts/overhaul_sprites_costume.py',ROOT/'work/overhaul_20261105/sprites/shibuki_preultimate/wall_dash_01_generated.png',ROOT/'work/overhaul_20261105/sprites/shibuki_preultimate/wall_dash_01_target.png']
 write(H/'material_history.json',{'source_sha256':SHA,'files':[{'path':rel(p),'sha256':sha(p.read_bytes())}for p in files], 'legacy_lower_comparison':legacy,'confirmed':'의상 제작 normalize 함수가 기존 acquired 그림의 lower(hip+3 이하)를 새 그림보다 우선 복사한다. 최신 검은 다리는 비투명 색인 2/F 및 붉은 B가 포함된 기존 하체를 이어받았다.','limits':'최초 생성 단계에서 검은 부츠가 생긴 최초 원인까지 확정한 것은 아니다. PL00 기본 부츠 형상을 따르는 구작과 후속 lower 보존은 직접 확인했으나, 모든 중간 등록판의 최초 오염 시점을 이 감사에서 재구성하지 않았다.'})
 refs=[0,1,3,13,33,79,83,85,204,205];w=200;h=220;sheet=Image.new('RGB',(w*5,h*2),(26,32,43));d=ImageDraw.Draw(sheet)
 for i,n in enumerate(refs):
  im=arc.composite(n,0)[0];crop=im.crop((136,125,176,163)).resize((200,190),Image.Resampling.NEAREST);x=i%5*w;y=i//5*h
  d.text((x+4,y+4),f'ref {n}: same world crop',fill='white');sheet.paste(crop,(x,y+24),crop)
 sheet.save(H/'sunglasses_candidates.png')
 ui=[ROOT/'out/sprite_consistency_20261105/shibuki/supplementary/selection_sheet_00.png',ROOT/'out/sprite_consistency_20261105/shibuki/supplementary/save_sheet.png']
 findings={
  'source_bin':rel(SRC),'source_sha256':SHA,'graphics_identity':rel(H/'prepared_manifest.json'),'actual_gameplay_newly_verified':False,
  'visual_review':{'method':'view_image로 실제 픽셀 비교시트를 직접 열람. 각 pose 옆에 해당 폼 idle0을 같은 원점·같은 정수 배율로 표시.','main_sheets':m['main_sheets'],'main_sheets_count':64,'main_valid_pose_compositions':912,'partial_sheets':m['partial_sheets'],'partial_mask_compositions':288,'supplementary_sheets':[rel(p) for p in ui],'supplementary_selection_refs':25,'supplementary_save_combinations':34,'arm1_vs_arm2_main_rgba_identical':True,'revised_gallery_frames_applied':m['revised_count']},
  'confirmed':[{'id':'SH-LEG-01','priority':'수정 대상','forms':['ultimate_before','ultimate_after'],'refs':REFS,'finding':'대기와 설정화의 맨다리·짧은 샌들 대신 검은 정강이/부츠 면이 여러 공중·벽·대시 및 이동 자세에 남아 있다. 79/80의 앞다리는 붉은 긴 부츠로도 읽힌다.','cause':'색이 비어 보이는 투명 구멍이 아니라 기존 하체의 어두운 색인/부츠 재질이 유지된 문제. 의상 전후 표시 분기나 원점의 문제가 아니다.','evidence':[rel(H/'ultimate_dash_focus.png'),rel(H/'run_leg_diagnosis.png'),rel(H/'material_history.json')],'fix':'새 자세나 실루엣을 만들지 않고 원래 PL00 명암 위치를 피부 C/D와 짧은 샌들 재질로 대응. 자세별 하체 마스크 밖·외곽 1px·alpha·팔레트·조립·타이밍 보존.','prepared':rel(H/'prepared_v3/proposal.json'),'runtime_verified':False}],
  'candidates':[{'id':'SH-ACCESSORY-01','forms':['ultimate_before','ultimate_after'],'refs':[3,13,33,79,83,204,205],'finding':'대기0/사격85에서 읽히는 금테 선글라스가 많은 기존 모션에서 보이지 않으며, 붉은 단일 장식만 보이는 경우가 있다.','evidence':[rel(H/'sunglasses_candidates.png'),rel(files[0]),rel(files[4])],'status':'설정화의 선글라스 정체성은 확인. 기존 wall_dash 생성 원화부터 없으므로 등록 누락만으로 단정하지 않는다. 같은 각도 복원/새 각도 해석은 별도 미술 작업이며 이번 재질 패치에 포함하지 않음.'},
   {'id':'SH-LEG-02','forms':['ultimate_before','ultimate_after'],'refs':[9,10,17,18],'finding':'머리/천과 겹친 작은 뒷발에서 어두운 부츠 잔재로 보이는 부분이 있다.','status':'큰 검은 종아리 그룹보다 가려짐/소재 경계가 불명확하다. 천까지 피부로 바꾸는 일을 피하려고 이번 영역에서 제외. 별도 부위 소유 확인 필요.'},
   {'id':'SH-DETAIL-01','forms':['base','fourth'],'refs':[95,96,100,120,121,122,123,124,125],'finding':'몸을 숙인 일부 사격·체력부족 자세는 대기에 비해 얼굴/옷의 명암 덩어리가 단순하다.','status':'서로 다른 원근·숙임 자세 때문에 크기 차이를 오류로 단정하지 않는다. 전면 재생성 근거까지 확정하지 않았고 이번에는 보존.'}],
  'non_defects':['라이드아머 184..203은 원래 탑승 머리 자원으로 전체 몸 크기 축소가 아니다.','등장133/135에서 포스가 잠시 기본 의상으로 보이는 것은 확인된 native 임시 armor0 단계다.','수정141/142는 수용된 대기+기존 잔광 규칙이며 이번 최신 그래픽과 일치한다.','포스183은 검정·금색 의상 복원이 반영되어 있다.','기본형에서 사용 불가능한 armor-only 213..230은 기본형 실제 미교체로 세지 않았다.','귀환/등장 outline·단색/입자 단계는 독립 몸체 결함으로 세지 않았다.'],
  'not_fully_visually_reviewed':['부분아머는 18대표 참조×16mask만 직접 열람. 나머지 참조×모든 mask를 모두 육안 검사하지 않았다.','arm1/arm2 주요 폼은 RGBA 전수 동일하나 모든 부분mask arm1을 별도로 육안 열람한 것은 아니다.','예약/부분업로드 105 및175..182를 가짜 완성 그림으로 채우지 않았다. 독립 완성 프레임으로 평가하지 않는다.','실제 배경·피격 CLUT·특수 효과 합성·좌우 실기·시간 연속성은 이 정적 재감사에서 새로 실행하지 않았다.','큰 선택 일러스트/대화 초상화를 새로 미술 감수한 것은 아니다. 선택/저장 작은 플레이어 자원 시트를 검토했다.'],
  'conclusion':'명백한 하체 재질 결함은 준비 패치와 분리해 기록했다. 수치검증/과거 수용만으로 모든 프레임의 미술 품질이 완벽하다고 결론내리지 않는다.'}
 findings['confirmed'][0]['prepared']=rel(H/'prepared_v4/proposal.json')
 findings['rejected_intermediates']=['prepared_v1: 6참조 최소안','prepared_v2: 52참조 중간안','prepared_v3: 공유 압축 스트림의 비사격 타일만 수정해 일부 사격 전용 하체 타일 복원 누락. 육안 재추출에서 발견, 적용 반려.']
 write(H/'findings.json',findings)
 print(json.dumps({'main_sheets':64,'partial_sheets':18,'legacy_exact':sum(x['all_material_indices_equal'] for x in legacy),'refs':len(REFS)}))
if __name__=='__main__':main()
