"""대시 뒷머리 연결부만 다시 등록하고 얼굴·몸·권총을 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_dash_20261104T091041940430Z'
PARENT_SHA='8c100b37b6aa24062393fc1cc1993cbcf8773c782f5699ea14084686b47d68bb'
ARC_SHA='5c90434be5ac356008df903b8c0cc70f1046b48c1cdfdabec925482fcb31e753'
SOURCE_SHA='7ece63bddcbc747996d281c8626f177082e3c450e664fc97a4c1499dda99dbea'
FRAMES=list(range(67,85));ORDER=[67,69,71,75,77,79,81,83]

def artwork(out):
    arc=(PARENT/'PL02_U.ARC').read_bytes();require(sha256(arc)==ARC_SHA,'Wrong dash hair parent');src=D/'dash_hair_v1/generated.png';require(digest(src)==SOURCE_SHA,'Hair source changed');source=Image.open(src).convert('RGBA');words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);yy,xx=np.indices((160,160));targets={n:full(arc,n)for n in FRAMES};proof=json.loads((PARENT/'ultimate_dash/registration.json').read_text('utf8'))
    for i,q in enumerate(proof):
        n,shot=q['frames'];ex,ey=q['eye'];old=targets[n].copy();base=render(arc,n)[1];cell=source.crop((i%4*source.width//4,i//4*source.height//2,(i%4+1)*source.width//4,(i//4+1)*source.height//2));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));ca=np.array(crop).astype(np.int32);sy,sx=np.indices(ca.shape[:2]);green=(ca[:,:,1]>ca[:,:,0]+5)&(ca[:,:,1]>ca[:,:,2]+5)&(ca[:,:,3]>=192)&(sy<crop.height*.65);gy,gx=np.nonzero(green);require(len(gx)>0,'Source eye missing');cx,cy=float(np.median(gx)),float(np.median(gy));h=round(16*crop.height/(cy+.5));v=normalize(crop,h,rgb,width=round(crop.width*h/crop.height));vx=round((cx+.5)*v.shape[1]/crop.width-.5);vy=round((cy+.5)*h/crop.height-.5);registered=np.zeros_like(old);dx,dy=ex-vx,ey-vy;registered[dy:dy+h,dx:dx+v.shape[1]]=v
        # Keep the established tail extent; only the rear half is registered.
        start=ex+6;end=int(np.nonzero((old>0)&(xx>=start)&(yy<q['leg_silhouette_from_y']))[1].max())+1;top=ey-13;bottom=q['leg_silhouette_from_y'];tail=registered[top:bottom,start:];cols=np.flatnonzero(np.any(np.isin(tail,(5,6,7,8,9)),axis=0));require(len(cols)>0,'Generated hair absent');native_tail=tail[:,:cols.max()+1];piece=np.array(Image.fromarray(native_tail).resize((end-start,bottom-top),Image.Resampling.NEAREST));piece[np.isin(piece,(10,11,12,13,14,15))]=0
        repaint=np.zeros_like(old);repaint[top:bottom,start:end]=piece
        # Below the head retain clothes and the back hand. Native pink hair
        # identifies the lower trailing locks independently of jacket colors.
        region=(xx>=start)&(xx<end)&(yy>=top)&(yy<bottom);allowed=region&((yy<ey+3)|np.isin(base,(5,6,7,8,9))|(old==0));allowed&=~np.isin(old,(10,11,12,13,14,15))
        good=np.isin(repaint,(5,6,7,8,9));require(good.any(),'Hair material missing');_,nearest=distance_transform_edt(~good,return_indices=True);need=allowed&(base>0)&(repaint==0);repaint[need]=repaint[nearest[0][need],nearest[1][need]]
        provisional=old.copy();provisional[allowed]=repaint[allowed]
        components,count=label(provisional>0,np.ones((3,3)));sizes=np.bincount(components.flat);sizes[0]=0;detached=[]
        for k in range(1,count+1):
            if k==sizes.argmax():continue
            isolated=components==k
            if np.count_nonzero(isolated)<=2 and np.all(region[isolated]) and not np.any(base[isolated]):
                allowed[isolated]=True;repaint[isolated]=0;detached.extend([[int(x),int(y)]for y,x in np.argwhere(isolated)])
        for ref in(n,shot):
            before=targets[ref].copy();targets[ref][allowed]=repaint[allowed];require(np.array_equal(before[~allowed],targets[ref][~allowed]),'Nonhair pixels changed');require(not np.any((render(arc,ref)[1]>0)&(targets[ref]==0)),'Base escapes hair')
        # The rear hair and the head must form one connected pink component.
        final=targets[n];hair=np.isin(final,(5,6,7,8,9))&(yy<ey+7)&(xx>=ex-4);labels,count=label(hair,np.ones((3,3)));roots=set(labels[ey-7:ey+3,ex+2:ex+8].flat)-{0};rear=hair&(xx>=ex+12)&(yy<ey+3);require(roots and np.all(np.isin(labels[rear],list(roots))),f'Hair root disconnected {n}')
        mask=Image.fromarray((allowed*255).astype(np.uint8));mask.save(out/f'hair_mask_{n:03}.png');q.update(hair_edit_box=[start,top,end,bottom],hair_mask_file=f'hair_mask_{n:03}.png',hair_changed_pixels=int(np.count_nonzero(old!=final)),nonhair_pixels_preserved=True,hair_root_connected=True,removed_detached_pixels=detached)
    for n in(73,74):targets[n]=np.where(targets[n-2]>0,targets[n-2],render(arc,n)[1]).astype(np.uint8)
    for n,t in targets.items():save_image(t.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
    for shot,name in((False,'dash_hair_review_4x.png'),(True,'dash_hair_shot_review_4x.png')):
        board=Image.new('RGB',(1280,960),'#252c3c');draw=ImageDraw.Draw(board)
        for i,n in enumerate([*ORDER,0]):
            f=n+int(shot)if n else 0;v=targets[f]if n else full(arc,0);rgba=np.concatenate((rgb[v].astype('uint8'),((v>0)*255).astype('uint8')[...,None]),axis=2);im=Image.fromarray(rgba,'RGBA').crop((32,36,112,112)).resize((320,304),Image.Resampling.NEAREST);x,y=i%4*320,i//4*320;board.paste(im,(x,y+16),im);draw.text((x+3,y+2),str(f)if n else'ACCEPTED IDLE',fill='white')
        board.save(out/name)
    return targets,proof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent BIN changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack_resources((PARENT/'PL02_U.ARC').read_bytes(),targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',{'task':'ultimate_armor_nana','kind':'ultimate_dash_hair','parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'generated_sha256':SOURCE_SHA,'frames':FRAMES,'registration':proof,**packed,'files':{'PL02_U.ARC':sha256(result)},'full_ultimate_complete':False});print(json.dumps({'output':str(out),'sha256':sha256(result),'verification':packed['verification']}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
