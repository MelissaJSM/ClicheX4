"""제공 X6 입력을 읽기 전용으로 검증. 게임/에뮬레이터에 쓰지 않는다."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.inventory_riko_voice import parse_bank
from src.psx_sector import validate_checks
from src.psx_spu_audio import decode_spu
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN
from unicorn.mips_const import UC_MIPS_REG_SP, UC_MIPS_REG_RA, UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3, UC_MIPS_REG_V0
import capstone

EXPECTED = 'e0b5e6b6349bb0f0f487234f52cda43f26754a3d67764b7c306ba75c01e76e1f'
sha = lambda b: hashlib.sha256(b).hexdigest()

def file_sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def main():
    path = ROOT/'MegaManX6.bin'
    before = file_sha(path)
    assert before == EXPECTED, 'Unsupported source'
    checked = set()
    with path.open('rb') as f:
        d = DiscReader(f, path.stat().st_size)
        # ISO record identities were read by inventory.py; independently read boot bytes.
        assert b'SLPM_885.09;1' in d.read(41886, 68)
        exe = d.read(41887, 524288)
        assert exe[:8] == b'PS-X EXE'
        assert struct.unpack_from('<I', exe, 24)[0] == 0x80010000
        assert exe == (OUT/'SLPM_885.09').read_bytes()
        tab = d.read(17047, 4096)
        assets = {}
        for index in (0x55, 0x56):
            rel, size = struct.unpack_from('<II', tab, index*8)
            arc = d.read(17047+rel, size)
            assert arc == (OUT/f'dat_{index:02x}.arc').read_bytes()
            for lba in range(17047+rel, 17047+rel+(size+2047)//2048):
                f.seek(lba*2352)
                validate_checks(f.read(2352))
                checked.add(lba)
            assets[index] = arc
        for lba in range(41887, 41887+256):
            f.seek(lba*2352)
            validate_checks(f.read(2352))
            checked.add(lba)
    def words(va, count):
        return struct.unpack_from('<'+'I'*count, exe, va-0x80010000+2048)
    # Local executable statements, not US hardcoded offsets.
    assert words(0x8003A054, 9) == (0x24040003,0x30420001,0x38450001,0x0C005DE0,0x02203021,0x24040003,0x24050011,0x0C005DE0,0x02203021)
    assert words(0x8003E33C, 6) == (0x0C005DE0,0xA2000003,0x24040003,0x2405000E,0x0C005DE0,0x02003021)
    assert words(0x800744B0, 4) == (0x8003D5B0,0x800359C8,0x8003D644,0x8003D680)
    assert words(0x80074714, 4) == (0x8003E22C,0x8003E2DC,0x8003E380,0x8003E454)
    dis = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
    ranges = [(0x80017780,228),(0x8003A024,84),(0x8003D644,60),(0x8003E22C,340),(0x8005EB18,296)]
    assembly=[]
    for va,size in ranges:
        off=va-0x80010000+2048
        assembly += [f'\n0x{va:08X} len={size} SHA256={sha(exe[off:off+size])}']
        assembly += [f'{x.address:08X}  {x.bytes.hex()}  {x.mnemonic} {x.op_str}' for x in dis.disasm(exe[off:off+size],va)]
    (OUT/'local_code_evidence.txt').write_text('\n'.join(assembly),encoding='utf-8')
    reports = json.loads((OUT/'sound_candidates.json').read_text())
    verified=[]
    for q in reports:
        arc = assets[q['dat_index']]
        es=psx_arc(arc)
        hrec,brec=es[q['header_entry']],es[q['body_entry']]
        h=arc[hrec['offset']:hrec['offset']+hrec['size']]
        body=arc[brec['offset']:brec['offset']+brec['size']]
        bank=parse_bank(h,body,False)
        tbase=bank['vab_offset']+32+128*16
        tone=h[tbase+(q['program']*16+q['tone'])*32:tbase+(q['program']*16+q['tone']+1)*32]
        assert tone.hex()==q['tone_hex']
        wave_id=struct.unpack_from('<H',tone,22)[0]
        wr=bank['waves'][wave_id-1]
        raw=body[wr['body_offset']:wr['body_offset']+wr['bytes']]
        assert raw==(OUT/q['raw']).read_bytes() and sha(raw)==q['wave']['sha256']
        decoded=decode_spu(raw)
        assert decoded.end_flag==1
        assert list(raw[1::16]).count(1)==1 and raw[-16:]==bytes.fromhex('0007'+'77'*14)
        u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
        u.mem_map(0,0x200000);u.mem_write(0x10000,exe[2048:])
        for reg,value in [(UC_MIPS_REG_SP,0x801ff000),(UC_MIPS_REG_RA,0x80001000),(UC_MIPS_REG_A0,tone[6]),(UC_MIPS_REG_A1,tone[5]),(UC_MIPS_REG_A2,tone[4]),(UC_MIPS_REG_A3,tone[5])]:
            u.reg_write(reg,value)
        u.emu_start(0x8005EB18,0x80001000,count=10000)
        pitch=u.reg_read(UC_MIPS_REG_V0)&0xffff
        assert pitch==q['native_pitch_proof']['pitch']
        with wave.open(str(OUT/q['wav']),'rb') as wav:
            assert wav.getnchannels()==1 and wav.getsampwidth()==2 and wav.getframerate()==q['wav_header_rate']
            assert wav.readframes(wav.getnframes())==struct.pack('<'+'h'*len(decoded.pcm),*decoded.pcm)
        verified.append(dict(kind=q['kind'],dat_index=q['dat_index'],source_command_bank=3,source_command_id=q['source_command'],source_command_hex=q['source_command_hex'],sample_sha256=sha(raw),raw_file=q['raw'],wav_file=q['wav'],wave_bytes=len(raw),pitch=pitch,effective_rate=44100*pitch/4096,adsr1=q['adsr1'],adsr2=q['adsr2'],native_pitch_executed=True,program_volume=q['program_volume'],vab_master_volume=q['vab_master_volume'],one_shot_end_flag=decoded.end_flag))
    for kind in ('death','hurt'):
        pair=[q for q in verified if q['kind']==kind]
        assert pair[0]['sample_sha256']==pair[1]['sample_sha256']
    assert file_sha(path)==before
    result=dict(passed=True,source=dict(path='MegaManX6.bin',sha256=before,boot='SLPM_885.09',region_revision='실행 ID 외 공식 지역/리비전은 미확인',exe_sha256=sha(exe)),source_unchanged=True,checked_form1_sectors=len(checked),subheader_edc_ecc_all_pass=True,source_calls=dict(play_sound='0x80017780',hurt_voice='0x8003A060, bank3 ID0/1',hurt_se='0x8003A070, bank3 ID17',death_voice='0x8003E33C, bank3 ID16',death_se='0x8003E34C, bank3 ID14',player_state_table='0x800744B0 state2 -> 0x8003D644',death_phase_table='0x80074714 -> phase1 0x8003E2DC'),samples=verified,limitations=['X6 실제 에뮬레이터 실행/오디오 출력 캡처는 하지 않았다.','도구의 오디오 입력 미지원으로 사람 청취 완료라고 주장하지 않는다. 비보컬 분류는 별도 호출 및 X/Zero 공통 파형 근거다.','WAV는 native pitch에 따른 표본율, SPU 보간/ADSR/리버브 적용 전 단일 파형이다.','다른 XA14섹터의 중복서브헤더 불일치가 별도 inventory에 있으나, 이번 검사 1103 Form1 섹터는 모두 통과.'],files_modified=['work/audio_c01_revision_20261105/x6/*'])
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,sectors=len(checked),samples=len(verified),source=before)))

if __name__=='__main__':main()
