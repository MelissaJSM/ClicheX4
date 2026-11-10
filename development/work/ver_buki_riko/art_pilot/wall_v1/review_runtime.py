import hashlib,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts.project import digest,load_project,inspect_references
from src.epsxe_state import match_sprite
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T012121410066Z'
R=B/('wall_validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));R.mkdir()
runtime=[ROOT/'work/ver_buki_riko/wall_runtime'/n for n in ['20261024T015541398330Z','20261024T015824607315Z','20261024T015939987083Z']]
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[];strict=set();wall=set();directions={}
canvas=Image.new('RGB',(960,520),(25,32,42));draw=ImageDraw.Draw(canvas)
for i,n in enumerate(range(35,41)):
 d=json.loads((runtime[0]/'verification.local.json').read_text());r=d['frames'][str(n)]
 assert r['verified']
 page=r['matches'][0]['page_y']; actual=Image.open(runtime[0]/f'actual_{n:03d}_{page}.png').convert('RGB')
 expected=Image.open(runtime[0]/f'expected_{n:03d}.png').convert('RGBA')
 assert match_sprite(actual,expected)
 negative=expected.copy()
 xy=next((x,y) for y in range(negative.height) for x in range(negative.width) if negative.getpixel((x,y))[3])
 negative.putpixel(xy,(255,0,255,255))
 assert not match_sprite(actual,negative)
 checks.append({'frame':n,'full_opaque_match':True,'one_pixel_negative_rejected':True,'actual':rel(runtime[0]/f'actual_{n:03d}_{page}.png')})
 x=(i%3)*320;y=(i//3)*260;canvas.paste(actual,(x,y+20));draw.text((x+5,y+3),f'Actual game: frame {n}',fill='white')
canvas.save(R/'actual_right_wall_contact.png')
shutil.copy2(runtime[0]/'slide_compare.png',R/'slide_effect_comparison.png')
for p in runtime:
 d=json.loads((p/'verification.local.json').read_text());strict.update(d['verified_frames'])
 for n,r in d['frames'].items():
  if r['verified']:directions.setdefault(n,set()).update(m['flip_x'] for m in r['matches'])
wall=set(range(35,44))&strict
project=load_project(ROOT,'ver_buki_riko'); source=ROOT/project['source_bin']
assert digest(source)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
assert digest(B/'riko_motion.bin')=='686e5f4d26acc4e2e06bedb527213a8baa35a200f2330527b98a1edf0e35f0e2'
for pid in ['ver_buki_riko','ver_rin_nana']:inspect_references(ROOT,load_project(ROOT,pid))
summary={'build':rel(B),'bin_sha256':digest(B/'riko_motion.bin'),'source_sha256':digest(source),
 'build_art_changed':False,'riko_reference_count':56,'runtime_reports':[rel(p/'verification.local.json') for p in runtime],
 'wall_full_pixel_verified_frames':sorted(wall),'connection_full_pixel_verified_frames':sorted(strict-wall),
 'verified_frame_flip_flags':{n:sorted(v) for n,v in directions.items()},
 'wall_observed_ram_vram_but_full_render_unverified_frames':[41,42,43],
 'wall_left_side_verified':False,'wall_slide_render_limit':'Original white dust overlaps lower body; no masked or relaxed full-pixel pass assigned',
 'user_assisted_navigation_and_first_capture':True,'user_assistance_statement':'너가 대쉬를 잘못하는거같아서 보조조작중이었어 이제 손놓을게',
 'first_capture_input':'Observer sent no keys; user assisted gameplay',
 'later_captures_input':'Logged ordinary keyboard playback after user released controls',
 'process_memory_written':False,'agent_save_state_loaded':False,'agent_save_state_created':True,
 'session':'work/ver_buki_riko/emulator_sessions/20261024T014807152589Z','session_closed':True,
 'previous_session_exit_cause':'PID38668 disappeared without agent close; cause not established',
 'runtime_negative_controls':checks,'unit_tests':{'count':53,'passed':True,'command':'python -m unittest discover -s tests -q'},
 'current_build_all_evidence_unverified_frames':[32,41,42,43,44]}
write(R/'runtime_summary.json',summary)
I=ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z'; inv=json.loads((I/'inventory.json').read_text())
animations=[a for a in inv['animations'] if a['id'] in [88,89,90]]
target=sorted({s['frame'] for a in animations for s in a['sequence']})
groups={k:v for k,v in inv['stream_sharing'].items() if any(bank==0 and frame in target for bank,frame in v)}
affected=sorted({frame for members in groups.values() for bank,frame in members if bank==0})
linked=[a['id'] for a in inv['animations'] if a['graphics_bank']==0 and any(s['frame'] in affected for s in a['sequence'])]
plan={'kind':'analysis_only_no_new_art_or_patch','source_inventory':rel(I/'inventory.json'),'source_inventory_sha256':digest(I/'inventory.json'),
 'animation_ids':[88,89,90],'animations':animations,'direct_frame_references':target,'direct_count':len(target),
 'shared_stream_groups':groups,'shared_bank0_references':affected,'shared_bank0_count':len(affected),
 'other_animations_using_shared_references':linked,
 'preserve_original_timing_events_parts_hitboxes':True,
 'weapon_effect_mapping_status':'Weapon object spawn found in local player_special.c; PS1 effect graphics and sword/body split still require byte/runtime verification',
 'design_basis':'Current full Riko master, approved walking design and head scale; all three slashes reviewed together',
 'frames':{str(n):inv['frames'][f'bank0_{n:03d}'] for n in affected}}
write(R/'ground_slash_plan.json',plan)
sheet=Image.new('RGB',(8*112,((len(target)+7)//8)*128),(33,44,58));d=ImageDraw.Draw(sheet)
for i,n in enumerate(target):
 f=inv['frames'][f'bank0_{n:03d}'];img=Image.open(I/f['image']).convert('RGBA');x=i%8*112;y=i//8*128
 sheet.paste(img,(x+56-f['origin'][0],y+66-f['origin'][1]),img);d.text((x+4,y+3),str(n),fill='white')
sheet.save(R/'original_ground_slash_reference.png')
for name in ['current_build.json','art_selection.json','master_sheet.json']:
 p=ROOT/'projects/ver_buki_riko'/name;shutil.copy2(p,R/('previous_'+name));d=json.loads(p.read_text(encoding='utf-8'))
 if name=='current_build.json':
  all_frames=set(d['runtime_verified_frames'])|set(d['runtime_unverified_current_build_frames'])
  d['runtime_previous_summary']=d['runtime_summary'];d['runtime_summary']=rel(R/'runtime_summary.json')
  d['runtime_verified_frames']=sorted(strict|{147});d['runtime_unverified_current_build_frames']=sorted(all_frames-set(d['runtime_verified_frames']))
  d['runtime_unverified_any_evidence_frames']=[32,41,42,43,44]
  d['runtime_inherited_unchanged_frames']=sorted(set(d['runtime_inherited_unchanged_frames'])-set(d['runtime_verified_frames']))
  d['session']=summary['session'];d['session_closed']=True;d['user_assisted_runtime']=True
  d['agent_created_save_state']=True;d['agent_loaded_save_state']=False;d['boot_navigation_fully_observed']=False
  d['next_task']='Verify left wall and unobscured slide rendering; ground slash88..90 shared-frame plan ready'
 if name=='art_selection.json':
  d['game_applied_scope']='56 bank0 references; original47 preserved; wall35..40 + connection22/23 + idle147 have exact runtime evidence; slide41..43 obscured by dust'
 if name=='master_sheet.json':d['next_group']='remaining_wall_runtime_and_ground_slash_analysis'
 d['wall_runtime_verified']=False;d['wall_runtime_verified_frames']=sorted(wall)
 d['wall_render_occluded_frames']=[41,42,43];d['wall_left_runtime_verified']=False
 d['wall_runtime_report']=rel(R/'runtime_summary.json');d['ground_slash_plan']=rel(R/'ground_slash_plan.json')
 write(p,d)
print(json.dumps({'review':rel(R),'wall_verified':sorted(wall),'slash_direct':len(target),'slash_shared':len(affected),'linked_animations':linked}))
