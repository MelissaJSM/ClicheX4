"""다섯 탑승 머리를 공통 배율로 16색·단일 타일에 등록한다."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_ride_heads import OUT
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.project import digest
from scripts.extract_zero import save_image

def main():
    m=json.loads((OUT/'guide.json').read_text('utf-8'));words=m['palette_words'];colors=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in words[1:]],np.int32)
    image=Image.open(OUT/'generated.png').convert('RGBA');a=np.array(image);a[:,:,3]=np.where(a[:,:,3]>=128,255,0);image=Image.fromarray(a);crops=[];boxes=[]
    for i in range(6):
        box=(i%3*image.width//3,i//3*image.height//2,(i%3+1)*image.width//3,(i//3+1)*image.height//2);c=image.crop(box);b=c.getbbox()
        if b is None:raise ValueError('Missing generated head')
        crops.append(c.crop(b));boxes.append([box,b])
    # One identical scale for all angles. Column0 must stay transparent at GPU U0.
    scale=min(15/max(c.width for c in crops),16/max(c.height for c in crops));frames={};unique={};records=[]
    sheet=Image.new('RGB',(6*160,360),(34,37,47));d=ImageDraw.Draw(sheet)
    for i,(n,crop) in enumerate(zip(m['slots'],crops)):
        px=quantize(crop,colors,scale)
        if px.shape[0]>16 or px.shape[1]>15:raise ValueError('Head exceeds single tile')
        canvas=np.zeros((16,16),np.uint8);x=1+(15-px.shape[1])//2;y=16-px.shape[0];canvas[y:y+px.shape[0],x:x+px.shape[1]]=px
        if np.any(canvas[:,0]):raise ValueError('Mirror U0 edge occupied')
        groups=connected_groups(canvas>0)
        if len(groups)>1 and any(len(q)>3 for q in groups[1:]):raise ValueError('Detached head fragment')
        path=OUT/('calibration.png' if n is None else f'head_{n}.png');p=save_image(canvas.tobytes(),(16,16),words,path)
        if n is not None:unique[n]={'file':path.name,'sha256':digest(path),'size':[16,16],'opaque_pixels':int(np.count_nonzero(canvas))}
        big=p.convert('RGBA').resize((128,128),Image.Resampling.NEAREST);sheet.paste(big,(i*160+16,210),big);d.text((i*160+8,185),'Rin '+str(n),fill='white')
        if n is not None:
            old=Image.open(OUT/f'original_{n}.png').convert('RGBA').resize((128,128),Image.Resampling.NEAREST);sheet.paste(old,(i*160+16,30),old)
        d.text((i*160+8,8),'source '+str(n),fill='white');records.append({'frame':n,'crop':boxes[i],'native_content_size':[px.shape[1],px.shape[0]],'placement':[x,y]})
    for n,r in m['frames'].items():
        if r['source'] is not None:frames[n]={**unique[r['source']],'source':r['source'],'bounds':r['bounds']}
    sheet.save(OUT/'comparison.png');report={'parent':m['parent'],'parent_sha256':m['parent_sha256'],'generated_sha256':digest(OUT/'generated.png'),'prompt_sha256':digest(OUT/'prompt.txt'),'uniform_scale':scale,'alpha_threshold':128,'per_pose_scaling':False,'records':records,'frames':frames,'preserved_blank_refs':[80],'palette_words':words,'part_coordinates_preserved':True,'issues':[]}
    (OUT/'recipe.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps({'references':len(frames),'unique':len(unique),'uniform_scale':scale,'native_sizes':[q['native_content_size'] for q in records]}))

if __name__=='__main__':main()
