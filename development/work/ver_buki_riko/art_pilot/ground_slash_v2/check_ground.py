from fit_ground import *
from scripts.discover_inputs import sha256,psx_arc
from scripts.build_riko_idle import patch_frames,check_motion_scale
from src.psx_frame_edit import edit_frame_set,read_indexed_png
from src.psx_compress import encode_stream

build=ROOT/'out/ver_buki_riko/riko_motion_20261024T024352897084Z'
prior=ROOT/'out/ver_buki_riko/riko_motion_20261024T012121410066Z'
manifest=json.loads((build/'manifest.json').read_text('utf8'))
before=json.loads((prior/'manifest.json').read_text('utf8'))
unchanged=[]
for key in before['frame_inputs']:
 n=int(key);name=f'{"idle" if n in (0,1,2,146,147,148) else "frame"}_{n:03}.png'
 if (build/name).read_bytes()!=(prior/name).read_bytes():raise ValueError(f'Existing frame changed: {n}')
 unchanged.append(n)
frames={n:read_indexed_png(build/f'frame_{n:03}.png',words) for n in range(61,135)}
guard=[]
for label,n,position in [('effect64',64,0),('duplicate81',81,48*32)]:
 bad=dict(frames);pixels,size=bad[n];pixels=bytearray(pixels);pixels[position]=(pixels[position]+1)%16;bad[n]=(bytes(pixels),size)
 try:patch_frames(arc,gmeta,gfx,parts,bad,pal)
 except ValueError as exc:guard.append({'case':label,'rejected':True,'error':str(exc)})
 else:raise ValueError(f'Negative guard accepted: {label}')
motion=json.loads(Path(manifest['motion_set']).read_text('utf8'))
all_frames={int(n):read_indexed_png(build/f'frame_{int(n):03}.png',words) for n in motion['frames']}
reference=read_indexed_png(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png',words)
n=61;bad=dict(all_frames);pixels,size=bad[n];pixels=bytearray(pixels);hx,hy=motion['body_standard']['head_world_positions'][str(n)];b=geometry[n][1]
yy,xx=np.argwhere(front!=0)[0];position=(hy-b[1]+int(yy))*size[0]+hx-b[0]+int(xx);pixels[position]=(pixels[position]+1)%16;bad[n]=(bytes(pixels),size)
try:check_motion_scale(motion,bad,gfx,parts,reference)
except ValueError as exc:guard.append({'case':'head61','rejected':True,'error':str(exc)})
else:raise ValueError('Changed approved head was accepted')
original=[]
f=bank['frames'][77];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
for n in range(77,82):
 c=composition_frame(parts,0,n);pixels,size=compose_indices(raw,f['tile_count'],c)[:2];original.append((c,pixels,size))
roundtrip=edit_frame_set(raw,f['tile_count'],original,overlap_policy='equal_sources')
if roundtrip!=raw:raise ValueError('Overlapping original roundtrip changed hidden bytes')
report={'build':str(build),'bin_sha256':manifest['modified_bin']['sha256'],'unchanged_previous_body_refs':sorted(unchanged),
 'negative_guards':guard,'original77_81_roundtrip_byte_identical':True,'source_sha256':profile['source_sha256'],
 'new_body_frames':body_frames,'preserved_effect_frames':effect_frames,'input_rom_or_reference_modified':False}
(D/'guard_checks.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
