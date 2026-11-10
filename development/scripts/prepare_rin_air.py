"""린 공중 생성 시트를 공통 축척으로 등록하고 공유 프레임을 검사한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.build_rin_idle import entry
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_set
from src.psx_compress import encode_stream

OUT=ROOT/'work/ver_rin_nana/air_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_run_20261028T093826216004Z'
KEYS=[21,22,24,25,26,27,28,29,31,33,34,147]
MAPPING={n:n for n in range(21,35)};MAPPING.update({23:22,30:29,32:31})
SCALE=.1875

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,0)
    original_parts=parts
    # Reposition the existing windows to cover Rin's bob/ribbon/raised foot.
    # Each row stays disjoint, with identical counts, tile IDs, flags and y.
    parts=bytearray(parts)
    adjustments={22:{0:-4,1:-4,2:2,3:2,4:2,8:2},23:{0:-4,1:-4,2:2,3:2,4:2,8:2},
                 24:{0:-4,1:-4,2:4,3:4,4:4,5:-3,6:-3,7:-3},34:{2:1,3:1,4:1}}
    for n,delta in adjustments.items():
        for q in composition_frame(parts,0,n)['parts']:
            if q['index'] in delta:parts[q['record_offset']+2]=(q['x']+delta[q['index']])&255
    parts=bytes(parts)
    colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    source=OUT/'generated_air.png';im=Image.open(source).convert('RGBA');poses={}
    for i,n in enumerate(KEYS):
        box=(round(i%4*im.width/4),round(i//4*im.height/3),round((i%4+1)*im.width/4),round((i//4+1)*im.height/3))
        a=quantize(im.crop(box),colors,SCALE);groups=connected_groups(a>0)
        if any(len(q)>3 for q in groups[1:]):raise ValueError(f'Detached art in key {n}: {[len(q) for q in groups]}')
        clean=np.zeros_like(a);q=groups[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]]
        yy,xx=np.nonzero(clean);a=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
        poses[n]=a
    records={};frames={};issues=[];previews={}
    for n in range(21,35):
        a=poses[MAPPING[n]];h,w=a.shape;f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]]=False
        eye_y,eye_x=np.nonzero((a==15)&(np.indices(a.shape)[1]<w*.7))
        if not len(eye_x):raise ValueError(f'No cyan eye in {n}')
        ex=float(eye_x.mean());ey=float(eye_y.mean());ideal_x=-4-bounds[0]-ex;ideal_y=23-bounds[1]-(h-1)
        options=[]
        for y in range(max(0,size[1]-h+1)):
            for x in range(max(0,size[0]-w+1)):
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,2*abs(x-ideal_x)+abs(y-ideal_y),x,y))
        if not options:issues.append({'frame':n,'canvas':size,'art':[w,h]});continue
        bad,score,x,y=min(options)
        if bad:issues.append({'frame':n,'outside_safe_parts':bad,'size':[w,h]})
        pixels=np.zeros((size[1],size[0]),np.uint8);pixels[y:y+h,x:x+w]=a
        shift=round(-4-(x+bounds[0]+ex))
        if shift:
            updated=bytearray(parts)
            for q in c['parts']:updated[q['record_offset']+2]=(q['x']+shift)&255
            parts=bytes(updated);bounds=(bounds[0]+shift,bounds[1],bounds[2]+shift,bounds[3])
        path=OUT/f'frame_{n:03d}.png';pic=save_image(pixels.tobytes(),size,words,path)
        cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+bounds[0],48+bounds[1]));previews[n]=cell
        frames[n]=(pixels.tobytes(),size)
        records[str(n)]={'file':path.name,'sha256':digest(path),'source_key':MAPPING[n],'native_size':[w,h],'placement':[x,y],'bounds':bounds,'eye_world':[x+bounds[0]+ex,y+bounds[1]+ey],'floor':y+bounds[1]+h-1,'outside_safe_parts':bad,'whole_frame_x_registration':shift}
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
    for i,n in enumerate(range(21,35)):
        if n not in previews:continue
        pic=previews[n].resize((320,384),Image.Resampling.NEAREST);board.paste(pic,(i%4*320,i//4*384),pic);draw.text((i%4*320+8,i//4*384+8),str(n),fill='white')
    board.save(OUT/'review_4x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'source':source.name,'source_sha256':digest(source),'prompt':'prompt_air.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(original_parts,parts)) if a!=b],'compression':compression,'issues':issues,'applied':False}
    (OUT/'air_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'issues':issues,'compression':compression,'pose_sizes':{n:list(a.shape[::-1]) for n,a in poses.items()}}))

if __name__=='__main__':main()
