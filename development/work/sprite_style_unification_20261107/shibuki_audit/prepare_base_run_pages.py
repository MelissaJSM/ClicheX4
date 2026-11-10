"""기본/포스 나머지 이동12키의 원점 고정 입력. 게임 파일 쓰기 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
P=H/'prepared_dash_base01/PL00_U.ARC';PSHA='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b'
GROUPS={'page02':[5,7,9],'page03':[13,15,17],'page04':[21,23,25],'page05':[27,29,31]};CROP=(128,124,192,188)
def main():
    o=H/'base_run_inputs01';need(not o.exists(),'Fresh output');need(sha(P.read_bytes())==PSHA,'Parent changed');a=Archive(P.read_bytes());o.mkdir()
    prompt=(H/'base_run_followup02/prompt.txt').read_text('utf8')
    for name,refs in GROUPS.items():
        d=o/name;d.mkdir();im=Image.new('RGBA',(1536,1024));anchors=[]
        for row,(form,mask)in enumerate((('base',0),('fourth',15))):
            for col,n in enumerate(refs):
                q=a.composite(n,mask)[0];crop=q.crop(CROP);need(np.count_nonzero(np.array(q)[:,:,3])==np.count_nonzero(np.array(crop)[:,:,3]),'Clipped target');im.alpha_composite(crop.resize((512,512),Image.Resampling.NEAREST),(col*512,row*512));q.save(d/f'{form}_{n:03}.png');yy,xx=np.nonzero(np.array(q)[:,:,3]);anchors.append({'form':form,'ref':n,'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'sole_y':int(yy.max())-160})
        im.save(d/'edit_target.png');style=Image.open(H/'base_run_followup02/accepted_style.png');style.save(d/'accepted_style.png')
        follow=Image.new('RGBA',(1536,1024))
        for row,form in enumerate(('base','fourth')):
            for col,n in enumerate((3,11,19)):
                q=Image.open(H/'base_run_layers_probe01'/f'{form}_{n:03}.png');follow.alpha_composite(q.crop(CROP).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
        follow.save(d/'new_detail_reference.png')
        text=prompt.replace('Columns are3 the transition into movement with its forward lean and split legs,11 a walking stride,19 the different mid-step walking pose.',f'Columns are native motion refs {refs[0]}, {refs[1]}, {refs[2]}: three distinct consecutive stride poses. Their exact thigh, knee, ankle and foot positions must follow Image1.').replace('Image2 is the accepted style reference at the same scale:', 'Image3 shows the newly detailed SAME character and costumes in OTHER walking poses. Match its readable locks, collar and folds, but do not substitute its poses. Image2 is the accepted style reference at the same scale:')
        text+='\nPreserve distinct alternating stride phases. Never reuse one leg arrangement for several columns. Keep the eye positions and both foot silhouettes at the same native coordinates as Image1, including airborne feet. Arms stay bent in their original run gesture; no weapon or new hand. Avoid losing the gold pupil at small scale. Preserve the small red side flower in BASE and the dark/gold side ornament in FOURTH.\n'
        (d/'prompt.txt').write_text(text,'utf8');write(d/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PSHA,'refs':refs,'layout':{'canvas':[1536,1024],'cell':[512,512],'native_cell':[64,64],'origin':[32,36],'crop':list(CROP),'scale':8},'anchors':anchors,'inputs':{p.name:sha(p.read_bytes())for p in(d/'edit_target.png',d/'accepted_style.png',d/'new_detail_reference.png')},'art_generated':False,'original_game_written':False})
    print(json.dumps({'pages':GROUPS,'new_body_keys':12,'sprites':24}))
if __name__=='__main__':main()
