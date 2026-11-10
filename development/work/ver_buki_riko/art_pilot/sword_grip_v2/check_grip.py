"""Check actual short-grip assets against the pre-sword body/effect inputs."""
from assemble_grip import *
from scripts.build_riko_idle import validate_sword_effect,check_motion_scale
new=json.loads((D/'recipe.json').read_text());regs=json.loads((D/'registration.json').read_text())
changed=[];preserved=[];checks=[]
for key,rec in new['frames'].items():
 n=int(key);before=np.array(Image.open(old/recipe['frames'][key]['file']));after=np.array(Image.open(D/rec['file']))
 assert sha256((D/rec['file']).read_bytes())==rec['sha256']
 if np.array_equal(before,after):preserved.append(n)
 else:changed.append(n)
 if n in SABER_EFFECT_FRAMES:
  orig,b,c=original(n);assert np.array_equal(orig,after)
  validate_sword_effect(orig.tobytes(),after.tobytes())
  broken=after.copy();y,x=np.argwhere(after!=0)[0];broken[y,x]=(int(broken[y,x])%15)+1
  try:validate_sword_effect(orig.tobytes(),broken.tobytes())
  except ValueError:pass
  else:raise AssertionError('Effect mutation accepted')
 elif n in BODY:
  r=next(r for r in regs if r['frame']==n);w,b,cov=world_image(n);out=np.load(D/'final_worlds.npz')[str(n)]
  hx,hy=r['hand'];glove=np.zeros_like(cov);glove[96+hy-2:96+hy+3,96+hx-2:96+hx+3]=True
  assert not np.any((w!=0)&(w!=out)&~glove),f'Unrelated opaque body edited {n}'
  assert not np.any((out!=0)&~cov),f'Outside coverage {n}'
  assert not np.any((w!=0)&(out==0)),f'Body erased {n}'
  assert out[96+hy,96+hx]!=0,f'Empty grip center {n}'
  px,py=recipe['body_standard']['head_world_positions'][key]
  assert np.array_equal(out[96+py:96+py+19,96+px:96+px+23][front!=0],front[front!=0])
  checks.append({'frame':n,'hand_center_opaque':True,'all_existing_body_pixels_outside_5x5_hand_unchanged':True,'no_original_body_erasure':True,'head_unchanged':True})
 else:assert np.array_equal(before,after),f'Unselected frame changed {n}'
assert set(changed)==set(BODY)
assert not new['sword_effect_edits'] and new['preserved_effect_frames']==sorted(SABER_EFFECT_FRAMES)
write(D/'guard_checks.json',{'body_changed':changed,'preserved_motion_pngs':preserved,'original_effects_equal':sorted(SABER_EFFECT_FRAMES),'effect_mutation_rejection_cases':50,'body_checks':checks,'art_quality_automatically_proven':False})
print(json.dumps({'changed':len(changed),'preserved':len(preserved),'original_effects':50,'head_and_body_guard_cases':len(checks)}))
