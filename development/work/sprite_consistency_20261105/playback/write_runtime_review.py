"""실제 창 녹화 조밀 접촉시트의 직접 미술 관찰 기록."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent/'art_review/runtime_dense'
capture=json.loads((HERE/'capture.json').read_text('utf8'))
for row in capture['sheets']:
    assert hashlib.sha256((ROOT/row['sheet']).read_bytes()).hexdigest()==row['sheet_sha256']
    row['view_image_opened']=True
report={'schema_version':1,'scope':'root가 녹화한 실제 ePSXe 창의 시간별 원본 픽셀 crop을 직접 열람한 미술 검토',
 'simulation':False,'new_emulator_input_by_reviewer':False,'art_modified':False,
 'source_bin_sha256':'5a57b31c7a4410d697183a01b2246a28344c847cefb331d27aad56135e7a924d',
 'sheets':capture['sheets'],'reviewed_encoded_frames':sum(x['frames'] for x in capture['sheets']),
 'timing_note':capture['timing'],
 'observations':[
  {'case':'shibuki_fourth_arrival','range_seconds':[6.5,10.05],
   'observed_timeline':[
     {'seconds':[7.328,7.703],'detail':'기본 붉은/흰 의상의 준비 자세가 실제로 보인다.'},
     {'seconds':[7.765,7.828],'detail':'백색 전환 효과 다음 포스 검정/금색 대기형 실루엣으로 복귀한다.'},
     {'seconds':[7.828,10.031],'detail':'이어지는 포스 대기와 머리·발 기준점, 몸통 크기가 시각적으로 연결된다.'}],
   'finding':'복귀 구간에서 눈에 띄는 좌우 점프·키 축소·관절 분리를 확인하지 못했다. 코드로 확인한140event의소유아머복원과 관찰된색전환이 일치한다.',
   'native_branch_proof':'work/sprite_consistency_20261105/playback/art_review/fourth_arrival_native.json',
   'important_limit':'녹화 샘플은 약16fps이며 WebP가동일그림을병합했다.141/142 개별ID를 모든 캡처에 강제로 배정하지 않는다.물보라가 허리/다리 일부를 가린다.',
   'confirmed_defect':False,'action':'현재 등장 아트와 전환 유지'},
  {'case':'shibuki_fourth_rising_fire_ground','range_seconds':[0.44,1.25],
   'finding':'0.563초 올려든 손 자세에서0.625초 화염이 손/전방 몸체를 덮으며 시작하고 이후 위로 이동한다.발생점과 손 사이의 새로운 빈틈은 보이지 않는다.대기 대비 머리·몸통이 비정상적으로 커지는 현상도 확인하지 못했다.',
   'confirmed_defect':False,'action':'현재 자세 유지'},
  {'case':'shibuki_fourth_rising_fire_air','range_seconds':[2.12,3.25],
   'finding':'점프 이후 팔을 들어 화염을 내보내고 하강·착지로 연결된다.2.313초 화염 시작 시 몸체와 연결되며 공중 굽힌 무릎은 정상 포즈 변화로 판단한다.',
   'confirmed_defect':False,'action':'현재 자세 유지'},
  {'case':'shibuki_fourth_charged_rising_fire','range_seconds':[[6.70,8.30],[11.70,13.30]],
   'finding':'두 차지 실행 모두 웅크림→화염에 둘러싸인 상승→하강→대기로 이어진다.6.938~7.438초 및11.938~12.500초에서 화염과 손/몸체가 분리되어 떠 있는 틈을 확인하지 못했다.화염이 본체를 가리는 동안의 색면 변화는 별도 효과로 구분했다.',
   'confirmed_defect':False,'action':'현재 명암 복원6참조와 원래 화염 유지'},
  {'case':'riko_wall_actual_contact','path':'work/sprite_consistency_20261105/runtime/riko_wall_sync/recording/contact.png',
   'view_image_opened':True,'scope':'실제12장접촉시트만추가관찰; 이번작업에서벽동작녹화전체를조밀재검수하지않음',
   'finding':'보이는 머리·팔과 벽 자세는 정상 범주로 보이나 폭포가 캐릭터를 크게 가려 전체 몸체의 픽셀 완전성은 이 화면만으로 판정하지 않는다.',
   'confirmed_defect':False,'action':'가려진부위는정적/시뮬레이션검토증거와구분'}],
 'overall':'직접 관찰한 실제 녹화 구간에서 새로 수정해야 할 확정 미술 결함을 발견하지 못했다. 사용자 수용과 전 장면 전수 실기 성공으로 확대하지 않는다.',
 'full_framebuffer_pixel_equivalence_claimed':False,'source_videos_unchanged':True}
(HERE/'findings.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sheets':len(capture['sheets']),'frames':report['reviewed_encoded_frames'],'confirmed_defects':0}))
