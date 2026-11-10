"""승인 대기와 현재 저체력 원점만 모은 신규 생성 입력. 그림을 생성/변경하지 않는다."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from native_pose_pack import SOURCE,SOURCE_SHA,need,sha,write
from src.psx_disc import file_hash

def plate(a,n):
 out=Image.new('RGBA',(1536,1024))
 for col,mask in enumerate((0,15)):
  # 96x128 native viewport. Integer enlargement only; each character keeps world origin.
  crop=a.composite(n,mask)[0].crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST)
  out.alpha_composite(crop,(col*768,0))
 return out

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');raw=read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'];a=Archive(raw)
 out=H/'lowhp_generation01';out.mkdir(exist_ok=True)
 plate(a,0).save(out/'idle_reference.png');plate(a,120).save(out/'pose_reference.png')
 prompt='''Create exactly TWO revised pixel-art sprites of the SAME adult fox-girl character Tenko Shibuki, side by side on a transparent 1536x1024 canvas. The LEFT is her base red-and-white outfit; RIGHT is her black-and-purple Fourth Armor cape outfit. This is a two-pose sprite sheet, not a portrait or scene.
Use idle_reference.png as the exact accepted pixel-art quality/identity reference: detailed lavender hair strands, human anime face rather than animal muzzle, fox ears, floral side ornaments, precise eyes and facial boundary, structured clothing seams, crisp restrained one-native-pixel outline, no large featureless hair/cloth blobs. Use pose_reference.png ONLY for the low-health pose, world size, direction, and foot locations. Preserve a tired hand-near-chest pose with lowered shoulders and a slight head tilt; it must not become an attack or upright victory pose. Improve the whole figure including head and clothing to match the accepted idle's detail, without merely pasting the idle head over a different angle.
The provided character concept images define garment identity. LEFT: white wide sleeves, red inner dress with detailed ribbon/pleat structure, white patterned boots. RIGHT: deep navy/purple short cape, soft white fur collar and cuffs, black skirt with gold trim, dark stockings and pale boots. IMPORTANT: Fourth's chest is BLACK/DARK PURPLE, NOT a large red bodice or red lacing. Only a SMALL RED tassel/ornament may hang beside the waist. Keep the cape; do not substitute a swimsuit or jacket.
Maintain the exact 2-column layout of pose_reference.png: each cell is768x1024; the apparent sprite is around47 native pixels tall displayed at8x (about376px), with substantial transparent margin. Keep the feet at the same positions in each cell, and keep the accepted idle body size. Do not stretch the figure to fill the cell. Use authentic low-resolution pixel clusters visibly enlarged by integer factor8, no smooth illustration, gradients, blur, antialiasing, noise, text, labels, backdrop, watermark, or extra figures. Each pose must be complete and unclipped. The mouth is a quiet tired/closed-mouth expression; later blink/breath frames are registered separately. Do not duplicate the current simplified hair/torso: restore the detailed visual density of idle_reference throughout.
'''
 (out/'prompt.txt').write_text(prompt,'utf8')
 write(out/'inputs.json',{'source_bin_sha256':SOURCE_SHA,'source_arc_sha256':sha(raw),'canvas':[1536,1024],'columns':2,'native_viewport':[112,96,208,224],'integer_display_scale':8,'target_refs':[120],'reference_refs':[0,120],'body_foot_world':[1,22],'forms':['base','fourth'],'sources':[{'path':(out/name).relative_to(ROOT).as_posix(),'sha256':sha((out/name).read_bytes())}for name in('idle_reference.png','pose_reference.png')],'concepts':['character/ver_buki_riko/buki(X).webp','character/ver_buki_riko/buki(4th armor).webp'],'generation_started':False,'queue':'Nana arm -> Rin stride -> Riko cloth -> Shibuki lowHP; root permission slot required'})
 print(out)
if __name__=='__main__':main()
