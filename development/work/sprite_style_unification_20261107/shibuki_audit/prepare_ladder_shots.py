"""새 사다리 몸체와 원 총구를 발사팔 국소 편집 입력으로 조립한다."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent
ROOT=H.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--body',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();body=args.body.resolve();out=args.output.resolve()
    need(body.is_relative_to(H) and out.is_relative_to(H),'Outside own work area')
    need(not out.exists(),'Output already exists')
    raw=(H/'prepared_wall_front01/PL00_U.ARC').read_bytes()
    need(sha(raw)=='db508292c2746b5c4a12e60e9cf28f5ebe558e7998788c3d1d5440a4f8fd481a','Wall checkpoint changed')
    a=Archive(raw);out.mkdir()
    board=Image.new('RGBA',(1024,1024));guide=Image.new('RGBA',board.size);draw=ImageDraw.Draw(guide);records=[]
    rects={150:(-25,-12,-15,-4),155:(-22,-16,-12,-8)}
    for row,(name,mask) in enumerate((('base',0),('fourth',15))):
        for col,ref in enumerate((150,155)):
            im=Image.open(body/f'{name}_149.png').convert('RGBA')
            current=a.composite(ref,mask)[0]
            x0,y0,x1,y1=rects[ref]
            barrel=current.crop((160+x0,160+y0,160+x1,160+y1))
            need(sha(barrel.tobytes())=='c35050bae24e7317eaff978c6ed4c8f4c31c437bc6c5856baf0eaa58c6f9ea87','Barrel identity changed')
            im.alpha_composite(barrel,(160+x0,160+y0))
            im.save(out/f'{name}_{ref:03}_target.png')
            cell=im.crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST)
            board.alpha_composite(cell,(512*col,512*row));guide.alpha_composite(cell,(512*col,512*row))
            # This green guide is never used as game artwork.
            points=[(x1,y0-1),(-5,-10),(-2,-1),(-6,5),(x1-1,y1+2)]
            draw.line([(512*col+(x+32)*8,512*row+(y+32)*8) for x,y in points+[points[0]]],fill=(0,255,128,255),width=3)
            records.append({'ref':ref,'form':name,'body_ref':149,'body_source':(body/f'{name}_149.png').relative_to(ROOT).as_posix(),'barrel_world_exclusive':list(rects[ref]),'barrel_rgba_sha256':sha(barrel.tobytes()),'barrel_opaque':int(np.count_nonzero(np.array(barrel)[:,:,3])),'arm_edit_pending':True})
    board.save(out/'page.png');guide.save(out/'guide.png')
    write(out/'inputs.json',{'records':records,'native_crop':[-32,-32,32,32],'scale':8,'input_is_composition_not_finished_arm':True,'new_body_only':True,'old_barrel_only_reused':True,'not_ready_to_pack':True})
    prompt='''Edit the FIRST transparent sprite sheet in place, exactly 1024x1024, two columns by two rows of 512x512 cells. Top row is the pale-blue/red shrine outfit, bottom row is the black-purple/gold Fourth outfit. Every sprite is the SAME newly detailed side-facing ladder-climbing body, with one rear arm raised to grip the ladder. The only unfinished part is the FRONT firing arm that connects the torso to the small existing barrel floating to the LEFT. The second image is only a green boundary GUIDE, not artwork; never reproduce its green lines.

Preserve the exact new head, ears, hair strands, gold eye, raised rear hand and arm, torso, waist, legs, feet, tail and all clothing outside the front firing arm. Do not resize or move any sprite. Preserve the small barrel's exact shape, size and pixel position. Source represents native64x64 per cell enlarged8 times, origin(32,32).

Column1, firing150: barrel occupies world x=-25..-16, y=-12..-5. Column2, firing155: barrel occupies x=-22..-13, y=-16..-9 and recoils slightly upward/right. Both barrels are identical short pieces. Draw a compact front upper-arm and naturally bent elbow from the shoulder around world(-6,-5) into the RIGHT edge of each barrel. Replace the old tucked front fist and bent sleeve with this shooting arm; never leave a second extra front hand. The raised rear gripping arm remains exactly unchanged. The front arm should have believable short joints and the same total compact limb proportion as the reference, no long rectangular sleeve tube, no detached elbow, no black empty gap, and no inflated fist. Do not solve reach by enlarging the gun or stretching the whole arm horizontally.

Top-row arm: broad but short white/pale-blue shrine sleeve, readable middle-blue folds, small red stitched trim, compact blue-violet underfold and a small attached hand inside/behind the barrel. Bottom-row arm: matching short purple sleeve with dark cuff and restrained gold edge, no leftover white shrine sleeve. Both costumes have the same anatomical elbow/wrist/contact geometry. Use clean one-native-pixel violet outlines, a few broad light/middle/shadow clusters and the existing native palette appearance. No new background, ladder, text, grid, markers or glow. Transparent background. All pixels outside the small front arm region remain unchanged.'''
    (out/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    print(out)

if __name__=='__main__':main()
