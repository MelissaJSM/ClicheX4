"""미국판 EXE의 탑승 애니메이션 지정 경로를 읽기 전용으로 대조한다.

정상 탑승 경로의 범위 감사이며 전체 프로그램의 미사용 증명은 아니다.
"""
import json,re,struct,sys
from datetime import datetime,timezone
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.build_rin_idle import entry,sha
from src.psx_player import graphics_bank,decode_stream,composition_frame

def main():
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'));ptr=json.loads((ROOT/'projects/ver_rin_nana/current_build.json').read_text('utf-8'));build=ROOT/ptr['build'];m=json.loads((build/'manifest.json').read_text('utf-8'))
    extract=ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z';exe_path=extract/'original.exe';arc_path=extract/'original.arc';exe=exe_path.read_bytes();original=arc_path.read_bytes();current=(build/'modified.arc').read_bytes()
    if sha(exe)!=profile['executable']['sha256'] or sha(original)!=profile['zero_archive']['sha256'] or sha(current)!=m['modified_archive_sha256'] or digest(build/'rin_nana.bin')!=ptr['sha256']:raise ValueError('Unsupported input hash')
    layout=ROOT/'work/research/decomp/config/SLUS_005.61.splat.yaml';text=layout.read_text('utf-8');start=min(int(s,16) for s in re.findall(r'\[(0x[0-9A-Fa-f]+), c,',text));end=min(int(s,16) for s in re.findall(r'\[(0x[0-9A-Fa-f]+), \.data,',text))
    if (start,end)!=(0x323c,0xdec0c):raise ValueError('Code layout differs')
    base=profile['executable']['load_address'];cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
    def off(a):return a-base+2048
    def word(a):return struct.unpack_from('<I',exe,off(a))[0]
    def dis(a,b):return [f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in cs.disasm(exe[off(a):off(b)],a)]
    def addiu_a1(a):
        v=word(a)
        if v>>16!=0x2405:raise ValueError('Expected immediate animation argument')
        return v&65535
    def calls(target):
        return [o-2048+base for o in range(start,end,4) if struct.unpack_from('<I',exe,o)[0]==(3<<26)|((target>>2)&0x3ffffff)]
    expected={0x8003b5f8:([0x8003b5fc],None),0x8003bbd4:([0x8003bbd8],None),0x8003bd1c:([0x8003bd20],None),0x8003c024:([0x8003bff8,0x8003c010,0x8003c020],None),0x8003c174:([],0x800f910c),0x8003c278:([],0x800f9110),0x8003c3bc:([0x8003c390,0x8003c3a8,0x8003c3b8],None),0x8003c45c:([],0x800f9114),0x8003c958:([0x8003c95c],None),0x8003caec:([0x8003cac0,0x8003cad8,0x8003cae8],None)}
    actual=calls(0x8003b458)
    if set(actual)!=set(expected):raise ValueError('Unhandled chaser call site')
    rows=[];values=set()
    for address,(constants,table) in expected.items():
        numbers=[addiu_a1(a) for a in constants]
        if table:
            # lui at,0x8010; addu at,at,v0; lbu a1,signed table offset(at).
            if word(address-12)!=0x3c018010 or word(address-8)!=0x00220821 or word(address-4)!=0x90250000|(table&65535):raise ValueError('Table load changed')
            numbers=list(exe[off(table):off(table)+4])
        values.update(numbers);rows.append({'call_address':hex(address),'animation_ids':numbers,'constant_instruction_addresses':list(map(hex,constants)),'table_address':hex(table) if table else None,'disassembly':dis(address-88,address+8)})
    mech=[]
    for address in calls(0x8003dc1c):
        value=addiu_a1(address+4)
        if not 41<=value<=64:raise ValueError('Unexpected mech animation')
        mech.append({'call_address':hex(address),'animation_id':value})
    stores=[]
    for o in range(start,end,4):
        w=struct.unpack_from('<I',exe,o)[0]
        if w>>26==0x28 and w&65535 in (0xd4,0x199c):stores.append(o-2048+base)
    if stores!=[0x80035a50,0x8003b45c,0x8003dc30]:raise ValueError('New candidate ride byte writer')
    g=entry(original,2)[1];p=entry(original,3)[1];ng=entry(current,2)[1];np=entry(current,3)[1];partial=[]
    for n in range(42,50):
        f=graphics_bank(g,1)['frames'][n];q=graphics_bank(ng,1)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;new=decode_stream(ng,q['offset'],q['limit'],q['tile_count']*128).data;c=composition_frame(p,5,n)
        if f['tile_count']!=1 or raw!=new or c!=composition_frame(np,5,n):raise ValueError('Partial original reference changed')
        partial.append({'frame':n,'bytes':len(raw),'sha256':sha(raw),'parts':len(c['parts']),'max_tile_index':max(v['tile'] for v in c['parts']),'original_preserved':True})
    if values!={0,*range(65,77)}:raise ValueError('Chaser animation range changed')
    out=ROOT/'work/ver_rin_nana'/('vehicle_audit_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    report={'input_exe_sha256':sha(exe),'input_arc_sha256':sha(original),'current_bin_sha256':ptr['sha256'],'build':ptr['build'],'capstone_version':capstone.__version__,'layout_sha256':digest(layout),'scanned_file_code_range':[start,end],'chaser_setter':hex(0x8003b458),'chaser_calls':rows,'chaser_animation_ids':sorted(values),'mech_calls':mech,'candidate_ride_field_writes':[{'address':hex(a),'disassembly':dis(a-16,a+8)} for a in stores],'partial_references':partial,'decompression_disassembly':dis(0x80015ecc,0x80016000),'player_ride_disassembly':dis(0x80032e94,0x80032f60),'conclusion':'No calls to animations77..80 in the inspected US-EXE normal vehicle setter paths; preserve the8 partial references as unresolved/reserved, not8 missing body poses.','limitations':['Not a whole-program proof of unreachable code.','No new runtime input or injection performed.','Indirect/computed addresses, scripts or unmodeled paths are not ruled out.'],'game_data_changed':False}
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps({'output':str(out),'chaser_calls':len(rows),'mech_calls':len(mech),'chaser_animation_ids':sorted(values),'partial_refs':len(partial)}))

if __name__=='__main__':main()
