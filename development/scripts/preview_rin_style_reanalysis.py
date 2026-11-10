"""대기 기준점으로 샘플을 팔레트 변환하고 같은 배율의 비교표를 만든다."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.extract_zero import save_image
from scripts.project import digest

def main():
    p=ROOT/'work/ver_rin_nana/style_revision/v2'
    source=p/'generated_stride.png';master=ROOT/'work/ver_rin_nana/style_revision/v1/master_preview_147.png'
    m=json.loads((master.parent/'master.json').read_text('utf-8'))
    if digest(master)!=m['master_sha256']:raise ValueError('Frozen idle changed')
    words=m['palette_words'];colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    im=Image.open(source).convert('RGBA');a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=128,255,0);im=Image.fromarray(a);im=im.crop(im.getbbox());a=np.array(im);rgb=a[:,:,:3].astype(int)
    mask=(a[:,:,3]>0)&(rgb[:,:,0]<100)&(rgb[:,:,1]>120)&(rgb[:,:,2]>140);mask[im.height//3:]=False
    q=connected_groups(mask)[0];eye=q.mean(axis=0);scale=10/eye[0]
    px=quantize(im,colors,scale);save_image(px.tobytes(),(px.shape[1],px.shape[0]),words,p/'stride_indexed.png')
    items=[('현재 대기 · 고정',master),('거절된 이동',master.parent/'assembled/bank0_007.png'),('새 질감 샘플 · 미적용',p/'stride_indexed.png')]
    s=Image.new('RGB',(900,330),(37,40,49));d=ImageDraw.Draw(s);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
    for i,(label,path) in enumerate(items):
        pic=Image.open(path).convert('RGBA');pic=pic.crop(pic.getbbox());pic=pic.resize((pic.width*5,pic.height*5),Image.Resampling.NEAREST);s.paste(pic,(i*300+20,45),pic);d.text((i*300+10,8),label,font=font,fill='white')
    s.save(p/'comparison_native_5x.png')
    report={'source':'generated_stride.png','source_sha256':digest(source),'master_sha256':digest(master),'head_top_to_eye_scale':scale,'source_eye_center':eye.tolist(),'native_size':[px.shape[1],px.shape[0]],'whole_pose_height_normalization':False,'applied':False,'imagegen_mode':'built_in','prompt':'prompt_stride.txt'}
    (p/'stride_conversion.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
