"""새 얼티밋 대시8몸체 위 원총구/수용34총열을 고정한 팔 편집 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from prepare_dash_body_layers import ARM
from prepare_dash_shot_inputs import GROUPS,SHOULDER

def main():
    o=H/'ultimate_dash_shot_inputs01';need(not o.exists(),'Fresh destination');o.mkdir();parent=H/'prepared_ultimate_air01/PL02_U.ARC';a=Archive(parent.read_bytes());bdir=H/'ultimate_dash_contacts04';gdir=H/'ultimate_dash_barrel_guard01';gmeta=json.loads((gdir/'report.json').read_text('utf8'));bmeta=json.loads((bdir/'report.json').read_text('utf8'));need(sha(a.data)==gmeta['parent_sha256']==bmeta['parent_sha256'],'Changed parent');rows=[]
    for pn,refs in enumerate(GROUPS,1):
        d=o/f'page{pn:02}';d.mkdir();sheet=Image.new('RGBA',(1536,1024))
        for row,(form,pal)in enumerate((('before',16),('after',0))):
            for col,n in enumerate(refs):
                p=bdir/f'{form}_{n:03}_indices.png';body=np.array(Image.open(p));gun=np.array(Image.open(gdir/f'{n+1:03}_indices.png'));guard=np.array(Image.open(gdir/f'{n+1:03}_mask.png'))>0;gm=next(r for r in gmeta['rows']if r['body_ref']==n and r['form']==form)
                need(sha(gun.tobytes())==gm['module_raw_sha256'] and sha(guard.tobytes())==gm['mask_raw_sha256'],'Module changed')
                whole=body.copy();whole[guard]=gun[guard];im=a.rgba(whole,pal);im.save(d/f'{form}_{n+1:03}_edit_target.png');cut=im.crop((112,124,208,188));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(whole),'Clipped target');sheet.alpha_composite(cut.resize((768,512),Image.Resampling.NEAREST),(col*768,row*512))
                rows.append({'page':pn,'form':form,'body_ref':n,'shot_ref':n+1,'palette_start':pal,'muzzle_world':gm['muzzle_world'],'shoulder_world':list(SHOULDER[n]),'body_file':p.relative_to(ROOT).as_posix(),'body_file_sha256':sha(p.read_bytes()),'barrel':gm,'edit_target_sha256':sha((d/f'{form}_{n+1:03}_edit_target.png').read_bytes())})
        sheet.save(d/'edit_target.png');guide=sheet.copy();draw=ImageDraw.Draw(guide)
        for row in range(2):
            for col,n in enumerate(refs):
                gm=next(r for r in gmeta['rows']if r['body_ref']==n and r['form']=='before');mx,my=gm['muzzle_world'];sx,sy=SHOULDER[n];poly=[(mx+8,my-4),(sx+3,sy-4),(sx+3,sy+6),(mx+8,my+6)]
                draw.line([(col*768+(x+48)*8,row*512+(y+36)*8)for x,y in poly+[poly[0]]],fill=(60,255,150,255),width=3)
                x0,y0,x1,y1=ARM[n];draw.rectangle((col*768+(x0+48)*8,row*512+(y0+36)*8,col*768+(x1+48)*8,row*512+(y1+36)*8),outline=(255,160,50,255),width=2)
        guide.save(d/'arm_guide.png')
        prompt=f'''Precise localized pixel sprite edit. Image1 is the EXACT accepted new detailed Tenko Shibuki body-and-gun target: TWO columns by TWO rows on transparent1536x1024. Each768x512 cell is a native96x64 game window enlarged8x, native world origin48,36. Image2 is ONLY a positioning guide: orange marks the existing bent FRONT arm to REPLACE, green shows the new firing arm route. Never draw guide lines in the output. Columns are body refs{refs}, becoming firing refs{tuple(n+1 for n in refs)}. All face LEFT.
Change ONLY the front/image-left arm. The small lavender buster already placed far LEFT is at the exact original firing position. Keep the gun muzzle, size, barrel shape and colors FIXED. Join its right end to the same shoulder with a naturally bent short arm. Replace the existing foreground arm, remove its old fist/sleeve from the old position; exactly TWO arms total. Keep the other rear/image-right hand unchanged. No third fist near the chin or waist. Preserve every other new head, golden eyes, gold heart sunglasses, fox ears, navy flower, detailed lavender hair, torso, hem, legs, sandals and their coordinates from Image1. Do not paste an older coarse body or move the whole character.
TOP BEFORE outfit: white/navy short jacket with short loose folded sleeves, tiny gold cuff detail and lavender shadows. BOTTOM AFTER: same skeleton/pose but NO JACKET and NO SLEEVES, bare upper arm and forearm connected to the existing sleeveless sailor swimsuit. Both outfits must use the SAME arm and wrist positions; the bare arm contour fits INSIDE the corresponding loose jacket sleeve contour. Do not grow or move the bottom arm outside the top sleeve. Hands and barrel endpoints identical in both rows. Keep the gun separate from cloth/skin: no skin-colored gun extension.
Render compact natural elbow/upperarm/forearm anatomy, not a long straight rectangular strip. At a nearby muzzle use a visibly bent elbow and hand under the barrel, not a stretched shoulder or floating forearm. Preserve original precise barrel position even if the arm must fold. Newly uncovered areas behind the removed bent arm should show the actual adjacent detailed cloth/hair or transparency; no flat skin/black patch. Preserve crisp coherent pixel clusters and current detail density without glow, gradients or hatching. No enlarged head, shifted feet, added objects, projectile, speed streak, dust, text or floor. EXACT four figures with locked cell origins, native scale and completely transparent margins.'''
        (d/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    write(o/'manifest.json',{'parent_sha256':sha(a.data),'body_report_sha256':sha((bdir/'report.json').read_bytes()),'barrel_report_sha256':sha((gdir/'report.json').read_bytes()),'layout':{'source':[1536,1024],'cell':[768,512],'native_cell':[96,64],'native_origin':[48,36],'scale':0.125,'crop':[112,124,208,188]},'rows':rows,'page_body_refs':[list(v)for v in GROUPS],'art_generated':False,'game_modified':False});print(json.dumps({'pages':4,'displays':16,'output':str(o)}))
if __name__=='__main__':main()
