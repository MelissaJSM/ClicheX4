"""승인된 생성 원출력을 게임용 4bpp 후보로 정규화·검사. BIN에는 쓰지 않는다."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_indices
from src.psx_compress import encode_stream
from scripts.project import load_project,inspect_references,write_json


def prepare(source,extracted,palette_path=None,resample='nearest'):
    source=source.resolve();extracted=extracted.resolve()
    if not source.is_relative_to((ROOT/'work/ver_buki_riko/art_pilot').resolve()):
        raise ValueError('Expected preserved generated image in first-project art work directory')
    if not extracted.is_relative_to((ROOT/'work/ver_buki_riko/zero_extract').resolve()):
        raise ValueError('Expected first-project extraction directory')
    inspect_references(ROOT,load_project(ROOT,'ver_buki_riko'))
    report=json.loads((extracted/'report.json').read_text(encoding='utf-8'))
    if hashlib.sha256((extracted/'original.arc').read_bytes()).hexdigest()!=report['archive']['sha256']:
        raise ValueError('Changed extraction archive')
    raw=Image.open(source).convert('RGBA');rgba=np.array(raw)
    mask=rgba[:,:,3]>=128
    ys,xs=np.nonzero(mask)
    if not len(xs):raise ValueError('Empty generated image')
    bbox=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
    crop=raw.crop(bbox)
    height=48;width=round(crop.width*height/crop.height)
    if width>48:raise ValueError('Silhouette too wide for automatic placement; art revision required')
    # 새로 생성된 아트의 격자를 게임 크기로 샘플링한다. 설정화 축소가 아니다.
    if resample not in ('nearest','area','palette-area'):
        raise ValueError('Unsupported resampling mode')
    # 생성 이미지의 불규칙한 확대 격자를 정규화한다. 면적 평균은 premultiplied alpha로
    # 투명 바탕 RGB의 테두리 번짐을 막고, 이후 불투명 15색으로 다시 확정한다.
    if resample in ('area','palette-area'):
        sampled=crop.convert('RGBa').resize((width,height),Image.Resampling.BOX).convert('RGBA')
    else:
        sampled=crop.resize((width,height),Image.Resampling.NEAREST)
    data=np.array(sampled);visible=data[:,:,3]>=128
    opaque_rgb=data[:,:,:3][visible]
    if palette_path:
        candidate=json.loads(palette_path.read_text(encoding='utf-8'))
        palette_rgb=np.array([c['rgb'] for c in candidate['colors']],dtype=np.int32)
        if candidate['transparent_index']!=0 or palette_rgb.shape!=(15,3) or np.any(palette_rgb<0) or np.any(palette_rgb>255):
            raise ValueError('Expected 15 valid opaque palette colors and transparent index 0')
        palette_method='semantic candidate palette, rounded RGB555, nearest color, no dithering'
    else:
        sample=Image.fromarray(opaque_rgb.reshape((1,-1,3)))
        reduced=sample.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
        palette_rgb=np.array(reduced.getpalette()[:45],dtype=np.uint16).reshape(15,3)
        palette_method='15-color median cut, rounded RGB555, nearest color, no dithering'
    # 5bit 채널로 반올림하고 중복 색을 합친다. word 0은 투명 전용이다.
    rgb5=(palette_rgb*31+127)//255
    words=sorted({int(c[0]|(c[1]<<5)|(c[2]<<10)) for c in rgb5},
                 key=lambda w:((w&31)*3+((w>>5)&31)*6+((w>>10)&31),w))
    if 0 in words:raise ValueError('Opaque black quantized to transparent PS1 word zero')
    palette_words=[0]+[w|0x8000 for w in words]
    while len(palette_words)<16:palette_words.append(palette_words[-1])
    colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31]
                     for w in palette_words[1:]],dtype=np.int32)
    distance=np.sum((opaque_rgb.astype(np.int32)[:,None,:]-colors[None,:,:])**2,axis=2)
    indices_small=np.zeros((height,width),dtype=np.uint8)
    indices_small[visible]=np.argmin(distance,axis=1)+1
    if resample=='palette-area':
        # 축소 후 중간색 대신 각 셀에서 면적이 큰 후보색을 고른다.
        # 생성 이미지를 먼저 후보색으로 줄이고 알파로 가중한 면적 투표를 한다.
        rules={}
        if palette_path:
            for entry in candidate['colors']:
                channels=[(v*31+127)//255 for v in entry['rgb']]
                word=channels[0]|channels[1]<<5|channels[2]<<10|0x8000
                rules[palette_words.index(word)]=entry
        source_data=np.array(crop)
        source_indices=np.empty(source_data.shape[:2],dtype=np.uint8)
        for row in range(crop.height):
            dif=source_data[row,:,:3].astype(np.int32)[:,None,:]-colors[None,:,:]
            costs=np.sum(dif*dif,axis=2)
            for index,rule in rules.items():
                if 'minimum_rb_over_g' in rule:
                    rgb=source_data[row,:,:3].astype(np.int32)
                    chroma=np.minimum(rgb[:,0],rgb[:,2])-rgb[:,1]
                    costs[chroma<rule['minimum_rb_over_g'],index-1]=1000000
            source_indices[row]=np.argmin(costs,axis=1)+1
        votes=[]
        for index in range(1,16):
            weight=np.where(source_indices==index,source_data[:,:,3],0).astype(np.uint8)
            votes.append(np.array(Image.fromarray(weight).resize((width,height),Image.Resampling.BOX),dtype=np.float32)
                         *rules.get(index,{}).get('area_weight',1))
        dominant=np.argmax(np.stack(votes),axis=0)+1
        indices_small[visible]=dominant[visible]
        palette_method='RGB555 palette before area voting; alpha and configured color weights; no dithering'
    indices=np.zeros((48,56),dtype=np.uint8)
    x_origin=8
    indices[:,x_origin:x_origin+width]=indices_small
    gfx=(extracted/'graphics_entry.bin').read_bytes();parts=(extracted/'composition_entry.bin').read_bytes()
    descriptor=graphics_bank(gfx,0)['frames'][147]
    original=decode_stream(gfx,descriptor['offset'],descriptor['limit'],descriptor['tile_count']*128)
    comp=composition_frame(parts,0,147)
    coverage,_,bounds=frame_coverage(original.data,descriptor['tile_count'],comp)
    outside=sum(bool(i) and not c for i,c in zip(indices.flat,coverage))
    if outside:raise ValueError(f'Art exceeds existing parts at {outside} pixels; no clipping performed')
    packed=edit_frame_indices(original.data,descriptor['tile_count'],comp,indices.tobytes(),(56,48))
    encoded=encode_stream(packed)
    back=decode_stream(encoded,0,len(encoded),len(packed))
    if back.data!=packed:raise AssertionError('Pilot compression roundtrip mismatch')
    other_frames=[]
    for number in (146,148):
        c=composition_frame(parts,0,number)
        old,_,_,_=compose_indices(original.data,descriptor['tile_count'],c)
        new,_,_,_=compose_indices(packed,descriptor['tile_count'],c)
        if old!=new:raise AssertionError('Pilot changed a neighboring frame index')
        other_frames.append(number)
    parent=ROOT/'out/ver_buki_riko'
    if not parent.resolve().is_relative_to(ROOT):raise ValueError('Output escaped workspace')
    out=parent/('riko_pilot_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True,exist_ok=False)
    if palette_path:
        (out/'palette_config.json').write_bytes(palette_path.read_bytes())
    picture=Image.frombytes('P',(56,48),indices.tobytes())
    flat=[component for w in palette_words for component in
          ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31)]
    picture.putpalette(flat+[0]*(768-len(flat)));picture.info['transparency']=0
    picture.save(out/'riko_idle147_indexed.png')
    rgba_picture=picture.convert('RGBA');rgba_picture.save(out/'riko_idle147_rgba.png')
    rgba_picture.resize((448,384),Image.Resampling.NEAREST).save(out/'riko_idle147_8x.png')
    (out/'riko_idle147.indices').write_bytes(indices.tobytes())
    (out/'candidate_block.packed4').write_bytes(packed)
    (out/'candidate_block.compressed').write_bytes(encoded)
    (out/'candidate_palette.bin').write_bytes(struct.pack('<16H',*palette_words))
    original_picture=Image.open(extracted/'idle_147.png').convert('RGBA')
    native=Image.new('RGBA',(128,48),(42,46,56,255))
    native.alpha_composite(original_picture,(0,0));native.alpha_composite(rgba_picture,(72,0))
    native.convert('RGB').save(out/'comparison_1x.png')
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22)
    card=Image.new('RGB',(960,444),(30,33,40));draw=ImageDraw.Draw(card)
    labels=['\uc6d0\ubcf8 \uc81c\ub85c \u00b7 8\ubc30','Riko \uae30\uc900\uc548 \u00b7 8\ubc30']
    for x,im,label in [(16,original_picture,labels[0]),(496,rgba_picture,labels[1])]:
        draw.text((x,10),label,font=font,fill='white')
        enlarged=im.resize((448,384),Image.Resampling.NEAREST)
        card.paste(enlarged,(x,48),enlarged)
    card.save(out/'comparison_8x.png')
    # 실제 배경의 인물이 없는 위치에 배치한 합성. 실행 증거로 사용하지 않는다.
    screen=Image.open(extracted/'runtime_framebuffer_0.png').convert('RGBA')
    screen.alpha_composite(rgba_picture.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(224,146))
    screen.convert('RGB').save(out/'background_composite_1x.png')
    large=Image.new('RGB',(960,764),(30,33,40));d=ImageDraw.Draw(large)
    d.text((12,6),'\ud569\uc131 \ubbf8\ub9ac\ubcf4\uae30 \u00b7 \uac8c\uc784 \uc801\uc6a9 \uc804',font=font,fill='white')
    large.paste(screen.resize((960,720),Image.Resampling.NEAREST).convert('RGB'),(0,44))
    large.save(out/'background_composite_3x.png')
    result={'source_generated_image':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'source_size':raw.size,'source_opaque_bbox':bbox,
            'resampling':resample+', alpha threshold 128',
            'sampled_size':[width,height],'placement':[x_origin,0],'size':[56,48],
            'palette_method':palette_method,'palette_config':str(palette_path) if palette_path else None,
            'palette_config_sha256':hashlib.sha256(palette_path.read_bytes()).hexdigest() if palette_path else None,
            'palette_words':palette_words,'opaque_colors_used':len(set(indices.flat)-{0}),
            'opaque_pixels':int(np.count_nonzero(indices)),'binary_alpha':True,'transparent_index':0,
            'pixels_outside_parts':outside,'bounds':bounds,'origin':[24,24],
            'compressed_bytes':len(encoded),'original_stream_budget':original.end-original.start,
            'fits_original_stream':len(encoded)<=original.end-original.start,
            'decoded_roundtrip_equal':True,'neighbor_frame_indices_unchanged':other_frames,
            'palette_differs_from_zero':True,'palette_sharing_runtime_unverified':True,
            'game_applied':False,'style_approved':False,'background_preview_is_composite':True}
    write_json(out/'validation.local.json',result)
    print(json.dumps({'output':str(out),**{k:result[k] for k in ('sampled_size','opaque_colors_used','opaque_pixels','pixels_outside_parts','compressed_bytes','original_stream_budget','fits_original_stream')}}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--extract',type=Path,required=True)
    parser.add_argument('--palette',type=Path)
    parser.add_argument('--resample',choices=['nearest','area','palette-area'],default='nearest')
    args=parser.parse_args();prepare(args.source,args.extract,args.palette,args.resample)
