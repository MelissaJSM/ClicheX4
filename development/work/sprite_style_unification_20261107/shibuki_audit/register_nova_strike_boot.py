"""새 부츠 donor 고정 등록. 합성 영역 확정 전 전체 donor를 채택하지 않는다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    s=H/'nova_strike_boot_inputs01';d=H/'nova_strike_boot_native01';need(not d.exists(),'새 등록');d.mkdir();g=s/'generated.png';need(not g.exists(),'원화 보호');src=Path(sys.argv[1]);shutil.copy2(src,g)
    m=json.loads((s/'input.json').read_text('utf8'));a=Archive((H/'prepared_nova_base01/PL00_U.ARC').read_bytes());need(sha(a.data)==m['parent_sha256'],'부모 변경')
    for n,h in m['files'].items():need(sha((s/n).read_bytes())==h,'입력 변경')
    im=Image.open(g).convert('RGBA');need(im.width==im.height,'정사각 전체');v=np.array(im.resize((128,128),Image.Resampling.NEAREST));rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[16:32]],np.int32)
    ind=(1+((v[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);ind[v[:,:,3]<128]=0;z=np.zeros((384,384),np.uint8);z[96:224,96:224]=ind;native=a.rgba(z,16);Image.fromarray(z).save(d/'fourth_217_indices.png');native.save(d/'fourth_217.png');Image.fromarray(v).save(d/'sample_rgba.png')
    old=Image.open(ROOT/m['source']['path']).convert('RGBA');page([('새217 이전',old),('부츠 donor 전체 진단',native)],a.composite(0,15)[0],d/'comparison.png',cols=2,scale=6)
    box=(164,163,188,176);scale=24;panel=Image.new('RGB',((box[2]-box[0])*scale*2,(box[3]-box[1])*scale+40),(26,32,43));dr=ImageDraw.Draw(panel)
    for k,srcim in enumerate((old,native)):
        cropped=srcim.crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST);panel.paste(cropped,(k*cropped.width,40),cropped)
        for x in range(box[0],box[2]):dr.text((k*cropped.width+(x-box[0])*scale,0),str(x-160),fill='white');dr.line((k*cropped.width+(x-box[0])*scale,40,k*cropped.width+(x-box[0])*scale,panel.height),fill='#567')
        for y in range(box[1],box[3]):dr.text((k*cropped.width,40+(y-box[1])*scale),str(y-160),fill='white');dr.line((k*cropped.width,40+(y-box[1])*scale,(k+1)*cropped.width,40+(y-box[1])*scale),fill='#567')
    panel.save(d/'boot_grid.png');labs,_=label(ind>0,np.ones((3,3)));rows={'old_metrics':metrics(old),'donor_metrics':metrics(native),'components':sorted(np.bincount(labs.ravel())[1:].tolist(),reverse=True),'low_alpha_samples':int(((v[:,:,3]>0)&(v[:,:,3]<128)).sum())}
    write(s/'generation_receipt.json',{'tool':'builtin image_gen','default_output':str(src),'sha256':sha(g.read_bytes()),'size':list(im.size),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'original_preserved':True,'whole_donor_accepted':False})
    write(d/'registration.json',{'source_sha256':sha(g.read_bytes()),'whole_canvas_native':[128,128],'alpha_cutoff':128,'sprite_specific_scaling':False,'rows':rows,'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[s/'input.json',g,s/'generation_receipt.json',Path(__file__),*d.glob('*.png')]}});print(json.dumps({'generated':sha(g.read_bytes()),**rows}))
if __name__=='__main__':main()
