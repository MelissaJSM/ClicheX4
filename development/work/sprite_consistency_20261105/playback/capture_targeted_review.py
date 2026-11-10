"""최근 수정한 벽·특수기·부분파츠의 HTML 시뮬레이션 연속 미술 증거."""
import hashlib,json,math
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
from capture_art_review import ROOT,HTML,FONT,crop_canvas
HERE=Path(__file__).resolve().parent/'art_review/targeted'

def sequence(page,aid):
    page.select_option('#animationSelect',str(aid));page.locator('#loopAnimation').check()
    anim=page.evaluate('animationCurrent');page.locator('#playAnimation').click()
    cells=[];observed=[];seen=set()
    for index,step in enumerate(anim['steps']):
        assert page.evaluate('animationStep')==index
        im,path=crop_canvas(page,'#animationCanvas')
        observed.append({'position':step['position'],'frame_id':step['frame_id'],'calls':step['duration_calls'],'path':path})
        if step['frame_id'] not in seen:
            cells.append((im,f'A{aid} {step["frame_id"].split(":")[-1]}'));seen.add(step['frame_id'])
        page.clock.run_for(math.ceil(step['duration_calls']*1000/60))
    page.locator('#playAnimation').click()
    return cells,observed

def save_sheet(title,rows,path):
    heights=[math.ceil(len(cells)/8)*166+24 for label,cells in rows]
    sheet=Image.new('RGB',(8*164,sum(heights)+28),'#161c27');d=ImageDraw.Draw(sheet)
    d.text((6,6),title,font=FONT,fill='white');y=28
    for (label,cells),height in zip(rows,heights):
        d.text((6,y+4),label,font=FONT,fill='#ffe8a0')
        for i,(im,text) in enumerate(cells):
            x=i%8*164;yy=y+24+i//8*166;sheet.paste(im,(x,yy));d.text((x+3,yy+145),text,font=FONT,fill='white')
        y+=height
    sheet.save(path)

def main():
    HERE.mkdir(parents=True,exist_ok=True);proof=[];hash0=hashlib.sha256(HTML.read_bytes()).hexdigest()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(viewport={'width':1600,'height':1000},device_scale_factor=1,offline=True)
        page=context.new_page();page.goto(HTML.as_uri(),wait_until='load');page.clock.install();page.clock.pause_at(1000000000000)
        page.select_option('#zoom','2');page.locator('#guides').uncheck()
        for char,forms,aids in [('riko',['normal','black'],[13,15,14,94]),('shibuki',['base','fourth','fourth_arm1'],[99,100,101,102,103])]:
            page.locator(f'#characters button[data-id="{char}"]').click()
            for form in forms:
                page.select_option('#form',form);idle,_=crop_canvas(page,'#idle');rows=[];records=[]
                for aid in aids:
                    cells,observed=sequence(page,aid);rows.append((f'{char}/{form}: native animation {aid}',[(idle,'IDLE REF')]+cells))
                    records.append({'id':aid,'steps':observed})
                target=HERE/f'{char}_{form}.png';save_sheet(f'{char}/{form} targeted actual HTML timed sequence',rows,target)
                proof.append({'character':char,'form':form,'sheet':target.relative_to(ROOT).as_posix(),'animations':records})
        page.locator('#characters button[data-id="nana"]').click();page.select_option('#form','partial_fourth')
        batches=[]
        for arm in (1,2):
            page.select_option('#armorArm',str(arm));batch=[]
            for mask in range(16):
                page.select_option('#armorMask',str(mask));idle,_=crop_canvas(page,'#idle');cells=[(idle,'IDLE REF')];records=[];seen=set()
                for aid in (5,88,91):
                    new,observed=sequence(page,aid)
                    for im,label in new:
                        ref=label.rsplit('_',1)[1]
                        if ref not in seen:cells.append((im,label));seen.add(ref)
                    records.append({'id':aid,'steps':observed})
                batch.append((f'Nana partial fourth / arm{arm} mask{mask:02d}',cells))
                proof.append({'character':'nana','form':'partial_fourth','arm':arm,'mask':mask,'animations':records})
                if len(batch)==4:
                    target=HERE/f'nana_arm{arm}_masks{mask-3:02d}_{mask:02d}.png'
                    save_sheet('Nana changed head/leg ownership: idle + standing shot',batch,target)
                    for rec in proof[-4:]:rec['sheet']=target.relative_to(ROOT).as_posix()
                    batch=[]
                print('nana',arm,mask,'captured',flush=True)
        browser.close()
    assert hashlib.sha256(HTML.read_bytes()).hexdigest()==hash0
    (HERE/'capture.json').write_text(json.dumps({'html_sha256':hash0,'records':proof,'actual_browser_timer':True,'gameplay':False},ensure_ascii=False,indent=2)+'\n','utf8')
    print('done',len(proof))

if __name__=='__main__':main()
