"""승인 대기의 얼굴·명암과 공통 사랑이 모듈로 벽12자세를 만든다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,require,render,write
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_nana_ultimate_run_detail import register_shaded_legs
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_ultimate_gun_size import patch_gun_base
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.prepare_shibuki_capsule_nova import raster
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_gun_size_20261104T080614586285Z'
PARENT_SHA='d542f70dd7d5146d2f508b7201096664c603f541765693888ff4f4c76a9e3f2d'
ARC_SHA='6734fbf16af4c88950a0eb5730e37ebf46775d18adba80de7a32b6e662e38b50'
SOURCE_SHA='d10e022973bba829ccd15914470b7cdcbe3f6a7439d8ff674e49ed6b82239bd5'
FRAMES=list(range(55,67));ORDER=FRAMES[::2]

def gun_records(arc):
    yy,xx=np.indices((160,160));proof=[];module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'))
    for n in ORDER:
        base=render(arc,n)[1];shot=render(arc,n+1)[1];ey,ex=np.nonzero((base==14)&(yy<85));ex=int(round(float(np.median(ex))));ey=int(round(float(np.median(ey))));xmin=int(np.nonzero((shot>0)&(xx<ex-8)&(yy<ey+12))[1].min());yp=int(np.nonzero(np.isin(shot[ey-4:ey+12,xmin:xmin+6],(5,6,7,8,9)))[0].min())+ey-4
        proof.append({'frames':[n,n+1],'eye':[ex,ey],'muzzle_anchor':[xmin,yp],'gun_module_box':[xmin,yp-1,xmin+8,yp+6],'pistol_mask_bbox':[xmin,yp-1,xmin+8,yp+6]})
    return proof,module

def correct_base(arc):
    require(sha256(arc)==ARC_SHA,'Wrong wall parent');proof,module=gun_records(arc)
    # Frame58's pistol starts at the muzzle row. Move its storage rectangle up
    # one row, counter-shifting texels, to admit the shared rear sight.
    from src.psx_player import graphics_bank,composition_frame,decode_stream,indexed_atlas
    from src.psx_bank_repack import repack_graphics_bank
    from src.psx_compress import encode_stream
    from scripts.prepare_riko_ui import replace_entry
    g,c=entry(arc,2),entry(arc,3);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][58];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;p=next(p for p in composition_frame(c,0,58)['parts'] if p['tile']==7);require(not(p['flip_x'] or p['flip_y']) and p['x']+80==57 and p['y']+80==71,'Unexpected pistol storage');require(7 not in {q['tile'] for q in composition_frame(c,0,57)['parts']},'Regular pose uses pistol tile');atlas,loc,_=indexed_atlas(raw,f['tile_count']);pix=np.frombuffer(atlas,np.uint8).reshape(-1,256);tile=pix[:16,112:128].copy();require(not np.any(tile[-1]),'Pistol bottom row occupied');moved=np.zeros_like(tile);moved[1:]=tile[:-1];data=bytearray(raw)
    for y in range(16):
        for x in range(16):
            pos,shift=loc[y*256+112+x];data[pos]=(data[pos]&~(15<<shift))|(int(moved[y,x])<<shift)
    nc=bytearray(c);nc[p['record_offset']+3]=(p['y']-1)&255;ng,_=repack_graphics_bank(g,0,{57:encode_stream(bytes(data)),58:encode_stream(bytes(data))})
    for n in (57,58):
        for cb in (0,6,7,8):require(np.array_equal(raster(g,c,0,cb,n),raster(ng,bytes(nc),0,cb,n)),'Storage adjustment moved a visible pixel')
    shifted=replace_entry(replace_entry(arc,2,ng),3,bytes(nc));result,baseproof=patch_gun_base(shifted,proof,module);baseproof.append({'frame':58,'storage_tile':7,'storage_y_delta':-1,'texel_y_delta':1,'original_display_preserved_before_module':True});return result,baseproof

def artwork(out):
    require(digest(D/'wall_v1/generated.png')==SOURCE_SHA,'Wall source changed');source=Image.open(D/'wall_v1/generated.png').convert('RGBA');arc=(PARENT/'PL02_U.ARC').read_bytes();require(sha256(arc)==ARC_SHA,'Parent ARC changed');corrected,baseproof=correct_base(arc);proof,module=gun_records(arc);words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.int32);master=full(arc,0);yy,xx=np.indices((160,160));targets={};fourth=(PARENT/'modified.arc').read_bytes()
    # Shading comes from the authored source; native feet/hand contacts set registration.
    for i,n in enumerate(ORDER):
        base=render(corrected,n)[1];shot=render(corrected,n+1)[1];q=proof[i];ex,ey=q['eye'];bottom=int(np.nonzero(base)[0].max());cell=source.crop((i%3*512,i//3*512,i%3*512+512,i//3*512+512));a=np.array(cell);labels,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labels.flat);sizes[0]=0;keep=labels==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));choices=[]
        for h in range(42,67):
            v=normalize(crop,h,rgb);vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<h//2))
            if not len(vx):continue
            cy,cx=float(np.median(vy)),float(np.median(vx));choices.append((abs((h-1-cy)-(bottom-ey)),abs(cy-16),v,cx,cy))
        require(bool(choices),'Generated eye missing');_,_,v,cx,cy=min(choices,key=lambda z:z[:2]);dx=ex-round(cx);dy=ey-round(cy);target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        # Register the authored head separately from the bent legs. Otherwise
        # short wall silhouettes shrink the ears and face below the idle scale.
        head=master[52:73,67:90].copy();target[:ey+5,ex-10:ex+15]=0;target[ey-16:ey+5,ex-9:ex+14]=head
        # Reuse the accepted small face cluster without repainting it per pose.
        target[ey-2:ey+5,ex-2:ex+7]=master[66:73,74:83]
        palm=np.isin(base,(11,12,13))&(xx>ex+8)&(yy<ey+4);lab,count=label(palm,np.ones((3,3)));require(count>0,'Native wall palm missing');k=max(range(1,count+1),key=lambda k:int(np.nonzero(lab==k)[1].max()));py,px=np.nonzero(lab==k);box=[int(px.min())-1,int(py.min())-1,int(px.max())+2,int(py.max())+2];x,y,x2,y2=box;target[y:y2,x:x2]=base[y:y2,x:x2]
        accepted=full(fourth,n);lower=(yy>=ey+17)|((xx<ex)&(yy>=ey+12));legmask=register_shaded_legs(target,base,ex,ey,np.isin(accepted,(10,11,12,13)),lower)
        dist,near=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0);require(dist[missing].max(initial=0)<=7,f'Wall {n} registration too far');target[missing]=target[near[0][missing],near[1][missing]];target[bottom+1:]=0;target[y:y2,x:x2]=base[y:y2,x:x2]
        # The firing body shares the regular silhouette; only the lowered front arm changes.
        gy,gx=np.nonzero(base!=shot);gun=(xx>=gx.min())&(xx<=min(gx.max(),ex-1))&(yy>=gy.min())&(yy<=gy.max());firing=target.copy();firing[gun]=shot[gun];mx,my=q['muzzle_anchor'];arm=(xx>=mx+8)&(xx<ex-1)&(yy>=my)&(yy<my+7)&(shot>0);firing[arm]=shot[arm]
        # Register the accepted shaded sleeve onto the native arm silhouette.
        sleeve_source=full(arc,2)[72:77,64:74]
        strip=np.array(Image.fromarray(sleeve_source).resize((max(1,ex-1-(mx+8)),5),Image.Resampling.NEAREST))
        for xcol in range(mx+8,ex-1):
            ys=np.flatnonzero(arm[:,xcol])
            if not len(ys):continue
            lo,hi=int(ys.min()),int(ys.max())
            for yrow in ys:
                firing[yrow,xcol]=1 if yrow in (lo,hi) else strip[min(4,max(0,yrow-lo-1)),xcol-mx-8]
        for yrow in range(my+1,my+6):
            left=np.flatnonzero(firing[yrow,ex-8:ex-1])+ex-8;right=np.flatnonzero(firing[yrow,ex:ex+6])+ex
            if len(left) and len(right) and 0<int(right.min()-left.max()-1)<=5:
                for xcol in range(int(left.max()+1),int(right.min())):
                    if not firing[yrow,xcol]:firing[yrow,xcol]=7
        xg,yg,xg2,yg2=q['gun_module_box'];firing[yg:yg2,xg:xg2]=module
        missing=(shot>0)&(firing==0);firing[missing]=shot[missing];firing[yg:yg2,xg:xg2]=module
        for ref,b,t in ((n,base,target),(n+1,shot,firing)):
            require(not np.any((b>0)&(t==0)),'Base escapes wall art');require(int(np.nonzero(t)[0].max())==bottom,'Wall feet moved');targets[ref]=t;save_image(t.tobytes(),(160,160),words,out/f'ultimate_{ref:03}.png')
        q.update(sole=bottom,generated_size=list(v.shape[::-1]),head_registration_size=[23,21],head_eye_to_ear_top=16,wall_contact_box=box,face_source='accepted idle head and face, exact indexed pixels',leg_shading='generated color clusters registered to accepted pose',skin_counts={str(k):int(np.count_nonzero((target==k)&legmask)) for k in (10,11,12,13)},registration_extension_pixels=int(missing.sum()),runtime_verified=False)
    for shot,name in ((False,'wall_review_4x.png'),(True,'wall_shot_review_4x.png')):
        board=Image.new('RGB',(1280,640),'#252c3c');draw=ImageDraw.Draw(board)
        for i,n in enumerate([*ORDER,0]):
            ref=n+int(shot) if n else 0;v=targets[ref] if n else master;rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);pic=Image.fromarray(rgba,'RGBA').crop((40,36,120,112)).resize((320,304),Image.Resampling.NEAREST);x=i%4*320;y=i//4*320;board.paste(pic,(x,y+16),pic);draw.text((x+5,y+3),str(ref) if n else 'ACCEPTED IDLE',fill='white')
        board.save(out/name)
    return targets,proof,corrected,baseproof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent BIN changed');out.mkdir();targets,proof,base,baseproof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack_resources(base,targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',{'task':'ultimate_armor_nana','kind':'ultimate_wall','parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'generated_sha256':SOURCE_SHA,'frames':FRAMES,'registration':proof,'base_correction':baseproof,**packed,'files':{'PL02_U.ARC':sha256(result)},'full_ultimate_complete':False});print(json.dumps({'output':str(out),'sha256':sha256(result),'verification':packed['verification']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
