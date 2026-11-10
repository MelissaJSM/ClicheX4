import json,sys,shutil,subprocess,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import write
from scripts.build_nana_run import validate,configure_scope
from scripts.prepare_nana_checkpoint import refresh
d=Path(__file__).parent;src=d/'production02';out=d/'negative_inputs01';shutil.copytree(src,out);results=[]
for case in ('wrong_palette','wrong_effect_palette','missing_frame','stale_packing_hash','armor_write'):
 for name in ('art.json','packing.json'):shutil.copyfile(src/name,out/name)
 p=out/('packing.json' if case in ('stale_packing_hash','armor_write')else 'art.json');r=json.loads(p.read_text('utf8'))
 if case=='wrong_palette':r['palette_words'][1]^=1
 elif case=='wrong_effect_palette':r['effect_palette_words'][1]^=1
 elif case=='missing_frame':r['frames'].pop()
 elif case=='stale_packing_hash':r[0]['raw_sha256']='0'*64
 else:r[0]['writable'].append(8)
 write(p,r);proc=subprocess.run([sys.executable,'scripts/prepare_shibuki_hurt.py','--project','ver_rin_nana','--art',str(out),'--parent','out/ver_rin_nana/nana_wall_20261029T224356693137Z'],cwd=ROOT,capture_output=True,text=True);reason=proc.stderr.strip().splitlines()[-1];assert proc.returncode!=0 and 'ValueError' in reason;results.append({'case':case,'rejected':True,'reason':reason})
configure_scope('hurt');source=ROOT/'work/ver_rin_nana/nana_hurt/20261029T225320652984Z';out=ROOT/'work/ver_rin_nana/nana_hurt/rejection_checks_v1';out.mkdir(exist_ok=False)
for case in ('wrong_parent','wrong_frame_scope','changed_style','tampered_arc','previous_wall_changed','shared_effect_changed'):
 a=out/case/'a';b=out/case/'b';a.mkdir(parents=True);b.mkdir();r=json.loads((source/'recipe.json').read_text('utf8'))
 if case=='wrong_parent':r['parent_bin_sha256']='0'*64
 elif case=='wrong_frame_scope':r['changed_bitmap_references'][0]=[0,85]
 elif case=='changed_style':r['master_sha256']='0'*64
 elif case=='previous_wall_changed':r['wall_frames_preserved']=False
 elif case=='shared_effect_changed':r['shared_effect_tiles_parts_preserved']=False
 else:
  raw=bytearray((source/'modified.arc').read_bytes());raw[-1]^=1;(a/'modified.arc').write_bytes(raw);shutil.copyfile(source/'modified.arc',b/'modified.arc')
 for p in (a,b):write(p/'recipe.json',r)
 try:validate(a,b)
 except ValueError as e:results.append({'case':case,'rejected_before_disc_write':True,'reason':str(e)})
 else:raise AssertionError('Accepted '+case)
write(d/'negative_checks.json',results);print(json.dumps({'passed':len(results),'results':results}))
