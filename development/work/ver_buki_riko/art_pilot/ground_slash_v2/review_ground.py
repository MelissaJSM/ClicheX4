"""Collect existing evidence and run two real-screen negative controls. No game input."""
from pathlib import Path
from datetime import datetime, timezone
import json, shutil, sys
from PIL import Image, ImageDraw
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.build_riko_idle import GROUND_SLASH_BODY_FRAMES
from src.epsxe_state import match_sprite

B=ROOT/'out/ver_buki_riko/riko_motion_20261024T024352897084Z'
B1=ROOT/'out/ver_buki_riko/riko_motion_20261024T023541350651Z'
D=Path(__file__).parent
M=ROOT/'work/ver_buki_riko/production_master/20261024T024429065616Z'
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out=B/('ground_validation_'+stamp);out.mkdir()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rel(p):return p.relative_to(ROOT).as_posix()
def save(name,obj):(out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=read(B/'manifest.json');assert digest(B/'riko_motion.bin')==manifest['modified_bin']['sha256']
for name in ('current_build.json','art_selection.json','master_sheet.json'):
    shutil.copy2(ROOT/'projects/ver_buki_riko'/name,out/('previous_'+name))
shutil.copy2(ROOT/'docs/STATUS.md',out/'previous_STATUS.md')
records={};controls=[];union=set();loaded=set()
for direction,folder in [('right','20261024T024552585869Z'),('left','20261024T024701002791Z')]:
    p=ROOT/'work/ver_buki_riko/ground_slash_runtime'/folder
    d=read(p/'verification.local.json');assert d['modified_bin_sha256']==manifest['modified_bin']['sha256']
    strict=set(d['verified_frames']);pipeline=set(d['pipeline_verified_frames'])
    data={int(n) for n,v in d['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in v['samples'])}
    union|=strict|pipeline;loaded|=data
    flips=sorted({m['flip_x'] for v in d['frames'].values() for m in v['matches']})
    records[direction]={'report':rel(p/'verification.local.json'),'strict_same_sample':sorted(strict),'separate_sample_pipeline':sorted(pipeline),'ram_vram_palette_equal':sorted(data),'observed_flip_x':flips}
    m=d['frames']['127']['matches'][0];screen=Image.open(p/f"actual_127_{m['page_y']}.png");sprite=Image.open(p/'expected_127.png').convert('RGBA')
    assert match_sprite(screen,sprite)
    arr=np.array(sprite);ys,xs=np.nonzero(arr[:,:,3]);y,x=int(ys[len(ys)//2]),int(xs[len(xs)//2]);arr[y,x,0]^=1
    rejected=not match_sprite(screen,Image.fromarray(arr));assert rejected
    controls.append({'direction':direction,'frame':127,'screen':rel(p/f"actual_127_{m['page_y']}.png"),'expected_one_rgb_channel_changed_at':[x,y],'rejected':rejected})
changed=[n for n in sorted(GROUND_SLASH_BODY_FRAMES) if (B/f'frame_{n:03d}.png').read_bytes()!=(B1/f'frame_{n:03d}.png').read_bytes()]
assert changed==[111,121,123,125,127]
assert loaded==GROUND_SLASH_BODY_FRAMES|{147}
assert len(union & GROUND_SLASH_BODY_FRAMES)==29
summary={'build':rel(B),'bin_sha256':manifest['modified_bin']['sha256'],'baseline':'work/ver_buki_riko/live_poc/20261024T024527849273Z/verification.local.json','directions':records,'ground_body_refs':sorted(GROUND_SLASH_BODY_FRAMES),'new_body_render_verified':sorted(union & GROUND_SLASH_BODY_FRAMES),'new_body_full_render_unverified':sorted(GROUND_SLASH_BODY_FRAMES-union),'all_body_and_idle_loaded':sorted(loaded),'strict_and_pipeline_are_distinct':True,'old_body_render_unverified_including_inherited':[32,41,42,43,44],'boot_navigation_fully_observed':False,'agent_loaded_save_state':False,'agent_created_save_state':False,'process_memory_written':False,'initial_v1_gameplay_user_assisted':True,'v2_input_plans':['work/ver_buki_riko/input_playback/20261024T024553570843Z','work/ver_buki_riko/input_playback/20261024T024702004901Z'],'limitations':['11 body refs lack complete visible-pixel proof; effects and short frame duration interfere','Animation104 shares recovery131..134; mixed original/custom sequence untested','Left wall and old32/41..44 render limits remain','Custom sword blade, Black Zero and special palettes unverified']}
save('runtime_summary.json',summary)
save('final_checks.json',{'build':rel(B),'bin_sha256':manifest['modified_bin']['sha256'],'last_observed_unit_tests':{'command':'python -m unittest discover -s tests -q','count':59,'passed':True,'source':'Prior tool execution in this task; not rerun by this collector'},'real_screen_negative_controls':controls,'v1_to_v2_changed_body_refs':changed,'build_verification':rel(B/'verification_20261024T024443585884Z.local.json'),'guards':rel(D/'guard_checks.json'),'art_checks':rel(D/'art_checks.json'),'master_split':'work/ver_buki_riko/master_split/20261024T024441552560Z/validation.local.json','master_image_size':Image.open(M/'riko_master_indexed.png').size,'preserved_effect_refs':manifest['preserved_ground_effect_frames'],'body_reference_count':96})
# Actual framebuffer crops, never paint over game pixels; nearest magnification.
sheet=Image.new('RGB',(3*384,360),(25,29,35));draw=ImageDraw.Draw(sheet)
for col,(label,folder,filename) in enumerate([
    ('V1 BEFORE / right','20261024T024052907492Z','actual_127_0.png'),
    ('V2 AFTER / right','20261024T024552585869Z','actual_127_256.png'),
    ('V2 AFTER / left','20261024T024701002791Z','actual_127_0.png')]):
    p=ROOT/'work/ver_buki_riko/ground_slash_runtime'/folder
    d=read(p/'verification.local.json');m=next(m for m in d['frames']['127']['matches'] if filename==f"actual_127_{m['page_y']}.png")
    spr=Image.open(p/'expected_127.png');screen=Image.open(p/filename)
    crop=screen.crop((m['x']-8,m['y']-8,m['x']+spr.width+8,m['y']+spr.height+8));crop=crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST)
    draw.text((col*384+8,8),label,fill='white');sheet.paste(crop,(col*384+8,30))
sheet.save(out/'actual_cape_before_after.png')
save('artifact_sources.json',{'comparison':'Actual framebuffer crops at 3x nearest; labels only added outside image','art_tool':'builtin image_gen, three calls; no CLI fallback','art_directory':rel(D),'prompts':[rel(D/n) for n in ['generation_prompt.txt','recovery_prompt.txt','lunge_prompt.txt']],'generated_sources':[rel(D/n) for n in ['generated_keyposes_v1.png','generated_recovery_v2.png','generated_lunge_v3.png']]})
print(json.dumps({'output':rel(out),'rendered_body':len(union & GROUND_SLASH_BODY_FRAMES),'unverified':summary['new_body_full_render_unverified'],'changed':changed}))
