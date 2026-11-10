"""린 등장5키의 두 부츠 중심을 대기에 맞추고2섬광을 파생한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.prepare_rin_wall_saber import source_groups
from scripts.build_rin_idle import entry
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_set
from src.psx_compress import encode_stream
from src.psx_beam_in import foot_contacts
from src.rin_effects import derive_arrival,validate_arrival
OUT=ROOT/'work/ver_rin_nana/arrival_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_ladder_20261028T123019376066Z';SCALE=.118

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);oldparts=parts
    adjusted=bytearray(parts)
    for q in composition_frame(parts,0,248)['parts']:adjusted[q['record_offset']+2]=(q['x']+4)&255
    # Extend the rightmost lower column upward one pixel for the ribbon tip.
    # Its bottom row is transparent. World-space art and boot contacts stay fixed.
    for q in composition_frame(parts,0,252)['parts']:
        if q['tile'] in (6,9):adjusted[q['record_offset']+3]=(q['y']-1)&255
    parts=bytes(adjusted);words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,0);colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    def native(n):
        f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        return f,c,raw,compose_indices(raw,f['tile_count'],c)
    _,_,_,idle=native(147);target=foot_contacts(idle[:2],idle[2]);source=OUT/'generated_arrival.png';poses={}
    for n,(_,crop) in zip(range(249,254),source_groups(source,5)):
        a=quantize(crop,colors,SCALE);gs=connected_groups(a>0)
        if any(len(q)>3 for q in gs[1:]):raise ValueError(f'Detached art {n}')
        clean=np.zeros_like(a);q=gs[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]];yy,xx=np.nonzero(clean);poses[n]=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
    frames={};records={};bounds_by_frame={};issues=[]
    for n,a in poses.items():
        h,w=a.shape;f,c,raw,_=native(n);cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]]=False
        contacts=foot_contacts((a.tobytes(),(w,h)),(0,0,w,h));ideal_x=target['center_x']-bounds[0]-contacts['center_x'];y=target['floor_y']-bounds[1]-contacts['floor_y'];options=[]
        if 0<=y and y+h<=size[1]:
            for x in range(max(0,size[0]-w+1)):
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,abs(x-ideal_x),x))
        if not options:issues.append({'frame':n,'art':[w,h],'canvas':size});continue
        bad,_,x=min(options);pixels=np.zeros((size[1],size[0]),np.uint8);pixels[y:y+h,x:x+w]=a
        if bad:issues.append({'frame':n,'outside':bad})
        shift=round(ideal_x-x)
        if shift:
            updated=bytearray(parts)
            for q in c['parts']:updated[q['record_offset']+2]=(q['x']+shift)&255
            parts=bytes(updated);bounds=(bounds[0]+shift,bounds[1],bounds[2]+shift,bounds[3])
        frames[n]=(pixels.tobytes(),size);bounds_by_frame[n]=bounds;records[str(n)]={'native_size':[w,h],'bounds':bounds,'placement':[x,y],'whole_frame_x_registration':shift,'outside_safe_parts':bad}
    compression=[];validation=None
    if not issues:
        try:
            frames.update(derive_arrival(g,parts,frames[249]));validation=validate_arrival(g,parts,frames,bounds_by_frame,idle[:2],idle[2])
        except ValueError as e:issues.append({'flash_or_contact_error':str(e)})
    if not issues:
        groups={}
        for n in frames:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
        for offset,ns in groups.items():
            f=bank['frames'][ns[0]];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
            if 252 in ns:raw=bytes(len(raw))  # Entire shared 252/253 bitmap is authored here.
            try:packed=edit_frame_set(raw,f['tile_count'],[(composition_frame(parts,0,n),*frames[n]) for n in ns],overlap_policy='equal_sources' if 252 in ns else 'reject')
            except ValueError as e:issues.append({'frames':ns,'error':str(e)});continue
            code=encode_stream(packed);budget=f['limit']-offset;compression.append({'frames':ns,'encoded_bytes':len(code),'budget':budget})
            if len(code)>budget:issues.append({'frames':ns,'overflow':len(code)-budget})
    board=Image.new('RGB',(7*240,288),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(sorted(frames)):
        pixels,size=frames[n];path=OUT/f'frame_{n:03d}.png';pic=save_image(pixels,size,words,path);b=native(n)[3][2];records.setdefault(str(n),{'derived_from':249,'bounds':b});cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+b[0],48+b[1]));cell=cell.resize((240,288),Image.Resampling.NEAREST);board.paste(cell,(i*240,0),cell);draw.text((i*240+8,8),str(n),fill='white');records[str(n)].update({'file':path.name,'sha256':digest(path)})
    board.save(OUT/'review_3x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'source':source.name,'source_sha256':digest(source),'prompt':'prompt_arrival.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(oldparts,parts)) if a!=b],'flash_and_contact_validation':validation,'compression':compression,'issues':issues,'applied':False}
    (OUT/'arrival_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'issues':issues,'compression':compression,'sizes':{n:list(a.shape[::-1]) for n,a in poses.items()},'validation':validation}))

if __name__=='__main__':main()
