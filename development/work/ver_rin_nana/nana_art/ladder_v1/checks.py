import json,sys,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import write
from scripts.build_nana_run import validate,configure_scope
configure_scope('ladder');d=Path(__file__).parent;src=ROOT/'work/ver_rin_nana/nana_ladder/20261029T232636368928Z';out=ROOT/'work/ver_rin_nana/nana_ladder/rejection_checks_v1';out.mkdir();rows=[]
for case in ('wrong_parent','wrong_frame_scope','changed_style','tampered_arc','air_changed','wall_changed','hurt_changed'):
 a=out/case/'a';b=out/case/'b';a.mkdir(parents=True);b.mkdir();r=json.loads((src/'recipe.json').read_text('utf8'))
 if case=='wrong_parent':r['parent_bin_sha256']='0'*64
 elif case=='wrong_frame_scope':r['changed_bitmap_references'][0]=[0,43]
 elif case=='changed_style':r['master_sha256']='0'*64
 elif case in ('air_changed','wall_changed','hurt_changed'):r[case.split('_')[0]+'_frames_preserved']=False
 else:
  raw=bytearray((src/'modified.arc').read_bytes());raw[-1]^=1;(a/'modified.arc').write_bytes(raw);shutil.copyfile(src/'modified.arc',b/'modified.arc')
 for p in (a,b):write(p/'recipe.json',r)
 try:validate(a,b)
 except ValueError as e:rows.append({'case':case,'rejected_before_disc_write':True,'reason':str(e)})
 else:raise AssertionError('Accepted '+case)
for case in ('armor_tile','missing_stream','palette_changed'):
 a=d/('rejected_'+case);shutil.copytree(d/'production01',a);pack=json.loads((a/'packing.json').read_text('utf8'));art=json.loads((a/'art.json').read_text('utf8'))
 if case=='armor_tile':pack[0]['writable'].append(13)
 elif case=='missing_stream':pack.pop()
 else:art['palette_words'][1]^=1
 write(a/'packing.json',pack);write(a/'art.json',art)
 r=subprocess.run([sys.executable,str(ROOT/'scripts/prepare_shibuki_ladder.py'),'--project','ver_rin_nana','--art',str(a),'--parent',str(ROOT/'out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z')],capture_output=True,text=True)
 if r.returncode==0:raise AssertionError('Accepted '+case)
 reason=r.stderr.strip().splitlines()[-1]
 if not reason.startswith('ValueError:'):raise AssertionError(reason)
 rows.append({'case':case,'rejected_before_disc_write':True,'reason':reason})
write(d/'negative_checks.json',{'rows':rows});print(json.dumps({'rejections':len(rows)}))
