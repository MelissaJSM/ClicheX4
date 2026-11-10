"""Export current, hash-pinned mod art. Never writes to the supplied BIN files."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, struct, sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
DEV=ROOT/'development';sys.path.insert(0,str(DEV))
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import Archive, GROUPS
from zero_metadata import classify, animations as zero_animations
from scripts.export_x_consistency import animation_map as x_animations
from src.psx_player import composition_frame,decode_stream
from src.psx_ui_atlas import aliased_composition,write_tile
from src.psx_ui_render import render_static_rgba
from src.psx_static_effect import compose_static

def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def disc(path,names):
    with path.open('rb') as f:
        d=DiscReader(f,path.stat().st_size);records={x['name'].split(';')[0]:x for x in d.inspect()['files']}
        return {n:d.read(records[n]['lba'],records[n]['size']) for n in names}
def picture(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def indexed(p,a,words):
    im=Image.fromarray(a.astype('uint8'),'P');pal=[]
    for w in words:pal.extend((int(w)>>s&31)*255//31 for s in(0,5,10))
    im.putpalette(pal+[0]*(768-len(pal)));im.info['transparency']=bytes(0 if i%16==0 else 255 for i in range(len(words)));picture(p,im)
def world(im,bounds):
    c=Image.new('RGBA',(160,160));c.alpha_composite(im,(80+bounds[0],80+bounds[1]));return c
def sprites(raw,base,xc,zc,out):
    exclusions=[];counts={}
    for char,zero in [(xc,False),(zc,True)]:
        dest=out/'characters'/char/'sprites';rows=[];layers=[]
        if not zero:
            animations,_=x_animations(raw['SLUS_005.61']);save(dest/'animations.json',animations)
            for arcname in ['PL00_U.ARC','PL02_U.ARC']:
                arc=Archive(raw[arcname]);original=Archive(base[arcname]);ultimate=arcname.startswith('PL02')
                forms=[('ultimate_before',15,2),('ultimate_after',0,2)] if ultimate else [('base',0,2),('fourth',15,2),('fourth_arm1',15,1)]
                for n in range(237):
                    if n in {105,*range(175,183)}:
                        exclusions.append({'character':char,'archive':arcname,'ref':n,'reason':'reserved / partial VRAM; no standalone artwork'});continue
                    changed=False
                    for pb in (0,5,6,7,8):
                        a,rec=arc.layer(n,pb);old,_=original.layer(n,pb)
                        if np.array_equal(a,old):continue
                        changed=True
                        group=('ultimate'if ultimate else'normal_fourth')+f'/bank{pb}'
                        path=dest/'indexed_layers'/group/f'{n:03}.png';words=arc.words[:64] if pb==0 else arc.words[16:32]
                        indexed(path,a,words)
                        layers.append({'file':path.relative_to(dest).as_posix(),'ref':n,'bank':pb,'archive':arcname,'origin':[160,160],'palette_words':[int(w) for w in words],'alternate_arm_palette':[int(w)for w in arc.words[32:48]]if pb==7 else None,**rec})
                    if not changed:
                        exclusions.append({'character':char,'archive':arcname,'ref':n,'reason':'unchanged original bitmap/parts; not republished'});continue
                    for form,mask,arm in forms:
                        if form=='ultimate_after' and 217<=n<=230:mask=15
                        im,_=arc.composite(n,mask,arm);p=dest/form/f'{n:03}.png';picture(p,im)
                        rows.append({'file':p.relative_to(dest).as_posix(),'form':form,'ref':n,'group':next(k for k,v in GROUPS.items()if n in v),'mask':mask,'arm_type':arm,'rgba_sha256':sha(im.tobytes())})
        else:
            animations,_,_=zero_animations(raw['SLUS_005.61']);save(dest/'animations.json',animations)
            arc=Archive(raw['PL01_U.ARC']);original=Archive(base['PL01_U.ARC'])
            words=arc.words.copy();black=words.copy();black[:16]=words[13*16:14*16]
            for gb,pb in [(0,0),(1,5)]:
                for n in range(len(arc.banks[gb]['frames'])):
                    group,kind=classify(gb,n)
                    if kind in {'effect','blank','unknown','partial_vram_update'}:
                        exclusions.append({'character':char,'bank':gb,'ref':n,'reason':kind});continue
                    a,rec=arc.layer(n,pb,gb);old,_=original.layer(n,pb,gb)
                    if np.array_equal(a,old):
                        exclusions.append({'character':char,'bank':gb,'ref':n,'reason':'unchanged original bitmap/parts'});continue
                    name=f'bank{gb}_{n:03}.png';p=dest/'indexed_layers'/name;indexed(p,a,words[:64]);layers.append({'file':p.relative_to(dest).as_posix(),'palette_words':[int(w)for w in words[:64]],'origin':[160,160],**rec})
                    for form,palette in [('normal',words),('black',black)]:
                        arc.words=palette;im=arc.rgba(a);p=dest/form/name;picture(p,im);rows.append({'file':p.relative_to(dest).as_posix(),'form':form,'bank':gb,'ref':n,'group':group,'classification':kind,'rgba_sha256':sha(im.tobytes())})
                    arc.words=words
            pal=json.loads((ROOT/'tools/data'/f'{char}_static_palette.json').read_text('utf8'))['words']
            for n in [23,24]:
                cp=composition_frame(arc.c,6,n);pix,size,bb,_=compose_static(entry(raw['PL01_U.ARC'],0x10206),cp)
                a=np.zeros((384,384),np.uint8);a[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(pix,np.uint8).reshape(size[1],size[0])
                p=dest/'indexed_layers'/f'static6_{n:03}.png';indexed(p,a,pal)
                im=Image.open(p).convert('RGBA');q=dest/'normal'/p.name;picture(q,im)
                rows.append({'file':q.relative_to(dest).as_posix(),'form':'normal','bank':6,'ref':n,'group':'rakuhouha_static_body','palette_status':'historical capture','rgba_sha256':sha(im.tobytes())})
                layers.append({'file':p.relative_to(dest).as_posix(),'ref':n,'bank':6,'parts':cp['parts'],'palette_words':pal,'origin':[160,160]})
        save(dest/'manifest.json',{'character':char,'canvas':[384,384],'origin':[160,160],'native_scale':1,'frames':rows,'layers':layers,'order_is_not_animation':True,'runtime_capture':False,'note':'X layers compose in order base, leg(8), head(5), arm(7), body(6). Mask bits head1/body2/arm4/leg8. Original unchanged effects/placeholder refs excluded. Embedded effect pixels can remain in authored body poses.'})
        counts[char]={'composed':len(rows),'indexed_layers':len(layers)}
    return counts,exclusions
def illustrations(raw,xc,zc,mode,out):
    records=[]
    def col(name,row):return struct.unpack_from('<16H',entry(raw[name],5),row*32)
    def native(name,pal,bank,frame,row,private=False):
        p=entry(raw[name],10);start=struct.unpack_from('<I',entry(raw[name],12),bank*4)[0]
        if private:
            offset=struct.unpack_from('<I',p,bank*4)[0]+1376;comp=composition_frame(struct.pack('<I',4)+p[offset:],0,frame)
        else:comp=aliased_composition(p,bank,frame)
        pals={q['clut']:col(pal,row+q['clut'])for q in comp['parts']}
        return render_static_rgba(entry(raw[name],0x10102)[start:],comp,pals)
    def add(char,category,state,n,im,origin=None):
        p=out/'characters'/char/'illustrations'/category/state/f'{n:02}.png';picture(p,im)
        records.append({'character':char,'category':category,'state':state,'frame':n,'file':p.relative_to(out).as_posix(),'origin':origin,'sha256':digest(p)})
    for side,char in enumerate([xc,zc]):add(char,'selection','shared',0,native('ST0E_U1.ARC','COL0E_U1.ARC',1,side,4)[0])
    x=raw['ST0D_0X.ARC'];blob=entry(x,13)[96:];chunks=[]
    for k in range(struct.unpack_from('<I',blob,4)[0]):
        kind,start,offset,size=struct.unpack_from('<4I',blob,16+k*16);chunks.append((kind,start,decode_stream(blob,offset,len(blob),size).data))
    states=next(b for kind,start,b in chunks if kind==0);dictionary=b''.join(b for kind,start,b in chunks if kind==1)
    for state in range(18):
        data=states[state*1412:(state+1)*1412];tex=bytearray(176*128)
        for tile,j in enumerate(struct.unpack('<176H',data[:352])):
            if j!=65535:write_tile(tex,tile,bytes(v for q in dictionary[j*128:j*128+128]for v in(q&15,q>>4)))
        p=struct.pack('<I',4)+data[352:]
        for n in range(12):
            im,bb=render_static_rgba(tex,composition_frame(p,0,n),{0:col('COL0D_0X.ARC',35)})
            add(xc,'hunter_base',f'{state:02}',n,world(im,bb),[80,80])
    changes={'ver_rin_nana':{2:(8,3,5),3:(13,4,7),7:(22,2,5),8:(30,4,7),9:(31,12,14)},'ver_buki_riko':{2:(28,29,30),3:(3,4,6),4:(5,6,8),5:(11,12,15),13:(21,22,24)}}
    for category,name,palname,bank,row in [('hunter_base','ST0D_0Z.ARC','COL0D_0Z.ARC',2,35),('dialogue','ST00_00.ARC','COL00_0Z.ARC',13,63)]:
        start=struct.unpack_from('<I',entry(raw[name],12),bank*4)[0];parts=entry(raw[name],10)
        for variant in ['normal','black']:
            pal=list(col(palname,row))
            if variant=='black':
                for i,(r,g,b)in changes[mode].items():pal[i]=(pal[i]&0x8000)|r|g<<5|b<<10
            for n in range(aliased_composition(parts,bank,0)['bank_frame_count']):
                im,bb=render_static_rgba(entry(raw[name],0x10102)[start:],aliased_composition(parts,bank,n),{0:pal})
                add(zc,category,variant,n,world(im,bb)if category=='hunter_base'else im,[80,80]if category=='hunter_base'else None)
    for state in range(6):
        for n,frame in enumerate([state,state+4]if state<4 else [0,4]if state==4 else[1,5]):
            add(xc,'dialogue',f'{state:02}',n,native('ST00_00.ARC','COL00_0X.ARC',11,frame,62,private=state>=4)[0])
    # Native pause renderer, using the exact final executable; no guessed tile layout.
    sys.path.insert(0,str(DEV/'work/pause_variants_20261109'))
    spec=importlib.util.spec_from_file_location('pause_export_cpu',DEV/'work/pause_variants_20261109/verify_cpu.py');pause=importlib.util.module_from_spec(spec);spec.loader.exec_module(pause)
    for side,char in enumerate([xc,zc]):
        for n in range(2 if side else 6):
            arc=raw['PL01_U.ARC'if side else'PL00_U.ARC'if n<4 else'PL02_U.ARC'];special=n if side else int(n>=4);armor=0 if side else n if n<4 else 15*int(n==5)
            prims,_,_=pause.run(raw['SLUS_005.61'],arc,30,char=side,special=special,armor=armor);face,_=pause.raster(arc,prims)
            add(char,'pause',f'{n:02}',0,face.crop((32,144,96,224)))
    from scripts.inventory_shibuki_ui import background
    for side,char in enumerate([xc,zc]):
        screens=[6]if side==0 else[1,2];im=Image.new('RGBA',(256*len(screens),256))
        for k,screen in enumerate(screens):im.alpha_composite(background(raw['ST0E_U0.ARC'],entry(raw['COL0E_U0.ARC'],5),screen),(k*256,0))
        add(char,'title_weapon_get','shared',0,im)
    return records
def main():
    p=argparse.ArgumentParser();p.add_argument('--original',type=Path,required=True);p.add_argument('--br',type=Path,required=True);p.add_argument('--rn',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    manifest=json.loads((ROOT/'release-manifest.json').read_text('utf8'))
    if digest(a.original)!=manifest['ps1_original_sha256']:raise ValueError('Original hash mismatch')
    names=['SLUS_005.61','PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','ST00_00.ARC','COL00_0X.ARC','COL00_0Z.ARC','ST0D_0X.ARC','ST0D_0Z.ARC','COL0D_0X.ARC','COL0D_0Z.ARC','ST0E_U1.ARC','COL0E_U1.ARC','ST0E_U0.ARC','COL0E_U0.ARC']
    base=disc(a.original,['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC']);counts={};excluded=[];pics=[]
    for mode,game,xc,zc in [('ver_buki_riko',a.br,'shibuki','riko'),('ver_rin_nana',a.rn,'nana','rin')]:
        if digest(game)!=manifest['ps1'][mode]['sha256']:raise ValueError('Current mod hash mismatch')
        raw=disc(game,names);c,e=sprites(raw,base,xc,zc,a.out);counts.update(c);excluded+=e;pics+=illustrations(raw,xc,zc,mode,a.out)
        print(mode,c,flush=True)
    save(a.out/'asset-manifest.json',{'sources':manifest['ps1'],'sprites':counts,'illustrations':pics,'excluded':excluded,'not_gameplay_capture':True})
    print('Export complete:',counts,len(pics),'illustrations',flush=True)
if __name__=='__main__':main()
