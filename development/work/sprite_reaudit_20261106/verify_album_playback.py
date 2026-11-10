"""Headless current album timing and current-native-pixel checks; no game input."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import importlib.util,json,math,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_sprite_playback import parse_sequence,TABLES,read_disc,digest
from scripts.export_x_consistency import Archive
from playwright.sync_api import sync_playwright
spec=importlib.util.spec_from_file_location('album_helper',ROOT/'work/sprite_consistency_20261105/zero/album/verify_album.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
HERE=Path(__file__).parent;SOURCE=ROOT/'out/sprite_reaudit_20261106/ALL_SPRITES_CURRENT.html'

def main():
 source_hash=digest(SOURCE);source=SOURCE.read_text('utf8');dec=json.JSONDecoder();data=dec.raw_decode(source[source.index('const DATA=')+11:])[0];play=dec.raw_decode(source[source.index('PLAYBACK=')+9:])[0]
 assert sum(len(c['frames'])-len(c.get('partial',[]))for c in data)==4510
 assert sum(c['revised_count']for c in data)==120
 bychar={c['id']:c for c in data};assets={};sources={};native_tables=[]
 for mode,p in play['sources'].items():
  path=ROOT/p['bin'];assert digest(path)==p['bin_sha256'];sources[mode]={'bin':p['bin'],'sha256':p['bin_sha256']};assets[mode]=read_disc(path,('SLUS_005.61','PL02_U.ARC'))
 for char,c in play['characters'].items():
  mode='ver_buki_riko'if char in('riko','shibuki')else'ver_rin_nana';family='zero'if char in('riko','rin')else'x'
  for form,v in c['forms'].items():
   if form.startswith('capsule'):continue
   for a in v['animations']:
    native=parse_sequence(assets[mode]['SLUS_005.61'],TABLES[family],a['id'])
    assert [(s['position'],s['duration_calls'],s['event'])for s in a['steps']]==[(s['position'],s['duration_calls'],s['event'])for s in native['steps']],(char,form,a['id'])
    assert a['loop_to_position']==native['loop_to_position']
    native_tables.append([char,form,a['id']])
 errors=[];external=[];natural=[];deterministic=[];pixel_checks=[];seen={};forms_checked=[]
 archives={'shibuki':Archive(assets['ver_buki_riko']['PL02_U.ARC']),'nana':Archive(assets['ver_rin_nana']['PL02_U.ARC'])}
 with sync_playwright()as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True)
  context=browser.new_context(viewport={'width':1600,'height':1100},device_scale_factor=1,offline=True);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text)if m.type=='error'else None);page.on('request',lambda r:external.append(r.url)if not r.url.startswith(('file:','data:','blob:'))else None)
  page.goto(SOURCE.as_uri(),wait_until='load');helper.loaded(page);page.locator('#guides').uncheck();page.select_option('#zoom','2');helper.loaded(page)
  assert page.evaluate('DATA.reduce((n,c)=>n+c.revised_count,0)')==120
  assert page.evaluate('Object.values(ASSETS).every(x=>x.startsWith("data:image/png;base64,"))')
  for char in data:
   page.locator(f'#characters button[data-id="{char["id"]}"]').dispatch_event('click')
   for form in char['forms']:
    page.select_option('#form',form['id']);helper.loaded(page);assert page.locator('#cards .card').count()==page.evaluate('subset.length');forms_checked.append([char['id'],form['id'],page.evaluate('subset.length')])
  page.evaluate("""()=>{window.__steps=[];window.__oldShow=showAnimationStep;showAnimationStep=function(){__oldShow();if(animationCurrent){const s=animationCurrent.steps[animationStep];__steps.push({index:animationStep,position:s.position,frame_id:s.frame_id,duration_calls:s.duration_calls,event:s.event,time:Date.now(),path:document.getElementById('animationCanvas').dataset.path})}}}""")
  def choose(char,form,aid):
   page.locator(f'#characters button[data-id="{char}"]').dispatch_event('click');page.select_option('#form',form);page.select_option('#animationSelect',str(aid));helper.loaded(page)
   page.evaluate("""async()=>{const keys=animationCurrent.steps.map(s=>s.frame_id?char.frames.find(f=>f.id===s.frame_id):null).map(f=>f?selectedPath(f):EMPTY);await Promise.all(keys.map(k=>ready(pic(k))))}""")
   page.wait_for_function("document.getElementById('animationCanvas').dataset.loaded==='true'")
  for char,form,aid in [('riko','normal',8),('rin','black',8),('shibuki','ultimate_before',8),('nana','ultimate_after',8)]:
   choose(char,form,aid);page.locator('#loopAnimation').check();page.evaluate('window.__steps=[]');page.locator('#playAnimation').dispatch_event('click');page.wait_for_function('__steps.length>=4');page.locator('#playAnimation').dispatch_event('click');assert page.evaluate('animationTimer')is None
   paused=page.evaluate('({index:animationStep,count:__steps.length,path:document.getElementById("animationCanvas").dataset.path})');page.wait_for_timeout(180);assert page.evaluate('({index:animationStep,count:__steps.length,path:document.getElementById("animationCanvas").dataset.path})')==paused
   page.wait_for_function("document.getElementById('animationCanvas').dataset.loaded==='true'");px=helper.exact_image(page,'#animationCanvas');trace=page.evaluate('__steps');assert [s['index']for s in trace[:4]]==list(range(4));natural.append({'character':char,'form':form,'animation':aid,'observed_steps':trace,'pause_stable_ms':180,'paused_canvas':px})
  # Virtual time executes the actual page timers, without accelerating or
  # changing their duration arguments. Every expected image is preloaded.
  start=datetime(2026,11,6,tzinfo=timezone.utc);page.clock.install(time=start);page.clock.pause_at(start+timedelta(seconds=1))
  page.evaluate("""()=>{window.__nativeSetTimeout=window.setTimeout;window.__lastSchedule=null;window.setTimeout=function(fn,delay,...args){if(String(fn).includes('animationStep++'))window.__lastSchedule={time:Date.now(),delay:delay};return __nativeSetTimeout(fn,delay,...args)}}""")
  def step_check(char,form,expected,changed):
   status=page.evaluate('({index:animationStep,step:animationCurrent.steps[animationStep],path:document.getElementById("animationCanvas").dataset.path})')
   assert status['index']==expected
   frame=next((f for f in bychar[char]['frames']if f['id']==status['step']['frame_id']),None)
   if frame is None:assert status['path']==page.evaluate('EMPTY')
   else:assert status['path']==frame.get('revised_path',frame['path'])
   page.wait_for_function("document.getElementById('animationCanvas').dataset.loaded==='true'")
   key=(char,form,status['step']['frame_id'])
   if frame and frame.get('ref')in changed and key not in seen:
    mask=15 if form=='ultimate_before'else 0;im=archives[char].composite(frame['ref'],mask,2)[0];proof=helper.exact_image(page,'#animationCanvas',im);proof.update(character=char,form=form,ref=frame['ref'],frame_id=frame['id'],revised_path_used=status['path']==frame.get('revised_path'));pixel_checks.append(proof);seen[key]=True
   return status
  for char,wanted in [('shibuki',set(range(11,17))|set(range(33,85))),('nana',{95,96})]:
   for form in('ultimate_before','ultimate_after'):
    animations=play['characters'][char]['forms'][form]['animations'];missing=wanted.copy();selected=[]
    while missing:
     ranked=[]
     for a in animations:
      refs={int(s['frame_id'].rsplit('_',1)[1])for s in a['steps']if s['frame_id']};ranked.append((len(missing&refs),-sum(s['duration_calls']for s in a['steps']),a,refs))
     count,_,a,refs=max(ranked,key=lambda z:z[:2]);assert count;selected.append(a);missing-=refs
    for a in selected:
     choose(char,form,a['id']);page.locator('#loopAnimation').check();page.evaluate('window.__steps=[]');page.locator('#playAnimation').dispatch_event('click');trace=[]
     for i,s in enumerate(a['steps']):
      status=step_check(char,form,i,wanted);schedule=page.evaluate('__lastSchedule');expected_delay=max(1,s['duration_calls'])*1000/60;assert abs(schedule['delay']-expected_delay)<1e-7
      n=page.evaluate('__steps.length');elapsed=page.evaluate('Date.now()')-schedule['time'];remaining=max(0,math.ceil(expected_delay-elapsed))
      if remaining>2:page.clock.run_for(remaining-2);assert page.evaluate('__steps.length')==n,(char,form,a['id'],i,schedule,elapsed,remaining,page.evaluate('({now:Date.now(),tail:__steps.slice(-3),last:__lastSchedule})'))
      page.clock.run_for(2)
      if page.evaluate('__steps.length')==n:page.clock.run_for(1) # sub-ms virtual-clock rounding at large epoch
      assert page.evaluate('__steps.length')==n+1,(char,form,a['id'],i,schedule,elapsed,remaining,page.evaluate('({now:Date.now(),tail:__steps.slice(-3),last:__lastSchedule})'))
      item=page.evaluate('__steps[__steps.length-1]');actual_delay=item['time']-schedule['time'];assert abs(actual_delay-expected_delay)<=1.01
      trace.append({'index':i,'position':s['position'],'frame_id':s['frame_id'],'duration_calls':s['duration_calls'],'scheduled_delay_ms':schedule['delay'],'observed_timer_delay_ms':actual_delay,'expected_path':status['path']})
     loop=next(i for i,s in enumerate(a['steps'])if s['position']==a['loop_to_position']);step_check(char,form,loop,wanted);page.locator('#playAnimation').dispatch_event('click');assert page.evaluate('animationTimer')is None
     paused=page.evaluate('({index:animationStep,count:__steps.length})');page.clock.run_for(500);assert page.evaluate('({index:animationStep,count:__steps.length})')==paused
     deterministic.append({'character':char,'form':form,'animation':a['id'],'steps':trace,'loop_to_index':loop,'pause_stable_virtual_ms':500})
    assert {k[2]for k in seen if k[:2]==(char,form)}=={f'{form}_{n:03}'for n in wanted}
  choose('riko','normal',121);assert page.locator('#animationCanvas').get_attribute('data-path')==page.evaluate('EMPTY');null_proof=helper.exact_image(page,'#animationCanvas');assert '별도'in page.locator('#animationState').inner_text()
  assert not errors and not external;version=browser.version;browser.close()
 assert digest(SOURCE)==source_hash
 report={'passed':True,'html':SOURCE.relative_to(ROOT).as_posix(),'html_sha256':source_hash,'html_unmodified':True,'browser':'Microsoft Edge headless','browser_version':version,'offline':True,'forms':forms_checked,'forms_checked':len(forms_checked),'revised_refs':120,'current_sources':sources,'native_table_sequences_checked':len(native_tables),'natural_play_pause_checks':natural,'deterministic_timer_sequences':deterministic,'modified_canvas_pixel_checks':pixel_checks,'modified_refs_checked':len(pixel_checks),'null_reference':null_proof,'no_gui_focus_or_input':True,'game_modified':False,'runtime_gameplay_verified':False,'timing_scope':'Native table duration call counts; UI60calls/sec assumption. Actual browser setTimeout executed with Playwright virtual clock, native dispatcher/event logic not simulated.','javascript_errors':errors,'external_requests':external}
 (HERE/'album_playback_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'forms':len(forms_checked),'natural':len(natural),'timed_sequences':len(deterministic),'modified_pixels':len(pixel_checks),'native_tables':len(native_tables),'sha256':source_hash}),flush=True)
if __name__=='__main__':main()
