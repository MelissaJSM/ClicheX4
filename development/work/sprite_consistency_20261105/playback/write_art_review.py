"""직접 본 브라우저 연속 캡처의 미술 판정을 기록한다. 그림/게임은 수정하지 않는다."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
capture=json.loads((HERE/'art_review/capture.json').read_text('utf8'))
manifest=json.loads((HERE/'manifest.json').read_text('utf8'))

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

viewed=[]
for record in capture['records']:
    path=ROOT/record['sheet']
    viewed.append({'character':record['character'],'form':record['form'],'sheet':record['sheet'],
      'sheet_sha256':sha(path),'view_image_opened':True,
      'animation_ids':[x['id'] for x in record['sequences']],
      'ordered_frame_ids':list(dict.fromkeys(s['frame_id'] for a in record['sequences'] for s in a['steps'])),
      'confirmed_new_art_defect':False,
      'result':'검토한 대기·이동·공중·대시·등장·승리귀환에서 신규 몸체 단절·급격한 체형 변경·검은 잔점의 확정 근거 없음'})

arms=[]
for char in ('shibuki','nana'):
    frame_sources=manifest['characters'][char]['image_sources']
    record=next(x for x in viewed if x['character']==char and x['form']=='fourth')
    refs=[int(x.rsplit('_',1)[1]) for x in record['ordered_frame_ids']]
    for ref in sorted(set(refs)):
        a=frame_sources[f'fourth_{ref:03d}'];b=frame_sources[f'fourth_arm1_{ref:03d}']
        # These PNGs have the same encoding; hash equality proves the rendered pixels too.
        same=sha(ROOT/a['path'])==sha(ROOT/b['path'])
        arms.append({'character':char,'ref':ref,'rendered_png_equal':same})

report={
 'schema_version':1,
 'scope':'브라우저에서 실제 타이머 콜백을 진행해 연속 스텝을 캡처하고, 원점이 고정된 순서별 시트를 직접 눈으로 비교한 미술 검토',
 'not_claimed':['게임 물리·장면전환을 시뮬레이션했다는 주장','실제 플레이 영상 전체를 연속 관찰했다는 주장',
                '모든 특수기·피격·벽·사다리·부분파츠까지 이번 연속 검토로 전수 수용했다는 주장',
                '확정 결함이 없다는 이유로 사용자의 미술 수용을 대신하는 주장'],
 'html':{'path':'out/sprite_consistency_20261105/ALL_SPRITES.html','sha256':capture['html_sha256'],
         'unchanged_after_review':sha(ROOT/'out/sprite_consistency_20261105/ALL_SPRITES.html')==capture['html_sha256']},
 'sources':manifest['sources'],
 'capture_proof':'work/sprite_consistency_20261105/playback/art_review/capture.json',
 'viewed_sheets':viewed,
 'viewed_form_count':len(viewed),
 'browser_sequence_count':sum(len(x['sequences']) for x in capture['records']),
 'browser_step_count':sum(len(a['steps']) for x in capture['records'] for a in x['sequences']),
 'art_observations':[
  {'characters':['riko','rin'],'scope':'일반/블랙 대기·이동·공중·대시',
   'finding':'머리의 기본 부피와 흉곽·골반의 연결이 유지된다. 뛰는 중 무릎 굽힘과 망토/머리카락의 수평 이동은 정상 포즈 변화로 판단한다.',
   'action':'현재 그림 보존'},
  {'characters':['riko','rin'],'scope':'animation39/40, bank1 refs1..8',
   'finding':'승리·귀환에서 옆모습으로 돌아서 몸통 폭이 좁아진다. 정면 대기 bbox보다 좁다는 이유만으로 체형 축소로 판단하지 않았다.',
   'action':'현재 그림 보존'},
  {'characters':['shibuki'],'scope':'기본/포스/얼티밋전후 이동·공중·대시',
   'finding':'여우 귀·머리 크기와 무릎/발의 위치가 포즈 안에서 연결된다. 대시에 따라 몸을 숙이는 변형 외 몸체가 길게 늘어나는 신규 결함은 확인하지 못했다.',
   'action':'현재 그림 보존'},
  {'characters':['shibuki'],'scope':'등장 마지막141/142→대기0',
   'finding':'이번 수정된 마지막 복귀 구간이 각 폼의 대기 체형으로 연결된다. 앞선 등장 포즈의 높이 차이는 별개 동작으로 남겨 둔다.',
   'action':'현재 수정본 보존'},
  {'characters':['nana'],'scope':'기본/포스/얼티밋전후 이동·공중·대시·승리',
   'finding':'고정 원점에서 머리와 다리 크기의 급변, 어깨/허리의 비어 있는 연결부, 새 검은 잔점을 확정하지 못했다. 포스 맨다리와 짧은 구두 경계도 이동 전반에서 유지된다.',
   'action':'현재 그림 보존'},
 ],
 'runtime_observation':{
   'path':'work/sprite_consistency_20261105/runtime/nana_base/contact.png','view_image_opened':True,
   'source_video':'work/sprite_consistency_20261105/runtime/nana_base/play.webp',
   'scope':'실제 Nana 기본형 영상의 12장 접촉시트를 직접 확인; 영상 전체 프레임 재검수 아님',
   'finding':'표시된 대기·걷기·공중·대시·사격 장면에서 몸 크기의 급변·관절 단절은 뚜렷하지 않음'},
 'unconfirmed_observations':[
   {'id':'fourth_arrival_transient_costume','character':'shibuki','form':'fourth',
    'animation_id':2,'refs':[133,135],
    'finding':'고정 full-mask 검토 시트에서는 기본 붉은 의상 일부가 보인다.',
    'why_not_confirmed_defect':'등장 중 임시 아머 마스크와 이벤트에 따른 레이어 전환이 있다. 고정 폼의 미리보기만으로 실제 누락을 단정할 수 없다.',
    'next':'실제 포스 등장 장면에서 이벤트·armor 필드·표시 프레임을 함께 관찰한 뒤 필요할 경우에만 수정',
    'art_change_made':False}],
 'fourth_arm_variants_for_reviewed_refs':arms,
 'remaining_visual_scope':['이번 목록 밖 공격·특수기·피격·벽·사다리의 연속 연결',
                            '각 부분파츠의 모든 조합에 대한 연속 미술 검토',
                            '실시간 효과 객체·팔레트 섬광·무기와 몸체의 동기',
                            '실제 점프 궤적·벽 충돌·착지에 따른 체감 연결'],
 'confirmed_new_art_defects':[],
 'art_or_archive_modified':False,'emulator_controlled':False,
 'conclusion':'이번 주요 연속 스텝 미술 검토에서는 추가 수정할 확정 결함을 발견하지 못했다. 현재 그림을 보존하며 실제 플레이 관찰을 이어가는 것이 타당하다.'
}
(HERE/'art_review/findings.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'viewed_forms':len(viewed),'sequences':report['browser_sequence_count'],
                  'steps':report['browser_step_count'],'arm_equal':sum(x['rendered_png_equal'] for x in arms),
                  'arm_total':len(arms),'confirmed_new_art_defects':0}))
