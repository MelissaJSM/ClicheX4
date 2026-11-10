"""차량 작은 머리의 원US/BR29 caller와 의상 분기만 읽는다. 실행·패킹 없음."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import animation_map
OUT=Path(__file__).resolve().parent
assert not (OUT/'report.json').exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
tracked={}
def rel(p):return p.relative_to(ROOT).as_posix()
def read(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 tracked[rel(p)]=h.hexdigest();return h.hexdigest()
sources={
 'US':(ROOT/'MegaMan X4.bin','3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'),
 'BR29':(ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v29/shibuki_riko.bin','753928a3cf2101caabf05cbe112217aa6d4b95b6320674632692831297a52252')}
ex={}
for tag,(p,h) in sources.items():
 assert digest(p)==h
 ex[tag]=read_disc(p,('SLUS_005.61',))[0]['SLUS_005.61']
 assert struct.unpack_from('<I',ex[tag],24)[0]==0x80010000
def code(tag,lo,hi):return ex[tag][lo-0x80010000+2048:hi-0x80010000+2048]
cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
ranges=[]
for name,lo,hi in (
 ('mech_player_animation_writer',0x8003dc1c,0x8003dc44),
 ('mech_state_machine',0x8003d3f8,0x80040608),
 ('player_normal_update',0x800312b4,0x80031410),
 ('player_ride',0x80032e94,0x80032f64),
 ('player_entry_ride',0x80035a24,0x80035a6c),
 ('player_set_animation',0x800350a4,0x8003516c),
 ('object_animation_update',0x80015dc8,0x80015e94),
 ('player_draw_dispatcher',0x80023e70,0x80023ed0),
 ('armor_wrapper',0x800257bc,0x8002588c),
 ('partial_renderer',0x8002588c,0x80025cdc)):
 u=code('US',lo,hi);b=code('BR29',lo,hi)
 if name!='armor_wrapper':assert u==b,name
 rec={'name':name,'start':hex(lo),'end_exclusive':hex(hi),'US_exact':u==b,'US_sha256':sha(u),'BR29_sha256':sha(b)}
 for tag in ('US','BR29') if name=='armor_wrapper' else ('BR29',):
  if name=='mech_state_machine':continue
  p=OUT/f'{name}_{tag}.txt'
  p.write_text('\n'.join(f'{i.address:08x} {bytes(i.bytes).hex()} {i.mnemonic} {i.op_str}'for i in cs.disasm(code(tag,lo,hi),lo))+'\n',encoding='utf-8')
  rec[tag+'_disassembly']=rel(p);read(p)
 ranges.append(rec)
state_addr=0x800f8990+18*4
assert code('US',state_addr,state_addr+4)==code('BR29',state_addr,state_addr+4)
assert struct.unpack('<I',code('BR29',state_addr,state_addr+4))[0]==0x80032e94
seq,refs=animation_map(ex['BR29']);useq,urefs=animation_map(ex['US'])
headrefs=set(range(184,204));seqs=[]
for s in seq:
 if headrefs&{q['frame']for q in s['steps']}:
  assert s==useq[s['id']]
  seqs.append(s)
calls=[]
ins=list(cs.disasm(code('BR29',0x8003d3f8,0x80040608),0x8003d3f8))
for j,i in enumerate(ins):
 if i.mnemonic=='jal' and i.op_str=='0x8003dc1c':
  nearby=ins[max(0,j-4):j+2]
  vals=[q for q in nearby if q.mnemonic=='addiu' and q.op_str.startswith('$a1, $zero, ')]
  val=int(vals[-1].op_str.rsplit(', ',1)[1],0) if vals else None
  calls.append({'call':hex(i.address),'animation_id_nearby_immediate':val,'context':[f'{q.address:08x} {q.mnemonic} {q.op_str}'for q in nearby]})
for p in ('work/research/decomp/src/main/mech.c','work/research/decomp/src/main/player.c','work/research/decomp/src/main/player_common.c','work/research/decomp/src/main/14A60.c','work/research/decomp/include/obj.h','work/research/decomp/config/symbols.us.txt','scripts/ultimate_costume_renderer.py','config/shibuki_x_us.json','work/sprite_style_unification_20261107/shibuki_audit/vehicle_head_accessory_read01/conclusions.json'):
 read(ROOT/p)
read(Path(__file__))
report={
 'scope':'원US+BR29 작은차량머리184..203 caller/부분아머·Ultimate 마스크 분기 독립 읽기. 원화/ARC 검사와 MIPS 실행은 범위 밖.',
 'EXE_sha256':{k:sha(v)for k,v in ex.items()},'code_ranges':ranges,
 'player_normal_state18':{'address':hex(state_addr),'target':'0x80032e94','US_exact':True},
 'head_animation_tables_US_exact':seqs,'head_ref_to_animation_ids':{str(n):refs[n]for n in sorted(headrefs)},
 'mech_calls_to_player_animation_writer':calls,
 'mask_decision':{
  'US_all_X_frames':'g_Player+0xA7 = 0x8014196F의 실제 아머 비트; 작은머리 예외 없음',
  'BR29_non_Ultimate':'engine+0x37(0x801721F7)==0이면 g_Player+0xA7 사용',
  'BR29_Ultimate':'engine+0x37 !=0이면 engine+0x47(0x80172207)==0 또는 frame217..230일 때15, 그밖0',
  'BR29_small_heads184_203':'217..230 범위밖. 획득전engine armor0은mask15, 획득후nonzero는mask0. g_Player+0xA7 일시값과 독립.',
  'field_name_correction':'0xA7은 player 오프셋이며 engine의 소유 아머는0x47이다.',
  'part_calls':[{'bit':8,'composition_bank':8,'a1':3},{'bit':1,'composition_bank':5,'a1':0},{'bit':4,'composition_bank':7,'a1':2},{'bit':2,'composition_bank':6,'a1':1}],
  'CLUT':'부위5/6/8은0x7843,팔7은player+0xB8=2일때0x7844 아니면0x7843'},
 'findings':[
  'mech 0x8003DC1C는 조건부로 g_Player.ride_animation을 쓰고 unk6을0으로 한다. 별도머리 렌더러 호출이 아니다.',
  '정상상태18→player_ride는 ride_animation으로 player_set_animation을 호출한 뒤 일반 animate_object를 사용한다.',
  '원 dispatcher는 화면활성 player에 본체0x80024334를 그리고 X(kind0)일때0x800257BC를 호출한다. 프레임184..203 배제 조건이 없다.',
  'BR29 wrapper만원US와다르며 그 아래partialrenderer는전체비교범위원USexact다.',
  '198이실제로빈그림인지는동료ARC감사범위이며caller는198만특별히제외하지않는다.',
  '작은머리전용표현/타참조빈층공유는자산구조이며코드가layer5를항상무시하는것으로해석하면안된다.'
 ],
 'limits':['MIPS/실기 실행 없음','개별조종석 장면 도달/가림순서/시각수용 미검증','ARC/빈678/19별칭은HUD 별도검사','원본·게임·입력 변경 없음'],
 'inputs':tracked}
p=OUT/'report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report_sha256':sha(p.read_bytes()),'EXE_sha256':report['EXE_sha256'],'table_ids':[s['id']for s in seqs],'refs':report['head_ref_to_animation_ids'],'writer_calls':len(calls),'ranges':[{k:r[k]for k in ('name','US_exact')}for r in ranges]},ensure_ascii=False))
