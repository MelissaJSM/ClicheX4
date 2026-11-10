"""원본 기준점과 수용 팔레트로 이동 시트를 정규화한다. 아직 BIN을 쓰지 않는다."""
import json,sys,struct,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256

def ranges(values):
    values=np.flatnonzero(values)
    return [(int(s.min()),int(s.max()+1)) for s in np.split(values,np.where(np.diff(values)>1)[0]+1) if len(s)>8]

def quantize(im,size,rgb,edge_threshold=None):
    src=np.array(im);labels=np.zeros(src.shape[:2],np.uint8)
    for y in range(im.height):
        delta=src[y,:,:3].astype(np.int32)[:,None,:]-rgb[None,1:,:]
        labels[y]=np.argmin((delta*delta).sum(2),axis=1)+1
    votes=[]
    for n in range(1,16):
        weight=np.where(labels==n,src[:,:,3],0).astype(np.uint8)
        votes.append(np.array(Image.fromarray(weight).resize(size,Image.Resampling.BOX)))
    result=np.argmax(np.stack(votes),axis=0).astype(np.uint8)+1
    alpha=np.array(im.getchannel('A').resize(size,Image.Resampling.BOX))
    result[alpha<128]=0
    if edge_threshold is not None:
        if not 1<=edge_threshold<=255:raise ValueError('Invalid source outline coverage threshold')
        opaque=alpha>=128;padded=np.pad(opaque,1)
        edge=opaque&~(padded[:-2,1:-1]&padded[2:,1:-1]&padded[1:-1,:-2]&padded[1:-1,2:])
        # Retain a sampled dark contour only in the exterior pixel layer.
        # This changes palette selection, never alpha or silhouette size.
        result[edge&(votes[14]>=edge_threshold)]=15
    if not np.any(result==7):
        # Retain an existing gold eye sample when area averaging splits it
        # across cells. Never synthesize a color absent from that source cell.
        gold=votes[6].copy();gold[alpha<128]=0;gold[int(size[1]*.6):]=0
        if gold.max()>=48:result[np.unravel_index(gold.argmax(),gold.shape)]=7
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--art-dir',type=Path,default=ROOT/'work/ver_buki_riko/shibuki_art/run_cycle_v1')
    parser.add_argument('--output-name',default='normalized')
    parser.add_argument('--match-head',action='store_true',help='Calibrate one common scale using approved ear-to-eye distance')
    args=parser.parse_args();work=args.art_dir.resolve()
    if not work.is_relative_to((ROOT/'work/ver_buki_riko/shibuki_art').resolve()):raise ValueError('Unexpected art directory')
    import re
    if not re.fullmatch(r'normalized[0-9]*',args.output_name):raise ValueError('Expected simple normalized output name')
    out=work/args.output_name;out.mkdir(exist_ok=False)
    order=json.loads((work/'order.json').read_text())['frames']
    selection=json.loads((ROOT/'projects/ver_buki_riko/shibuki_art_selection.json').read_text(encoding='utf-8'))
    palette_file=ROOT/selection['candidate']/'palette.bin'
    if palette_file.exists():words=struct.unpack('<16H',palette_file.read_bytes())
    else:words=json.loads((ROOT/selection['candidate']/'candidate.json').read_text(encoding='utf-8'))['palette_words']
    rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    im=Image.open(work/'generated.png').convert('RGBA');a=np.array(im);mask=a[:,:,3]>=128
    rows=ranges(mask.any(1));boxes=[]
    if len(rows)!=2:raise ValueError('Expected two sprite rows')
    for top,bottom in rows:
        cols=ranges(mask[top:bottom].any(0))
        if len(cols)!=8:raise ValueError('Expected eight isolated sprites per row')
        for left,right in cols:
            yy,xx=np.nonzero(mask[top:bottom,left:right]);boxes.append((left,top+int(yy.min()),right,top+int(yy.max()+1)))
    scale=47/(boxes[0][3]-boxes[0][1])
    head_calibration=None
    if args.match_head:
        reference=np.array(Image.open(ROOT/selection['indexed_png']))
        target=float(np.median(np.nonzero(reference==7)[0])-np.nonzero(reference)[0].min())
        first=np.array(im.crop(boxes[0]));gold=[]
        for y in range(first.shape[0]//2):
            d=first[y,:,:3].astype(np.int32)[:,None,:]-rgb[None,1:,:]
            lab=np.argmin((d*d).sum(2),axis=1)+1
            gold.extend([y]*int(np.count_nonzero((lab==7)&(first[y,:,3]>=128))))
        if not gold:raise ValueError('No eye landmark for scale calibration')
        scale=target/float(np.median(gold))
        head_calibration={'target_ear_to_eye':target,'source_ear_to_eye':float(np.median(gold))}
    source=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z'
    inv=json.loads((source/'inventory.json').read_text(encoding='utf-8'))
    records=[];sheet=Image.new('RGB',(8*224,2*256),'#222630');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
    for i,(n,bb) in enumerate(zip(order,boxes)):
        crop=im.crop(bb);size=(round(crop.width*scale),round(crop.height*scale));labels=quantize(crop,size,rgb)
        original=np.array(Image.open(source/f'base_{n:03d}.png'));ob=inv['base_frames'][n]['bounds']
        # Palette indices 3/4 are X face shades; only the upper face is used.
        face=np.isin(original,[3,4]);face[25:]=False
        oy,ox=np.nonzero(face)
        if not len(ox):raise ValueError('Original face anchor not found')
        # Shibuki gold eye uses index 7 in the selected remapped palette.
        ey,ex=np.nonzero(labels==7)
        if not len(ex):raise ValueError(f'Golden eye missing in frame {n}')
        left=round(float(np.median(ox)+ob[0]-np.median(ex)))
        # Preserve original visible head bob, with two pixels for fox ear tips.
        top=inv['base_frames'][n]['opaque_bbox'][1]+ob[1]-2
        if args.match_head:
            top=inv['base_frames'][n]['opaque_bbox'][3]+ob[1]-size[1]
        canvas=np.zeros((80,96),np.uint8);x=left+48;y=top+40
        if x<0 or y<0 or x+size[0]>96 or y+size[1]>80:raise ValueError('Canvas clipping')
        canvas[y:y+size[1],x:x+size[0]]=labels
        pic=save_image(canvas.tobytes(),(96,80),words,out/f'run_{n:03d}.png').convert('RGBA')
        bx=(i%8)*224;by=(i//8)*256;draw.text((bx+6,by+5),f'Shibuki {n:03}',font=font,fill='white')
        big=pic.resize((288,240),Image.Resampling.NEAREST);sheet.paste(big,(bx-32,by+20),big)
        draw.line((bx+4,by+20+63*3,bx+220,by+20+63*3),fill='#45556b')
        records.append({'frame':n,'crop':bb,'native_size':size,'world_position':[left,top],
                        'world_bounds':[-48,-40,48,40],'opaque_pixels':int(np.count_nonzero(canvas)),
                        'eye_anchor_method':'original face median x, common scale; eye lies at original face median',
                        'image':f'run_{n:03d}.png'})
    sheet.save(out/'run_master_3x.png')
    sequence=inv['animations'][8]['steps'];pictures=[]
    for step in sequence:
        p=Image.open(out/f"run_{step['frame']:03d}.png").convert('RGBA')
        bg=Image.new('RGB',(288,240),'#222630');p=p.resize(bg.size,Image.Resampling.NEAREST);bg.paste(p,(0,0),p);pictures.append(bg)
    pictures[0].save(out/'run_preview.gif',save_all=True,append_images=pictures[1:],duration=[round(s['duration_ticks']*1000/60) for s in sequence],loop=0,disposal=2)
    report={'task':'x_shibuki','source_sha256':sha256((work/'generated.png').read_bytes()),'common_scale':scale,
            'frames':records,'palette_words':words,'game_applied':False,'runtime_verified':False,
            'per_pose_scaling':False,'source_inventory':str((source/'inventory.json').relative_to(ROOT)),
            'quantization':'palette area; preserve source gold eye if >=48/255 alpha-weighted cell coverage',
            'head_calibration':head_calibration,
            'alignment_review_pending':True,'full_loop_art_review_pending':True}
    (out/'art.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(out),'sizes':[(r['frame'],r['native_size'],r['opaque_pixels']) for r in records]}))

if __name__=='__main__':main()
