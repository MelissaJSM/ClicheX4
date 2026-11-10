"""통합 개선의 실제 BIN 스프라이트·팔레트·공유 구조를 읽기 전용으로 조사한다."""
import json,struct,sys,hashlib,html
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.verify_nana_ultimate_ui import read_assets
from scripts.project import digest
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_ui_atlas import local_composition

D=ROOT/'work/overhaul_20261105/sprites'
BASES={
 'ver_buki_riko':('out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin','8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a'),
 'ver_rin_nana':('out/ver_rin_nana/nana_ultimate_nova_20261104T185708218838Z/rin_nana.bin','5dd089c181cd141955f8e98e3a6b028f24253f2ca4179ed34e194f6a276047f0')}
SOURCE_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
NAMES=('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','MOJIPAT.ARC','LOAD_U.ARC','COL0E_U1.ARC')
PLACEHOLDERS={105,*range(175,183)}

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
def load(project):
    relative,expected=BASES[project];path=ROOT/relative
    if digest(path)!=expected:raise ValueError('Baseline hash mismatch')
    return read_assets(path,NAMES)
def rgba(indices,words):
    words=np.asarray(words,np.uint16)
    table=np.array([[(int(w)>>s&31)*255//31 for s in (0,5,10)]+[0 if i%16==0 else 255] for i,w in enumerate(words)],np.uint8)
    return Image.fromarray(table[indices])
def render(arc,gb,pb,n,palette_row=0):
    g,c,p=entry(arc,2),entry(arc,3),entry(arc,9)
    f=graphics_bank(g,gb,allow_bank_aliases=True)['frames'][n]
    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    comp=composition_frame(c,pb,n)
    if not comp['parts']:return np.zeros((384,384),np.uint8),{'bounds':None,'parts':[],'raw_sha256':sha(raw)}
    if pb in (5,6,7,8) and gb==0:comp=local_composition(comp)
    pix,size,bounds,_=compose_indices(raw,f['tile_count'],comp,allowed_cluts={0,1,2,3})
    small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);a=np.zeros((384,384),np.uint8)
    sy,sx=np.nonzero(small);x=sx+bounds[0]+160;y=sy+bounds[1]+160
    if len(x) and (x.min()<0 or x.max()>=384 or y.min()<0 or y.max()>=384):raise ValueError('Native pixels outside audit canvas')
    a[y,x]=small[sy,sx]
    return a,{'bounds':bounds,'parts':comp['parts'],'raw_sha256':sha(raw),'tile_count':f['tile_count'],'stream_offset':f['offset']}
def metrics(a):
    y,x=np.nonzero(a)
    if not len(x):return {'opaque_pixels':0,'bbox':None}
    return {'opaque_pixels':len(x),'bbox':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],
            'size':[int(x.max()-x.min()+1),int(y.max()-y.min()+1)],'centroid':[float(x.mean()-160),float(y.mean()-160)],
            'color_count':len(np.unique(a[a>0]))}
def board(items,path,cols=8,scale=2):
    cell=(192,176);rows=(len(items)+cols-1)//cols
    pic=Image.new('RGB',(cell[0]*cols,cell[1]*rows),(28,34,45));draw=ImageDraw.Draw(pic)
    for i,(label,im) in enumerate(items):
        x=i%cols*cell[0];y=i//cols*cell[1]
        shown=im.crop((112,120,208,200)).resize((192,160),Image.Resampling.NEAREST)
        pic.paste(shown,(x,y+16),shown);draw.text((x+4,y+2),label,fill='white')
    pic.save(path)
def main():
    D.mkdir(parents=True,exist_ok=True)
    if digest(ROOT/'MegaMan X4.bin')!=SOURCE_SHA:raise ValueError('Original mismatch')
    original,_=read_assets(ROOT/'MegaMan X4.bin',NAMES)
    oldpal=entry(original['PL01_U.ARC'],9);reports={};pages=[]
    for project in BASES:
        assets,records=load(project);out=D/project;out.mkdir(exist_ok=True);resources=out/'baseline';resources.mkdir(exist_ok=True)
        for name,data in assets.items():(resources/name).write_bytes(data)
        pal=entry(assets['PL01_U.ARC'],9);menu=assets['MOJIPAT.ARC'];po=struct.unpack_from('<I',menu,4)[0]
        black={'normal_row_sha256':sha(pal[:32]),'black_row_sha256':sha(pal[13*32:14*32]),
               'black_row_equals_original':pal[13*32:14*32]==oldpal[13*32:14*32],
               'black_row_equals_current_normal':pal[13*32:14*32]==pal[:32],
               'menu_normal_matches_body':menu[po+10*32:po+11*32]==pal[:32],
               'menu_black_matches_original_black':menu[po+29*32:po+30*32]==oldpal[13*32:14*32],
               'palette_row_13_offset':next(q['offset'] for q in __import__('scripts.discover_inputs',fromlist=['psx_arc']).psx_arc(assets['PL01_U.ARC']) if int(q['type'],16)==9)+13*32,
               'menu_black_palette_offset':po+29*32,'bitmap_bank_shared':True,'new_black_design_authored':False}
        a,_=render(assets['PL01_U.ARC'],0,0,147)
        normal=struct.unpack_from('<64H',pal);bp=list(normal);bp[:16]=struct.unpack_from('<16H',pal,13*32)
        board([('normal',rgba(a,normal)),('current Black',rgba(a,bp)),('restore normal palette',rgba(a,normal))],out/'black_palette_review.png',cols=3)
        ride=[]
        for n in range(66,86):
            a,r=render(assets['PL01_U.ARC'],1,5,n);b,o=render(original['PL01_U.ARC'],1,5,n)
            ride.append({'frame':n,'indices_identical_to_zero':np.array_equal(a,b),'stream_identical_to_zero':r['raw_sha256']==o['raw_sha256'],'metrics':metrics(a)})
        sheets=[];frames={};failures=[]
        for name,arcname,gb,pb,pr in [('zero_base','PL01_U.ARC',0,0,0),('zero_special','PL01_U.ARC',1,5,0),('x_base','PL00_U.ARC',0,0,0),('x_fourth','PL00_U.ARC',0,-1,1),('x_preultimate','PL02_U.ARC',0,0,0),('x_ultimate','PL02_U.ARC',0,-1,1)]:
            arc=assets[arcname];p=entry(arc,9);words=struct.unpack_from('<64H',p);items=[]
            count=len(graphics_bank(entry(arc,2),gb,allow_bank_aliases=True)['frames'])
            for n in range(count):
                if arcname!='PL01_U.ARC' and n in PLACEHOLDERS:continue
                try:
                    if pb==-1:
                        im=Image.new('RGBA',(384,384));metas=[];mask=np.zeros((384,384),np.uint8)
                        for layer in (0,8,5,7,6):
                            a,m=render(arc,gb,layer,n);im.alpha_composite(rgba(a,words if layer==0 else words[32:48] if layer==7 else words[16:32]));mask[a>0]=1;metas.append(m)
                        rec={'metrics':metrics(mask),'layers':metas}
                    else:
                        a,m=render(arc,gb,pb,n);im=rgba(a,words);rec={'metrics':metrics(a),**m}
                except (ValueError,IndexError) as error:
                    failures.append({'group':name,'frame':n,'error':str(error)});continue
                frames[f'{name}_{n:03}']=rec
                folder=out/name;folder.mkdir(exist_ok=True);im.save(folder/f'{n:03}.png');items.append((f'{name} {n}',im))
            for start in range(0,len(items),64):
                path=out/f'{name}_{start//64:02}.png';board(items[start:start+64],path);sheets.append(path.relative_to(D).as_posix())
        write(out/'frames.json',frames);write(out/'audit.json',{'source_bin':BASES[project][0],'source_sha256':BASES[project][1],
              'assets':{name:{**records[name],'sha256':sha(data)} for name,data in assets.items()},'black':black,'ride_heads':ride,
              'rendered_references':len(frames),'unrendered_references':failures,'sheet_pages':sheets,'runtime_verified':False,
              'notes':['Sheets are native index decoding, not resized artwork; review panels use nearest-neighbor 2x.','A shorter jumping/crouched bbox is not by itself a size defect.','Fixed world origin (160,160); no per-frame normalization.','X full forms composite base + legs + head + arm + body. Effects retain runtime CLUT limitations.','Sheet cells show world window -48..48 X / -40..40 Y. Large effects outside that preview window remain complete in native PNGs.']})
        reports[project]={'black':black,'original_ride_heads':[q['frame'] for q in ride if q['indices_identical_to_zero']], 'rendered_references':len(frames),'unrendered_references':failures}
        pages+=sheets
    write(D/'audit_summary.json',reports)
    (D/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Sprite audit</title><style>body{background:#181c26;color:white;font:16px sans-serif}img{image-rendering:pixelated;max-width:100%}details{margin:2em}</style><h1>두 모드 실제 BIN 스프라이트 비교</h1><p>정적 복원 · 게임 실행 검증 아님 · 정상 포즈 변형과 크기 오류를 구분하여 검토</p>'+''.join(f'<details><summary>{html.escape(p)}</summary><img loading="lazy" src="{p}"></details>' for p in pages),'utf8')
    print(json.dumps(reports,ensure_ascii=False))
if __name__=='__main__':main()
