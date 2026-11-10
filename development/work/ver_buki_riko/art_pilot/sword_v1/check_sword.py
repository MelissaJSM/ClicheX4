from fit_sword import *
from scripts.build_riko_idle import validate_sword_effect,SABER_EFFECT_FRAMES
new=json.loads((D/'recipe.json').read_text('utf8'))
regs={r['frame']:r for r in json.loads((D/'registration.json').read_text('utf8'))}
master=np.array(Image.open(D/'sword_native.png'));pivot=json.loads((D/'sword_master.json').read_text('utf8'))['grip_pivot']
unchanged=[];changed=[];negative=[]
for key,r in new['frames'].items():
 n=int(key);before=np.array(Image.open(old/recipe['frames'][key]['file']));after=np.array(Image.open(D/r['file']));assert before.shape==after.shape
 assert sha256((D/r['file']).read_bytes())==r['sha256']
 if np.array_equal(before,after):unchanged.append(n)
 else:changed.append(n)
 if n in BODY:
  a,b,safe=original(n);reg=regs[n];hx,hy=reg['hand'];layer=np.zeros((192,192),np.uint8);layer[96+hy-48:96+hy+48,96+hx-48:96+hx+48]=orient(master,pivot,reg['angle']);local=layer[96+b[1]:96+b[3],96+b[0]:96+b[2]]
  assert not np.any((before!=after)&(local==0)),f'Changed non-weapon body {n}'
  for y in range(hy-1,hy+2):
   for x in range(hx-1,hx+2):
    if b[0]<=x<b[2] and b[1]<=y<b[3] and before[y-b[1],x-b[0]]:assert after[y-b[1],x-b[0]]==before[y-b[1],x-b[0]]
 elif n in SABER_EFFECT_FRAMES:
  validate_sword_effect(before.tobytes(),after.tobytes(),new['sword_effect_edits'].get(key))
  if key in new['sword_effect_edits']:
   try:validate_sword_effect(before.tobytes(),after.tobytes())
   except ValueError:negative.append({'frame':n,'missing_permission_rejected':True})
   else:raise AssertionError('Effect changed without explicit policy')
   broken=after.copy();y,x=np.argwhere(before!=0)[0];broken[y,x]=(int(before[y,x])%15)+1
   record={'original_indices_sha256':sha256(before.tobytes()),'replacement_indices_sha256':sha256(broken.tobytes()),'added_pixels':int((before!=broken).sum())}
   try:validate_sword_effect(before.tobytes(),broken.tobytes(),record)
   except ValueError:negative[-1]['original_trail_mutation_rejected']=True
   else:raise AssertionError('Trail mutation accepted')
 else:assert np.array_equal(before,after),f'Unselected motion changed {n}'
assert set(changed)==set(BODY)|set(map(int,new['sword_effect_edits']))
assert len(changed)==74 and len(new['preserved_effect_frames'])==34
assert all(r['grip_overlaps_original_glove'] and r['outside']==0 for r in json.loads((D/'attachment_checks.json').read_text('utf8')))
result={'changed_body_frames':BODY,'changed_effect_frames':sorted(map(int,new['sword_effect_edits'])),'unchanged_motion_pngs':unchanged,
 'unchanged_idle_pngs':'Build inputs retain the same six selected idle PNG hashes',
 'body_differences_only_on_weapon_layer':True,'gripping_glove_opaque_pixels_preserved':True,
 'all_58_grip_centers_attached':True,'original_trail_nonzero_pixels_preserved':True,'negative_checks':negative,
 'body_canvas_head_pose_scale_unchanged':True,'full_anatomical_and_animation_quality_automatically_proven':False}
(D/'guard_checks.json').write_text(json.dumps(result,indent=2),'utf8');print(json.dumps({'changed':len(changed),'unchanged_motion_pngs':len(unchanged),'negative_effect_cases':len(negative)}))
