from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
def rec(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
e=json.loads((R/'rn40_nova_play/evidence.json').read_text('utf8'))
m=json.loads((R/'rn40_nova_review01/manifest.json').read_text('utf8'))
assert e['bin_sha256']=='fdcebed25fb3ffde641d9a6fc5f56180e74f2d3367057eea2f70c5123ac613b9'
assert len(e['capture_times'])==112 and m['mapping']['encoded_frames']==112
seen=[R/'rn40_stage_play/last.png',R/'rn40_nova_play/contact.png',*sorted((R/'rn40_nova_review01').glob('*.png'))]
assert len(seen)==6
p=R/'rn40_nova_summary.json';assert not p.exists()
result={'project':'ver_rin_nana','bin_sha256':e['bin_sha256'],'session':e['session'],'fresh_boot':True,'source_asset_sha256':'1ec00de5164827c5dd5322b93b7060e11a1afbddd26bacb23f5b585e63715195','recorded_captures':112,'encoded_frames':112,'actually_viewed_files':[dict(rec(f),actually_viewed=True)for f in seen],'observations':['복사 카드 DATA3의 획득 후 Ultimate에서 양방향 R2 노바를 실제 발동했다.','새 준비 자세·돌진·원래 점멸 효과·복귀를 확인했다. 관찰 표본에서 추가 확정 몸 분리나 갑작스러운 크기 도약을 찾지 못했다.','점멸 중 단색 실루엣과 공격 이펙트가 몸을 가리므로 모든 몸체 픽셀의 실기 가시성 검증은 아니다.'],'limits':['약16Hz 창 캡처이며 60Hz 전수 또는 참조별 RAM/GPU 추적은 수행하지 않았다.','게임판정·이펙트 자체는 기존 동작이며 신규 효과 디자인 검토가 아니다.','획득 전 의상 및 부분 아머의 실기 검증이 아니다.'],'evidence':[rec(R/f)for f in ['rn40_stage_play/evidence.json','rn40_nova_play/evidence.json','rn40_nova_review01/manifest.json','rn40_load_ultimate.json','rn40_hq.json']],'protection':rec(R.parent/'protection_checkpoint48.json'),'session_closed':True,'memory_written':False,'F1_F3_sent':False,'whole_project_complete':False}
p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rec(p)))
