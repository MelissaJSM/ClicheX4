"""린 사다리32몸체를 원작의 기본 몸/뒤 레이어 공유 구조에 등록한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.prepare_rin_wall_saber import source_groups
from scripts.build_rin_idle import entry
from scripts.build_riko_idle import LADDER_BODY_FRAMES as IDS,LADDER_EFFECT_FRAMES as EFFECTS,LADDER_BASE_COUNTS as BASE
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_set,edit_frame_indices,edit_base_layer_set
from src.psx_compress import encode_stream
OUT=ROOT/'work/ver_rin_nana/ladder_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_wall_saber_20261028T121324194684Z'
KEYS=[174,178,182,186,190,192,193,194,195,197,199,202];SCALE=.15
ALIASES={191:192,196:195,201:199,204:202,206:202,208:202,210:202,212:197}

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);oldparts=parts
    words=struct.unpack_from('<16H',pal);bank=graphics_bank(g,0);colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    source=OUT/'generated_ladder.png';im=Image.open(source);cs=source_groups(source,12);cs.sort(key=lambda q:(int((q[0][1]+q[0][3])/2*3/im.height),q[0][0]))
    fixed=OUT/'generated_ladder_repairs.png';fi=Image.open(fixed);fc=source_groups(fixed,12);fc.sort(key=lambda q:(int((q[0][1]+q[0][3])/2*3/fi.height),q[0][0]))
    if im.size!=fi.size:raise ValueError('Repair changed sheet dimensions')
    for i in (4,5,6,8):cs[i]=fc[i]
    poses={};accent_restored=[]
    for n,(_,crop) in zip(KEYS,cs):
        a=quantize(crop,colors,SCALE)
        if n>=192 and not np.any(a[:round(a.shape[0]*.65)]==15):
            rgba=np.array(crop);nearest=np.argmin(((rgba[:,:,:3].astype(np.int32)[:,:,None]-colors[None,None])**2).sum(axis=3),axis=2)+1
            mask=(nearest==15)&(rgba[:,:,3]>=128);mask[round(mask.shape[0]*.65):]=False;clusters=connected_groups(mask)
            if not clusters:raise ValueError(f'No eye accent in original source {n}')
            ey,ex=clusters[0].mean(axis=0);ay=min(a.shape[0]-1,round(ey*SCALE));ax=min(a.shape[1]-1,round(ex*SCALE))
            if not a[ay,ax]:raise ValueError('Eye accent outside body')
            a[ay,ax]=15;accent_restored.append({'frame':n,'source_eye_xy':[float(ex),float(ey)],'quantized_eye_xy':[ax,ay]})
        gs=connected_groups(a>0)
        if any(len(q)>3 for q in gs[1:]):raise ValueError(f'Detached art {n}')
        clean=np.zeros_like(a);q=gs[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]];yy,xx=np.nonzero(clean);poses[n]=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
    def geo(n,base=False):
        f=bank['frames'][n];c=composition_frame(parts,0,n)
        if base and n in BASE:c={**c,'parts':c['parts'][:BASE[n]]}
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]+(15 if q['flip_x'] else 0)]=False
        return raw,c,size,bounds,safe
    worlds={};records={};issues=[]
    for n in KEYS:
        a=poses[n];h,w=a.shape;raw,c,size,bounds,safe=geo(n,True)
        if n in (174,178,182,186,190):
            mask=np.isin(a,(7,8,9,10,11))&(np.indices(a.shape)[0]<h*.5);groups=connected_groups(mask);head=groups[0]
            cx=(float(head[:,1].min())+float(head[:,1].max()))/2;hy=float(head[:,0].min());ideal_x=-cx-bounds[0];ideal_y=-24-hy-bounds[1]
        else:
            yy,xx=np.nonzero((a==15)&(np.indices(a.shape)[0]<h*.65))
            if not len(xx):raise ValueError(f'No face anchor {n}')
            ideal_x=-4-bounds[0]-float(xx.mean());ideal_y=(23-bounds[1]-(h-1)) if n in (192,193) else -14-bounds[1]-float(yy.mean())
        options=[]
        for y in ([round(ideal_y)] if n in (192,193) else range(max(0,size[1]-h+1))):
            if y<0 or y+h>size[1]:continue
            for x in range(max(0,size[0]-w+1)):
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,2*abs(x-ideal_x)+abs(y-ideal_y),x,y))
        if not options:issues.append({'frame':n,'art':[w,h],'canvas':size});continue
        bad,_,x,y=min(options);world=np.zeros((192,192),np.uint8);world[96+y+bounds[1]:96+y+bounds[1]+h,96+x+bounds[0]:96+x+bounds[0]+w]=a;worlds[n]=world
        if bad:
            by,bx=np.nonzero((a>0)&~safe[y:y+h,x:x+w]);issues.append({'frame':n,'outside':bad,'coords':[[int(xx+x+bounds[0]),int(yy+y+bounds[1])] for xx,yy in zip(bx,by)]})
        records[str(n)]={'source_key':n,'native_size':[w,h],'placement_world':[x+bounds[0],y+bounds[1]],'outside_safe_parts':bad}
    for n,key in ALIASES.items():
        if key not in worlds:continue
        worlds[n]=np.roll(worlds[key],-10,axis=0) if n==191 else worlds[key].copy();records[str(n)]={'source_key':key,'world_dy':-10 if n==191 else 0}
    if not issues:
        for key in (174,178,182,186):
            f=bank['frames'][key];_,c,size,bounds,_=geo(key,True);w=worlds[key];pixels=w[96+bounds[1]:96+bounds[3],96+bounds[0]:96+bounds[2]].tobytes()
            raw=edit_frame_indices(bytes(f['tile_count']*128),f['tile_count'],c,pixels,size)
            for n in range(key,key+4):
                cc=composition_frame(parts,0,n);a,s,b,_=compose_indices(raw,f['tile_count'],cc);w=np.zeros((192,192),np.uint8);w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=np.frombuffer(a,np.uint8).reshape(s[1],s[0]);worlds[n]=w
                records[str(n)]={'source_key':key,'base_part_count':BASE[n],'mirrored':cc['parts'][0]['flip_x']!=c['parts'][0]['flip_x'],'original_ponytail_overlay_empty':True}
    frames={}
    for n,w in worlds.items():
        raw,c,size,b,safe=geo(n);yy,xx=np.nonzero(w);a=w[96+b[1]:96+b[3],96+b[0]:96+b[2]]
        if n in BASE:
            # Mirrored aliases were composed from the safe packed base above.
            # An empty overlay's U0 can overlap a valid base pixel on screen.
            cover,_,_=frame_coverage(raw,bank['frames'][n]['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        bad=int(np.count_nonzero((a>0)&~safe))+int(np.count_nonzero((xx<96+b[0])|(xx>=96+b[2])|(yy<96+b[1])|(yy>=96+b[3])))
        if bad and not any(q.get('frame')==n for q in issues):issues.append({'frame':n,'alias_outside':bad})
        frames[n]=(a.tobytes(),size);records[str(n)]['bounds']=b
    compression=[]
    if not issues:
        groups={}
        for n in frames:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
        for offset,ns in groups.items():
            f=bank['frames'][ns[0]];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data;effects=[e for e in EFFECTS if bank['frames'][e]['offset']==offset]
            try:
                edits=[(composition_frame(parts,0,n),*frames[n]) for n in ns]
                packed=edit_base_layer_set(raw,f['tile_count'],[(*e,BASE[n]) for n,e in zip(ns,edits)]) if set(ns)<=BASE.keys() else edit_frame_set(raw,f['tile_count'],edits,preserved_compositions=[composition_frame(parts,0,e) for e in effects])
            except ValueError as e:issues.append({'frames':ns,'error':str(e)});continue
            code=encode_stream(packed);budget=f['limit']-offset;compression.append({'frames':ns,'preserved_effects':effects,'encoded_bytes':len(code),'budget':budget})
            if len(code)>budget:issues.append({'frames':ns,'overflow':len(code)-budget})
    board=Image.new('RGB',(8*240,4*288),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(sorted(frames)):
        pixels,size=frames[n];path=OUT/f'frame_{n:03d}.png';pic=save_image(pixels,size,words,path);b=records[str(n)]['bounds'];cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+b[0],48+b[1]));cell=cell.resize((240,288),Image.Resampling.NEAREST);board.paste(cell,(i%8*240,i//8*288),cell);draw.text((i%8*240+8,i//8*288+8),str(n),fill='white');records[str(n)].update({'file':path.name,'sha256':digest(path)})
    board.save(OUT/'review_3x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'sources':[{'file':s,'sha256':digest(OUT/s)} for s in ('generated_ladder.png','generated_ladder_repairs.png')],'prompts':['prompt_ladder.txt','prompt_ladder_repairs.txt'],'imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[],'base_part_counts':BASE,'preserved_effect_frames':sorted(EFFECTS),'compression':compression,'issues':issues,'applied':False}
    report['eye_accent_quantization']=accent_restored
    (OUT/'ladder_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'issues':issues,'compression':compression,'sizes':{n:list(a.shape[::-1]) for n,a in poses.items()}}))

if __name__=='__main__':main()
