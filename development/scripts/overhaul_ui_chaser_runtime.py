"""루트가 채취한 실제 체이서 F1/RAM/VRAM을 읽기 전용으로 대조한다."""
import gzip,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets
from src.epsxe_state import locate_vram

SOURCE=ROOT/'work/overhaul_20261105/runtime/riko_chaser_fresh_state/SLUS_005.61.000'
SOURCE_SHA='d392bf6b3d9421512b867985b3f0b44bd0958dc0d3f2a4eda7e1d33f4f2274d7'
BUILD=ROOT/'out/ver_buki_riko/overhaul_20261105_candidate03'
BIN_SHA='be4468029fe2941a840b9693558cbaccc980b7519e6df2f2af9f66f208506c1e'
CAPTURE=ROOT/'work/ver_buki_riko/korean_runtime/20261104T210943121467Z'
OUT=ROOT/'work/overhaul_20261105/ui/riko_chaser_v1/runtime_fresh_frame14.json'
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):
    with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert digest(SOURCE)==SOURCE_SHA and digest(BUILD/'shibuki_riko.bin')==BIN_SHA
    state=gzip.decompress(SOURCE.read_bytes());assert len(state)==4254418 and state.startswith(b'ePSXe\x06\x00SLUS_005.61')
    ram=state[442:442+0x200000];player=ram[0x1418c8:0x1418c8+228]
    assert (player[2],player[0x17],player[0x47],player[0xc5],player[0xd4])==(1,65,14,255,65)
    assert ram[0x1721cc:0x1721ce]==bytes([5,0])
    arc=(BUILD/'resources/PL01_U.ARC').read_bytes()
    with (BUILD/'shibuki_riko.bin').open('rb')as f:
        reader=DiscReader(f,(BUILD/'shibuki_riko.bin').stat().st_size)
        record=next(r for r in reader.inspect()['files']if r['path']=='/ARC/PL01_U.ARC;1')
        assert reader.read(record['lba'],record['size'])==arc
    captured_ram=(CAPTURE/'ram_19537440.bin').read_bytes();captured_vram=(CAPTURE/'vram_88764448.bin').read_bytes()
    entries={};assets={}
    for kind in (2,3,9):
        data=entry(arc,kind);at=ram.find(data);assert at>=0 and ram.find(data,at+1)<0
        assert captured_ram[at:at+len(data)]==data
        entries[str(kind)]={'address':hex(0x80000000+at),'size':len(data),'sha256':sha(data),'whole_entry_equal_in_state_and_live_capture':True}
        assets[kind]=data
    f=graphics_bank(assets[2],1)['frames'][14]
    raw=decode_stream(assets[2],f['offset'],f['limit'],f['tile_count']*128).data
    assert ram[0x16dea8:0x16dea8+len(raw)]==raw==captured_ram[0x16dea8:0x16dea8+len(raw)]
    vram=locate_vram(state,raw,f['tile_count']);assert vram==2569183
    assert locate_vram(captured_vram,raw,f['tile_count'])==0
    assert state[vram+480*2048:vram+480*2048+32]==assets[9][:32]==captured_vram[480*2048:480*2048+32]
    gp,cp=struct.unpack_from('<II',player,0x38)
    assert gp==0x80000000+ram.find(assets[2])+graphics_bank(assets[2],1)['base']
    assert cp==0x80000000+ram.find(assets[3])+bank_offsets(assets[3])[5]
    head=(ROOT/'work/overhaul_20261105/sprites/patch_v1/ver_buki_riko/PL01_U.ARC').read_bytes()
    for n in range(66,86):
        before=graphics_bank(entry(head,2),1)['frames'][n];after=graphics_bank(assets[2],1)['frames'][n]
        assert decode_stream(entry(head,2),before['offset'],before['limit'],before['tile_count']*128).data==decode_stream(assets[2],after['offset'],after['limit'],after['tile_count']*128).data
        assert composition_frame(entry(head,3),5,n)==composition_frame(assets[3],5,n)
    report={'source_state':SOURCE.relative_to(ROOT).as_posix(),'source_state_sha256':SOURCE_SHA,
      'source_bin':(BUILD/'shibuki_riko.bin').relative_to(ROOT).as_posix(),'source_bin_sha256':BIN_SHA,
      'disc_arc_sha256':sha(arc),'capture':CAPTURE.relative_to(ROOT).as_posix(),'character':1,'stage':5,'area':0,
      'animation':65,'frame':14,'previous_frame':player[0x48],'ride_state':255,'ride_animation':65,'hp':player[0x5c],
      'world':[struct.unpack_from('<i',player,o)[0]/65536 for o in (8,12)],'whole_entries':entries,
      'decoded_active_frame_sha256':sha(raw),'active_tiles':f['tile_count'],'active_compressed_offset':f['offset'],
      'active_buffer_address':'0x8016DEA8','active_buffer_equals_new_disc_decode':True,
      'vram_state_offset':vram,'gpu_uploaded_pixels_equal_new_disc_decode':True,'player_clut_row480_equals_riko_palette':True,
      'player_graphics_bank_pointer':hex(gp),'player_parts_bank_pointer':hex(cp),'active_pointers_equal_new_bank_bases':True,
      'RideArmor_heads_66_85_preserved_against_head_patch':True,
      'runtime_verified':'루트 새 부팅 실제 stage5 체이서에서 frame14 자원 전체/압축해제버퍼/VRAM/CLUT 일치',
      'limits':['일시정지 화면을 채취했으므로 체이서 몸체 전체 framebuffer 픽셀 일치 검사는 미실행.',
                '좌석/핸들 접점, 네 자세의 오르막·내리막 전환, 전체 28참조 재생은 이 단일 표본으로 검증하지 않음.'],
      'source_files_modified':False,'emulator_keys_sent':False,'process_memory_written':False}
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(OUT),'character':1,'stage':5,'animation':65,'frame':14,'tiles':f['tile_count'],'disk_ram_gpu_match':True}))
if __name__=='__main__':main()
