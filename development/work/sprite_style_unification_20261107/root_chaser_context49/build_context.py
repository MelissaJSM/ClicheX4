"""최신 네 캐릭터를 원체이서 좌표에 조립한 정적 비교. 실기 증거가 아님."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw
from probe_body import draw, b, r
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1]
sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.build_sprite_style_album import zero_palettes,zero_image
sha=lambda b:hashlib.sha256(b).hexdigest()
inputs={};arcs={}
for tag in ('br_v31','rn_v43'):
    p=W/f'staging_{tag}.json';raw=p.read_bytes();inputs[p.relative_to(ROOT).as_posix()]=sha(raw);plan=json.loads(raw)
    arcs[tag]={}
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        src=plan['resources'][name];p=ROOT/src['path'];raw=p.read_bytes();assert sha(raw)==src['after']
        inputs[p.relative_to(ROOT).as_posix()]=sha(raw);arcs[tag][name]=raw
rows=[];pages=[]
for character,tag,is_zero in [('shibuki','br_v31',False),('nana','rn_v43',False),('riko','br_v31',True),('rin','rn_v43',True)]:
    forms=('normal','black') if is_zero else ('base','fourth','ultimate_before','ultimate_after')
    sheet=Image.new('RGB',(1100,len(forms)*242),'#26313f');d=ImageDraw.Draw(sheet)
    if is_zero:
        arc=arcs[tag]['PL01_U.ARC'];pal=zero_palettes(arc)
    for row,form in enumerate(forms):
        mask=15 if form in ('fourth','ultimate_before') else 0
        if not is_zero:a=Archive(arcs[tag]['PL02_U.ARC' if form.startswith('ultimate') else 'PL00_U.ARC'])
        def sprite(ref,bank=0):
            if not is_zero:return a.composite(ref,mask)[0]
            return zero_image(arc,character,{'id':f'{form}:b{bank}_{ref:03}','form':form,'bank':bank,'ref':ref},pal)
        idle=sprite(147 if is_zero else 0)
        d.text((4,row*242+4),f'{character} {form}',fill='white')
        window=(112,112,212,212)
        q=idle.crop(window).resize((200,200),Image.Resampling.NEAREST);sheet.paste(q,(10,row*242+30),q)
        for col,(ref,bodyref) in enumerate(zip((14,22,30,38) if is_zero else (162,166,170,174),range(4)),1):
            p=sprite(ref,1 if is_zero else 0).crop((96,96,224,224))
            body=draw(bodyref,384,0,0x784a if is_zero else 0x7848)
            combo=Image.alpha_composite(body,p)
            file=O/f'{character}_{form}_{ref:03}_body{bodyref}.png';combo.save(file)
            q=combo.crop((16,16,116,116)).resize((200,200),Image.Resampling.NEAREST)
            sheet.paste(q,(col*220+10,row*242+30),q)
            d.text((col*220+4,row*242+4),f'{ref} + bike {bodyref}',fill='white')
            rows.append({'character':character,'form':form,'ref':ref,'body_frame':bodyref,'sprite_sha256':sha(p.tobytes()),'body_sha256':sha(body.tobytes()),'composite_path':file.relative_to(ROOT).as_posix(),'composite_sha256':sha(file.read_bytes()),'body_under_rider':True})
    p=O/f'{character}_current_context.png';sheet.save(p);pages.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())})
report={'scope':'최신 체이서4기본 자세×12폼 정적 원좌표 비교','inputs':inputs,'state_sha256':sha(b),'vehicle_object':'0x80173a30','parts_address':'0x801ba31c','texture_base_words':[384,0],'player_vehicle_world_same_in_saved_state':r[0x1418d0:0x1418d8]==r[0x173a38:0x173a40],'rows':rows,'pages':pages,'runtime_verified':False,'actually_viewed':False,'limits':['보존 상태는 일시정지 화면이다. 이 조립을 당시 화면과 픽셀 일치 검증하지 않았다.','차량 먼저/탑승자 다음의 정적 가림 순서. 실제 GPU 그리기 순서는 추가 확인 대상.','4기본 자세의 좌표 비교이며 시간축 전환의 호출 지연을 실행한 결과가 아니다.'],'game_assets_changed':False}
(O/'context_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'forms':12,'poses':len(rows),'pages':len(pages),'same_world_origin':report['player_vehicle_world_same_in_saved_state']}))
