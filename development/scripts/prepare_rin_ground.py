"""린 지상3연타 원화를 동일 축척으로 조립하고 원래 검기를 보호한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.prepare_riko_jump import components
from scripts.build_rin_idle import entry
from scripts.build_riko_idle import GROUND_SLASH_BODY_FRAMES as IDS,GROUND_SLASH_EFFECT_FRAMES as EFFECTS
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_set
from src.psx_compress import encode_stream

OUT=ROOT/'work/ver_rin_nana/ground_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_hurt_20261028T110922534247Z'
KEYS=[61,62,63,65,67,82,83,85,87,89,91,105,107,109,111,130,131,133]
SCALE=.19
MAPPING={n:n for n in IDS}
MAPPING.update({n:67 for n in [69,71,73,75,77,79,81]})
MAPPING.update({n:91 for n in [93,95,97,99,101]})
MAPPING.update({n:111 for n in [113,115,117,119,121,123,125,127]})
MAPPING.update({132:131,134:133})
EYES={61:-2,62:-2,63:-5,65:-7,67:-9,82:-2,83:-6,85:-8,87:-3,89:-3,91:-2,105:-2,107:-2,109:-7,111:-14,130:-4,131:-2,133:-2}

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);original_parts=parts
    parts=bytearray(parts)
    for n,deltas in {83:{0:3,1:3},107:{3:-10},113:{0:3,1:3,6:4,7:4},115:{0:2,1:2},117:{0:2,1:2}}.items():
        for q in composition_frame(parts,0,n)['parts']:
            if q['index'] in deltas:parts[q['record_offset']+2]=(q['x']+deltas[q['index']])&255
    parts=bytes(parts)
    words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,0);colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    source=OUT/'generated_ground.png';im=Image.open(source).convert('RGBA');crops=components(im,18);crops.sort(key=lambda v:(int((v[0][1]+v[0][3])/2*3/im.height),v[0][0]));poses={}
    fixed=Image.open(OUT/'generated_grip105.png').convert('RGBA')
    if fixed.size!=im.size:raise ValueError('Grip repair changed canvas scale')
    fc=components(fixed,18);fc.sort(key=lambda v:(int((v[0][1]+v[0][3])/2*3/im.height),v[0][0]));crops[11]=fc[11]
    for n,(box,crop) in zip(KEYS,crops):
        a=quantize(crop,colors,SCALE);groups=connected_groups(a>0)
        if any(len(q)>3 for q in groups[1:]):raise ValueError(f'Detached source art {n}')
        clean=np.zeros_like(a);q=groups[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]];yy,xx=np.nonzero(clean);poses[n]=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
    lunges={};lunge_source=OUT/'generated_lunge_margin.png';lunge_im=Image.open(lunge_source).convert('RGBA');lc=components(lunge_im,4);lc.sort(key=lambda v:(int((v[0][1]+v[0][3])/lunge_im.height),v[0][0]))
    for i,(box,crop) in enumerate(lc):
        a=quantize(crop,colors,.1);groups=connected_groups(a>0)
        if any(len(q)>3 for q in groups[1:]):raise ValueError('Detached lunge')
        clean=np.zeros_like(a);q=groups[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]];yy,xx=np.nonzero(clean);lunges[i]=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
    lunge_keys={111:0,113:1,115:2,117:2,119:2,121:3,123:3,125:3,127:3}
    frames={};records={};issues=[];previews={}
    for n in sorted(IDS):
        key=MAPPING[n];a=lunges[lunge_keys[n]] if n in lunge_keys else poses[key];h,w=a.shape;f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]]=False
        ey,ex=np.nonzero((a==15)&(np.indices(a.shape)[0]<h*.55));eye=float(ex.mean()) if len(ex) else w*.3
        ideal_x=EYES[key]-bounds[0]-eye+(1 if n==93 else -1 if n==113 else 0);ideal_y=23-bounds[1]-(h-1);options=[]
        for y in [int(ideal_y)]:
            if y<0 or y+h>size[1]:continue
            for x in ([round(ideal_x)] if n in lunge_keys else range(max(0,size[0]-w+1))):
                if x<0 or x+w>size[0]:continue
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,abs(x-ideal_x),x,y))
        if not options:issues.append({'frame':n,'art':[w,h],'canvas':size,'ideal_y':ideal_y});continue
        bad,_,x,y=min(options);pixels=np.zeros((size[1],size[0]),np.uint8);pixels[y:y+h,x:x+w]=a
        if bad:
            by,bx=np.nonzero((a>0)&~safe[y:y+h,x:x+w]);issues.append({'frame':n,'outside':bad,'coords':[[int(xx+x+bounds[0]),int(yy+y+bounds[1])] for xx,yy in zip(bx,by)]})
        frames[n]=(pixels.tobytes(),size);records[str(n)]={'source_key':key,'lunge_key':lunge_keys.get(n),'native_size':[w,h],'bounds':bounds,'placement':[x,y],'eye_world':x+bounds[0]+eye,'floor':y+bounds[1]+h-1,'outside_safe_parts':bad}
    # Align recovery133's source pixels with134 for LZ compression without
    # changing a single displayed world pixel. Same tile count and tile IDs.
    if 133 in frames:
        px,sz=frames[133];a=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);v=np.zeros_like(a)
        if a[:,-2:].any():raise ValueError('Packing registration would clip art')
        v[:,2:]=a[:,:-2];frames[133]=(v.tobytes(),sz);updated=bytearray(parts)
        for q in composition_frame(parts,0,133)['parts']:updated[q['record_offset']+2]=(q['x']-2)&255
        parts=bytes(updated);rec=records['133'];bb=rec['bounds'];rec['bounds']=[bb[0]-2,bb[1],bb[2]-2,bb[3]];rec['placement'][0]+=2
        rec['packing_registration']={'parts_dx':-2,'indices_dx':2,'displayed_world_pixels_preserved':True}
    compression=[]
    if not issues:
        groups={}
        for n in frames:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
        for offset,ns in groups.items():
            f=bank['frames'][ns[0]];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data;effects=[e for e in EFFECTS if bank['frames'][e]['offset']==offset]
            try:packed=edit_frame_set(raw,f['tile_count'],[(composition_frame(parts,0,n),*frames[n]) for n in ns],preserved_compositions=[composition_frame(parts,0,e) for e in effects],overlap_policy='equal_sources' if 81 in ns else 'reject')
            except ValueError as e:issues.append({'frames':ns,'error':str(e)});continue
            code=encode_stream(packed);budget=f['limit']-offset;compression.append({'frames':ns,'preserved_effects':effects,'encoded_bytes':len(code),'budget':budget})
            if len(code)>budget:issues.append({'frames':ns,'overflow':len(code)-budget})
    board=Image.new('RGB',(8*240,5*288),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(sorted(frames)):
        pixels,size=frames[n];path=OUT/f'frame_{n:03d}.png';pic=save_image(pixels,size,words,path);bounds=records[str(n)]['bounds']
        cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+bounds[0],48+bounds[1]));cell=cell.resize((240,288),Image.Resampling.NEAREST);board.paste(cell,(i%8*240,i//8*288),cell);draw.text((i%8*240+8,i//8*288+8),str(n),fill='white')
        records[str(n)].update({'file':path.name,'sha256':digest(path)})
    board.save(OUT/'review_3x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'source':source.name,'source_sha256':digest(source),'prompt':'prompt_ground.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(original_parts,parts)) if a!=b],'preserved_effect_frames':sorted(EFFECTS),'compression':compression,'issues':issues,'applied':False}
    report['lunge_source']={'file':lunge_source.name,'sha256':digest(lunge_source),'uniform_scale':.1,'prompt':'prompt_lunge.txt','repair_prompt':'prompt_lunge_margin.txt'}
    report['grip105_revision']={'source':'generated_grip105.png','sha256':digest(OUT/'generated_grip105.png'),'used_key':105,'prompt':'prompt_grip105.txt','other17_keys_preserved_from_original_generation':True}
    (OUT/'ground_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'issues':[{k:v for k,v in q.items() if k!='coords'} for q in issues],'compression':compression,'sizes':{n:list(a.shape[::-1]) for n,a in poses.items()}}))

if __name__=='__main__':main()
