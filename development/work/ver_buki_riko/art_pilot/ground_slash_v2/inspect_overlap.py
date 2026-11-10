from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.repack_zero import read_inputs
from src.psx_player import graphics_bank,composition_frame,decode_stream,indexed_atlas,compose_indices
from src.psx_frame_edit import frame_coverage
from scripts.extract_zero import save_image
D=Path(__file__).parent
profile,project,arc,gmeta,gfx,parts,words=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
bank=graphics_bank(gfx,0)
report=[]
for n in range(77,82):
 f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 at,m,h=indexed_atlas(raw,f['tile_count']);coverage,size,b=frame_coverage(raw,f['tile_count'],c)
 overlap=[]
 for i,sources in enumerate(coverage):
  if len(set(sources))>1:
   overlap.append({'world':[i%size[0]+b[0],i//size[0]+b[1]],'sources':sources,'values':[(raw[o]>>s)&15 for o,s in sources]})
 report.append({'frame':n,'parts':c['parts'],'overlap':overlap})
 save_image(at,(256,h),words,D/f'original_atlas_{n}.png')
(D/'overlap_details.json').write_text(json.dumps(report,indent=2),encoding='utf8')
for r in report:
 print(r['frame'],[(p['tile'],p['x'],p['y']) for p in r['parts']])
 if r['overlap']:
  pairs={tuple(v['values']) for v in r['overlap']};print('overlap values',sorted(pairs));print('opaque',sum(any(v['values']) for v in r['overlap']))
with (ROOT/project['source_bin']).open('rb') as stream:
 stream.seek(232979*2352);raw=stream.read(576*2352)
exe=b''.join(raw[i+24:i+2072] for i in range(0,len(raw),2352))
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
lines=[f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(exe[0x886ec:0x88df4],0x80097eec)]
(D/'saber_weapon_us_disassembly.txt').write_text('\n'.join(lines),encoding='utf8')
print('weapon excerpt instructions',len(lines),'EXE header',exe[:8])
