"""손실 없는 등록에서 발견된 두 자세를 별도 원화 편집으로 보정한다."""
import json,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/ver_rin_nana/style_revision/v3'

def main():
    batches=json.loads((OUT/'batches.json').read_text())
    for group,n,batch in [('run',17,4),('ground',97,2)]:
        folder=OUT/group;slots=[None,n];template=Image.new('RGBA',(160,80))
        idle=Image.open(OUT/'master_preview_147.png').convert('RGBA')
        pose=Image.open(folder/f'prepared_{n:03d}.png').convert('RGBA')
        template.alpha_composite(idle,(16,16));template.alpha_composite(pose,(90,16))
        target=folder/f'template_{batch}.png';template.resize((1280,640),Image.Resampling.NEAREST).save(target)
        prompt=f'''Edit this two-cell sprite sheet. First idle on left is a calibration and MUST remain exactly unchanged, including size. Second Rin sprite on right needs a LOCAL silhouette correction. Keep the SAME slender character, SAME detailed angular pixel rendering, SAME exact head size, SAME body/leg pose and all hair, face, clothing and glove details. Only change the long blue/white rear ribbon: curve it tightly downward close behind the character's back instead of sweeping far to the right. Its rightmost tip must end immediately behind the rear elbow, its bottom no lower than her waist. The character torso, head and legs must NOT be scaled down. Preserve the ribbon's connected root and white stripe. Only curve this loose fabric into a more compact silhouette. The fists should stay small and angular. Maintain two equal cells in one row, character pixels48 high for standing, transparent background, no labels/effects. Actual target frame {n} of {group}. Preserve the thin navy contours and gray-blue pixel shading.'''
        promptpath=folder/f'prompt_{batch}.txt';promptpath.write_text(prompt+'\n','utf-8')
        meta={'id':f'{group}_{batch}','group':group,'batch':batch,'slots':slots,'columns':2,'rows':1,'template':str(target),'poses':str(target),'prompt':str(promptpath),'output':str(folder/f'generated_{batch}.png')}
        batches=[b for b in batches if b['id']!=meta['id']];batches.append(meta)
    (OUT/'batches.json').write_text(json.dumps(batches,indent=2)+'\n','utf-8')
if __name__=='__main__':main()
