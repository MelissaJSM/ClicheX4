from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
D=Path(__file__).parent
O=D/'nana_ultimate_nova8_independent01'
sha=lambda b:hashlib.sha256(b).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
p=O/'report.json'
r=json.loads(p.read_text('utf8'))
assert sha(p.read_bytes())=='3423784d767d94e69d275398c5490cd97fcfc29330282a3fa4cdb05ca8969b17'
for s in r['readback_sheets']:assert sha((ROOT/s['path']).read_bytes())==s['sha256']
v={
 'scope':'Nana Ultimate Nova 최종 1ec00de5 독립 재추출 8판의 실제 정적 열람',
 'candidate_sha256':r['candidate_sha256'],'report':rel(p),'report_sha256':sha(p.read_bytes()),
 'actually_viewed':r['readback_sheets'],
 'observations':[
  '213/215 양 의상의 새 머릿결·귀·의상 명암과 접힌 다리/신발의 분리가 이전보다 선명하다. 215 머리 옆 높은 주먹에서 팔꿈치와 어깨로 이어지는 굽힌 팔이 보이며 후폼에 남은 명백한 옛 소매나 제3의 팔을 찾지 못했다.',
  '준비 순서 213→215→216→214→217을 같은 원점으로 열람했다. 213/214와 215/216의 현재 Nana 동형 정책을 보존하고, 펼친 준비 자세에서 낮게 접힌 돌진 자세로 이어진다. 원 시간표 속 실제 재생 속도와 신체 흔들림을 이 정지판만으로 검증하지 않는다.',
  '217 새 얼굴·앞 주먹·접힌 하체는 효과 없는 판과 218/220 효과 합성판에서 같은 실루엣으로 읽힌다. 머리와 팔/몸 사이에 새로 생긴 명백한 절단이나 구형 몸체 잔상을 찾지 못했다.',
  '218/220의 새 몸체 주변 효과 면은 이어지고 220의 오른쪽 긴 광선 끝까지 판에 포함됐다. 색이 달라진 작은 셀을 임의 잡티로 분류하지 않았다. 기술 보고서의 외부 효과 보존과 새 몸체 주변 재계산 범위를 유지하며 전체 효과 byte exact라고 하지 않는다.',
  '219는 새217 실루엣의 Manhattan 2 팽창으로 만든 별도 섬광이다. 효과 순서 217→218→219→220에서 머리카락과 접힌 하체 형태가 대응함을 확인했다.',
  '준비판의 217 before/after 열은 비교용 마스크 조합이다. 실제217..220은 원 renderer의 mask15 강제 상태이므로 두 개의 실제 의상 상태로 세지 않는다.'
 ],
 'producer_functions_called':False,'source_generation7_cells_requantized':False,
 'new_MIPS_execution':False,'runtime_verified':False,'final_user_art_acceptance':False,
 'overall_complete':False,
 'limits':['최초 생성 7셀의 RGB→색인 양자화는 제작자 증거이며 직접 반복하지 않았다. 등록 색인 이후 출처·국소 팔·의상·효과 규칙과 40층은 독립 재구성했다.','256부분 조합은 정적 포맷 검증이며 실제 모든 부분 아머 동작을 뜻하지 않는다. 새 원MIPS/원표 재생/실기는 이 읽기 검사의 범위 밖이다.']
}
p=O/'visual.json';assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
inputs=dict(r['inputs'])
for q in [D/'verify_nana_ultimate_nova8_independent.py',D/'verify_shibuki_ultimate_hurt13_independent.py',Path(__file__),O/'report.json',p]+[ROOT/s['path']for s in r['readback_sheets']]:inputs[rel(q)]=sha(q.read_bytes())
for name,h in inputs.items():assert sha((ROOT/name).read_bytes())==h,name
p=O/'READER_LOCK.json';assert not p.exists();p.write_text(json.dumps({'count':len(inputs),'inputs':inputs,'candidate_sha256':r['candidate_sha256'],'producer_calls':False,'source_writes':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'visual_sha256':sha((O/'visual.json').read_bytes()),'lock_sha256':sha(p.read_bytes()),'inputs':len(inputs)}))
