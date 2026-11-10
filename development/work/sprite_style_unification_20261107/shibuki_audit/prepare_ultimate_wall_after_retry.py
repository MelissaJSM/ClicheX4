"""양폼의 손발 불일치를 제거하는 의상 편집 입력. 생성 호출은 하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,write,need
I=H/'ultimate_wall_inputs01';N=H/'ultimate_wall_native01';O=H/'ultimate_wall_after_retry01'
def main():
    need(not O.exists(),'Fresh output required');O.mkdir()
    sheet=Image.new('RGBA',(1536,512));locked=Image.new('RGBA',(1536,512))
    specs=[]
    for i,n in enumerate((55,57,59)):
        im=Image.open(N/'before'/f'{n:03}.png').convert('RGBA');crop=im.crop((128,120,192,184));sheet.alpha_composite(crop.resize((512,512),Image.Resampling.NEAREST),(i*512,0))
        q=np.array(crop);mask=np.zeros((64,64),bool)
        # 명시된 잠금은 머리와 하체의 참고용이다. 새 torso 영역을 삭제/보간하지 않는다.
        mask[:34]=True;mask[47:]=True
        if n==59:mask[:35,41:]=False
        q[~mask]=0;locked.alpha_composite(Image.fromarray(q).resize((512,512),Image.Resampling.NEAREST),(i*512,0))
        specs.append({'ref':n,'body_source':str((N/'before'/f'{n:03}_indices.png').relative_to(ROOT)),'body_source_sha256':sha((N/'before'/f'{n:03}_indices.png').read_bytes()),'not_art_mask_for_packing':True})
    sheet.save(O/'edit_target.png');locked.save(O/'locked_head_legs_reference.png')
    prompt='''Edit ONLY the clothing and sleeves of edit_target.png, a three-cell native sprite plate of Tenko Shibuki. Each cell512x512 represents EXACTLY64x64 native pixels; canvas1536x512. The first image is the strict pose/scale/layout and pixel-detail target, not a loose illustration reference. The second locked-head-and-legs guide marks the new character areas which must remain unchanged. The third image, the previous AFTER attempt, is clothing-detail inspiration ONLY: do NOT copy its larger head, shifted shoulders, changed arms or overall proportions.

For ALL THREE cells retain the target sprite's exact top of head, neck socket, left/right shoulder, elbow, exposed fists/palms, knees and both sandal soles. The rightmost pose has a raised diagonal arm; its palm must stay at the target location, not above/right/left. Do not enlarge or redraw head/ears/face/glasses/hair/tail/legs. Do not move or resize the entire figure, stretch the torso or straighten curled knees. The original silhouette of the white jacket is the maximum allowed outer envelope; the AFTER body and bare arms must fit inside it. All transparent space outside that silhouette stays transparent.

Replace the white/navy outer jacket and long sleeves with the same character's sleeveless one-piece white/light-lavender sailor swim-dress: dark navy sailor collar, pink neck ribbon, covered chest and midriff, short flared skirt hem, subtle seam and folds. The garment must be a connected ONE PIECE, no exposed midriff, no bikini, no shorts. Elbows/forearms are bare, with natural thickness between the exact same shoulders and exposed fists; remove fabric cuffs entirely. Keep short compact body and original hairstyle detail; do not simplify the current native hair clusters into flat shapes. Use clean game-pixel clusters and the accepted palette, no extra tiny scratch texture. Body garment may change inside the jacket, but preserve the fixed head/limbs faithfully.

Output only the three same-position AFTER sprites on true transparent background, same canvas and same cell placement. No captions, grid, outlines around cells, new poses, shadows, ground or reference examples.'''
    (O/'prompt.txt').write_text(prompt+'\n','utf8')
    write(O/'inputs.json',{'kind':'의상과 팔만 재편집; 새 before 머리/다리 고정','refs':specs,'generated':False,'sources':{str(p.relative_to(ROOT)):sha(p.read_bytes())for p in[O/'edit_target.png',O/'locked_head_legs_reference.png',I/'page01_generated_after.png']},'reason':'첫 after 원화는 공통 접지 정렬 후 머리 높이와 팔 위치까지 달라 단순 평행이동만으로 정합할 수 없다. 원화 좌표를 강제 축소하거나 옛 머리로 덮지 않는다.','game_written':False,'packing_started':False})
    print(str(O))
if __name__=='__main__':main()
