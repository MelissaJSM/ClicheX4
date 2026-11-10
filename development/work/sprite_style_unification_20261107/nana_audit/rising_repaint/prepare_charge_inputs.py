"""차지100/101과 회복102/지상231의 새 전신 입력. 일반104와 팔방향을 혼동하지 않는다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 data=(N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC').read_bytes();assert sha(data)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa';a=Archive(data)
 for page,refs in [('charge',(100,101)),('recovery_ground',(102,231))]:
  out=D/(page+'_inputs_v1');assert not out.exists();out.mkdir();target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));records=[]
  for i,(form,mask,n) in enumerate([('base',0,refs[0]),('base',0,refs[1]),('fourth',15,refs[0]),('fourth',15,refs[1])]):
   im=a.composite(n,mask)[0];window=(112,112,208,208);assert np.count_nonzero(np.array(im)[:,:,3])==np.count_nonzero(np.array(im.crop(window))[:,:,3])
   target.alpha_composite(im.crop(window).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768));records.append({'cell':i,'form':form,'ref':n,'source_RGBA_sha256':sha(im.tobytes()),'crop_world':[-48,-48,48,48]})
  for i,(form,mask,n) in enumerate([('base',0,0),('base',0,47),('fourth',15,0),('fourth',15,47)]):
   im=a.composite(n,mask)[0];style.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
  target.save(out/'edit_targets.png');style.save(out/'accepted_style.png')
  first='coiled charged-upward-shot windup with deeply bent knees' if page=='charge' else 'falling recovery from an upward charged shot, knees tucked and legs pointing diagonally down-right'
  second='rising charged shot with the left-side pistol raised fully overhead, one knee lifted and the other leg extended diagonally down-left' if page=='charge' else 'grounded standing upward shot, keep the original two foot positions and their sole height'
  prompt=f'''Use case: style-transfer. Edit four full-body adult Nana action-game pixel sprites in the first image; the second image is the accepted idle and recent airborne pixel-art style master. Keep the exact 1536x1536 canvas and 2x2 equal cells, the bodies at their existing centers and native sizes. Top row basic black outfit with long fitted boots; bottom row Fourth black veil outfit with bare legs and small dark red shoes. Left column {refs[0]}: {first}. Right column {refs[1]}: {second}.
Redraw these FOUR bodies with purposeful hair-strand clusters, fine gray cloth folds/cuffs, layered pink locks and the eye/head/shoe proportions of the second image. Preserve pose, face direction, original eye locations, knee/ankle/foot anchors and black clothing design. No body enlargement, stretching, smoothing or big undifferentiated black strips. Preserve each costume's materials: black fitted boots in the top row, natural skin-shaded legs and dark red shoes in the bottom row. Keep dark and light skin planes consistent with accepted idle, not a thick continuous black outline on the bright leg side.
These particular charged/ground poses intentionally keep the pistol-bearing arm on the VIEWER-LEFT of the face. Do not swap it to the right, do not mirror the body. Preserve the exact old upward muzzle positions and small pistol size; keep the arm naturally connected shoulder/elbow/cuff/wrist to the pistol grip. One black-and-pink pistol Sarang-i in one hand, exactly two arms/two legs. Do not change the pistol into a fist or a cannon. No flames, shot effects or particles.
Match the same refined head and clothing density in all four cells. The long hair may flow as in the existing pose but must retain a narrow face and separated strands rather than a broad plain pink wedge. Keep full figures inside their cells with the same transparent margins. Return only four sprites on a genuinely transparent background. No grid, text, guide marks, watermarks, glow or cast shadow. Crisp intentional PS1-resolution pixel clusters, not a smooth anime illustration.'''
  (out/'prompt.txt').write_text(prompt+'\n','utf8')
  meta={'source_arc_sha256':sha(data),'frames':records,'canvas':[1536,1536],'grid':[2,2],'cell':[768,768],'native_cell':[96,96],
   'original_US_pose_comparison':'native_contacts_v1/original_pose_1.png','source_policy':'원US는100..102와231/232에서 왼쪽 손,103/104에서 오른쪽 손을 사용한다. 232는 현재231과RGBA정확동일이나 최종 native 별도대조한다.',
   'images':{p.name:sha(p.read_bytes())for p in out.glob('*.png')},'prompt_sha256':sha((out/'prompt.txt').read_bytes())}
  (out/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
  print(out)
if __name__=='__main__':main()
