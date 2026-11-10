"""사격 생성 원화의 고정 셀/팔레트 등록. 합성 및 패킹과 분리한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,required=True);ap.add_argument('--sha',required=True);ap.add_argument('--original-name',required=True);z=ap.parse_args();d=H/f'base_run_shot_inputs01/page{z.page:02}';out=H/f'base_run_shot_page{z.page:02}_source01';need(not out.exists(),'Fresh output');m=json.loads((d/'manifest.json').read_text('utf8'));p=H/'prepared_dash_base01/PL00_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)==m['source_parent_sha256'],'Parent changed');src=d/'generated.png';need(sha(src.read_bytes())==z.sha,'Source changed');im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Fixed source size changed');sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));full=np.array(im);out.mkdir();rows=[]
    for form,mask,pal in(('base',0,0),('fourth',15,16)):
        rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for r in [r for r in m['rows']if r['form']==form]:
            c,row=r['cell'];n=r['shot_ref'];cell=sample[row*64:(row+1)*64,c*64:(c+1)*64];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0;ar=np.zeros((384,384),np.uint8);ar[124:188,128:192]=q;Image.fromarray(ar).save(out/f'{form}_{n:03}_source_indices.png');new=a.rgba(ar,pal);new.save(out/f'{form}_{n:03}_source.png');labs,nc=label(ar>0,np.ones((3,3),int));sizes=sorted([int(np.count_nonzero(labs==k))for k in range(1,nc+1)],reverse=True)
            target=Image.open(d/f'{form}_{n:03}_target.png').convert('RGBA');pics.extend([(f'{n} fixed target body+gun',target),(f'{n} generated whole source only',new)]);rows.append({'form':form,'ref':n,'body_ref':r['body_ref'],'cell':r['cell'],'source_sha256':z.sha,'native_components8':sizes,'alpha_threshold':128})
            if form=='base':
                board=Image.new('RGB',(940,510),(28,34,44));dr=ImageDraw.Draw(board)
                for pos,img in enumerate((target,new)):
                    cut=img.crop((128,144,176,176));big=cut.resize((720,480),Image.Resampling.NEAREST);bg=Image.new('RGBA',big.size,(28,34,44,255));bg.alpha_composite(big);bg=bg.resize((720,480),Image.Resampling.NEAREST)
                    # A separate large grid per input prevents labels obscuring pixels.
                    sheet=Image.new('RGBA',(760,530),(28,34,44,255));sheet.alpha_composite(bg,(35,25));dd=ImageDraw.Draw(sheet)
                    for x in range(0,49):
                        px=35+x*15;dd.line((px,25,px,505),fill=(90,95,105,100),width=1)
                        if x%2==0:dd.text((px,5),str(x-32),fill='white')
                    for y in range(0,33):
                        py=25+y*15;dd.line((35,py,755,py),fill=(90,95,105,100),width=1)
                        if y%2==0:dd.text((3,py),str(y-16),fill='white')
                    sheet.convert('RGB').save(out/f'{n:03}_{"input"if pos==0 else "source"}_grid.png')
        page(pics,a.composite(0,mask)[0],out/f'{form}_source_comparison.png',cols=2,scale=5)
    prompt=(d/'prompt.txt').read_text('utf8').strip();(d/'prompt_used.txt').write_text(prompt,'utf8');write(d/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':z.original_name,'source_sha256':z.sha,'source_size':list(im.size),'prompt_sha256':sha(prompt.encode()),'inputs':{n:sha((d/n).read_bytes())for n in('edit_target.png','arm_guide.png')}});write(out/'report.json',{'parent_sha256':sha(a.data),'source_sha256':z.sha,'rows':rows,'sampling':'fixed1/8 nearest, original15opaqueCLUT','whole_generated_body_not_adopted':True,'arm_semantic_composite_pending':True,'arc_written':False});print(json.dumps({'source_sha256':z.sha,'registered_displays':len(rows),'components':[r['native_components8']for r in rows]}))
if __name__=='__main__':main()
