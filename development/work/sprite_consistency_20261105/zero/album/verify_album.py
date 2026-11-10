"""One copied HTML, offline Edge, no sibling assets: verify gallery and simulated playback."""
from pathlib import Path
import base64
import hashlib
import io
import json
import shutil
import sys
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.export_zero_consistency import write
from src.psx_disc import file_hash

HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'out/sprite_consistency_20261105/ALL_SPRITES.html'


def loaded(page):
    page.wait_for_function("['idle','compare','before','after'].every(id=>{const c=document.getElementById(id);return !c.dataset.path||c.dataset.loaded==='true'})")
    assert not page.locator('#error').inner_text()
    checks=page.evaluate("""()=>[...document.querySelectorAll('canvas')].filter(c=>c.dataset.loaded==='true').map(c=>({
      id:c.id,width:c.width,height:c.height,scale:+c.dataset.scale,box:JSON.parse(c.dataset.viewport),
      css:c.getBoundingClientRect().width,smoothing:c.getContext('2d').imageSmoothingEnabled}))""")
    for c in checks:
        x,y,r,b=c['box'];assert c['width']==(r-x)*c['scale'] and c['height']==(b-y)*c['scale']
        assert c['scale'] in (1,2,3,4) and not c['smoothing']
        if c['css']:assert abs(c['css']-c['width']-2)<.01,c


def canvas_data(page,selector):
    d=page.locator(selector).evaluate("""c=>{const data=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let s='';for(let i=0;i<data.length;i+=8192)s+=String.fromCharCode(...data.subarray(i,i+8192));return {path:c.dataset.path,box:JSON.parse(c.dataset.viewport),scale:+c.dataset.scale,width:c.width,height:c.height,data:btoa(s)}}""")
    return d,np.frombuffer(base64.b64decode(d.pop('data')),np.uint8).reshape(d['height'],d['width'],4)


def exact_image(page,selector,expected=None):
    d,actual=canvas_data(page,selector)
    if expected is None:
        uri=page.evaluate('(key)=>ASSETS[key]',d['path'])
        expected=Image.open(io.BytesIO(base64.b64decode(uri.split(',',1)[1]))).convert('RGBA')
    x,y,r,b=d['box'];source=expected.crop((160+x,160+y,160+r,160+b));bg=Image.new('RGBA',source.size,'#242d3b');bg.alpha_composite(source)
    wanted=np.asarray(bg)
    if page.locator('#flip').is_checked():wanted=wanted[:,::-1]
    wanted=wanted.repeat(d['scale'],0).repeat(d['scale'],1)
    assert np.array_equal(wanted,actual),(selector,d,int(np.count_nonzero(wanted!=actual)))
    return {'canvas':selector,**d,'pixels_exact':True}


def main():
    assert SOURCE.is_file();source_hash=file_hash(SOURCE)
    isolated=HERE/'isolated';isolated.mkdir(exist_ok=True)
    target=isolated/'모음집.html';shutil.copyfile(SOURCE,target)
    assert [p.name for p in isolated.iterdir()]==['모음집.html']
    errors=[];external=[];forms=[];pixels=[];partial_checks=[];animations=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(viewport={'width':1600,'height':1100},device_scale_factor=1,offline=True)
        page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        page.on('request',lambda r:external.append(r.url) if not r.url.startswith(('file:','data:','blob:')) else None)
        page.goto(target.as_uri(),wait_until='load');loaded(page)
        assert page.evaluate('DATA.reduce((n,c)=>n+c.frames.length-c.partial.length,0)')==4510
        assert page.evaluate('DATA.reduce((n,c)=>n+c.revised_count,0)')==77
        assert page.evaluate('Object.values(ASSETS).every(p=>p.startsWith("data:image/png;base64,"))')
        assert page.evaluate('DATA.every(c=>c.frames.every(f=>f.form==="partial_fourth"||!!ASSETS[f.path]))')
        chars=page.evaluate('DATA.map(c=>({id:c.id,forms:c.forms.map(f=>f.id)}))')
        for char in chars:
            page.locator(f'#characters button[data-id="{char["id"]}"]').click()
            for form in char['forms']:
                page.select_option('#form',form);loaded(page)
                count=page.evaluate('subset.length');assert page.locator('#cards .card').count()==count
                assert page.locator('.paging').count()==0
                groups=page.locator('.album-group').count()
                assert groups==page.evaluate('new Set(subset.map(f=>f.group)).size')
                last=page.locator('#cards .card').last;last.scroll_into_view_if_needed()
                page.wait_for_function("document.querySelector('#cards .card:last-child canvas')!==null")
                last.locator('button').click();loaded(page)
                # All references are present in one scroll document, including the final one.
                assert page.evaluate('chosen.id')==last.get_attribute('data-id')
                forms.append({'character':char['id'],'form':form,'cards':count,'sections':groups,'last_frame_accessible':True})
        page.locator('#characters button[data-id="riko"]').click();page.select_option('#form','normal')
        page.locator('#changedOnly').check();loaded(page);assert page.locator('#cards .card').count()==16
        page.locator('#cards .card button').nth(1).click();loaded(page)
        latest=page.locator('#after').get_attribute('data-path');original=page.locator('#before').get_attribute('data-path');assert latest!=original
        page.locator('#showRevised').uncheck();loaded(page);assert page.locator('#compare').get_attribute('data-path')==original
        page.locator('#showRevised').check();loaded(page);assert page.locator('#compare').get_attribute('data-path')==latest
        page.locator('#guides').uncheck()
        for zoom in (1,2,3,4):
            page.select_option('#zoom',str(zoom));loaded(page)
            pixels.extend(exact_image(page,s) for s in ('#idle','#compare','#before','#after'))
        page.locator('#flip').check();loaded(page);pixels.append(exact_image(page,'#after'));page.locator('#flip').uncheck()
        page.locator('#changedOnly').uncheck()
        # Independent native renderer comparison for every mask/arm choice at idle,
        # plus the ladder exit and special-shoot poses that were changed in this revision.
        for char,mode,stem in (('shibuki','ver_buki_riko','shibuki_riko'),('nana','ver_rin_nana','rin_nana')):
            assets,_=read_disc(ROOT/f'out/{mode}/sprite_consistency_20261105_v1/{stem}.bin',('PL00_U.ARC',));arc=Archive(assets['PL00_U.ARC'])
            page.locator(f'#characters button[data-id="{char}"]').click();page.select_option('#form','partial_fourth')
            page.select_option('#group','idle');page.select_option('#zoom','2');loaded(page)
            for arm in (1,2):
                page.select_option('#armorArm',str(arm))
                for mask in range(16):
                    page.select_option('#armorMask',str(mask));loaded(page)
                    proof=exact_image(page,'#after',arc.composite(0,mask,arm)[0]);partial_checks.append({'character':char,'ref':0,'arm':arm,'mask':mask,**proof})
            for ref,group in ((183,'ladder'),(101,'shoot_special')):
                page.select_option('#group',group)
                page.locator(f'.card[data-id="partial_fourth_{ref:03}"] button').click();loaded(page)
                partial_checks.append({'character':char,'ref':ref,'arm':2,'mask':15,**exact_image(page,'#after',arc.composite(ref,15,2)[0])})
        # Native time-table simulation can advance, pause, and keep null references blank.
        for char,form,anim in (('riko','normal','5'),('shibuki','base','8'),('nana','ultimate_after','8'),('rin','black','5')):
            page.locator(f'#characters button[data-id="{char}"]').click();page.select_option('#form',form)
            page.select_option('#animationSelect',anim);page.locator('#loopAnimation').check();page.locator('#playAnimation').click()
            page.wait_for_function('animationStep>0')
            position=page.evaluate('animationStep');page.locator('#playAnimation').click()
            assert page.evaluate('animationTimer') is None
            animations.append({'character':char,'form':form,'animation':anim,'advanced_to_index':position,'paused':True})
        page.locator('#characters button[data-id="riko"]').click();page.select_option('#form','normal');page.select_option('#animationSelect','121')
        page.wait_for_function("document.getElementById('animationCanvas').dataset.loaded==='true'")
        assert page.locator('#animationCanvas').get_attribute('data-path')==page.evaluate('EMPTY')
        assert '별도' in page.locator('#animationState').inner_text()
        # Representative actual browser views; the browser remains headless.
        page.select_option('#animationSelect','5');page.select_option('#group','wall');page.select_option('#zoom','3');page.locator('#guides').check();loaded(page)
        page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(HERE/'album_riko.png'))
        page.locator('#characters button[data-id="nana"]').click();page.select_option('#form','partial_fourth');page.select_option('#group','idle');page.select_option('#armorMask','8');loaded(page)
        page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(HERE/'album_nana_partial.png'))
        page.set_viewport_size({'width':760,'height':1000});loaded(page);page.screenshot(path=str(HERE/'album_narrow.png'))
        assert not external,external
        assert not errors,errors
        version=browser.version;browser.close()
    assert file_hash(SOURCE)==source_hash and file_hash(target)==source_hash
    report={'passed':True,'html_sha256':source_hash,'isolated_copy':target.relative_to(ROOT).as_posix(),
      'only_file_in_folder':True,'offline_browser':True,'browser':'Microsoft Edge headless','browser_version':version,
      'main_references':4510,'revised_references':77,'forms':forms,'forms_checked':len(forms),
      'no_page_splitting':True,'native_origin':[160,160],'pixel_checks':pixels,
      'partial_composite_checks':partial_checks,'playback_checks':animations,
      'null_reference_not_replaced_by_fake_body':True,'external_requests':external,'javascript_errors':errors,
      'game_modified':False,'runtime_gameplay_verified':False}
    write(HERE/'browser_verification.json',report)
    print(json.dumps({'passed':True,'forms':len(forms),'pixels':len(pixels),'partial_cases':len(partial_checks),'animations':len(animations),'sha256':source_hash}))


if __name__=='__main__':main()
