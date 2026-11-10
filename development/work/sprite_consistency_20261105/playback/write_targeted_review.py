"""직접 열람한 최근 수정 범위의 연속 미술 검토를 기록한다."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent/'art_review'
capture=json.loads((HERE/'targeted/capture.json').read_text('utf8'))
gallery=json.loads((ROOT/'out/sprite_consistency_20261105/gallery_manifest.json').read_text('utf8'))
riko=next(c for c in gallery['characters'] if c['id']=='riko')['revisions']['frames']
targets={'riko':list(riko),'shibuki':[f'{form}_{ref:03d}' for form in ('base','fourth','fourth_arm1') for ref in (101,102,103,104,231,232)],
         'nana':[0,85,86,87,92,115,116,117,118,119]}
coverage=[]
for record in capture['records']:
    frames={s['frame_id'] for a in record['animations'] for s in a['steps']}
    if record['character']=='riko':
        wanted={x for x in targets['riko'] if x.startswith(record['form']+':')}
    elif record['character']=='shibuki':
        wanted={x for x in targets['shibuki'] if x.rsplit('_',1)[0]==record['form']}
    else:wanted={f'fourth_{n:03d}' for n in targets['nana']}
    assert wanted<=frames,(record,wanted-frames)
    coverage.append({'character':record['character'],'form':record['form'],'mask':record.get('mask'),
        'arm':record.get('arm'),'target_frame_ids':sorted(wanted),'all_targets_captured':True,
        'animation_ids':[a['id'] for a in record['animations']],'sheet':record['sheet'],
        'view_image_opened':True})
sheets=sorted({x['sheet'] for x in coverage})
report={'passed_scope_review':True,'confirmed_new_art_defect':False,
 'scope':'최근 수정된 참조를 실제 단독 HTML 타이머로 재생하고 순서별 캡처 시트를 직접 열람; 게임 실기 증거와 구별',
 'html_sha256':capture['html_sha256'],'sheets':[{'path':s,'sha256':hashlib.sha256((ROOT/s).read_bytes()).hexdigest(),'view_image_opened':True} for s in sheets],
 'cases':coverage,'case_count':len(coverage),'sheet_count':len(sheets),
 'animation_count':sum(len(x['animations']) for x in capture['records']),
 'timed_step_count':sum(len(a['steps']) for x in capture['records'] for a in x['animations']),
 'findings':[
  {'character':'riko','forms':['normal','black'],'animations':[13,15,14,94],
   'target_refs':['bank0:38..43','bank1:50,51,53,54,56,57,59,61,63,65'],
   'observation':'최근 머리 교정16참조를 모두 포함한다. 벽 붙기·미끄러짐·벽차기·벽베기 사이 머리 크기와 목·어깨의 연결이 유지된다. 팔을 위로 든 자세는 원래 벽 동작으로 판단하며, 외부 검기 없이 몸체/짧은 손잡이만 보이는 것은 미리보기 범위다.',
   'confirmed_defect':False,'action':'현재 수정본 유지'},
  {'character':'shibuki','forms':['base','fourth','fourth_arm1'],'animations':[99,100,101,102,103],
   'target_refs':[101,102,103,104,231,232],
   'observation':'복원한 머리/의상 명암이 공격 자세의 선과 이어진다. 정면과 웅크린 자세에서 머리 비중이 커 보이는지 대기0·기존 공중39·대시종료81·시작100과 추가 확대 대조했다. 정면 귀 실루엣과 무릎을 접은 자세 차이로 설명 가능한 범위이며, 이 비교만으로 확정 크기 오류라고 판단하지 않았다.',
   'comparison':'work/sprite_consistency_20261105/playback/art_review/targeted/shibuki_head_compare.png',
   'confirmed_defect':False,'action':'실제 화염 효과와 함께 보이는 체감 연결은 root 실기로 보완; 현재 아트 유지'},
  {'character':'nana','form':'partial_fourth','masks':list(range(16)),'arms':[1,2],'animations':[5,88,91],
   'target_refs':targets['nana'],
   'observation':'수정10참조를 32개 파츠/팔 조합에서 모두 포함했다. 머리 없는 다리 조합8/10/12/14에서 이전 떠 있는 검은 베일 경계점은 보이지 않고, 머리 파츠가 있는 조합의 베일 선은 연결된다. 대기↔사격에서 손/어깨의 빈틈이나 체형 급변을 새로 확인하지 못했다.',
   'confirmed_defect':False,'action':'현재 파츠 소유 교정 유지'}],
 'resolved_observation':{'id':'fourth_arrival_transient_costume','status':'정상 원래 임시 아머 전환으로 확정',
   'proof':'work/sprite_consistency_20261105/playback/art_review/fourth_arrival_native.json',
   'detail':'최신 실제 MIPS reset_entity→player_beam_in/표시 선택 검사에서133~139는임시armor0,140event에서소유armor15/arm2복원. 해당코드는원본과동일.',
   'art_fix_required':False,'runtime_emulator_verified':False},
 'limitations':['외부 검기/화염/차지 이펙트의 실시간 GPU 합성은 미술 시뮬레이션에 포함되지 않음',
                '부분 파츠는 이10참조와같이재생한88..91 범위의 검토이며 모든 동작32조합을 이번에 전수 관찰한 것은 아님',
                '이 결과가 사용자 최종 미술 수용이나 실제 모든 기술 플레이 성공을 대신하지 않음'],
 'art_or_game_changes':False}
(HERE/'targeted/findings.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
main=json.loads((HERE/'findings.json').read_text('utf8'))
main['unconfirmed_observations'][0]['resolution']=report['resolved_observation']
main['followup_review']='work/sprite_consistency_20261105/playback/art_review/targeted/findings.json'
(HERE/'findings.json').write_text(json.dumps(main,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sheets':len(sheets),'cases':len(coverage),'animations':report['animation_count'],'steps':report['timed_step_count'],'confirmed_defects':0}))
