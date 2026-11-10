"""린 일반/강한 피격과 체력 부족 원화를 동일 축척으로 등록한다."""
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
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_hurt_launch import compose_launch
from src.psx_frame_edit import frame_coverage,edit_frame_set
from src.psx_compress import encode_stream
from src.rin_hurt import derive

OUT=ROOT/'work/ver_rin_nana/hurt_production/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_wall_20261028T104140560792Z'
SCALE=.1
KEYS=[135,139,149,152]

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9)
    original_parts=parts;parts=bytearray(parts)
    for n in (135,136,137):
        for q in composition_frame(parts,0,n)['parts'][:10]:
            if q['index'] in (8,9):parts[q['record_offset']+2]=(q['x']-6)&255
    for q in composition_frame(parts,0,138)['parts']:
        if q['index'] in (7,8,9):parts[q['record_offset']+2]=(q['x']+1)&255
    for n in (139,140,141,143,144,145):
        for q in composition_frame(parts,0,n)['parts'][:10]:
            delta=-1 if q['index'] in (2,3,4) or (n in (139,140,141) and q['index']==8) else 1 if n in (139,140,141) and q['index']==9 else 0
            parts[q['record_offset']+2]=(q['x']+delta)&255
    parts=bytes(parts)
    words=struct.unpack_from('<64H',pal);bank=graphics_bank(g,0)
    colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:16]],np.int32)
    source=OUT/'generated_hurt.png';im=Image.open(source).convert('RGBA');crops=components(im,4);crops.sort(key=lambda v:(int((v[0][1]+v[0][3])/im.height),v[0][0]))
    poses={}
    for n,(box,crop) in zip(KEYS,crops):
        a=quantize(crop,colors,SCALE);groups=connected_groups(a>0)
        if any(len(q)>3 for q in groups[1:]):raise ValueError(f'Detached art {n}')
        clean=np.zeros_like(a);q=groups[0];clean[q[:,0],q[:,1]]=a[q[:,0],q[:,1]];yy,xx=np.nonzero(clean);poses[n]=clean[yy.min():yy.max()+1,xx.min():xx.max()+1]
    frames={};records={};issues=[]
    for n in KEYS:
        a=poses[n];h,w=a.shape;f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        cover,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cover]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]]=False
        ey,ex=np.nonzero((a==15)&(np.indices(a.shape)[0]<20));eye=float(ex.mean()) if len(ex) else w*.3
        ideal_x=-4-bounds[0]-eye;ideal_y=24-bounds[1]-(h-1);options=[]
        for y in range(max(0,size[1]-h+1)):
            for x in range(max(0,size[0]-w+1)):
                bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]));options.append((bad,abs(x-ideal_x)*2+abs(y-ideal_y),x,y))
        if not options:issues.append({'frame':n,'art':[w,h],'canvas':size});continue
        bad,_,x,y=min(options)
        if n==152:
            # Both source poses have the same boot span. Anchor the planted feet,
            # allowing the head to bow naturally during the exhale.
            x=records['149']['placement'][0]
            bad=int(np.count_nonzero((a>0)&~safe[y:y+h,x:x+w]))
        pixels=np.zeros((size[1],size[0]),np.uint8);pixels[y:y+h,x:x+w]=a
        if bad:
            by,bx=np.nonzero((a>0)&~safe[y:y+h,x:x+w]);issues.append({'frame':n,'outside':bad,'coords':[[int(xx+x+bounds[0]),int(yy+y+bounds[1])] for xx,yy in zip(bx,by)]})
        frames[n]=(pixels.tobytes(),size);records[str(n)]={'source_key':n,'native_size':[w,h],'bounds':bounds,'placement':[x,y],'eye_world':x+bounds[0]+eye,'floor':y+bounds[1]+h-1,'outside_safe_parts':bad}
    streams={}
    if not issues:
        try:
            derived,streams=derive(g,parts,frames[135],frames[139]);frames.update(derived)
        except ValueError as e:issues.append({'derived_effect':str(e)})
    for n in range(149,155):
        key=149 if n<152 else 152
        if key not in frames:continue
        frames[n]=frames[key];records.setdefault(str(n),{'source_key':key,'same_registered_body':True})
    compression=[]
    if not issues:
        groups={}
        for n in frames:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
        for offset,ns in groups.items():
            f=bank['frames'][ns[0]];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
            try:packed=streams[ns[0]] if ns[0] in streams else edit_frame_set(raw,f['tile_count'],[(composition_frame(parts,0,n),*frames[n]) for n in ns])
            except ValueError as e:issues.append({'frames':ns,'error':str(e)});continue
            code=encode_stream(packed);budget=f['limit']-offset;compression.append({'frames':ns,'encoded_bytes':len(code),'budget':budget})
            if len(code)>budget:issues.append({'frames':ns,'overflow':len(code)-budget})
    board=Image.new('RGB',(5*320,4*384),(35,38,48));draw=ImageDraw.Draw(board)
    for i,n in enumerate(sorted(frames)):
        pixels,size=frames[n];path=OUT/f'frame_{n:03d}.png';pic=save_image(pixels,size,words if n in (140,141,143,145) else words[:16],path)
        f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;bounds=compose_launch(raw,f['tile_count'],composition_frame(parts,0,n))[2]
        cell=Image.new('RGBA',(80,96));cell.alpha_composite(pic.convert('RGBA'),(40+bounds[0],48+bounds[1]));cell=cell.resize((320,384),Image.Resampling.NEAREST);board.paste(cell,(i%5*320,i//5*384),cell);draw.text((i%5*320+8,i//5*384+8),str(n),fill='white')
        records.setdefault(str(n),{'derived_from':135 if n<139 else 139});records[str(n)].update({'file':path.name,'sha256':digest(path),'palette_banks':4 if n in (140,141,143,145) else 1})
    board.save(OUT/'review_4x.png');(OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],'source':source.name,'source_sha256':digest(source),'prompt':'prompt_hurt.txt','imagegen_mode':'built_in','uniform_scale':SCALE,'per_pose_resizing':False,'frames':records,'composition_sha256':digest(OUT/'composition_entry.bin'),'composition_x_edits':[],'compression':compression,'issues':issues,'applied':False}
    report['composition_x_edits']=[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(original_parts,parts)) if a!=b]
    (OUT/'hurt_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'issues':issues,'compression':compression,'sizes':{n:list(a.shape[::-1]) for n,a in poses.items()}}))

if __name__=='__main__':main()
