"""Read actual current discs; inspect endpoint copies and album exclusions only."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry, SELECTION_MAPPING
from scripts.overhaul_sprites_audit import render, rgba
from src.psx_player import composition_frame
from src.psx_ui_atlas import aliased_composition, local_composition
from src.psx_static_effect import compose_static

W = ROOT / 'work/sprite_style_unification_20261107'
D = Path(__file__).parent
O = D / 'final_endpoint_audit01'
O.mkdir(exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: json.loads(p.read_text('utf8'))
rel = lambda p: p.relative_to(ROOT).as_posix()

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def static_world(texture, comp):
    px, size, bb, _ = compose_static(texture, local_composition(comp))
    a = np.zeros((384,384), np.uint8)
    s = np.frombuffer(px, np.uint8).reshape(size[1],size[0])
    yy,xx = np.nonzero(s)
    if len(xx):
        x,y = xx+bb[0]+160, yy+bb[1]+160
        assert x.min()>=0 and y.min()>=0 and x.max()<384 and y.max()<384
        a[y,x]=s[yy,xx]
    return a

def words(data,row): return struct.unpack_from('<16H',data,row*32)

def plate(items,path,cols=4,scale=3):
    # All items retain native size. Tight transparent margin trim changes no pixels.
    cropped=[]
    for label, im in items:
        bb=im.getbbox()
        if bb: im=im.crop((max(0,bb[0]-3),max(0,bb[1]-3),min(im.width,bb[2]+3),min(im.height,bb[3]+3)))
        cropped.append((label,im))
    cw=max(220,max(im.width for _,im in cropped)*scale+20)
    ch=max(im.height for _,im in cropped)*scale+48
    out=Image.new('RGB',(cols*cw,((len(items)+cols-1)//cols)*ch),'#263345')
    dr=ImageDraw.Draw(out)
    for i,(label,im) in enumerate(cropped):
        x,y=i%cols*cw,i//cols*ch
        dr.text((x+8,y+8),label,fill='white')
        im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
        out.paste(im,(x+(cw-im.width)//2,y+32),im)
    out.save(path)

CASES={
 'riko':{'mode':'ver_buki_riko','version':14,'stem':'shibuki_riko','bin_sha256':'b1e00232f8a62bea766e7b40dded110b0c2e66a2fbd2795725347510a0af581d',
         'plan':'staging_br_v14.json','latest':'riko/prepared_ground_boots_v13','review':'riko/all_unique_review_v8/inventory.json'},
 'rin': {'mode':'ver_rin_nana','version':15,'stem':'rin_nana','bin_sha256':'66b808fc2f37a93eefd915ab7199934bbed62dcef4500ee087b75daa80324989',
         'plan':'staging_rn_v15.json','latest':'zero_audit/rin_extension/prepared_burst_remaining02','review':'zero_audit/rin_extension/all_unique_review303/inventory.json'}
}
NAMES=('PL01_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC','LOAD_U.ARC','MOJIPAT.ARC','ST0D_0Z.ARC','COL0D_0Z.ARC','ST00_00.ARC','COL00_0Z.ARC')
report={'scope':'최신 두 BIN의 별도 끝점 사본과 최종 원화 연결만 읽기 검토. 기존 전섹터/패킹/MIPS 검사 재실행 아님.',
        'passed':False,'projects':{},'game_or_sources_modified':False,'runtime_executed':False,'user_accepted':False}
for char,c in CASES.items():
    out=O/char;out.mkdir(exist_ok=True)
    binpath=ROOT/f"out/{c['mode']}/sprite_style_unification_20261107_v{c['version']}/{c['stem']}.bin"
    assert digest(binpath)==c['bin_sha256']
    assets,recs=read_disc(binpath,NAMES)
    arc=assets['PL01_U.ARC'];parts=entry(arc,3);pal=entry(arc,9)
    plan=read(W/c['plan'])
    assert sha(arc)==plan['resources']['PL01_U.ARC']['after']
    assert sha(assets['ST0E_U1.ARC'])==plan['resources']['ST0E_U1.ARC']['after']
    review=read(W/c['review']);assert review['source_sha256']==sha(arc) and review['all_visually_reviewed']
    latest=W/c['latest'];proposal=read(latest/'proposal.json');assert proposal['after_sha256']==sha(arc)
    targets=[]
    if char=='riko':
        for f in proposal['registration']['frames']:
            p=ROOT/f['target'];assert digest(p)==f['target_sha256']
            a=render(arc,f['bank'],f['bank']*5,f['ref'])[0]
            assert np.array_equal(a,np.array(Image.open(p)))
            targets.append(f"b{f['bank']}_{f['ref']:03}")
    else:
        for n,h in proposal['target_sha256'].items():
            p=latest/f'b1_{int(n):03}_indices.png';assert digest(p)==h
            assert np.array_equal(render(arc,1,5,int(n))[0],np.array(Image.open(p)))
            targets.append(f'b1_{int(n):03}')
    selection=[]
    tex=entry(assets['ST0E_U1.ARC'],0x10102)[:40960]
    ui_parts=entry(assets['ST0E_U1.ARC'],10)
    for n,(b,k) in SELECTION_MAPPING.items():
        cp=composition_frame(ui_parts,0,n);assert all(p['clut']==0 for p in cp['parts'])
        actual=static_world(tex,cp);expected=render(arc,b,b*5,k)[0]
        assert np.array_equal(actual,expected),(char,'selection',n)
        selection.append({'ui_ref':n,'player':f'b{b}_{k:03}','pixels_and_origin_exact':True})
    assert entry(assets['COL0E_U1.ARC'],5)[:32]==pal[:32]
    idle=render(arc,0,0,147)[0]
    menu=assets['MOJIPAT.ARC'];po=struct.unpack_from('<I',menu,4)[0];assert po==6788
    save_cp=composition_frame(menu,2,43)
    save=static_world(entry(assets['LOAD_U.ARC'],0x10008),save_cp)
    assert np.array_equal(save,idle),(char,'save43')
    assert menu[po+320:po+352]==pal[:32]
    assert menu[po+29*32:po+30*32]==pal[13*32:14*32]
    recipe=read(latest/'static_effects.json')
    assert recipe['parts_sha256']==sha(parts)
    assert recipe['modified_texture_sha256']==sha(entry(arc,0x10206))
    items=[('play idle b0_147',rgba(idle,words(pal,0))),('save 43 normal',rgba(save,words(pal,0))),
           ('save 43 black',rgba(save,words(pal,13)))]
    separate=[]
    htex=entry(assets['ST0D_0Z.ARC'],0x10102)[63488:81920]
    hparts=entry(assets['ST0D_0Z.ARC'],10);hpal=words(entry(assets['COL0D_0Z.ARC'],5),35)
    hqitems=[]
    for n in range(14):
        cp=aliased_composition(hparts,2,n);assert all(p['clut']==0 for p in cp['parts'])
        a=static_world(htex,cp);im=rgba(a,hpal);im.save(out/f'hq_{n:02}.png')
        hqitems.append((f'HQ bank2 ref{n}',im))
        if n in (0,13):items.append((f'HQ independent {n}',im))
        separate.append({'group':'hunter_base','ref':n,'source':'ST0D_0Z.ARC','parts_bank':2,'native_bbox':im.getbbox(),'in_current_album':False})
    plate(hqitems,out/'hq_all14.png',cols=7,scale=2)
    lifeitems=[]
    for n in (89,90,91,92,93,94,96,97,98):
        cp=composition_frame(parts,3,n);assert all(p['clut']==0 for p in cp['parts'])
        a=static_world(entry(arc,0x10206),cp)
        im=rgba(a,words(entry(assets['COL00_0Z.ARC'],5),11));im.save(out/f'life_{n:03}.png')
        lifeitems.append((f'1UP bank3 ref{n}',im))
        separate.append({'group':'life_item','ref':n,'source':'PL01_U.ARC 0x10206','parts_bank':3,'palette':'COL00_0Z.ARC entry5 row11','in_current_album':False})
        if n==89:items.append(('1UP separate 16px head',im))
    plate(lifeitems,out/'life_all9.png',cols=5,scale=5)
    for n in (75,77):items.append((f'new ride head b1_{n}',rgba(render(arc,1,5,n)[0],words(pal,0))))
    pause_cp=aliased_composition(struct.pack('<I',4)+entry(arc,0x12),0,10)
    pause=static_world(entry(arc,0x10007)[12288:],pause_cp)
    pause_im=rgba(pause,words(entry(arc,0x11),10));pause_im.save(out/'pause.png');items.append(('pause separate portrait',pause_im))
    dialogue=[]
    for n in range(3):
        cp=aliased_composition(entry(assets['ST00_00.ARC'],10),13,n)
        a=static_world(entry(assets['ST00_00.ARC'],0x10102)[217088:223232],cp)
        im=rgba(a,words(entry(assets['COL00_0Z.ARC'],5),63));im.save(out/f'dialogue_{n}.png')
        dialogue.append((f'dialogue mouth {n}',im))
    plate(dialogue,out/'dialogue_all3.png',cols=3,scale=3)
    plate(items,out/'endpoints.png',cols=5,scale=3)
    report['projects'][c['mode']]={'character':char,'bin':rel(binpath),'bin_sha256':c['bin_sha256'],
      'resources':{n:{'sha256':sha(v),'lba':recs[n]['lba'],'size':len(v)} for n,v in assets.items()},
      'latest_authored_refs_exact':targets,'latest_authored_ref_count':len(targets),'selection_copies':selection,
      'selection_normal_palette_exact':True,'selection_38':'b1_011 귀환빛. CLUT0 지정이지 idle 별칭이 아님.',
      'save43_pixels_and_origin_exact_to_idle147':True,'save_normal10_black29_palettes_exact_to_player0_13':True,
      'static23_24_current_recipe_hash_binding_exact':True,'static_recipe':rel(latest/'static_effects.json'),
      'prior_full_visual_review':{'path':rel(W/c['review']),'sha256':digest(W/c['review']),'source_arc_matches_actual_disc':True,
        'reviewer':'root24판' if char=='riko' else 'hud_checkpoint58판','new_full_review_repeated':False},
      'separate_resources':separate,'preview_sheets':[rel(out/n) for n in ('endpoints.png','hq_all14.png','life_all9.png','dialogue_all3.png')],
      'preview_actually_viewed_this_audit':False}
report.update(passed=True,body_latest_targets_mismatched=0,selection_or_save_copy_mismatched=0,
  album_scope_evidence={'files':['scripts/export_zero_consistency.py:235','scripts/build_sprite_consistency_gallery.py:53','scripts/build_sprite_style_album.py:95'],
    'included':['압축 gameplay 436 표시/각 캐릭터','static6 23/24 몸체','선택32사본/각 Zero','저장43 일반/블랙'],
    'excluded':['HQ 전신14/각 Zero','잔기 아이템 머리9/각 Zero','대사 얼굴3과 반복 stage 사본','일시정지/선택 대형 초상화','타이틀·무기획득 배경 전신']},
  limitations=['별도 HQ/초상화/아이템은 다른 해상도와 과거 수용 원화를 사용한다. 최신 gameplay 사본 누락과 동일시하지 않는다.',
    '이번에 본문313개를 다시 미술검토하거나 기존 전섹터/CPU/GPU 회귀를 반복하지 않았다. 최신 ARC와 기존 전수 시각장부 해시를 결속했다.',
    '대사 stage 반복사본 전체와 title/weapon-get 배경 전체는 이번 실제 그림 열람 범위 밖이다.',
    '부분VRAM b1_42..49는 이전 업로드 의존이며 새 완성 그림/미사용으로 분류하지 않는다.',
    '새 게임 조작·실기·사용자 수용을 수행하지 않았다.'])
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report':rel(O/'report.json'),'sha256':digest(O/'report.json'),'projects':{k:{'authored':v['latest_authored_ref_count'],'selection':len(v['selection_copies'])} for k,v in report['projects'].items()}}))
