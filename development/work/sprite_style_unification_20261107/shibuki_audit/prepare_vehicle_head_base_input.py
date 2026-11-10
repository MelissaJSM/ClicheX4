"""기본/포스 작은머리 두 셀: 외곽/홍채/고유장식은 고정, 머릿결만 새 묘사."""
from pathlib import Path
import sys,json
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'vehicle_head_base_inputs01';need(not d.exists(),'입력 보호');d.mkdir();src=H/'vehicle_head_accessory_read01';canvas=Image.new('RGBA',(96,96));roles={}
    for form,x in (('base',14),('fourth',62)):
        head=Image.open(src/f'{form}_small184.png').convert('RGBA');need(head.size==(13,15),'머리 크기');canvas.alpha_composite(head,(x,38));roles[form]={'bbox_logical':[x,38,x+13,53],'eye':[x+6,50]}
    canvas.save(d/'target_native96.png');canvas.resize((1536,1536),Image.Resampling.NEAREST).save(d/'target_edit.png');style=Image.new('RGB',(720,640),'#e8e6df');dr=ImageDraw.Draw(style)
    for row,form in enumerate(('base','fourth')):
        im=Image.open(src/f'{form}_idle_head_crop.png').convert('RGBA').resize((408,300),Image.Resampling.NEAREST);style.paste(im,(10,row*320+18),im);dr.text((440,row*320+20),f'{form.upper()} accepted idle\nStyle reference only\nPreserve tiny target size\nNO forehead goggles',fill='#202020')
    style.save(d/'accepted_idle_style.png')
    prompt='''Use case: precise-object-edit. Asset: two tiny head-only game sprites of the SAME adult lavender-haired animal-eared character, in her base and Fourth forms.
Image 1 is the edit target: two small heads on one transparent square96x96 logical pixel canvas enlarged nearest-neighbor. Image 2 is style reference ONLY: upper base form, lower Fourth form. Edit the left small head using the upper reference; edit the right small head using the lower reference.
Improve only the broad flat lavender hair patch below the ears and above the eye, adding a few crisp dark-lavender strand clusters and pale highlights matching each accepted idle reference. Keep the tiny head silhouette, ear lengths and positions, left-facing face, golden eye, cheek and chin unchanged. Keep the pink side ornament of the left head and the distinctive dark-purple forehead/right-ear decoration of the right head. These forms DO NOT wear the Ultimate's gold forehead goggles: do NOT add goggles, a gold band or any new accessory.
Preserve the exact canvas composition. Left head bbox x14..26,y38..52 and eye x20,y50. Right head bbox x62..74,y38..52 and eye x68,y50. Each head stays exactly13logical pixels wide and15high; do not enlarge, shift or crop either one. Every original transparent pixel should stay transparent. No neck/body, no new object or extra face. The two heads must remain separate and equal size with the same blank space between them. Keep chunky limited-palette 1990s action-game pixel art, not smooth illustrations or realistic hair. Only improve interior hair shading; the original outline/eyes/accessories remain. Return this same square transparent canvas, two heads only, no labels, grids, backgrounds or shadows.'''
    (d/'prompt.txt').write_text(prompt,encoding='utf8');write(d/'input_manifest.json',{'scope':'기본/포스 작은머리2셀의 내부머릿결 편집. 고유장식/외곽/눈 보호.','logical_canvas':[96,96],'target_positions':roles,'source_parent':'prepared_nova_strike_base01/PL00_U.ARC','source_parent_sha256':sha((H/'prepared_nova_strike_base01/PL00_U.ARC').read_bytes()),'packing_parent_pending_root_hover':True,'sources':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in [src/'base_small184.png',src/'fourth_small184.png',src/'base_idle_head_crop.png',src/'fourth_idle_head_crop.png',Path(__file__)]},'files':{p.name:sha(p.read_bytes()) for p in d.iterdir() if p.is_file()},'generated':False,'resources_modified':False});print(json.dumps({'input':str(d),'manifest':sha((d/'input_manifest.json').read_bytes())}))
if __name__=='__main__':main()
