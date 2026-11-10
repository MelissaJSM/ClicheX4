import json,sys,shutil,subprocess
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));from scripts.prepare_nana_idle_shot import write
from scripts.build_nana_run import validate,configure_scope
configure_scope('air_clone');d=ROOT/'work/ver_rin_nana/nana_art/air_clone_v1';src=ROOT/'work/ver_rin_nana/nana_air_clone/20261030T012104920417Z';out=ROOT/'work/ver_rin_nana/nana_air_clone/rejection_checks_v1';out.mkdir();rows=[]
for case in('wrong_parent','wrong_frame_scope','changed_style','tampered_arc','arrival_changed','effects_changed','armor_changed'):
 a=out/case/'a';b=out/case/'b';a.mkdir(parents=True);b.mkdir();r=json.loads((src/'recipe.json').read_text('utf8'))
 if case=='wrong_parent':r['parent_bin_sha256']='0'*64
 elif case=='wrong_frame_scope':r['changed_bitmap_references'][0]=[0,143]
 elif case=='changed_style':r['master_sha256']='0'*64
 elif case=='arrival_changed':r['arrival_frames_preserved']=False
 elif case=='effects_changed':r['separate_attack_effects_preserved']=False
 elif case=='armor_changed':r['armor_tiles_preserved']=False
 else:
  raw=bytearray((src/'modified.arc').read_bytes());raw[-1]^=1;(a/'modified.arc').write_bytes(raw);shutil.copyfile(src/'modified.arc',b/'modified.arc')
 for p in(a,b):write(p/'recipe.json',r)
 try:validate(a,b)
 except ValueError as e:rows.append({'case':case,'rejected_before_disc_write':True,'reason':str(e)})
 else:raise AssertionError('Accepted '+case)
for case in('armor_tile','missing_stream','palette_changed','wrong_character','unapproved_repack','effect_mapping'):
 a=d/('rejected_'+case);shutil.copytree(d/'production01',a);art=json.loads((a/'art.json').read_text('utf8'));extra=[]
 if case=='armor_tile':art['groups'][0]['writable'].append(8)
 elif case=='missing_stream':art['groups'].pop()
 elif case=='palette_changed':art['palette_words'][1]^=1
 elif case=='wrong_character':art['task']='x_shibuki'
 elif case=='unapproved_repack':extra=['--repack-bank']
 else:
  art['effect_index_mapping'][1]=2
 write(a/'art.json',art)
 r=subprocess.run([sys.executable,str(ROOT/'scripts/prepare_shibuki_remaining.py'),'--project','ver_rin_nana','--scope','base_nana_air_clone_17','--art',str(a),'--parent',str(ROOT/'out/ver_rin_nana/nana_special_remaining_20261030T010327624138Z'),*extra],capture_output=True,text=True)
 if r.returncode==0:raise AssertionError('Accepted '+case)
 reason=r.stderr.strip().splitlines()[-1]
 if not reason.startswith('ValueError:'):raise AssertionError(reason)
 rows.append({'case':case,'rejected_before_disc_write':True,'reason':reason})
write(d/'negative_checks.json',{'rows':rows});print(json.dumps({'rejections':len(rows)}))
