"""보호 파일과 확정 Shibuki C03 자원의 독립 MIPS 버퍼 감사를 수행한다."""
import gzip,hashlib,json,struct,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.overhaul_nana_buffer_watch import cpu_checks,BUF,CAPACITY
from src.psx_player import graphics_bank,decode_stream
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn import mips_const as m
OUT=ROOT/'work/overhaul_20261105/audio/final_preservation'
ARC=ROOT/'work/overhaul_20261105/sprites/c03_final_v1/ver_buki_riko/PL02_U.ARC'
ARC_SHA='cb7f7d3d350f1d51705b6df9f3007693253a55b564ffef763e2e698944b71551'
US_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
CURRENT_SHA='736cdc2dc277767d2e4c8b935137bc9ad5ab07ff8074323e0b2f710070657719'
CURRENT_PIC_SHA='a1091bcc132de6cef066302b183fec3bfd79056f93480b0feb32697a3b53cd98'

def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def require(x,msg):
    if not x:raise ValueError(msg)

def preservation():
    baseline=ROOT/'work/overhaul_20261105/baseline';manifest=baseline/'preservation.json';rows=json.loads(manifest.read_text('utf8'));require(len(rows)==23,'Unexpected baseline inventory')
    results=[];exceptions=[]
    for row in rows:
        p=ROOT/row['path'];require(p.is_file(),'Missing protected file '+row['path']);actual=digest(p);size=p.stat().st_size
        q=dict(**row,actual_sha256=actual,actual_size=size,baseline_identical=actual==row['sha256'] and size==row['size'])
        if not q['baseline_identical']:
            name=p.name
            require(row['path'].startswith('work/ver_rin_nana/emulator/sstates/') and name in ('SLUS_005.61.000','SLUS_005.61.000.pic'),'Unexpected fixed file difference '+row['path'])
            expected=CURRENT_SHA if name.endswith('.000') else CURRENT_PIC_SHA
            backup=baseline/'current_progress'/name;original=baseline/'user_backup/ver_rin_nana/sstates'/name
            require(actual==expected and digest(backup)==expected and backup.read_bytes()==p.read_bytes(),'Unexpected latest user progress')
            require(digest(original)==row['sha256'] and original.stat().st_size==row['size'],'Initial F1 backup not preserved')
            q.update(authorized_latest_user_progress=True,current_progress_backup=backup.relative_to(ROOT).as_posix(),initial_snapshot_backup=original.relative_to(ROOT).as_posix(),initial_snapshot_backup_sha256=digest(original),explanation='사용자 최신 진행 F1과 대응 썸네일이다. 최초8cc51ce9 상태로 되돌리지 않으며 최초 상태도 별도 백업에서 원래 해시로 보존한다.')
            exceptions.append(row['path'])
        results.append(q)
    require(len(exceptions)==2,'Expected latest progress and thumbnail exceptions')
    refs=[]
    for project in ('ver_buki_riko','ver_rin_nana'):
        p=ROOT/f'projects/{project}/project.json';base=next(r for r in rows if r['path']==p.relative_to(ROOT).as_posix());require(digest(p)==base['sha256'],'Reference metadata differs')
        for ref in json.loads(p.read_text('utf8'))['references']:
            path=ROOT/ref['path'];actual=digest(path);require(actual==ref['sha256'],'Original character reference changed')
            refs.append(dict(project=project,task_id=ref['task_id'],path=ref['path'],expected_sha256=ref['sha256'],actual_sha256=actual,size=path.stat().st_size,metadata=p.relative_to(ROOT).as_posix()))
    return dict(baseline_manifest_sha256=digest(manifest),listed_files=len(rows),baseline_identical_files=len(rows)-len(exceptions),explained_latest_user_progress_exceptions=exceptions,unexpected_changes=[],files=results,additional_character_references=refs,reference_count=len(refs),all_fixed_files_preserved=True,active_files_written=False)

def ladder_decoder(exe,g,frame,observed):
    expected=decode_stream(g,frame['offset'],frame['limit'],frame['tile_count']*128).data
    require(frame['tile_count']<=32,'Frame exceeds native buffer');u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000)
    addr=struct.unpack_from('<I',exe,0x18)[0]&0x1fffffff;size=struct.unpack_from('<I',exe,0x1c)[0];u.mem_write(addr,exe[2048:2048+size]);u.mem_write(0x1789a0,g)
    sentinel=bytes((i*73+11)&255 for i in range(CAPACITY+128));u.mem_write(BUF-64,sentinel)
    u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);u.reg_write(m.UC_MIPS_REG_RA,0x80008000);u.reg_write(m.UC_MIPS_REG_A0,0x801789a0+frame['offset']);u.reg_write(m.UC_MIPS_REG_A1,0x80000000+BUF);writes=[]
    def code(cpu,pc,sz,user):
        if pc==0x80008000:cpu.emu_stop()
    def write(cpu,access,at,sz,value,user):writes.append((at&0x1fffffff,sz))
    u.hook_add(UC_HOOK_CODE,code)
    if observed:u.hook_add(UC_HOOK_MEM_WRITE,write,begin=BUF-64,end=BUF+CAPACITY+63)
    u.emu_start(0x80016ff4,0,count=1000000);require(u.reg_read(m.UC_MIPS_REG_PC)==0x80008000,'Native decoder did not return')
    actual=bytes(u.mem_read(BUF-64,CAPACITY+128));require(actual[64:64+len(expected)]==expected,'Native/Python decoding differs')
    require(actual[:64]==sentinel[:64] and actual[64+len(expected):]==sentinel[64+len(expected):],'Native decoder changed guard/unused tail')
    if observed:require(writes and min(a for a,s in writes)==BUF and max(a+s for a,s in writes)==BUF+len(expected),'Unexpected write boundary')
    return dict(frame=frame['index'],tiles=frame['tile_count'],compressed_offset=frame['offset'],compressed_limit=frame['limit'],decoded_bytes=len(expected),decoded_sha256=sha(expected),native_decoder='0x80016FF4',native_write_start=hex(BUF),native_write_end_exclusive=hex(BUF+len(expected)),remaining_buffer_bytes=CAPACITY-len(expected),prefix_guard64_and_unused_tail_and_suffix_guard64_preserved=True)

def main():
    require(not OUT.exists(),'Fresh isolated audit output required');fixed=preservation()
    proposal=ARC.parent/'proposal.json';p=json.loads(proposal.read_text('utf8'));arc=ARC.read_bytes();require(sha(arc)==ARC_SHA==p['files']['PL02_U.ARC']['after'],'Final Shibuki ARC not frozen expected input')
    us=ROOT/'MegaMan X4.bin';require(digest(us)==US_SHA,'US original differs')
    with us.open('rb') as f:
        d=DiscReader(f,us.stat().st_size);r=next(r for r in d.inspect()['files'] if r['path']=='/SLUS_005.61;1');exe=d.read(r['lba'],r['size'])
    es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']] for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True);frames={}
    for fr in bank['frames']:
        require(fr['tile_count']<=32,'Final bank0 frame exceeds 4096 bytes');frames[fr['index']]=(fr,decode_stream(es[2],fr['offset'],fr['limit'],fr['tile_count']*128).data)
    high=cpu_checks(exe,es,bank,frames);plain=cpu_checks(exe,es,bank,frames,observe_writes=False);require(high==plain,'Observer affected native high-tile result')
    ladder=[frames[n][0] for n in (148,149,150)];require(len({fr['offset'] for fr in ladder})==3,'Ladder streams are still aliased');ladder_results=[]
    for fr in ladder:
        a=ladder_decoder(exe,es[2],fr,True);b=ladder_decoder(exe,es[2],fr,False);require(a==b,'Observer affected native ladder result');ladder_results.append(a)
    require(digest(ARC)==ARC_SHA and digest(us)==US_SHA,'Source changed during audit')
    # End-of-audit hashes also ensure pointers/cards were not silently changed
    # while the source-bound decoder was running.
    after=preservation();require(after==fixed,'Protected inputs changed during audit')
    report=dict(created_utc=datetime.now(timezone.utc).isoformat(),preservation=fixed,final_arc=ARC.relative_to(ROOT).as_posix(),final_arc_sha256=ARC_SHA,proposal_sha256=digest(proposal),source_us_sha256=US_SHA,source_exe_sha256=sha(exe),native_wrapper_code_sha256=sha(exe[0x15ecc-0x10000+2048:0x16004-0x10000+2048]),native_decoder_code_sha256=sha(exe[0x16ff4-0x10000+2048:0x170b0-0x10000+2048]),buffer_capacity=CAPACITY,final_graphics_bank0_frame_count=len(frames),max_tiles=max(f['tile_count'] for f,b in frames.values()),reused_cpu_helper='scripts/overhaul_nana_buffer_watch.py:cpu_checks',native_wrapper_high_tile_checks=high,native_ladder_decoder_checks=ladder_results,ladder_three_independent_streams=True,all_cpu_checks_passed=True,observed_and_unobserved_native_results_identical=True,source_files_changed=False,game_code_modified=False,process_memory_accessed=False,active_F1_cards_pointers_written=False,limitations=['격리 MIPS 실행이며 게임 화면·사다리 실제 조작 전수 검증과 구분한다.','148..150은 실제 압축해제 함수를 직접 실행했고, >=29타일과0번은 기존 helper로 실제 플레이어 디코딩/전송 큐 함수까지 실행했다.','초기 보존23개 중 최신 사용자F1/썸네일2개는 명시한 진행 갱신 예외이며, 최초 상태는 보호 백업에 그대로 있다.'])
    OUT.mkdir(parents=True);(OUT/'evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(output=str(OUT),fixed_files=fixed['baseline_identical_files'],latest_progress_exceptions=len(fixed['explained_latest_user_progress_exceptions']),references=fixed['reference_count'],native_high_tile_checks=len(high),native_ladder_checks=len(ladder_results),max_tiles=report['max_tiles'])))
if __name__=='__main__':main()
