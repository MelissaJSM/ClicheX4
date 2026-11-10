"""생성한 Shibuki 그림을 X의 원래 기준점·4bpp·압축 예산으로 검사한다."""
import json
import argparse
import re
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scripts.project import write_json, inspect_references, load_project
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank, decode_stream, composition_frame, compose_indices
from src.psx_frame_edit import frame_coverage, edit_frame_indices
from src.psx_compress import encode_stream, replace_stream


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--art-dir', type=Path, default=ROOT/'work/ver_buki_riko/shibuki_art/idle_v1')
    parser.add_argument('--candidate', default='candidate01')
    parser.add_argument('--sampling', choices=['area', 'palette-area', 'nearest'], default='area')
    parser.add_argument('--palette', type=Path, default=ROOT/'config/shibuki_palette_candidate.json')
    parser.add_argument('--height', type=int, choices=[46,47,48], default=48)
    parser.add_argument('--index-permutation', type=Path, help='Lossless index/palette permutation JSON')
    args = parser.parse_args()
    project = load_project(ROOT, 'ver_buki_riko')
    inspect_references(ROOT, project)
    pointer = json.loads((ROOT/'projects/ver_buki_riko/shibuki_source_inventory.json').read_text(encoding='utf-8'))
    extracted = (ROOT/pointer['inventory']).parent
    inv = json.loads((extracted/'inventory.json').read_text(encoding='utf-8'))
    if sha256((extracted/'original.arc').read_bytes()) != inv['archive']['sha256']:
        raise ValueError('Extraction hash mismatch')
    work = args.art_dir.resolve()
    if not work.is_relative_to((ROOT/'work/ver_buki_riko/shibuki_art').resolve()):
        raise ValueError('Expected Shibuki work directory')
    if not re.fullmatch(r'candidate[0-9]{2}', args.candidate):
        raise ValueError('Expected a simple candidateNN output name')
    output = work/args.candidate
    output.mkdir(exist_ok=False)
    source = work/'generated.png'
    rgba = Image.open(source).convert('RGBA')
    data = np.array(rgba)
    y,x = np.nonzero(data[:,:,3] >= 128)
    crop_bounds = [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
    crop = rgba.crop(crop_bounds)
    height = args.height
    width = round(crop.width*height/crop.height)
    resample = Image.Resampling.NEAREST if args.sampling=='nearest' else Image.Resampling.BOX
    small = crop.convert('RGBa').resize((width,height),resample).convert('RGBA')
    sampled = np.array(small)
    palette_path = args.palette.resolve()
    config = json.loads(palette_path.read_text(encoding='utf-8'))
    active = config.get('quantization_indices', list(range(1,16)))
    if not active or len(active)!=len(set(active)) or any(type(i)!=int or not 1<=i<=15 for i in active):
        raise ValueError('Invalid quantization color indices')
    (output/'palette_config.json').write_bytes(palette_path.read_bytes())
    words = [0]
    for c in config['colors']:
        r,g,b = [(v*31+127)//255 for v in c['rgb']]
        words.append(0x8000|r|g<<5|b<<10)
    if len(words)!=16 or len(set(words))!=16:
        raise ValueError('Palette must have fifteen distinct opaque colors')
    rgb = np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],dtype=np.int32)
    diff = sampled[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[active][None,None,:,:]
    labels = np.array(active)[np.argmin((diff*diff).sum(axis=3),axis=2)]
    if args.sampling == 'palette-area':
        # Quantize the generated art before area sampling. Each target cell
        # uses its dominant real color, avoiding new muddy averaged shades.
        src = np.array(crop)
        src_labels = np.zeros(src.shape[:2], dtype=np.uint8)
        for row in range(crop.height):
            delta = src[row,:,:3].astype(np.int32)[:,None,:]-rgb[active][None,:,:]
            src_labels[row] = np.array(active)[np.argmin((delta*delta).sum(axis=2),axis=1)]
        votes=[]
        for index in active:
            weight=np.where(src_labels==index,src[:,:,3],0).astype(np.uint8)
            votes.append(np.array(Image.fromarray(weight).resize((width,height),Image.Resampling.BOX)))
        labels=np.array(active)[np.argmax(np.stack(votes),axis=0)]
    labels[sampled[:,:,3]<128] = 0
    canvas = np.zeros((48,48),dtype=np.uint8)
    # Match soles, not the silhouette center (the tail biases that center).
    foot_x = np.nonzero(labels[-3:])[1]
    foot_center = (int(foot_x.min())+int(foot_x.max()))/2
    original_labels = np.array(Image.open(extracted/'base_000.png'))
    original_foot_x = np.nonzero(original_labels[-3:])[1]
    original_foot_center = (int(original_foot_x.min())+int(original_foot_x.max()))/2
    left = round(original_foot_center-foot_center)
    top = 48-height
    if not (0 <= left and left+width <= 48):
        raise ValueError('Foot-aligned sprite exceeds canvas; revise artwork')
    canvas[top:top+height,left:left+width] = labels
    permutation = None
    if args.index_permutation:
        permutation = json.loads(args.index_permutation.read_text(encoding='utf-8'))['old_index_to_new']
        if (len(permutation)!=16 or any(type(v)!=int for v in permutation)
                or sorted(permutation)!=list(range(16)) or permutation[0]!=0):
            raise ValueError('Expected a bijective palette permutation preserving transparent index zero')
        previous_rgba = np.array(words,dtype=np.uint16)[canvas]
        reordered = [0]*16
        for old,new in enumerate(permutation):reordered[new]=words[old]
        canvas=np.array(permutation,dtype=np.uint8)[canvas]
        words=reordered
        if not np.array_equal(previous_rgba,np.array(words,dtype=np.uint16)[canvas]):
            raise ValueError('Palette permutation changed visible colors')
        (output/'index_permutation.json').write_bytes(args.index_permutation.read_bytes())
    gfx = (extracted/'graphics_entry.bin').read_bytes()
    parts = (extracted/'composition_entry.bin').read_bytes()
    desc = graphics_bank(gfx,0,allow_bank_aliases=True)['frames'][0]
    raw = decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
    comp = composition_frame(parts,0,0)
    coverage,size,bounds = frame_coverage(raw.data,desc['tile_count'],comp)
    outside = sum(bool(v) and not c for v,c in zip(canvas.flat,coverage))
    if outside:
        raise ValueError(f'{outside} visible pixels exceed X original parts; no clipping allowed')
    packed = edit_frame_indices(raw.data,desc['tile_count'],comp,canvas.tobytes(),size)
    encoded = encode_stream(packed)
    if decode_stream(encoded,0,len(encoded),len(packed)).data != packed:
        raise ValueError('Candidate codec roundtrip failed')
    fits = len(encoded) <= desc['limit']-desc['offset']
    patch_error = None
    if fits:
        modified, compressed = replace_stream(gfx,desc,packed)
        for bi in range(len(inv['graphics_banks'])):
            for f in graphics_bank(gfx,bi,allow_bank_aliases=True)['frames']:
                a=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
                b=decode_stream(modified,f['offset'],f['limit'],f['tile_count']*128).data
                if a != b and (bi,f['index']) != (0,0):
                    raise ValueError('Candidate modified another decoded frame')
        (output/'candidate_graphics_entry.bin').write_bytes(modified)
    else:
        compressed=None
        patch_error='Original stream budget exceeded; no relocation attempted'
    pic=save_image(canvas.tobytes(),size,words,output/'shibuki_idle000_indexed.png')
    pic.convert('RGBA').save(output/'shibuki_idle000_rgba.png')
    pic.resize((384,384),Image.Resampling.NEAREST).save(output/'shibuki_idle000_8x.png')
    (output/'palette.bin').write_bytes(struct.pack('<16H',*words))
    (output/'candidate.packed4').write_bytes(packed)
    (output/'candidate.compressed').write_bytes(encoded)
    original=Image.open(extracted/'base_000.png').convert('RGBA')
    riko=Image.open(ROOT/'out/ver_buki_riko/riko_motion_20261023T211436315688Z/idle_147.png').convert('RGBA')
    sources=[('X',original,[-19,-25,29,23]),('Shibuki',pic.convert('RGBA'),bounds),('Riko',riko,[-24,-24,32,24])]
    sheet=Image.new('RGB',(840,390),'#222630');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    for i,(label,im,bb) in enumerate(sources):
        x=i*280
        draw.text((x+12,8),label+' / 1x + 4x',font=font,fill='white')
        for scale,origin in [(1,(x+126,70)),(4,(x+126,234))]:
            enlarged=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
            sheet.paste(enlarged,(origin[0]+bb[0]*scale,origin[1]+bb[1]*scale),enlarged)
            draw.line((x+12,origin[1]+24*scale,x+265,origin[1]+24*scale),fill='#526075')
    draw.text((12,355),'정적 시안 · 같은 배율 / 실제 게임 적용 화면 아님',font=font,fill='#cad2e0')
    sheet.save(output/'review_1x_4x.png')
    report=dict(task='x_shibuki',status='candidate_pending_art_review',source=str(source.relative_to(ROOT)),
                source_sha256=sha256(source.read_bytes()),prompt=str((work/'prompt.txt').relative_to(ROOT)),
                tool='built-in image_gen',normalization=args.sampling+', RGB555 palette, no dithering',
                crop=crop_bounds,scaled_size=[width,height],position=[left,top],canvas_size=list(size),
                foot_center_original=original_foot_center,foot_center_candidate=left+foot_center,
                bounds=list(bounds),palette_words=words,index_permutation=permutation,opaque_pixels=int(np.count_nonzero(canvas)),
                original_opaque_pixels=inv['base_frames'][0]['opaque_pixels'],coverage_outside=outside,
                compressed_bytes=len(encoded),stream_budget=desc['limit']-desc['offset'],fits_original_stream=fits,
                compressed=compressed,patch_error=patch_error,codec_roundtrip=True,
                game_applied=False,runtime_verified=False,source_inventory=pointer['inventory'],
                scope='Single base idle frame 0. Six-frame idle family and other poses not yet produced.',
                armor_design_implemented=False,text_replacement_implemented=False)
    write_json(output/'candidate.json',report)
    print(json.dumps({'output':str(output),'native_size':[width,height],'compressed':len(encoded),
                      'budget':report['stream_budget'],'fits':fits,'game_applied':False}))


if __name__=='__main__':
    main()
