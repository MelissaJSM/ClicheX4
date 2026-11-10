"""린 수용 기준안을 보호하며 생성된 호흡/눈감음의 연결 부위만 원래 그리드에 등록."""
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.extract_zero import save_image

PILOT=ROOT/'out/ver_rin_nana/rin_pilot_20261028T080902512874Z'
OUT=ROOT/'work/ver_rin_nana/idle_production/v1'
SEQUENCE=[0,146,147,148,0,146,147,148,0,1,2,1]
TICKS=[21,12,42,12,54,12,42,12,24,3,3,3]

def main():
    source=OUT/'generated_exhale_blink.png'
    words=struct.unpack('<16H',(PILOT/'candidate_palette.bin').read_bytes())
    master=np.array(Image.open(PILOT/'rin_idle147_indexed.png'))
    colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],np.int32)
    image=Image.open(source).convert('RGBA');full=np.array(image);yy,xx=np.nonzero(full[:,:,3]>=128)
    box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
    crop=image.crop(box);rgba=np.array(crop);nearest=np.zeros(rgba.shape[:2],np.uint8)
    for y in range(crop.height):
        nearest[y]=np.argmin(np.sum((rgba[y,:,:3].astype(np.int32)[:,None]-colors[None])**2,axis=2),axis=1)+1
    votes=[np.array(Image.fromarray(np.where(nearest==i,rgba[:,:,3],0).astype(np.uint8)).resize((42,47),Image.Resampling.BOX)) for i in range(1,16)]
    visible=np.array(crop.getchannel('A').resize((42,47),Image.Resampling.BOX))>=128
    normalized=np.zeros((48,56),np.uint8);normalized[1:48,6:48]=np.where(visible,np.argmax(np.stack(votes),axis=0)+1,0)
    save_image(normalized.tobytes(),(56,48),words,OUT/'generated_registered.png')
    # Registration locks the accepted head, torso, apron, and sole pixels.
    # The tiny knee strip is the only newly generated geometry admitted.
    low=master.copy();low[:35]=0;low[1:35]=master[:34]
    low[35:40]=normalized[35:40]
    # Long ribbon remains part of the same translating body, not the knee joint.
    low[34:39,39:]=master[33:38,39:]
    # Closed-eye sample is registered onto the original face; skin and hair stay fixed.
    blink=master.copy()
    blink[10:11,21:23]=normalized[12:13,20:22]
    frames={0:low,1:low,2:low,146:low,147:master,148:blink}
    if np.array_equal(master,blink):raise ValueError('Blink missing')
    for n,a in frames.items():
        if not np.array_equal(a[40:],master[40:]):raise ValueError('Sole anchor changed')
        if n in (0,1,2,146) and not np.array_equal(a[1:34],master[:33]):raise ValueError('Head/torso/waist split')
        save_image(a.tobytes(),(56,48),words,OUT/f'idle_{n:03}.png')
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    board=Image.new('RGB',(224*3,232),(34,37,48));draw=ImageDraw.Draw(board)
    for i,(n,label) in enumerate(((147,'수용 기준 자세'),(0,'호흡 · 몸통 함께 이동'),(148,'눈깜빡임'))):
        draw.text((224*i+6,5),label,fill='white',font=font)
        pic=Image.open(OUT/f'idle_{n:03}.png').convert('RGBA').resize((224,192),Image.Resampling.NEAREST);board.paste(pic,(224*i,32),pic)
    board.save(OUT/'idle_comparison_4x.png')
    for scale in (1,4):
        pictures=[Image.open(OUT/f'idle_{n:03}.png').resize((56*scale,48*scale),Image.Resampling.NEAREST) for n in SEQUENCE]
        pictures[0].save(OUT/f'idle_preview_{scale}x.gif',save_all=True,append_images=pictures[1:],duration=[round(t*100/60)*10 for t in TICKS],loop=0,transparency=0,disposal=2,optimize=False)
    record={'project':'ver_rin_nana','task':'zero_rin','scope':'idle_six_references','approved_master':str(PILOT.relative_to(ROOT)/'rin_idle147_indexed.png'),'master_sha256':digest(PILOT/'rin_idle147_indexed.png'),'imagegen_mode':'built_in_edit','generated_source_sha256':digest(source),'prompt':'prompt_exhale_blink.txt','registration':{'generated_crop':box,'logical_size':[42,47],'placement':[6,1],'protected_master_rows':'head through apron 0..33 translated down one; boots 40..47 unchanged','generated_joint_rows':[35,40],'blink_roi':[21,10,23,11]},'frame_sha256':{n:digest(OUT/f'idle_{n:03}.png') for n in frames},'palette_sha256':digest(PILOT/'candidate_palette.bin'),'sequence':SEQUENCE,'duration_ticks':TICKS,'preview_is_runtime_evidence':False}
    (OUT/'recipe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'output':str(OUT),'frame147_preserved':np.array_equal(master,frames[147]),'blink_changes':int(np.count_nonzero(master!=blink))}))

if __name__=='__main__':main()
