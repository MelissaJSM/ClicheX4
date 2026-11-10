"""최신 시부키 자원과 revised 갤러리를 대조하고 읽기 전용 검토 시트를 구성한다."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.export_x_consistency import Archive,page,GROUPS,GROUP_NAMES
from scripts.build_sprite_consistency_gallery import normalized,OUT
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_disc import file_hash
SOURCE=ROOT/'out/ver_buki_riko/hurt_capsule_fix_20261106_v1/shibuki_riko.bin'
SHA='8c1a2fa5b3f985be9945717d3d88776f2f4534030c42818843ec8093a3ce1a81'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 assert file_hash(SOURCE)==SHA
 names=('PL00_U.ARC','PL02_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC','MOJIPAT.ARC','LOAD_U.ARC')
 assets,_=read_disc(SOURCE,names)
 old,_=read_disc(ROOT/'out/ver_buki_riko/sprite_consistency_20261105_v1/shibuki_riko.bin',names)
 equality={n:{'current':sha(assets[n]),'previous':sha(old[n]),'whole_equal':assets[n]==old[n],
              'graphics_entries_equal':{str(t):entry(assets[n],t)==entry(old[n],t) for t in (2,3,9) if t in (2,3,9)}} for n in names[:2]}
 for n in names[2:]:equality[n]={'current':sha(assets[n]),'previous':sha(old[n]),'whole_equal':assets[n]==old[n]}
 assert all(all(x.get('graphics_entries_equal',{}).values()) for x in equality.values())
 assert all(equality[n]['whole_equal'] for n in names[2:])
 gallery=normalized('shibuki');lookup={f['id']:f for f in gallery['frames']}
 arcs={n:Archive(assets[n]) for n in names[:2]};images={};checks=[];exceptions=[];sheets=[]
 forms=[('base','PL00_U.ARC',0,2),('fourth','PL00_U.ARC',15,2),('fourth_arm1','PL00_U.ARC',15,1),('ultimate_before','PL02_U.ARC',15,2),('ultimate_after','PL02_U.ARC',0,2)]
 for form,name,mask,arm in forms:
  folder=H/'sheets'/form;folder.mkdir(parents=True,exist_ok=True);images[form]={}
  for n in range(237):
   try:im,_=arcs[name].composite(n,15 if form=='ultimate_after' and 217<=n<=230 else mask,arm)
   except(ValueError,IndexError) as e:
    exceptions.append({'form':form,'ref':n,'reason':str(e)});im=Image.new('RGBA',(384,384))
   images[form][n]=im;f=lookup[f'{form}_{n:03}'];p=OUT/f.get('revised_path',f['path']);ref=Image.open(p).convert('RGBA')
   assert im.tobytes()==ref.tobytes(),(form,n,p)
   checks.append({'id':f['id'],'gallery_path':str(p.relative_to(ROOT)),'revised':bool(f.get('revised_path')),'rgba_sha256':sha(im.tobytes())})
  if form=='fourth_arm1':continue
  for group,refs in GROUPS.items():
   if group=='reserved_or_empty':continue
   for start in range(0,len(refs),24):
    selected=refs[start:start+24];p=folder/f'{group}_{start//24:02}.png'
    s=page([(f'{n:03} {GROUP_NAMES[group]}',images[form][n]) for n in selected],images[form][0],p)
    sheets.append({'form':form,'group':group,'refs':selected,**s})
 arm_diff=[n for n in range(237) if images['fourth'][n].tobytes()!=images['fourth_arm1'][n].tobytes()]
 if arm_diff:
  for start in range(0,len(arm_diff),24):
   sel=arm_diff[start:start+24];p=H/'sheets/fourth_arm1'/f'different_{start//24:02}.png'
   sheets.append({'form':'fourth_arm1','group':'arm_difference','refs':sel,**page([(f'{n:03} ARM1',images['fourth_arm1'][n]) for n in sel],images['fourth_arm1'][0],p)})
 partial=[]
 for n in (0,5,14,33,55,67,95,100,104,133,135,141,143,150,183,204,213,221):
  p=H/'partial'/f'ref{n:03}.png';p.parent.mkdir(exist_ok=True)
  items=[(f'ref{n:03} mask{mask:02}',arcs['PL00_U.ARC'].composite(n,mask,2)[0]) for mask in range(16)]
  partial.append({'ref':n,'masks':list(range(16)),'arm':2,**page(items,images['fourth'][0],p)})
 report={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':SHA,'assets':equality,'gallery_frame_checks':checks,
         'revised_count':sum(x['revised'] for x in checks),'main_sheets':sheets,'partial_sheets':partial,
         'arm1_vs_arm2_different_refs':arm_diff,'exceptions':exceptions,'actual_visual_review_completed':False}
 (H/'prepared_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'main_checks':len(checks),'revised':report['revised_count'],'sheets':len(sheets),'partial_sheets':len(partial),'arm_diff':arm_diff}))
if __name__=='__main__':main()
