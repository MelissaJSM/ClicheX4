"""귀환156 양 의상의 새 세부 원화 입력. 이미 수용된 빈손/작은 웅크림 유지."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need

def main():
 p=N/'ultimate_victory_repaint/packed_victory_candidate_v1/PL02_U.ARC'
 need(digest(p)=='b7dcf46dba35084265e8b32529d7a4d072108ed201a60ba4f17fcc71494aa1c5','승리 부모')
 a=Archive(p.read_bytes());out=D/'body_inputs_v1';out.mkdir(exist_ok=False)
 target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1536));records=[]
 for col,mask in enumerate((15,0)):
  im=a.composite(156,mask)[0]
  target.alpha_composite(im.crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(col*768,0))
  for row,n in enumerate((0,207)):
   style.alpha_composite(a.composite(n,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  y,x=np.nonzero(np.array(im)[:,:,3]);records.append({'ref':156,'form':'before' if mask else 'after','mask':mask,'cell':col,'world_bbox':[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)],'source_rgba_sha256':sha(im.tobytes())})
 target.save(out/'targets.png');style.save(out/'style.png')
 hp=ROOT/'work/ver_rin_nana/nana_ultimate_armor/ceremony_v1/generated_first.png'
 hist=Image.open(hp).convert('RGBA');hist.crop((512,0,1024,512)).save(out/'historical156.png')
 prompt='''Use case: style-transfer. Neutral full-body adult heroine sprite artwork for a late-1990s console action game. Image1 is the edit target: exactly TWO full figures in one horizontal row, same pose156. Keep the full1536x1024 canvas, two768x1024 cells representing96x128 native pixels each. Left is the pink-jacket costume, right is the same woman's accepted black/pink athletic costume with bare arms. Preserve the exact existing outfit coverage.
Improve only the drawing detail and material separation to the level of Image2's accepted idle and new victory sprites: individually grouped pink hair locks, layered fringe, compact green eyes, pink jacket lapels and elbow folds, pale cuff edges, stable skin midtones and selective darker knee/calf shadow boundaries, gray shorts or pink belt, and green/gray shoes. Preserve the head and ear size, overall height and body proportions of Image1.
Both figures are in the SAME small crouched departure-ready pose. Both EMPTY fists are held close together at upper chest level; both elbows are bent close to the body. The knees bend gently with both shoes planted close together. There is NO handgun in this particular gesture. Image3 is the historical pose reference confirming these empty fists and bent knees, not an instruction to copy its background or change scale. Do not import the raised gun or wide-legged stance of Image2's victory pose.
Keep exact foot contacts, floor row, shoulder/wrist/knee/ankle placement, body lean and original canvas origins. Both costume versions must share the same head/hair/skin/hand/leg/shoe positions; only the jacket and costume fabric differ. The bare-arm version must have no leftover jacket collar, sleeve or cuff. Do not lengthen, thin or expand limbs; do not create a new standing or running pose. Retain facial identity and outfit colors while breaking up flat hair and sleeve areas into clean small pixel clusters.
Output only the two complete sprites at those same positions on an actually transparent background, with all ears and shoe tips inside the existing padding. No labels, grid, text, halo, floor shadow, energy effects, weapons or additional limbs. Crisp pixel clusters suitable for the original small sprite scale, no smooth gradients or tiny high-resolution linework.'''
 (out/'prompt.txt').write_text(prompt,'utf8')
 write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'parent_frozen_at_input_creation':(p.parent/'FROZEN.json').exists(),'frames':records,'native_cell':[96,128],'render_scale':8,'world_crop':[-48,-64,48,64],'historical_art':hp.relative_to(ROOT).as_posix(),'historical_art_sha256':digest(hp),'historical_crop':[512,0,1024,512],'gesture_policy':'양손 모두 빈 주먹을 가슴 앞에 둔 기존156. 권총/효과 없이 몸체1키×2의상만 새 상세 제작.','source_target_unchanged_from_arrival':True,'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','historical156.png','prompt.txt')],'native_packed':False,'runtime_verified':False})
 print(out)
if __name__=='__main__':main()
