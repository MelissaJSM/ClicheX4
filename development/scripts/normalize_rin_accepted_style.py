"""시트의 고정 대기를 사용해 동작 전체를 동일 배율로 팔레트 변환한다."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import connected_groups,quantize
from scripts.extract_zero import save_image
from scripts.project import digest
OUT=ROOT/'work/ver_rin_nana/style_revision/v3'

def main():
    global OUT
    ap=argparse.ArgumentParser();ap.add_argument('group');ap.add_argument('--partial',action='store_true');ap.add_argument('--work',type=Path,default=OUT);a=ap.parse_args()
    OUT=a.work.resolve()
    if not OUT.is_relative_to(ROOT/'work/ver_rin_nana/style_revision'):raise ValueError('Unexpected art directory')
    batches=json.loads((OUT/'batches.json').read_text());master=json.loads((OUT/'master.json').read_text());words=master['palette_words'];colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    folder=OUT/a.group;records={};sheets=[]
    for b in batches:
        if b['group']!=a.group:continue
        path=Path(b['output'])
        if not path.exists():
            if a.partial:continue
            raise ValueError(f'Missing source {path}')
        im=Image.open(path).convert('RGBA');rgba=np.array(im);rgba[:,:,3]=np.where(rgba[:,:,3]>=128,255,0);im=Image.fromarray(rgba)
        groups=connected_groups(rgba[::4,::4,3]>0)[:len(b['slots'])];boxes=[]
        if len(groups)!=len(b['slots']):raise ValueError('Missing generated sprite')
        for g in groups:
            y,x=g[:,0],g[:,1];boxes.append((max(0,int(x.min())*4-8),max(0,int(y.min())*4-8),min(im.width,int(x.max())*4+12),min(im.height,int(y.max())*4+12)))
        boxes.sort(key=lambda r:(r[1]+r[3])/2);boxes=[r for start in range(0,len(boxes),b['columns']) for r in sorted(boxes[start:start+b['columns']],key=lambda q:q[0])]
        crops=[]
        for box in boxes:
            pic=im.crop(box);pic=pic.crop(pic.getbbox());crops.append(pic)
        scale=48/crops[0].height
        save_image(quantize(crops[0],colors,scale).tobytes(),(round(crops[0].width*scale),48),words,folder/f'calibration_{b["batch"]}.png')
        sheets.append({'source':path.name,'sha256':digest(path),'calibration_crop':boxes[0],'calibration_size':list(crops[0].size),'calibration_kind':b.get('calibration_kind','idle_height48'),'uniform_scale':scale,'pose_height_normalization':False})
        for i,n in enumerate(b['slots']):
            if n is None:continue
            px=quantize(crops[i],colors,scale);gs=connected_groups(px>0);significant=[len(q) for q in gs[1:] if len(q)>3]
            if significant:raise ValueError(f'Detached features {a.group}:{n} {significant}')
            for q in gs[1:]:px[q[:,0],q[:,1]]=0
            yy,xx=np.nonzero(px);px=px[yy.min():yy.max()+1,xx.min():xx.max()+1];p=folder/f'prepared_{n:03d}.png';save_image(px.tobytes(),(px.shape[1],px.shape[0]),words,p)
            records[str(n)]={'file':p.name,'sha256':digest(p),'sheet':b['batch'],'scale':scale,'source_sha256':digest(path),'native_size':[px.shape[1],px.shape[0]],'alpha_noise_removed':[len(q) for q in gs[1:]]}
    (folder/'prepared.json').write_text(json.dumps({'frames':records,'sheets':sheets},indent=2)+'\n','utf-8')
    ns=list(records);sheet=Image.new('RGB',(4*260,((len(ns)+3)//4)*270),(37,40,49));d=ImageDraw.Draw(sheet)
    for i,n in enumerate(ns):
        pic=Image.open(folder/records[n]['file']).convert('RGBA');pic=pic.resize((pic.width*4,pic.height*4),Image.Resampling.NEAREST);x=i%4*260;y=i//4*270;sheet.paste(pic,(x+8,y+30),pic);d.text((x+8,y+8),n,fill='white')
    sheet.save(folder/'prepared_4x.png');print(json.dumps({'group':a.group,'frames':len(records),'scales':[s['uniform_scale'] for s in sheets]}))

if __name__=='__main__':main()
