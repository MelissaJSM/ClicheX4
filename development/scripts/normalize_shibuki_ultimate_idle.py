"""Normalize imagegen outfit to native palette/anchors; no source-image mutation."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D
from scripts.prepare_riko_ui import entry
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--width',type=int,default=28);p.add_argument('--source',default='idle_generated.png');p.add_argument('--bands',action='store_true');a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(D):raise ValueError('Use task work directory')
    out.mkdir(exist_ok=False)
    arc=(D/'analysis/parent_PL00_U.ARC').read_bytes();words=list(struct.unpack_from('<16H',entry(arc,9)))
    for i,rgb in {1:(24,41,82),3:(106,148,205),4:(65,82,140),11:(238,123,164)}.items():words[i]=0x8000|sum(round(c*31/255)<<s for c,s in zip(rgb,(0,5,10)))
    rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.int32)
    source=Image.open(D/a.source).convert('RGBA');rgba=np.array(source);ys,xs=np.nonzero(rgba[:,:,3]>=128);bb=[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1];crop=source.crop(bb)
    if a.bands:
        # Technical landmark registration to the accepted native head/hip/sole rows.
        cut=[0,round((620-bb[1])),round((960-bb[1])),crop.height];pieces=[]
        for lo,hi,rows in zip(cut,cut[1:],[21,14,12]):pieces.append(crop.crop((0,lo,crop.width,hi)).resize((crop.width,rows*24),Image.Resampling.NEAREST))
        crop=Image.new('RGBA',(crop.width,47*24));y=0
        for piece in pieces:crop.paste(piece,(0,y));y+=piece.height
    data=np.array(crop);labels=np.zeros(data.shape[:2],np.uint8)
    for y in range(crop.height):
        delta=data[y,:,:3].astype(np.int32)[:,None,:]-rgb[1:][None,:,:];labels[y]=np.argmin((delta*delta).sum(2),axis=1)+1
    width,height=a.width,47
    votes=[np.array(Image.fromarray(np.where(labels==i,data[:,:,3],0).astype(np.uint8)).resize((width,height),Image.Resampling.BOX)) for i in range(1,16)]
    native=(np.argmax(np.stack(votes),axis=0)+1).astype(np.uint8);alpha=np.array(crop.getchannel('A').resize((width,height),Image.Resampling.BOX));native[alpha<128]=0
    base=np.array(Image.open(D/'analysis/parent_PL00_U.ARC_000_0.png').convert('RGBA'));by,bx=np.nonzero(base[:,:,3]);bottom=int(by.max());feet=np.nonzero(base[bottom-2:bottom+1,:,3])[1];fc=(feet.min()+feet.max())/2
    nf=np.nonzero(native[-3:])[1];left=round(fc-(nf.min()+nf.max())/2);top=bottom-height+1
    v=np.zeros((160,160),np.uint8);v[top:top+height,left:left+width]=native
    im=save_image(v.tobytes(),(160,160),words,out/'outfit.png').convert('RGBA')
    sheet=Image.new('RGB',(900,610),'#253546');dr=ImageDraw.Draw(sheet)
    for i,(image,label) in enumerate([(Image.fromarray(base),'Accepted Shibuki'),(im,'Ultimate jacket - native candidate')]):
        image=image.crop((50,50,110,110)).resize((420,420),Image.Resampling.NEAREST);sheet.paste(image,(i*450+10,90),image);dr.text((i*450+10,18),label,fill='white')
    sheet.save(out/'review.png');im.crop((50,50,110,110)).resize((600,600),Image.Resampling.NEAREST).save(out/'outfit_10x.png')
    missing=np.argwhere((base[:,:,3]>0)&(v==0));coords=np.argwhere(v>0);dist=[int(((coords-[y,x])**2).sum(1).min()) for y,x in missing]
    report={'source':a.source,'source_sha256':sha256((D/a.source).read_bytes()),'landmark_registration':a.bands,'palette_words':words,'source_crop':bb,'native_size':[width,height],'position':[left,top],'base_bbox':[int(bx.min()),int(by.min()),int(bx.max())+1,int(by.max())+1],'target_bbox':im.getbbox(),'foot_center':float(fc),'uncovered_base_pixels':len(missing),'max_uncovered_distance_squared':max(dist,default=0),'uncovered_coords':missing.tolist(),'quantization':'RGB555 palette area voting; no dithering','runtime_verified':False}
    (out/'normalization.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('uncovered_coords','palette_words')}))

if __name__=='__main__':main()
