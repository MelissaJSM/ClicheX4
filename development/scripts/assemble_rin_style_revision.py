"""대기 기준 재제작 몸체를 공유 타일에 결속하고 ARC 사본을 검증한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_style_revision import OUT,PARENT
from scripts.register_rin_style_revision import repack_windows,bbox
from scripts.build_rin_idle import entry,sha
from scripts.project import digest
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from scripts.build_riko_idle import LADDER_BASE_COUNTS
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas
from src.psx_hurt_launch import compose_launch,MULTI_FRAMES,local_layer
from src.psx_frame_edit import frame_coverage,_requested_writes,_apply_writes
from src.psx_compress import replace_stream,encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.rin_hurt import derive as derive_hurt
from src.rin_effects import arrival_flash,departure_flash,ice_flash
from src.psx_beam_in import foot_contacts
from src.psx_air_spin import ROTATING
from src.psx_hurt import flash_from_body

FIXED={0:{0,1,2,5,6,146,147,148},1:{0,86}}
GROUPS=['run','air','dash','wall','hurt','ground','air_slash','wall_saber','ladder','arrival','victory','spin','ice']
DEST=OUT/'assembled'

def to_world(frame,b):
    data,size=frame;a=np.frombuffer(data,np.uint8).reshape(size[1],size[0]);w=np.zeros((192,192),np.uint8);w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=a;return w

def arrival_anchor(world):
    """Closed boots form one contact; wide stances retain the two-foot measure."""
    yy,xx=np.nonzero(world)
    if not len(xx):raise ValueError('Empty arrival stance')
    floor=int(yy.max());columns=sorted(set(map(int,xx[yy>=floor-2])));groups=[]
    for x in columns:
        if not groups or x>groups[-1][-1]+1:groups.append([])
        groups[-1].append(x)
    if len(groups) not in (1,2):raise ValueError('Unexpected arrival ground contacts')
    contacts=[(g[0]+g[-1])/2-96 for g in groups]
    return {'center_x':sum(contacts)/len(contacts),'floor_y':floor-96,'contact_count':len(groups)}

def prepare(work=None):
    global OUT,DEST
    if work is not None:
        work=Path(work).resolve()
        if not work.is_relative_to(ROOT/'work/ver_rin_nana/style_revision'):raise ValueError('Unexpected work directory')
        OUT=work;DEST=OUT/'assembled'
    DEST.mkdir(exist_ok=True)
    frozen=json.loads((OUT/'master.json').read_text('utf-8'));pm=json.loads((PARENT/'manifest.json').read_text('utf-8'))
    if digest(OUT/frozen['master_file'])!=frozen['master_sha256']:raise ValueError('Master changed')
    arc=(PARENT/'modified.arc').read_bytes()
    if sha(arc)!=pm['modified_archive_sha256']:raise ValueError('Parent ARC changed')
    gm,g=entry(arc,2);cm,oldparts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<64H',pal);parts=bytearray(oldparts);worlds={0:{},1:{}};owners={};issues=[]
    expected={0:set(pm['cumulative_frames'])-FIXED[0],1:set(pm['cumulative_bank1_frames'])-FIXED[1]}
    for group in GROUPS:
        folder=OUT/group;r=json.loads((folder/'registered.json').read_text('utf-8'))
        if r['issues']:raise ValueError(f'Unresolved art {group}: {r["issues"]}')
        ps=(folder/'composition_entry.bin').read_bytes()
        if digest(folder/'composition_entry.bin')!=r['composition_sha256']:raise ValueError('Recipe composition changed')
        for i,(a,b) in enumerate(zip(oldparts,ps)):
            if a!=b:
                if parts[i] not in (a,b):raise ValueError('Cross-group composition conflict')
                parts[i]=b
        for n,rec in r['frames'].items():
            p=folder/rec['file'];im=Image.open(p)
            if digest(p)!=rec['sha256']:raise ValueError('Art input changed')
            bi=r['graphics_bank'];worlds[bi][int(n)]=to_world((im.tobytes(),im.size),rec['bounds']);owners[bi,int(n)]=group
    def native(n,bi=0,ps=None,gfx=None):
        gfx=g if gfx is None else gfx;ps=parts if ps is None else ps;f=graphics_bank(gfx,bi)['frames'][n];c=composition_frame(ps,0 if bi==0 else 5,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        return f,c,raw,compose_launch(raw,f['tile_count'],c)
    def original_world(n,bi=0):return to_world(native(n,bi,oldparts)[3][:2],native(n,bi,oldparts)[3][2])
    for n,key in ((23,22),(30,29),(32,31)):worlds[0][n]=worlds[0][key].copy()
    for n,key in ((42,41),(43,41)):worlds[0][n]=worlds[0][key].copy()
    for n in range(149,155):worlds[0][n]=worlds[0][149 if n<152 else 152].copy()
    # Preserve the landing/idle ground anchor, without forcing the boot span.
    arrival_contacts={}
    idle=native(147,0,oldparts)[3];target=foot_contacts(idle[:2],idle[2])
    for n in range(249,254):
        w=worlds[0][n];contact=arrival_anchor(w);dx=round(target['center_x']-contact['center_x']);dy=target['floor_y']-contact['floor_y'];worlds[0][n]=np.roll(np.roll(w,dx,axis=1),dy,axis=0);arrival_contacts[n]={'dx':dx,'dy':dy,'contacts':contact['contact_count']}
    for n in (247,248):worlds[0][n]=np.frombuffer(arrival_flash((worlds[0][249].tobytes(),(192,192)),(-96,-96,96,96),(192,192),(-96,-96,96,96),n)[0],np.uint8).reshape(192,192)
    for n in (7,8):worlds[1][n]=np.frombuffer(departure_flash((worlds[1][3].tobytes(),(192,192)),(-96,-96,96,96),(192,192),(-96,-96,96,96),n)[0],np.uint8).reshape(192,192)
    for i,n in enumerate(ROTATING):worlds[1][n]=np.array(Image.fromarray(worlds[1][161]).rotate(i*45,Image.Resampling.NEAREST,center=(96,96)))
    worlds[1][132]=worlds[0][229].copy();worlds[1][160]=worlds[0][213].copy()
    for n in (87,95,96,98,99):worlds[1][n]=worlds[0][246].copy()
    worlds[1][88]=np.frombuffer(ice_flash((worlds[1][87].tobytes(),(192,192)))[0],np.uint8).reshape(192,192)
    worlds[1][133]=np.roll(worlds[1][134],1,axis=0)
    for n in (136,137):worlds[1][n]=worlds[1][134].copy()
    worlds[1][135][96:]=worlds[1][134][96:]
    for n in (139,141,142,143):worlds[1][n]=worlds[1][140].copy()
    for n,base in ((138,135),(142,139)):
        worlds[0][n]=np.frombuffer(flash_from_body((worlds[0][base].tobytes(),(192,192)),(-96,-96,96,96),(192,192),(-96,-96,96,96),fill_index=10,outline_index=11)[0],np.uint8).reshape(192,192)
    worlds[0][143]=np.where(worlds[0][139]>0,15,0).astype(np.uint8)
    worlds[0][144]=worlds[0][139].copy()
    # Sampling windows alone can change. Pixels remain fixed in world space.
    def place(n,bi,world,allow_fit=True):
        nonlocal parts
        f,c,raw,_=native(n,bi)
        def check(c):
            if bi==0 and n in LADDER_BASE_COUNTS:c={**c,'parts':c['parts'][:LADDER_BASE_COUNTS[n]]}
            if any(p['clut'] for p in c['parts']):c=local_layer(c,c['parts'])
            cov,sz,bb=frame_coverage(raw,f['tile_count'],c);px=world[96+bb[1]:96+bb[3],96+bb[0]:96+bb[2]].copy();bad=int(np.count_nonzero(world)-np.count_nonzero(px));safe=np.array([bool(s) for s in cov]).reshape(sz[1],sz[0])
            for p in c['parts']:
                if p['tile']%16==0:safe[p['y']-bb[1]:p['y']-bb[1]+16,p['x']-bb[0]+(15 if p['flip_x'] else 0)]=False
            bad+=int(np.count_nonzero((px>0)&~safe));return bad,px,sz,bb
        bad,px,size,b=check(c)
        if bad and allow_fit:
            rowparts={}
            for p in c['parts']:rowparts.setdefault(p['y'],[]).append(p)
            candidate=bytearray(parts)
            for row,ps in rowparts.items():
                best=(bad,0,candidate)
                for shift in range(-8,9):
                    trial=bytearray(candidate)
                    for p in ps:trial[p['record_offset']+2]=(p['x']+shift)&255
                    value=check(composition_frame(trial,0 if bi==0 else 5,n))[0]
                    if (value,abs(shift))<best[:2]:best=(value,abs(shift),trial)
                candidate=best[2]
            val=check(composition_frame(candidate,0 if bi==0 else 5,n))
            if val[0]<bad:parts=candidate;bad,px,size,b=val
        if bad and allow_fit:
            yy,xx=np.nonzero(world);x0,y0=int(xx.min()),int(yy.min());a=world[y0:int(yy.max())+1,x0:int(xx.max())+1];candidate=repack_windows(parts,0 if bi==0 else 5,n,a,x0-96,y0-96,LADDER_BASE_COUNTS.get(n) if bi==0 else None)
            if candidate is not None:
                val=check(composition_frame(candidate,0 if bi==0 else 5,n))
                if val[0]<bad:parts=candidate;bad,px,size,b=val
        if bad:raise ValueError(f'World art escapes {bi}:{n} by {bad} pixels')
        return px.tobytes(),size
    frames={0:{},1:{}}
    pose_bindings=[]
    def bind_pose(target,source,mirror=False):
        """A shared bitmap is one authored pose, optionally mirrored by the game."""
        src=composition_frame(parts,0,source)['parts'];dst=composition_frame(parts,0,target)['parts']
        if source in LADDER_BASE_COUNTS:src=src[:LADDER_BASE_COUNTS[source]]
        if target in LADDER_BASE_COUNTS:dst=dst[:LADDER_BASE_COUNTS[target]]
        if len(dst)<len(src):raise ValueError('Alias lacks sufficient sampling windows')
        mapping={};used=set()
        for p in dst:
            matches=[i for i,q in enumerate(src) if q['tile']==p['tile']]
            if matches:mapping[p['record_offset']]=matches[0];used.add(matches[0])
        for p in sorted(dst,key=lambda p:p['tile']%16!=0):
            if p['record_offset'] in mapping:continue
            options=[i for i,q in enumerate(src) if i not in used and (p['tile']%16!=0 or q['tile']%16==0)]
            if not options:options=[i for i,q in enumerate(src) if p['tile']%16!=0 or q['tile']%16==0]
            if not options:raise ValueError('Alias cannot preserve U0 edge')
            i=min(options,key=lambda i:abs(src[i]['x']-p['x'])+abs(src[i]['y']-p['y']))
            mapping[p['record_offset']]=i;used.add(i)
        if len(used)!=len(src):raise ValueError('Alias leaves a source window uncovered')
        for p in dst:
            q=src[mapping[p['record_offset']]]
            if (p['flip_x']!=q['flip_x'])!=mirror or p['flip_y']!=q['flip_y']:raise ValueError('Alias orientation mismatch')
            x=-q['x']-16 if mirror else q['x'];y=q['y']
            parts[p['record_offset']+2]=x&255;parts[p['record_offset']+3]=y&255
        worlds[0][target]=np.fliplr(worlds[0][source]).copy() if mirror else worlds[0][source].copy()
        pose_bindings.append({'target':target,'source':source,'mirror_x':mirror})
    if frozen.get('accepted_stride'):
        for target,source in ((47,46),(48,46),(81,79),(93,91),(95,97),(201,199),(204,202),(208,206),(210,206)):
            bind_pose(target,source)
        for source,targets in ((174,[(175,False),(176,True),(177,True)]),(178,[(179,False),(180,True),(181,True)]),(182,[(183,False),(184,True),(185,True)]),(186,[(187,True),(188,False),(189,True)])):
            for target,mirror in targets:bind_pose(target,source,mirror)
    layout_aliases={0:{23:22,30:29,32:31,42:41,43:41,101:99},1:{53:51,96:95,99:98,136:134,137:136}}
    def align_alias(n,source,bi):
        pb=0 if bi==0 else 5;old_source=composition_frame(oldparts,pb,source)['parts'];new_source=composition_frame(parts,pb,source)['parts'];old_target=composition_frame(oldparts,pb,n)['parts'];new_target=composition_frame(parts,pb,n)['parts']
        for old,current in zip(old_target,new_target):
            choices=[]
            for a,b in zip(old_source,new_source):
                if a['flags']!=old['flags']:continue
                score=abs(a['x']-old['x'])+abs(a['y']-old['y'])*3
                choices.append((score,a,b))
            score,a,b=min(choices,key=lambda q:q[0])
            if score>3:raise ValueError(f'Unknown alias layout {bi}:{n}/{source}')
            parts[current['record_offset']+2]=b['x']&255;parts[current['record_offset']+3]=b['y']&255
    for bi in (0,1):
        for n in sorted(worlds[bi]):
            if n in layout_aliases[bi]:align_alias(n,layout_aliases[bi][n],bi)
            if bi==1 and n==135:
                shared={p['tile']:p for p in composition_frame(parts,5,134)['parts']}
                for p in composition_frame(parts,5,n)['parts']:
                    if p['tile'] in shared:
                        q=shared[p['tile']];parts[p['record_offset']+2]=q['x']&255;parts[p['record_offset']+3]=q['y']&255
            frames[bi][n]=place(n,bi,worlds[bi][n])
    # Damage overlays depend on the body sampling layout; copy only matching
    # base tile coordinates, retaining their CLUT2 effect parts.
    for base,targets,count in ((135,(136,137),10),(139,(140,141),10),(144,(145,),11)):
        source=composition_frame(parts,0,base)['parts']
        for n in targets:
            dest=composition_frame(parts,0,n)['parts']
            for a,b in zip(source[:count],dest[:count]):
                if a['tile']!=b['tile']:raise ValueError('Hurt base tile identity differs')
                parts[b['record_offset']+2]=a['x']&255;parts[b['record_offset']+3]=a['y']&255
    original_arc=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.arc').read_bytes();_,original_gfx=entry(original_arc,2)
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'))
    if sha(original_arc)!=profile['zero_archive']['sha256']:raise ValueError('Original hurt source differs')
    hurt,streams=derive_hurt(original_gfx,bytes(parts),frames[0][135],frames[0][139]);frames[0].update(hurt)
    for n,frame in hurt.items():worlds[0][n]=to_world(frame,native(n)[3][2])
    if any(set(frames[b])!=expected[b] for b in (0,1)):raise ValueError(f'Incomplete body selection {[(b,sorted(expected[b]-frames[b].keys()),sorted(frames[b].keys()-expected[b])) for b in (0,1)]}')
    # Every composition mutation must be an x/y coordinate belonging to a
    # selected body. Resource IDs, flags, counts and unrelated parts are fixed.
    allowed=set()
    for bi in (0,1):
        pb=0 if bi==0 else 5
        for n in expected[bi]:
            before=composition_frame(oldparts,pb,n);after=composition_frame(parts,pb,n)
            if len(before['parts'])!=len(after['parts']):raise ValueError('Part count changed')
            for a,b in zip(before['parts'],after['parts']):
                if any(a[k]!=b[k] for k in a if k not in ('x','y')):raise ValueError('Part metadata changed')
                allowed.update((a['record_offset']+2,a['record_offset']+3))
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(oldparts,parts))):raise ValueError('Unrelated part bytes changed')
    # Recompose requested frames after all shared composition pointers settle.
    for bi in (0,1):
        for n in sorted(frames[bi]):
            if bi==0 and n in hurt:continue
            frames[bi][n]=place(n,bi,worlds[bi][n],False)
    modified=g;compression=[];sharing=[];final_frames={0:{},1:{}};packed_streams={};overflows=[]
    for bi in (0,1):
        bank=graphics_bank(g,bi);groups={}
        for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f)
        pb=0 if bi==0 else 5
        for offset,refs in groups.items():
            selected=[f for f in refs if f['index'] in expected[bi]]
            if not selected:continue
            f=refs[0];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
            special=next((streams[q['index']] for q in selected if bi==0 and q['index'] in streams),None)
            if special is not None:packed=special
            else:
                protected={};writes={};write_owner={};conflicts={};all_used=set()
                for ref in refs:
                    n=ref['index'];c=composition_frame(parts,pb,n)
                    cov=frame_coverage(raw,f['tile_count'],c)[0];all_used.update(s for v in cov for s in v)
                    if n not in expected[bi]:
                        for sources in cov:
                            for o,s in sources:protected[o,s]=raw[o]>>s&15
                for ref in selected:
                    n=ref['index'];c=composition_frame(parts,pb,n);data,size=frames[bi][n]
                    if bi==0 and n in LADDER_BASE_COUNTS:
                        c={**c,'parts':c['parts'][:LADDER_BASE_COUNTS[n]]};_,sz,bb,_=compose_indices(raw,f['tile_count'],c);data=worlds[bi][n][96+bb[1]:96+bb[3],96+bb[0]:96+bb[2]].tobytes();size=sz
                    requests,_=_requested_writes(bytes(len(raw)),f['tile_count'],c,data,size,'equal_sources')
                    for source,value in requests.items():
                        if source in protected and protected[source]!=value:raise ValueError(f'Effect/fixed body collision {bi}:{n}')
                        if source in writes and writes[source]!=value:conflicts[n]=conflicts.get(n,0)+1
                        else:writes[source]=value;write_owner[source]=n
                # First body reference owns each reused native texel. Later
                # references reuse the SAME pixel rather than separate redraws.
                base=bytearray(len(raw));base[:]=raw
                for o in range(len(base)):
                    for s in (0,4):
                        if (o,s) not in protected:base[o]&=~(15<<s)
                packed=_apply_writes(bytes(base),writes)
                sharing.append({'bank':bi,'frames':[q['index'] for q in refs],'conflicting_requests_resolved_by_first_body':conflicts})
            atlas,_,_=indexed_atlas(packed,f['tile_count'])
            for ref in selected:
                for p in composition_frame(parts,pb,ref['index'])['parts']:
                    t=p['tile']
                    if t%16==0 and any(atlas[(t//16*16+y)*256] for y in range(16)):raise ValueError(f'Mirror U0 {bi}:{ref["index"]}')
            packed_streams[offset]=packed;code=encode_stream(packed)
            if len(code)>f['limit']-offset:
                budget={'start':offset,'encoded_bytes':len(code),'capacity':f['limit']-offset,'overflow':len(code)-(f['limit']-offset)};overflows.append({'bank':bi,'frames':[q['index'] for q in refs],**budget})
            else:modified,budget=replace_stream(modified,f,packed,allocated_limit=f['limit'])
            compression.append({'bank':bi,'frames':[q['index'] for q in refs],**budget})
    repacking=[]
    if overflows:
        # Reuse the established in-bank lossless packer: ARC entry size, bank
        # boundaries, external file/LBA references and decoded pixels stay fixed.
        for bi in sorted({q['bank'] for q in overflows}):
            replacements={}
            for f in graphics_bank(g,bi)['frames']:
                if f['offset'] in packed_streams:replacements[f['index']]=encode_stream(packed_streams[f['offset']])
            modified,report=repack_graphics_bank(modified,bi,replacements);repacking.append(report)
    checked=[];diffs=[]
    for bi in (0,1):
        if (graphics_bank(g,bi)['base'],graphics_bank(g,bi)['end'])!=(graphics_bank(modified,bi)['base'],graphics_bank(modified,bi)['end']):raise ValueError('Bank boundaries changed')
        for f in graphics_bank(g,bi)['frames']:
            n=f['index'];old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;new=packed_streams.get(f['offset'],old)
            newf=graphics_bank(modified,bi)['frames'][n]
            if newf['tile_count']!=f['tile_count'] or decode_stream(modified,newf['offset'],newf['limit'],newf['tile_count']*128).data!=new:raise ValueError('Written compressed stream differs')
            if n not in expected[bi]:
                if old!=new:
                    before=compose_launch(old,f['tile_count'],composition_frame(oldparts,0 if bi==0 else 5,n));after=compose_launch(new,f['tile_count'],composition_frame(parts,0 if bi==0 else 5,n))
                    if before[:3]!=after[:3]:raise ValueError(f'Unselected display changed {bi}:{n}')
            else:
                result=compose_launch(new,f['tile_count'],composition_frame(parts,0 if bi==0 else 5,n));actual=to_world(result[:2],result[2]);count=int(np.count_nonzero(actual!=worlds[bi][n]));final_frames[bi][n]=result
                if count:diffs.append({'bank':bi,'frame':n,'shared_pixels_changed':count,'desired_opaque_pixels':int(np.count_nonzero(worlds[bi][n])),'actual_opaque_pixels':int(np.count_nonzero(actual))})
                p=DEST/f'bank{bi}_{n:03d}.png';save_image(result[0],result[1],words if n in MULTI_FRAMES and bi==0 else words[:16],p)
            checked.append([bi,n])
    if frozen.get('accepted_stride') and diffs:
        raise ValueError(f'Shared rendering differs from the accepted pose mapping: {diffs}')
    # Fixed idle is checked in world space AND raw composition, even if its
    # bitmap shares a stream with revised victory/recovery references.
    for bi,ns in FIXED.items():
        for n in ns:
            f,c,raw,before=native(n,bi,oldparts);after=compose_launch(packed_streams.get(f['offset'],raw),f['tile_count'],composition_frame(parts,0 if bi==0 else 5,n))
            if before[:3]!=after[:3] or c!=composition_frame(parts,0 if bi==0 else 5,n):raise ValueError('Frozen idle changed')
    output=bytearray(arc);output[gm['offset']:gm['offset']+gm['size']]=modified;output[cm['offset']:cm['offset']+cm['size']]=parts
    if len(output)!=len(arc):raise ValueError('Archive length changed')
    for e in psx_arc(arc):
        if e['type'] not in ('0x2','0x3') and output[e['offset']:e['offset']+e['size']]!=arc[e['offset']:e['offset']+e['size']]:raise ValueError('Unrelated archive entry changed')
    (DEST/'modified.arc').write_bytes(output)
    (DEST/'composition_entry.bin').write_bytes(parts)
    for offset,packed in packed_streams.items():(DEST/f'stream_{offset:06x}.bin').write_bytes(packed)
    for bi in (0,1):
        ns=sorted(final_frames[bi]);sheet=Image.new('RGB',(10*224,((len(ns)+9)//10)*240),(35,38,48));draw=ImageDraw.Draw(sheet)
        for i,n in enumerate(ns):
            result=final_frames[bi][n];pic=Image.open(DEST/f'bank{bi}_{n:03d}.png').convert('RGBA');cell=Image.new('RGBA',(112,112));cell.alpha_composite(pic,(56+result[2][0],56+result[2][1]));cell=cell.resize((224,224),Image.Resampling.NEAREST);xy=(i%10*224,i//10*240);sheet.paste(cell,(xy[0],xy[1]+16),cell);draw.text((xy[0]+8,xy[1]),str(n),fill='white')
        sheet.save(DEST/f'bank{bi}_review.png')
    report={'parent':str(PARENT.relative_to(ROOT)),'parent_sha256':pm['modified_bin']['sha256'],'modified_archive_sha256':sha(output),'body_frames':{str(b):sorted(expected[b]) for b in (0,1)},'fixed_idle_unchanged':True,'references_checked':len(checked),'palette_animation_other_entries_unchanged':True,'resource_addresses_unchanged':not bool(repacking),'bank_boundaries_unchanged':True,'compression':compression,'sharing':sharing,'shared_display_adjustments':diffs,'arrival_contact_registration':arrival_contacts,'slot_overflows_resolved_by_in_bank_repacking':overflows,'in_bank_repacking':repacking,'runtime_verified':False}
    report['shared_pose_bindings']=pose_bindings
    (DEST/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');return bytes(output),report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path);args=ap.parse_args()
    _,r=prepare(args.work);print(json.dumps({'output':str(DEST),'modified_archive_sha256':r['modified_archive_sha256'],'refs':r['references_checked'],'shared_adjustments':r['shared_display_adjustments']}))
