"""새 Fourth217의 부츠 재질만 고치는 별개 국소 원화 입력."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive

def main():
    d=H/'nova_strike_boot_inputs01';need(not d.exists(),'새 입력');d.mkdir();src=H/'nova_strike_base_native01/fourth_217.png';a=Archive((H/'prepared_nova_base01/PL00_U.ARC').read_bytes());target=Image.open(src).convert('RGBA').crop((96,96,224,224)).resize((1024,1024),Image.Resampling.NEAREST);style=Image.new('RGBA',(1024,1024))
    for i,n in enumerate((0,71,215,205)):
        im=a.composite(n,15)[0].crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST);style.alpha_composite(im,((i%2)*512,(i//2)*512))
    prompt='''Edit Image1, a single refined lavender-haired fox-eared character flying horizontally to the LEFT, on exactly1024x1024 transparent canvas. The entire canvas is128x128 logical pixels at8x and its origin is(64,64). This is a small local COSTUME MATERIAL correction only.
Keep all existing new head, hair strands, dark/gold hair accessory, face, eyes, both fists, sleeves, bodice, skirt, waist tassels, pose, anatomy and transparent margins pixel-aligned and unchanged. Preserve every knee, ankle, toe tip and outer leg/foot silhouette at its exact current location. Do not extend, shorten, bend, enlarge, move, reshape or remove any limb.
Only fix the boots at the viewer's RIGHT end of the horizontal body: their large white/lavender and red areas incorrectly repeat the base costume. Redraw those exact boot surfaces with the accepted Fourth outfit's DARK black-purple boot material, purple shaded folds and small gold/cream toe trim, matching Image2. Keep the boots compact and the same size. Avoid a large white boot shaft, red heel or red sole. Small controlled pale toe highlight is allowed as in the reference; the main boot is dark. Preserve the original separation and overlap of the two legs. Keep the lavender braid/hair above the legs untouched, and keep any exposed skin at the thigh unchanged.
Image2 contains accepted Fourth idle, dash, preparation and victory details for BOOT MATERIAL ONLY. Do not copy their poses or change the target's airborne legs. Clean restrained console pixel clusters with2-3tones. No aura, glow, halo, ground shadow, text, grid, labels or new object. True transparent background. Return one complete character in the same position, with only the boot material corrected.'''
    target.save(d/'edit_target.png');style.save(d/'accepted_boots.png');(d/'prompt.txt').write_text(prompt,'utf8');write(d/'input.json',{'source':{'path':src.relative_to(ROOT).as_posix(),'sha256':sha(src.read_bytes())},'parent_sha256':sha(a.data),'layout':{'canvas':[1024,1024],'logical_canvas':[128,128],'origin':[64,64],'crop':[96,96,224,224]},'policy':'기존 새217 전신 보존. 포스 부츠 표면만 국소 donor로 사용하며 몸체 전체 치환 금지.','files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}});print(d)
if __name__=='__main__':main()
