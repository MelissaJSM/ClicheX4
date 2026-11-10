"""F3에 남은 이전 저장 UI 텍스처만 갱신하고 다른 저장 바이트는 보존한다."""
import argparse,gzip,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.verify_nana_ultimate_ui import read_assets
from scripts.prepare_riko_ui import entry
from scripts.prepare_nana_fourth_pilot import require,write
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_ui_atlas import tile_pixels

OLD_BUILD=ROOT/'out/ver_rin_nana/nana_fourth_ui_20261030T122936152482Z'
OLD_SHA='c7fc576c68a4c4bc2f55090bfccf47d4e03a11489fa49c9b824399cbcab11d8a'
TILES=[200,201,202,221,222,223,237]
RAM_OFFSET=442
VRAM_OFFSET=2569183

def atlas(raw,video=VRAM_OFFSET):
    return b''.join(raw[video+(256+y)*2048+1792:video+(256+y)*2048+1920] for y in range(256))

def refresh(raw,old_texture,new_texture,menu):
    require(len(raw)==4254418 and raw.startswith(b'ePSXe\x06\x00SLUS_005.61'),'Unsupported checkpoint')
    anchor=bytes.fromhex('150001000c0001922a0001930c00019436000100')
    require(raw[RAM_OFFSET+0x11a2f8:RAM_OFFSET+0x11a2f8+len(anchor)]==anchor,'RAM anchor differs')
    ram=raw[RAM_OFFSET:RAM_OFFSET+0x200000]
    require(ram.count(menu)==1,'Current menu resource missing from state')
    require(len(old_texture)==len(new_texture)==32768,'Unsupported atlas size')
    changed_tiles=[t for t in range(256) if tile_pixels(old_texture,t)!=tile_pixels(new_texture,t)]
    require(changed_tiles==TILES,'Unexpected atlas change scope')
    before=atlas(raw);require(before in (old_texture,new_texture),'Unrecognized resident UI texture; no writes')
    po=struct.unpack_from('<I',menu,4)[0]
    # Gameplay reuses these CLUT slots; preserve them without replacing colors.
    in_save_menu=ram[0x1721c0]==12
    if in_save_menu:
        for r in (8,9,10,11,30,31):
            off=VRAM_OFFSET+(480+r//16)*2048+(r%16)*32
            require(raw[off:off+32]==menu[po+r*32:po+(r+1)*32],'Resident UI palette differs')
    result=bytearray(raw);allowed=set()
    for y in range(256):
        for x in range(128):
            i=y*128+x
            if old_texture[i]!=new_texture[i]:
                off=VRAM_OFFSET+(256+y)*2048+1792+x
                result[off]=new_texture[i];allowed.add(off)
    differences=[i for i,(a,b) in enumerate(zip(raw,result)) if a!=b]
    require(all(i in allowed for i in differences),'Non-atlas byte changed')
    require(atlas(result)==new_texture,'Atlas reconstruction differs')
    require(result[RAM_OFFSET:RAM_OFFSET+0x200000]==ram,'Game progress or code changed')
    p=ram[0x1418c8:0x1418c8+228]
    proof={'ram_offset':RAM_OFFSET,'vram_offset':VRAM_OFFSET,'changed_vram_bytes':len(differences),'changed_tiles':changed_tiles,
           'all_other_state_bytes_identical':True,'all_ram_and_progress_identical':True,'palettes_preserved':True,'save_palette_checked':in_save_menu,
           'current_engine_state':ram[0x1721c0],'current_player':{'character':p[2],'hp':p[0x5c],'armor':p[0xa7],
           'weapon':p[0x93],'ultimate':ram[0x1721f7],'world':[struct.unpack_from('<i',p,o)[0]/65536 for o in (8,12)]},
           'already_current':before==new_texture,'atlas_before_sha256':sha256(before),'atlas_after_sha256':sha256(new_texture)}
    return bytes(result),proof

def main(source,source_sha,build,out):
    source,build,out=source.resolve(),build.resolve(),out.resolve()
    require(source.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') and out.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') and not out.exists(),'Fresh isolated checkpoint paths required')
    require(build.is_relative_to(ROOT/'out/ver_rin_nana') and digest(source)==source_sha,'Source/path mismatch')
    m=json.loads((build/'manifest.json').read_text('utf8'))
    require(m['task']=='ultimate_armor_nana' and digest(build/'rin_nana.bin')==m['modified_bin']['sha256'],'Changed Ultimate build')
    require(digest(OLD_BUILD/'rin_nana.bin')==OLD_SHA,'Unsupported old atlas source')
    a,_=read_assets(OLD_BUILD/'rin_nana.bin',('LOAD_U.ARC',));b,_=read_assets(build/'rin_nana.bin',('MOJIPAT.ARC','LOAD_U.ARC'))
    old,new=entry(a['LOAD_U.ARC'],0x10008),entry(b['LOAD_U.ARC'],0x10008);menu=b['MOJIPAT.ARC'];raw=gzip.decompress(source.read_bytes())
    changed,proof=refresh(raw,old,new,menu);again,_=refresh(raw,old,new,menu);require(changed==again,'Independent refresh differs')
    same,second=refresh(changed,old,new,menu);require(same==changed and second['changed_vram_bytes']==0,'Refresh is not idempotent')
    tests=[('resident_unrelated_tile',VRAM_OFFSET+256*2048+1792),('menu',RAM_OFFSET+raw[RAM_OFFSET:RAM_OFFSET+0x200000].find(menu)),('resident_ultimate_tile',VRAM_OFFSET+(256+192)*2048+1792+64),('ram_anchor',RAM_OFFSET+0x11a2f8)]
    if proof['save_palette_checked']:tests.append(('palette30',VRAM_OFFSET+481*2048+14*32))
    rejected=[]
    for label,pos in tests:
        corrupt=bytearray(raw);corrupt[pos]^=1
        try:refresh(bytes(corrupt),old,new,menu)
        except ValueError:rejected.append(label)
        else:raise AssertionError('Unsafe checkpoint accepted: '+label)
    out.parent.mkdir(parents=True,exist_ok=True);packed=gzip.compress(changed,mtime=0);out.write_bytes(packed)
    require(digest(source)==source_sha and gzip.decompress(out.read_bytes())==changed,'Source/output integrity differs')
    proof.update(source=source.relative_to(ROOT).as_posix(),source_sha256=source_sha,output_sha256=sha256(packed),
                 build=build.relative_to(ROOT).as_posix(),build_sha256=m['modified_bin']['sha256'],old_atlas_build_sha256=OLD_SHA,
                 reproduced_identical=True,idempotent=True,rejected_corruptions=rejected,game_bin_changed=False)
    write(out.parent/'refresh.json',proof);print(json.dumps(proof))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--source-sha256',required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.source,a.source_sha256,a.build,a.output)
