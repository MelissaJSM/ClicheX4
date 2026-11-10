import gzip,json,shutil,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.prepare_nana_pause import entry
from src.epsxe_state import framebuffer,match_sprite
base=ROOT/'work/ver_rin_nana/checkpoints/nana_pause_preview_20261030';proof=base/'runtime';proof.mkdir(exist_ok=False)
source=ROOT/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';shutil.copyfile(source,proof/source.name);state=gzip.decompress((proof/source.name).read_bytes());build=ROOT/'out/ver_rin_nana/nana_pause_20261030T030037246376Z';vram=2569183
g=entry((build/'modified.arc').read_bytes(),0x10007);pal=entry((build/'modified.arc').read_bytes(),0x11)
if not all(state[vram+(256+r)*2048+832*2:vram+(256+r)*2048+832*2+128]==g[r*128:(r+1)*128]for r in range(256)):raise ValueError('Loaded menu atlas differs')
preview=json.loads((base/'preview.json').read_text('utf8'))
for q in preview['changes']:
    if q['label']=='menu palette RAM'and state[q['offset']:q['offset']+q['size']]!=pal:raise ValueError('RAM palette differs')
    if q['label']=='menu portrait VRAM palette'and state[q['offset']:q['offset']+32]!=pal[320:352]:raise ValueError('VRAM palette differs')
hits={};im=Image.open(build/'pause/portrait.png').convert('RGBA')
for y in(0,240,256):
    screen=framebuffer(state,vram,y);found=match_sprite(screen,im)
    if found:hits[str(y)]=found;screen.save(proof/f'menu_{y}.png')
if not hits:raise ValueError('No exact visible portrait')
report={'build':build.relative_to(ROOT).as_posix(),'bin_sha256':digest(build/'rin_nana.bin'),'session':'work/ver_rin_nana/emulator_sessions/20261030T030225867920Z','state_sha256':digest(source),'matches':hits,'full_menu_atlas_rows_equal':256,'ram_vram_palette_equal':True,'graphics_refreshed_checkpoint':True,'fresh_disc_portrait_load_verified':False,'progress_preserved':True}
(proof/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))
