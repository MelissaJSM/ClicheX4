"""린 빙열참과 공용 회복 자세. 얼음 검(parts6)은 원본을 보존한다."""
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
from src.psx_ice import BODY,PRESERVED_EFFECTS,flash_from_recovery
OUT=ROOT/'work/ver_rin_nana/ice_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_spin_20261028T131143880636Z';SCALE=.12


def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);oldparts=parts
    words=struct.unpack_from('<16H',pal);colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    def native(n,bi=1,pi=5):
        f=graphics_bank(g,bi)['frames'][n];c=composition_frame(parts,pi,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        return f,c,raw,compose_indices(raw,f['tile_count'],c)
    def original_world(n,bi=1,pi=5):
        pixels,size,b,_=native(n,bi,pi)[3];w=np.zeros((192,192),np.uint8);w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);return w
    source=OUT/'generated_ice.png';groups=source_groups(source,4);height=Image.open(source).height;groups=sorted(groups,key=lambda q:(q[0][1]//(height//2),q[0][0]));poses={};source_records={}
    for n,(box,crop) in zip((134,135,138,140),groups):
        a=quantize(crop,colors,SCALE);gs=connected_groups(a>0)
        if any(len(q)>3 for q in gs[1:]):raise ValueError(f'Disconnected ice art {n}')
        clean=np.zeros_like(a);q=gs[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]];a=clean;h,w=a.shape;ey,ex=np.nonzero((a==15)&(np.indices(a.shape)[0]<h*.65))
        if not len(ex):raise ValueError(f'No ice eye {n}')
        eye=[float(ex.mean()),float(ey.mean())];x=round(-8-eye[0]);y=round(-21-eye[1]) if n<138 else 24-h;world=np.zeros((192,192),np.uint8);world[96+y:96+y+h,96+x:96+x+w]=a;poses[n]=world
        source_records[str(n)]={'source_bounds':box,'native_size':[w,h],'world_top_left':[x,y],'eye_world':[x+eye[0],y+eye[1]],'opaque_pixels':int(np.count_nonzero(a))}
    worlds={132:original_world(132),133:np.roll(poses[134],1,axis=0),134:poses[134],135:poses[135],136:poses[134],137:poses[134],138:poses[138],139:poses[140],140:poses[140],141:poses[140],142:poses[140],143:poses[140]}
    # Four falling references share the complete lower body tiles. Keep those
    # world pixels identical; only independent head/ribbon tiles use pose B.
    for n in (135,137):worlds[n]=worlds[n].copy();worlds[n][96:]=poses[134][96:]
    worlds[86]=original_world(147,0,0)
    for n in (87,95,96,98,99):worlds[n]=original_world(246,0,0)
    flash=flash_from_recovery(worlds[87].tobytes(),(192,192))[0];worlds[88]=np.frombuffer(bytes(11 if v==15 else 10 if v==12 else v for v in flash),np.uint8).reshape(192,192)
    # Horizontal tile-row registration changes display windows, not body placement.
    adjusted=bytearray(parts);row_edits=[];issues=[]
    for n in sorted(BODY-{132}):
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
            if bad:issues.append({'frame':n,'row':row,'outside_row':bad})
            if shift:
                for q in ps:adjusted[q['record_offset']+2]=(q['x']+shift)&255
                row_edits.append({'frame':n,'row_y':row,'x_shift':shift})
    # One-pixel tile registration reduces encoding from1128 to1102 bytes;
    # the fixed world-space drawing and shared lower legs stay identical.
    for n in (134,):
        for q in composition_frame(adjusted,5,n)['parts']:
            if q['y']==-16:adjusted[q['record_offset']+2]=(q['x']+1)&255
        row_edits.append({'frame':n,'row_y':-16,'x_shift':1,'reason':'lossless_packing_registration'})
    parts=bytes(adjusted);frames={};records={}
    for n in sorted(BODY):
        f,c,raw,_=native(n);cover,size,b=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0]);world=worlds[n];pixels=world[96+b[1]:96+b[3],96+b[0]:96+b[2]].copy();count=int(np.count_nonzero(world));bad=int(np.count_nonzero((pixels>0)&~safe));cropped=count-int(np.count_nonzero(pixels))
        if bad or cropped:issues.append({'frame':n,'outside_canvas':cropped,'outside_parts':bad})
        frames[n]=(pixels.tobytes(),size);records[str(n)]={'bounds':b,'opaque_pixels':count,'outside_safe_parts':bad,'source':'existing132' if n==132 else 'generated134_y_plus1' if n==133 else 'existing147' if n==86 else 'existing246' if n in (87,95,96,98,99) else 'flash87' if n==88 else 'generated_ice'}
    compression=[]
    if not issues:
        allframes=dict(frames)
        for n in PRESERVED_EFFECTS:allframes[n]=native(n)[3][:2]
        try:_,checks=patch_bank(g,parts,1,5,allframes,PRESERVED_EFFECTS,clear_unreferenced=True);compression=checks['compression']
        except ValueError as e:issues.append({'error':str(e)})
    board=Image.new('RGB',(5*288,4*288),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(sorted(frames)):
        pixels,size=frames[n];path=OUT/f'bank1_{n:03d}.png';pic=save_image(pixels,size,words,path);b=records[str(n)]['bounds'];cell=Image.new('RGBA',(96,96));cell.alpha_composite(pic.convert('RGBA'),(48+b[0],48+b[1]));cell=cell.resize((288,288),Image.Resampling.NEAREST);board.paste(cell,(i%5*288,i//5*288),cell);draw.text((i%5*288+8,i//5*288+8),str(n),fill='white');records[str(n)].update({'file':path.name,'sha256':digest(path)})
    board.save(OUT/'review_3x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'graphics_bank':1,'parts_bank':5,'source':source.name,'source_sha256':digest(source),'prompt':'prompt.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'source_keys':source_records,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'tile_row_registration':row_edits,'preserved_effect_frames':sorted(PRESERVED_EFFECTS),'preserved_authored_body_frames':[132],'external_ice_blade_parts6_edited':False,'compression':compression,'issues':issues,'applied':False}
    (OUT/'ice_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'issues':issues,'compression':compression,'source_keys':source_records}))


if __name__=='__main__':main()
