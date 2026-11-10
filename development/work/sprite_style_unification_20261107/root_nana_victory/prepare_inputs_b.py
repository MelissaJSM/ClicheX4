from pathlib import Path
D=Path(__file__).resolve().parent
s=(D/'prepare_inputs_a.py').read_text('utf8')
replacements=[("'inputs_a01'","'inputs_b01'"),('(204,205)','(206,207)'),('left column204 is a planted victory transition, the front hand and tiny pistol bent inward across the chest, rear hand on waist. Right column205 raises the front bent forearm and hand beside the forehead, body slightly angled, rear hand on waist.','left column206 is the planted victory follow-through, front forearm bent upward with a tiny pink pistol close to the cheek/temple, rear hand on waist. Right column207 extends the front arm fully upward, holding the tiny pink pistol vertically overhead, with the rear hand still on the waist. Both retain the wide original planted stance.'),('victory204/205 input prepared','victory206/207 input prepared')]
for a,b in replacements:
 assert a in s,a;s=s.replace(a,b)
exec(compile(s,str(D/'prepare_inputs_b.py'),'exec'))
