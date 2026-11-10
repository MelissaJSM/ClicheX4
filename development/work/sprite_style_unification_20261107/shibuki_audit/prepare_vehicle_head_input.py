"""13×15 탑승 머리 내부의 고글/머릿결 편집 입력. 실제 자원 변경 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'vehicle_head_ultimate_inputs01';need(not d.exists(),'입력 보호');d.mkdir();src=H/'vehicle_head_accessory_read01'
    head=Image.open(src/'ultimate_after_small184.png').convert('RGBA');need(head.size==(13,15),'현재 머리 크기')
    cell=Image.new('RGBA',(64,64));cell.alpha_composite(head,(25,22));cell.save(d/'target_native64.png');cell.resize((1024,1024),Image.Resampling.NEAREST).save(d/'target_edit.png')
    style=Image.new('RGB',(720,640),'#e8e6df');dr=ImageDraw.Draw(style)
    for i,form in enumerate(('ultimate_before','ultimate_after')):
        im=Image.open(src/f'{form}_idle_head_crop.png').convert('RGBA');up=im.resize((408,300),Image.Resampling.NEAREST);style.paste(up,(10,i*320+18),up);dr.text((440,i*320+20),f'{form}\nACCEPTED IDLE\nStyle reference ONLY\nKeep target tiny head size',fill='#202020')
    style.save(d/'accepted_idle_style.png')
    prompt='''Use case: precise-object-edit. Asset: one tiny head-only pixel sprite for a PlayStation-era action game.
Image 1 is the EDIT TARGET: a single lavender-haired animal-eared adult character head on a transparent 64 by 64 logical pixel canvas, enlarged nearest-neighbor to 1024 by 1024. Image 2 is STYLE REFERENCE ONLY showing this same character's accepted full-size heads. Do not copy the reference layout or its larger head proportions.
Edit only the interior shading and small forehead accessory of the target head. Add the recognizable compact gold-framed goggles pushed up on the forehead, as shown in reference image 2, leaving the golden eye below unobscured. Clarify two or three tiny hair strand/shadow clusters inside the broad light-lavender forehead patch. Keep the current face looking left, the eye and cheek pixels at the same place, both pointed ears, purple side/back hair, black outlines, and the entire existing head silhouette and size.
The target head occupies logical x25 through37 and y22 through36, width13 and height15, with the golden eye at x31,y34. Keep these exact placement and scale constraints; do not enlarge, crop, shift, extend the ears or add neck/body. The head must still be a tiny 13x15 sprite, not a portrait. Use chunky crisp nearest-neighbor pixel clusters with the existing limited lavender/dark purple/peach/gold palette. The gold goggles must read as a small forehead accessory above the eye, not an extra eye or a helmet. Preserve all blank canvas around the head. Transparent background; one head only; no labels, grids, shadows, other characters or frames.'''
    (d/'prompt.txt').write_text(prompt,encoding='utf8')
    write(d/'input_manifest.json',{'scope':'Ultimate 탑승 작은 머리 한 셀의 내부 장식/머릿결 새 편집 입력. 전후 측면색 소유는 후속 등록.','parent_arc':'prepared_hover_ultimate01/PL02_U.ARC','parent_sha256':sha((H/'prepared_hover_ultimate01/PL02_U.ARC').read_bytes()),'target_ref':184,'logical_canvas':[64,64],'native_head_bbox':[25,22,38,37],'eye':[31,34],'world_bbox':[-10,-37,3,-22],'whole_canvas_registration':True,'body_scale_change':False,'input_roles':{'target_edit.png':'편집 대상.13x15 머리의 원점/실루엣 보호.','accepted_idle_style.png':'고글/머릿결 설정 참고.크기/배치 복사 금지.'},'sources':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in [src/'ultimate_after_small184.png',src/'ultimate_before_idle_head_crop.png',src/'ultimate_after_idle_head_crop.png',src/'report.json',src/'conclusions.json',Path(__file__)]},'files':{p.name:sha(p.read_bytes()) for p in d.iterdir() if p.is_file()},'generated':False,'game_resources_modified':False})
    print(json.dumps({'input':str(d),'manifest_sha256':sha((d/'input_manifest.json').read_bytes())}))
if __name__=='__main__':main()
