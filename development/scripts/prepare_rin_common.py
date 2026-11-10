"""린 수용본에 공통 한글/로고를 자원별 병합한다. 첫 모드와 BIN은 읽기 전용."""
import argparse,contextlib,copy,io,json,runpy,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import DiscReader,psx_arc,sha256
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import require,render_pixels
from scripts.prepare_riko_illustrations import repack_one_bank,regrid_ui_parts
from scripts.prepare_korean_ui import label,align_loading_label,patch_preserving,frames
from scripts.prepare_cliche_logo_v4 import old_records,pack_bank
from scripts.prepare_cliche_logo import background_indices,write_background
from scripts.prepare_korean_ending import extract_screens
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels,write_tile
from src.psx_static_effect import compose_static
from src.psx_korean_font import font_cache_proposal

PARENT=ROOT/'out/ver_rin_nana/rin_effect_colors_20261029T043059092457Z'
PARENT_SHA='917227b3d063139c225e2a28a58f6eb9743b716fb0d511a7d42933aa396c6ad1'
DONOR=ROOT/'out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin'
DONOR_SHA='8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a'
SOURCE_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
FIRST=ROOT/'work/ver_buki_riko/korean_v1'
NAMES={5:'하나코 나나',6:'아오쿠모 린'}
MODE='하나코 나나 / 아오쿠모 린 모드'

def renamed(text):
    text=text.replace('텐코 시부키','하나코 나나').replace('유즈하 리코','아오쿠모 린')
    for a,b in [('리코는','린은'),('리코가','린이'),('리코를','린을'),('리코와','린과'),('리코야','린아')]:text=text.replace(a,b)
    return text.replace('시부키','나나').replace('리코','린')

def read_disc(path,names):
    with path.open('rb') as f:
        disc=DiscReader(f,path.stat().st_size);records={r['path'].split('/')[-1].split(';')[0]:r for r in disc.inspect()['files']}
        return {n:disc.read(records[n]['lba'],records[n]['size']) for n in names},{n:records[n] for n in names}

def frame(texture,parts,bank,n):
    return compose_static(texture,local_composition(aliased_composition(parts,bank,n)))[:3]

def merge_load(current,donor):
    """Keep fixed direct-draw UVs; transplant original/Rin save sprites separately."""
    menu=current['MOJIPAT.ARC'];dmenu=donor['MOJIPAT.ARC'];offs=struct.unpack_from('<4I',menu)
    require(offs==struct.unpack_from('<4I',dmenu),'MOJIPAT bank boundaries differ')
    texture=entry(donor['LOAD_U.ARC'],0x10008);old=entry(current['LOAD_U.ARC'],0x10008)
    common=set(range(24))|{25,41};movable={3,22,23,41};fixed=common-movable
    records=old_records(dmenu,2);source=old_records(menu,2);donor_records=copy.deepcopy(records)
    # US 80016124 draws U=0,W=112; U=112,W=96; U=0,W=16, V=208,H=48.
    # The rightmost 48px are native character storage, not background UVs.
    bg_tiles={y*16+x for y in range(13,16) for x in range(13)}
    reserved={q['page']*256+q['tile'] for n in fixed for q in aliased_composition(dmenu,2,n)['parts']}|bg_tiles
    # Entire fixed loading rectangles, including omitted transparent tiles.
    exe=donor['SLUS_005.61'];table=0xDED04
    for i in range(9):
        _,_,t,w,h,_=struct.unpack_from('<hhBBBB',exe,table+i*8)
        starts=list(exe[table+72:table+84]) if i==6 else [t]
        reserved.update(t0+dy*16+dx for t0 in starts for dy in range(h) for dx in range(w))
    patterns={}
    def register(px,t):
        a=np.frombuffer(px,np.uint8).reshape(16,16)
        for v,fl in ((a,0),(a[:,::-1],64),(a[::-1],128),(a[::-1,::-1],192)):patterns.setdefault(v.tobytes(),(t,fl))
    for t in sorted(reserved):register(tile_pixels(texture,t),t)
    free=iter(t for t in range(len(texture)//128) if t not in reserved)
    ng=bytearray(texture)
    for n in sorted(set(range(53))-fixed):
        records[n]=[]
        for q in (donor_records[n] if n in movable else source[n]):
            flags,t,x,y=struct.unpack('<BBbb',q);px=tile_pixels(texture if n in movable else old,(flags&3)*256+t)
            if px not in patterns:
                ident=next(free,None);require(ident is not None,f'Save/UI tile budget exceeded at frame {n}; reserved {len(reserved)}');register(px,ident);write_tile(ng,ident,px)
            ident,flip=patterns[px];records[n].append(struct.pack('<BBbb',((flags&252)^flip)|(ident//256),ident%256,x,y))
    bank,proof=pack_bank(records,offs[3]-offs[2]);nm=dmenu[:offs[1]]+menu[offs[1]:offs[2]]+bank+menu[offs[3]:]
    require(len(nm)==len(menu),'MOJIPAT size changed')
    protected=[]
    for n in common:require(frame(ng,nm,2,n)==frame(texture,dmenu,2,n),f'Common label changed {n}')
    for n in set(range(53))-common:
        require(frame(ng,nm,2,n)==frame(old,menu,2,n),f'Save frame changed {n}');protected.append(n)
    require(all(tile_pixels(ng,t)==tile_pixels(texture,t) for t in bg_tiles),'Repeated background touched')
    # New full names use the accepted 80px strips and 4px departure gap.
    cp={n:local_composition(aliased_composition(nm,2,n)) for n in range(53)};targets={}
    for n,text in NAMES.items():
        a=align_loading_label(n,label(text,(80,16),12,profile='loading',shaded=True));targets[n]=(a.tobytes(),(80,16))
    ng=patch_preserving(bytes(ng),cp,targets)
    out=replace_entry(replace_entry(current['LOAD_U.ARC'],0x10008,ng),0x10001,entry(donor['LOAD_U.ARC'],0x10001))
    return out,nm,{'save_frames_preserved':sorted(protected),'bank':proof,'font_from_accepted_mode':True,'palette_bank_from_current_rin':True,'background_uv_rect_preserved':[0,208,208,48],'background_renderer_address':'0x80016124','relocated_composed_only_labels':sorted(movable)}

def prepare(output):
    require(output.resolve().is_relative_to(ROOT/'work/ver_rin_nana') and not output.exists(),'Fresh isolated work directory required')
    for p,h in [(PARENT/'rin_nana.bin',PARENT_SHA),(DONOR,DONOR_SHA),(ROOT/'MegaMan X4.bin',SOURCE_SHA)]:require(digest(p)==h,'Input BIN hash mismatch')
    import scripts.prepare_gangzi_capsule as gangzi
    capsules=json.loads((gangzi.D/'capsule_layout.json').read_text('utf8'))
    names={'SLUS_005.61','LOAD_U.ARC','MOJIPAT.ARC','PL00_U.ARC','PL01_U.ARC','PL02_U.ARC',
           'ST0E_U0.ARC','COL0E_U0.ARC','ST0E_U1.ARC','COL0E_U1.ARC','ST0D_0X.ARC','ST0D_0Z.ARC',
           'ST0F_UX.ARC','ST0F_UZ.ARC','ST0F_U1.ARC','COL0F_U0.ARC','COL0F_U1.ARC'}|{f'STD_1_{n}U.ARC' for n in range(1,9)}
    for c in capsules:
        names.add(c['name']);names.update(f"COL{c['name'][2:4]}_{c['name'][6]}{s}.ARC" for s in ('X','Z'))
    current,records=read_disc(PARENT/'rin_nana.bin',sorted(names));donor,_=read_disc(DONOR,sorted(names));original,_=read_disc(ROOT/'MegaMan X4.bin',sorted(names))
    output.mkdir(parents=True);preview=output/'preview';preview.mkdir();inventory=output/'inventory';inventory.mkdir();ui=output/'ui_inventory';ui.mkdir()
    merged=dict(current);proof={};log=io.StringIO()
    # Approved logo and menus only: retain title archive's Rin weapon-get art.
    for kind in (0x10002,0x12,0xd):merged['ST0E_U0.ARC']=replace_entry(merged['ST0E_U0.ARC'],kind,entry(donor['ST0E_U0.ARC'],kind))
    col=merged['COL0E_U0.ARC'];merged['COL0E_U0.ARC']=replace_entry(col,5,entry(donor['COL0E_U0.ARC'],5)[:32]+entry(col,5)[32:])
    import scripts.prepare_cliche_logo_v4 as logo
    logo.MODE_LABEL=MODE;mode,proof['mode_label']=logo.mode_label()
    raw=merged['ST0E_U0.ARC'];g=entry(raw,0x10002);p=struct.pack('<I',4)+entry(raw,0x12);targets={}
    for n in (0,17):
        px,size,bounds=frame(g,p,0,n);require(size==(240,88),'Unexpected accepted title canvas');a=np.frombuffer(px,np.uint8).reshape(88,240).copy();a[:16]=0;a[:16,24:216]=mode;targets[n]=(a.tobytes(),size)
    ng,np_,proof['title']=repack_one_bank(g,p,0,targets);merged['ST0E_U0.ARC']=replace_entry(replace_entry(raw,0x10002,ng),0x12,np_[4:])
    render_pixels(np.frombuffer(targets[0][0],np.uint8).reshape(88,240),entry(merged['COL0E_U0.ARC'],5)[:32]).save(preview/'title_logo_mode.png')
    merged['LOAD_U.ARC'],merged['MOJIPAT.ARC'],proof['load']=merge_load(current,donor)
    # Renderer is the accepted 54-byte hook; loading layout is display data.
    exe,proof['renderer']=font_cache_proposal(current['SLUS_005.61']);newexe=bytearray(exe);newexe[0xDED04:0xDED04+84]=donor['SLUS_005.61'][0xDED04:0xDED04+84];merged['SLUS_005.61']=bytes(newexe)
    proof['exe_changed_offsets']=[i for i,(a,b) in enumerate(zip(current['SLUS_005.61'],newexe)) if a!=b]
    # Existing logo background art, retaining every other background screen.
    proof['backgrounds']={}
    for name in ('ST0E_U1.ARC','ST0F_UX.ARC','ST0F_UZ.ARC'):
        before=extract_screens(merged[name]);pixels,rows=background_indices(donor[name]);require(np.array_equal(rows,background_indices(merged[name])[1]),'Background CLUT changed')
        merged[name],tiles=write_background(merged[name],pixels);after=extract_screens(merged[name])
        for n in set(before)-{1,2}:
            require(all(np.array_equal(a,b) for a,b in zip(before[n],after[n])),f'Other background screen changed: {name}/{n}')
        proof['backgrounds'][name]={'tiles':len(tiles),'other_screens_preserved':len(before)-2}
    # Selection full names: preserve all non-name composed art.
    name='ST0E_U1.ARC';raw=merged[name];g=entry(raw,0x10102);p=entry(raw,10);bank=g[40960:90112];targets={}
    for n,text in {2:'캐릭터 선택',3:NAMES[5],4:NAMES[6],5:NAMES[5],7:NAMES[6]}.items():
        _,size,_=frame(bank,p,1,n);row=7 if n==2 else 4 if n==7 else 6;pal=struct.unpack_from('<16H',entry(merged['COL0E_U1.ARC'],5),row*32)
        light=max(range(1,16),key=lambda i:sum(pal[i]>>s&31 for s in (0,5,10)));dark=min(range(1,16),key=lambda i:sum(pal[i]>>s&31 for s in (0,5,10)))
        a=label(text,size,22 if n in (2,5,7) else 12,light,border=dark);targets[n]=(a.tobytes(),size);render_pixels(a,struct.pack('<16H',*pal)).save(preview/f'select_name_{n}.png')
    np_=regrid_ui_parts(p,1,targets);ng,np_,proof['selection_names']=repack_one_bank(bank,np_,1,targets)
    for b,lo,hi in [(0,0,40960),(1,40960,90112),(2,90112,len(g))]:
        texture=ng if b==1 else g[lo:hi]
        for n in range(aliased_composition(p,b,0)['bank_frame_count']):
            if b==1 and n in targets:continue
            require(frame(texture,np_,b,n)==frame(g[lo:hi],p,b,n),f'Selection art changed {b}/{n}')
    merged[name]=replace_entry(replace_entry(raw,0x10102,g[:40960]+ng+g[90112:]),10,np_)
    # Native pause menu label replacement; portraits and personal colors stay.
    from scripts.prepare_korean_ui import WEAPONS_X,WEAPONS_R
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        raw=merged[name];g=entry(raw,0x10007);p=struct.pack('<I',4)+entry(raw,0x12);cp=frames(g[96*128:],p,0);targets={}
        labels=dict(enumerate(WEAPONS_R if name=='PL01_U.ARC' else ['사랑이']+WEAPONS_X[1:]));labels.update({11:'탈출',12:'설정'})
        for n,text in labels.items():
            px,size,_,_=compose_static(g[96*128:],cp[n]);a=label(text,size,12,8,14)
            if n in (11,12):
                old=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);a[:2]=old[:2];a[-2:]=old[-2:];a[:,:2]=old[:,:2];a[:,-2:]=old[:,-2:]
            targets[n]=(a.tobytes(),size)
        ng=patch_preserving(g[96*128:],cp,targets);merged[name]=replace_entry(raw,0x10007,g[:96*128]+ng)
    # Prepare translation from accepted content, with Korean particles fixed.
    trans=runpy.run_path(str(FIRST/'translation_ko.py'));translation={k:{i:[renamed(t) for t in pages] for i,pages in trans[k].items()} for k in ('X','R')}
    headers={k:renamed(v) for k,v in trans['HEADERS'].items()};headers.update({'ZERO':NAMES[6],'X':NAMES[5],'MEGAMAN':NAMES[5],'MEGA MAN':NAMES[5],'DR.LIGHT':'강지 사장','DR. LIGHT':'강지 사장'})
    translation['HEADERS']=headers
    from scripts.inventory_korean import messages
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        for m in messages(entry(merged[name],0x15))[:-1]:
            for page in m['pages']:
                line=page['lines'][0]
                if line['words'][-1]&0x4000 and not line['words'][0]&0x1000:require(line['text'].strip() in headers,'Unmapped original speaker '+repr(line['text']))
    (output/'translation_ko.py').write_text('\n'.join(k+'='+repr(v) for k,v in translation.items())+'\n','utf8')
    # Inputs for established codecs are isolated copies; their module paths
    # are rebound only within this preparation process, never edited on disk.
    for name,raw in merged.items():(inventory/name).write_bytes(raw);(ui/name).write_bytes(raw)
    # Dialogue helper expects pre-hook EXE for its independent 54-byte audit.
    (inventory/'SLUS_005.61').write_bytes(current['SLUS_005.61'])
    import scripts.prepare_korean_dialogue as dialogue
    import scripts.verify_korean_dialogue as audit
    import scripts.prepare_korean_stage_labels as stage
    import scripts.prepare_korean_ending as ending
    dialogue.D=output;audit.D=output;stage.D=output;ending.D=output
    ending.NARRATIVE={n:[(x,y,renamed(t)) for x,y,t in texts] for n,texts in ending.NARRATIVE.items()}
    with contextlib.redirect_stdout(log):
        dialogue.main(output/'dialogue');proof['dialogue']=audit.verify(output/'dialogue')
        stage.main(output/'stage');ending.main(output/'ending')
    for sub in ('dialogue','stage','ending'):
        report=json.loads((output/sub/'proposal.json').read_text('utf8'))
        for name in report['files']:
            if name=='SLUS_005.61':continue
            proposed=(output/sub/name).read_bytes()
            if sub=='dialogue':merged[name]=proposed
            else:merged[name]=proposed
        proof[sub+'_summary']={k:v for k,v in report.items() if k not in ('dialogue','files')}
    # Boss surfaces contain no player assets and are unchanged in the Rin base.
    for n in range(1,9):
        name=f'STD_1_{n}U.ARC';require(current[name]==original[name],'Boss resource has local edits');merged[name]=donor[name]
    # Reuse the accepted GangZi art within original capsule layers only.
    with contextlib.redirect_stdout(log):proof['gangzi']=gangzi.patch_capsules(merged,merged,preview)
    # Body, battle palette, portraits and player sound are immutable here.
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        for e in psx_arc(current[name]):
            kind=int(e['type'],16)
            if kind in (0x15,0x10007):continue
            require(entry(current[name],kind)==entry(merged[name],kind),f'Player nontext resource changed {name}/{kind:x}')
    from scripts.prepare_korean_loading_names import loading_preview
    for n in NAMES:loading_preview(merged,n).save(preview/f'loading_{n}.png')
    changed={n:a for n,a in merged.items() if a!=current[n]};files={}
    for name,raw in changed.items():
        require(len(raw)==len(current[name]),'Resource length changed');(output/name).write_bytes(raw)
        files[name]={'before':sha256(current[name]),'after':sha256(raw),'size':len(raw)}
    (output/'pipeline.log').write_text(log.getvalue(),'utf8')
    report={'kind':'rin_common_localization','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'donor_sha256':DONOR_SHA,'source_sha256':SOURCE_SHA,'files':files,'records':{n:records[n] for n in files},'checks':proof,'names':NAMES,'mode_label':MODE,'nana_art_produced':False,'voice_policy_changed':False,'runtime_verified':False}
    (output/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(output),'resources':len(changed),'names':NAMES},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output.resolve())
