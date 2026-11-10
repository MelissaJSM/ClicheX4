"""린 벽 동작의 정면/등 원화를 공통 축척으로 등록하고 공유를 검사한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.prepare_riko_jump import components
from scripts.build_rin_idle import entry
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_set
from src.psx_compress import encode_stream

OUT=ROOT/'work/ver_rin_nana/wall_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_dash_20261028T102644640190Z'
KEYS=[35,36,37,38,39,41]
MAPPING={n:n for n in range(35,44)};MAPPING.update({40:39,42:41,43:41})
SCALE=.14

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,0)
    original_parts=parts
    # Reposition the existing windows to cover Rin's bob/ribbon/raised foot.
    # Each row stays disjoint, with identical counts, tile IDs, flags and y.
    parts=bytearray(parts)
    adjustments={35:{6:8,7:8}}
    for n,delta in adjustments.items():
        for q in composition_frame(parts,0,n)['parts']:
            if q['index'] in delta:parts[q['record_offset']+2]=(q['x']+delta[q['index']])&255
    parts=bytes(parts)
    colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    source=OUT/'generated_wall.png';im=Image.open(source).convert('RGBA');poses={}
    crops=components(im,6)
    crops.sort(key=lambda v:(int((v[0][1]+v[0][3])/2*3/im.height),v[0][0]))
    fixed=Image.open(OUT/'generated_tip_fix.png').convert('RGBA');fixes=components(fixed,6)
    if fixed.size!=im.size:raise ValueError('Edit changed the sheet dimensions')
    fixes.sort(key=lambda v:(int((v[0][1]+v[0][3])/2*3/fixed.height),v[0][0]))
    crops[4]=fixes[4]
    for n,(box,crop) in zip(KEYS,crops):
        a=quantize(crop,colors,SCALE);groups=connected_groups(a>0)
        if any(len(q)>3 for q in groups[1:]):raise ValueError(f'Detached art in key {n}: {[len(q) for q in groups]}')
        clean=np.zeros_like(a);q=groups[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]]
        yy,xx=np.nonzero(clean);a=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
        poses[n]=a
    records={};frames={};issues=[];previews={}
    for n in range(35,44):
        a=poses[MAPPING[n]];h,w=a.shape;f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]]=False
        eye_y,eye_x=np.nonzero((a==15)&(np.indices(a.shape)[1]<w*.7))
        has_eye=bool(len(eye_x))
        if not len(eye_x):eye_x=np.array([w*.5]);eye_y=np.array([h*.25])
        ex=float(eye_x.mean());ey=float(eye_y.mean());anchor=0 if n==38 else -4;ideal_x=anchor-bounds[0]-ex;ideal_y=29-bounds[1]-(h-1)
        options=[]
        for y in range(max(0,size[1]-h+1)):
            for x in range(max(0,size[0]-w+1)):
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,2*abs(x-ideal_x)+abs(y-ideal_y),x,y))
        if not options:issues.append({'frame':n,'canvas':size,'art':[w,h]});continue
        bad,score,x,y=min(options)
        if bad:
            by,bx=np.nonzero((a>0)&~safe[y:y+h,x:x+w])
            issues.append({'frame':n,'outside_safe_parts':bad,'size':[w,h],'outside_coordinates':[[int(xx+x+bounds[0]),int(yy+y+bounds[1])] for xx,yy in zip(bx,by)]})
        pixels=np.zeros((size[1],size[0]),np.uint8);pixels[y:y+h,x:x+w]=a
        shift=round(anchor-(x+bounds[0]+ex))
        if shift:
            updated=bytearray(parts)
            for q in c['parts']:updated[q['record_offset']+2]=(q['x']+shift)&255
            parts=bytes(updated);bounds=(bounds[0]+shift,bounds[1],bounds[2]+shift,bounds[3])
        path=OUT/f'frame_{n:03d}.png';pic=save_image(pixels.tobytes(),size,words,path)
        cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+bounds[0],48+bounds[1]));previews[n]=cell
        frames[n]=(pixels.tobytes(),size)
        records[str(n)]={'file':path.name,'sha256':digest(path),'source_key':MAPPING[n],'source_sheet':'generated_tip_fix.png' if MAPPING[n]==39 else source.name,'native_size':[w,h],'placement':[x,y],'bounds':bounds,'registration_anchor':'cyan_eye' if has_eye else 'silhouette_center_back_view','eye_world':[x+bounds[0]+ex,y+bounds[1]+ey] if has_eye else None,'floor':y+bounds[1]+h-1,'outside_safe_parts':bad,'whole_frame_x_registration':shift}
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
    for i,n in enumerate(range(35,44)):
        if n not in previews:continue
        pic=previews[n].resize((320,384),Image.Resampling.NEAREST);board.paste(pic,(i%4*320,i//4*384),pic);draw.text((i%4*320+8,i//4*384+8),str(n),fill='white')
    board.save(OUT/'review_4x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'source':source.name,'source_sha256':digest(source),'prompt':'prompt_wall.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(original_parts,parts)) if a!=b],'compression':compression,'issues':issues,'applied':False}
    report['ribbon_revision']={'source':'generated_tip_fix.png','sha256':digest(OUT/'generated_tip_fix.png'),'used_key':39,'prompt':'prompt_tip_fix.txt','other_keys_preserved_from_first_generation':True}
    report['segmentation']='six complete alpha>=128 connected components, not fixed cell crops; same scale for every source'
    (OUT/'wall_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'issues':issues,'compression':compression,'pose_sizes':{n:list(a.shape[::-1]) for n,a in poses.items()}}))

if __name__=='__main__':main()
