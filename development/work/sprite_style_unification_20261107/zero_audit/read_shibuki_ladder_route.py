"""Existing test card/menu-route evidence only; no emulator/save mutation."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3];B=ROOT/'work/sprite_style_unification_20261107';O=Path(__file__).parent/'shibuki_ladder_route01';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=ROOT/'work/ver_buki_riko/sprite_style_checkpoint13/cards/x_allboss.mcr';raw=p.read_bytes()
assert sha(p)=='bfeacc6f59f0731581af8e8d77709fea04211775a2b66acf4478ff01ff5c9c6e'
assert len(raw)==131072 and raw[:2]==b'MC'
slots=[]
for block in range(1,16):
    rec=raw[block*128:(block+1)*128];name=rec[10:30].split(b'\0')[0].decode('ascii',errors='replace')
    if rec[0]!=0x51 or not name.startswith('BASLUS-00561'):continue
    for n in range(3):
        off=block*8192+512+n*42;s=raw[off:off+42]
        slots.append({'DATA':n+1,'file':name,'offset':off,'character':s[0],'max_hp':s[1],'arm_type':s[2],'armor':s[3],'boss_palette_flags':s[4],'ultimate_or_black':s[41],'bytes':s.hex()})
post=[s for s in slots if s['DATA']==3 and s['character']==0 and s['armor']==15 and s['ultimate_or_black']==1]
assert len(post)==1
summary=B/'runtime/shibuki_ultimate_dash14_summary.json';old=json.loads(summary.read_text('utf8'))
assert old['save_load_route']=='시험카드 사본1 DATA3를 게임 메뉴에서 불러오기'
load=B/'runtime/br14_load_ultimate.json';meta=json.loads(load.read_text('utf8'));assert meta['loaded'] and meta['source_record_authenticated']
paths=[p,summary,load,B/'runtime/br14_continue_trace.json',ROOT/'docs/SHIBUKI_LADDER.md',ROOT/'docs/NANA_ULTIMATE_LADDER.md',ROOT/'docs/NANA_ULTIMATE_CEREMONY.md',ROOT/'work/ver_rin_nana/armor_capture/20261104T105703747488Z/verification.local.json']
paths += [ROOT/f'work/ver_buki_riko/sprite_style_checkpoint{n}/cards/copies.json'for n in(10,11,12,13)]
report={'scope':'기존 시험카드·실행기록에서 Ultimate after 메뉴로드 및 사다리 접근 증거만 읽음. 새 플레이/카드/저장상태 쓰기 없음.',
 'card':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'slots':slots},
 'confirmed_menu_route':{'card_port':1,'slot':'DATA3','ultimate_after':True,'proof':summary.relative_to(ROOT).as_posix(),'load_trace':load.relative_to(ROOT).as_posix(),'historical_session':old['session']},
 'ladder_route':{'fresh_boot_menu_to_near_ladder_replay_record_found':False,'exact_stage_from_record':None,'tested_short_input_plan':None,
     'older_user_ladder_position':{'character':'Nana Ultimate','x':1960,'y':707.5,'animation':31,'frame':147,'record':'docs/NANA_ULTIMATE_CEREMONY.md','basis':'과거사용자가직접이동한저장상태진행;새부팅입력계획아님','resource_match':'RAM/VRAM일치기록은있으나전체화면exact실패로전수실기아님'},
     'next_step':'새후보통합후위기존카드의새사본으로정상부팅/메뉴DATA3로드가가능하다.사다리스테이지선택과짧은안전접근동선은현재확인된재생계획이없어실기담당이화면으로확인해야한다.'},
 'searched_scope':['현재sprite_style runtime 요약/로드기록','기존Shibuki/Nana 사다리문서·Nana104443/105703 자원관측기록','기존시험카드10~13복사이력'],
 'evidence':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)}for q in paths],
 'limits':['이조사는최단경로나현재스테이지의사다리위치를새로발굴하는장거리플레이조사가아니다.','옛사다리F1은현재사용자진행에복원하거나후보자원으로수정하지않았다.','DATA3의원작진행로드를확인한기록이며새사다리14후보의원테이블/GPU/화면실기검사대체가아니다.'],
 'writes':{'game':False,'card':False,'savestate':False,'process_memory':False,'emulator_input':False}}
assert sha(p)==report['card']['sha256']
q=O/'report.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(q),'slots':[{k:s[k]for k in('DATA','character','armor','ultimate_or_black')}for s in slots]}))
