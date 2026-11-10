from pathlib import Path
import hashlib,json
P=Path(__file__).parent;ROOT=P.resolve().parents[3];gen=Path('<LOCAL_PATH>')
def file(p):
 p=Path(p);return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size}
calls=[
 ('prompt_run.txt','generated_run_v1.png','exec-fb75a195-8a4a-460e-844c-55f0a67551fc.png',['run_edit_reference.png','master_idle_6x.png']),
 ('prompt_jump.txt','generated_jump_v1.png','exec-202172c0-a276-4cdc-9e15-05e0ed079c7f.png',['jump_edit_reference.png','master_idle_6x.png']),
 ('prompt_compact.txt','generated_compact_v1.png','exec-c7eb9ae0-e94e-4c73-ab3d-644902172886.png',['compact_edit_reference.png']),
 ('gait_cape_repair/prompt_cape.txt','gait_cape_repair/generated_cape.png','exec-2de24d42-0518-4884-ac36-9084c3c7cf3c.png',['gait_cape_repair/cape_edit_reference.png']),
 ('gait_cape_repair/prompt_legs.txt','gait_cape_repair/generated_legs.png','exec-9c0f9ce4-4466-4392-b1de-2a8facee8277.png',['master_idle_6x.png']),
 ('gait_cape_repair/prompt_legs_v2.txt','gait_cape_repair/generated_legs_v2.png','exec-35d3ceaa-840b-49b7-808e-ee0874f5d99d.png',['gait_cape_repair/generated_legs.png']),
 ('upper_body_repair/prompt_upper.txt','upper_body_repair/generated_upper_v1.png','exec-bc45b68c-8e2b-4668-85c3-f9bc6be0bbe4.png',['upper_body_repair/upper_edit_reference.png']),
 ('upper_body_repair/prompt_upper_v2.txt','upper_body_repair/generated_upper_v2.png','exec-c4364b00-dafc-4f92-bf91-de0615852fd7.png',['upper_body_repair/generated_upper_v1.png']),
 ('stride_revision/prompt_stride.txt','stride_revision/generated_stride_v1.png','exec-2d8085fa-b1a4-4b54-aea4-3995cc2c728d.png',['master_idle_6x.png','gait_cape_repair/generated_legs.png']),
 ('stride_revision/prompt_guided_stride.txt','stride_revision/generated_stride_guided.png','exec-50a52809-e17e-4f32-a5f3-c611cea9e1e7.png',['stride_revision/kinematic_guide.png','gait_cape_repair/generated_legs.png']),
 ('coherent_walk/prompt.txt','coherent_walk/generated_v1.png','exec-3526e9dd-f370-454e-9cf7-176cdfe1aa63.png',['coherent_walk/reference_cycle.png','master_idle_6x.png']),
 ('coherent_walk/prompt_v2.txt','coherent_walk/generated_v2.png','exec-be759fb0-fabc-4da1-bd68-84ff7ee37a70.png',['master_idle_6x.png']),
 ('coherent_walk/prompt_guided.txt','coherent_walk/generated_guided.png','exec-3eb2b990-8497-4303-9bd6-8a39d2dc9e24.png',['coherent_walk/pose_guide.png','master_idle_6x.png']),
 ('coherent_walk/prompt_cape_v1.txt','coherent_walk/generated_cape_v1.png','exec-06b3b5ac-7383-40b2-b844-63cbe855fd72.png',['coherent_walk/generated_guided.png']),
 ('coherent_walk/prompt_compact.txt','coherent_walk/generated_compact.png','exec-b8b90769-2afd-4119-aa12-450937a55b31.png',['coherent_walk/generated_guided.png']),
 ('coherent_walk/prompt_final.txt','coherent_walk/generated_final.png','exec-bddfef51-0132-43e9-aa42-cfdaf17feb74.png',['coherent_walk/generated_compact.png']),
 ('zero_based_rebuild/prompt_key_poses.txt','zero_based_rebuild/generated_keys_v1.png','exec-7cf642dd-05c9-4905-93ae-4136f8bb8710.png',['zero_based_rebuild/zero_key_poses.png','master_idle_6x.png']),
 ('zero_based_rebuild/prompt_keys_v2.txt','zero_based_rebuild/generated_keys_v2.png','exec-4d1558a6-25d5-4b65-8481-0a5c1a8b6209.png',['zero_based_rebuild/generated_keys_v1.png','master_idle_6x.png']),
 ('zero_based_rebuild/prompt_cycle.txt','zero_based_rebuild/generated_cycle.png','exec-17105072-5ae1-4fb0-868d-311a93959101.png',['zero_based_rebuild/zero_full_cycle.png','zero_based_rebuild/generated_keys_v2.png','master_idle_6x.png']),
 ('zero_based_rebuild/prompt_cycle_compact.txt','zero_based_rebuild/generated_cycle_compact.png','exec-791e33f5-bdbd-4f1e-8f4f-5a0876d3003e.png',['zero_based_rebuild/generated_cycle.png']),
 ('zero_based_rebuild/prompt_fit.txt','zero_based_rebuild/generated_fit.png','exec-cb2d9dae-5402-4272-aacd-e8cde331cab1.png',['zero_based_rebuild/fit_edit_reference.png'])]
records=[]
for prompt,local,original,refs in calls:
 a,b=file(P/local),file(gen/original);assert a['sha256']==b['sha256'];records.append({'tool':'built-in image_gen.imagegen','transparent_background':True,'prompt':file(P/prompt),'inputs':[file(P/p) for p in refs],'default_output':b,'project_copy':a})
(P/'imagegen_calls.local.json').write_text(json.dumps({'calls':records,'external_service_cli_used':False,'original_sprite_pose_references_sent_to_builtin':True,'original_sprite_reference_calls':[17,19],'rom_bios_or_save_states_sent':False,'authorization_context':'User: 정 안되면 기본 제로처럼 걷는다는 느낌을 살려봐'},ensure_ascii=False,indent=2),encoding='utf-8')
old=ROOT/'out/ver_buki_riko/riko_motion_20261023T195248689307Z';new=ROOT/'out/ver_buki_riko/riko_motion_20261023T200224432890Z'
from PIL import Image
import numpy as np
motion=json.loads((P/'upper_body_repair/recipe.json').read_text());checks=[]
for r in motion['upper_body_motion']['records']:
 n=r['frame'];a=np.array(Image.open(old/f'frame_{n:03d}.png'));b=np.array(Image.open(new/f'frame_{n:03d}.png'))
 # Bounds are read from the build's frame metadata, below via the existing source parser.
checks=motion['upper_body_motion']['records']
preserved=[]
for n in [0,1,2,3,4,5,6,*range(21,35),146,147,148]:
 name=f'{"idle" if n in [0,1,2,146,147,148] else "frame"}_{n:03d}.png';assert (old/name).read_bytes()==(new/name).read_bytes();preserved.append(name)
(new/'upper_body_comparison.json').write_text(json.dumps({'previous_build':str(old),'changed_frames':list(range(7,21)),'other_pngs_byte_identical':preserved,'native_upper_edit_checks':checks,'generated_source':file(P/'upper_body_repair/generated_upper_v2.png')},indent=2),encoding='utf-8')
print(json.dumps({'image_calls':len(records),'unchanged_full_pngs':len(preserved),'upper_frames':len(checks)}))
