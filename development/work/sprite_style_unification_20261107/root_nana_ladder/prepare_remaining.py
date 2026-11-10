from pathlib import Path
import json,sys,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((D/'first_inputs01/manifest.json').read_text('utf8'));source=ROOT/m['source_arc'];data=source.read_bytes();assert sha(data)==m['source_arc_sha256'];arc=Archive(data)
desc={144:'rear-view middle climb with one hand extended overhead, the other bent out to the side and one knee lifted',149:'side-facing hanging at rest with one arm raised straight overhead and the other bent near the chest',151:'rear-view nearing the top of the ladder with both hands above the head and one knee bent',153:'rear-view pulling over the top with elbows out and legs tucked',154:'side-view low landing crouch after stepping off the ladder',183:'rear-view standing/stepping onto the ladder with hands held near shoulder height'}
for page,pair in enumerate(((144,149),(151,153),(154,183)),2):
 out=D/f'inputs_page{page:02}';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));frames=[]
 for row,(form,mask) in enumerate((('base',0),('fourth',15))):
  for col,ref in enumerate(pair):
   im,_=arc.composite(ref,mask,2);target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
   frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':ref,'rgba_sha256':sha(im.tobytes()),'bbox':im.getbbox(),'fixed_cell_world':[-48,-48,48,48]})
 target.save(out/'targets.png')
 prompt=(D/'first_inputs01/prompt.txt').read_text('utf8')
 prompt=prompt.replace('left column is ladder-grab transition143 with an arm extended diagonally up-left and bent knees; right column146 is rear-view climbing with a hand raised straight up, opposite arm bent to the side and one leg bent.',f'left column is animation frame {pair[0]}, {desc[pair[0]]}; right column is frame {pair[1]}, {desc[pair[1]]}.')
 prompt+='\nImage 3 is the recently refined matching four-pose ladder sheet, STYLE/DETAIL REFERENCE ONLY. Use its separated pink hair strands and shaped black veil folds for continuity. Do not substitute its poses for target poses. Keep every target hand, knee, foot and head at its original grid coordinate and match the original figure size, with NO extra pixel at the soles. Preserve the target view direction. Keep rear views as rear views.'
 (out/'prompt.txt').write_text(prompt,'utf8')
 manifest={**m,'frames':frames,'scope':'나나 기본/포스 사다리 추가4표시 원화 입력','inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())} for p in (out/'targets.png',D/'first_inputs01/style.png',D/'first_art01/generated.png',out/'prompt.txt')]}
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8');print(out.name,pair)
