"""검증된 ePSXe 세션의 메뉴/플레이어 상태만 짧게 읽는다. 입력·쓰기 없음."""
import argparse
import importlib.util
import json
import re
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess, EXPECTED, need
from scripts.audit_sprite_consistency_coverage import file_sha, read_assets, exe_slice, sha

def main(args):
    session = args.session.resolve()
    projects = [p for p in EXPECTED if session.is_relative_to(ROOT/'work'/p/'emulator_sessions')]
    need(len(projects) == 1, 'Session outside known project')
    project = projects[0]
    rec = json.loads((session/'session.local.json').read_text('utf8'))
    need(rec['pid'] == args.pid, 'PID differs from session')
    cue = Path(rec['cue'])
    match = re.match(r'FILE "([^"\r\n]+)" BINARY', cue.read_text('ascii'))
    need(match and Path(match[1]).name == match[1], 'Unexpected CUE')
    game = cue.parent/match[1]
    pointer = json.loads((ROOT/'projects'/project/'current_build.json').read_text('utf8'))
    manifest = json.loads((game.parent/'manifest.json').read_text('utf8'))
    need(file_sha(game) == rec['bin_sha256'] == {'ver_buki_riko': '963ccbd41c71819bec1c594b0314683273972c08d85db3925a75b9599f060ea1', 'ver_rin_nana': '0000000000000000000000000000000000000000000000000000000000000000'}[project] == manifest['modified_bin']['sha256'],
         'Disc differs from hash-bound checkpoint17 BR build')
    exe = read_assets(game, ['SLUS_005.61'])[0]['SLUS_005.61']
    need(sha(exe) in {'1789ef719487b3e49571ccc2f419d6eb36c16f03709a16cb74f856d433f699ab',
                      '93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616'},
         'Unexpected native code')
    need(0 < args.ram_base < 2**48, 'Invalid host RAM base')
    proc = ReadOnlyProcess(rec)
    total = 0
    try:
        def read(offset, size):
            nonlocal total
            need(0 <= offset <= 0x200000-size, 'RAM range')
            total += size
            return proc.read(args.ram_base+offset, size)
        anchors = [0x1540C, 0x15ECC, 0x233C8, 0x23400, 0xEA20C]
        for address in anchors:
            need(read(address,48) == exe_slice(exe,address|0x80000000,48), 'Native RAM anchor mismatch: '+hex(address))
        gi=read(0x173C70,16); e=read(0x1721C0,100); t=read(0x141BD8,12)
        m=read(0x1721B0,16); p=read(0x1418C8,228); pads=read(0x166C08,6)
        ptr=struct.unpack_from('<I',m,12)[0]
        record=read(ptr & 0x1FFFFF,42) if 0x80000000 <= ptr <= 0x801FFFD6 else None
        gi2=read(0x173C70,4); e2=read(0x1721C0,4); cur2=read(0x141BDF,1)
        report={'passed':True,'utc':datetime.now(timezone.utc).isoformat(),'project':project,'pid':args.pid,
                'ram_base':args.ram_base,'native_anchors_verified':len(anchors),'ram_bytes_read':total,
                'state_sample_stable':gi[:4]==gi2 and e[:4]==e2 and t[7:8]==cur2,
                'game_info':{'route':gi[0],'mode':gi[1],'title_cursor':gi[2],'subvalue':gi[3],
                             'value4':struct.unpack_from('<h',gi,4)[0],'value6':struct.unpack_from('<h',gi,6)[0],
                             'option_count':struct.unpack_from('<h',gi,8)[0],'input_phase':gi[13],'hex':gi.hex()},
                'engine':{'state':e[0],'substate':e[1],'subsubstate':e[2],'mission_cursor':e[3],
                          'stage':e[12],'area':e[13],'character':e[0x43],'armor':e[0x47],
                          'arm_type':e[0x48],'ultimate_black':e[0x37],'boss_flags':e[0x59],'progress':e[0x5F]},
                'transition_active':t[4],'menu_cursor':t[7],'native_frame_counter':struct.unpack_from('<I',t)[0],
                'card_menu':{'card_status':list(m[4:6]),'port':m[6],'data_index':m[7],
                             'result':m[8],'operation':m[9],'timer':m[10],
                             'record_pointer':hex(ptr),'pointed_record_hex':record.hex() if record else None},
                'player':{'active':p[0],'state':p[1],'character':p[2],'animation':p[0x17],
                          'frame':p[0x47],'hp':p[0x5C],'weapon':p[0x93],'armor':p[0xA7],
                          'gfx_ptr':hex(struct.unpack_from('<I',p,0x38)[0]),
                          'parts_ptr':hex(struct.unpack_from('<I',p,0x3C)[0])},
                'controller':dict(zip(('held','previous','pressed'),struct.unpack('<3H',pads))),
                'inputs_sent':False,'memory_written':False,'files_written':False,
                'limitation':'이전 전환과 함께 판독해야 함. game_info/player가 현재 화면과 무관하게 남을 수 있으며 자원/GPU 일치 검사는 별도.'}
        print(json.dumps(report,ensure_ascii=False),flush=True)
    finally:
        proc.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session',type=Path,required=True)
    parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--ram-base',type=int,required=True)
    main(parser.parse_args())
