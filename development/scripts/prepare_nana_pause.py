"""나나 일시정지 얼굴: 두 X 자원의 UI만 교체하고 몸/사랑이 아이콘은 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_pause import composition
from scripts.prepare_nana_dialogue import WORDS,PAL
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.extract_zero import save_image
from src.psx_ui_atlas import local_composition
from src.psx_static_effect import compose_static,patch_static
from src.psx_ui_render import render_static_rgba
PARENT=ROOT/'out/ver_rin_nana/nana_dialogue_20261030T025314649620Z'
PARENT_SHA='9e7cb7936cd22f14add6c13bd99a4dfc3c781df6daba05784381200f24fa9224'
ART=ROOT/'work/ver_rin_nana/illustrations/nana_pause_v1'
def sources():
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Accepted parent differs')
    m=json.loads((PARENT/'manifest.json').read_text('utf8'));records={};raw={}
    with(PARENT/'rin_nana.bin').open('rb')as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size);iso={q['path']:q for q in d.inspect()['files']}
        for name,file in(('PL00_U.ARC','modified.arc'),('PL02_U.ARC','PL02_U.ARC')):
            q=iso['/ARC/'+name+';1'];a=d.read(q['lba'],q['size'])
            if a!=(PARENT/file).read_bytes():raise ValueError('Parent ARC differs')
            records[name]={**q,'sha256':sha256(a)};raw[name]=a
    return m,records,raw
def verify(old,new,indices):
    c=composition(old);g=entry(old,0x10007);pal=entry(old,0x11)
    if len(indices)!=64*80 or max(indices)>15:raise ValueError('Invalid native image')
    ng=patch_static(g[12288:],{10:local_composition(c)},{10:(indices,(64,80))})
    if new!=replace_entry(replace_entry(old,0x10007,g[:12288]+ng),0x11,pal[:320]+PAL+pal[352:]):raise ValueError('Bytes outside portrait changed')
    if composition(new)!=c:raise ValueError('Portrait geometry changed')
    before,size,bounds,_=compose_static(g[12288:],local_composition(c));px,sz,bb,_=compose_static(entry(new,0x10007)[12288:],local_composition(c))
    if(px,sz,bb)!=(indices,size,bounds)or size!=(64,80):raise ValueError('Portrait readback differs')
    if bytes(bool(v)for v in before)!=bytes(bool(v)for v in indices):raise ValueError('Original menu mask changed')
    im,b=render_static_rgba(entry(new,0x10007)[12288:],c,{0:WORDS});a=np.frombuffer(indices,np.uint8).reshape(80,64);expected=np.zeros((80,64,4),np.uint8)
    for i,w in enumerate(WORDS[1:],1):expected[a==i]=[*(int(w>>s&31)*255//31 for s in(0,5,10)),255]
    if b!=bounds or not np.array_equal(np.array(im),expected):raise ValueError('Actual menu CLUT mismatch')
    return {'frame':10,'native_size':list(size),'bounds':list(bounds),'parts':len(c['parts']),'original_mask_and_coordinates_exact':True,'actual_clut_render_equal':True,'palette_row':10,'all_other_arc_bytes_exact':True,'runtime_verified':False}
def prepare(out):
    m,records,raw=sources();old=raw['PL00_U.ARC'];c=composition(old);px,size,bounds,_=compose_static(entry(old,0x10007)[12288:],local_composition(c));mask=np.frombuffer(px,np.uint8).reshape(80,64)>0;ys,xs=np.nonzero(mask);box=(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1);w,h=box[2]-box[0],box[3]-box[1]
    im=Image.open(ART/'generated.png').convert('RGB');scale=max(w/im.width,h/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);dx=(im.width-w)//2;dy=(im.height-h)//2;im=im.crop((dx,dy,dx+w,dy+h));canvas=np.zeros((80,64,3),np.uint8);canvas[box[1]:box[3],box[0]:box[2]]=np.array(im)
    colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in WORDS[1:]],np.int32);dist=((canvas.astype(np.int32)[:,:,None,:]-colors)**2).sum(3);a=np.where(mask,dist.argmin(2)+1,0).astype(np.uint8);indices=a.tobytes();new={};checks={}
    for name,old in raw.items():
        g=entry(old,0x10007);pal=entry(old,0x11);ng=patch_static(g[12288:],{10:local_composition(composition(old))},{10:(indices,size)});new[name]=replace_entry(replace_entry(old,0x10007,g[:12288]+ng),0x11,pal[:320]+PAL+pal[352:]);checks[name]=verify(old,new[name],indices)
    out.mkdir(parents=True,exist_ok=False)
    for n,data in new.items():(out/n).write_bytes(data)
    im=save_image(indices,size,WORDS,out/'portrait.png');im.resize((384,480),Image.Resampling.NEAREST).save(out/'portrait_6x.png');(out/'palette.bin').write_bytes(PAL)
    r={'kind':'nana_pause','parent_sha256':PARENT_SHA,'parent_manifest_sha256':digest(PARENT/'manifest.json'),'tool':'built-in image_gen','art':(ART/'generated.png').relative_to(ROOT).as_posix(),'art_sha256':digest(ART/'generated.png'),'prompt':(ART/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(ART/'prompt.txt'),'uniform_scale':scale,'target_box':box,'verification':checks,'files':[{'file':n,'source':records[n],'sha256':sha256(new[n])}for n in sorted(new)]};(out/'recipe.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'verification':checks}))
def inventory():
    m,records,raw=sources();ART.mkdir(parents=True,exist_ok=True);old=raw['PL00_U.ARC'];c=composition(old);im,b=render_static_rgba(entry(old,0x10007)[12288:],c,{0:struct.unpack_from('<16H',entry(old,0x11),320)});im.save(ART/'original.png');im.resize((384,480),Image.Resampling.NEAREST).save(ART/'original_6x.png');(ART/'sources.json').write_text(json.dumps(records,indent=2)+'\n','utf8');print(json.dumps({'bounds':b,'parts':len(c['parts'])}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inventory',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args();inventory()if a.inventory else prepare(a.output)
