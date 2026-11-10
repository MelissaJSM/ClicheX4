"""Collect final air/landing evidence and preserve the prior project pointers."""
from fit_air import *
from datetime import datetime,timezone
import shutil
from scripts.project import digest
from src.epsxe_state import match_sprite
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T031656659594Z'
M=ROOT/'work/ver_buki_riko/production_master/20261024T031722651640Z'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def rel(p):return p.relative_to(ROOT).as_posix()
manifest=read(B/'manifest.json');assert digest(B/'riko_motion.bin')==manifest['modified_bin']['sha256']
out=B/('air_validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
def save(name,value):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for name in ['current_build.json','art_selection.json','master_sheet.json']:
 shutil.copy2(ROOT/'projects/ver_buki_riko'/name,out/('previous_'+name))
shutil.copy2(ROOT/'docs/STATUS.md',out/'previous_STATUS.md')
runs={'right':['20261024T032355947622Z','20261024T032521136071Z'],'left':['20261024T032621109303Z','20261024T032750445712Z']}
directions={};all_render=set();all_data=set();controls=[];examples=[]
for direction,folders in runs.items():
 strict=set();pipeline=set();loaded=set();reports=[]
 for folder in folders:
  p=ROOT/'work/ver_buki_riko/air_slash_runtime'/folder;d=read(p/'verification.local.json');assert d['modified_bin_sha256']==manifest['modified_bin']['sha256']
  strict.update(d['verified_frames']);pipeline.update(d['pipeline_verified_frames']);loaded.update(int(n) for n,v in d['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in v['samples']))
  reports.append({'report':rel(p/'verification.local.json'),'strict':d['verified_frames'],'pipeline':d['pipeline_verified_frames']})
  for n in [229,246]:
   if not d['frames'][str(n)]['matches'] or any(c['direction']==direction and c['frame']==n for c in controls):continue
   m=d['frames'][str(n)]['matches'][0];image_path=p/f'actual_{n:03d}_{m["page_y"]}.png';screen=Image.open(image_path);sprite=Image.open(p/f'expected_{n:03d}.png').convert('RGBA');assert match_sprite(screen,sprite)
   a=np.array(sprite);ys,xs=np.nonzero(a[:,:,3]);y,x=int(ys[len(ys)//2]),int(xs[len(xs)//2]);a[y,x,0]^=1
   assert not match_sprite(screen,Image.fromarray(a));controls.append({'direction':direction,'frame':n,'screen':rel(image_path),'one_pixel_change_rejected':True,'flip_x':m['flip_x']})
   examples.append((direction,n,screen,sprite,m))
 assert set(body)<=loaded
 directions[direction]={'runs':reports,'strict_same_sample':sorted(strict),'separate_sample_pipeline':sorted(pipeline-strict),'body_loaded':sorted(loaded&set(body)),'body_full_render_verified':sorted((strict|pipeline)&set(body))}
 all_render.update(strict|pipeline);all_data.update(loaded)
summary={'build':rel(B),'bin_sha256':manifest['modified_bin']['sha256'],'directions':directions,
 'current_render_verified_frames':sorted(all_render),'new_body_frames':body,'new_body_full_render_verified':sorted(all_render&set(body)),
 'new_body_full_render_unverified':sorted(set(body)-all_render),'all_body_loaded_both_directions':True,
 'previous_unverified32_now_exact_both_directions':32 in all_render,'agent_loaded_save_state':False,'agent_created_save_state':False,
 'process_memory_written':False,'zero_selection_observed':True,'attract_demo_excluded_from_runtime_results':True,
 'input_records':['work/ver_buki_riko/input_playback/'+n for n in ['20261024T032356922246Z','20261024T032522113227Z','20261024T032622088562Z','20261024T032751420629Z']],
 'limits':['11 new refs have data proof but no complete visible-pixel match; saber overlays and short frame duration remain','Old ground11 and old41..44 plus left wall limits remain','104 Shippuuga requires unlock, mixed recovery untested','New air/landing art awaits user review']}
save('runtime_summary.json',summary)
save('final_checks.json',{'build':rel(B),'unit_tests':{'count':60,'passed':True,'command':'python -m unittest discover -s tests -q','source':'Observed tool run before build'},'real_screen_negative_controls':controls,
 'build_verification':rel(B/'verification_20261024T031745637981Z.local.json'),'guards':rel(D/'guard_checks.json'),
 'master_split':'work/ver_buki_riko/master_split/20261024T031750844443Z/validation.local.json','master_size':Image.open(M/'riko_master_indexed.png').size,
 'body_reference_count':114,'preserved_effect_count':50,'changed_sector_count':47})
board=Image.new('RGB',(4*320,352),(30,34,42));draw=ImageDraw.Draw(board)
for i,(direction,n,screen,sprite,m) in enumerate(examples):
 crop=screen.crop((m['x']-6,m['y']-6,m['x']+sprite.width+6,m['y']+sprite.height+6));crop=crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST)
 board.paste(crop,(i*320+8,28));draw.text((i*320+8,8),f'{direction} / frame {n}',fill='white')
board.save(out/'actual_air_landing.png')
save('artifact_sources.json',{'tool':'builtin image_gen, three calls; no CLI fallback','selected':['generated_air_v2.png','generated_landing_v3.png'],'rejected':'generated_v1.png: airborne/ground row assignment did not follow18-pose request','directory':rel(D),'prompts':['generation_prompt_v1.txt','generation_prompt_v2.txt','landing_prompt.txt'],'native_reused_pose':{'246':'approved ground134 guard'}})
print(json.dumps({'output':rel(out),'new_body_rendered':len(all_render&set(body)),'new_full_render_unverified':summary['new_body_full_render_unverified'],'current_verified':sorted(all_render)}))
