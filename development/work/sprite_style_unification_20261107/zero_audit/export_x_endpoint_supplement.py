"""Extract X-only separate UI/HQ art from BR14/RN15. Read-only game access."""
import base64
import hashlib
import html
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import Archive
from src.psx_ui_atlas import aliased_composition
from src.psx_ui_render import render_static_rgba

B=ROOT/'work/sprite_style_unification_20261107'
OUT=B/'zero_audit/x_endpoint_supplement01'
OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def render(texture,parts,bank,n,palette,row):
    cp=aliased_composition(parts,bank,n)
    cluts=sorted({p['clut'] for p in cp['parts']})
    pals={k:struct.unpack_from('<16H',palette,(row+k)*32) for k in cluts}
    im,bounds=render_static_rgba(texture,cp,pals)
    world=Image.new('RGBA',(384,384))
    x,y=160+bounds[0],160+bounds[1]
    assert x>=0 and y>=0 and x+im.width<=384 and y+im.height<=384
    world.alpha_composite(im,(x,y))
    return world,{'ref':n,'parts_bank':bank,'part_count':len(cp['parts']),'clut_addends':cluts,
      'palette_base_row':row,'native_bounds':list(bounds),'opaque_world_bbox':world.getbbox(),
      'rgba_sha256':sha(world.tobytes()),'composition_count':cp['bank_frame_count']}

def fixed_plate(items,path,cols,scale):
    # One shared world crop; never individually recenter or resize native figures.
    boxes=[im.getbbox() for _,im in items if im.getbbox()]
    box=(min(b[0] for b in boxes)-3,min(b[1] for b in boxes)-3,max(b[2] for b in boxes)+3,max(b[3] for b in boxes)+3)
    w,h=box[2]-box[0],box[3]-box[1]
    cw=max(230,w*(scale+1)+30);ch=h*scale+50
    sheet=Image.new('RGB',(cw*cols,ch*((len(items)+cols-1)//cols)),'#263345')
    draw=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(items):
        x,y=i%cols*cw,i//cols*ch
        draw.text((x+8,y+6),name,fill='white')
        native=im.crop(box);big=native.resize((w*scale,h*scale),Image.Resampling.NEAREST)
        sheet.paste(native,(x+8,y+38),native)
        sheet.paste(big,(x+w+20,y+38),big)
        draw.text((x+8,y+22),'1x',fill='#aec6de');draw.text((x+w+20,y+22),f'{scale}x / shared origin',fill='#aec6de')
    sheet.save(path)
    return {'path':rel(path),'sha256':digest(path),'size':list(sheet.size),'scale':[1,scale],
      'shared_world_crop':list(box),'world_origin':[160,160],'per_frame_recenter':False,'actually_viewed':False}

def overview(items,path):
    # Different original art uses different coordinates. Do not fake shared proportions.
    cols=3;cw=600;ch=380
    out=Image.new('RGB',(cols*cw,((len(items)+cols-1)//cols)*ch),'#263345');draw=ImageDraw.Draw(out)
    for i,(label,im) in enumerate(items):
        bb=im.getbbox();crop=im.crop((bb[0]-2,bb[1]-2,bb[2]+2,bb[3]+2))
        scale=2 if crop.height>85 else 3
        assert crop.height*scale<=330 and crop.width*(scale+1)<580
        x,y=i%cols*cw,i//cols*ch
        draw.text((x+10,y+8),label,fill='white')
        draw.text((x+10,y+25),f'native {bb[2]-bb[0]}x{bb[3]-bb[1]} / 1x + {scale}x; independent usage',fill='#aec6de')
        out.paste(crop,(x+10,y+50),crop);big=crop.resize((crop.width*scale,crop.height*scale),Image.Resampling.NEAREST)
        out.paste(big,(x+crop.width+30,y+50),big)
    out.save(path)
    return {'path':rel(path),'sha256':digest(path),'size':list(out.size),'scale':'1 and integer2/3 by native category','actually_viewed':False}

CASES={
 'shibuki':('ver_buki_riko',14,'shibuki_riko','b1e00232f8a62bea766e7b40dded110b0c2e66a2fbd2795725347510a0af581d','staging_br_v14.json'),
 'nana':('ver_rin_nana',15,'rin_nana','66b808fc2f37a93eefd915ab7199934bbed62dcef4500ee087b75daa80324989','staging_rn_v15.json')}
NAMES=['PL00_U.ARC','PL02_U.ARC','ST0D_0X.ARC','COL0D_0X.ARC','ST00_00.ARC','COL00_0X.ARC']
report={'scope':'현재 BR14/RN15에서 별도 X HQ/대사/잔기/일시정지 그림을 읽기 추출한 보충판. 플레이4510 모음집 수에 합산하지 않는다.',
 'passed':False,'projects':{},'game_or_art_modified':False,'new_runtime_executed':False,'root_visual_review_pending':True,'user_accepted':False}
for char,(mode,version,stem,bh,planname) in CASES.items():
    folder=OUT/char;folder.mkdir(exist_ok=True)
    binpath=ROOT/f'out/{mode}/sprite_style_unification_20261107_v{version}/{stem}.bin'
    assert digest(binpath)==bh
    assets,recs=read_disc(binpath,NAMES)
    plan=json.loads((B/planname).read_text('utf-8'))
    for n in ['PL00_U.ARC','PL02_U.ARC']:assert sha(assets[n])==plan['resources'][n]['after']
    frames=[];hq=[];dialogue=[];life=[];refs=[]
    def save(group,stem,world,meta):
        file=folder/(stem+'.png');world.save(file)
        meta.update(group=group,native_png=rel(file),png_sha256=digest(file),world_origin=[160,160])
        frames.append(meta)
    arc=assets['ST0D_0X.ARC'];palette=entry(assets['COL0D_0X.ARC'],5)
    for n in range(12):
        world,m=render(entry(arc,0x10102)[63488:75776],entry(arc,10),2,n,palette,35)
        assert m['composition_count']==12
        m.update(source='ST0D_0X.ARC',texture_entry='0x10102',texture_range=[63488,75776],palette_source='COL0D_0X.ARC/entry5')
        save('hq',f'hq_{n:02}',world,m);hq.append((f'HQ b2_{n:02}',world))
    arc=assets['ST00_00.ARC'];palette=entry(assets['COL00_0X.ARC'],5)
    for n in range(8):
        world,m=render(entry(arc,0x10102)[204800:217088],entry(arc,10),11,n,palette,62)
        alias,am=render(entry(arc,0x10102)[204800:217088],entry(arc,10),12,n,palette,62)
        assert world.tobytes()==alias.tobytes()
        m.update(source='ST00_00.ARC',texture_entry='0x10102',texture_range=[204800,217088],palette_source='COL00_0X.ARC/entry5',bank12_display_exact=True)
        save('dialogue',f'dialogue_{n:02}',world,m);dialogue.append((f'dialogue b11/b12_{n}',world))
    for n in range(89,99):
        worlds=[]
        for resource in ['PL00_U.ARC','PL02_U.ARC']:
            arc=assets[resource]
            world,m=render(entry(arc,0x10206),entry(arc,3),3,n,palette,11)
            m.update(source=resource,texture_entry='0x10206',palette_source='COL00_0X.ARC/entry5',bubble_only=n==95)
            save('life',f'{resource[:4]}_life_{n}',world,m);worlds.append(world)
        refs.append({'life_ref':n,'PL00_PL02_display_equal':worlds[0].tobytes()==worlds[1].tobytes()})
        life.append((f'PL00 1UP {n}'+(' bubble only' if n==95 else ''),worlds[0]))
        life.append((f'PL02 1UP {n}',worlds[1]))
    pause=[]
    for resource in ['PL00_U.ARC','PL02_U.ARC']:
        arc=assets[resource]
        world,m=render(entry(arc,0x10007)[12288:],struct.pack('<I',4)+entry(arc,0x12),0,10,entry(arc,0x11),10)
        m.update(source=resource,texture_entry='0x10007',texture_range=[12288,len(entry(arc,0x10007))],palette_source=resource+'/entry0x11')
        save('pause_portrait',resource[:4]+'_pause',world,m);pause.append(world)
    a=Archive(assets['PL00_U.ARC']);idle,_=a.composite(0,0,2)
    if not isinstance(idle,Image.Image):idle=Image.fromarray(idle)
    idle.save(folder/'play_idle_reference.png')
    sheets=[fixed_plate(hq,folder/'hq_all12.png',4,2),
      fixed_plate(dialogue,folder/'dialogue_all8.png',4,2),
      fixed_plate(life,folder/'life_all20.png',5,5),
      overview([('gameplay idle - small pixel sprite',idle),('HQ - separate full-body motion',hq[0][1]),('HQ departure pose',hq[9][1]),('dialogue - large portrait',dialogue[0][1]),('1UP - independent tiny design',life[0][1]),('pause - independent portrait',pause[0])],folder/'endpoints.png')]
    report['projects'][mode]={'character':char,'bin':rel(binpath),'bin_sha256':bh,
      'resources':{n:{'sha256':sha(v),'lba':recs[n]['lba'],'size':len(v)} for n,v in assets.items()},
      'frames':frames,'sheets':sheets,'hq_frames':12,'dialogue_slots':8,'dialogue_alias_bank':12,
      'life_slots_per_resource':10,'life_face_slots_per_resource':9,'life_PL00_PL02_comparison':refs,
      'pause_PL00_PL02_equal':pause[0].tobytes()==pause[1].tobytes(),
      'uses':{'hq':'헌터베이스에서 사용하는 독립 전신/표정·출발 포즈. 게임플레이48px 몸체와 다른 native크기의 수용 도트.',
        'dialogue':'112×96 전후의 별도 대화 일러스트. 여덟 슬롯과 두 조립은행, 아머별 실제 외형 대신 기본 얼굴을 공유하는 과거설계가 있음.',
        'life':'16px 전후의 별도 잔기 얼굴·거품 애니메이션. 작은 조종석 머리 또는 대기머리의 필수 사본이 아님.',
        'pause':'별도 일시정지 초상화. 전신 미술 기준으로 일괄 재작화하지 않음.'},
      'source_code_evidence':['scripts/prepare_nana_hunter.py','scripts/prepare_shibuki_ui.py','scripts/prepare_nana_dialogue.py','scripts/prepare_nana_life_revision.py','src/psx_ui_render.py'],
      'actual_visual_review_this_extraction':False}
report.update(passed=True,limitations=[
 '실제 현재 BIN의 바이트/조립/각 파츠 CLUT로 그린 정적 추출이다. 게임에서 이번에 모든 모션/표정을 재생하지 않았다.',
 'HQ는12참조, 대화는8슬롯과bank12별칭, 잔기는양PL각10슬롯 중95거품만이다. 세트의 별도 폼수를 플레이어28폼에 더하지 않는다.',
 '대화의 반복 스테이지9사본/팔레트 전체와 타이틀·무기획득 대형 그림은 이번 추출 범위 밖이다.',
 '일러스트와 픽셀 전신의 원래 용도/크기를 구분했다. 새 결함 또는 미술 수용 여부는 실제 보충판 검토 후 기록한다.',
 '최종 nativePNG는384원점160 유지. 시트는 한 범주의 공통 월드crop으로1배+정수배만 표시하며 개별 전신 축소/늘림 없음.'
 ])
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
page=['<!doctype html><meta charset="utf-8"><title>X 별도 UI·HQ 보충판</title><style>body{background:#141c27;color:#eef3f9;font:16px system-ui,sans-serif;margin:24px}a{color:#a8d4ff}img{display:block;image-rendering:pixelated;max-width:none;margin:12px 0}figure{margin:28px 0;overflow:auto;border:1px solid #526479;padding:12px}h2{margin-top:40px}.note{background:#3b3020;padding:14px}</style>',
 '<h1>시부키·나나 별도 UI / 헌터베이스 보충판</h1><p>현재 BR14 / RN15 실제 BIN 추출. 4,510 플레이어 모음집과 별도이며 완료율 분모에 더하지 않습니다.</p>',
 '<p class="note">HQ의 독립 전신 도트, 큰 대화/일시정지 일러스트, 작은 잔기 디자인은 서로 다른 용도입니다. 이 파일은 실제 게임 재생이 아닌 원점·CLUT를 보존한 정적 비교입니다. 원본크기와 정수배를 나란히 표시합니다.</p>',
 '<p><a href="report.json">출처·해시·범위 JSON</a> · <a href="../full_scope_matrix01/COVERAGE.html">전체 폼 범위표</a> · <a href="../final_endpoint_audit01/ZERO_UI_HQ_SUPPLEMENT.html">리코·린 보충판</a></p>']
for proj in report['projects'].values():
    page.append('<h2 id="'+proj['character']+'">'+('시부키' if proj['character']=='shibuki' else '나나')+'</h2>')
    for s in proj['sheets']:
        p=ROOT/s['path'];encoded=base64.b64encode(p.read_bytes()).decode('ascii')
        page.append('<figure><figcaption>'+html.escape(p.name)+' — native + integer scale</figcaption><img alt="'+html.escape(proj['character']+'/'+p.name)+'" width="'+str(s['size'][0])+'" height="'+str(s['size'][1])+'" src="data:image/png;base64,'+encoded+'"></figure>')
(OUT/'X_UI_HQ_SUPPLEMENT.html').write_text('\n'.join(page),encoding='utf-8')
print(json.dumps({'passed':True,'report':rel(OUT/'report.json'),'sheets':8,'frames':sum(len(p['frames']) for p in report['projects'].values())}))
