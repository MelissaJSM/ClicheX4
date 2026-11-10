"""Register new full-body wall art without replacing any region with old art."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[4]
D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import crop_cell,register
import numpy as np
from PIL import Image
from scipy.ndimage import label

KEYS=[55,57,61,65]
TOPS={55:-21,57:-22,61:-22,65:-21}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',type=int,choices=[1,2],default=1);ap.add_argument('--page',choices=['keys','remaining','firing','remaining_reach','firing_reach'],default='keys');args=ap.parse_args()
    plan=json.loads((D/'inputs.json').read_text('utf8'))
    a=Archive((ROOT/plan['source_arc']).read_bytes());need(sha(a.data)==plan['source_sha256'],'Parent hash')
    folder=D/f'basic_{args.page}_v{args.version}'
    out=D/(f'basic_registered_probe_v{args.version}'if args.page=='keys'else f'basic_{args.page}_registered_v{args.version}');out.mkdir(exist_ok=True)
    im=Image.open(folder/'generated.png').convert('RGBA')
    expected={'keys':{1:'a75ca91528a08f8ae9f3d8d7c7e5c58df94f382a420798c294caaa63bc0201ac',2:'f3eb6dc3bdbe40a3d01d8b4c00578c0320cee76b285bf8f31e81cf2ae17cf075'},'remaining':{1:'08b4b34b0437e1b52191d0f71e3ca9e8ce545e30aa4df01fd2e75fef13dba248'},'firing':{1:'725bf52b9081da3eedc7c258edeebe448688702bccc5b98a84fde730e0476fa8'},'firing_reach':{2:'2d69400afc3af46b33a4aeebd6f5a6e4c2113fae36dc0ea11389ba888ec5e48f'},'remaining_reach':{2:'f63ace161e2e0629827defe26ab5ac7563b55c9ca2833e144ac737bf57a11565'}}
    need(digest(folder/'generated.png')==expected[args.page][args.version],'Source art')
    refs={'keys':KEYS,'remaining':[59,63,64,66],'firing':[56,58,60,62],'remaining_reach':[59,63,64,66],'firing_reach':[56,58,60,62]}[args.page]
    palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
    rows=[];records=[]
    for k,n in enumerate(refs):
        p=next(v for v in plan['frames']if v['ref']==n)
        crop,box=crop_cell(im,k);crop.save(out/f'source_{n:03}.png')
        arr=np.array(crop);rgb=arr[:,:,:3].astype(float);opaque=arr[:,:,3]>=128
        green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&opaque
        green[crop.height//3:]=False
        labels,count=label(green)
        candidates=[]
        for li in range(1,count+1):
            cy,cx=np.nonzero(labels==li)
            if len(cx)>=8:candidates.append((int(cy.min()),-len(cx),li))
        need(bool(candidates),'No source eye')
        sy,sx=np.nonzero(labels==min(candidates)[2])
        ey,ex=float(np.median(sy)),float(np.median(sx))
        # Hat crown is in the head region, unlike the higher raised wall hand.
        yy,xx=np.nonzero(opaque&(np.indices(opaque.shape)[1]<crop.width*.6))
        crown=float(yy.min());dx,dy=map(int,p['eye_world'])
        head_top=TOPS[n]if n in TOPS else int(np.where((a.layer(n)[0]>0)&(np.indices((384,384))[1]<160+dx+8))[0].min()-160)
        scale=(dy-head_top+1)/(ey-crown+1)
        width=round(crop.width*scale);split=round(ey+1)
        native_top=dy-round(split*scale)+1
        height_above=dy-native_top+1;bottom=p['bbox_world'][3];height_below=bottom-dy-1
        upper=register(crop.crop((0,0,crop.width,split)),(width,height_above),palette,'area_vote')
        lower=register(crop.crop((0,split,crop.width,crop.height)),(width,height_below),palette,'area_vote')
        native=np.concatenate((upper,lower))
        eye_col=round((ex+.5)*width/crop.width-.5)
        # Collapse only the source green iris to one native pixel; all body art is new.
        native[:upper.shape[0]][native[:upper.shape[0]]==14]=12;native[height_above-1,eye_col]=14
        ox,oy=dx-eye_col,native_top;target=np.zeros((384,384),np.uint8)
        target[160+oy:160+oy+native.shape[0],160+ox:160+ox+width]=native
        Image.fromarray(target).save(out/f'base_{n:03}.png');a.rgba(target).save(out/f'base_{n:03}_rgba.png')
        ty,tx=np.nonzero(target)
        records.append({'ref':n,'source_crop':box,'source_eye':[ex,ey],'source_crown_y':crown,'source_scale_x':scale,'native_position':[ox,oy],'native_bbox':[int(tx.min()-160),int(ty.min()-160),int(tx.max()+1-160),int(ty.max()+1-160)],'expected_eye':[dx,dy],'target_eye':[dx,dy],'expected_foot_max_y':bottom-1,'target_foot_max_y':int(ty.max()-160),'old_art_pixels_used':0,'contact_check':'pending local hand/foot correspondence','indexed_sha256':sha(target.tobytes())})
        rows.append((f'wall {n}',[('idle master',a.composite(0)[0]),('current',a.composite(n)[0]),('new whole source',a.rgba(target))]))
    helper.grid(rows,out/'comparison.png',7)
    write(out/'registration.json',{'source_arc_sha256':sha(a.data),'source_art_sha256':digest(folder/'generated.png'),'frames':records,'native_packed':False,'runtime_verified':False})
    print(json.dumps({'out':str(out),'frames':len(records)}))

if __name__=='__main__':main()
