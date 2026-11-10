"""실제 F1에서 포스 아머 CLUT의 원작 코드/VRAM 근거를 확인한다."""
import gzip,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_nova_watch import load,sha,digest,compose
from scripts.overhaul_sprites_audit import board

STATE=ROOT/'work/overhaul_20261105/runtime/nana_fourth_fresh_state/SLUS_005.61.000'
STATE_SHA='4d109b2297609a3dcf2d66da0f2827a49af8dff0023831aa308b02e7df15a089'
OUT=ROOT/'work/overhaul_20261105/ui/nana_fourth_nova_runtime01'

def main():
    assert digest(STATE)==STATE_SHA
    arc,exe,es,bank,frames=load();s=gzip.decompress(STATE.read_bytes());ram=s[442:442+0x200000];vram=s[2569183:2569183+1048576]
    assert ram[0x1418ca]==0 and ram[0x1418c8+0xa7]==15 and ram[0x1721f7]==0
    sourcecode=exe[0x257bc-0x10000+2048:0x2588c-0x10000+2048]
    assert sourcecode==ram[0x257bc:0x2588c]
    constants=[]
    for off,value in((0x257f0,0x7843),(0x25814,0x7843),(0x25840,0x7843),(0x25844,0x7844),(0x25870,0x7843)):
        assert struct.unpack_from('<I',ram,off)[0]==0x24060000|value
        constants.append({'address':hex(0x80000000+off),'instruction':'addiu $a2,$zero,'+hex(value)})
    palettes={};rows=[]
    for clut,row in((0x7800,0),(0x7843,1),(0x7844,2)):
        off=(clut>>6)*2048+(clut&63)*32;data=vram[off:off+32]
        assert data==es[9][row*32:(row+1)*32];palettes[clut]=data
        rows.append({'CLUT':hex(clut),'VRAM_word_xy':[(clut&63)*16,clut>>6],'matches_PL00_palette_row':row,'sha256':sha(data)})
    evidence=json.loads((OUT/'evidence.json').read_text('utf8'));items=[];seen=set();composites=[]
    basewords=struct.unpack('<64H',vram[480*2048:480*2048+128]);armorwords=struct.unpack('<16H',palettes[0x7843]);armwords=struct.unpack('<16H',palettes[0x7844])
    folder=OUT/'snapshot_palette_reconstruction';folder.mkdir(exist_ok=True)
    for event in evidence['events']:
        n=event['frame']
        if n in seen or not event['verified']:continue
        seen.add(n);raw=(OUT/event['gpu_capture']).read_bytes();f,expected=frames[n];assert raw==expected
        im=compose(raw,f['tile_count'],es[3],n,basewords,event['armtype'],armorwords,armwords)
        reference=compose(expected,f['tile_count'],es[3],n,struct.unpack_from('<64H',es[9]),event['armtype'])
        assert im.tobytes()==reference.tobytes()
        im.save(folder/f'{n:03}.png');items.append((str(n)+' observed upload + F1 palette',im));composites.append(n)
    board(items,folder/'review.png',cols=4)
    report={'source_state':STATE.relative_to(ROOT).as_posix(),'source_state_sha256':STATE_SHA,'native_code_start':'0x800257BC','native_code_sha256':sha(sourcecode),'native_constants':constants,'palettes':rows,'observed_upload_frames':sorted(composites),'GPU_bytes_with_normal_F1_palettes_match_disc_composite':True,'same_instant_as_nova_frame':False,'earlier_auxiliary_images_invalid':True,'earlier_images_pattern':'frame_*_GPU_palette.png','correction':'runtime01의 초기 부가 합성은 아머 CLUT를 base+1/+2로 가정해 색상을 잘못 해석했다. 원작은 고정0x7843/0x7844이며 실제 F1에서도 정확히 로딩됨. 초기 부가 이미지와 composition_matches_disc_with_live_palette false는 게임 오류 근거가 아니다. 실제 노바 시점의 팔레트 점멸은 별도 조건이므로 이 재합성을 그 순간의 화면과 동일하다고 하지 않는다.','runtime_upload_evidence_unchanged':True,'keys_sent':False,'process_memory_written':False}
    (OUT/'palette_correction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    evidence['auxiliary_composition_correction']='palette_correction.json';evidence['auxiliary_composition_images_invalidated']=True
    (OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'palette_CLUTs_verified':list(palettes),'frames':sorted(composites),'same_time_framebuffer':False}))
if __name__=='__main__':main()
