"""생성한 피격 외곽만 등록하고 기본형/부분 아머의 실제 몸과 타이밍을 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import label,binary_dilation,binary_erosion,distance_transform_edt
from PIL import Image,ImageDraw
from scripts.prepare_nana_hurt_aura_reference import PARENT,PARENT_SHA,FRAMES,bodies
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_shibuki_armor_remaining import pack_many
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import encode_stream,replace_stream

SOURCE=ROOT/'work/ver_rin_nana/nana_fourth_armor/hurt_aura_v1/generated.png'
SOURCE_SHA='76b298178b7f2066f44ba36dde25f1d5e64632397c0f60fccee1d8dce6283a34'

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh isolated output required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(SOURCE)==SOURCE_SHA,'Source changed')
    arc=(PARENT/'modified.arc').read_bytes();g,c,p=entry(arc,2),entry(arc,3),entry(arc,9);words=struct.unpack_from('<16H',p,32)
    variants=bodies(arc);base=variants[0];union=np.logical_or.reduce([v>0 for v in variants]);guard=binary_dilation(union,iterations=1);distance=distance_transform_edt(~union)
    fy,fx=np.nonzero(variants[15]);body_box=[int(fx.min()),int(fy.min()),int(fx.max()+1),int(fy.max()+1)]
    src=Image.open(SOURCE).convert('RGBA');require(src.getchannel('A').getextrema()==(0,255),'Transparent artwork required')
    bank=graphics_bank(g,0,allow_bank_aliases=True);ng=g;nc=bytearray(c);expected={};reports=[];changed_records={};out.mkdir(parents=True)
    board=Image.new('RGB',(1024,560),'#242934');draw=ImageDraw.Draw(board)
    for i,n in enumerate(FRAMES):
        cell=np.array(src.crop((i*src.width//2,0,(i+1)*src.width//2,src.height)));rgb=cell[:,:,:3].astype(np.int32);red,green,blue=rgb.transpose(2,0,1)
        cyan=(green>red+35)&(blue>red+35)&(green>80)&(blue>80)&(cell[:,:,3]>=96)
        character=(cell[:,:,3]>=160)&~cyan;labels,count=label(character);sizes=np.bincount(labels.flat);sizes[0]=0;main=labels==sizes.argmax();sy,sx=np.nonzero(main);crop=[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)]
        scale_x=(body_box[2]-body_box[0])/(crop[2]-crop[0]);scale_y=(body_box[3]-body_box[1])/(crop[3]-crop[1])
        size=(round(cell.shape[1]*scale_x),round(cell.shape[0]*scale_y));mask=np.array(Image.fromarray(np.where(cyan,cell[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX))>=80
        dx=body_box[0]-round(crop[0]*scale_x);dy=body_box[1]-round(crop[1]*scale_y);require(min(dx,dy)>=0 and dx+size[0]<=160 and dy+size[1]<=160,'Effect canvas overflow')
        effect_mask=np.zeros_like(union);effect_mask[dy:dy+size[1],dx:dx+size[0]]=mask;before_mask=int(np.count_nonzero(effect_mask));effect_mask&=~guard&(distance<=6)
        require(np.count_nonzero(effect_mask)>=60,'Generated contour too sparse after registration')
        fx=np.zeros_like(base);fx[effect_mask]=8 if n==235 else 13
        if n==236:fx[binary_erosion(effect_mask)]=5
        target=np.where(base,base,fx).astype(np.uint8);require(np.array_equal(target[union],base[union]),'Effect overwrites a partial-armor body')
        save_image(fx.tobytes(),(160,160),words,out/f'effect_{n}.png');save_image(target.tobytes(),(160,160),words,out/f'base_{n}.png')
        f=bank['frames'][n];require([q['index'] for q in bank['frames'] if q['offset']==f['offset']]==[n],'Unselected compression alias')
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;comp=composition_frame(c,0,n);writable={q['tile'] for q in comp['parts']};armor={q['tile'] for b in (5,6,7,8) for q in composition_frame(c,b,n)['parts']};require(not writable&armor,'Body/effect tiles shared with armor')
        packed,records=pack_many(raw,f['tile_count'],[target],writable,[len(comp['parts'])]);records=records[0]
        require(0<len(records)<=len(comp['parts']),'Part count expansion')
        for j,q in enumerate(comp['parts']):
            require(not(q['page'] or q['clut'] or q['unknown_flags']),'Unsupported part flags')
            tile,x,y,flag=records[min(j,len(records)-1)];value=struct.pack('<BBbb',flag,tile,x-80,y-80);pos=q['record_offset'];require(pos not in changed_records or changed_records[pos]==value,'Shared record conflict');changed_records[pos]=value;nc[pos:pos+4]=value
        require(np.array_equal(canvas_from_parts(packed,f['tile_count'],composition_frame(nc,0,n)),target),'Base/effect readback differs')
        before_atlas=indexed_atlas(raw,f['tile_count'])[0];after_atlas=indexed_atlas(packed,f['tile_count'])[0]
        for t in range(f['tile_count']):
            if t in writable:continue
            for y in range(16):
                pos=(t//16*16+y)*256+t%16*16;require(before_atlas[pos:pos+16]==after_atlas[pos:pos+16],'Armor/unused tile changed')
        code=encode_stream(packed);require(len(code)<=f['limit']-f['offset'],'Original compression slot exceeded');ng,compression=replace_stream(ng,f,packed);expected[n]=packed
        layers={b:canvas_from_parts(packed,f['tile_count'],composition_frame(c,b,n)) for b in (5,6,7,8)}
        for b in layers:require(np.array_equal(layers[b],canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,n))),'Armor raster changed')
        for mask_bits in range(16):
            merged=target.copy()
            for bit,b in ((8,8),(1,5),(4,7),(2,6)):
                if mask_bits&bit:merged=np.where(layers[b],layers[b],merged)
            require(np.array_equal(merged[variants[mask_bits]>0],variants[mask_bits][variants[mask_bits]>0]),'Visible body changed')
            save_image(merged.tobytes(),(160,160),words,out/f'frame_{n:03}_mask{mask_bits:02}.png')
        for row,im in enumerate((render(arc,n,True)[0],Image.open(out/f'frame_{n:03}_mask15.png').convert('RGBA'))):
            # A 4x preview with a fixed common actor-space crop.
            x=i*512;y=row*280+24;tile=im.crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);board.paste(tile,(x,y),tile);draw.text((x+4,row*280+4),f'{n} '+('before' if row==0 else 'fixed'),fill='white')
            body_im=render(arc,234,True)[0].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);board.paste(body_im,(x+256,y),body_im)
        reports.append({'frame':n,'source_crop':crop,'scale':[scale_x,scale_y],'registration':[dx,dy],'body_box':body_box,'generated_effect_pixels':before_mask,'registered_effect_pixels':int(np.count_nonzero(effect_mask)),'max_distance_to_any_outfit':float(distance[effect_mask].max()),'minimum_distance':float(distance[effect_mask].min()),'original_effect_pixels':int(np.count_nonzero((render(arc,n)[1]>0)&(base==0))),'writable_tiles':sorted(writable),'encoded_bytes':len(code),'capacity':f['limit']-f['offset'],'compression':compression})
    checked=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        oldb,newb=graphics_bank(g,bi,allow_bank_aliases=True),graphics_bank(ng,bi,allow_bank_aliases=True)
        require((oldb['base'],oldb['end'],len(oldb['frames']))==(newb['base'],newb['end'],len(newb['frames'])),'Bank layout changed')
        for a,b in zip(oldb['frames'],newb['frames']):
            require(a['tile_count']==b['tile_count'],'Tile count changed');old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data
            require(new==(expected[a['index']] if bi==0 and a['index'] in FRAMES else old),'Other graphic changed');checked+=1
    other=0
    for bi,off in enumerate(bank_offsets(c)):
        for n in range(struct.unpack_from('<I',c,off)[0]>>16):
            if bi==0 and n in FRAMES:continue
            require(composition_frame(c,bi,n)==composition_frame(nc,bi,n),'Other composition changed');other+=1
    allowed={pos+i for pos in changed_records for i in range(4)};require(all(i in allowed for i,(a,b) in enumerate(zip(c,nc)) if a!=b),'Composition outside scope')
    result=bytearray(arc)
    for kind,data in ((2,ng),(3,bytes(nc))):
        e=next(e for e in psx_arc(arc) if int(e['type'],16)==kind);require(len(data)==e['size'],'ARC entry grew');result[e['offset']:e['offset']+e['size']]=data
    (out/'modified.arc').write_bytes(result);board.save(out/'comparison_4x.png')
    approval=json.loads((ROOT/'projects/ver_rin_nana/nana_fourth_candidate.json').read_text('utf8'))
    write(out/'recipe.json',{'task':'fourth_armor_nana','scope':'hurt_aura','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'parent_arc_sha256':sha256(arc),'modified_arc_sha256':sha256(result),'frames':FRAMES,'partial_outfit_assignment':approval['partial_outfit_assignment'],'checked_bitmap_references':checked,'other_compositions_preserved':other,'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':SOURCE_SHA,'palette_bytes_identical':True,'all_body_and_armor_pixels_preserved':True,'effect_shared_with_basic_and_partial_armor':True,'reports':reports,'runtime_verified':False})
    print({'output':out.relative_to(ROOT).as_posix(),'arc_sha256':sha256(result),'reports':reports})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
