"""현재 BIN의 카드 로드 경로를 정적으로 감사한다. 프로세스 접근/입력 없음."""
import json, struct, sys, winreg
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.audit_sprite_consistency_coverage import read_assets, exe_slice, sha, write
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

OUT = Path(__file__).parent

def decode_menu_state(ram):
    """호출자가 이미 검증하여 읽은 2MB RAM만 파싱한다. 프로세스 접근 없음."""
    if len(ram) != 2 * 1024 * 1024:
        raise ValueError('Expected exactly 2 MiB verified PSX RAM')
    e = ram[0x1721C0:0x172224]
    g = ram[0x173C70:0x173C80]
    m = ram[0x1721B0:0x1721C0]
    pointer = struct.unpack_from('<I', m, 12)[0]
    slot = ram[pointer & 0x1FFFFF:(pointer & 0x1FFFFF) + 42] if 0x80000000 <= pointer < 0x80200000 else None
    return {
        'game_info': {'route': g[0], 'mode': g[1], 'title_cursor': g[2], 'input_phase': g[13]},
        'engine': {'state': e[0], 'substate': e[1], 'subsub': e[2], 'mission_cursor': e[3],
                   'stage': e[12], 'area': e[13], 'character': e[0x43], 'armor': e[0x47],
                   'arm_type': e[0x48], 'ultimate_black': e[0x37], 'boss_flags': e[0x59], 'progress': e[0x5F]},
        'transition_active': ram[0x141BDC], 'menu_cursor': ram[0x141BDF],
        'frame_counter': struct.unpack_from('<I', ram, 0x141BD8)[0],
        'controller': dict(zip(('held', 'previous', 'pressed'), struct.unpack_from('<3H', ram, 0x166C08))),
        'card_menu': {'buffer_pointer': struct.unpack_from('<I', m)[0], 'card_status': list(m[4:6]),
                      'port': m[6], 'selected_data': m[7], 'result': m[8], 'operation': m[9],
                      'timer': m[10], 'record_pointer': pointer, 'pointed_record_hex': slot.hex() if slot else None},
        'scope': '상태값만 파싱. 활성 스케줄러/화면 판정은 호출자가 이전 전환과 함께 확인해야 하며 오래 남은 game_info만으로 현재 화면을 단정하지 않는다.'}

def main():
    inventory = json.loads((OUT/'runtime_card_inventory.json').read_text('utf8'))
    exes = {mode: read_assets(ROOT/item['bin'], ['SLUS_005.61'])[0]['SLUS_005.61'] for mode,item in inventory['builds'].items()}
    exe = exes['ver_rin_nana']; assert exe == exes['ver_buki_riko']
    assert sha(exe) == '1789ef719487b3e49571ccc2f419d6eb36c16f03709a16cb74f856d433f699ab'
    original = read_assets(ROOT/'MegaMan X4.bin', ['SLUS_005.61'])[0]['SLUS_005.61']
    ranges = [(0x8001AA98,0x8001B644), (0x8001C210,0x8001C30C),
              (0x8001D8DC,0x8001DAD0), (0x8001EC90,0x8001F118),
              (0x8002E7BC,0x8002ED80)]
    proof=[]
    for lo,hi in ranges:
        a=exe_slice(exe,lo,hi-lo); b=exe_slice(original,lo,hi-lo)
        proof.append({'start':hex(lo),'end_exclusive':hex(hi),'sha256':sha(a),'original_native_code_equal':a==b})
        assert a==b,(hex(lo),'Menu branch differs from original US')
    cards=[0x8001AA98,0x8001ABDC,0x8001AE8C,0x8001B10C,0x8001B388,0x8001B4E4,0x8001B558]
    assert list(struct.unpack('<7I',exe_slice(exe,0x800F1FA0,28)))==cards
    mission=list(exe_slice(exe,0x800F474C,12)); assert mission==[1,6,7,4,5,3,8,2,9,10,11,0]
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\epsxe\config') as key:
        pad=list(map(int,winreg.QueryValueEx(key,'Pad1')[0].split(',')))
    assert len(pad)==16
    mapping={k:{'pad_index':i,'directinput_scan':pad[i],'scan_without_extended':pad[i]&127,'extended':bool(pad[i]&128)}
             for k,i in {'left':0,'right':1,'up':2,'down':3,'triangle':4,'circle':5,'cross_confirm':6,'square':7,'start':12}.items()}
    dis=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
    excerpts={hex(lo):['%08X %s %s'%(i.address,i.mnemonic,i.op_str)for i in dis.disasm(exe_slice(exe,lo,n),lo)]
              for lo,n in [(0x8001AA98,128),(0x8001D8DC,72),(0x8002ED20,44)]}
    report={'passed':True,'checked_utc':datetime.now(timezone.utc).isoformat(),'exe_sha256':sha(exe),
            'native_code_ranges':proof,'card_load_substates':list(map(hex,cards)),'mission_order':mission,
            'native_address_evidence':excerpts,'pad1_current':pad,'mapping':mapping,
            'process_read':False,'inputs_sent':False,'card_writes':False,
            'limitations':['정적 메뉴 분기와 키 설정 조회이며 새 실기 메뉴 통과 결과가 아니다.',
                           'D_8015D9C8는 고정 버퍼가 아니라 포인터 전역이다. 슬롯은 memcard_menu의 실제 record_pointer로 읽는다.',
                           'Start는 타이틀/스테이지 선택에서 확인 가능하지만 카드·DATA·YES에서는 Cross를 써야 한다.']}
    write(OUT/'menu_route_native.json',report)
    print(json.dumps({'passed':True,'current_cross':mapping['cross_confirm'],'current_start':mapping['start'],
                      'native_ranges_equal':len(proof),'process_read':False}))

if __name__=='__main__':main()
