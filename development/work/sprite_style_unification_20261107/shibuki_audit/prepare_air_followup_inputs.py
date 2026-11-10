"""남은 공중 새 원화 입력. 원본 프레임의 전체 위치·팔·발을 그대로 보여준다."""
from pathlib import Path
import argparse,sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,choices=(2,3,4),required=True);args=ap.parse_args()
    refs={2:(37,41,43),3:(45,47,49),4:(51,53)}[args.page];O=H/f'air_detail_inputs{args.page:02}';need(not O.exists(),'Fresh output required')
    P=H/'prepared_arrival_victory01/PL00_U.ARC';data=P.read_bytes();need(sha(data)=='78b329a07d888682c24b440386cb365f826572402346b3ee6620216ce951617e','Wrong parent')
    a=Archive(data);O.mkdir();cols=len(refs);sheet=Image.new('RGBA',(512*cols,1024));rows=[];crop=(128,124,192,188)
    for row,(form,mask)in enumerate((('base',0),('fourth',15))):
        for col,n in enumerate(refs):
            im=a.composite(n,mask)[0];cut=im.crop(crop);need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Pose clipped')
            sheet.alpha_composite(cut.resize((512,512),Image.Resampling.NEAREST),(col*512,row*512));yy,xx=np.nonzero(np.array(im)[:,:,3])
            rows.append({'form':form,'ref':n,'cell':[col,row],'foot_y_world':int(yy.max()-160),'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)]})
    sheet.save(O/'poses.png')
    prompt=f'''Use case: style-transfer. Edit target=image1, earlier accepted new air artwork=image2, accepted idle/wall/victory identity and proportion reference=image3. Repaint only the {cols*2} fully clothed Tenko Shibuki sprites of image1 into image2's fine pixel-art detail, staying consistent with image3. Keep the transparent {512*cols}x1024 canvas, {cols} columns of512x512 cells and2 rows. Each cell is a64x64 native window at8x with world origin(32,36). Exact input actions and facing direction must remain: references{refs}, including original eye/neck positions, raised or lowered hands, bent knees and boot-bottom locations. No figure bbox normalization, stretched body, shifted ankles or altered limb angles.
Top row BASE: lavender fox ears and layered long hair, human face/golden eyes, red flower/ribbon ornament, white loose sleeves with light-blue folds and red trim, red shrine skirt/front cord, pale-lavender striped leg wraps, white/red boots. Bottom FOURTH: same skeleton/head/face/hair, navy-black layered cape with white fur edge, purple sleeves/gold trim, dark dress/gold edging, dark stockings, white/gold boots. All skin contacts and joints align between costume rows. Use accepted compact short limbs/torso and approx23-native-pixel head with ears. No mechanical armor, animal muzzle, added large fox tail, new ornaments, sunglasses, bare midriff, buster or projectile.
The intended change is detailed layered hair locks/controlled midtone shading, readable collar/cord/short sleeve folds/cloth layers and separate boots, replacing the old flat blob shapes. Hair remains long and flowing, not dense curled scratches. Thin clean contour and compact pixel clusters. Do not copy old coarse heads back over new detail. Keep all sprites complete within their original cells, original common scale and transparent margins. No backgrounds, matte, labels, gridlines, shadows, platforms or extra poses.'''
    (O/'prompt.txt').write_text(prompt+'\n','utf8')
    write(O/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':sha(data),'page':args.page,'refs':list(refs),
                             'forms':['base','fourth'],'layout':{'source':[512*cols,1024],'native_cell':[64,64],'cols':cols,'rows':2,'crop':list(crop),'scale':8},
                             'anchors':rows,'source_images':{str(O/'poses.png'):sha((O/'poses.png').read_bytes())},'generation_started':False,'game_written':False})
    print({'path':str(O),'refs':refs})
if __name__=='__main__':main()
