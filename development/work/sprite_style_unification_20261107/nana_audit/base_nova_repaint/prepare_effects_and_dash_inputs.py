"""원US214 효과124셀 재검증 및217 역사 가는 윤곽 분리 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need,helper
from scripts.c01_audio_build import read_disc
from prepare_common import comp
def main():
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['parent_arc'];need(digest(p)==meta['parent_sha256'],'부모');a=Archive(p.read_bytes())
 data=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC',))[0]['PL00_U.ARC'];u=Archive(data);old213=u.layer(213)[0];old214=u.layer(214)[0];fx=(old213==0)&(old214>0);need(int(fx.sum())==124,'원FX124')
 out=D/'preparation_effect_probe_v1';out.mkdir(exist_ok=False);fxz=np.where(fx,old214,0).astype(np.uint8);Image.fromarray(fxz).save(out/'effect214_indices.png');checks=[];rows=[]
 for pb in(0,5,6,7,8):
  expected=a.layer(213,pb)[0].copy();expected[fx]=old214[fx] if pb==0 else 0
  need(np.array_equal(expected,a.layer(214,pb)[0]),f'기존214출처/{pb}')
 layers={n:{pb:np.array(Image.open(D/f'common_layers_probe_v1/layer{pb}_{src:03}.png'))for pb in(0,5,6,7,8)}for n,src in((213,213),(214,213),(215,215),(216,215))}
 for pb,z in layers[214].items():z[fx]=fxz[fx] if pb==0 else 0
 for n,ls in layers.items():
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  if n==214:
   for mask in range(16):
    for arm in(1,2):
     actual=np.array(comp(a,ls,mask,arm));expected=np.array(a.rgba(fxz));need(np.array_equal(actual[fx],expected[fx]),'FX全조건')
  checks.append({'ref':n,'source_body':213 if n==214 else 215 if n==216 else n,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()}})
 for mask in(0,15):
  for n in(213,214,215,216):rows.append((f'{mask}/{n}',[('parent',a.composite(n,mask)[0]),('new body+source FX',comp(a,layers[n],mask))]))
 for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
 write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_sha256':digest(p),'original_US_PL00_sha256':sha(data),'effect214_source_rule':'US213 transparent & US214 opaque;現在C04外部124既存方針','effect214_texels':[[int(x-160),int(y-160),int(fxz[y,x])]for y,x in np.argwhere(fx)],'parent_all5_reconstructed_exact':True,'new_effect_all32_rgba_conditions_exact':True,'new_body_under_fx_pixels':int(((layers[213][0]>0)&fx).sum()),'new_armor_under_fx_pixels':{str(pb):int(((layers[213][pb]>0)&fx).sum())for pb in(5,6,7,8)},'frames':checks,'native_packed':False,'runtime_verified':False})
 hist=ROOT/'work/overhaul_20261105/ui/nana_fourth_nova';fm=np.array(Image.open(hist/'fourth_217.png'))>0
 mask=np.zeros((384,384),bool);mask[80:240,80:336]=fm
 ring=binary_dilation(mask,iterations=1)&~mask;need(np.all(a.layer(217)[0][ring]==9),'217역사ring9');need(np.array_equal(a.layer(217)[0]>0,mask|ring),'217몸과ring알파')
 inp=D/'b_inputs_v1';inp.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,768));style=target.copy();frames=[];bodyrows=[]
 for col,(form,masknum)in enumerate((('base',0),('fourth',15))):
  indices=a.layer(217)[0].copy()
  if masknum:
   for pb in(8,5,7,6):z=a.layer(217,pb)[0];indices[z>0]=z[z>0]
  body=np.where(mask,indices,0).astype(np.uint8);Image.fromarray(body).save(inp/f'{form}_217_body_indices.png')
  target.alpha_composite(a.rgba(body,16 if masknum else 0).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,0))
  style.alpha_composite(a.composite(0,masknum)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,0))
  frames.append({'ref':217,'form':form,'mask':masknum,'cell':col,'body_sha256':sha(body.tobytes()),'body_pixels':int((body>0).sum())})
  bodyrows.append((form,[('current with thin FX',a.composite(217,masknum)[0]),('body only input',a.rgba(body,16 if masknum else 0)),('approved idle',a.composite(0,masknum)[0])]))
 target.save(inp/'targets.png');style.save(inp/'style.png');helper.grid(bodyrows,inp/'input_review.png',6)
 prompt='''Use case: style-transfer. Edit the FIRST transparent two-cell horizontal pixel-art sheet. The SECOND is Nana's approved adult character design and fine sprite detail. Make exactly TWO game sprites, left BASE costume and right FOURTH costume, preserving the first sheet's two fixed 96 by 96 game canvases enlarged eight times, all blank margins and pixel-game scale.
These are the SAME compact horizontal airborne rush pose. Her face points left and the body leans almost horizontally. Keep the front bent arm tucked beside the face, the other arm alongside the torso, both hands, the sharply bent knees and folded feet at EXACTLY their first-sheet positions. Preserve the eye location, head size, torso length, hip position and two distinct shoe/boot endpoints. Do not straighten the knees, lengthen the legs, invent stretched arms, enlarge the figure or move it in its cell.
Left wears the approved black beret, pink curled hair, dark long-sleeved dress/skirt and dark boots from the second image's left. Right wears the approved black bonnet with trailing veil, dark dress and its distinct bare lower legs/small shoes from the second image's right. Both retain the same body size and pose. Retain the small green iris. Add the approved fine dark curled hair locks, middle pink strands and short highlights, hat/veil shading, readable collar and sleeve folds, skirt shading, hand/wrist and ankle details. Keep variable thin dark contours and natural shaded skin, avoiding a smooth flat pink mass, thick black border, or thin stick-like limbs.
The input has been separated from its game effects. This is ONLY the adult heroine's clothed body: do NOT add a pink outline, glow, aura, speed trails, flame, weapon, projectile or halo. Hands are empty. Do not alter clothing into other costumes, add extra hands/feet, text, labels, a grid, background or cast shadow. Match the first sheet's exactly two fixed positions on transparent RGBA.'''
 (inp/'prompt.txt').write_text(prompt,'utf8')
 write(inp/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_sha256':digest(p),'native_cell':[96,96],'world_crop':[-48,-48,48,48],'layout':[2,1],'frames':frames,'historical_alpha_source':(hist/'fourth_217.png').relative_to(ROOT).as_posix(),'historical_alpha_source_sha256':digest(hist/'fourth_217.png'),'historical_ring_pixels':int(ring.sum()),'historical_body_pixels':int(mask.sum()),'current217_alpha_reconstruction_exact':True,'files':[{'path':(inp/f).relative_to(ROOT).as_posix(),'sha256':digest(inp/f)}for f in('targets.png','style.png','prompt.txt')],'scope':'원217 몸에서 역사Manhattan1 ring만 분리한 신체입력. 새몸 ring/220효과 연동은후속수용검토.','native_packed':False,'runtime_verified':False})
 print(json.dumps({'effect214':int(fx.sum()),'body217':int(mask.sum()),'ring217':int(ring.sum()),'inputs217_saved':True}))
if __name__=='__main__':main()
