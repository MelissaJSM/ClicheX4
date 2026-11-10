"""생성 원화를 린의 원래 크기·팔레트·파츠에 등록한다. 게임 BIN은 쓰지 않는다."""
import argparse,json,struct,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,inspect_references,load_project
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import frame_coverage,edit_frame_indices
from src.psx_compress import encode_stream

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--extract',type=Path,required=True);p.add_argument('--sampling',choices=['area','nearest','palette-area'],default='palette-area');a=p.parse_args()
    source=a.source.resolve();extract=a.extract.resolve()
    if not source.is_relative_to(ROOT/'work/ver_rin_nana/art_pilot') or not extract.is_relative_to(ROOT/'work/ver_rin_nana/zero_extract'):raise ValueError('Wrong variant paths')
    inspect_references(ROOT,load_project(ROOT,'ver_rin_nana'))
    report=json.loads((extract/'report.json').read_text('utf-8'))
    if digest(extract/'original.arc')!=report['archive']['sha256']:raise ValueError('Extraction changed')
    cfg=json.loads((ROOT/'config/rin_palette_candidate.json').read_text('utf-8'));words=[0]
    for c in cfg['colors']:
        r,g,b=[(v*31+127)//255 for v in c['rgb']];words.append(0x8000|r|(g<<5)|(b<<10))
    if len(set(words))!=16:raise ValueError('Palette must have 16 distinct entries')
    colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],np.int32)
    im=Image.open(source).convert('RGBA');ar=np.array(im);yy,xx=np.nonzero(ar[:,:,3]>=128)
    box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));crop=im.crop(box);h=48;w=round(crop.width*h/crop.height)
    if not 0<w<=48:raise ValueError('Art needs silhouette revision')
    small=crop.convert('RGBa').resize((w,h),Image.Resampling.NEAREST if a.sampling=='nearest' else Image.Resampling.BOX).convert('RGBA');v=np.array(small);visible=v[:,:,3]>=128
    small_idx=np.zeros((h,w),np.uint8);cost=np.sum((v[:,:,:3][visible].astype(np.int32)[:,None]-colors[None])**2,axis=2);small_idx[visible]=np.argmin(cost,axis=1)+1
    if a.sampling=='palette-area':
        full=np.array(crop);nearest=np.zeros(full.shape[:2],np.uint8)
        for y in range(crop.height):nearest[y]=np.argmin(np.sum((full[y,:,:3].astype(np.int32)[:,None]-colors[None])**2,axis=2),axis=1)+1
        votes=[np.array(Image.fromarray(np.where(nearest==i,full[:,:,3],0).astype(np.uint8)).resize((w,h),Image.Resampling.BOX)) for i in range(1,16)]
        vote=np.argmax(np.stack(votes),axis=0)+1;small_idx[visible]=vote[visible]
    gfx=(extract/'graphics_entry.bin').read_bytes();parts=(extract/'composition_entry.bin').read_bytes();f=graphics_bank(gfx,0)['frames'][147]
    raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128);comp=composition_frame(parts,0,147);coverage,size,bounds=frame_coverage(raw.data,f['tile_count'],comp)
    mask=np.array([bool(c) for c in coverage]).reshape(size[1],size[0]);candidates=[]
    # Compare ground-contact centers; transparent image bounds do not define the world origin.
    riko=Image.open(ROOT/'out/ver_buki_riko/final_v1_0_0/sprites/riko/frames/bank0_147.png');ri=np.array(riko);ry,rx=np.nonzero(ri);ref_center=float(np.mean(rx[ry>=ry.max()-1]))
    for x in range(size[0]-w+1):
        canvas=np.zeros((size[1],size[0]),np.uint8);canvas[:h,x:x+w]=small_idx
        if np.any((canvas>0)&~mask):continue
        sy,sx=np.nonzero(canvas);center=float(np.mean(sx[sy>=sy.max()-1]));candidates.append((abs(center-ref_center),x,canvas))
    if not candidates:raise ValueError('Visible art does not fit original parts; no automatic clipping')
    _,x,canvas=min(candidates,key=lambda c:c[0]);packed=edit_frame_indices(raw.data,f['tile_count'],comp,canvas.tobytes(),size);encoded=encode_stream(packed)
    if decode_stream(encoded,0,len(encoded),len(packed)).data!=packed:raise ValueError('Compressed pixels do not roundtrip')
    for n in (146,148):
        c=composition_frame(parts,0,n)
        if compose_indices(raw.data,f['tile_count'],c)[:2]!=compose_indices(packed,f['tile_count'],c)[:2]:raise ValueError('Neighbor frame changed')
    out=ROOT/'out/ver_rin_nana'/('rin_pilot_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
    pic=save_image(canvas.tobytes(),size,words,out/'rin_idle147_indexed.png');rgba=pic.convert('RGBA');rgba.save(out/'rin_idle147_rgba.png');rgba.resize((size[0]*8,size[1]*8),Image.Resampling.NEAREST).save(out/'rin_idle147_8x.png')
    (out/'candidate_block.packed4').write_bytes(packed);(out/'candidate_block.compressed').write_bytes(encoded);(out/'candidate_palette.bin').write_bytes(struct.pack('<16H',*words))
    original=Image.open(extract/'idle_147.png').convert('RGBA');riko_rgba=riko.convert('RGBA');native=Image.new('RGBA',(3*64,48),(32,37,48,255))
    for i,src in enumerate([original,riko_rgba,rgba]):native.alpha_composite(src,(i*64,0))
    native.convert('RGB').save(out/'comparison_1x.png')
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22);board=Image.new('RGB',(1536,440),(32,37,48));draw=ImageDraw.Draw(board)
    for i,(src,label) in enumerate([(original,'원본 제로'),(riko_rgba,'수용된 리코 · 크기 참고'),(rgba,'린 대기 기준안 · 게임 적용 전')]):
        draw.text((i*512+12,8),label,font=font,fill='white');large=src.resize((448,384),Image.Resampling.NEAREST);board.paste(large,(i*512+12,48),large)
    board.save(out/'comparison_8x.png')
    background=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z/runtime_framebuffer_0.png'
    if background.exists():
        scene=Image.open(background).convert('RGBA');scene.alpha_composite(rgba.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(224,146));scene.convert('RGB').save(out/'background_composite_1x.png')
        review=Image.new('RGB',(960,764),(32,37,48));ImageDraw.Draw(review).text((10,8),'합성 미리보기 · 실제 실행 증거 아님',font=font,fill='white');review.paste(scene.resize((960,720),Image.Resampling.NEAREST),(0,44));review.save(out/'background_composite_3x.png')
    result={'project':'ver_rin_nana','task':'zero_rin','source_sha256':report['source_sha256'],'source_generated_image':source.relative_to(ROOT).as_posix(),'generated_sha256':digest(source),'source_size':im.size,'crop':box,'logical_body_size':[w,h],'palette_words':words,'sampling':a.sampling,'placement':[x,0],'world_bounds':bounds,'world_origin':[-bounds[0],-bounds[1]],'size':size,'palette_colors_used':len(set(canvas.flat)-{0}),'transparent_index':0,'outside_parts':0,'decoded_roundtrip_equal':True,'neighbor_frames_preserved':[146,148],'compressed_bytes':len(encoded),'original_stream_budget':raw.end-raw.start,'fits_original_stream':len(encoded)<=raw.end-raw.start,'art_approved':False,'game_applied':False,'runtime_tested':False,'background_is_composite':True,'palette_sharing':'대기 후보용 팔레트이며 다른 제로 참조에 전역 적용하지 않음'}
    (out/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    pointer={'candidate':out.relative_to(ROOT).as_posix(),'extract':extract.relative_to(ROOT).as_posix(),'source':source.relative_to(ROOT).as_posix(),'style_approved':False,'game_applied':False}
    (ROOT/'projects/ver_rin_nana/rin_candidate.json').write_text(json.dumps(pointer,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'size':[w,h],'colors_used':result['palette_colors_used'],'compressed_bytes':len(encoded),'budget':raw.end-raw.start,'fits':result['fits_original_stream']}))

if __name__=='__main__':main()
