"""실제 stage5 상태에서 Riko 잔기 팔레트 로딩과 원작 CLUT 연결을 확인한다."""
import gzip,json,struct,sys
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_chaser_runtime import SOURCE,SOURCE_SHA,BUILD,BIN_SHA,CAPTURE,sha,digest
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import DiscReader
from src.psx_player import composition_frame

def main():
    assert digest(SOURCE)==SOURCE_SHA and digest(BUILD/'shibuki_riko.bin')==BIN_SHA
    s=gzip.decompress(SOURCE.read_bytes());ram=s[442:442+0x200000];vram=s[2569183:2569183+1048576]
    assert ram[0x1418ca]==1 and ram[0x1721cc:0x1721ce]==bytes([5,0])
    folder=BUILD/'resources';col=(folder/'COL05_0Z.ARC').read_bytes();palette=entry(col,5);at=ram.find(palette)
    with (BUILD/'shibuki_riko.bin').open('rb')as stream:
        disc=DiscReader(stream,(BUILD/'shibuki_riko.bin').stat().st_size)
        record=next(q for q in disc.inspect()['files']if q['path']=='/ARC/COL05_0Z.ARC;1')
        assert disc.read(record['lba'],record['size'])==col
    assert at>=0 and ram.find(palette,at+1)<0
    assert (CAPTURE/'ram_19537440.bin').read_bytes()[at:at+len(palette)]==palette
    candidates=[p.name for p in folder.glob('COL*.ARC')if entry(p.read_bytes(),5)==palette]
    assert candidates==['COL05_0Z.ARC']
    row=palette[11*32:12*32];pl=(folder/'PL01_U.ARC').read_bytes();parts=entry(pl,3)
    assert row==entry(pl,9)[12*32:13*32]
    clut=0x780b;x=(clut&63)*16;y=clut>>6;offset=y*2048+x*2
    assert (x,y)==(176,480)and vram[offset:offset+32]==row
    assert (CAPTURE/'vram_88764448.bin').read_bytes()[offset:offset+32]==row
    cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
    # Actual code/animation bytes resident in this freshly booted game.
    code=ram[0xbf7d0:0xbf7f4]
    assert struct.unpack_from('<I',ram,0xbf7ec)[0]==0x2402780b
    instructions=[f'{i.address:08x}: {i.mnemonic} {i.op_str}'for i in cs.disasm(code,0x800bf7d0)]
    ptr=struct.unpack_from('<I',ram,0x10c61c+4*4)[0];pos=0;seen=set();sequence=[]
    while pos not in seen:
        seen.add(pos);ticks,event,step,frame=struct.unpack_from('<bbbB',ram,ptr-0x80000000+4*pos)
        sequence.append({'step':pos,'ticks':ticks,'event':event,'relative':step,'frame':frame});pos+=step
    assert set(q['frame']for q in sequence)==set(range(89,99))
    rows=[]
    for n in range(89,99):
        comp=composition_frame(parts,3,n)
        assert all(q['clut']==0 for q in comp['parts'])
        rows.append({'frame':n,'part_clut_addends':[q['clut']for q in comp['parts']],
                     'effective_clut':'0x780B','tiles':[q['page']*256+q['tile']for q in comp['parts']]})
    report={'source_state':SOURCE.relative_to(ROOT).as_posix(),'source_state_sha256':SOURCE_SHA,'source_bin_sha256':BIN_SHA,
        'scene':{'character':1,'stage':5,'area':0},'scene_COL':'COL05_0Z.ARC','scene_COL_sha256':sha(col),
        'COL_entry5_sha256':sha(palette),'COL_entry5_bytes':len(palette),'COL_entry5_RAM_address':hex(0x80000000+at),
        'whole_COL_palette_found_unique_in_RAM_and_capture':True,'candidate03_matching_COL_files':candidates,
        'palette_slot':11,'palette_sha256':sha(row),'slot11_equals_Riko_PL01_slot12':True,
        'CLUT':'0x780B','VRAM_word_xy':[x,y],'VRAM_palette_equals_modified_COL':True,
        'pickup_kind4_native_code':instructions,'pickup_animation4_address':hex(ptr),'pickup_animation4':sequence,
        'disc_COL_equals_inspected_resource':True,
        'PL01_life_compositions':rows,'scope':'실제 새 부팅 stage5의 COL 전체/RAM/잔기 CLUT/VRAM 팔레트 로딩 및 PL01 조립 연결 확인',
        'life_item_visible_on_screen_verified':False,'limitations':['화면에 실제 잔기 드롭이 없으므로 얼굴·거품의 실제 아이템 표시/취득을 확인한 것은 아님.',
          '다른 stage/character의 팔레트 로딩까지 이 표본으로 전수 확인하지 않음.'],
        'source_files_modified':False,'process_memory_written':False,'keys_sent':False}
    dest=ROOT/'work/overhaul_20261105/ui/fixes_v1/riko_life_stage5_runtime.json'
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(dest),'scene_COL':report['scene_COL'],'CLUT':report['CLUT'],'palette_RAM_VRAM_equal':True,'item_display_verified':False}))
if __name__=='__main__':main()
