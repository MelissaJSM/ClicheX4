"""단독 HTML의 실제 브라우저 타이머를 진행하고 미술 검토용 연속 스텝을 저장한다."""
import base64,hashlib,io,json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent/'art_review'
HTML=ROOT/'out/sprite_consistency_20261105/ALL_SPRITES.html'
FONT=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
GROUPS={'idle':[5],'run':[7,8,9],'air':[10,11,12],'dash':[16,17],
        'arrival':[2],'victory_return':[39,40]}
FORMS={'riko':['normal','black'],'rin':['normal','black'],
       'shibuki':['base','fourth','ultimate_before','ultimate_after'],
       'nana':['base','fourth','ultimate_before','ultimate_after']}
BOX=(-38,-42,42,30)

def crop_canvas(page,selector):
    page.wait_for_function('(s)=>document.querySelector(s).dataset.loaded==="true"',arg=selector)
    data=page.locator(selector).evaluate('c=>({png:c.toDataURL(),box:JSON.parse(c.dataset.viewport),scale:+c.dataset.scale,path:c.dataset.path})')
    im=Image.open(io.BytesIO(base64.b64decode(data['png'].split(',',1)[1]))).convert('RGB')
    x,y,_,_=data['box'];scale=data['scale']
    result=im.crop(tuple(int((value-(x if i%2==0 else y))*scale) for i,value in enumerate(BOX)))
    return result,data['path']

def main():
    HERE.mkdir(parents=True,exist_ok=True)
    original=hashlib.sha256(HTML.read_bytes()).hexdigest();proof=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(viewport={'width':1600,'height':1000},device_scale_factor=1,offline=True)
        page=context.new_page();page.goto(HTML.as_uri(),wait_until='load')
        page.clock.install();page.clock.pause_at(1000000000000)
        page.select_option('#zoom','2');page.locator('#guides').uncheck()
        for char,forms in FORMS.items():
            page.locator(f'#characters button[data-id="{char}"]').click()
            for form in forms:
                page.select_option('#form',form)
                idle,_=crop_canvas(page,'#idle');groups=[];sequence_proofs=[]
                for group,aids in GROUPS.items():
                    cells=[]
                    for aid in aids:
                        page.select_option('#animationSelect',str(aid));page.locator('#loopAnimation').check()
                        animation=page.evaluate('animationCurrent')
                        page.locator('#playAnimation').click()
                        previous=None;observed=[]
                        for index,step in enumerate(animation['steps']):
                            actual=page.evaluate('({index:animationStep,frame:animationCurrent.steps[animationStep].frame_id})')
                            assert actual['index']==index,(char,form,aid,index,actual)
                            im,path=crop_canvas(page,'#animationCanvas')
                            observed.append({'position':step['position'],'frame_id':step['frame_id'],'path':path,'calls':step['duration_calls']})
                            if step['frame_id']!=previous:
                                cells.append((im,f'A{aid} {step["frame_id"].split(":")[-1]}'))
                            previous=step['frame_id']
                            # Browser's existing timeout callback, not a replacement frame scheduler.
                            page.clock.run_for(math.ceil(step['duration_calls']*1000/60))
                        page.locator('#playAnimation').click()
                        sequence_proofs.append({'id':aid,'steps':observed,'actual_browser_timeout_advanced':True})
                    groups.append((group,cells))
                # Every group has a new idle reference at the same origin, with ordered action cells.
                width=8*164;heights=[math.ceil((1+len(cells))/8)*166+24 for _,cells in groups]
                sheet=Image.new('RGB',(width,sum(heights)+28),'#161c27');draw=ImageDraw.Draw(sheet)
                draw.text((6,6),char+' / '+form+' | timed browser playback samples; fixed origin; 2x',font=FONT,fill='white')
                y=28
                for (group,cells),height in zip(groups,heights):
                    draw.text((6,y+3),group+' | idle reference, then actual ordered steps',font=FONT,fill='#ffe8a0')
                    for i,(im,label) in enumerate([(idle,'IDLE REF')]+cells):
                        x=i%8*164;yy=y+24+(i//8)*166
                        sheet.paste(im,(x,yy));draw.text((x+3,yy+145),label,font=FONT,fill='white')
                    y+=height
                target=HERE/f'{char}_{form}.png';sheet.save(target)
                proof.append({'character':char,'form':form,'sheet':target.relative_to(ROOT).as_posix(),
                              'sequences':sequence_proofs,'visual_review_completed':False})
                print(char,form,'captured',flush=True)
        browser.close()
    assert hashlib.sha256(HTML.read_bytes()).hexdigest()==original
    (HERE/'capture.json').write_text(json.dumps({'html_sha256':original,'scope':'offline browser timer playback captures; no gameplay',
          'camera':'fixed origin (160,160), body review crop [-38,-42,42,30], 2x nearest',
          'records':proof,'game_files_written':False},ensure_ascii=False,indent=2)+'\n','utf8')

if __name__=='__main__':main()
