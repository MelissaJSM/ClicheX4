"""Read-only review of frozen C01 sources, prepared assets, and built images."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import struct
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.inventory_riko_voice import parse_bank
from scripts.c01_audio_build import check_arc
from scripts.overhaul_audio_verify_cpu import banks, run
from src.psx_sector import validate_checks
from src.psx_spu_audio import decode_spu
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN
from unicorn import mips_const as m

sha = lambda b: hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def require(x, msg):
    if not x:
        raise ValueError(msg)
def disc(p, names):
    with p.open('rb') as f:
        d = DiscReader(f, p.stat().st_size)
        rs = {r['name'].split(';')[0]: r for r in d.inspect()['files'] if not r['directory']}
        return {n: d.read(rs[n]['lba'], rs[n]['size']) for n in names}, {n: rs[n] for n in names}
def pitch(exe, addr, tone):
    u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0, 0x200000)
    load = struct.unpack_from('<I', exe, 24)[0] & 0x1fffffff
    u.mem_write(load, exe[2048:])
    if addr == 0x800e2598:
        # X4 note2pitch2 reads the selected VAB tone through SDK globals;
        # unlike X6's pure helper, a2/a3 are not its center/fine inputs.
        u.mem_write(0x142f88, struct.pack('<I', 0x801a0000))
        u.mem_write(0x166bef, b'\0')
        u.mem_write(0x166bf4, b'\0')
        u.mem_write(0x1a0000, tone)
    for reg, val in ((m.UC_MIPS_REG_SP, 0x801ff000), (m.UC_MIPS_REG_RA, 0x80001000),
                     (m.UC_MIPS_REG_A0, tone[6]), (m.UC_MIPS_REG_A1, tone[5]),
                     (m.UC_MIPS_REG_A2, tone[4]), (m.UC_MIPS_REG_A3, tone[5])):
        u.reg_write(reg, val)
    u.emu_start(addr, 0x80001000, count=10000)
    require(u.reg_read(m.UC_MIPS_REG_PC) == 0x80001000, 'Pitch routine did not return')
    return u.reg_read(m.UC_MIPS_REG_V0) & 0xffff
def refused(fn):
    try:
        fn()
    except (ValueError, struct.error, IndexError):
        return True
    raise AssertionError('Invalid input accepted')

def main():
    sources = {
        'MegaMan X4.bin': '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',
        'Rockman X4.bin': 'a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1',
        'Rockman X5 (Japan).bin': '15b17f44fc461ae04c64c83b9b5b0c294e2eb16bed6c6ede9461c27743aa6323',
        'MegaManX6.bin': 'e0b5e6b6349bb0f0f487234f52cda43f26754a3d67764b7c306ba75c01e76e1f',
        'out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin': '8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a'}
    for p, h in sources.items():
        require(digest(ROOT/p) == h, 'Protected source hash: '+p)
    spec = importlib.util.spec_from_file_location('c01_preparation_review', WORK/'prepare_x6_c01.py')
    prep = importlib.util.module_from_spec(spec); spec.loader.exec_module(prep)
    source_rows = json.loads((WORK/'x6/sound_candidates.json').read_text('utf8'))
    x6, rs = disc(ROOT/'MegaManX6.bin', ['SLPM_885.09', 'SYSTEM.CNF'])
    xe = x6['SLPM_885.09']
    require(b'SLPM_885.09;1' in x6['SYSTEM.CNF'], 'X6 boot identifier')
    def words(va, n):
        return struct.unpack_from('<'+'I'*n, xe, va-0x80010000+2048)
    require(words(0x8003a054, 9) == (0x24040003,0x30420001,0x38450001,0x0c005de0,0x02203021,0x24040003,0x24050011,0x0c005de0,0x02203021), 'Separate hurt voice/SE instructions')
    require(words(0x8003e33c, 6) == (0x0c005de0,0xa2000003,0x24040003,0x2405000e,0x0c005de0,0x02003021), 'Separate death voice/SE instructions')
    samples = {}; source_proof = []; checked = set()
    with (ROOT/'MegaManX6.bin').open('rb') as f:
        d = DiscReader(f, (ROOT/'MegaManX6.bin').stat().st_size)
        table = d.read(17047, 4096)
        for idx in (85,86):
            rel, size = struct.unpack_from('<II', table, idx*8)
            arc = d.read(17047+rel, size); es = psx_arc(arc)
            require(arc == (WORK/f'x6/dat_{idx:02x}.arc').read_bytes(), 'Extracted X6 ARC mismatch')
            for lba in range(17047+rel, 17047+rel+(size+2047)//2048):
                f.seek(lba*2352); validate_checks(f.read(2352)); checked.add(lba)
            for row in [x for x in source_rows if x['dat_index']==idx]:
                he, be = es[row['header_entry']], es[row['body_entry']]
                h = arc[he['offset']:he['offset']+he['size']]; b = arc[be['offset']:be['offset']+be['size']]
                q = parse_bank(h,b,False); tb = q['vab_offset']+32+128*16
                t = h[tb+(row['program']*16+row['tone'])*32:tb+(row['program']*16+row['tone']+1)*32]
                w = q['waves'][struct.unpack_from('<H',t,22)[0]-1]
                raw = b[w['body_offset']:w['body_offset']+w['bytes']]
                require(t.hex()==row['tone_hex'] and raw==(WORK/'x6'/row['raw']).read_bytes(), 'Source tone or raw mismatch')
                expected = prep.HURT_SHA if row['kind']=='hurt' else prep.DEATH_SHA
                require(sha(raw)==expected and decode_spu(raw).end_flag==1, 'Sample hash or ending flag')
                require(pitch(xe,0x8005eb18,t)==row['native_pitch_proof']['pitch'], 'X6 native pitch')
                cmdh = arc[es[13]['offset']:es[13]['offset']+es[13]['size']]
                cmd = cmdh[8+row['source_command']*4:12+row['source_command']*4]
                require(cmd.hex()==row['source_command_hex'], 'X6 source command mismatch')
                require((cmd[0]&63,cmd[1]&127,cmd[2]>>4)==(row['bank'],row['program'],row['tone']), 'Source dispatcher mapping')
                source_proof.append({'kind':row['kind'],'member':idx,'raw_sha256':sha(raw),'bytes':len(raw),'pitch':row['native_pitch_proof']['pitch'],'source_command':row['source_command']})
                if idx==86: samples[row['kind']]={'raw':raw,'tone':t,'source':row}
    names = prep.NAMES
    bosses = tuple(f'{p}{n}{s}.ARC' for n in (5,6,7) for p,s in (('ST','_1_1'),('ONPARE','')))
    targets={'ver_buki_riko':'6d9f0310be3df40b5000643a1b19d860cc6ebe4f8c476fb4150210ce189ecf88',
             'ver_rin_nana':'0c019de65ea2b39e46cdd215d13f2d1de3a4cbda5aaac1567eecc16a83be4108'}
    state_rams={}
    for key,(p,h) in prep.STATES.items():
        raw=(ROOT/p).read_bytes();require(sha(raw)==h,'Saved evidence changed');state_rams[key]=gzip.decompress(raw)[442:442+0x200000]
    projects={}
    for project,(stem,baseline_sha) in prep.BASES.items():
        before_path=ROOT/'out'/project/'selection_unified_20261105_v4'/(stem+'.bin')
        target_path=ROOT/'out'/project/'c01_x6_sfx_20261105_v1'/(stem+'.bin')
        require(digest(before_path)==baseline_sha and digest(target_path)==targets[project], 'Build hashes')
        old, records=disc(before_path, names+bosses+('SLUS_005.61',))
        new, nrecords=disc(target_path, names+bosses+('SLUS_005.61',))
        require(records==nrecords, 'ISO file placement changed')
        require(all(old[n]==new[n] for n in bosses+('SLUS_005.61',)), 'Boss resources or executable changed')
        proposal=json.loads((WORK/'prepared'/project/'proposal.json').read_text('utf8'))
        resources={};rejections=0
        for name in names:
            target=new[name]; original=old[name]; loaded=banks(target); previous=banks(original)
            require(target==(WORK/'prepared'/project/name).read_bytes(), 'Prepared/final ARC mismatch')
            require(sha(target)==proposal['files'][name]['after'], 'Proposal digest mismatch')
            require(prep.pack(original,sha(original),samples)[0]==target, 'Frozen code reproducibility')
            check=check_arc(original,target)
            h,b,q=loaded[3];oh,ob,oq=previous[3];tb=q['vab_offset']+32+128*16
            require(h[tb+64:tb+512]==oh[tb+64:tb+512], 'Unrelated tones modified')
            require(h[q['vab_offset']:tb]==oh[oq['vab_offset']:tb], 'Program/master volume or VAB header changed')
            for i,kind in enumerate(('hurt','death')):
                w=q['waves'][i];raw=b[w['body_offset']:w['body_offset']+w['bytes']]
                t=h[tb+i*32:tb+(i+1)*32];ref=bytearray(samples[kind]['tone']);struct.pack_into('<HH',ref,20,0,i+1)
                require(t==bytes(ref) and raw==samples[kind]['raw'], 'X6 timbre/envelope/pitch/raw changed')
                require(pitch(old['SLUS_005.61'],0x800e2598,t)==(1024 if kind=='hurt' else 1290), 'Independent X4 native rate check')
            sdk=prep.native_sdk(state_rams['zero' if name=='PL01_U.ARC' else 'x'],original,target)
            # Replay all existing protagonist and restored boss commands against final assets.
            cpu_count=0
            for c in range(13):
                calls=run(old['SLUS_005.61'],loaded,3,c);require(calls,'No dispatcher call');cpu_count+=1
                if c in (0,1,12):
                    kind='death' if c==12 else 'hurt'
                    require(all(x['bank']==3 and x['channel']==20 and x['wave_sha256']==sha(samples[kind]['raw']) for x in calls),'Incorrect C01 mapping')
                elif c==10 and name=='PL01_U.ARC':
                    require(calls==run(old['SLUS_005.61'],previous,3,c),'Rakuhouha changed')
                else:require(all(not x['pcm_nonzero'] for x in calls),'Player voice became audible')
            for stage,commands in ((5,(178,)),(6,(196,199)),(7,(190,))):
                for boss in (f'ST{stage}_1_1.ARC',f'ONPARE{stage}.ARC'):
                    for c in commands:
                        prior=run(old['SLUS_005.61'],{**previous,**banks(old[boss])},2,c)
                        after=run(new['SLUS_005.61'],{**loaded,**banks(new[boss])},2,c)
                        require(after==prior and all(x['pcm_nonzero'] for x in after),'C06 boss regression');cpu_count+=1
            badsample={**samples,'hurt':{**samples['hurt'],'raw':bytes([samples['hurt']['raw'][0]^1])+samples['hurt']['raw'][1:]}}
            for fun in (lambda:prep.pack(original,'0'*64,samples),lambda:prep.pack(target,sha(target),samples),lambda:prep.pack(original,sha(original),badsample)):
                rejections+=refused(fun)
            es=psx_arc(target);non=next(e for e in es if e['type']=='0x2');bad=bytearray(target);bad[non['offset']]^=1
            rejections+=refused(lambda:check_arc(original,bytes(bad)))
            resources[name]={'after_sha256':sha(target),'check':check,'original_X6_raw_and_tone_except_program_wave_identical':True,'native_X4_note2pitch_pass':True,'native_SDK_cases':sdk,'dispatcher_cases_including_all_C06':cpu_count}
        # Compare every physical sector, restricting all changes to declared player ARC payloads.
        allowed=set()
        for name in names:
            r=records[name];allowed.update(range(r['lba'],r['lba']+(r['size']+2047)//2048))
        changed=[];count=0
        with before_path.open('rb') as a,target_path.open('rb') as b:
            while x:=a.read(2352):
                y=b.read(2352);require(len(y)==2352,'Disc length')
                if x!=y:
                    require(count in allowed and x[:24]==y[:24],'Changed outside player data/checks')
                    validate_checks(y);changed.append(count)
                count+=1
            require(not b.read(1),'Extra disc bytes')
        manifest=json.loads((target_path.parent/'manifest.json').read_text('utf8'))
        require(set(changed)=={r['lba'] for r in manifest['modified_bin']['changed_sectors']},'Builder change declaration')
        require(digest(before_path)==baseline_sha and digest(target_path)==targets[project],'Images changed during review')
        projects[project]={'bin_sha256':targets[project],'baseline_sha256':baseline_sha,'all_disc_sectors_compared':count,'changed_sectors':len(changed),'unrelated_sectors_including_C07_XA_identical':True,'C06_resources_and_all_restored_commands_preserved':True,'graphics_UI_executable_preserved':True,'EDC_ECC_changed_sectors_passed':True,'prepared_reproduction_resources':3,'negative_rejections':rejections,'resources':resources}
        print(project,'passed',count,'sectors',len(changed),'changed',flush=True)
    x5=json.loads((WORK/'x5/extracted_player_banks_v1/manifest.json').read_text('utf8'))
    x5matches={k:[{'member':b['member_index'],'bank':b['body_slot'],'wave':w['wave_id']} for b in x5['banks'] for w in b['waves'] if w['sha256']==sha(v['raw'])] for k,v in samples.items()}
    for p,h in sources.items():require(digest(ROOT/p)==h,'Protected source changed during review')
    for p,h in prep.STATES.values():require(digest(ROOT/p)==h,'Saved evidence changed during review')
    result={'passed':True,'created_utc':datetime.now(timezone.utc).isoformat(),'projects':projects,'X6_raw_source_reextracted_and_verified':source_proof,'X6_source_Form1_EDC_ECC_sectors':len(checked),'X6_voice_and_SE_calls_separate':True,'X5_118_exported_wave_matches':x5matches,'protected_input_sha256':sources,'saved_evidence_states_preserved':True,'no_emulator_or_card_or_active_F1_operations':True,'runtime_verified':False,'human_listening_verified':False,'limitations':['CPU/SPU SDK calls are isolated tests, not live mixer output or listening acceptance.','X5 matching covers the 118 exported player-bank waveforms, not every bank in the disc.']}
    dest=WORK/'independent.json';require(not dest.exists(),'Do not replace existing independent evidence')
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(dest)

if __name__=='__main__':main()
