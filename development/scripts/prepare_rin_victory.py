"""린 승리7키와 새 몸체를 따르는 퇴장2섬광을 bank1에 준비한다."""
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
from src.psx_frame_edit import frame_coverage
from src.psx_bank_patch import patch_bank
from src.rin_effects import derive_departure,validate_departure
OUT=ROOT/'work/ver_rin_nana/victory_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_arrival_20261028T124830252983Z'
SCALE=.12


def boot_center(a):
    yy,xx=np.nonzero(a);floor=int(yy.max());contacts=xx[yy>=floor-2]
    return (int(contacts.min())+int(contacts.max()))/2,floor


def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);oldparts=parts
    words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,1);colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    def native(n,bi=1,pi=5):
        f=graphics_bank(g,bi)['frames'][n];c=composition_frame(parts,pi,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        return f,c,raw,compose_indices(raw,f['tile_count'],c)
    idle=native(147,0,0)[3];idle_a=np.frombuffer(idle[0],np.uint8).reshape(idle[1][1],idle[1][0]);center,floor=boot_center(idle_a);center+=idle[2][0];floor+=idle[2][1]
    source=OUT/'generated_victory.png';groups=source_groups(source,6);groups=sorted(groups,key=lambda q:(q[0][1]//512,q[0][0]));poses={};source_bounds={}
    for n,(b,crop) in enumerate(groups,1):
        a=quantize(crop,colors,SCALE);gs=connected_groups(a>0)
        if any(len(q)>3 for q in gs[1:]):raise ValueError(f'Detached victory {n}')
        clean=np.zeros_like(a);q=gs[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]];yy,xx=np.nonzero(clean);poses[n]=clean[yy.min():yy.max()+1,xx.min():xx.max()+1];source_bounds[n]=b
    frames={};records={};issues=[]
    for n in range(7):
        f,c,raw,_=native(n);cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]+(15 if q['flip_x'] else 0)]=False
        if n==0:
            pixels=np.zeros((size[1],size[0]),np.uint8)
            for yy,xx in np.argwhere(idle_a>0):
                x=int(xx+idle[2][0]-bounds[0]);y=int(yy+idle[2][1]-bounds[1])
                if not (0<=x<size[0] and 0<=y<size[1]):raise ValueError('Idle does not fit victory start')
                pixels[y,x]=idle_a[yy,xx]
            bad=int(np.count_nonzero((pixels>0)&~safe));shift=0;records['0']={'source':'current_idle147_world_coordinates','bounds':bounds}
        else:
            a=poses[n];h,w=a.shape;contact,lower=boot_center(a);ideal_x=center-bounds[0]-contact;y=floor-bounds[1]-lower;options=[]
            if 0<=y and y+h<=size[1]:
                for x in range(max(0,size[0]-w+1)):
                    bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,abs(x-ideal_x),x))
            if not options:issues.append({'frame':n,'art':[w,h],'canvas':size});continue
            bad,_,x=min(options);pixels=np.zeros((size[1],size[0]),np.uint8);pixels[y:y+h,x:x+w]=a;shift=round(ideal_x-x)
            if shift:
                updated=bytearray(parts)
                for q in c['parts']:updated[q['record_offset']+2]=(q['x']+shift)&255
                parts=bytes(updated);bounds=(bounds[0]+shift,bounds[1],bounds[2]+shift,bounds[3])
            records[str(n)]={'source_cell':n,'source_bounds':source_bounds[n],'native_size':[w,h],'bounds':bounds,'placement':[x,y],'whole_frame_x_registration':shift,'boot_extent_center':x+bounds[0]+contact,'floor':floor}
        if bad:issues.append({'frame':n,'outside':bad})
        frames[n]=(pixels.tobytes(),size);records[str(n)]['outside_safe_parts']=bad
    validation=None;compression=[]
    if not issues:
        try:
            frames.update(derive_departure(g,parts,frames[3]));validation=validate_departure(g,parts,frames)
            allframes=dict(frames)
            for n in range(9,14):allframes[n]=native(n)[3][:2]
            _,checks=patch_bank(g,parts,1,5,allframes,range(9,14),clear_unreferenced=True);compression=checks['compression']
        except ValueError as e:issues.append({'error':str(e)})
    board=Image.new('RGB',(5*240,2*288),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(sorted(frames)):
        pixels,size=frames[n];path=OUT/f'bank1_{n:03d}.png';pic=save_image(pixels,size,words,path);b=native(n)[3][2];records.setdefault(str(n),{'derived_from':3,'bounds':b});cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+b[0],48+b[1]));cell=cell.resize((240,288),Image.Resampling.NEAREST);board.paste(cell,(i%5*240,i//5*288),cell);draw.text((i%5*240+8,i//5*288+8),str(n),fill='white');records[str(n)].update({'file':path.name,'sha256':digest(path)})
    board.save(OUT/'review_3x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'graphics_bank':1,'parts_bank':5,'source':source.name,'source_sha256':digest(source),'prompt':'prompt.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(oldparts,parts)) if a!=b],'preserved_effect_frames':list(range(9,14)),'departure_validation':validation,'compression':compression,'issues':issues,'applied':False}
    (OUT/'victory_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'issues':issues,'compression':compression,'sizes':{n:list(a.shape[::-1]) for n,a in poses.items()}}))


if __name__=='__main__':main()
