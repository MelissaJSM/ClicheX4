import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import *
SEEN={
'shibuki':{'base':['run','air','dash','hurt_lowhp','arrival','shoot_special'], 'fourth':['run','air','wall','dash','hurt_lowhp','arrival','shoot_special','nova_hover'], 'ultimate_before':['run','air','dash','hurt_lowhp','arrival','ladder','shoot_special'], 'ultimate_after':['air','dash','hurt_lowhp','arrival','ladder','shoot_special','nova_hover']},
'nana':{'base':['run','air','hurt_lowhp','arrival','dash','shoot_special'], 'fourth':['run','air','wall','hurt_lowhp','arrival','dash','shoot_special','nova_hover'], 'ultimate_before':['run','air','wall','hurt_lowhp','arrival','dash','ladder','shoot_special'],'ultimate_after':['run','air','wall','hurt_lowhp','arrival','dash','ladder','shoot_special','nova_hover']}}
for character,forms in SEEN.items():
 manifest=json.loads((OUT/character/'manifest.json').read_text('utf8'));lists={}
 for form,groups in forms.items():
  seen=set(n for g in groups for n in GROUPS[g][:24]);records=[r for r in manifest['frames'] if r['form']==form and r['ref'] not in seen and r['status']!='unreconstructed']
  images=[Image.open(ROOT/r['path']).convert('RGBA') for r in records];boxes=[im.getbbox() for im in images if im.getbbox()]
  b=(min([156]+[q[0] for q in boxes])-3,min([156]+[q[1] for q in boxes])-3,max([164]+[q[2] for q in boxes])+3,max([180]+[q[3] for q in boxes])+3);w,h=(b[2]-b[0])*2,(b[3]-b[1])*2;cw=max(w,90);ch=h+24
  sheet=Image.new('RGB',(cw*10,ch*math.ceil(len(images)/10)),(26,32,43));dr=ImageDraw.Draw(sheet)
  for i,(r,im) in enumerate(zip(records,images)):
   x,y=i%10*cw,i//10*ch;dr.text((x+3,y+1),f"{r['ref']:03}",font=FONT,fill='white');pic=im.crop(b).resize((w,h),Image.Resampling.NEAREST);sheet.paste(pic,(x+(cw-w)//2,y+24),pic)
  path=OUT/character/f'{form}_remaining_review.png';sheet.save(path);lists[form]={'previously_viewed_groups_page0':groups,'remaining_review':relative(path),'remaining_refs':[r['ref'] for r in records],'previously_viewed_refs':sorted(seen),'window_world':[v-160 for v in b]}
 write(TASK/character/'visual_review_plan.json',lists)
 print(character,{f:len(r['remaining_refs']) for f,r in lists.items()})
