"""등장 끝138의 전후 의상 두 표시. 139 전개는 별도 역사관계 근거로 수행한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
PROMPT='''Use case: style-transfer. A neutral full-body pixel-art game animation sheet.
Image1 is the EDIT TARGET: TWO complete adult Nana sprites side by side, the same settling-to-ready pose138. Left wears the accepted pink long-sleeved jacket; right wears the accepted black-and-pink athletic swimsuit costume with bare arms. Image2 is STYLE ONLY: accepted idle and accepted detailed air sprites, jacket on the top row and swimsuit on the bottom row.
Redraw only these two complete sprites with detailed but readable small native pixel clusters: layered pink fringe, separate darker and lighter hair strands, compact green-eyed face, the same bunny-ear accessory, small selective outlines, coherent sleeve and jacket folds. Make the LEFT jacket visibly long-sleeved with pale cuffs, open lapels and its short hem as in the accepted idle; the old target's simplified clothing fragments are not the jacket identity. On the RIGHT, keep the established black shoulder straps/top and pink waist trim, bare shoulders and arms, no leftover jacket sleeves/collar/cuffs. Neutral game costume and ordinary coverage; no body emphasis.
Preserve exactly the target's quiet standing recovery gesture, head angle, ear tips, eye center, shoulder, hand, hip, knee, ankle and shoe positions. Both feet must stay on the existing floor and keep the same spread. The arms remain in their current low ready positions. Any tiny held pistol remains in its existing hand at its existing compact size; do not add a raised weapon. Preserve pose and body anatomy across the two costume versions. Do not replace the pose with the style reference's idle or jump. Do not enlarge the face or shrink/lengthen the legs.
Image1 is1536x1024 with TWO equal768x1024 cells. Each cell is96x128 native pixels. Keep every sprite at exactly its existing cell origin and scale; do not auto-center or crop. Output exactly the same wide1536x1024 layout with TWO complete figures. Crisp pixel clusters, genuinely transparent background. No text, labels, grid, border, particles, aura, beam, cast shadow, blur or halo.'''
def main():
    p=N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC';need(digest(p)=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5','부모');a=Archive(p.read_bytes())
    relation=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ceremony_sources01/report.json';need(digest(relation)=='142b03a3788078269086f05f884c7e523add8a55e550e1b51b6beb90aba5e4a7','독립관계')
    out=D/'settle_inputs_v1';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1536));frames=[]
    for i,mask in enumerate((15,0)):
        im=a.composite(138,mask)[0];target.alpha_composite(im.crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(i*768,0))
        yy,xx=np.nonzero(np.array(im)[:,:,3]);frames.append({'cell':i,'ref':138,'form':'before'if mask else'after','mask':mask,'rgba_sha256':sha(im.tobytes()),'world_bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)],'fixed_cell_world':[-48,-64,48,64]})
        for col,n in enumerate((0,47)):style.alpha_composite(a.composite(n,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,i*768))
    target.save(out/'targets.png');style.save(out/'style.png');(out/'prompt.txt').write_text(PROMPT,'utf8')
    write(out/'manifest.json',{'source_arc':p.relative_to(ROOT).as_posix(),'source_arc_sha256':digest(p),'frames':frames,'native_cell':[96,128],'render_scale':8,'source_layout':[2,1],'linked_ref139':{'planned_translation':[0,-1],'policy':'과거 수용Nana 양폼의138→139 관계. 현재after153px 등록차이와 원US다른포즈를 별도기록한다.','independent_report':relation.relative_to(ROOT).as_posix(),'independent_report_sha256':digest(relation),'producer_verified':False},'inputs':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','prompt.txt')],'native_packed':False,'runtime_verified':False})
    print(json.dumps({'out':str(out),'frames':len(frames)}))
if __name__=='__main__':main()
