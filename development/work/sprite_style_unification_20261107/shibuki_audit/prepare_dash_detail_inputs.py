"""현재 대시의 실제 원점/원 제작 자료를 보존한 새 상세화 입력."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
P=H/'prepared_rising_right_base01/PL00_U.ARC'
PSHA='13a29023365419d32475cf5a6551adc4658116c8f03622d962d5b8071744e8b8'
O=H/'dash_detail_inputs01';B=ROOT/'work/ver_buki_riko/shibuki_art'
KEYS=(67,69,71);CROP=(128,124,192,188)
def main():
    global O,KEYS
    parser=argparse.ArgumentParser();parser.add_argument('--page',type=int,choices=(1,2,3,4),default=1);args=parser.parse_args();number=args.page
    KEYS={1:(67,69,71),2:(75,77,79),3:(81,83),4:(93,94)}[number];O=H/f'dash_detail_inputs{number:02}'
    need(not O.exists(),'Fresh output required');data=P.read_bytes();need(sha(data)==PSHA,'Wrong parent');a=Archive(data);O.mkdir()
    provenance=[]
    for n in (67,69,71,75,77,79,81,83):
        for shot in (False,True):
            p=B/'dash_v1/production08'/f'{"shoot" if shot else "run"}_{n:03}.png'
            q=np.zeros((384,384),np.uint8);q[120:200,112:208]=np.array(Image.open(p));ref=n+int(shot)
            need(np.array_equal(q,a.layer(ref)[0]),f'Base dash source differs: {ref}')
            provenance.append({'ref':ref,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'current_layer0_exact':True})
    poses=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1024));anchors=[]
    for row,(form,mask) in enumerate((('base',0),('fourth',15))):
        items=[]
        for col,n in enumerate(KEYS):
            im=a.composite(n,mask)[0];crop=im.crop(CROP);need(np.count_nonzero(np.array(crop)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Crop clips pose')
            poses.alpha_composite(crop.resize((512,512),Image.Resampling.NEAREST),(col*512,row*512));im.save(O/f'{form}_{n:03}.png')
            yy,xx=np.nonzero(np.array(im)[:,:,3]);anchors.append({'form':form,'ref':n,'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'foot_y_world':int(yy.max()-160)})
            items.append((f'{n} current dash',im))
        for col,n in enumerate((0,33,55)):
            im=a.composite(n,mask)[0];style.alpha_composite(im.crop(CROP).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
        page(items,a.composite(0,mask)[0],O/f'{form}_current.png',cols=3,scale=6)
    pose_name=f'page{number:02}_poses.png';poses.save(O/pose_name);style.save(O/'accepted_style.png')
    prompt='''Edit target page01_poses.png: repaint the same six compact Tenko Shibuki game sprites in the detailed approved pixel-art style in accepted_style.png. Preserve the exact action, facing left, two real arms, head/eye/neck position, compact leaning spine, bent knees, both original shoe contacts and each cell's full-body placement. This is ONE character with two existing costumes, not six unrelated characters. Transparent canvas1536x1024, three512x512 cells per row and two rows; each cell is a native64x64 window enlarged exactly8x, world origin at native32,36. Do not enlarge the figures to fill cells and do not lengthen limbs. Keep about23 native pixels of head/ears in upright equivalent and accepted short, full-bodied proportions. No whole-figure resizing.
Columns are67 beginning the forward crouch,69 leaning deeper,71 fully low running dash. Keep each different pose and its knee/foot placement. Both costume rows use precisely the same underlying skeleton/head scale. The three reference columns in accepted_style are idle, new airborne pose, new wall pose: use their contour clarity, layered locks and short garment-fold shading, not their poses.
Top row BASE costume: layered lavender fox ears and long hair; human gold eyes; red side flower/ribbon; white loose sleeves with light-blue shadows, red edges; red shrine dress/skirt and front cord; pale-lavender striped leg wraps and white/red footwear. Bottom row FOURTH costume: same character and face/hair, black/navy layered cape and dark dress with white fur at collar/edge, purple sleeves with gold trim, dark stockings and white/gold footwear. Show the black/purple sleeve material clearly, never substitute the pale-blue base sleeve in row2. Fully clothed in both rows, no new costume.
Replace old large flat lavender head patches and blank sleeve/torso masses with clean thin dark contours, 2-3 readable lavender middle-tone hair clusters, distinct ear interior, proper collar/cord/gold-edge and short sleeve folds. Preserve long flowing hair and actual costume silhouette. Detailed but not noisy strands, scribbles or thick black blobs. No animal muzzle, oversized head, fox tail, sunglasses (those belong only to her Ultimate costume), new jewelry, firearm, projectile, speed streaks, dust, platform, text, labels, grid or cast shadows. All six complete sprites remain separate in their exact cells. Truly transparent background.'''
    if number!=1:
        description={2:'Columns are75 a low dash with fist close to the chin,77 rising from the dash with the leading arm held low and palm open,79 a higher crouch with the leading fist near the chest.',3:'Columns are81 an upright landing/recovery stance with both legs spread and hands held down,83 a crouched recovery stance with one knee forward. The third column is entirely empty in both rows; render only FOUR poses.',4:'Columns are93 the airborne-dash entry with its exact bent legs and94 the next airborne-dash transition. These are TWO DIFFERENT BODY POSES, not firing pairs. The third column is entirely empty in both rows; render only FOUR poses.'}[number]
        prompt=prompt.replace('page01_poses.png',pose_name).replace('Columns are67 beginning the forward crouch,69 leaning deeper,71 fully low running dash.',description)
        if number>=3:prompt=prompt.replace('same six compact','same four compact').replace('All six complete sprites','All four complete sprites')
        prompt+='\nAdditional style continuity input generated_first_page.png shows the same character already repainted in the preceding67/69/71 dash poses. Keep its compact anatomy, layered hair, sleeve folds and costume treatment; do not copy its poses over these new action positions.'
    (O/'prompt.txt').write_text(prompt+'\n','utf8')
    sources=[O/pose_name,O/'accepted_style.png']
    if number!=1:
        prior=H/'dash_detail_inputs01/generated.png';need(sha(prior.read_bytes())=='390a5ff9080abd924ce2c9ccb161da0b28442602bfabff51be3fe4a5b00639fe','Changed preceding artwork');(O/'generated_first_page.png').write_bytes(prior.read_bytes());sources.append(O/'generated_first_page.png')
    write(O/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PSHA,'page_number':number,'first_page':list(KEYS),'forms':['base','fourth'],'layout':{'source':[1536,1024],'native_cell':[64,64],'crop':CROP,'scale':8},'anchors':anchors,'current_base16_matches_old_production':provenance,'old_palette_manifest':{'path':(B/'dash_v1/source_manifest.json').relative_to(ROOT).as_posix(),'sha256':sha((B/'dash_v1/source_manifest.json').read_bytes())},'source_images':{p.name:sha(p.read_bytes())for p in sources},'scope':f'대시 신규 두 의상 본체 페이지{number}: {KEYS}. 사격·73/74 속도선·나머지 동작은 별도 후속이다.','generation_started':False,'game_written':False})
    print(json.dumps({'out':str(O),'base_source_exact':len(provenance),'anchors':anchors}))
if __name__=='__main__':main()
