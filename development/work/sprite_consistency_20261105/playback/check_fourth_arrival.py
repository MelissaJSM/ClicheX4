"""포스 등장 임시 아머/표시 분기를 최신 실제 MIPS로 읽기 전용 검증한다."""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE,mips_const as m
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_sprite_playback import read_disc,digest,at,EXE_SHA
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'manifest.json').read_text('utf8'))
source=manifest['sources']['ver_buki_riko'];assert digest(ROOT/source['bin'])==source['bin_sha256']
exe=read_disc(ROOT/source['bin'],['SLUS_005.61'])['SLUS_005.61'];assert hashlib.sha256(exe).hexdigest()==EXE_SHA
original=read_disc(ROOT/'MegaMan X4.bin',['SLUS_005.61'])['SLUS_005.61']
assert at(exe,0x80031410,0x130)==at(original,0x80031410,0x130)
assert at(exe,0x8002A728,0x24)==at(original,0x8002A728,0x24)
spec=importlib.util.spec_from_file_location('nc',ROOT/'work/ultimate_costume_swap_20261105/audit/native_contracts.py')
nc=importlib.util.module_from_spec(spec);spec.loader.exec_module(nc)
u=nc.cpu(exe);PLAYER=0x1418C8;ENGINE=0x1721C0;END=nc.RETURN
u.mem_write(PLAYER,bytes([0xA5])*0xE4)
u.reg_write(m.UC_MIPS_REG_A0,PLAYER|0x80000000);nc.finish(u,0x8002A728)
assert u.mem_read(PLAYER+0xA7,1)==b'\0' and u.mem_read(PLAYER+0xB8,1)==b'\0'
# Stage ownership is separate from the just-reset player object's transient fields.
u.mem_write(ENGINE+0x47,b'\x0f');u.mem_write(ENGINE+0x48,b'\x02');u.mem_write(ENGINE+0x37,b'\0')
u.mem_write(PLAYER+6,b'\x01') # grounded phase of beam-in, after animation2 selection
anim=manifest['characters']['shibuki']['forms']['fourth']['animations'][2]
u.mem_write(PLAYER+0x34,struct.pack('<I',int(anim['address'],16)))
u.mem_write(PLAYER+0x44,bytes.fromhex(anim['steps'][0]['bytes']))

draw_calls=[];entered_idle=False
def observe(mu,pc,size,_):
    global entered_idle
    if pc==0x8002588C:draw_calls.append(mu.reg_read(m.UC_MIPS_REG_A1))
    if pc==0x800343A4:
        entered_idle=True;mu.emu_stop()
    elif pc==END:mu.emu_stop()

# The bounded display selector is native code; the rasterizing callee is replaced
# only inside this isolated CPU so its selected part IDs can be observed.
u.mem_write(0x2588C,bytes.fromhex('0800e00300000000'))
u.hook_add(UC_HOOK_CODE,observe)
rows=[];seen=set();calls=0
def run(entry):
    u.reg_write(m.UC_MIPS_REG_A0,PLAYER|0x80000000);u.reg_write(m.UC_MIPS_REG_RA,END)
    u.emu_start(entry,0,count=10000)

while not entered_idle:
    cursor,=struct.unpack('<I',u.mem_read(PLAYER+0x34,4))
    state=bytes(u.mem_read(PLAYER+0x44,4));frame=state[3]
    armor=u.mem_read(PLAYER+0xA7,1)[0];arm=u.mem_read(PLAYER+0xB8,1)[0]
    draw_calls.clear();run(0x800257BC)
    assert draw_calls==([3,0,2,1] if armor==15 else [])
    if cursor not in seen:
        seen.add(cursor);rows.append({'native_call_before_frame':calls,'cursor':hex(cursor),'ref':frame,
          'position':(cursor-int(anim['address'],16))//4,'player_transient_armor':armor,'player_arm_type':arm,
          'engine_owned_armor':u.mem_read(ENGINE+0x47,1)[0],
          'native_renderer_parts':list(draw_calls),'event_after_caller':state[1]})
    run(0x80031410);calls+=1
    assert calls<500
assert all(x['player_transient_armor']==0 for x in rows if x['ref'] in (133,135,136,137,138,139))
assert all(x['player_transient_armor']==15 and x['player_arm_type']==2 for x in rows if x['ref'] in (140,141,142))
report={'passed':True,'source':source,'scope':'최신 실제 reset_entity/player_beam_in/의상 표시 선택 함수를 격리 MIPS 실행; GPU와 실제 게임 입력은 실행하지 않음',
        'reset_entity_zeroes_transient_armor':True,'beam_in_native_code_original_exact':True,
        'input_sequence_id':2,'owned_armor':15,'ultimate':0,'calls_until_idle_transition':calls,
        'rows':rows,'conclusion':'133~139는 원래 일시적으로 기본형을 표시한다.140의event1에서소유아머복원후141/142는포스로복귀한다.133/135의기본붉은의상은새누락이아니므로정상전환으로분류.',
        'initialization_evidence':['objects.c:34..41 reset_entity 전체 구조0 초기화','objects.c:71..80 reset_objects→reset_entity(g_Player)',
          'player_common.c:405..543 player_spawn은beam-in전에A7/B8복원을하지않음','player.c:125..157 event에서engine소유값복원'],
        'game_or_save_modified':False,'runtime_emulator_verified':False}
(HERE/'art_review/fourth_arrival_native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'calls':calls,'refs':[x['ref'] for x in rows],'armor':[x['player_transient_armor'] for x in rows]}))
