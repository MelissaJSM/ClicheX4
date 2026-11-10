"""피격233/234 양 의상을 현재 원점과 새106/110의 세부 기준으로 준비한다."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics

def main():
    d=H/'hurt_inputs01/page02';need(not d.exists(),'Fresh input');d.mkdir()
    p=H/'prepared_base_run01/PL00_U.ARC';need(sha(p.read_bytes())=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce','Parent changed')
    a=Archive(p.read_bytes());board=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1024));rows=[];style_paths=[]
    for row,(form,mask) in enumerate([('base',0),('fourth',15)]):
        for col,n in enumerate((233,234)):
            im=a.composite(n,mask)[0];cut=im.crop((112,128,208,192));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Source cropped')
            board.alpha_composite(cut.resize((768,512),Image.Resampling.NEAREST),(col*768,row*512));im.save(d/f'{form}_{n:03}_current.png')
            rows.append({'form':form,'ref':n,'metrics':metrics(im),'source_rgba_sha256':sha(im.tobytes())})
        ims=[a.composite(0,mask)[0]]
        for n in (106,110):
            sp=H/'hurt_native01'/f'{form}_{n:03}.png';ims.append(Image.open(sp).convert('RGBA'));style_paths.append({'path':sp.relative_to(ROOT).as_posix(),'sha256':sha(sp.read_bytes())})
        for col,im in enumerate(ims):style.alpha_composite(im.crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
    board.save(d/'pose_reference.png');style.save(d/'accepted_style_reference.png')
    prompt='''Use case: stylized-concept. Production PIXEL SPRITE art, exact1536x1024 true transparent page, TWO columns by TWO rows. Each768x512 cell represents a native96x64 sprite window at exact8x enlarged pixel scale, native origin(48,32). Exactly FOUR complete figures of the SAME compact fox-girl Shibuki, fully clothed.
Image1 is ONLY the POSE and POSITION guide. TOP LEFT233: body leans back while the forward knee/boot is lifted high toward the left, right leg hangs lower, face in three-quarter side view, arms protecting the body. TOP RIGHT234: tightly bent protective hurt/recoil, torso folds toward screen left, forward sleeve raised near the chin, bent knees/boots at their exact existing positions. BOTTOM row repeats exactly the same respective skeleton in Fourth clothes. Keep each pose's facing, head center/tilt, ear endpoints, wrist/finger endpoints, shoulder, hips, bent knees and ankle/boot endpoints at the same cell coordinates. Keep the full occupied height and compact volumes. Do not straighten them into standing or running. Do not shift or resize a whole figure to fill the page. Precisely two arms and two legs, no extra hands.
Image2 defines quality/identity: TOP row accepted BASE idle and newly detailed106/110 hurt; BOTTOM accepted FOURTH idle and its corresponding new hurt sprites. Keep the compact short torso/limbs, rounded sleeve/thigh volume and head including ears about38% of the neutral idle height. Match the new intentional lavender hair locks and shadow clusters, fox ears with interior detail, pained readable face, layered collar/cuffs, short skirt/coattails, boot seams and clear consistent outline. Preserve the original pose even where new details differ. No old flat giant hair area, random black hatching, thin stick legs, stretched adult proportions, or blurry gradients.
TOP BASE outfit: white/light-blue broad folded sleeves, red bodice/collar and short red skirt, dark borders, red hair ribbon, lavender/red boots exactly from the style row. BOTTOM FOURTH outfit: dark black/deep-purple bodice and skirt/coattails, folded lavender sleeves, gold clasp/trim, dark purple boots with lavender/gold edges and its accepted gold head ornament. Fourth must not inherit the basic red bodice or broad white base sleeves. Both clothes share the same actual head/joints/feet per pose while retaining their own cloth volume and details.
Output only the four sprites at the original fixed cell positions on genuine transparency. Deliberate crisp8x pixel blocks, coherent clusters. No labels, text, ground, shadows behind the figure, purple glow, halo, lightning, particles, silhouettes, weapon, palette swatches or extra poses. The original game effects are separate assets and must not be painted into these bodies.'''
    (d/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    write(d/'input.json',{'parent':p.relative_to(ROOT).as_posix(),'parent_sha256':sha(p.read_bytes()),'rows':rows,'source_layout':{'size':[1536,1024],'cell':[768,512],'native_cell':[96,64],'native_origin':[48,32],'scale':0.125,'crop':[112,128,208,192]},'style_inputs':style_paths,'style_refs':[0,106,110],'source_art_generated':False,'arc_changed':False,'note':'현재233/234의 동작은 유지하고 수용 대기 및 새106/110의 디테일을 적용하는 새 원화 입력이다. 원효과는 포함하지 않는다.'})
    print(d.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
