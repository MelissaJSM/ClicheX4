"""체이서 원시간표65..76 및 실제 호출/선택사본 매핑 읽기 보충."""
from pathlib import Path
import ast,hashlib,json,struct,sys
import capstone
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;O=D/'shibuki_chaser_sequences01';assert not O.exists()
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import animation_map
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
plan=json.loads(blob(W/'staging_br_v24.json'));disc=ROOT/plan['source_bin'] if 'source_bin'in plan else None
# staging의 출력 이미지를 명시적으로 선택한다.
disc=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v24/shibuki_riko.bin'
original,_=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61',));current,_=read_disc(disc,('SLUS_005.61',))
oe,ce=original['SLUS_005.61'],current['SLUS_005.61'];oa,orr=animation_map(oe);ca,crr=animation_map(ce);seq=[]
off=lambda a:a-0x80010000+2048
for n in range(65,77):
 q=oa[n];assert q==ca[n]
 seq.append({'id':n,'address':hex(q['address']),'steps':q['steps'],'loop_to':q['loop_to'],'one_walk_duration_sum':sum(v['duration_ticks']for v in q['steps']),'original_current_exact':True})
used=sorted({v for n in range(162,175)for v in orr[n]});assert used==list(range(65,77))
cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
O.mkdir(exist_ok=False);blocks=[]
for name,lo,hi in(('player_ride',0x80032e94,0x80032f6c),('ride_animation_writer',0x8003b458,0x8003b470),('bike_animation_callers',0x8003b470,0x8003d01c)):
 v=oe[off(lo):off(hi)];assert v==ce[off(lo):off(hi)]
 ins=list(cs.disasm(v,lo));lines=[f'{i.address:08x} {i.mnemonic} {i.op_str}'for i in ins]
 if name=='bike_animation_callers':
  selected=set()
  for i,t in enumerate(ins):
   if t.mnemonic=='jal'and t.op_str=='0x8003b458':selected.update(range(max(0,i-5),min(len(ins),i+3)))
  lines=[lines[i]for i in sorted(selected)]
 p=O/(name+'.txt');p.write_text('\n'.join(lines)+'\n','utf8');blocks.append({'name':name,'range':[hex(lo),hex(hi)],'original_current_exact':True,'sha256':sha(v),'disassembly':rel(p)})
tables=[]
for ad,name in((0x800f910c,'acceleration'),(0x800f9110,'recovery'),(0x800f9114,'normal')):
 v=oe[off(ad):off(ad)+4];assert v==ce[off(ad):off(ad)+4];tables.append({'address':hex(ad),'meaning_from_decomp':name,'u8_values':list(v),'original_current_exact':True})
src=ROOT/'scripts/prepare_shibuki_ui.py';tree=ast.parse(blob(src).decode('utf8'));maps=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='mapping'for t in node.targets):
  try:maps.append(ast.literal_eval(node.value))
  except(ValueError,TypeError):pass
mapping=next(v for v in maps if v.get(1)==85 and v.get(18)==207);assert not(set(mapping.values())&set(range(162,175)))
for p in(ROOT/'work/research/decomp/src/main/bike.c',ROOT/'work/research/decomp/src/main/player.c',W/'shibuki_audit/chaser_sources01/report.json'):blob(p)
r={'scope':'Shibuki 체이서162..174의 원표/호출·선택사본 읽기 보충','current_disc':rel(disc),'current_EXE_sha256':sha(ce),'original_EXE_sha256':sha(oe),'animations':seq,'only_animation_ids_using_162_174':used,'original_MIPS_read_blocks':blocks,'selector_tables':tables,'selection_mapping_from_existing_production':mapping,'selected_chaser_UI_copies_found':False,'interpretation':['player_ride는 ride_state가 살아 있고 unk6==0일 때 ride_animation을 player_set_animation에 전달하고 이후 animate_object를 호출한다. bike의8003B458은 player ride_animation 저장과 unk6=0만 수행한다.','0x41/43/45(65/67/69)는 차량 기울기 인덱스에 따라 선택하는 기본 자세이고,0x42/44/46(66/68/70)은 대응 착지/흔들림이다. 테이블0x800F910C가73/72/71,0x800F9110가76/75/74,0x800F9114가69/67/65를 인덱스순으로 제공한다.','표의 duration 합은 해당 경로를 한 번 걷는 animation 호출수의 합이다. relative_step0의 정지/루프와 외부 상태전환이 있으므로 그 합을 실제 게임의 전체 동작 길이나 초로 부르지 않는다.','기존 ST0E 선택 소형사본의 명시 매핑은0,85..92,207,156..159,161이며 체이서162..174가 없다. 저장화면은0 몸/부분아머 재사용이다. 다른 임의 리소스에 그림이 전혀 없다는 전역 부재 증명으로 확대하지 않는다.','원US/현재 BR24 EXE의 위 표와 호출블록은 byte exact다. PC/Saturn용 decomp의 함수 이름/조건 해석은 원MIPS 호출창과 분리하여 기록했다.'],'source_hashes':tracked,'new_MIPS_execution':False,'runtime_verified':False,'producer_functions_called':False}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'animations':[{'id':q['id'],'refs':[s['frame']for s in q['steps']],'durations':[s['duration_ticks']for s in q['steps']],'loop_to':q['loop_to']}for q in seq]}))
