"""나나 두 포즈 원화를 미국판 X 좌표·팔레트·압축 제약으로 정규화한다. BIN은 쓰지 않는다."""
import argparse
import json
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scripts.discover_inputs import psx_arc, sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank, bank_offsets, composition_frame, decode_stream, compose_indices, indexed_atlas
from src.psx_frame_edit import frame_coverage, edit_frame_indices
from src.psx_compress import encode_stream, replace_stream

SOURCE = ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z'
PARENT = ROOT/'out/ver_rin_nana/rin_common_20261029T051459667484Z'
COLORS = [(24,24,32),(48,48,56),(80,80,88),(128,128,136),
          (104,24,48),(176,48,80),(216,72,112),(240,120,152),(255,176,192),
          (192,128,112),(232,184,160),(255,224,200),(248,240,224),
          (120,176,64),(64,160,176)]

def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')

def normalize(crop, height, palette, *, width=None):
    # Same width correction for both poses; generated wide hair is registered
    # to the established 32-pixel upper-body tile envelope without clipping.
    if width is None:width=round(crop.width*height/crop.height*0.90)
    a=np.array(crop); active=np.arange(1,16)
    labels=np.zeros(a.shape[:2],np.uint8)
    for y in range(len(a)):
        delta=a[y,:,:3].astype(np.int32)[:,None,:]-palette[None,1:,:]
        labels[y]=1+(delta*delta).sum(2).argmin(1)
    votes=[np.array(Image.fromarray(np.where(labels==i,a[:,:,3],0).astype(np.uint8)).resize((width,height),Image.Resampling.BOX)) for i in active]
    result=1+np.stack(votes).argmax(0).astype(np.uint8)
    alpha=np.array(crop.getchannel('A').resize((width,height),Image.Resampling.BOX))
    result[alpha<128]=0
    return result

def prepare(art, output):
    art=art.resolve();output=output.resolve()
    if not art.is_relative_to(ROOT/'work/ver_rin_nana') or not output.is_relative_to(ROOT/'out/ver_rin_nana'):
        raise ValueError('Variant path mismatch')
    if output.exists():raise ValueError('Fresh output required')
    inv=json.loads((SOURCE/'inventory.json').read_text('utf8'))
    original=(SOURCE/'original.arc').read_bytes()
    if sha256(original)!=inv['archive']['sha256']:raise ValueError('Original extraction changed')
    def entries(data):
        return {int(e['type'],16):data[e['offset']:e['offset']+e['size']] for e in psx_arc(data)}
    src=entries(original);current=entries((PARENT/'common/PL00_U.ARC').read_bytes())
    for key in (2,3,9):
        if src[key]!=current[key]:raise ValueError('Current X art differs from extraction')
    ref=ROOT/'character/ver_rin_nana/nana(X).webp'
    if sha256(ref.read_bytes())!='225ef208df912c89c54a19e2cd1ac5a61a6736b402670de83cca9b3034ae217e':raise ValueError('Reference changed')
    gfx,parts=src[2],src[3];bank=graphics_bank(gfx,0,allow_bank_aliases=True)
    im=Image.open(art/'generated.png').convert('RGBA')
    if im.getchannel('A').getextrema()!=(0,255):raise ValueError('Transparent generation required')
    words=[0]+[0x8000|((r*31+127)//255)|((g*31+127)//255)<<5|((b*31+127)//255)<<10 for r,g,b in COLORS]
    pal=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    if len(set(words))!=16:raise ValueError('Palette collision')
    output.mkdir(parents=True)
    frames=[];modified=gfx
    for i,n in enumerate((0,85)):
        section=im.crop((i*im.width//2,0,(i+1)*im.width//2,im.height))
        aa=np.array(section.getchannel('A'));yy,xx=np.nonzero(aa>=128)
        box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
        pix=normalize(section.crop(box),45,pal)
        desc=bank['frames'][n];comp=composition_frame(parts,0,n)
        raw=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
        coverage,size,bounds=frame_coverage(raw.data,desc['tile_count'],comp)
        foot=np.nonzero(pix[-3:])[1];center=(int(foot.min())+int(foot.max()))/2
        # Both poses share idle X's support center (-1) and bottom contact y=22.
        x=round(-1-bounds[0]-center);y=23-bounds[1]-pix.shape[0]
        if min(x,y)<0 or x+pix.shape[1]>size[0] or y+pix.shape[0]>size[1]:raise ValueError('Artwork exceeds native canvas')
        canvas=np.zeros(size[::-1],np.uint8);canvas[y:y+pix.shape[0],x:x+pix.shape[1]]=pix
        outside=np.count_nonzero(canvas.flatten()[np.array([not c for c in coverage])])
        if outside:
            save_image(canvas.tobytes(),size,words,output/f'failed_{n:03d}.png').convert('RGBA').resize((384,384),Image.Resampling.NEAREST).save(output/f'failed_{n:03d}_8x.png')
            bad=np.argwhere((canvas!=0)&np.array([not c for c in coverage]).reshape(canvas.shape))
            raise ValueError(f'Frame {n}: {outside} pixels outside parts at {bad.tolist()}, placement {x,y}, scaled {pix.shape}; revise artwork')
        packed=edit_frame_indices(raw.data,desc['tile_count'],comp,canvas.tobytes(),size)
        encoded=encode_stream(packed)
        if decode_stream(encoded,0,len(encoded),len(packed)).data!=packed:raise ValueError('Codec roundtrip differs')
        if compose_indices(packed,desc['tile_count'],comp)[:2]!=(canvas.tobytes(),size):raise ValueError('Composition differs')
        allowed={q['tile'] for q in comp['parts']}
        old_atlas=indexed_atlas(raw.data,desc['tile_count'])[0]
        new_atlas=indexed_atlas(packed,desc['tile_count'])[0]
        for t in range(desc['tile_count']):
            if t in allowed:continue
            for row in range(16):
                start=((t>>4)*16+row)*256+(t&15)*16
                if old_atlas[start:start+16]!=new_atlas[start:start+16]:raise ValueError('Armor tile changed')
        fit=len(encoded)<=desc['limit']-desc['offset']
        if fit:modified,_=replace_stream(modified,desc,packed)
        picture=save_image(canvas.tobytes(),size,words,output/f'nana_{n:03d}_indexed.png')
        picture.convert('RGBA').save(output/f'nana_{n:03d}.png')
        picture.convert('RGBA').resize((288,288),Image.Resampling.NEAREST).save(output/f'nana_{n:03d}_6x.png')
        (output/f'nana_{n:03d}.packed4').write_bytes(packed)
        (output/f'nana_{n:03d}.compressed').write_bytes(encoded)
        frames.append({'frame':n,'section':i,'crop_in_section':box,'scaled_size':list(pix.shape[::-1]),'placement':[x,y],
            'world_bounds':list(bounds),'size':list(size),'support_center_world':bounds[0]+x+center,'sole_world_y':22,
            'opaque_bbox':picture.convert('RGBA').getbbox(),'opaque_pixels':int(np.count_nonzero(canvas)),
            'colors_used':len(set(canvas.flat)-{0}),'coverage_outside':int(outside),'encoded_bytes':len(encoded),
            'original_budget':desc['limit']-desc['offset'],'fits_original_slot':fit,'codec_roundtrip':True,'armor_tiles_preserved':True})
    changed=[];total=0
    for bi in range(len(bank_offsets(gfx,allow_aliases=True))):
        for d in graphics_bank(gfx,bi,allow_bank_aliases=True)['frames']:
            a=decode_stream(gfx,d['offset'],d['limit'],d['tile_count']*128).data
            b=decode_stream(modified,d['offset'],d['limit'],d['tile_count']*128).data;total+=1
            if a!=b:changed.append([bi,d['index']])
    expected=[[0,f['frame']] for f in frames if f['fits_original_slot']]
    if changed!=expected:raise ValueError('Unselected compressed reference changed')
    if all(f['fits_original_slot'] for f in frames):(output/'candidate_graphics_entry.bin').write_bytes(modified)
    (output/'palette.bin').write_bytes(struct.pack('<16H',*words))
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    board=Image.new('RGB',(960,350),'#222630');draw=ImageDraw.Draw(board)
    for i,(n,is_nana,label) in enumerate([(0,False,'원작 X 대기'),(0,True,'나나 대기'),(85,False,'원작 X 사격'),(85,True,'나나 사랑이 사격')]):
        path=output/f'nana_{n:03d}.png' if is_nana else SOURCE/f'base_{n:03d}.png'
        pic=Image.open(path).convert('RGBA');bb=next(f['world_bounds'] for f in frames if f['frame']==n)
        draw.text((i*240+12,8),label,font=font,fill='white')
        for scale,origin in [(1,(i*240+130,70)),(4,(i*240+130,205))]:
            p=pic.resize((pic.width*scale,pic.height*scale),Image.Resampling.NEAREST)
            board.paste(p,(origin[0]+bb[0]*scale,origin[1]+bb[1]*scale),p)
            draw.line((i*240+8,origin[1]+23*scale,i*240+231,origin[1]+23*scale),fill='#526075')
    draw.text((12,320),'정적 기준안 · 1배/4배 · 실제 게임 적용 화면 아님',font=font,fill='#cad2e0');board.save(output/'review_1x_4x.png')
    background=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z/runtime_framebuffer_0.png'
    scene=Image.open(background).convert('RGBA')
    for n,x in ((0,165),(85,224)):scene.alpha_composite(Image.open(output/f'nana_{n:03d}.png').convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT),(x,146))
    scene.save(output/'background_composite_1x.png')
    back=Image.new('RGB',(960,764),'#222630');ImageDraw.Draw(back).text((10,8),'합성 미리보기 · 실제 실행 증거 아님',font=font,fill='white')
    back.paste(scene.resize((960,720),Image.Resampling.NEAREST),(0,44));back.save(output/'background_composite_3x.png')
    report={'task':'x_nana','status':'art_pilot_pending_user_review','frames':frames,'source_arc_sha256':sha256(original),
        'parent_build':PARENT.relative_to(ROOT).as_posix(),'source_generated':(art/'generated.png').relative_to(ROOT).as_posix(),
        'generated_sha256':sha256((art/'generated.png').read_bytes()),'prompt':(art/'prompt.txt').relative_to(ROOT).as_posix(),
        'tool':'built-in image_gen','normalization':'dominant palette area, RGB555, no dithering, common 45-pixel height / 0.90 width factor',
        'palette_words':words,'transparent_index':0,'all_graphics_references_checked':total,'changed_references':changed,
        'parts_and_animations_changed':False,'game_applied':False,'runtime_verified':False,'art_approved':False,
        'background_is_composite':True,'muzzle_alignment':'Original frame 85 reference; exact firing flash runtime pending',
        'palette_scope':'candidate only; not applied to all X states or armor'}
    write(output/'candidate.json',report)
    print(json.dumps({'output':str(output),'frames':frames,'references_checked':total,'game_applied':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();prepare(a.art,a.output)
