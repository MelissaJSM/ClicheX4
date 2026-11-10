"""생성 원화를 공통 축척·기존 월드 위치·팔레트에 등록한다. 화소를 잘라 맞추지 않는다."""
import argparse,itertools,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_style_revision import OUT,PARENT
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.build_rin_idle import entry
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import frame_coverage
from src.sprite_window_fit import fit_windows
from scripts.build_riko_idle import LADDER_BASE_COUNTS

def bbox(a):
    y,x=np.nonzero(a);return (int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1))

def repack_windows(parts,pb,n,a,wx,wy,base_count=None):
    """같은 파츠 수와 타일 ID 안에서 16px 띠를 다시 배치한다."""
    c=composition_frame(parts,pb,n);ps=c['parts']
    if base_count is not None:ps=ps[:base_count]
    if len({p['tile'] for p in ps})!=len(ps) or len({p['clut'] for p in ps})!=1:return None
    yy,xx=np.nonzero(a);points=np.column_stack((xx+wx,yy+wy));choices=[]
    edge=[p for p in ps if p['tile']%16==0];ordinary=[p for p in ps if p['tile']%16]
    if any(p['flip_x'] for p in edge):
        fitted=fit_windows(ps,a,wx,wy)
        if fitted is None:return None
        candidate=bytearray(parts)
        for p,x,y in fitted:candidate[p['record_offset']+2]=x&255;candidate[p['record_offset']+3]=y&255
        return candidate
    for top in range(int(points[:,1].min())-15,int(points[:,1].min())+1):
        bands=list(range(top,int(points[:,1].max())+1,16))
        for edge_rows in itertools.combinations(bands,len(edge)):
            rects=[];edge_rects=[]
            for y in bands:
                xs=sorted(set(int(x) for x in points[(points[:,1]>=y)&(points[:,1]<y+16),0]))
                if y in edge_rows:
                    left=xs[0] if xs else int(points[:,0].max())+2;edge_rects.append((left-1,y));xs=[x for x in xs if x>=left+15]
                while xs:
                    left=xs[0];rects.append((left,y));xs=[x for x in xs if x>=left+16]
            if len(rects)>len(ordinary):continue
            candidate=bytearray(parts);assign=list(zip(edge,edge_rects));remaining=list(rects)
            unused=0;empty_x=max(x+16 for x,y in rects+edge_rects)+1
            for p in ordinary:
                if remaining:r=remaining.pop(0)
                else:r=(empty_x,top+16*unused);unused+=1
                assign.append((p,r))
            movement=0
            for p,(x,y) in assign:
                if not -128<=x<=127 or not -128<=y<=127:raise ValueError('Window overflow')
                candidate[p['record_offset']+2]=x&255;candidate[p['record_offset']+3]=y&255;movement+=abs(x-p['x'])+abs(y-p['y'])
            choices.append((len(rects)+len(edge),movement,candidate))
    if choices:return min(choices,key=lambda t:t[:2])[2]
    fitted=fit_windows(ps,a,wx,wy)
    if fitted is None:return None
    candidate=bytearray(parts)
    for p,x,y in fitted:
        candidate[p['record_offset']+2]=x&255;candidate[p['record_offset']+3]=y&255
    return candidate

def main():
    ap=argparse.ArgumentParser();ap.add_argument('group');ap.add_argument('--factor',type=float,default=1.0);ap.add_argument('--work',type=Path,default=OUT);ap.add_argument('--prepared',action='store_true');args=ap.parse_args()
    if not args.work.resolve().is_relative_to(ROOT/'work/ver_rin_nana/style_revision'):raise ValueError('Unexpected art directory')
    folder=args.work/args.group;guide=json.loads((folder/'guide.json').read_text('utf-8'));bi=guide['graphics_bank'];pb=guide['parts_bank']
    parent=(ROOT/guide['parent']).resolve()
    if not parent.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Unexpected guide parent')
    pm=json.loads((parent/'manifest.json').read_text('utf-8'))
    if pm['modified_bin']['sha256']!=guide['parent_sha256']:raise ValueError('Guide parent identity differs')
    arc=(parent/'modified.arc').read_bytes()
    if __import__('hashlib').sha256(arc).hexdigest()!=pm['modified_archive_sha256']:raise ValueError('Guide parent ARC changed')
    _,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<16H',pal)
    colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    bank=graphics_bank(g,bi);records={};poses={};issues=[];sheets=[];native={};parts=bytearray(parts)
    if args.prepared:
        prepared=json.loads((folder/'prepared.json').read_text('utf-8'))
        if set(prepared['frames'])!=set(guide['frames']):raise ValueError('Incomplete prepared poses')
        sheets=prepared['sheets']
        for n,rec in prepared['frames'].items():
            p=folder/rec['file']
            if digest(p)!=rec['sha256']:raise ValueError('Prepared art changed')
            im=Image.open(p)
            if im.mode!='P':raise ValueError('Indexed art required')
            poses[int(n)]=np.array(im);records[n]=dict(rec)
    for si,s in enumerate([] if args.prepared else guide['sheets']):
        source=folder/f'generated_{si}.png';im=Image.open(source).convert('RGBA');crops={};ratios=[]
        # Generation can shift a pose across the nominal cell border. Segment
        # the actual alpha silhouettes first; cell clipping would steal a foot
        # from the row above and mistake it for a disconnected hand below.
        small=np.array(im.getchannel('A'))[::4,::4]>=128
        components=connected_groups(small)[:len(s['frames'])]
        if len(components)!=len(s['frames']):raise ValueError('Missing source silhouettes')
        boxes=[]
        for q in components:
            yy,xx=q[:,0],q[:,1];boxes.append((max(0,int(xx.min())*4-4),max(0,int(yy.min())*4-4),min(im.width,int(xx.max())*4+8),min(im.height,int(yy.max())*4+8)))
        boxes.sort(key=lambda b:((b[1]+b[3])/2))
        boxes=[b for start in range(0,len(boxes),s['columns']) for b in sorted(boxes[start:start+s['columns']],key=lambda b:b[0])]
        for i,n in enumerate(s['frames']):
            box=boxes[i]
            crop=im.crop(box);a=np.array(crop);a[:,:,3]=np.where(a[:,:,3]>=128,a[:,:,3],0);crop=Image.fromarray(a)
            b=crop.getbbox()
            if b is None:raise ValueError(f'Missing generated pose {n}')
            crop=crop.crop(b);old=np.array(Image.open(folder/guide['frames'][str(n)]['before']));ob=bbox(old)
            ratios.append((ob[3]-ob[1])/crop.height);crops[n]=crop
        scale=float(np.median(ratios))*args.factor
        for n,crop in crops.items():
            a=quantize(crop,colors,scale)
            if not np.any(a==15) and args.group!='hurt':
                rgba=np.asarray(crop);rgb=rgba[:,:,:3].astype(np.int32);yy,xx=np.indices(rgba.shape[:2]);mask=(rgba[:,:,3]>=128)&(rgb[:,:,0]<100)&(rgb[:,:,1]>120)&(rgb[:,:,2]>140)&(yy<rgba.shape[0]*.55)
                eye_groups=connected_groups(mask)
                if eye_groups and len(eye_groups[0])>=3:
                    ey,ex=eye_groups[0].mean(axis=0);ey=min(a.shape[0]-1,round(ey*scale));ex=min(a.shape[1]-1,round(ex*scale))
                    if a[ey,ex]:a[ey,ex]=15
            gs=connected_groups(a>0);clean=np.zeros_like(a);q=gs[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]]
            # Preserve significant detached features for review, never silently
            # discard a hand, cuff or foot to make the coverage check pass.
            for q in gs[1:]:
                if len(q)>3:clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]]
            removed=[len(q) for q in gs[1:]]
            if any(k>3 for k in removed):issues.append({'frame':n,'detached_generated_components':removed})
            x0,y0,x1,y1=bbox(clean);a=clean[y0:y1,x0:x1];poses[n]=a
            save_image(a.tobytes(),(a.shape[1],a.shape[0]),words,folder/f'unregistered_{n:03d}.png')
            records[str(n)]={'sheet':si,'uniform_scale':scale,'source_sha256':digest(source),'native_size':[a.shape[1],a.shape[0]],'discarded_alpha_noise':removed}
        sheets.append({'source':source.name,'sha256':digest(source),'uniform_scale':scale,'per_pose_resizing':False})
    for n,key in guide['aliases'].items():poses[int(n)]=poses[key];records[n]={'alias':key}
    for n,a in poses.items():
        old=np.array(Image.open(folder/guide['frames'][str(guide['aliases'].get(str(n),n))]['before']));oldb=guide['frames'][str(guide['aliases'].get(str(n),n))]['bounds'];ob=bbox(old)
        h,w=a.shape;target_y=oldb[1]+ob[3]-h
        # Align the head without altering the relative pose geometry. Face index
        # is used only if present in both; otherwise center of upper silhouette.
        oy,ox=np.nonzero((old==15)&(np.indices(old.shape)[0]<ob[1]+22));ay,ax=np.nonzero((a==15)&(np.indices(a.shape)[0]<min(h,22)))
        target_x=round(float(ox.mean())+oldb[0]-float(ax.mean())) if len(ox) and len(ax) else round(oldb[0]+(ob[0]+ob[2]-w)/2)
        if args.group=='rise' and n in (148,150,152,154):
            # Rising flame attaches to the raised grip, not the ribbon or
            # silhouette center. Align that topmost original hand landmark.
            oyy,oxx=np.nonzero(old[ob[1]:ob[1]+2]>0)
            ayy,axx=np.nonzero(a[:2]>0)
            target_x=round(oldb[0]+float(oxx.mean())-float(axx.mean()))
            target_y=oldb[1]+ob[1]
        f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;c=composition_frame(parts,pb,n)
        def evaluate(c,dx,dy):
            if args.group=='ladder' and n in LADDER_BASE_COUNTS:c={**c,'parts':c['parts'][:LADDER_BASE_COUNTS[n]]}
            coverage,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in coverage]).reshape(size[1],size[0])
            for p in c['parts']:
                if p['tile']%16==0:
                    col=p['x']-bounds[0]+(15 if p['flip_x'] else 0)
                    safe[p['y']-bounds[1]:p['y']-bounds[1]+16,col]=False
            x=target_x+dx-bounds[0];y=target_y+dy-bounds[1];px=np.zeros((size[1],size[0]),np.uint8)
            l=max(0,x);t=max(0,y);r=min(size[0],x+w);b=min(size[1],y+h)
            if l<r and t<b:px[t:b,l:r]=a[t-y:b-y,l-x:r-x]
            bad=int(np.count_nonzero(a)-np.count_nonzero(px)+np.count_nonzero((px>0)&~safe))
            return bad,px,size,bounds
        options=[]
        for dy in (-1,0,1):
            for dx in range(-3,4):
                bad,px,size,bounds=evaluate(c,dx,dy);options.append((bad,abs(dx)+3*abs(dy),dx,dy,px,size,bounds))
        bad,_,dx,dy,px,size,bounds=min(options,key=lambda t:t[:2])
        # Existing disjoint horizontal tile windows may translate to contain the
        # redrawn outline. This never changes pixels, tile IDs, flags or timing.
        edits=[]
        if bad and args.group not in ('hurt','ladder','spin'):
            rows={}
            for p in c['parts']:rows.setdefault(p['y'],[]).append(p)
            candidate=bytearray(parts)
            for y,row in rows.items():
                yy0=max(0,y-target_y);yy1=min(h,y+16-target_y)
                if yy0>=yy1:continue
                yy,xx=np.nonzero(a[yy0:yy1]);
                if not len(xx):continue
                required=(target_x+int(xx.min()),target_x+int(xx.max()))
                lo=min(p['x']+(1 if p['tile']%16==0 and not p['flip_x'] else 0) for p in row);hi=max(p['x']+15-(1 if p['tile']%16==0 and p['flip_x'] else 0) for p in row)
                delta=max(required[1]-hi,min(0,required[0]-lo))
                if abs(delta)<=8:
                    for p in row:candidate[p['record_offset']+2]=(p['x']+delta)&255
            cc=composition_frame(candidate,pb,n)
            opts=[]
            for dy0 in (-1,0,1):
                for dx0 in range(-3,4):
                    val=evaluate(cc,dx0,dy0);opts.append((val[0],abs(dx0)+3*abs(dy0),dx0,dy0,*val[1:]))
            revised=min(opts,key=lambda t:t[:2])
            if revised[0]<bad:
                bad,_,dx,dy,px,size,bounds=revised
                edits=[{'offset':i,'before':x,'after':y} for i,(x,y) in enumerate(zip(parts,candidate)) if x!=y];parts=candidate
        if bad:
            candidate=repack_windows(parts,pb,n,a,target_x,target_y,LADDER_BASE_COUNTS.get(n) if args.group=='ladder' else None) if args.group!='spin' else None
            if candidate is not None:
                val=evaluate(composition_frame(candidate,pb,n),0,0)
                if val[0]<bad:
                    bad,px,size,bounds=val;dx=dy=0
                    edits=[{'offset':i,'before':x,'after':y} for i,(x,y) in enumerate(zip(parts,candidate)) if x!=y];parts=candidate
        if bad and args.group!='spin':
            fit_parts=composition_frame(parts,pb,n)['parts']
            if args.group=='ladder' and n in LADDER_BASE_COUNTS:fit_parts=fit_parts[:LADDER_BASE_COUNTS[n]]
            fitted=fit_windows(fit_parts,a,target_x,target_y)
            if fitted is not None:
                candidate=bytearray(parts)
                for p,x,y in fitted:
                    candidate[p['record_offset']+2]=x&255;candidate[p['record_offset']+3]=y&255
                val=evaluate(composition_frame(candidate,pb,n),0,0)
                if val[0]<bad:
                    bad,px,size,bounds=val;dx=dy=0
                    edits=[{'offset':i,'before':x,'after':y} for i,(x,y) in enumerate(zip(parts,candidate)) if x!=y];parts=candidate
        if bad:
            # Move the EXISTING rectangular sampling windows as complete rows;
            # the world-space sprite is neither cropped nor distorted.
            rows={}
            for p in c['parts']:rows.setdefault(p['y'],[]).append(p)
            ordered=sorted(rows)
            if args.group not in ('ladder','spin') and all(b-a>=16 for a,b in zip(ordered,ordered[1:])):
                alternatives=[]
                for sy in range(-6,7):
                    candidate=bytearray(parts);movement=abs(sy)*len(c['parts'])
                    for row,ps in rows.items():
                        y0=max(0,row+sy-target_y);y1=min(h,row+sy+16-target_y)
                        if y0>=y1:continue
                        yy,xx=np.nonzero(a[y0:y1]);xx=xx+target_x
                        shifts=[]
                        for sx in range(-16,17):
                            covered=np.zeros(len(xx),bool)
                            for p in ps:
                                covered|=(xx>=p['x']+sx+(1 if p['tile']%16==0 and not p['flip_x'] else 0))&(xx<p['x']+sx+16-(1 if p['tile']%16==0 and p['flip_x'] else 0))
                            shifts.append((int(np.count_nonzero(~covered)),abs(sx),sx))
                        rowbad,_,sx=min(shifts);movement+=abs(sx)*len(ps)
                        for p in ps:
                            candidate[p['record_offset']+2]=(p['x']+sx)&255
                    for p in c['parts']:candidate[p['record_offset']+3]=(p['y']+sy)&255
                    cc=composition_frame(candidate,pb,n);val=evaluate(cc,0,0)
                    alternatives.append((val[0],movement,candidate,*val[1:]))
                best=min(alternatives,key=lambda t:t[:2])
                if best[0]<bad:
                    bad,_,candidate,px,size,bounds=best;dx=dy=0
                    edits=[{'offset':i,'before':x,'after':y} for i,(x,y) in enumerate(zip(parts,candidate)) if x!=y];parts=candidate
        if bad:
            issues.append({'frame':n,'outside_safe_parts':bad,'native_size':[w,h],'world_placement':[target_x+dx,target_y+dy],'part_rows':[[p['tile'],p['x'],p['y']] for p in composition_frame(parts,pb,n)['parts']]})
        path=folder/f'frame_{n:03d}.png';save_image(px.tobytes(),size,words,path);native[n]=(px,size,bounds)
        records[str(n)].update({'file':path.name,'sha256':digest(path),'bounds':bounds,'registration':[target_x+dx,target_y+dy],'opaque_pixels':int(np.count_nonzero(px)),'outside_safe_parts':bad,'composition_x_edits':edits})
    cols=4;cell=112;board=Image.new('RGB',(cols*cell*3,((len(native)+cols-1)//cols)*cell*3),(35,38,48));draw=ImageDraw.Draw(board)
    for i,(n,(px,size,bounds)) in enumerate(native.items()):
        pic=Image.open(folder/records[str(n)]['file']).convert('RGBA');canvas=Image.new('RGBA',(cell,cell));canvas.alpha_composite(pic,(56+bounds[0],56+bounds[1]));canvas=canvas.resize((cell*3,cell*3),Image.Resampling.NEAREST);xy=(i%cols*cell*3,i//cols*cell*3);board.paste(canvas,xy,canvas);draw.text((xy[0]+8,xy[1]+8),str(n),fill='white')
    board.save(folder/'registered_3x.png');(folder/'composition_entry.bin').write_bytes(parts)
    report={'parent':guide['parent'],'parent_sha256':guide['parent_sha256'],'graphics_bank':bi,'parts_bank':pb,'frames':records,'sheets':sheets,'issues':issues,'composition_sha256':digest(folder/'composition_entry.bin'),'applied':False}
    (folder/'registered.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps({'group':args.group,'scales':[s['uniform_scale'] for s in sheets],'issues':issues}))

if __name__=='__main__':main()
