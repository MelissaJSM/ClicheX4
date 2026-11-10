from fit_air import *
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import patch_frames,check_motion_scale
from src.psx_frame_edit import read_indexed_png,edit_frame_set
from src.psx_player import compose_indices
build=ROOT/'out/ver_buki_riko/riko_motion_20261024T031656659594Z';prior=ROOT/'out/ver_buki_riko/riko_motion_20261024T024352897084Z'
manifest=json.loads((build/'manifest.json').read_text('utf8'));previous=json.loads((prior/'manifest.json').read_text('utf8'))
same=[]
for n in map(int,previous['frame_inputs']):
 name=f'{"idle" if n in (0,1,2,146,147,148) else "frame"}_{n:03d}.png'
 assert (build/name).read_bytes()==(prior/name).read_bytes(),n
 same.append(n)
frames={n:read_indexed_png(build/f'frame_{n:03d}.png',words) for n in roles['shared_references']};guards=[]
for n in roles['effect_frames']:
 changed=dict(frames);pixels,size=changed[n];pixels=bytearray(pixels);pixels[0]=(pixels[0]+1)%16;changed[n]=(bytes(pixels),size)
 try:patch_frames(arc,gmeta,gfx,parts,changed,pal)
 except ValueError as exc:
  assert 'effect' in str(exc);guards.append({'frame':n,'changed_effect_rejected':True,'error':str(exc)})
 else:raise AssertionError('Changed effect accepted')
roundtrips=[]
for offset in sorted({bank['frames'][n]['offset'] for n in roles['shared_references']}):
 nums=[n for n in roles['shared_references'] if bank['frames'][n]['offset']==offset];f=bank['frames'][nums[0]];raw=decode_stream(gfx,offset,f['limit'],f['tile_count']*128).data;edits=[]
 for n in nums:
  c=composition_frame(parts,0,n);pixels,size=compose_indices(raw,f['tile_count'],c)[:2];edits.append((c,pixels,size))
 assert edit_frame_set(raw,f['tile_count'],edits)==raw;roundtrips.append(nums)
motion=json.loads(Path(manifest['motion_set']).read_text('utf8'));all_frames={int(n):read_indexed_png(build/f'frame_{int(n):03d}.png',words) for n in motion['frames']}
reference=read_indexed_png(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png',words)
bad=dict(all_frames);pixels,size=bad[213];pixels=bytearray(pixels);hx,hy=motion['body_standard']['head_world_positions']['213'];b=geometry[213][1];y,x=np.argwhere(front!=0)[0];pos=(hy-b[1]+int(y))*size[0]+hx-b[0]+int(x);pixels[pos]=(pixels[pos]+1)%16;bad[213]=(bytes(pixels),size)
try:check_motion_scale(motion,bad,gfx,parts,reference)
except ValueError as exc:head_guard=str(exc)
else:raise AssertionError('Head identity changed without rejection')
report={'build':str(build),'bin_sha256':manifest['modified_bin']['sha256'],'unchanged_prior_all_input_refs':sorted(same),'unchanged_prior_body_count':96,
 'effect_negative_guards':guards,'original_stream_roundtrips':roundtrips,'original_roundtrip_byte_identical':True,'changed_head_rejected':head_guard,
 'source_sha256':profile['source_sha256'],'new_body_frames':body,'new_effects_preserved':roles['effect_frames']}
(D/'guard_checks.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'unchanged_prior_inputs':len(same),'effect_rejections':len(guards),'roundtrip_groups':len(roundtrips),'head_guard':head_guard}))
