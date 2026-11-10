"""기존 벽 자세를 기준으로 린 bank1/parts5 벽 베기를 등록한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.prepare_riko_jump import components
from scripts.build_rin_idle import entry
from scripts.build_rin_motion import SCOPES,WALL_SABER_EFFECTS
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.psx_bank_patch import patch_bank
from src.psx_frame_edit import frame_coverage,edit_frame_set
from src.psx_compress import encode_stream

OUT=ROOT/'work/ver_rin_nana/wall_saber_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_air_slash_20261028T115715800703Z'
IDS=SCOPES['wall_saber'];EFFECTS=WALL_SABER_EFFECTS
MAPPING={50:50,51:51,53:51,54:54,56:54,**dict.fromkeys((57,59,61,63,65),57)}

def source_groups(path,count):
    rgba=np.array(Image.open(path).convert('RGBA'));gs=connected_groups(rgba[:,:,3]>=128)
    if len(gs)!=count:raise ValueError('Unexpected disconnected source artwork')
    result=[]
    for q in gs:
        y0,x0=q.min(axis=0);y1,x1=q.max(axis=0)+1;a=rgba[y0:y1,x0:x1].copy();a[:,:,3]=0;a[q[:,0]-y0,q[:,1]-x0,3]=255
        result.append(([int(x0),int(y0),int(x1),int(y1)],Image.fromarray(a)))
    return sorted(result,key=lambda q:q[0][0])

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);oldparts=parts
    words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,1);colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    src=OUT/'generated_wall_saber.png';cs=source_groups(src,3);ready=source_groups(OUT/'generated_ready50.png',1)[0];poses={}
    for n,(_,crop),scale in [(50,ready,.044),*[(n,c,.09) for n,c in zip((51,54,57),cs)]]:
        a=quantize(crop,colors,scale);gs=connected_groups(a>0)
        if any(len(q)>3 for q in gs[1:]):raise ValueError(f'Detached art {n}')
        clean=np.zeros_like(a);q=gs[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]];yy,xx=np.nonzero(clean);poses[n]=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
    frames={};records={};issues=[]
    for n in sorted(IDS):
        a=poses[MAPPING[n]];h,w=a.shape;f=bank['frames'][n];c=composition_frame(parts,5,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]+(15 if q['flip_x'] else 0)]=False
        hy,hx=np.nonzero(np.isin(a,(12,13,14))&(np.indices(a.shape)[0]<10))
        if not len(hx):raise ValueError(f'No support hand anchor {n}')
        hand=float(hx.mean());hand_y=float(hy.mean());ideal_x=-1.058824-bounds[0]-hand;ideal_y=-28.588235-bounds[1]-hand_y;options=[]
        for y in range(max(0,size[1]-h+1)):
            for x in range(max(0,size[0]-w+1)):
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,2*abs(x-ideal_x)+abs(y-ideal_y),x,y))
        if not options:issues.append({'frame':n,'art':[w,h],'canvas':size});continue
        bad,_,x,y=min(options);pixels=np.zeros((size[1],size[0]),np.uint8);pixels[y:y+h,x:x+w]=a
        if bad:
            by,bx=np.nonzero((a>0)&~safe[y:y+h,x:x+w]);issues.append({'frame':n,'outside':bad,'coords':[[int(xx+x+bounds[0]),int(yy+y+bounds[1])] for xx,yy in zip(bx,by)]})
        shift=round(-1.058824-(x+bounds[0]+hand))
        if shift:
            updated=bytearray(parts)
            for q in c['parts']:updated[q['record_offset']+2]=(q['x']+shift)&255
            parts=bytes(updated);bounds=(bounds[0]+shift,bounds[1],bounds[2]+shift,bounds[3])
        frames[n]=(pixels.tobytes(),size);records[str(n)]={'source_key':MAPPING[n],'native_size':[w,h],'bounds':bounds,'placement':[x,y],'support_hand_world':[x+bounds[0]+hand,y+bounds[1]+hand_y],'bottom':y+bounds[1]+h-1,'outside_safe_parts':bad,'whole_frame_x_registration':shift}
    compression=[]
    if not issues:
        allframes=dict(frames)
        for n in EFFECTS:
            f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;allframes[n]=compose_indices(raw,f['tile_count'],composition_frame(parts,5,n))[:2]
        try:
            _,checks=patch_bank(g,parts,1,5,allframes,EFFECTS,clear_unreferenced=True);compression=checks['compression']
        except ValueError as e:issues.append({'error':str(e)})
    board=Image.new('RGB',(5*240,2*288),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(sorted(frames)):
        pixels,size=frames[n];path=OUT/f'bank1_{n:03d}.png';pic=save_image(pixels,size,words,path);b=records[str(n)]['bounds'];cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+b[0],48+b[1]));cell=cell.resize((240,288),Image.Resampling.NEAREST);board.paste(cell,(i%5*240,i//5*288),cell);draw.text((i%5*240+8,i//5*288+8),str(n),fill='white');records[str(n)].update({'file':path.name,'sha256':digest(path)})
    board.save(OUT/'review_3x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'graphics_bank':1,'parts_bank':5,'sources':[{'file':s,'sha256':digest(OUT/s)} for s in ('generated_wall_saber.png','generated_ready50.png')],'prompts':['prompt_wall_saber.txt','prompt_ready50.txt'],'imagegen_mode':'built_in','uniform_scale':.096,'ready_source_scale':.044,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(oldparts,parts)) if a!=b],'preserved_effect_frames':sorted(EFFECTS),'compression':compression,'issues':issues,'applied':False}
    report['uniform_scale']=.09
    report['registration_reference']={'file':'work/ver_rin_nana/wall_production/v1/frame_039.png','sha256':digest(ROOT/'work/ver_rin_nana/wall_production/v1/frame_039.png'),'support_hand_world':[-1.058824,-28.588235]}
    (OUT/'wall_saber_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'issues':issues,'compression':compression,'sizes':{n:list(a.shape[::-1]) for n,a in poses.items()}}))

if __name__=='__main__':main()
