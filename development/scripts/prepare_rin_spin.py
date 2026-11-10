"""공통 배율/회전 중심으로 린 회전 베기를 만들고 공유 빙열참 몸133을 보존한다."""
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
from src.psx_air_spin import BODY,ROTATING
OUT=ROOT/'work/ver_rin_nana/spin_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_victory_20261028T125245059284Z'
EFFECTS=set(range(162,177,2));PRESERVED=EFFECTS|{133};SCALE=.06


def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);oldparts=parts
    words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,1);colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    def native(n,bi=1,pi=5):
        f=graphics_bank(g,bi)['frames'][n];c=composition_frame(parts,pi,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        return f,c,raw,compose_indices(raw,f['tile_count'],c)
    source=OUT/'generated_spin.png';box,crop=source_groups(source,1)[0];a=quantize(crop,colors,SCALE);accent=None
    if not np.any(a==15):
        rgba=np.asarray(crop);rgb=rgba[:,:,:3].astype(np.int32);mask=(rgba[:,:,3]>=128)&(rgb[:,:,0]<100)&(rgb[:,:,1]>120)&(rgb[:,:,2]>140)&(np.indices(rgba.shape[:2])[0]<rgba.shape[0]*.5);gs=connected_groups(mask)
        if not gs:raise ValueError('No source eye accent')
        ey,ex=gs[0].mean(axis=0);ax,ay=round(ex*SCALE),round(ey*SCALE)
        if not a[ay,ax]:raise ValueError('Quantized eye outside body')
        a[ay,ax]=15;accent={'source_xy':[float(ex),float(ey)],'native_xy':[ax,ay]}
    groups=connected_groups(a>0)
    if any(len(q)>3 for q in groups[1:]):raise ValueError('Disconnected spin body')
    clean=np.zeros_like(a);q=groups[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]];a=clean
    base=np.zeros((192,192),np.uint8);base[96-21:96-21+a.shape[0],96-14:96-14+a.shape[1]]=a
    worlds={n:np.array(Image.fromarray(base).rotate(i*45,Image.Resampling.NEAREST,center=(96,96))) for i,n in enumerate(ROTATING)}
    # Reposition existing tile rows around the fixed world-space rotated art.
    # This does not move/scale each pose, add parts or change vertical coordinates.
    adjusted=bytearray(parts);row_edits=[]
    for n in ROTATING:
        rows={}
        for q in composition_frame(parts,5,n)['parts']:rows.setdefault(q['y'],[]).append(q)
        for row,ps in rows.items():
            occupied=worlds[n][96+row:96+row+16]>0;options=[]
            for shift in range(-16,17):
                safe=np.zeros_like(occupied)
                for q in ps:
                    left=96+q['x']+shift;safe[:,left:left+16]=True
                    if q['tile']%16==0:safe[:,left+(15 if q['flip_x'] else 0)]=False
                bad=int(np.count_nonzero(occupied&~safe));options.append((bad,abs(shift),shift))
            bad,_,shift=min(options)
            if bad:raise ValueError(f'Spin row {n}/{row} requires crop: {bad}')
            if shift:
                for q in ps:adjusted[q['record_offset']+2]=(q['x']+shift)&255
                row_edits.append({'frame':n,'row_y':row,'x_shift':shift,'world_art_moved':False})
    parts=bytes(adjusted)
    for n,source_n in ((132,229),(160,213)):
        pixels,size,b,_=native(source_n,0,0)[3];pic=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);canvas=np.zeros_like(base);canvas[96+b[1]:96+b[3],96+b[0]:96+b[2]]=pic;worlds[n]=canvas
    frames={};records={};issues=[]
    for n in sorted(BODY):
        f,c,raw,_=native(n);cover,size,b=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-b[1]:q['y']-b[1]+16,q['x']-b[0]+(15 if q['flip_x'] else 0)]=False
        world=worlds[n];pixels=world[96+b[1]:96+b[3],96+b[0]:96+b[2]].copy();expected=int(np.count_nonzero(world));actual=int(np.count_nonzero(pixels));bad=int(np.count_nonzero((pixels>0)&~safe))
        if bad or actual!=expected:
            yy,xx=np.nonzero((pixels>0)&~safe);issues.append({'frame':n,'outside_canvas':expected-actual,'outside_parts':bad,'coords':[[int(x+b[0]),int(y+b[1])] for x,y in zip(xx,yy)]})
        frames[n]=(pixels.tobytes(),size);yy,xx=np.nonzero(world);records[str(n)]={'bounds':b,'opaque_pixels':expected,'native_opaque_bounds':[int(xx.min()-96),int(yy.min()-96),int(xx.max()+1-96),int(yy.max()+1-96)],'rotation_degrees':ROTATING.index(n)*45 if n in ROTATING else None,'source_body':229 if n==132 else 213 if n==160 else 'generated_spin','outside_parts':bad}
    compression=[]
    if not issues:
        allframes=dict(frames)
        for n in PRESERVED:allframes[n]=native(n)[3][:2]
        try:_,checks=patch_bank(g,parts,1,5,allframes,PRESERVED,clear_unreferenced=True);compression=checks['compression']
        except ValueError as e:issues.append({'error':str(e)})
    board=Image.new('RGB',(5*288,2*288),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(sorted(frames)):
        pixels,size=frames[n];path=OUT/f'bank1_{n:03d}.png';pic=save_image(pixels,size,words,path);b=records[str(n)]['bounds'];cell=Image.new('RGBA',(96,96));cell.alpha_composite(pic.convert('RGBA'),(48+b[0],48+b[1]));cell=cell.resize((288,288),Image.Resampling.NEAREST);board.paste(cell,(i%5*288,i//5*288),cell);draw.text((i%5*288+8,i//5*288+8),str(n),fill='white');records[str(n)].update({'file':path.name,'sha256':digest(path)})
    board.save(OUT/'review_3x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'graphics_bank':1,'parts_bank':5,'source':source.name,'source_sha256':digest(source),'source_bounds':box,'prompt':'prompt.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'rotation_pivot':[0,0],'rotation_step_degrees':45,'eye_accent_quantization':accent,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_edits':[{'offset':i,'before':x,'after':y} for i,(x,y) in enumerate(zip(oldparts,parts)) if x!=y],'preserved_effect_frames':sorted(EFFECTS),'preserved_shared_body_frames':[133],'compression':compression,'issues':issues,'applied':False}
    report.update({'base_world_top_left':[-14,-21],'tile_row_registration':row_edits,'base_opaque_pixels':int(np.count_nonzero(a)),'jump21_opaque_pixels':sum(bool(v) for v in native(21,0,0)[3][0]),'area_check_is_not_anatomical_proof':True})
    (OUT/'spin_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'issues':issues,'compression':compression,'base_native_size':list(a.shape[::-1]),'base_pixels':int(np.count_nonzero(a)),'accent':accent}))


if __name__=='__main__':main()
