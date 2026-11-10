from pathlib import Path
import json,sys,struct
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import sha256,psx_arc
from scripts.repack_zero import read_inputs
from scripts.build_riko_idle import check_motion_scale
from src.psx_hurt_launch import *
from src.psx_player import bank_offsets
from src.psx_frame_edit import edit_frame_indices,read_indexed_png
from src.psx_compress import replace_stream
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
D=Path(__file__).parent;E=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
profile,_,arc,gm,gfx,parts,words=read_inputs(E)
B=Path(json.loads((D/'builds.json').read_text())['build']['output']);P=ROOT/'out/ver_buki_riko/riko_bank1_20261024T082504508553Z'
changed=(B/'modified.arc').read_bytes();previous=(P/'modified.arc').read_bytes()
newgfx=changed[gm['offset']:gm['offset']+gm['size']];oldgfx=previous[gm['offset']:gm['offset']+gm['size']]
delta=[]
for bi in range(len(bank_offsets(gfx))):
 for f in graphics_bank(gfx,bi)['frames']:
  n=f['index'];length=f['tile_count']*128
  if decode_stream(newgfx,f['offset'],f['limit'],length).data!=decode_stream(oldgfx,f['offset'],f['limit'],length).data:delta.append([bi,n])
assert delta==[[0,n] for n in range(139,146)]
pngs=list(P.glob('*.png'));assert all((B/p.name).read_bytes()==p.read_bytes() for p in pngs)
assert changed[:gm['offset']]==previous[:gm['offset']] and changed[gm['offset']+gm['size']:]==previous[gm['offset']+gm['size']:]
bank=graphics_bank(gfx,0);roundtrip=[]
for n in (139,142,143,144):
 f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;c=composition_frame(parts,0,n);c=local_layer(c,c['parts'])
 picture=compose_indices(raw,f['tile_count'],c)[:2];edited=edit_frame_indices(raw,f['tile_count'],c,*picture);assert edited==raw
 reg,budget=replace_stream(gfx,f,edited);assert decode_stream(reg,f['offset'],f['limit'],f['tile_count']*128).data==raw
 roundtrip.append({'frame':n,'decoded_identical':True,'compressed_identical':reg==gfx,'budget':budget})
palette=struct.unpack('<64H',(D/'preview_palette.bin').read_bytes());frames={n:read_indexed_png(D/f'frame_{n:03d}.png',palette if n in MULTI_FRAMES else palette[:16],palette_banks=4 if n in MULTI_FRAMES else 1) for n in LAUNCH_FRAMES}
guards=[]
for n in LAUNCH_FRAMES:
 test=dict(frames);del test[n]
 try:validate_launch(gfx,parts,test)
 except ValueError:guards.append({'case':f'missing_{n}','rejected':True})
 else:raise AssertionError('Missing frame accepted')
for n in LAUNCH_FRAMES-{139}:
 test=dict(frames);pixels,size=test[n];v=bytearray(pixels);i=next(i for i,x in enumerate(v) if x);v[i]^=1;test[n]=(bytes(v),size)
 try:validate_launch(gfx,parts,test)
 except ValueError:guards.append({'case':f'derivative_pixel_{n}','rejected':True})
 else:raise AssertionError('Mutated derivative accepted')
exe=(E/'original.exe').read_bytes();md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN);start=0x8002456c;end=0x800245a0
disassembly=[f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(exe[start-0x80010000+2048:end-0x80010000+2048],start)]
report={'build':str(B),'previous':str(P),'previous_pngs_byte_identical':len(pngs),'changed_decoded_references':delta,'archive_outside_graphics_identical':True,'original_roundtrip':roundtrip,'guards':guards,'us_clut_selector_disassembly':disassembly,'source_exe_sha256':sha256(exe),'bin_sha256':json.loads((B/'manifest.json').read_text())['modified_bin']['sha256']}
(D/'preservation_audit.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps({k:report[k] for k in ('previous_pngs_byte_identical','changed_decoded_references','bin_sha256')}))
