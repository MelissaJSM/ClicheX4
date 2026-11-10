"""린 공중 베기·공격 중 착지를 등록하고 원래 검기와 압축 슬롯을 검사한다."""
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.prepare_riko_jump import components
from scripts.build_rin_idle import entry
from scripts.build_riko_idle import AIR_SLASH_BODY_FRAMES as IDS,AIR_SLASH_EFFECT_FRAMES as EFFECTS
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage,edit_frame_set
from src.psx_compress import encode_stream

OUT=ROOT/'work/ver_rin_nana/air_slash_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_ground_20261028T113205974189Z'
AIR=list(range(213,230,2));LAND=list(range(230,247,2));SCALE=.15

def split(path):
    im=Image.open(path).convert('RGBA');cs=components(im,9)
    cs.sort(key=lambda v:(int((v[0][1]+v[0][3])/2*3/im.height),v[0][0]))
    return cs

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);oldparts=parts
    adjusted=bytearray(parts)
    shifts={234:{8:2,9:2,10:2}}
    for n,deltas in shifts.items():
        for q in composition_frame(parts,0,n)['parts']:
            if q['index'] in deltas:adjusted[q['record_offset']+2]=(q['x']+deltas[q['index']])&255
    parts=bytes(adjusted)
    words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,0)
    colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    poses={};accent_restored=[];cs=split(OUT/'generated_air.png');cs[1]=split(OUT/'generated_air_grip_fix.png')[1]
    landing=split(OUT/'generated_landing.png');fold=split(OUT/'generated_landing_clean.png')
    for i in (4,5,6):landing[i]=fold[i]
    for n,(_,crop) in zip(AIR+LAND,cs+landing):
        a=quantize(crop,colors,SCALE)
        if not np.any(a[:round(a.shape[0]*.6)]==15):
            rgba=np.asarray(crop);nearest=np.argmin(((rgba[:,:,:3].astype(np.int32)[:,:,None]-colors[None,None])**2).sum(axis=3),axis=2)+1
            mask=(nearest==15)&(rgba[:,:,3]>=128);mask[round(mask.shape[0]*.6):]=False
            clusters=connected_groups(mask)
            if not clusters:raise ValueError(f'No cyan eye in generated source {n}')
            ey,ex=clusters[0].mean(axis=0);ay=min(a.shape[0]-1,round(ey*SCALE));ax=min(a.shape[1]-1,round(ex*SCALE))
            if not a[ay,ax]:raise ValueError('Eye accent outside body')
            a[ay,ax]=15;accent_restored.append({'frame':n,'source_eye_xy':[float(ex),float(ey)],'quantized_eye_xy':[ax,ay]})
        gs=connected_groups(a>0)
        if any(len(q)>3 for q in gs[1:]):raise ValueError(f'Detached source art {n}')
        clean=np.zeros_like(a);q=gs[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]]
        yy,xx=np.nonzero(clean);poses[n]=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
    records={};frames={};issues=[]
    for n in sorted(IDS):
        a=poses[n];h,w=a.shape;f=bank['frames'][n];c=composition_frame(parts,0,n)
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]]=False
        ey,ex=np.nonzero((a==15)&(np.indices(a.shape)[0]<h*.6))
        if not len(ex):raise ValueError(f'No cyan eye {n}')
        eye=float(ex.mean());eye_y=float(ey.mean())
        target_eye=-4 if n in AIR else -4 if n in (230,232,244,246) else -7
        ideal_x=target_eye-bounds[0]-eye;ideal_y=(23-bounds[1]-(h-1)) if n in LAND else (-14-bounds[1]-eye_y)
        options=[]
        for y in ([round(ideal_y)] if n in LAND else range(max(0,size[1]-h+1))):
            if y<0 or y+h>size[1]:continue
            for x in range(max(0,size[0]-w+1)):
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,2*abs(x-ideal_x)+abs(y-ideal_y),x,y))
        if not options:issues.append({'frame':n,'art':[w,h],'canvas':size,'ideal_y':ideal_y});continue
        bad,_,x,y=min(options);pixels=np.zeros((size[1],size[0]),np.uint8);pixels[y:y+h,x:x+w]=a
        if bad:
            yy,xx=np.nonzero((a>0)&~safe[y:y+h,x:x+w]);issues.append({'frame':n,'outside':bad,'coords':[[int(px+x+bounds[0]),int(py+y+bounds[1])] for px,py in zip(xx,yy)]})
        shift=round(target_eye-(x+bounds[0]+eye))
        if shift:
            updated=bytearray(parts)
            for q in c['parts']:updated[q['record_offset']+2]=(q['x']+shift)&255
            parts=bytes(updated);bounds=(bounds[0]+shift,bounds[1],bounds[2]+shift,bounds[3])
        frames[n]=(pixels.tobytes(),size)
        records[str(n)]={'native_size':[w,h],'bounds':bounds,'placement':[x,y],'eye_world':[x+bounds[0]+eye,y+bounds[1]+eye_y],'floor':y+bounds[1]+h-1,'outside_safe_parts':bad,'whole_frame_x_registration':shift}
    compression=[]
    if not issues:
        groups={}
        for n in frames:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
        for offset,ns in groups.items():
            f=bank['frames'][ns[0]];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data;effects=[e for e in EFFECTS if bank['frames'][e]['offset']==offset]
            try:packed=edit_frame_set(raw,f['tile_count'],[(composition_frame(parts,0,n),*frames[n]) for n in ns],preserved_compositions=[composition_frame(parts,0,e) for e in effects])
            except ValueError as e:issues.append({'frames':ns,'error':str(e)});continue
            code=encode_stream(packed);budget=f['limit']-offset;compression.append({'frames':ns,'preserved_effects':effects,'encoded_bytes':len(code),'budget':budget})
            if len(code)>budget:issues.append({'frames':ns,'overflow':len(code)-budget})
    board=Image.new('RGB',(6*240,3*288),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(sorted(frames)):
        pixels,size=frames[n];path=OUT/f'frame_{n:03d}.png';pic=save_image(pixels,size,words,path);bounds=records[str(n)]['bounds']
        cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+bounds[0],48+bounds[1]));cell=cell.resize((240,288),Image.Resampling.NEAREST)
        board.paste(cell,(i%6*240,i//6*288),cell);draw.text((i%6*240+8,i//6*288+8),str(n),fill='white');records[str(n)].update({'file':path.name,'sha256':digest(path)})
    board.save(OUT/'review_3x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'sources':[{'file':f,'sha256':digest(OUT/f)} for f in ('generated_air.png','generated_air_grip_fix.png','generated_landing.png')],'prompts':['prompt_air.txt','prompt_air_grip_fix.txt','prompt_landing.txt'],'imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(oldparts,parts)) if a!=b],'preserved_effect_frames':sorted(EFFECTS),'compression':compression,'issues':issues,'applied':False}
    report['eye_accent_quantization']=accent_restored
    report['landing_fold_revision']={'file':'generated_landing_clean.png','sha256':digest(OUT/'generated_landing_clean.png'),'prompt':'prompt_landing_fold.txt','alpha_cleanup_prompt':'prompt_landing_alpha.txt','used_frames':[238,240,242]}
    (OUT/'air_slash_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'issues':issues,'compression':compression,'sizes':{n:list(a.shape[::-1]) for n,a in poses.items()}}))

if __name__=='__main__':main()
