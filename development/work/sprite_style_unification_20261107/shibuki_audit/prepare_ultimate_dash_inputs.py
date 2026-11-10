"""새 대시 관절을 유지하는 얼티밋 의상 전후 입력. 게임/동결본 변경 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
B=H/'prepared_dash_base01/PL00_U.ARC';U=H/'prepared_ultimate_air01/PL02_U.ARC'
BS='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b';US='3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7'
PAGES=((67,69,71),(75,77,79),(81,83),(93,94));CROP=(128,124,192,188)
def cell(im):
    cropped=im.crop(CROP);need(np.count_nonzero(np.array(cropped)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Input crop clips art');return cropped.resize((512,512),Image.Resampling.NEAREST)
def main():
    o=H/'ultimate_dash_inputs01';need(not o.exists(),'Fresh input folder');need(sha(B.read_bytes())==BS and sha(U.read_bytes())==US,'Source hash changed');b=Archive(B.read_bytes());a=Archive(U.read_bytes());o.mkdir();style=Image.new('RGBA',(1536,1024));rows=[]
    for row,mask in enumerate((15,0)):
        for col,n in enumerate((0,13,33)):style.alpha_composite(cell(a.composite(n,mask)[0]),(col*512,row*512))
    style.save(o/'accepted_ultimate_style.png')
    for pn,refs in enumerate(PAGES,1):
        d=o/f'page{pn:02}';d.mkdir();poses=Image.new('RGBA',(1536,1024));old=poses.copy()
        for row,mask in enumerate((15,0)):
            for col,n in enumerate(refs):
                new=b.composite(n,0)[0];prev=a.composite(n,mask)[0];poses.alpha_composite(cell(new),(col*512,row*512));old.alpha_composite(cell(prev),(col*512,row*512));rows.append({'page':pn,'ref':n,'form':'before'if mask else'after','new_pose_reference':metrics(new),'current_ultimate':metrics(prev)})
        poses.save(d/'new_pose_reference.png');old.save(d/'current_ultimate_reference.png')
        prompt=f'''Edit the provided new_pose_reference.png into Tenko Shibuki's two already accepted Ultimate costumes. This is a COSTUME edit retaining the EXACT new detailed dash pose, compact proportions, facing left, head angle, shoulder/hip angle, bent knees, hand placement and both foot contacts. The first image provides the pose and refined pixel detail. The second image accepted_ultimate_style.png supplies the actual face, gold heart sunglasses, hair ornament, white/navy jacket and white sleeveless swimsuit. The third current_ultimate_reference.png explains the old coordinate only: do not copy its flat coarse head or old clothing blocks.
Transparent1536x1024, three512x512 cells across and two rows. Each is a64x64 native viewport enlarged8x, world origin(32,36), crop(-32,-36..32,28). Columns are refs {','.join(map(str,refs))}. Keep sprite content at EXACTLY the first image's scale and positions; do not fill the empty margins by scaling up. Accepted compact head including fox ears roughly23 native pixels upright equivalent; short substantial torso/limbs, no long thin legs. Preserve the different leaning/crouching action of each column, do not stand them up.
Top row BEFORE acquisition: short loose WHITE outer jacket over a short white sailor swimsuit/dress, NAVY collar and trim, small gold accents, proper lavender fold shading. Readable short full sleeves and cuffs. Bottom row AFTER acquisition: identical face/hair/body/legs at the same coordinates, short WHITE sailor swimsuit with NAVY collar, remove outer jacket and ALL sleeve fabric to reveal BARE ARMS. The two rows are the same body and same pose. Keep pale bare legs and small white/pink sandals in both rows; do not retain base-form leg wraps, socks or red shrine shoes.
All figures keep lavender fox ears, human golden eyes, layered long lavender hair with coherent midtone strands, dark navy flower ornament and GOLD HEART-SHAPED SUNGLASSES perched above the eyes. No fox muzzle or tail. Make collar seams, tiny gold accents, cuff folds, hair locks and ear interiors as clear as accepted idle and accepted new air art, without scribbly excess strands or harsh black masses. No red shrine skirt, red hair flowers, light-blue shrine sleeves or Fourth armor cape. Do not recolor the old flat art; actually interpret the new compact detailed pose in the accepted Ultimate clothes.
Exactly TWO arms per figure, hands stay at their first-image positions. No additional fist behind the head, no extra arm, gun, barrel, projectile, speed streak, dust, floor, text, grid or shadow. Both costumes must share identical new head, eyes, hands, legs and sandals; only jacket-covered torso and forearms change. Transparent blank margins.'''
        if len(refs)==2:prompt+=' The third column stays completely transparent in both rows; only FOUR complete figures.'
        (d/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    write(o/'manifest.json',{'base_pose':{'path':B.relative_to(ROOT).as_posix(),'sha256':BS},'ultimate_parent':{'path':U.relative_to(ROOT).as_posix(),'sha256':US},'layout':{'canvas':[1536,1024],'native_cell':[64,64],'scale':8,'crop':CROP},'pages':[list(r)for r in PAGES],'rows':rows,'accepted_style_refs':[0,13,33],'accepted_idle_changed':False,'old_ultimate_body_used_as_art':False,'generated':False,'game_modified':False})
    print(json.dumps({'path':str(o),'pages':len(PAGES),'body_keys':10}))
if __name__=='__main__':main()
