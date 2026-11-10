"""실제 MIPS animate_object로 표의 prefix+두 주기 시간선을 독립 실행한다."""
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
from unicorn import mips_const as m, UC_HOOK_CODE

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.export_sprite_playback import read_disc, EXE_SHA, digest

HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'manifest.json').read_text('utf8'))
source=manifest['sources']['ver_rin_nana']
assert digest(ROOT/source['bin'])==source['bin_sha256']
exe=read_disc(ROOT/source['bin'],['SLUS_005.61'])['SLUS_005.61']
assert hashlib.sha256(exe).hexdigest()==EXE_SHA
spec=importlib.util.spec_from_file_location('native_contracts',ROOT/'work/ultimate_costume_swap_20261105/audit/native_contracts.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

animations={}
for char in manifest['characters'].values():
    for form in char['forms'].values():
        for animation in form['animations']:
            animations.setdefault(animation['address'],animation)

rows=[];total=0
for address,animation in animations.items():
    u=helper.cpu(exe)
    obj=0xA000
    steps=animation['steps']
    u.mem_write(obj+0x34,struct.pack('<I',int(address,16)))
    u.mem_write(obj+0x44,bytes.fromhex(steps[0]['bytes']))
    loop=animation['loop_start_index']
    sequence=steps[:loop]+steps[loop:]+steps[loop:]
    def stop(mu,pc,size,_):
        if pc==helper.RETURN:mu.emu_stop()
    hook=u.hook_add(UC_HOOK_CODE,stop)
    calls=0
    for step in sequence:
        for tick in range(step['duration_calls']):
            actual_pointer=struct.unpack('<I',u.mem_read(obj+0x34,4))[0]
            actual=bytes(u.mem_read(obj+0x44,4))
            assert actual_pointer==int(step['address'],16),(address,calls,actual_pointer,step)
            assert actual[1:]==bytes.fromhex(step['bytes'])[1:],(address,calls,actual.hex(),step)
            assert actual[0]==(step['duration_calls']-tick)&255
            u.reg_write(m.UC_MIPS_REG_A0,0x80000000+obj)
            u.reg_write(m.UC_MIPS_REG_RA,helper.RETURN)
            u.emu_start(0x80015DC8,0,count=1000)
            assert u.reg_read(m.UC_MIPS_REG_PC)==helper.RETURN
            calls+=1
    u.hook_del(hook)
    expected_next=steps[loop]
    assert struct.unpack('<I',u.mem_read(obj+0x34,4))[0]==int(expected_next['address'],16)
    assert bytes(u.mem_read(obj+0x44,4))==bytes.fromhex(expected_next['bytes'])
    rows.append({'address':address,'calls':calls,'prefix_calls':animation['prefix_calls'],
                 'loop_calls':animation['loop_calls'],'loop_to_position':animation['loop_to_position'],
                 'terminal_position':animation['terminal_position'],'passed':True})
    total+=calls

report={'passed':True,'scope':'최신 EXE의 실제 MIPS animate_object만 격리 RAM에서 실행; 게임 플레이·이벤트 핸들러 실행 아님',
        'source':source,'manifest_sha256':digest(HERE/'manifest.json'),'native_function':'0x80015DC8',
        'unique_sequence_addresses':len(rows),'actual_native_update_calls':total,
        'checks':['각 호출 전 cursor 주소·프레임·event·relative_step·남은 duration 일치',
                  '모든 고유 시퀀스의 prefix 뒤 두 주기 및 다음 복귀 주소 일치',
                  'terminal relative_step0도 원래 자기참조를 유지; 외부 상태 전환은 시험하지 않음'],
        'sequences':rows}
(HERE/'native_timeline.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'unique_sequences':len(rows),'native_calls':total}))
