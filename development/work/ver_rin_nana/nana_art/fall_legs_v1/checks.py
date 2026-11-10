import json,sys,shutil,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import write
from scripts.build_nana_run import validate,configure_scope
from scripts.prepare_nana_checkpoint import refresh
configure_scope('fall_legs');d=Path(__file__).parent;src=ROOT/'work/ver_rin_nana/nana_fall_legs/20261029T230719464749Z';out=ROOT/'work/ver_rin_nana/nana_fall_legs/rejection_checks_v1';out.mkdir();rows=[]
for case in ('wrong_parent','wrong_frame_scope','changed_style','tampered_arc','upper_body_changed','hurt_changed'):
 a=out/case/'a';b=out/case/'b';a.mkdir(parents=True);b.mkdir();r=json.loads((src/'recipe.json').read_text('utf8'))
 if case=='wrong_parent':r['parent_bin_sha256']='0'*64
 elif case=='wrong_frame_scope':r['changed_bitmap_references'][0]=[0,41]
 elif case=='changed_style':r['master_sha256']='0'*64
 elif case=='upper_body_changed':r['upper_body_gun_and_registration_preserved']=False
 elif case=='hurt_changed':r['hurt_frames_preserved']=False
 else:
  raw=bytearray((src/'modified.arc').read_bytes());raw[-1]^=1;(a/'modified.arc').write_bytes(raw);shutil.copyfile(src/'modified.arc',b/'modified.arc')
 for p in (a,b):write(p/'recipe.json',r)
 try:validate(a,b)
 except ValueError as e:rows.append({'case':case,'rejected_before_disc_write':True,'reason':str(e)})
 else:raise AssertionError('Accepted '+case)
state=gzip.decompress((ROOT/'work/ver_rin_nana/checkpoints/before_nana_fall_legs_20261030/current/SLUS_005.61.000').read_bytes());old=(ROOT/'out/ver_rin_nana/nana_hurt_20261029T225358832150Z/modified.arc').read_bytes();new=(ROOT/'out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z/modified.arc').read_bytes();result,report=refresh(state,old,new,442);assert report['active_frame']==115;assert result==gzip.decompress((ROOT/'work/ver_rin_nana/checkpoints/nana_fall_legs_preview_20261030/SLUS_005.61.000').read_bytes())
for name,offset,value in [('wrong_character',2,1),('active_fall_frame',0x47,47),('armor',0xa7,15)]:
 s=bytearray(state);s[442+0x1418c8+offset]=value
 try:refresh(bytes(s),old,new,442)
 except ValueError as e:rows.append({'case':name,'rejected':True,'reason':str(e)})
 else:raise AssertionError('Accepted '+name)
write(d/'negative_checks.json',{'rows':rows,'idle115_refresh_reproduced':True,'checkpoint_bytes_changed':report['changed_bytes']});print(json.dumps({'rejections':len(rows),'idle115_reproduced':True}))
