"""실제 F1의 포스 나나 자산·활성 텍스처·화면 픽셀을 읽기 전용 대조한다."""
import argparse,gzip,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import locate_vram,framebuffer,match_sprite


def verify(build,source,out,allow_screen_occlusion=False):
    build,source,out=[p.resolve() for p in (build,source,out)]
    require(build.is_relative_to(ROOT/'out/ver_rin_nana') and out.is_relative_to(build) and not out.exists(),'Fresh build evidence folder required')
    require(source.is_relative_to(ROOT/'work/ver_rin_nana') or source.is_relative_to(build),'Unexpected state path')
    manifest=json.loads((build/'manifest.json').read_text('utf8'))
    require(digest(build/'rin_nana.bin')==manifest['modified_bin']['sha256'],'BIN differs')
    require(digest(build/'modified.arc')==manifest['modified_archive_sha256'],'ARC differs')
    arc=(build/'modified.arc').read_bytes();data=source.read_bytes();state=gzip.decompress(data)
    require(len(state)==4254418 and state.startswith(b'ePSXe\x06\x00SLUS_005.61'),'Unsupported state')
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());exe=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.exe').read_bytes()
    addr=cfg['idle_sequence_address'];off=2048+addr-cfg['executable']['load_address'];anchor=exe[off:off+48];hit=state.find(anchor)
    require(hit>=0 and state.find(anchor,hit+1)<0,'Ambiguous RAM')
    rampos=hit-(addr&0x1fffff);ram=state[rampos:rampos+0x200000];player=ram[0x1418c8:0x1418c8+0xe4];n=player[0x47]
    require(player[2]==0 and player[0xa7]==15 and n in manifest['fourth_armor_frames'],'Unexpected armor frame')
    g=entry(arc,2);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    require(ram[0x16dea8:0x16dea8+len(raw)]==raw,'Active RAM texture differs')
    positions={str(k):ram.find(entry(arc,k)) for k in (2,3,9)};require(all(v>=0 for v in positions.values()),'Runtime asset differs')
    video=locate_vram(state,raw,f['tile_count']);out.mkdir(parents=True);(out/'SLUS_005.61.000').write_bytes(data);checks=[]
    for page in (0,240):
        screen=framebuffer(state,video,page);screen.save(out/f'framebuffer_{page}.png')
        for frame in manifest['fourth_armor_frames']:
            sprite=render(arc,frame,True)[0];sprite=sprite.crop(sprite.getbbox());matches=match_sprite(screen,sprite)
            if matches:checks.append({'page':page,'frame':frame,'matches':matches})
    if not allow_screen_occlusion:require(checks,'No complete framebuffer match')
    report={'state_sha256':digest(source),'build_sha256':manifest['modified_bin']['sha256'],'frame':n,
        'armor_mask':player[0xa7],'arm_type':player[0xb8],'ram_offset':rampos,'ram_entries':positions,
        'active_texture_identical':True,'vram_texture_identical':True,'vram_offset':video,'framebuffer_matches':checks,
        'framebuffer_fully_verified':bool(checks),'screen_comparison_limitation':None if checks else 'No complete match; overlay/scene effects require separate visual review. Asset identity alone is not a visual pass.',
        'evidence':'graphics-refreshed checkpoint after loading new BIN; not fresh disc resource loading or all motions'}
    write(out/'verification.json',report);print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-screen-occlusion',action='store_true',help='Keep RAM/VRAM evidence, explicitly mark unmatched framebuffer unverified')
    a=p.parse_args();verify(a.build,a.state,a.output,a.allow_screen_occlusion)
