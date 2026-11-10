"""린 이동 시트를 하나의 배율·팔레트로 정규화하고 원작 파츠에 등록한다."""
import json,struct,sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.prepare_riko_jump import components
from scripts.prepare_rin_idle import PILOT
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_indices
from src.psx_compress import encode_stream

OUT=ROOT/'work/ver_rin_nana/run_production/v1'
IDS=(3,4,*range(7,21));SCALE=.1875

def connected_groups(mask):
    mask=mask.copy();groups=[]
    while mask.any():
        y,x=np.argwhere(mask)[0];todo=deque([(int(y),int(x))]);mask[y,x]=False;points=[]
        while todo:
            y,x=todo.popleft();points.append((y,x))
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    yy,xx=y+dy,x+dx
                    if 0<=yy<mask.shape[0] and 0<=xx<mask.shape[1] and mask[yy,xx]:
                        mask[yy,xx]=False;todo.append((yy,xx))
        groups.append(np.array(points))
    return sorted(groups,key=len,reverse=True)

def register_head_attachments(pixels,left,top):
    """머리 교체로 떨어진 생성 리본을 확대·축소 없이 원래 매듭에 등록한다."""
    a=pixels.copy();groups=connected_groups(a>0);shifts=[]
    main=np.zeros(a.shape,bool);main[groups[0][:,0],groups[0][:,1]]=True
    for points in groups[1:]:
        yy,xx=points[:,0],points[:,1];values=a[yy,xx].copy()
        if np.isin(values,(12,13,14)).any() or xx.min()<left+10 or yy.min()>top+19:raise ValueError('Unexpected detached body instead of head attachment')
        a[yy,xx]=0
        # Connect to the right-hand hair/bonnet attachment, preserving every master pixel.
        anchor=main.copy();anchor[:,:left+11]=False;anchor[top+19:]=False
        adjacent=np.zeros_like(main)
        for dy in (-1,0,1):
            for dx in (-1,0,1):adjacent|=np.roll(np.roll(anchor,dy,axis=0),dx,axis=1)
        options=[]
        for dy in range(-6,7):
            for dx in range(-6,7):
                ny,nx=yy+dy,xx+dx
                if ny.min()<0 or nx.min()<0 or ny.max()>=a.shape[0] or nx.max()>=a.shape[1]:continue
                if np.any(a[ny,nx]) or not np.any(adjacent[ny,nx]):continue
                options.append((abs(dx)+abs(dy),abs(dy),abs(dx),dy,dx))
        if not options:raise ValueError('Ribbon needs an art revision, not pixel clipping')
        *_,dy,dx=min(options);ny,nx=yy+dy,xx+dx;a[ny,nx]=values;main[ny,nx]=True
        shifts.append({'pixel_count':len(points),'dx':dx,'dy':dy,'pixels_preserved':True})
    if len(connected_groups(a>0))!=1:raise ValueError('Body/ribbon still detached')
    return a,shifts

def quantize(crop,colors,scale=SCALE):
    full=np.array(crop);w,h=round(crop.width*scale),round(crop.height*scale)
    nearest=np.zeros(full.shape[:2],np.uint8)
    for y in range(crop.height):nearest[y]=np.argmin(np.sum((full[y,:,:3].astype(np.int32)[:,None]-colors[None])**2,axis=2),axis=1)+1
    votes=[np.array(Image.fromarray(np.where(nearest==i,full[:,:,3],0).astype(np.uint8)).resize((w,h),Image.Resampling.BOX)) for i in range(1,16)]
    alpha=np.array(crop.getchannel('A').resize((w,h),Image.Resampling.BOX))
    return np.where(alpha>=128,np.argmax(np.stack(votes),axis=0)+1,0).astype(np.uint8)

def main():
    source=OUT/'generated_run.png';im=Image.open(source).convert('RGBA');crops=components(im,16)
    crops.sort(key=lambda c:(int((c[0][1]+c[0][3])/2*4/im.height),c[0][0]))
    e=ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z';g=(e/'graphics_entry.bin').read_bytes();p=(e/'composition_entry.bin').read_bytes();bank=graphics_bank(g,0)
    # Keep the new pose intact: move the two existing lower-leg tile windows.
    # Counts, flags, bank size, animation and player collision remain unchanged.
    old_parts=p;p=bytearray(p);part_edits=[]
    for q in composition_frame(p,0,9)['parts'][-2:]:
        offset=q['record_offset']+2;before=p[offset];p[offset]=(q['x']+10)&255
        part_edits.append({'frame':9,'part':q['index'],'offset':offset,'before':before,'after':p[offset],'x_before':q['x'],'x_after':q['x']+10})
    p=bytes(p)
    words=struct.unpack('<16H',(PILOT/'candidate_palette.bin').read_bytes());colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],np.int32)
    master_head=np.array(Image.open(PILOT/'rin_idle147_indexed.png'))[:18,14:36]
    contact=Image.open(OUT/'generated_contact_fix.png').convert('RGBA');contact_crops=components(contact,4)
    contact_crops.sort(key=lambda c:(int((c[0][1]+c[0][3])/2*2/contact.height),c[0][0]))
    overrides=dict(zip((9,10,16,17),contact_crops));contact_scale=128/contact.width
    records={};issues=[];previews={};font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
    for n,(box,crop) in zip(IDS,crops):
        scale=SCALE
        if n in overrides:box,crop=overrides[n];scale=contact_scale
        a=quantize(crop,colors,scale)
        eye_y,eye_x=np.nonzero((a==15)&(np.indices(a.shape)[0]<a.shape[0]*.45))
        if not len(eye_x):raise ValueError(f'Eye registration missing {n}')
        ex0,ey0=round(float(eye_x.mean())),round(float(eye_y.mean()))
        pad=np.pad(a,((24,24),(24,24)));left=24+ex0-8;top=24+ey0-10
        pad[:top+18,left:left+22]=0;pad[top:top+18,left:left+22]=master_head
        pad,attachment_shifts=register_head_attachments(pad,left,top)
        yy,xx=np.nonzero(pad);a=pad[yy.min():yy.max()+1,xx.min():xx.max()+1]
        h,w=a.shape;f=bank['frames'][n];c=composition_frame(p,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cover,size,bounds=frame_coverage(raw,f['tile_count'],c)
        safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]]=False
        ry,rx=np.indices(a.shape);face=(a==15)&(ry<h*.4);ey,ex=np.nonzero(face)
        if not len(ex):raise ValueError(f'No face registration in {n}')
        face_center=[float(ex.mean()),float(ey.mean())];ideal_x=(-2 if n in (3,4) else -6)-bounds[0]-face_center[0]
        old,_,_,_=compose_indices(raw,f['tile_count'],c);old=np.frombuffer(old,np.uint8).reshape(size[1],size[0]);old_y=np.nonzero(old)[0];target_floor=min(23,int(old_y.max())+bounds[1]+1)
        ideal_y=target_floor-bounds[1]-(h-1)
        options=[]
        for y in range(max(0,size[1]-h+1)):
            for x in range(max(0,size[0]-w+1)):
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));score=abs(x-ideal_x)+2*abs(y-ideal_y)
                options.append((bad,score,x,y))
        if not options:issues.append({'frame':n,'reason':'canvas_size','native_size':[w,h],'canvas':size});continue
        bad,score,x,y=min(options)
        canvas=np.zeros((size[1],size[0]),np.uint8);canvas[y:y+h,x:x+w]=a
        preview=save_image(canvas.tobytes(),size,words,OUT/f'candidate_{n:03}.png')
        tile=Image.new('RGBA',(64,64));tile.alpha_composite(preview.convert('RGBA'),(32+bounds[0],32+bounds[1]));previews[n]=tile
        if bad:issues.append({'frame':n,'reason':'outside_safe_parts','pixels':bad,'placement':[x,y],'native_size':[w,h],'world_face':[round(x+bounds[0]+face_center[0],2),round(y+bounds[1]+face_center[1],2)]});continue
        packed=edit_frame_indices(raw,f['tile_count'],c,canvas.tobytes(),size);code=encode_stream(packed)
        # A world anchor is independent of transparent canvas bounds. Keep the
        # accepted face at one horizontal anchor across the complete run cycle.
        head_x=x+bounds[0]+face_center[0];desired=-2 if n in (3,4) else -8
        shift_x=round(desired-head_x)
        if shift_x:
            updated=bytearray(p)
            for q in c['parts']:
                offset=q['record_offset']+2;value=q['x']+shift_x
                if not -128<=value<=127:raise ValueError('Part coordinate overflow')
                updated[offset]=value&255
            p=bytes(updated);bounds=(bounds[0]+shift_x,bounds[1],bounds[2]+shift_x,bounds[3])
            tile=Image.new('RGBA',(64,64));tile.alpha_composite(preview.convert('RGBA'),(32+bounds[0],32+bounds[1]));previews[n]=tile
        path=OUT/f'frame_{n:03}.png';save_image(canvas.tobytes(),size,words,path)
        records[str(n)]={'file':path.name,'sha256':digest(path),'source_box':box,'source_sheet':'generated_contact_fix.png' if n in overrides else 'generated_run.png','uniform_sheet_scale':scale,'size':[w,h],'placement':[x,y],'bounds':bounds,'head_face_world':[x+bounds[0]+face_center[0],y+bounds[1]+face_center[1]],'floor':y+bounds[1]+h-1,'encoded_bytes':len(code),'budget':f['limit']-f['offset'],'outside_pixels':0,'mirror_boundary_pixels':0,'head_attachment_registration':attachment_shifts,'connected_components':1}
    board=Image.new('RGB',(1024,1120),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(IDS):
        if n not in previews:continue
        pic=previews[n].resize((256,256),Image.Resampling.NEAREST);board.paste(pic,(i%4*256,i//4*280+24),pic);draw.text((i%4*256+8,i//4*280+2),str(n),font=font,fill='white')
    board.save(OUT/'run_review_4x.png')
    ticks=[2,3,2,2,2,3,2]*2;elapsed=0;duration=[]
    for tick in ticks:
        old_time=round(elapsed*100/60)*10;elapsed+=tick;duration.append(round(elapsed*100/60)*10-old_time)
    if all(n in previews for n in range(7,21)):
        for slow in (1,4):
            seq=[]
            for n in range(7,21):
                a=Image.new('RGB',(256,256),(35,38,48));pic=previews[n].resize((256,256),Image.Resampling.NEAREST);a.paste(pic,(0,0),pic);seq.append(a)
            seq[0].save(OUT/f'run_preview_{slow}time.gif',save_all=True,append_images=seq[1:],duration=[t*slow for t in duration],loop=0)
    # Braking uses the accepted stance on the original two stop references.
    for n in (5,6):
        frame=bank['frames'][n];comp=composition_frame(p,0,n);raw=decode_stream(g,frame['offset'],frame['limit'],frame['tile_count']*128).data
        pic=Image.open(PILOT/'rin_idle147_indexed.png');packed=edit_frame_indices(raw,frame['tile_count'],comp,pic.tobytes(),pic.size)
        path=OUT/f'frame_{n:03}.png';pic.save(path,transparency=0)
        records[str(n)]={'file':path.name,'sha256':digest(path),'source_sheet':'accepted_idle147','encoded_bytes':len(encode_stream(packed)),'budget':frame['limit']-frame['offset']}
    (OUT/'composition_entry.bin').write_bytes(p)
    part_edits=[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(old_parts,p)) if a!=b]
    report={'project':'ver_rin_nana','source':'generated_run.png','source_sha256':digest(source),'prompt':'prompt_run.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resize':False,'frames':records,'issues':issues,'run_sequence':list(range(7,21)),'run_ticks':ticks,'runtime_verified':False,'palette_sha256':digest(PILOT/'candidate_palette.bin'),'composition_edits':part_edits,'composition_sha256':digest(OUT/'composition_entry.bin'),'contact_source':'generated_contact_fix.png','contact_sha256':digest(OUT/'generated_contact_fix.png'),'contact_prompt':'prompt_contact_fix.txt','contact_uniform_scale':contact_scale,'master_head_source':'approved idle147, rectangle [14,0,36,18]','head_native_pixels_preserved':True,'run_eye_world_x':-8,'start_eye_world_x':-2,'part_change_scope':'original part counts/order/flags/tile IDs unchanged; nine-frame lower tile windows and per-frame whole-body horizontal registration only'}
    (OUT/'run_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'ready':len(records),'issues':issues,'compression':{n:[r['encoded_bytes'],r['budget']] for n,r in records.items()}}))

if __name__=='__main__':main()
