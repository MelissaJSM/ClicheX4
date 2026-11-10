import copy,json,sys
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_armor_remaining import prepare
from scripts.project import new_run,digest,write_json
D=Path(__file__).resolve().parent;source=D/'layers06';out=new_run(ROOT,'ver_buki_riko','shibuki_armor_input_checks')
meta=json.loads((source/'layers.json').read_text());checks=[]
for name in ('wrong_scope','wrong_palette','rgba','index_overflow','part_overflow'):
    d=out/name;d.mkdir();m=copy.deepcopy(meta)
    if name=='wrong_scope':m['frames']=m['frames'][:-1]
    if name=='wrong_palette':m['palette_words'][1]^=1
    (d/'layers.json').write_text(json.dumps(m))
    if name in ('rgba','index_overflow','part_overflow'):
        for n in (33,34):
            im=Image.open(source/f'head_{n:03}.png')
            if name=='rgba':im=im.convert('RGBA')
            else:
                v=np.array(im)
                if name=='index_overflow':v[70,70]=16
                else:v[:]=0;v[60:80,60:90]=3
                im=Image.fromarray(v,mode='P');im.putpalette(Image.open(source/f'head_{n:03}.png').getpalette());im.info['transparency']=0
            im.save(d/f'head_{n:03}.png')
    try:prepare(d)
    except ValueError as e:checks.append({'case':name,'rejected':True,'message':str(e)})
    else:raise AssertionError('Invalid input was accepted: '+name)
expected={
 'MegaMan X4.bin':'3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',
 'character/ver_buki_riko/buki(4th armor).webp':'729065c46a128b5a6e307673a35d31a4738e5db5addb7ffc995c8cf1131eddd9',
 'character/ver_buki_riko/buki(X).webp':'d7476066b352ac041901b331ff1c78e7c05776df79392d114f7a69b7e61ed1c5',
 'out/ver_buki_riko/riko_sfx_20261026T022446511583Z/riko_motion.bin':'1c87c8baaa535dacf9e385e5157b2205b7b6db634ca5e8fed3597f68fc4a7246',
 'out/ver_buki_riko/shibuki_arrival_victory_style_20261026T235455012767Z/shibuki_riko.bin':'6a8e7519a229994bbb831be74d77324ce3ffd0afaefc370329208cd3f38a05a9',
 'out/ver_buki_riko/shibuki_arrival_victory_style_20261026T235455012767Z/modified.arc':'f8f1d567e612b5e60f5911a1b2930993a76951a1840d15821bafb0725fec2903',
 'ePSXe2018/sstates/SLUS_005.61.000':'eff46e6e1b992686e2e05a934c274c2c2f77ba5747aac37e23a73756270f3a25',
 'ePSXe2018/memcards/epsxe000.mcr':'b0a596dba2e0e6ba6cdaaf87a894990365f0a33ee2b8d6536f6a5eb2298d77f9',
 'ePSXe2018/memcards/epsxe001.mcr':'ab68aa740dd7a93b8b01b4b4b9cf1a57dab11c9900052879bfbc665499bf120f',
 'work/ver_buki_riko/shibuki_armor_runtime/20261027T003857790030Z/full_armor_pilot_f1.000':'858dd6f83deeadb51d06365646da57778abd7142c05d7ac93b94eccfd6998b21'}
preserved=[]
for name,want in expected.items():
    actual=digest(ROOT/name);preserved.append({'path':name,'sha256':actual,'equal':actual==want})
    if actual!=want:raise AssertionError('Protected source changed: '+name)
write_json(out/'checks.json',{'negative_checks':checks,'preserved_inputs':preserved,'unit_tests_passed':188})
print(json.dumps({'output':str(out),'rejected':len(checks),'preserved':len(preserved)}))
