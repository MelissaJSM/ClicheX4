"""Prepare native Korean labels; preserve fixed UVs for direct-draw loaders."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_riko_illustrations import repack_one_bank,regrid_ui_parts
from scripts.inventory_shibuki_ui import sheet
from scripts.inventory_korean_ui import grey
from scripts.discover_inputs import sha256
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static,patch_static
from src.psx_korean_typography import render_mask,profile_manifest

# Keep native READY (frame 0), as requested after the Korean UI review.
MENU={3:'시작 버튼을 누르세요',4:'불러오는 중...',5:'시부키',6:'리코',7:'출동',8:'스카이 라군',9:'정글',10:'스노 베이스',11:'바이오 랩',12:'볼케이노',13:'마린 베이스',14:'사이버 공간',15:'에어 포스',16:'군용 열차',17:'메모리얼 홀',18:'우주항',19:'최종 병기',20:'구역 1',21:'구역 2',22:'게임 오버',23:'감사합니다',41:'시작 버튼을 누르세요'}
WEAPONS_X=['시부키 버스터','노바 스트라이크','라이트닝 웹','프로스트 타워','소울 보디','라이징 파이어','그라운드 헌터','에이밍 레이저','더블 사이클론','트윈 슬래셔']
WEAPONS_R=['낙봉파','공원무','뇌신격','비연각','용염인','천공패','빙열참','질풍아']
TITLE_MENU_TEXT={'게임 시작','이어하기','설정'}

def label(text,size,height=12,ink=14,background=0,border=None,profile=None,shaded=False):
    profile=profile or ('display' if height>13 else 'menu')
    # Fixed native canvases are never enlarged. Leave space for the outline
    # or lower-right shadow before fitting the actual font ink.
    for fs in range(height,8,-1):
        mask=render_mask(text,profile,size=fs)
        if mask.width<=size[0]-3 and mask.height<=size[1]-3:break
    else:raise ValueError(f'Label cannot fit: {text} in {size}')
    if profile=='title' and text in TITLE_MENU_TEXT:
        # Different syllables in the same font have different tight heights.
        # Normalize the three main choices together: 11px ink + 1px shadow,
        # an even final width, and therefore one exact integer-pixel centre.
        mask=mask.point(lambda v:v if v>=40 else 0)
        mask=mask.crop(mask.getbbox())
        width=max(3,round(mask.width*11/mask.height))
        if width%2==0:width+=1
        mask=mask.resize((width,11),Image.Resampling.BOX)
        if mask.width>size[0]-3:raise ValueError('Normalized title menu does not fit')
    alpha=np.zeros((size[1],size[0]),np.uint8)
    x=(size[0]-mask.width)//2;y=(size[1]-mask.height)//2
    alpha[y:y+mask.height,x:x+mask.width]=np.array(mask,np.uint8)
    m=alpha>=40;out=np.full_like(alpha,background)
    if border is not None:
        edge=np.zeros_like(m)
        edge[1:]|=m[:-1];edge[:-1]|=m[1:];edge[:,1:]|=m[:,:-1];edge[:,:-1]|=m[:,1:]
        out[edge]=border
    if shaded:
        if background!=0 or border is not None:raise ValueError('Shading requires a native monotone 0..15 palette')
        shadow=np.zeros_like(m);shadow[1:,1:]=m[:-1,:-1];out[shadow]=3
        # Indices 3..15 are the preserved native title/load grey ramps. The
        # loading-yellow and title-inactive palettes use the same index ramp.
        brightness=np.linspace(1.0,0.84,mask.height)[:,None]
        ramp=np.clip(np.rint(3+12*np.array(mask,dtype=float)/255*brightness),3,15).astype(np.uint8)
        region=out[y:y+mask.height,x:x+mask.width];on=np.array(mask)>=40
        region[on]=ramp[on]
    else:out[alpha>=112]=ink
    return out

def frames(g,p,bank):
    return {n:local_composition(aliased_composition(p,bank,n)) for n in range(aliased_composition(p,bank,0)['bank_frame_count'])}

def loading_ink_bounds(a):
    ys,xs=np.nonzero(a)
    if not len(xs):raise ValueError('Loading label is empty')
    return [int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]

def align_loading_label(frame,a):
    """Move existing ink inside its fixed UV canvas, without reshaping glyphs."""
    if frame in (5,6):side,margin='right',2
    elif frame==7:side,margin='left',2
    elif 8<=frame<=19:side,margin='right',1
    elif frame in (20,21):side,margin='left',0
    else:return a
    x0,y0,x1,y1=loading_ink_bounds(a)
    dx=a.shape[1]-margin-x1 if side=='right' else margin-x0
    if x0+dx<0 or x1+dx>a.shape[1]:raise ValueError(f'Loading ink cannot fit: {frame}')
    out=np.zeros_like(a);out[:,x0+dx:x1+dx]=a[:,x0:x1]
    if not np.array_equal(out[:,x0+dx:x1+dx],a[:,x0:x1]) or np.count_nonzero(out)!=np.count_nonzero(a):
        raise ValueError(f'Loading alignment changed glyph pixels: {frame}')
    if loading_ink_bounds(out)!=[x0+dx,y0,x1+dx,y1]:raise ValueError('Loading ink bounds differ')
    return out

def verify_loading_layout(before,after,cp,targets,exe):
    """Check actual direct-draw rectangles, compact gaps and protected logos."""
    table=0xDED04
    rows=[struct.unpack_from('<hhBBBB',exe,table+i*8) for i in range(9)]
    expected=[(96,96,0,8,1,1),(200,192,112,5,2,2),(248,192,117,4,2,3),
              (16,192,8,3,1,0),(32,192,203,2,1,0),(64,192,12,4,1,0),
              (16,208,32,6,1,0),(120,208,121,3,1,0),(120,208,137,3,1,0)]
    if rows!=expected:raise ValueError('Accepted loading rectangle table differs')
    raw=np.frombuffer(after,np.uint8);atlas=np.empty(len(raw)*2,np.uint8)
    atlas[::2]=raw&15;atlas[1::2]=raw>>4;atlas=atlas.reshape(-1,256)
    frames_checked={}
    for n in range(5,22):
        row=3 if n==5 else 4 if n==6 else 5 if n==7 else 6 if n<=19 else n-13
        x,y,t,w,h,clut=rows[row]
        if 8<=n<=19:t=exe[table+72+n-8] # Native stage-to-UV table.
        direct=atlas[(t//16)*16:(t//16+h)*16,(t%16)*16:(t%16+w)*16]
        pixels,size=targets[n]
        if direct.shape!=(size[1],size[0]) or direct.tobytes()!=pixels:
            raise ValueError(f'Loading fixed UV differs from frame: {n}')
        ink=loading_ink_bounds(direct)
        if not (0<=ink[0]<ink[2]<=w*16 and 0<=ink[1]<ink[3]<=h*16):raise ValueError('Loading ink escaped canvas')
        frames_checked[str(n)]={'label':MENU[n],'canvas':[w*16,h*16],
                               'screen_origin':[x,y],'uv':[t%16*16,t//16*16],
                               'ink_in_canvas':ink,'screen_ink':[x+ink[0],y+ink[1],x+ink[2],y+ink[3]]}
    names=[];stages=[];departure=frames_checked['7']['screen_ink']
    for n in (5,6):
        name=frames_checked[str(n)]['screen_ink'];gap=departure[0]-name[2]
        if name[2]!=62 or departure[0]!=66 or gap!=4:raise ValueError('Loading name gap differs')
        names.append({'frame':n,'label':MENU[n],'name_bounds':name,'departure_bounds':departure,'gap_pixels':gap})
    for n in range(8,20):
        stage=frames_checked[str(n)]['screen_ink'];areas=[]
        for area in (20,21):
            bounds=frames_checked[str(area)]['screen_ink'];gap=bounds[0]-stage[2]
            if stage[2]!=111 or bounds[0]!=120 or gap!=9:raise ValueError('Loading stage/area gap differs')
            areas.append({'frame':area,'bounds':bounds,'gap_pixels':gap})
        stages.append({'frame':n,'label':MENU[n],'stage_bounds':stage,'areas':areas,
                       'native_loader_displays_area':n<17})
    for n in (0,1,2):
        if compose_static(before,cp[n])[:3]!=compose_static(after,cp[n])[:3]:
            raise ValueError(f'Loading READY/logo changed: {n}')
    return {'frames':frames_checked,'names':names,'stages':stages,
            'name_gap_bounds':[min(v['gap_pixels'] for v in names),max(v['gap_pixels'] for v in names)],
            'stage_area_gap_bounds':[9,9],'stage_labels_checked':12,
            'native_rectangles':rows,'native_rectangle_bytes_sha256':sha256(exe[table:table+84]),
            'exe_output_generated':False,'fixed_uvs_sizes_compositions_preserved':True,
            'ready_and_both_logo_compositions_preserved':True,'logo_screen_x':[200,248]}

def patch_preserving(g,cp,targets):
    out=patch_static(g,cp,targets)
    for n,c in cp.items():
        expected=targets[n] if n in targets else compose_static(g,c)[:2]
        if compose_static(out,c)[:2]!=expected:raise ValueError(f'Non-target static frame changed: {n}')
    return out

def align_title_menu(texture,parts):
    """Align visible Korean ink around the shared x=160 title-object anchor.

    The original English labels share a left edge but have different canvas
    widths. Centring Korean inside those canvases leaves different world-space
    centres. Selection and dimmed objects use these same three compositions.
    """
    count=aliased_composition(parts,0,0)['bank_frame_count']
    before={n:aliased_composition(parts,0,n) for n in range(count)}
    rendered={n:compose_static(texture,local_composition(c))[:3] for n,c in before.items()}
    def ink(frame):
        px,size,bounds=frame;a=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);ys,xs=np.where(a!=0)
        if not len(xs):raise ValueError('Title menu text is empty')
        return [int(xs.min())+bounds[0],int(ys.min())+bounds[1],int(xs.max())+1+bounds[0],int(ys.max())+1+bounds[1]]
    reference=ink(rendered[2]);reference_center2=reference[0]+reference[2]
    out=bytearray(parts);shifts={};coordinate_bytes=set();proof={}
    for n in (2,29,30):
        old_ink=ink(rendered[n]);delta2=reference_center2-old_ink[0]-old_ink[2]
        dx=round(delta2/2);dy=reference[3]-old_ink[3];shifts[n]=(dx,dy)
        for p in before[n]['parts']:
            x,y=p['x']+dx,p['y']+dy
            if not -128<=x<=127 or not -128<=y<=127:raise ValueError('Aligned title coordinate exceeds s8')
            offset=p['record_offset']+2;out[offset:offset+2]=struct.pack('<bb',x,y)
            if dx or dy:coordinate_bytes.update((offset,offset+1))
        proof[str(n)]={'before_ink_bounds':old_ink,'delta':[dx,dy]}
    changed={i for i,(a,b) in enumerate(zip(parts,out)) if a!=b}
    if not changed<=coordinate_bytes:raise ValueError('Title alignment changed non-coordinate bytes')
    unchanged=0
    for n,old in before.items():
        c=aliased_composition(out,0,n);after=compose_static(texture,local_composition(c))[:3];dx,dy=shifts.get(n,(0,0))
        if after[:2]!=rendered[n][:2]:raise ValueError(f'Title bitmap or size changed during alignment: {n}')
        expected=tuple(v+(dx if i%2==0 else dy) for i,v in enumerate(rendered[n][2]))
        if after[2]!=expected:raise ValueError(f'Title frame moved unexpectedly: {n}')
        # Tile selection, palette selectors, order and flips remain exact.
        if [p['flags'] for p in old['parts']]!=[p['flags'] for p in c['parts']] or [p['tile'] for p in old['parts']]!=[p['tile'] for p in c['parts']]:
            raise ValueError(f'Title palette or texture selection changed: {n}')
        if not (dx or dy):unchanged+=1
        if n in shifts:
            new_ink=ink(after);proof[str(n)]['after_ink_bounds']=new_ink
            if abs(new_ink[0]+new_ink[2]-reference_center2)>1:raise ValueError('Title ink alignment failed')
            if new_ink[3]!=reference[3]:raise ValueError('Title text baselines differ')
    return bytes(out),{'reference_frame':2,'object_anchor_x':160,'screen_ink_center_x':160+reference_center2/2,'frames':proof,'coordinate_bytes_changed':len(changed),'unchanged_frames_checked':unchanged,'all_text_bitmaps_sizes_preserved':True,'all_tile_palette_flip_flags_preserved':True,'texture_unchanged_by_alignment':True}

def main(output):
    output.mkdir(exist_ok=False);files={};checks={};preview=[]
    def read(n):
        p=D/'inventory'/n
        return p.read_bytes() if p.exists() else (D/'ui_inventory'/n).read_bytes()
    def save(n,old,new):
        if len(old)!=len(new):raise ValueError('UI resource size changed')
        (output/n).write_bytes(new);files[n]={'before':sha256(old),'after':sha256(new),'size':len(new)}
    def add(key,a):preview.append((key,grey(a.tobytes(),(a.shape[1],a.shape[0]))))
    # Direct-draw loading code uses fixed texture UVs. Patch these tiles in
    # place and check every other composed frame instead of repacking them.
    raw=read('LOAD_U.ARC');menu=read('MOJIPAT.ARC');g=entry(raw,0x10008);cp=frames(g,menu,2);targets={}
    for n,text in MENU.items():
        _,size,_,_=compose_static(g,cp[n]);a=label(text,size,12,profile='loading',shaded=True)
        a=align_loading_label(n,a);targets[n]=(a.tobytes(),size);add(f'menu {n}',a)
    ng=patch_preserving(g,cp,targets)
    layout=verify_loading_layout(g,ng,cp,targets,read('SLUS_005.61'))
    save('LOAD_U.ARC',raw,replace_entry(raw,0x10008,ng));checks['loading_fixed_uv']={'frames':list(targets),'other_frames_preserved':True,'ink_alignment':layout}
    # Full names in both small and large character-selection name frames.
    name='ST0E_U1.ARC';raw=read(name);g=entry(raw,0x10102);p=entry(raw,10);bank=g[40960:90112];targets={}
    for n,text in {2:'캐릭터 선택',3:'텐코 시부키',4:'유즈하 리코',5:'텐코 시부키',7:'유즈하 리코'}.items():
        c=local_composition(aliased_composition(p,1,n));_,size,_,_=compose_static(bank,c)
        row=7 if n==2 else 4 if n==7 else 6
        pal=struct.unpack_from('<16H',entry(read('COL0E_U1.ARC'),5),row*32)
        light=max(range(1,16),key=lambda i:sum(pal[i]>>s&31 for s in (0,5,10)))
        dark=min(range(1,16),key=lambda i:sum(pal[i]>>s&31 for s in (0,5,10)))
        a=label(text,size,22 if n in (2,5,7) else 12,light,border=dark);targets[n]=(a.tobytes(),size);add(f'select {n}',a)
    p=regrid_ui_parts(p,1,targets);ng,p,proof=repack_one_bank(bank,p,1,targets)
    save(name,raw,replace_entry(replace_entry(raw,0x10102,g[:40960]+ng+g[90112:]),10,p));checks['selection']=proof
    # Pause labels have a native background-color index14; index8 is the
    # contrasting text in both active/inactive original menu palettes.
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        raw=read(name);g=entry(raw,0x10007);p=struct.pack('<I',4)+entry(raw,0x12);cp=frames(g[96*128:],p,0);targets={}
        labels=dict(enumerate(WEAPONS_R if name=='PL01_U.ARC' else WEAPONS_X));labels.update({11:'탈출',12:'설정'})
        for n,text in labels.items():
            old,size,_,_=compose_static(g[96*128:],cp[n]);a=label(text,size,12,ink=8,background=14)
            if n in (11,12):
                # Keep the original button edge while replacing its lettering.
                original=np.frombuffer(old,np.uint8).reshape(size[1],size[0]);a[:2]=original[:2];a[-2:]=original[-2:];a[:,:2]=original[:,:2];a[:,-2:]=original[:,-2:]
            targets[n]=(a.tobytes(),size);add(f'{name} {n}',a)
        ng=patch_preserving(g[96*128:],cp,targets)
        save(name,raw,replace_entry(raw,0x10007,g[:96*128]+ng));checks[name]={'pause_frames':list(targets),'other_frames_preserved':True}
    # Title text shares its atlas with the accepted logo. Repacking protects
    # every non-target composed object, including mode name and animated logo.
    name='ST0E_U0.ARC';raw=read(name);g=entry(raw,0x10002);p=struct.pack('<I',4)+entry(raw,0x12);targets={}
    for n,text in {2:'게임 시작',4:'시작 버튼을 누르세요',5:'시작 또는 결정 버튼을 누르세요',6:'시작 또는 결정 버튼을 누르세요',29:'이어하기',30:'설정'}.items():
        c=local_composition(aliased_composition(p,0,n));_,size,_,_=compose_static(g,c);a=label(text,size,12,14,profile='title',shaded=True);targets[n]=(a.tobytes(),size);add(f'title {n}',a)
    p=regrid_ui_parts(p,0,targets);ng,p,proof=repack_one_bank(g,p,0,targets)
    p,alignment=align_title_menu(ng,p);proof['part_coordinate_bytes_preserved']=False;proof['menu_alignment']=alignment
    save(name,raw,replace_entry(replace_entry(raw,0x10002,ng),0x12,p[4:]));checks['title']=proof
    for start in range(0,len(preview),24):sheet(preview[start:start+24],output/f'preview_{start//24}.png',4,(280,100))
    result={'kind':'korean_ui_raster_proposal','bin_applied':False,'files':files,'checks':checks,'typography':profile_manifest(),'pending':['actual emulator review of the new font profiles']}
    (output/'proposal.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'files':list(files),'labels':len(preview)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
