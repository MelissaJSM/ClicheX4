"""기존 새 원화 3개의 그늘쪽 다리 경계 보완 입력. 새 그림 생성은 별도 도구."""
from pathlib import Path
import sys,json
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need,sha
def main():
 out=D/'leg_edges_inputs_v1';out.mkdir(exist_ok=False);src=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';a=Archive(src.read_bytes());canvas=Image.new('RGBA',(1536,1536));records=[]
 for i,(n,page)in enumerate([(101,'charge'),(102,'recovery_ground'),(231,'recovery_ground')]):
  reg=json.loads((D/f'{page}_registered_v1/registration.json').read_text('utf8'));q=next(r for r in reg['frames']if r['ref']==n and r['form']=='fourth');p=D/f'{page}_v1/generated.png';need(digest(p)==reg['source_art_sha256'],'Art source');art=Image.open(p).convert('RGBA').crop(q['cell_crop']).resize((768,768),Image.Resampling.NEAREST)
  cell=Image.new('RGBA',(768,768));dx,dy=q['whole_translation'];cell.alpha_composite(art,(dx*8,dy*8));canvas.alpha_composite(cell,(i%2*768,i//2*768));records.append({'cell':i,'ref':n,'source_art':p.relative_to(ROOT).as_posix(),'source_art_sha256':digest(p),'source_crop':q['cell_crop'],'whole_translation_native':[dx,dy],'input_scale':8})
 idle=a.composite(0,15)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST);canvas.alpha_composite(idle,(768,768));canvas.save(out/'edit_targets_and_idle.png')
 prompt='''Use case: local image editing. This 1536x1536 transparent sheet has FOUR equal 768px cells. TOP LEFT is adult Nana Fourth costume raised-shot pose101; TOP RIGHT is the same adult character's recovery102; BOTTOM LEFT is grounded pose231. BOTTOM RIGHT is the already accepted idle STYLE REFERENCE and MUST remain exactly unchanged.
Edit ONLY the thin shadow-side LEG CONTOURS in the first THREE sprites. Match the accepted idle's readable 1-native-pixel dark silhouette on shadow-facing calves, ankles, and the line separating folded legs. The current gray outer leg lines become too faint at game size. Preserve skin highlights and midtone skin shading; do not draw a heavy continuous black border around every bright side. Make a selective dark charcoal contour like the reference, with clear two-leg separation in the top-right tucked pose. Do not change leg width, length, joint angles, foot placement, shoe silhouette, pose, or body scale. Keep all existing pixel clusters of the hair, veil, face, arms, gun, blouse and skirt untouched. The dark-red shoes and their shape are unchanged.
This is a color/contrast correction of the existing outer leg boundary, not anatomy redrawing and not a new pose. Keep the transparent silhouette exactly as drawn; do not expand the skin, add holes, thicken the legs, or sharpen them into spikes. Preserve the fine source hair and clothing detail in every cell. Same centers, margins, and full canvas. Return the same four full-body game sprites on genuine transparent background, no text, guides, frame, glow, ground shadow or background.'''
 (out/'prompt.txt').write_text(prompt+'\n','utf8');write(out/'manifest.json',{'source_arc_sha256':digest(src),'frames':records,'reference_idle_sha256':sha(a.composite(0,15)[0].tobytes()),'canvas':[1536,1536],'grid':[2,2],'native_cell':[96,96],'edit_targets_sha256':digest(out/'edit_targets_and_idle.png'),'prompt_sha256':digest(out/'prompt.txt'),'scope':'기존 새 포스101/102/231 다리 그늘 경계 색만 보완. 생성 결과는 고정 좌표의 실제 외곽 의미영역만 채택할 예정이며 전체 몸체 재등록은 하지 않는다.'});print(out)
if __name__=='__main__':main()
