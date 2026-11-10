"""검증된 잔기 앞 체크포인트의 그래픽만 갱신한다. 원본 진행은 보관한다."""
import gzip,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_checkpoint import refresh
from scripts.prepare_riko_ui import entry
from scripts.build_rin_effect_color_fix import PARENT,PARENT_SHA,OLD_STAGE_LIFE
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import locate_vram

def main():
    base=ROOT/'work/ver_rin_nana/checkpoints/before_actual_effect_colors_20261029'
    source=base/'current_progress';target=base/'refreshed_v2'/'SLUS_005.61.000'
    if target.exists():raise ValueError('Output already exists')
    pointer=json.loads((ROOT/'projects/ver_rin_nana/current_build.json').read_text('utf8'));build=ROOT/pointer['build']
    if not build.resolve().is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Unexpected build')
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA or digest(build/'rin_nana.bin')!=pointer['sha256']:raise ValueError('BIN hash mismatch')
    data=source.read_bytes();state=gzip.decompress(data)
    if len(state)!=4254418 or not state.startswith(b'ePSXe\x06\x00SLUS_005.61'):raise ValueError('Unsupported checkpoint')
    old=(PARENT/'modified.arc').read_bytes();new=(build/'modified.arc').read_bytes()
    for p,a in ((PARENT,old),(build,new)):
        m=json.loads((p/'manifest.json').read_text('utf8'))
        if sha256(a)!=m['modified_archive_sha256']:raise ValueError('ARC identity mismatch')
    g=entry(old,2);hit=state.find(g)
    if hit<0 or state.find(g,hit+1)>=0:raise ValueError('Graphics anchor not unique')
    rampos=hit-1542560
    if state[rampos+1756828:rampos+1756828+len(entry(old,3))]!=entry(old,3):raise ValueError('Parts anchor differs')
    refreshed,report=refresh(state,old,new,rampos)
    player=state[rampos+0x1418c8:rampos+0x1418c8+0xe4]
    frame=graphics_bank(g,0)['frames'][player[0x47]]
    packed=decode_stream(g,frame['offset'],frame['limit'],frame['tile_count']*128).data
    vram=locate_vram(state,packed,frame['tile_count'])
    if vram!=2569183:raise ValueError('VRAM layout differs')
    life=(build/'effect_colors/life_palette.bin').read_bytes();dst=bytearray(refreshed)
    # A runtime palette-upload copy repeatedly restores VRAM each frame.
    # Authenticate adjacent rows against the loaded COL buffer as well.
    if state[rampos+0x1d68b4-32:rampos+0x1d68b4+64]!=state[rampos+0x1420d0-32:rampos+0x1420d0+64]:raise ValueError('Palette upload copy differs')
    positions=[rampos+0x1420d0,rampos+0x1d68b4,vram+480*2048+11*32]
    for pos in positions:
        if state[pos:pos+32]!=OLD_STAGE_LIFE:raise ValueError('Actual stage life CLUT differs')
        dst[pos:pos+32]=life
    changed=[i for i,(a,b) in enumerate(zip(refreshed,dst)) if a!=b]
    if any(not any(p<=i<p+32 for p in positions) for i in changed):raise ValueError('Palette update escaped ranges')
    target.parent.mkdir();target.write_bytes(gzip.compress(bytes(dst),mtime=0))
    report.update(source_sha256=sha256(data),source_preserved=source.read_bytes()==data,output_sha256=digest(target),
        build=pointer['build'],build_sha256=pointer['sha256'],ram_offset=rampos,vram_offset=vram,
        palette_ranges=positions,palette_changed_bytes=len(changed),all_gameplay_bytes_preserved=True,
        runtime_evidence_kind='graphics-refreshed checkpoint; not proof of fresh disc loading')
    (target.parent/'refresh.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
    print(json.dumps(report))
if __name__=='__main__':main()
