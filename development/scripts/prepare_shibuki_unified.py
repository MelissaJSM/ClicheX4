"""한 생성 시트에서 대기/이동을 동일 축척·팔레트로 추출한다."""
import argparse,json,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import ranges,quantize
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--art-dir',type=Path,required=True);p.add_argument('--output-name',default='production');args=p.parse_args();work=args.art_dir.resolve()
    if not work.is_relative_to(ROOT/'work/ver_buki_riko/shibuki_art'):raise ValueError('Unexpected work directory')
    import re
    if not re.fullmatch(r'production[0-9]*',args.output_name):raise ValueError('Invalid output name')
    out=work/args.output_name;out.mkdir(exist_ok=False)
    old=json.loads((ROOT/'projects/ver_buki_riko/shibuki_art_selection.json').read_text(encoding='utf-8'))
    words=struct.unpack('<16H',(ROOT/old['candidate']/'palette.bin').read_bytes());rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    im=Image.open(work/'generated.png').convert('RGBA');mask=np.array(im)[:,:,3]>=128;rows=ranges(mask.any(1));boxes=[]
    if len(rows)!=2:raise ValueError('Expected two rows')
    for top,bottom in rows:
        cols=ranges(mask[top:bottom].any(0))
        if len(cols)!=8:raise ValueError('Expected eight sprites per row')
        for left,right in cols:
            yy,xx=np.nonzero(mask[top:bottom,left:right]);boxes.append((left,top+int(yy.min()),right,top+int(yy.max()+1)))
    scale=47/(boxes[0][3]-boxes[0][1]);order=[1,29,31,5,7,9,11,13,3,15,17,19,21,23,25,27]
    labels=[]
    for box in boxes:
        crop=im.crop(box);labels.append(quantize(crop,(round(crop.width*scale),round(crop.height*scale)),rgb,edge_threshold=48))
    idle=labels[0];foot=np.nonzero(idle[-3:])[1];left=round(18-(int(foot.min())+int(foot.max()))/2);top=48-idle.shape[0]
    canvas=np.zeros((48,48),np.uint8)
    world_shift=max(0,left+idle.shape[1]-32);left-=world_shift
    if left<1 or left+idle.shape[1]>32:raise ValueError(f'Idle exceeds reserved 32x48 base rectangle: {left}, {idle.shape}')
    canvas[top:top+idle.shape[0],left:left+idle.shape[1]]=idle
    save_image(canvas.tobytes(),(48,48),words,out/'shibuki_idle000_indexed.png')
    Image.open(out/'shibuki_idle000_indexed.png').resize((384,384),Image.Resampling.NEAREST).save(out/'shibuki_idle000_8x.png')
    (out/'palette.bin').write_bytes(struct.pack('<16H',*words));im.crop(boxes[8]).save(out/'blink_generated.png')
    ey,ex=np.nonzero(canvas==7)
    if not len(ex):raise ValueError('Idle eye missing')
    eye=[int(ex.min())-1,int(ey.min())-1,int(ex.max())+2,int(ey.max())+2]
    source=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';inv=json.loads((source/'inventory.json').read_text())
    records=[];sheet=Image.new('RGB',(8*224,2*256),'#222630');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
    for i,n in enumerate(order):
        lab=idle.copy() if n in (1,3) else labels[i]
        if n in (1,3):wx,wy=left-19+world_shift,top-25
        else:
            original=np.array(Image.open(source/f'base_{n:03d}.png'));ob=inv['base_frames'][n]['bounds'];face=np.isin(original,[3,4]);face[25:]=False
            ox=np.nonzero(face)[1];gold=np.nonzero(lab==7)[1]
            if not len(gold):raise ValueError(f'Run eye missing: {n}')
            wx=round(float(np.median(ox)+ob[0]-np.median(gold)));wy=inv['base_frames'][n]['opaque_bbox'][3]+ob[1]-lab.shape[0]
        a=np.zeros((80,96),np.uint8);a[wy+40:wy+40+lab.shape[0],wx+48:wx+48+lab.shape[1]]=lab
        pic=save_image(a.tobytes(),(96,80),words,out/f'run_{n:03d}.png').convert('RGBA');bx,by=(i%8)*224,(i//8)*256
        draw.text((bx+6,by+5),'Idle / start' if n in (1,3) else f'Run {n:03d}',font=font,fill='white');big=pic.resize((288,240),Image.Resampling.NEAREST);sheet.paste(big,(bx-32,by+20),big)
        draw.line((bx+4,by+20+63*3,bx+220,by+20+63*3),fill='#45556b')
        records.append({'frame':n,'crop':boxes[i],'native_size':[lab.shape[1],lab.shape[0]],'world_position':[wx,wy],'world_bounds':[-48,-40,48,40],
                        'opaque_pixels':int(np.count_nonzero(a)),'image':f'run_{n:03d}.png','ear_to_eye':float(np.median(np.nonzero(lab==7)[0]))})
    sheet.save(out/'unified_master_3x.png')
    report={'task':'x_shibuki','source_sha256':sha256((work/'generated.png').read_bytes()),'source_inventory':str((source/'inventory.json').relative_to(ROOT)),
            'common_scale':scale,'per_pose_scaling':False,'palette_words':words,'frames':records,'game_applied':False,'runtime_verified':False,
            'quantization':'area palette; retain source outline sample >=48/255 only in one-pixel silhouette boundary',
            'idle_position':[left,top],'idle_size':[idle.shape[1],idle.shape[0]],'eye_patch':eye,'world_x_shift':world_shift,
            'art_basis':'walking body proportions; thinner contour for both idle and run',
            'startup_poses_share_neutral_idle':True,'full_loop_art_review_pending':True}
    (out/'art.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'out':str(out),'idle_size':report['idle_size'],'eye_patch':eye,'sizes':[(r['frame'],r['native_size'],r['ear_to_eye']) for r in records]}))

if __name__=='__main__':main()
