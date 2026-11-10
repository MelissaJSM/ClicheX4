"""로컬 Edge headless로 갤러리 경로/토글/페이지/정수배 픽셀을 검사한다."""
from pathlib import Path
import base64
import hashlib
import json
import sys
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.export_zero_consistency import write
OUT=ROOT/'out/sprite_consistency_20261105'
EVIDENCE=ROOT/'work/sprite_consistency_20261105/zero/gallery_validation'


def baseline_digest():
    digest=hashlib.sha256();count=0
    for character in ('riko','shibuki','nana','rin'):
        for path in sorted((OUT/character).rglob('*.png')):
            digest.update(path.relative_to(OUT).as_posix().encode())
            digest.update(hashlib.sha256(path.read_bytes()).digest());count+=1
    return {'files':count,'tree_sha256':digest.hexdigest()}


def loaded(page):
    page.wait_for_function("[...document.querySelectorAll('#cards canvas,#idle,#compare,#before,#after')].filter(c=>c.dataset.path).every(c=>c.dataset.loaded==='true')")
    assert page.locator('#error').inner_text()==''
    checks=page.evaluate("""()=>[...document.querySelectorAll('#cards canvas,#idle,#compare,#before,#after')].filter(c=>c.dataset.path).map(c=>({
      path:c.dataset.path,width:c.width,height:c.height,scale:+c.dataset.scale,box:JSON.parse(c.dataset.viewport),
      cssWidth:c.getBoundingClientRect().width,cssHeight:c.getBoundingClientRect().height,
      borderX:parseFloat(getComputedStyle(c).borderLeftWidth)+parseFloat(getComputedStyle(c).borderRightWidth),
      borderY:parseFloat(getComputedStyle(c).borderTopWidth)+parseFloat(getComputedStyle(c).borderBottomWidth),
      smoothing:c.getContext('2d').imageSmoothingEnabled,transform:getComputedStyle(c).transform}))""")
    boxes={tuple(c['box']) for c in checks};assert len(boxes)==1
    for c in checks:
        x,y,r,b=c['box'];assert c['width']==(r-x)*c['scale'] and c['height']==(b-y)*c['scale']
        assert c['scale'] in (1,2,3,4) and not c['smoothing'] and c['transform']=='none'
        # Hidden <details> intentionally have a 0 client box. Visible canvases must not shrink.
        if c['cssWidth']:
            assert abs(c['cssWidth']-c['borderX']-c['width'])<.01,c
            assert abs(c['cssHeight']-c['borderY']-c['height'])<.01,c
    return len(checks)


def exact_pixels(page,selector):
    record=page.locator(selector).evaluate("""c=>{
      const data=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let s='';
      for(let i=0;i<data.length;i+=8192)s+=String.fromCharCode(...data.subarray(i,i+8192));
      return {path:c.dataset.path,width:c.width,height:c.height,scale:+c.dataset.scale,box:JSON.parse(c.dataset.viewport),data:btoa(s)}
    }""")
    x,y,r,b=record['box'];scale=record['scale']
    source=Image.open(OUT/record['path']).convert('RGBA').crop((x+160,y+160,r+160,b+160))
    canvas=Image.new('RGBA',source.size,'#242d3b');canvas.alpha_composite(source)
    expect=np.array(canvas)
    if page.locator('#flip').is_checked():expect=expect[:,::-1]
    expect=expect.repeat(scale,axis=0).repeat(scale,axis=1)
    actual=np.frombuffer(base64.b64decode(record.pop('data')),np.uint8).reshape(record['height'],record['width'],4)
    assert np.array_equal(expect,actual),(selector,record,np.count_nonzero(expect!=actual))
    return {'selector':selector,**record,'exact_nearest_pixels':True,'flipped':page.locator('#flip').is_checked()}


def main():
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    protection=baseline_digest();errors=[];request_failures=[];form_checks=[];pixel_checks=[];revision_checks=[];resource_checks=[]
    with sync_playwright() as playwright:
        # Readback only: scoped to this isolated temporary headless browser.
        # No normal Edge profile or system setting is changed.
        browser=playwright.chromium.launch(channel='msedge',headless=True,args=['--allow-file-access-from-files'])
        version=browser.version
        page=browser.new_page(viewport={'width':1600,'height':1100},device_scale_factor=1)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('console',lambda msg:errors.append(msg.text) if msg.type=='error' else None)
        page.on('requestfailed',lambda req:request_failures.append({'url':req.url,'failure':req.failure}))
        page.goto((OUT/'index.html').as_uri(),wait_until='load')
        loaded(page)
        assert page.locator('#showRevised').is_checked()
        assert not page.locator('#changedOnly').is_checked()
        characters=page.evaluate('DATA.map(c=>({id:c.id,forms:c.forms.map(f=>f.id)}))')
        assert {c['id'] for c in characters}=={'riko','rin','nana','shibuki'}
        # Every form: first page and actual last page, with the full group viewport.
        for character in characters:
            page.locator(f'#characters button[data-id="{character["id"]}"]').click()
            for form in character['forms']:
                page.select_option('#form',form);page.select_option('#group','')
                checked=loaded(page)
                expected=page.evaluate('subset.length');assert expected>0
                before=page.locator('#page').inner_text()
                last_index=max(0,(expected-1)//48)
                page.evaluate('page=Math.max(0,Math.ceil(subset.length/48)-1);render()')
                checked+=loaded(page)
                assert page.locator('#page').inner_text()==f'{last_index+1} / {last_index+1}'
                assert page.locator('#next').is_disabled()
                if last_index:
                    page.locator('#prev').click();loaded(page)
                    page.locator('#next').click();loaded(page)
                    assert page.locator('#page').inner_text()==f'{last_index+1} / {last_index+1}'
                form_checks.append({'character':character['id'],'form':form,'frames':expected,
                                    'pages':last_index+1,'loaded_canvas_checks':checked})
        # Automatically include final additional character mappings after a rebuild.
        revised_forms=page.evaluate('DATA.flatMap(c=>c.forms.map(f=>({character:c.id,form:f.id,count:c.frames.filter(q=>q.form===f.id&&q.revised_path).length}))).filter(f=>f.count)')
        page.locator('#changedOnly').check()
        for test in revised_forms:
            page.locator(f'#characters button[data-id="{test["character"]}"]').click()
            page.select_option('#form',test['form']);loaded(page)
            assert page.evaluate('subset.length')==test['count']
            assert page.locator('#cards .card').count()==min(48,test['count'])
            assert page.locator('#compare').get_attribute('data-path')==page.locator('#after').get_attribute('data-path')
            page.locator('#showRevised').uncheck();loaded(page)
            assert page.locator('#compare').get_attribute('data-path')==page.locator('#before').get_attribute('data-path')
            page.locator('#showRevised').check();loaded(page)
            revision_checks.append({**test,'toggle_and_comparison':True})
        for character in characters:
            page.locator(f'#characters button[data-id="{character["id"]}"]').click();loaded(page)
            resources=page.locator('#resources a').evaluate_all('(links)=>links.map(a=>({label:a.textContent,path:a.getAttribute("href")}))')
            for resource in resources:
                target=(OUT/resource['path']).resolve()
                assert target.is_relative_to(ROOT) and target.is_file()
            resource_checks.append({'character':character['id'],'links':resources,'all_local_targets_exist':True})
        # Riko changed-only: both color variants use the same 16 revised bitmaps.
        page.locator('#characters button[data-id="riko"]').click()
        page.select_option('#form','normal');page.locator('#changedOnly').check();loaded(page)
        assert page.locator('#cards .card').count()==16
        assert page.locator('#cards .changed').count()==16
        assert all('/revised/' in p for p in page.locator('#cards canvas').evaluate_all('(cs)=>cs.map(c=>"/"+c.dataset.path)'))
        page.locator('#cards .card button').nth(1).click();loaded(page)
        assert page.locator('#before').get_attribute('data-path')!=page.locator('#after').get_attribute('data-path')
        before_path=page.locator('#before').get_attribute('data-path');after_path=page.locator('#after').get_attribute('data-path')
        page.locator('#showRevised').uncheck();loaded(page)
        assert page.locator('#compare').get_attribute('data-path')==before_path
        assert page.locator('#after').get_attribute('data-path')==after_path
        page.locator('#showRevised').check();loaded(page)
        assert page.locator('#compare').get_attribute('data-path')==after_path
        # Pixel equality independently confirms whole-frame origin and integer scaling.
        page.locator('#guides').uncheck()
        for variant in ('normal','black'):
            page.select_option('#form',variant);loaded(page)
            assert page.locator('#cards .card').count()==16
            for scale in (1,2,3,4):
                page.select_option('#zoom',str(scale));loaded(page)
                for selector in ('#idle','#compare','#before','#after'):
                    pixel_checks.append(exact_pixels(page,selector))
            page.locator('#flip').check();loaded(page)
            pixel_checks.append(exact_pixels(page,'#after'))
            page.locator('#flip').uncheck();loaded(page)
        # Idle blink remains available and restores selected image when stopped.
        page.locator('#blink').click()
        page.wait_for_function("document.querySelector('#compare').dataset.path===document.querySelector('#idle').dataset.path")
        page.locator('#blink').click();loaded(page)
        assert page.locator('#compare').get_attribute('data-path')==page.locator('#after').get_attribute('data-path')
        # Empty filter is intentional for Rin; it must neither show stale frames nor error.
        page.locator('#characters button[data-id="rin"]').click();loaded(page)
        assert page.locator('#cards .card').count()==0
        assert page.locator('#cards .empty').count()==1
        assert page.locator('#revisionPanel').is_hidden()
        assert page.locator('#blink').is_disabled()
        page.locator('#changedOnly').uncheck();loaded(page)
        assert page.locator('#cards .card').count()>0
        # Final visual evidence: ordinary 3x mode and narrow viewport without canvas scaling.
        page.locator('#characters button[data-id="riko"]').click();page.select_option('#form','normal')
        page.locator('#changedOnly').check();page.select_option('#zoom','3');page.locator('#guides').check();loaded(page)
        page.locator('#cards .card button').nth(1).click();loaded(page)
        page.screenshot(path=str(EVIDENCE/'riko_revised_desktop.png'),full_page=True)
        page.set_viewport_size({'width':720,'height':1050});loaded(page)
        page.screenshot(path=str(EVIDENCE/'riko_revised_narrow.png'),full_page=True)
        page.set_viewport_size({'width':1600,'height':1100})
        page.select_option('#form','black');loaded(page)
        page.screenshot(path=str(EVIDENCE/'riko_black_revised.png'),full_page=True)
        assert not errors,errors
        assert not request_failures,request_failures
        browser.close()
    assert baseline_digest()==protection
    report={'passed':True,'browser':'Microsoft Edge headless','browser_version':version,
      'entry':'out/sprite_consistency_20261105/index.html','html_sha256':hashlib.sha256((OUT/'index.html').read_bytes()).hexdigest(),
      'headless_readback_argument':'--allow-file-access-from-files (isolated temporary browser only)',
      'characters':characters,'forms_checked':len(form_checks),'form_checks':form_checks,
      'revision_form_checks':revision_checks,'resource_link_checks':resource_checks,
      'revision_default_on':True,'revision_toggle_checked':True,'changed_only_filter_checked':True,
      'unchanged_character_empty_filter_checked':True,'idle_blink_checked':True,'previous_next_buttons_checked':True,
      'same_canvas_origin_and_integer_scale':True,'pixel_exact_checks':pixel_checks,
      'no_canvas_css_shrink':True,'narrow_view_scroll_instead_of_scale':True,
      'javascript_errors':errors,'failed_requests':request_failures,'baseline_pngs':protection,
      'baseline_pngs_unchanged':True,'game_or_emulator_modified':False,
      'screenshots':['riko_revised_desktop.png','riko_revised_narrow.png','riko_black_revised.png']}
    write(EVIDENCE/'verification.json',report)
    print(json.dumps({'passed':True,'forms':len(form_checks),'pixel_exact_checks':len(pixel_checks),'baseline_pngs':protection['files'],'evidence':str(EVIDENCE/'verification.json')}))


if __name__=='__main__':
    main()
