"""현재 이동 질감으로 다시 그린 대기를 동일 월드 기준과 팔레트로 등록한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.prepare_rin_idle import SEQUENCE,TICKS
from scripts.build_rin_idle import entry
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.psx_frame_edit import frame_coverage

OUT=ROOT/'work/ver_rin_nana/idle_style/v2'
PARENT=ROOT/'out/ver_rin_nana/rin_ice_20261028T204000812726Z'
IDS=(0,1,2,5,6,146,147,148)

def main():
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);oldparts=parts
    words=struct.unpack_from('<16H',pal)
    colors=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31] for v in words[1:]],np.int32)
    def source(name,height):
        im=Image.open(OUT/name).convert('RGBA');a=np.array(im);q=connected_groups(a[:,:,3]>=128)[0];yy,xx=q[:,0],q[:,1];box=tuple(map(int,(xx.min(),yy.min(),xx.max()+1,yy.max()+1)))
        crop=im.crop(box);return quantize(crop,colors,height/crop.height),box,height/crop.height
    a,box,scale=source('generated_idle.png',48)
    if a.shape!=(48,45):raise ValueError('Source idle shape changed')
    master=np.zeros((48,56),np.uint8);master[:,5:50]=a
    breath,bbox,bscale=source('generated_breath.png',47)
    registered=np.zeros_like(master);left=round(22.5-(breath.shape[1]-1)/2)
    registered[1:48,left:left+breath.shape[1]]=breath
    # Use the SAME neutral leg columns. A separate generated knee crop had a
    # different lateral position. Absorb the one-pixel lowering at the knee,
    # retaining all boot pixels and never shearing the torso at the waist.
    low=master.copy();low[:37]=0;low[1:37]=master[:36]
    low[37:40,40:]=master[36:39,40:]
    blink=master.copy();eyes=np.argwhere(master==15)
    if eyes.tolist()!=[[10,19]]:raise ValueError('Unexpected eye; do not edit hair')
    blink[10,19]=master[11,19]
    if blink[10,19] not in (12,13,14):raise ValueError('Blink must use neighbouring skin')
    poses={0:low,1:low,2:low,5:master,6:master,146:low,147:master,148:blink}
    for n,a in poses.items():
        if not np.array_equal(a[40:],master[40:]):raise ValueError('Boot anchors changed')
        if n in (0,1,2,146) and not np.array_equal(a[1:34],master[:33]):raise ValueError('Torso split')
        groups=connected_groups(a>0)
        if len(groups)!=1:raise ValueError(f'Detached idle {n}: {[len(q) for q in groups]}')
    # The new ribbon needs two more columns at lower-right. Move the complete
    # bottom tile row, retaining artwork world positions and disjoint windows.
    revised=bytearray(parts)
    for pi,ns in ((0,IDS),(5,(0,86))):
        for n in ns:
            c=composition_frame(parts,pi,n)
            for p in c['parts']:
                if p['y']==8:revised[p['record_offset']+2]=(p['x']+2)&255
                if pi==0 and n in (0,1,2) and p['y']==-8:revised[p['record_offset']+2]=(p['x']-3)&255
    parts=bytes(revised)
    frames={};aliases={};issues=[]
    def register(bi,pi,n,a):
        f=graphics_bank(g,bi)['frames'][n];c=composition_frame(parts,pi,n)
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        cov,size,b=frame_coverage(raw,f['tile_count'],c);mask=np.array([bool(v) for v in cov]).reshape(size[1],size[0])
        for p in c['parts']:
            if p['tile']%16==0:mask[p['y']-b[1]:p['y']-b[1]+16,p['x']-b[0]+(15 if p['flip_x'] else 0)]=False
        pixels=np.zeros((size[1],size[0]),np.uint8)
        for yy,xx in np.argwhere(a>0):
            x=int(xx)-24-b[0];y=int(yy)-24-b[1]
            if not 0<=x<size[0] or not 0<=y<size[1]:raise ValueError('World sprite outside canvas')
            pixels[y,x]=a[yy,xx]
        bad=int(np.count_nonzero((pixels>0)&~mask))
        if bad:issues.append({'bank':bi,'frame':n,'outside':bad})
        path=OUT/f'bank{bi}_{n:03d}.png';save_image(pixels.tobytes(),size,words,path)
        return {'file':path.name,'sha256':digest(path),'bounds':b,'size':size,'outside_safe_parts':bad,'opaque_pixels':int(np.count_nonzero(a))}
    for n,a in poses.items():frames[str(n)]=register(0,0,n,a)
    for n in (0,86):aliases[str(n)]=register(1,5,n,master)
    (OUT/'composition_entry.bin').write_bytes(parts)
    report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':json.loads((PARENT/'manifest.json').read_text('utf-8'))['modified_bin']['sha256'],
        'graphics_bank':0,'parts_bank':0,'frames':frames,'bank1_aliases':aliases,'composition_sha256':digest(OUT/'composition_entry.bin'),
        'imagegen_mode':'built_in_edit','source':'generated_idle.png','source_sha256':digest(OUT/'generated_idle.png'),'prompt':'prompt.txt',
        'breath_source':'generated_breath.png','breath_source_sha256':digest(OUT/'generated_breath.png'),'breath_prompt':'prompt_breath.txt',
        'registration':{'source_crop':box,'uniform_scale':scale,'breath_crop':bbox,'breath_scale':bscale,'native_size':[56,48],'world_origin':[24,24],'blink_xy':[19,10],'blink_changes':1,'body_down_pixels':1,'locked_boot_rows':[40,48],'generated_knee_rows':None,'knee_source':'same neutral master; rows1..36 use source0..35, rows37..47 unchanged; ribbon translates coherently','floor':23,'boot_extent_center':-1.5},
        'composition_x_edits':[{'offset':i,'before':x,'after':y} for i,(x,y) in enumerate(zip(oldparts,parts)) if x!=y],
        'sequence':SEQUENCE,'duration_ticks':TICKS,'issues':issues,'applied':False}
    (OUT/'idle_style_recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    board=Image.new('RGB',(280*4,300),(35,38,48));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    def native(n):
        f=graphics_bank(g,0)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        return compose_indices(raw,f['tile_count'],composition_frame(oldparts,0,n))
    panels=[('기존 대기',native(147)),('새 대기',(master.tobytes(),(56,48),(-24,-24,32,24))),('기준 걷기',native(7)),('새 호흡',(low.tobytes(),(56,48),(-24,-24,32,24)))]
    for i,(label,(px,sz,b,*_)) in enumerate(panels):
        pic=save_image(px,sz,words,OUT/f'comparison_{i}.png').convert('RGBA');cell=Image.new('RGBA',(70,64));cell.alpha_composite(pic,(32+b[0],28+b[1]));cell=cell.resize((280,256),Image.Resampling.NEAREST);board.paste(cell,(i*280,35),cell);draw.text((i*280+8,8),label,font=font,fill='white')
    board.save(OUT/'comparison_4x.png')
    pics=[]
    for n in SEQUENCE:
        pic=save_image(poses[n].tobytes(),(56,48),words,OUT/f'preview_{n:03d}.png');pics.append(pic.resize((224,192),Image.Resampling.NEAREST))
    pics[0].save(OUT/'idle_preview_4x.gif',save_all=True,append_images=pics[1:],duration=[round(t*100/60)*10 for t in TICKS],loop=0,transparency=0,disposal=2,optimize=False)
    print(json.dumps({'issues':issues,'output':str(OUT)}))

if __name__=='__main__':main()
