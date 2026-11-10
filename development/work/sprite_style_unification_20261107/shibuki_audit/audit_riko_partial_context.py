"""최신 제작 기준 EXE와 PL01에서 부분 VRAM 참조의 실제 호출 맥락을 읽는다."""
from pathlib import Path
import hashlib,json,re,struct,sys
import capstone
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_sprite_playback import parse_sequence
from scripts.build_rin_idle import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame

OUT=H/'riko_partial_context01'
BIN=ROOT/'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin'
ARC=ROOT/'work/sprite_style_unification_20261107/riko/prepared_wall_clothes_v1/PL01_U.ARC'
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def main():
    need(not OUT.exists(),'Fresh audit output required')
    need(sha(BIN.read_bytes())=='21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a','Unsupported BIN')
    data,_=read_disc(BIN,['SLUS_005.61']);exe=data['SLUS_005.61']
    need(sha(exe)=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616','Unexpected EXE')
    arc=ARC.read_bytes();need(sha(arc)=='8f81bd702370d9ae4d47a50cd6c628a9513067caeacf8de5ccff809097f06c48','Unfrozen PL01')
    original_dir=ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z'
    originalexe=(original_dir/'original.exe').read_bytes();original=(original_dir/'original.arc').read_bytes()
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf8'))
    need(sha(originalexe)==profile['executable']['sha256'] and sha(original)==profile['zero_archive']['sha256'],'Original hash mismatch')
    layout=ROOT/'work/research/decomp/config/SLUS_005.61.splat.yaml'
    txt=layout.read_text('utf8');start=min(int(s,16)for s in re.findall(r'\[(0x[0-9A-Fa-f]+), c,',txt));end=min(int(s,16)for s in re.findall(r'\[(0x[0-9A-Fa-f]+), \.data,',txt))
    need((start,end)==(0x323c,0xdec0c),'Code layout changed')
    cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
    def off(a):return a-0x80010000+2048
    def word(a):return struct.unpack_from('<I',exe,off(a))[0]
    def dis(a,b):return [f'{x.address:08x}: {x.mnemonic} {x.op_str}'for x in cs.disasm(exe[off(a):off(b)],a)]
    def calls(t):return [p-2048+0x80010000 for p in range(start,end,4)if struct.unpack_from('<I',exe,p)[0]==0x0c000000|((t>>2)&0x3ffffff)]
    def arg(a):
        w=word(a);need(w>>16==0x2405,'Unexpected immediate argument');return w&65535
    expected={0x8003b5f8:([0x8003b5fc],None),0x8003bbd4:([0x8003bbd8],None),0x8003bd1c:([0x8003bd20],None),0x8003c024:([0x8003bff8,0x8003c010,0x8003c020],None),0x8003c174:([],0x800f910c),0x8003c278:([],0x800f9110),0x8003c3bc:([0x8003c390,0x8003c3a8,0x8003c3b8],None),0x8003c45c:([],0x800f9114),0x8003c958:([0x8003c95c],None),0x8003caec:([0x8003cac0,0x8003cad8,0x8003cae8],None)}
    need(set(calls(0x8003b458))==set(expected),'Unhandled chaser setter caller')
    chaser=[];values=set()
    for a,(constants,table)in expected.items():
        nums=[arg(p)for p in constants]
        if table:
            need([word(a-12),word(a-8),word(a-4)]==[0x3c018010,0x00220821,0x90250000|(table&65535)],'Dynamic table load changed')
            nums=list(exe[off(table):off(table)+4]);need(exe[off(table):off(table)+4]==originalexe[off(table):off(table)+4],'Original table changed')
        need(exe[off(a)-88:off(a)+8]==originalexe[off(a)-88:off(a)+8],'Vehicle native path changed')
        values.update(nums);chaser.append({'call':hex(a),'ids':nums,'constant_addresses':list(map(hex,constants)),'table':hex(table)if table else None,'code_identical_to_original':True,'disassembly':dis(a-88,a+8)})
    need(values=={0,*range(65,77)},'Unexpected chaser ID domain')
    mech=[]
    for a in calls(0x8003dc1c):
        n=arg(a+4);need(41<=n<=64,'Unexpected mech ID');mech.append({'call':hex(a),'id':n})
    stores=[]
    for p in range(start,end,4):
        w=struct.unpack_from('<I',exe,p)[0]
        if w>>26==0x28 and w&65535 in(0xd4,0x199c):stores.append(p-2048+0x80010000)
    need(stores==[0x80035a50,0x8003b45c,0x8003dc30],'Additional candidate writer')
    table=0x8011aff0;selector=0x8011af60;allseq=[];matching=[]
    for n in range(144):
        s=parse_sequence(exe,table,n);s['graphics_bank']=exe[off(selector)+n]
        need(exe[off(selector)+n]==originalexe[off(selector)+n],'Selector changed')
        for step in s['steps']:
            a=int(step['address'],16);need(exe[off(a):off(a)+4]==originalexe[off(a):off(a)+4],'Animation bytes changed')
        allseq.append(s)
        if s['graphics_bank']==1 and any(42<=q['frame_ref']<=49 for q in s['steps']):matching.append(s)
    need([s['id']for s in matching]==[77,78,79,80],'Additional partial-reference animation')
    for n,s in enumerate(matching):
        need([q['frame_ref']for q in s['steps']]==[42+n*2,43+n*2] and s['loop_calls']==4 and s['loop_to_position']==0,'Partial loop changed')
    g=entry(arc,2)[1];c=entry(arc,3)[1];og=entry(original,2)[1];oc=entry(original,3)[1];partial=[]
    for n in range(42,50):
        f=graphics_bank(g,1)['frames'][n];of=graphics_bank(og,1)['frames'][n]
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        oldraw=decode_stream(og,of['offset'],of['limit'],of['tile_count']*128).data
        parts=composition_frame(c,5,n)['parts'];oldparts=composition_frame(oc,5,n)['parts']
        current_records=b''.join(c[p['record_offset']:p['record_offset']+4]for p in parts)
        original_records=b''.join(oc[p['record_offset']:p['record_offset']+4]for p in oldparts)
        need(f['tile_count']==of['tile_count']==1 and raw==oldraw and current_records==original_records,'Original partial stream changed')
        partial.append({'ref':n,'gfx_bank':1,'parts_bank':5,'uploaded_tiles':1,'decoded_bytes':len(raw),'decoded_sha256':sha(raw),'parts_count':len(parts),'referenced_tiles':sorted({p['tile']for p in parts}),'original_raw_and_parts_exact':True,'complete_frame_reconstructed':False})
    native_ranges={'player_ride':[0x80032e94,0x80032f60],'chaser_setter':[0x8003b458,0x8003b474],'mech_setter':[0x8003dc1c,0x8003dc40],'decode_upload':[0x80015ecc,0x80016000]}
    for label,(a,b)in native_ranges.items():need(exe[off(a):off(b)]==originalexe[off(a):off(b)],f'{label} differs from original')
    OUT.mkdir()
    report={'passed':True,'scope':'최신 미국판 코드·자원 읽기 전용 정적 호출 맥락 검사. 실제 게임에서 강제 진입하지 않음.','source_bin':str(BIN.relative_to(ROOT)),'source_bin_sha256':sha(BIN.read_bytes()),'source_exe_sha256':sha(exe),'source_arc':str(ARC.relative_to(ROOT)),'source_arc_sha256':sha(arc),'original_exe_sha256':sha(originalexe),'original_arc_sha256':sha(original),'code_range_file':[start,end],'layout_sha256':sha(layout.read_bytes()),'chaser_calls':chaser,'chaser_ids_including_padding':sorted(values),'mech_calls':mech,'candidate_writes':[{'address':hex(a),'disassembly':dis(a-16,a+8)}for a in stores],'all144_zero_animation_tables_checked':True,'partial_animations':matching,'normal_chaser_animations':allseq[65:77],'partial_resources':partial,'native_code':{k:{'range':list(map(hex,v)),'original_exact':True,'instructions':dis(*v)}for k,v in native_ranges.items()},'findings':['bank1 42..49는 77..80번의 별도 2스텝 루프에만 연결되어 있다. 65..76번의 뒤를 자동으로 이어 재생하는 참조가 아니다.','조사한 체이서 setter 10개 직접 호출과 3개 동적 표는 65..76만 선택한다. 표의 네 번째 0은 함께 기록했으며 일반 상태의 0..2 인덱스와 구분한다.','라이드 아머 setter 직접 호출은 41..64이며, ride_animation 후보 byte 쓰기는 초기값·체이서·라이드 아머의 3곳이다.','42..49는 원본부터 128바이트 1타일 업로드인데 조립은 최대23번 타일을 읽는다. 이전 VRAM 이력이 없으면 완성 그림을 유일하게 복원할 수 없다.','이번 최신 리코 제작본도 8개 부분 스트림과 조립을 원본 그대로 보존한다. 미복원 항목을 누락된 리코 8포즈로 간주해 새 몸을 만들지 않는다.'],'limitations':['간접/계산 주소, 미해석 스크립트까지 포함한 프로그램 전체 도달 불가 증명은 아니다.','현재 표준 탑승 경로에서 선택되지 않는 원본 부분 참조로 분류하며 미사용 확정으로 확대하지 않는다.','미확인 이전 VRAM을 추측하여 채우거나 실기 성공으로 보고하지 않는다.'],'game_data_changed':False,'runtime_verified':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    (OUT/'REPORT.md').write_text('# 리코 bank1 42–49의 실제 참조 맥락\n\n현재 제작 EXE와 PL01에서 원본 미국판 바이트를 다시 대조했다. 144개 제로 애니메이션 중 이 8개 부분 참조를 사용하는 표는 **77–80**뿐이며, 각 2프레임을 2호출씩 유지하는 독립 루프다. 체이서의 정상 setter 10곳과 동적 표 3개는 **65–76**을 선택한다. 일반 체이서 몸 14–41의 뒤에서 부분 참조가 자동으로 이어지는 구조가 아니다.\n\n원본과 현재 모두 각 스트림은 1타일(128바이트)만 업로드하지만 조립은 최대23번 타일을 읽는다. 따라서 이 8개를 이전 VRAM 이력 없이 완성 이미지로 만드는 것은 근거가 없다. 원래 raw와 조립을 보존한다.\n\n검사는 코드 범위 내 직접 JAL과 ride_animation 후보 byte 쓰기, 모든 표와 원본 보존을 대상으로 했다. 간접 호출·미해석 스크립트까지 포함한 전체 도달 불가 증명이나 실제 탑승 플레이 검증은 아니다. 상세 주소·바이트 해시·명령은 `report.json`에 있다.\n','utf8')
    print(json.dumps({'passed':True,'output':str(OUT),'chaser_calls':len(chaser),'mech_calls':len(mech),'partial_animation_ids':[s['id']for s in matching]}))
if __name__=='__main__':main()
