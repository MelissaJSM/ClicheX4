"""생성한 상체를 기존 이동 하체에 등록하고 원작 타일·압축 제약을 검사한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.build_rin_idle import entry
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_indices
from src.psx_compress import encode_stream

OLD=ROOT/'work/ver_rin_nana/run_production/v1'
OUT=ROOT/'work/ver_rin_nana/run_production/v2'
PARENT=ROOT/'out/ver_rin_nana/rin_run_20261028T090848002789Z'
ORDER=list(range(7,21))+[3,4]

def translated(a,dx,dy):
    out=np.zeros_like(a)
    y0=max(0,dy);y1=min(64,64+dy);x0=max(0,dx);x1=min(64,64+dx)
    out[y0:y1,x0:x1]=a[y0-dy:y1-dy,x0-dx:x1-dx]
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);args=p.parse_args()
    source=args.source.resolve()
    if not source.is_relative_to(OUT):raise ValueError('Expected local versioned generation')
    im=Image.open(source).convert('RGBA')
    alternate_path=OUT/'generated_upper_v2.png'
    alternate=Image.open(alternate_path).convert('RGBA')
    alternate_ids={11,12,18,19}
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<16H',pal)
    colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    bank=graphics_bank(g,0);records={};issues=[];previews={};board=Image.new('RGB',(1024,1024),(35,38,48))
    before_board=Image.open(OUT/'edit_target.png').convert('RGBA')
    for i,n in enumerate(ORDER):
        sheet=alternate if n in alternate_ids else im
        cell=sheet.crop((round(i%4*sheet.width/4),round(i//4*sheet.height/4),round((i%4+1)*sheet.width/4),round((i//4+1)*sheet.height/4)))
        a=quantize(cell,colors,64/cell.width)
        # Alpha noise outside the main generated character is not sprite data.
        groups=connected_groups(a>0);main=groups[0];clean=np.zeros_like(a);clean[main[:,0],main[:,1]]=a[main[:,0],main[:,1]];a=clean
        f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        original,size,bounds,_=compose_indices(raw,f['tile_count'],c);old=np.frombuffer(original,np.uint8).reshape(size[1],size[0]);x=32+bounds[0];y=32+bounds[1]
        world=np.zeros((64,64),np.uint8)
        lx,ly=max(0,x),max(0,y);rx,by=min(64,x+size[0]),min(64,y+size[1])
        world[ly:by,lx:rx]=old[ly-y:by-y,lx-x:rx-x]
        if np.count_nonzero(world)!=np.count_nonzero(old):raise ValueError('Original sprite exceeds guide canvas')
        # Use unchanged calves and feet for whole-pose registration. No body rescale.
        choices=[]
        for dy in range(-3,4):
            for dx in range(-3,4):
                shifted=translated(a,dx,dy)
                mismatch=np.count_nonzero((shifted[41:]>0)!=(world[41:]>0))
                mismatch+=np.count_nonzero((shifted[41:]!=world[41:])&(world[41:]>0))*.15
                choices.append((mismatch,abs(dx)+abs(dy),dx,dy))
        _,_,dx,dy=min(choices);a=translated(a,dx,dy)
        # Preserve every pixel from the lower skirt/hip line downward, including transparent pixels.
        coverage,_,_=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in coverage]).reshape(size[1],size[0])
        for q in c['parts']:
            if q['tile']%16==0:safe[q['y']-bounds[1]:q['y']-bounds[1]+16,q['x']-bounds[0]]=False
        # Subpixel registration errors are resolved by a whole-upper translation,
        # never by clipping the ribbon or rescaling a body part.
        cut=36;registration=[]
        for sy in (-1,0,1):
            for sx in (-1,0,1):
                upper=translated(a,sx,sy);candidate=world.copy();candidate[:cut]=upper[:cut]
                cropped=np.zeros_like(old);cropped[ly-y:by-y,lx-x:rx-x]=candidate[ly:by,lx:rx]
                bad=int(np.count_nonzero(candidate)-np.count_nonzero(cropped))+int(np.count_nonzero((cropped>0)&~safe))
                groups=connected_groups(cropped>0)
                registration.append((bad,max(0,len(groups)-1),abs(sx)+abs(sy),abs(sy),sx,sy))
        bad,detached,_,_,sx,sy=min(registration);a=translated(a,sx,sy)
        combined=world.copy();combined[:cut]=a[:cut]
        result=np.zeros_like(old);result[ly-y:by-y,lx-x:rx-x]=combined[ly:by,lx:rx]
        outside_canvas=int(np.count_nonzero(combined)-np.count_nonzero(result))
        if outside_canvas:issues.append({'frame':n,'outside_canvas':outside_canvas})
        if detached:issues.append({'frame':n,'detached_groups':detached})
        outside=int(np.count_nonzero((result>0)&~safe));code=None
        if outside:issues.append({'frame':n,'outside_safe_parts':outside})
        else:
            packed=edit_frame_indices(raw,f['tile_count'],c,result.tobytes(),size);code=encode_stream(packed)
            if len(code)>f['limit']-f['offset']:issues.append({'frame':n,'overflow':len(code)-(f['limit']-f['offset'])})
        if not np.array_equal(combined[cut:],world[cut:]):raise ValueError('Protected lower body differs')
        path=OUT/f'frame_{n:03d}.png';pic=save_image(result.tobytes(),size,words,path)
        cell_pic=Image.new('RGBA',(64,64));cell_pic.alpha_composite(pic.convert('RGBA'),(x,y));previews[n]=cell_pic
        big=cell_pic.resize((256,256),Image.Resampling.NEAREST);board.paste(big,(i%4*256,i//4*256),big)
        records[str(n)]={'file':path.name,'sha256':digest(path),'source_sheet':alternate_path.name if n in alternate_ids else source.name,'registration':[dx,dy],'upper_registration':[sx,sy],'bounds':bounds,'protected_world_y_from':cut-32,'lower_pixels_identical':True,'opaque_pixels':int(np.count_nonzero(result)),'upper_changed_pixels':int(np.count_nonzero(combined[:cut]!=world[:cut])),'connected_component_sizes':[len(q) for q in connected_groups(result>0)],'encoded_bytes':len(code) if code else None,'budget':f['limit']-f['offset']}
    for n in (5,6):
        path=OUT/f'frame_{n:03d}.png';path.write_bytes((OLD/path.name).read_bytes());records[str(n)]={'file':path.name,'sha256':digest(path),'unchanged':True}
    (OUT/'composition_entry.bin').write_bytes(parts)
    r=json.loads((OLD/'run_recipe.json').read_text('utf-8'));r.update({'source':source.name,'source_sha256':digest(source),'alternate_source':alternate_path.name,'alternate_sha256':digest(alternate_path),'alternate_frames':sorted(alternate_ids),'prompt':'prompt_upper.txt','alternate_prompt':'prompt_upper_v2.txt','frames':records,'issues':issues,'composition_sha256':digest(OUT/'composition_entry.bin'),'upper_revision':True,'protected_world_y_from':4,'composition_unchanged_from_run_v1':True,'master_head_source':'imagegen upper-body edit; no pasted rigid head','head_native_pixels_preserved':False,'runtime_verified':False})
    (OUT/'run_recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf-8');board.save(OUT/'run_review_4x.png')
    for slow in (1,4):
        seq=[]
        for n in range(7,21):
            bg=Image.new('RGB',(256,256),(35,38,48));pic=previews[n].resize((256,256),Image.Resampling.NEAREST);bg.paste(pic,(0,0),pic);seq.append(bg)
        elapsed=0;duration=[]
        for tick in r['run_ticks']:
            start=round(elapsed*100/60)*10;elapsed+=tick;duration.append((round(elapsed*100/60)*10-start)*slow)
        seq[0].save(OUT/f'run_preview_{slow}time.gif',save_all=True,append_images=seq[1:],duration=duration,loop=0)
    print(json.dumps({'issues':issues,'frames':{n:[v.get('encoded_bytes'),v.get('budget')] for n,v in records.items()}}))

if __name__=='__main__':main()
