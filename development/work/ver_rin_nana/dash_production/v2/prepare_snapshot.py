"""린 대시 원화와 기존 연결 자세를 원작 공유 타일에 등록한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups,register_head_attachments
from scripts.build_rin_idle import entry
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_set
from src.psx_compress import encode_stream

OUT=ROOT/'work/ver_rin_nana/dash_production/v2'
PARENT=ROOT/'out/ver_rin_nana/rin_air_20261028T095342289997Z'
KEYS=[44,45,46,47,48,49,50,51,52,3,4,147]
MAPPING={n:n for n in range(44,53)};MAPPING.update({47:46,48:46,49:44,52:51})
SCALE=.1875

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,0)
    original_parts=parts
    # Reposition the existing windows to cover Rin's bob and ribbon.
    # Each row stays disjoint, with identical counts, tile IDs, flags and y.
    parts=bytearray(parts)
    adjustments={46:{6:-3},47:{4:-3},48:{3:-3},
                 49:{0:-6,1:-6},50:{0:-9,1:-9},51:{0:-3,1:-3},
                 52:{**{i:1 for i in range(8)},0:-2,1:-2}}
    for n,delta in adjustments.items():
        for q in composition_frame(parts,0,n)['parts']:
            if q['index'] in delta:parts[q['record_offset']+2]=(q['x']+delta[q['index']])&255
    parts=bytes(parts)
    colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    source=OUT/'generated_dash.png';original=Image.open(source).convert('RGBA');poses={};head_registrations={}
    master_head=np.array(Image.open(ROOT/'out/ver_rin_nana/rin_pilot_20261028T080902512874Z/rin_idle147_indexed.png'))[:18,14:36]
    for i,n in enumerate(KEYS):
        if n not in (44,45,46,47,48,51):continue
        im=original
        if n in (47,48):im=Image.open(ROOT/'work/ver_rin_nana/dash_production/v1/generated_dash.png').convert('RGBA')
        box=(round(i%4*im.width/4),round(i//4*im.height/3),round((i%4+1)*im.width/4),round((i//4+1)*im.height/3))
        a=quantize(im.crop(box),colors,SCALE)
        if n in (44,45,46,51):
            ey,ex=np.nonzero((a==15)&(np.indices(a.shape)[1]<a.shape[1]*.65))
            if not len(ex):raise ValueError(f'Missing eye in {n}')
            left=24+round(float(ex.mean()))-6;top=24+round(float(ey.mean()))-10
            a=np.pad(a,((24,24),(24,24)))
            a[:top+18,left-3:left+24]=0;a[top:top+18,left:left+22]=master_head
            outline_noise=[]
            for isolated in connected_groups(a>0)[1:]:
                yy,xx=isolated[:,0],isolated[:,1]
                if len(isolated)<=9 and np.isin(a[yy,xx],(1,4)).all():
                    outline_noise.append(len(isolated));a[yy,xx]=0
            try:a,attachment_shifts=register_head_attachments(a,left,top)
            except ValueError as err:
                save_image(a.tobytes(),a.shape[::-1],words,OUT/f'head_registration_issue_{n}.png')
                raise ValueError(f'Head registration key {n}: {err}') from err
            head_registrations[n]={'source_roi':[14,0,36,18],'attachment_shifts':attachment_shifts,'isolated_outline_noise_removed':outline_noise}
        groups=connected_groups(a>0)
        if any(len(q)>3 for q in groups[1:]):raise ValueError(f'Detached art in key {n}: {[len(q) for q in groups]}')
        clean=np.zeros_like(a);q=groups[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]]
        yy,xx=np.nonzero(clean);a=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
        poses[n]=a
    records={};frames={};issues=[];previews={}
    for n in range(44,53):
        if n in (49,50):
            # Reverse the existing dash-entry/run-start poses to recover upright.
            # These are already runtime verified, and fit the tighter recovery slots.
            src={49:4,50:3}[n];sf=bank['frames'][src];sc=composition_frame(original_parts,0,src)
            tc=composition_frame(parts,0,n);updated=bytearray(parts)
            source_tiles={q['tile']:q for q in sc['parts']}
            for before in tc['parts']:
                after=source_tiles[before['tile']]
                if any(before[k]!=after[k] for k in ('tile','flags','y')):raise ValueError('Recovery layout is not compatible')
                updated[before['record_offset']+2]=after['x']&255
            parts=bytes(updated)
            raw=decode_stream(g,sf['offset'],sf['limit'],sf['tile_count']*128).data
            pixels,size,bounds,_=compose_indices(raw,sf['tile_count'],sc)
            path=OUT/f'frame_{n:03d}.png';pic=save_image(pixels,size,words,path)
            frames[n]=(pixels,size)
            cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+bounds[0],48+bounds[1]));previews[n]=cell
            records[str(n)]={'file':path.name,'sha256':digest(path),'source_parent_frame':src,'reason':'reverse existing entry for recovery','bounds':bounds,'pixels_identical_to_parent_frame':True,'outside_safe_parts':0}
            continue
        a=poses[MAPPING[n]];h,w=a.shape;f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]]=False
        eye_y,eye_x=np.nonzero((a==15)&(np.indices(a.shape)[1]<w*.7))
        if not len(eye_x):raise ValueError(f'No cyan eye in {n}')
        ex=float(eye_x.mean());ey=float(eye_y.mean());anchor={44:-8,45:-13,46:-15,47:-15,48:-15,49:-8,50:-5,51:-4,52:-4}[n];ideal_x=anchor-bounds[0]-ex;ideal_y=23-bounds[1]-(h-1)
        options=[]
        for y in range(max(0,size[1]-h+1)):
            for x in range(max(0,size[0]-w+1)):
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,2*abs(x-ideal_x)+abs(y-ideal_y),x,y))
        if not options:issues.append({'frame':n,'canvas':size,'art':[w,h]});continue
        bad,score,x,y=min(options)
        if bad:issues.append({'frame':n,'outside_safe_parts':bad,'size':[w,h]})
        pixels=np.zeros((size[1],size[0]),np.uint8);pixels[y:y+h,x:x+w]=a
        tail_variant=False
        if n in (47,48):
            alternate=poses[n];ah,aw=alternate.shape
            ay,ax=np.nonzero((alternate==15)&(np.indices(alternate.shape)[1]<aw*.7))
            sx=round(x+ex-float(ax.mean()));sy=y+h-ah
            if 0<=sx and 0<=sy and sx+aw<=size[0] and sy+ah<=size[1]:
                candidate=np.zeros_like(pixels);candidate[sy:sy+ah,sx:sx+aw]=alternate
                rows,cols=np.indices(pixels.shape)
                # Only the separately stored far ribbon tile. Body remains shared.
                mask=(cols+bounds[0]>=16)&(cols+bounds[0]<32)&(rows+bounds[1]>=-6)&(rows+bounds[1]<10)
                variant=np.where(mask,candidate,pixels)
                if len(connected_groups(variant>0))==1 and not np.any((variant>0)&~safe):
                    pixels=variant;tail_variant=True
        shift=round(anchor-(x+bounds[0]+ex))
        if shift:
            updated=bytearray(parts)
            for q in c['parts']:updated[q['record_offset']+2]=(q['x']+shift)&255
            parts=bytes(updated);bounds=(bounds[0]+shift,bounds[1],bounds[2]+shift,bounds[3])
        path=OUT/f'frame_{n:03d}.png';pic=save_image(pixels.tobytes(),size,words,path)
        cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+bounds[0],48+bounds[1]));previews[n]=cell
        frames[n]=(pixels.tobytes(),size)
        records[str(n)]={'file':path.name,'sha256':digest(path),'source_key':MAPPING[n],'tail_source_key':n if tail_variant else None,'native_size':[w,h],'placement':[x,y],'bounds':bounds,'eye_world':[x+bounds[0]+ex,y+bounds[1]+ey],'floor':y+bounds[1]+h-1,'outside_safe_parts':bad,'whole_frame_x_registration':shift}
    compression=[]
    if not issues:
        groups={}
        for n in frames:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
        for offset,ns in groups.items():
            f=bank['frames'][ns[0]];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
            try:packed=edit_frame_set(raw,f['tile_count'],[(composition_frame(parts,0,n),*frames[n]) for n in ns])
            except ValueError as err:issues.append({'frames':ns,'shared_error':str(err)});continue
            code=encode_stream(packed);budget=f['limit']-offset;compression.append({'frames':ns,'encoded_bytes':len(code),'budget':budget})
            if len(code)>budget:issues.append({'frames':ns,'overflow':len(code)-budget})
    board=Image.new('RGB',(4*320,4*384),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(range(44,53)):
        if n not in previews:continue
        pic=previews[n].resize((320,384),Image.Resampling.NEAREST);board.paste(pic,(i%4*320,i//4*384),pic);draw.text((i%4*320+8,i//4*384+8),str(n),fill='white')
    board.save(OUT/'review_4x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'source':source.name,'source_sha256':digest(source),'head_registrations':head_registrations,'prompt':'prompt_dash.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(original_parts,parts)) if a!=b],'compression':compression,'issues':issues,'applied':False}
    (OUT/'dash_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'issues':issues,'compression':compression,'pose_sizes':{n:list(a.shape[::-1]) for n,a in poses.items()}}))

if __name__=='__main__':main()
