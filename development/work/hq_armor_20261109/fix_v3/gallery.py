"""Decode the selected final discs into one offline, self-contained illustration review."""
import sys, struct, json, hashlib, base64, io, importlib.util
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[3]; H=ROOT/'work/hq_armor_20261109'; F=H/'fix_v3'
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_disc import file_hash
from src.psx_ui_atlas import aliased_composition, write_tile
from src.psx_player import composition_frame, decode_stream
from src.psx_ui_render import render_static_rgba
from scripts.inventory_shibuki_ui import background
from scripts.prepare_ui_revision import pause_background

OUT=ROOT/'out/illustration_review_20261109'; OUT.mkdir(exist_ok=True)
(OUT/'images').mkdir(exist_ok=True)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sys.path.insert(0,str(ROOT/'work/pause_variants_20261109'))
pause=module('pause_cpu',ROOT/'work/pause_variants_20261109/verify_cpu.py')
black=module('black_ui',ROOT/'work/illustration_variants_20261108/black_ui.py')
def load(p):return json.loads(p.read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def uri(im):
    b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
def col(raw,row):return struct.unpack_from('<16H',entry(raw,5),row*32)
def native(raw,pal,bank,frame,row,private=False):
    p=entry(raw,10);start=struct.unpack_from('<I',entry(raw,12),bank*4)[0]
    if private:
        off=struct.unpack_from('<I',p,bank*4)[0]+1376
        comp=composition_frame(struct.pack('<I',4)+p[off:],0,frame)
    else:comp=aliased_composition(p,bank,frame)
    pals={q['clut']:col(pal,row+q['clut'])for q in comp['parts']}
    return render_static_rgba(entry(raw,0x10102)[start:],comp,pals)
def world(im,bb):
    c=Image.new('RGBA',(160,160));c.alpha_composite(im,(80+bb[0],80+bb[1]));return c

cards=[];checks=[];sources=[]
def add(char,category,state,frames,labels,note='',ref='',origin=''):
    key=f'{char}-{category}-{len(cards):03}';files=[]
    for n,im in enumerate(frames):
        dest=OUT/'images'/f'{key}-{n:02}.png';im.save(dest);files.append(dest.relative_to(OUT).as_posix())
    cards.append(dict(id=key,char=char,category=category,state=state,frames=[uri(im)for im in frames],
                      size=[im.size for im in frames],labels=labels,note=note,ref=ref,origin=origin,files=files))

headbody=['기본형 · 머리/몸 없음','포스 · 머리','포스 · 몸','포스 · 머리+몸 (풀세트 공용)']
state_labels=['기본형'if n==0 else ('포스 풀세트'if n==15 else '포스 · '+'+'.join(label for bit,label in [(1,'머리'),(2,'몸'),(4,'팔'),(8,'다리')]if n&bit))for n in range(16)]+['얼티밋 획득 전 · 재킷','얼티밋 획득 후 · 수영복']
refs={}
for mode,chars in [('ver_rin_nana',['나나','린']),('ver_buki_riko',['시부키','리코'])]:
    ptr=load(F/'builds.json')[0]if mode=='ver_rin_nana'else load(ROOT/'projects'/mode/'current_build.json')
    game=ROOT/Path(ptr['cue']).with_suffix('.bin');assert file_hash(game)==ptr['sha256']
    names=['SLUS_005.61','ST00_00.ARC','COL00_0X.ARC','COL00_0Z.ARC','ST0D_0X.ARC','ST0D_0Z.ARC','COL0D_0X.ARC','COL0D_0Z.ARC','PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC','ST0E_U0.ARC','COL0E_U0.ARC','ST0F_UX.ARC','ST0F_UZ.ARC','COL0F_U0.ARC']
    raw,records=read_disc(game,names);sources.append({'mode':mode,'cue':ptr['cue'],'sha256':ptr['sha256'],'files':{n:sha(b)for n,b in raw.items()}})
    exe=raw['SLUS_005.61'];helper=black.palette_helper(mode);assert exe[black.off(0x800ca048):black.off(0x800ca048)+len(helper)]==helper
    base_x='nana'if mode=='ver_rin_nana'else'buki'
    for char,stem,kinds in [(chars[0],base_x,['X','4th armor','ultimate armor']),(chars[1],'rin'if mode=='ver_rin_nana'else'riko',['zero'])]:
        for kind in kinds:
            p=ROOT/'character'/mode/f'{stem}({kind}).webp';key=f'{char}-{kind}'
            refs[key]={'label':f'{char} · {kind} 설정화','data':'data:image/webp;base64,'+base64.b64encode(p.read_bytes()).decode(),'source':p.relative_to(ROOT).as_posix()}
    for side,char in enumerate(chars):
        im,bb=native(raw['ST0E_U1.ARC'],raw['COL0E_U1.ARC'],1,side,4)
        add(char,'캐릭터 선택','공용', [im],['선택 일러스트'],'선택 화면은 아머와 블랙 상태에 따라 바뀌지 않는 공용 그림입니다.',f'{char}-'+('X'if side==0 else'zero'),'ST0E_U1.ARC / bank1')
    # Reconstruct all HQ X states from the actual on-disc compressed container.
    x=raw['ST0D_0X.ARC'];blob=entry(x,13)[96:];chunks=[]
    for k in range(struct.unpack_from('<I',blob,4)[0]):
        kind,start,offset,size=struct.unpack_from('<4I',blob,16+16*k);chunks.append((kind,start,decode_stream(blob,offset,len(blob),size).data))
    states=next(b for kind,start,b in chunks if kind==0);dictionary=b''.join(b for kind,start,b in chunks if kind==1)
    for state in range(18):
        data=states[state*1412:(state+1)*1412];texture=bytearray(176*128)
        for tile,j in enumerate(struct.unpack('<176H',data[:352])):
            if j!=65535:write_tile(texture,tile,bytes(v for q in dictionary[j*128:j*128+128]for v in(q&15,q>>4)))
        p=struct.pack('<I',4)+data[352:];ims=[]
        for n in range(12):
            im,bb=render_static_rgba(texture,composition_frame(p,0,n),{0:col(raw['COL0D_0X.ARC'],35)});im=world(im,bb)
            expected=Image.open(H/mode/'review'/f'{state:02}'/f'{n:02}.png').convert('RGBA');assert im.tobytes()==expected.tobytes()
            ims.append(im)
        ref=f'{chars[0]}-'+('X'if state==0 else'4th armor'if state<16 else'ultimate armor')
        add(chars[0],'헌터베이스',state_labels[state],ims,[f'프레임 {n:02}'for n in range(12)],'원점과 160×160 복원 캔버스 고정. 0~2 눈, 3~8 손짓/대화, 9 출격, 10 반전 자세, 11 입.',ref,'ST0D_0X.ARC / 상태 '+str(state))
    # Normal/Black Zero share the same indexed art and use the actual native palette helper.
    for variant in [0,1]:
        pal=list(col(raw['COL0D_0Z.ARC'],35))
        if variant:
            for i,(r,g,b)in black.CHANGES[mode].items():pal[i]=(pal[i]&0x8000)|r|g<<5|b<<10
        z=raw['ST0D_0Z.ARC'];start=struct.unpack_from('<I',entry(z,12),8)[0];parts=entry(z,10);count=aliased_composition(parts,2,0)['bank_frame_count'];ims=[]
        for n in range(count):
            im,bb=render_static_rgba(entry(z,0x10102)[start:],aliased_composition(parts,2,n),{0:pal});ims.append(world(im,bb))
        add(chars[1],'헌터베이스','블랙 · '+('레드 린'if mode=='ver_rin_nana'else'검은 외투/흰 안쪽')if variant else'일반',ims,[f'프레임 {n:02}'for n in range(count)],'색상 변형은 현재 EXE의 블랙 팔레트 명령과 대조했습니다.',f'{chars[1]}-zero','ST0D_0Z.ARC / bank2')
    for n in range(6):
        ids=[n,n+4]if n<4 else([0,4]if n==4 else[1,5]);ims=[]
        for frame in ids:ims.append(native(raw['ST00_00.ARC'],raw['COL00_0X.ARC'],11,frame,62,private=n>=4)[0])
        label=headbody[n]if n<4 else state_labels[n+12]
        add(chars[0],'대화',label,ims,['입 닫힘','입 열림'],'팔·다리만 다른 조합은 같은 머리/몸 초상화를 공유합니다.',f'{chars[0]}-'+('X'if n==0 else'4th armor'if n<4 else'ultimate armor'),'ST00_00.ARC / bank11')
    for variant in [0,1]:
        pal=list(col(raw['COL00_0Z.ARC'],63))
        if variant:
            for i,(r,g,b)in black.CHANGES[mode].items():pal[i]=(pal[i]&0x8000)|r|g<<5|b<<10
        z=raw['ST00_00.ARC'];start=struct.unpack_from('<I',entry(z,12),13*4)[0];p=entry(z,10);count=aliased_composition(p,13,0)['bank_frame_count']
        ims=[render_static_rgba(entry(z,0x10102)[start:],aliased_composition(p,13,n),{0:pal})[0]for n in range(count)]
        add(chars[1],'대화','블랙'if variant else'일반',ims,[f'표정 {n}'for n in range(count)],'',f'{chars[1]}-zero','ST00_00.ARC / bank13')
    for side,char in enumerate(chars):
        for n in range(2 if side else 6):
            arc=raw['PL01_U.ARC'if side else'PL00_U.ARC'if n<4 else'PL02_U.ARC'];special=n if side else int(n>=4);armor=0 if side else n if n<4 else (15 if n==5 else 0)
            prims,_,_=pause.run(exe,arc,30,char=side,special=special,armor=armor);face,coords=pause.raster(arc,prims)
            im=face.crop((32,144,96,224));scene=pause_background(arc);scene.alpha_composite(face)
            state=('블랙'if n else'일반')if side else(headbody[n]if n<4 else state_labels[n+12])
            add(char,'일시정지',state,[im,scene],['초상화 원래 창','메뉴 배치 합성'],'원래 사선 창 마스크를 포함합니다. 메뉴 이미지는 복원 합성이며 실기 캡처가 아닙니다.',f'{char}-'+('zero'if side else'X'if n==0 else'4th armor'if n<4 else'ultimate armor'),'원래 MIPS 메뉴 렌더러 / 항목30')
    for side,char in enumerate(chars):
        imgs=[]
        for filename,palname,screens in [('ST0E_U0.ARC','COL0E_U0.ARC',[6]if side==0 else[1,2]),('ST0F_UX.ARC','COL0F_U0.ARC',[5]if side==0 else[3,4]),('ST0F_UZ.ARC','COL0F_U0.ARC',[5]if side==0 else[3,4])]:
            im=Image.new('RGBA',(256*len(screens),256))
            for k,screen in enumerate(screens):im.alpha_composite(background(raw[filename],entry(raw[palname],5),screen),(k*256,0))
            imgs.append(im)
        identical=imgs[0].tobytes()==imgs[1].tobytes()==imgs[2].tobytes()
        checks.append({'mode':mode,'character':char,'action_copies_identical':identical})
        assert identical,(mode,char,'title/acquisition images differ')
        add(char,'타이틀·획득','공용',imgs,['타이틀','X 루트 획득 자원','제로 루트 획득 자원'],'타이틀과 두 획득 자원에서 같은 그림임을 픽셀 복원으로 확인했습니다. 아머·블랙 전용 그림은 현재 없습니다.',f'{char}-'+('X'if side==0 else'zero'),'ST0E_U0 / ST0F_UX / ST0F_UZ')
    checks.append({'mode':mode,'final_disc_authenticated':True,'HQ_X216_equals_native_GPU_render':True,'black_helper_exact':True,'actual_gameplay_verified_by_gallery':False})
    print(mode,'decoded',flush=True)

# Comparison is explicitly labelled old/new and is separate from current-game cards.
before=Image.open(F/'baseline/ver_rin_nana/review/15/00.png').convert('RGBA');after=Image.open(H/'ver_rin_nana/review/15/00.png').convert('RGBA')
compare={'before':uri(before),'after':uri(after)}
payload=json.dumps({'cards':cards,'refs':refs,'sources':sources,'compare':compare},ensure_ascii=False).replace('</',r'<\/')
template=(F/'gallery_template.html').read_text('utf8');(OUT/'일러스트_모음집.html').write_text(template.replace('/*PAYLOAD*/',payload),'utf8')
manifest={'sources':sources,'checks':checks,'cards':[{k:v for k,v in c.items()if k not in('frames',)}for c in cards],'total_images':sum(len(c['frames'])for c in cards),'self_contained_html':True,'actual_gameplay_capture':False}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8')
# Technical contact sheets for reviewing the first frame of every state.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
for n,char in enumerate(['나나','린','시부키','리코']):
    subset=[c for c in cards if c['char']==char];sheet=Image.new('RGB',(1440,((len(subset)+3)//4)*300),(30,41,57));draw=ImageDraw.Draw(sheet)
    for k,c in enumerate(subset):
        im=Image.open(OUT/c['files'][0]).convert('RGBA');factor=min(2,340/im.width,244/im.height)
        im=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.NEAREST);x=k%4*360;y=k//4*300
        draw.text((x+8,y+4),char+' · '+c['category'],font=font,fill='white');draw.text((x+8,y+25),c['state'],font=font,fill='#b8cee8')
        sheet.paste(im,(x+(360-im.width)//2,y+50+(244-im.height)//2),im)
    sheet.save(OUT/f'audit_{n}.png')
print('Gallery:',len(cards),'groups',manifest['total_images'],'images',flush=True)
