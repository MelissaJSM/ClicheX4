"""생성한 연속 자세를 수용 팔레트와 원작 좌표에 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label,find_objects
from scripts.prepare_nana_idle_shot import PILOT,INV,write
from scripts.project import digest
from scripts.extract_zero import save_image

def quantize(im,size,rgb):
    a=np.array(im);labels=np.zeros(a.shape[:2],np.uint8)
    for y in range(len(a)):
        delta=a[y,:,:3].astype(np.int32)[:,None,:]-rgb[None,1:,:];labels[y]=1+(delta*delta).sum(2).argmin(1)
        r,g,b=a[y,:,:3].astype(np.int32).T
        labels[y,(g>=60)&(g>r+20)&(g>b+20)]=14
    votes=np.stack([np.array(Image.fromarray(np.where(labels==i,a[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX)) for i in range(1,16)])
    result=(1+votes.argmax(0)).astype(np.uint8);alpha=np.array(im.getchannel('A').resize(size,Image.Resampling.BOX));result[alpha<128]=0
    if not np.any(result==14):
        eye=votes[13].copy();eye[alpha<128]=0;eye[size[1]//2:]=0
        if eye.max()>=8:result[np.unravel_index(eye.argmax(),eye.shape)]=14
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--revised-cycle',action='store_true');a=p.parse_args()
    if not a.source.resolve().is_relative_to(ROOT/'work/ver_rin_nana/nana_art') or not a.output.resolve().is_relative_to(ROOT/'work/ver_rin_nana/nana_art') or a.output.exists():raise ValueError('Fresh Nana art output required')
    plan=json.loads((a.source.parent/'plan.json').read_text('utf8'));inv=json.loads(INV.read_text('utf8'));words=struct.unpack('<16H',(PILOT/'palette.bin').read_bytes())
    rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    im=Image.open(a.source).convert('RGBA');boxes=[]
    labels,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(labels.flat)
    objects=[(idx,(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)) for idx,sl in enumerate(find_objects(labels),1) if sizes[idx]>1000]
    objects.sort(key=lambda r:(r[1][1]>=im.height//2,r[1][0]))
    if len(objects)!=16:raise ValueError('Expected 16 isolated figures')
    boxes=[b for _,b in objects]
    scale=45/(boxes[0][3]-boxes[0][1]);out=a.output;out.mkdir(parents=True);records=[];frames={}
    second=None
    if a.revised_cycle:
        second=Image.open(a.source.parent/'second_half_revision.png').convert('RGBA');slab,_=label(np.array(second.getchannel('A'))>=192);sizes2=np.bincount(slab.flat);sob=[(j,(s[1].start,s[0].start,s[1].stop,s[0].stop)) for j,s in enumerate(find_objects(slab),1) if sizes2[j]>1000];sob.sort(key=lambda r:r[1][0])
        if len(sob)!=8:raise ValueError('Eight second-half keyposes required')
        scale2=scale*(boxes[8][3]-boxes[8][1])/(sob[0][1][3]-sob[0][1][1])
        second_map={13:0,15:0,17:1,19:3,21:4,23:1,25:6,27:7}
    board=Image.new('RGB',(8*240,3*244),'#222630');draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15)
    for i,(n,box) in enumerate(zip(plan['order'],boxes)):
        used=i;pic=im;lab=labels;idx=objects[i][0];sc=scale
        if a.revised_cycle and n==7:used=4;idx,box=objects[used]
        if a.revised_cycle and n in second_map:used=second_map[n];idx,box=sob[used];pic=second;lab=slab;sc=scale2
        crop=pic.crop(box);pixels=np.array(crop);local=lab[box[1]:box[3],box[0]:box[2]];pixels[local!=idx,3]=0;crop=Image.fromarray(pixels)
        size=(round(crop.width*sc*.9),round(crop.height*sc));v=quantize(crop,size,rgb)
        eye=(v==14);eye[size[1]//2:]=False;ey,ex=np.nonzero(eye)
        if not len(ex):raise ValueError(f'Eye missing {n}')
        source=np.array(Image.open(INV.parent/f'base_{n:03d}.png'));face=np.isin(source,[3,4]);face[25:]=False;fy,fx=np.nonzero(face);bb=inv['base_frames'][n]['bounds']
        # Master eye world -4; source's upper face center supplies only relative X.
        native0=np.array(Image.open(INV.parent/'base_000.png'));f0=np.isin(native0,[3,4]);f0[25:]=False;y0,x0=np.nonzero(f0)
        native_face0=float(np.median(x0)+inv['base_frames'][0]['bounds'][0])
        x=round(44+(float(np.median(fx)+bb[0])-native_face0)-float(np.median(ex)))
        bottom=inv['base_frames'][n]['opaque_bbox'][3]+bb[1]+40;y=bottom-size[1]
        canvas=np.zeros((80,96),np.uint8);canvas[y:y+size[1],x:x+size[0]]=v;frames[n]=canvas
        if a.revised_cycle and n in second_map:
            accepted_upper=np.array(Image.open(a.source.parent/'normalized03'/f'run_{n:03d}.png'))
            # Preserve the first coherent sheet's upper body; the targeted revision
            # contributes only the crossing legs below the hem.
            canvas[:46]=accepted_upper[:46]
            eys,exs=np.nonzero((accepted_upper==14)&(np.indices(accepted_upper.shape)[0]<40))
            ex=np.array([float(np.median(exs))-x]);ey=np.array([float(np.median(eys))-y])
        save_image(canvas.tobytes(),(96,80),words,out/f'run_{n:03d}.png')
        pic=Image.open(out/f'run_{n:03d}.png').convert('RGBA').crop((16,12,76,65)).resize((240,212),Image.Resampling.NEAREST)
        px,py=i%8*240,i//8*244;board.paste(pic,(px,py+25),pic);draw.text((px+5,py+4),f'run {n:03d}',font=font,fill='white')
        records.append({'frame':n,'image':f'run_{n:03d}.png','source_box':box,'source_keypose':used,'source_image':'second_half_revision.png' if pic is second else a.source.name,'native_size':size,'position':[x-48,y-40],'opaque_pixels':int(np.count_nonzero(canvas)),'eye':[int(round(np.median(ex)+x)),int(round(np.median(ey)+y))]})
    for i,n in enumerate((0,85)):
        old=ROOT/'out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z/art'/f'frame_{n:03d}.png';pic=Image.open(old).convert('RGBA').crop((16,12,76,65)).resize((240,212),Image.Resampling.NEAREST);board.paste(pic,(i*240,513),pic);draw.text((i*240+5,492),f'accepted {n:03d}',font=font,fill='white')
    board.save(out/'family_4x.png')
    pics=[]
    for s in plan['run_animation']['steps']:
        pic=Image.open(out/f"run_{s['frame']:03d}.png").convert('RGBA').resize((384,320),Image.Resampling.NEAREST);bg=Image.new('RGB',pic.size,'#222630');bg.paste(pic,(0,0),pic);pics.append(bg)
    pics[0].save(out/'run_preview.gif',save_all=True,append_images=pics[1:],duration=[round(s['duration_ticks']*1000/60) for s in plan['run_animation']['steps']],loop=0,disposal=2)
    write(out/'art.json',{'task':'x_nana','source':a.source.as_posix(),'source_sha256':digest(a.source),'source_inventory':INV.relative_to(ROOT).as_posix(),'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'frames':records,'palette_words':list(words),'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'runtime_verified':False})
    print(json.dumps({'output':str(out),'sizes':[(r['frame'],r['native_size']) for r in records]}))
if __name__=='__main__':main()
