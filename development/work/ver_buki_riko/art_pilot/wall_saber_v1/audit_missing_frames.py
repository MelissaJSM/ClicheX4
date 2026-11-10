from pathlib import Path
import sys,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.repack_zero import read_inputs
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
D=Path(__file__).parent;B=ROOT/'out/ver_buki_riko/riko_bank1_20261024T070810249163Z'
profile,_,original_arc,gm,gfx,parts,pal=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
arc=(B/'modified.arc').read_bytes();built=arc[gm['offset']:gm['offset']+gm['size']]
def pixels(g,bi,n):
 f=graphics_bank(g,bi)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 return compose_indices(raw,f['tile_count'],composition_frame(parts,5 if bi else 0,n))[:3]
records=[]
for bi,ns in [(0,range(35,44)),(1,[50,51,53,54,56,57,59,61,63,65]),(0,range(149,155))]:
 for n in ns:
  old,size,bounds=pixels(gfx,bi,n);new,newsize,_=pixels(built,bi,n)
  records.append({'bank':bi,'frame':n,'original_indices_sha256':sha256(old),'current_indices_sha256':sha256(new),
   'same_as_original':old==new,'different_pixels':sum(a!=b for a,b in zip(old,new)),'size_unchanged':size==newsize})
board=Image.new('RGBA',(6*240,290),(32,36,48));draw=ImageDraw.Draw(board)
for i,n in enumerate(range(149,155)):
 data,size,b=pixels(gfx,0,n);path=D/f'original_low_hp_{n}.png';save_image(data,size,pal,path)
 cell=Image.new('RGBA',(80,90));cell.alpha_composite(Image.open(path).convert('RGBA'),(40+b[0],55+b[1]));board.alpha_composite(cell.resize((240,270),Image.Resampling.NEAREST),(i*240,20));draw.text((i*240+4,2),f'{n} ORIGINAL',fill='white')
board.save(D/'low_hp_original_review.png')
trace=ROOT/'work/ver_buki_riko/input_playback/20261024T071550989151Z/playback.local.json'
tr=json.loads(trace.read_text());observed=sorted({r[5] for r in tr['rows'] if r[4]==6})
vpath=ROOT/'work/ver_buki_riko/wall_saber_runtime/20261024T071550227238Z/verification.local.json';v=json.loads(vpath.read_text())
report={'source_sha256':profile['source_sha256'],'build':str(B),'frame_checks':records,
 'original_wall_cling_body_remaining':[r['frame'] for r in records if r['bank']==0 and 35<=r['frame']<=43 and r['same_as_original']],
 'original_wall_saber_body_remaining':[r['frame'] for r in records if r['bank']==1 and r['same_as_original']],
 'original_low_hp_idle_remaining':[r['frame'] for r in records if r['bank']==0 and 149<=r['frame']<=154 and r['same_as_original']],'low_hp_observed_in_run':observed,
 'low_hp_rule':'player_set_idle_animation: hp < max_hp / 3 selects animation6',
 'source_function':'work/research/decomp/src/main/player_common.c:1101',
 'trace':str(trace),'bank1_runtime':str(vpath),
 'bank1_ram_vram_palette_verified':sorted(int(n) for n,r in v['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in r['samples'])),
 'bank1_full_framebuffer_verified':v['verified_frames'],'bank1_unobserved':[int(n) for n,r in v['frames'].items() if not r['observed']],
 'style_issue':'Wall cling uses existing wall-side head/body; new wall saber uses front head and a longer-legged narrower pose. Head ROI equality alone does not prove anatomical consistency.',
 'no_claim_all_visible_awkwardness_is_caused_by_low_hp_idle':True}
(D/'missing_frame_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='frame_checks'}))
