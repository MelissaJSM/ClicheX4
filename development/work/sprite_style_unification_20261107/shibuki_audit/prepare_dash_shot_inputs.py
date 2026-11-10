"""새 대시8몸체와 고정 총구의 앞팔 편집 입력. 96×64창, 배율8 불변."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from prepare_lowhp_final import compose
from prepare_dash_body_layers import ARM,P
GROUPS=((67,69),(71,75),(77,79),(81,83))
SHOULDER={67:(-6,-1),69:(-9,4),71:(-14,10),75:(-13,10),77:(-9,1),79:(-5,-1),81:(-4,-2),83:(-5,-3)}
def main():
    o=H/'dash_shot_inputs02';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive(P.read_bytes());bdir=H/'dash_body_layers01';gdir=H/'dash_barrel_guard02';meta=json.loads((gdir/'report.json').read_text('utf8'));rows=[]
    for pn,refs in enumerate(GROUPS,1):
        d=o/f'page{pn:02}';d.mkdir();sheet=Image.new('RGBA',(1536,1024));guide=sheet.copy();gd=ImageDraw.Draw(guide)
        for row,(form,mask)in enumerate((('base',0),('fourth',15))):
            for col,n in enumerate(refs):
                layers={b:np.array(Image.open(bdir/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};body=compose(a,layers,mask);gun=np.array(Image.open(gdir/f'{n+1:03}_indices.png'));guard=np.array(Image.open(gdir/f'{n+1:03}_mask.png'))>0
                gm=next(r for r in meta['rows']if r['body_ref']==n and r['form']==form);need(sha(gun.tobytes())==gm['module_index_sha256'] and sha(guard.tobytes())==gm['guard_sha256'],'Changed gun guard')
                whole=np.array(body);whole[guard]=np.array(a.rgba(gun))[guard];im=Image.fromarray(whole);im.save(d/f'{form}_{n+1:03}_edit_target.png')
                cut=im.crop((112,124,208,188));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(whole[:,:,3]),'Shot input clipping')
                tile=cut.resize((768,512),Image.Resampling.NEAREST);sheet.alpha_composite(tile,(col*768,row*512));guide.alpha_composite(tile,(col*768,row*512))
                sx,sy=SHOULDER[n];mx,my=gm['muzzle_world'];poly=[(mx+8,my-4),(sx+3,sy-4),(sx+3,sy+6),(mx+8,my+6)]
                gd.line([(col*768+(x+48)*8,row*512+(y+36)*8)for x,y in poly+[poly[0]]],fill=(60,255,150,255),width=3)
                x0,y0,x1,y1=ARM[n];gd.rectangle((col*768+(x0+48)*8,row*512+(y0+36)*8,col*768+(x1+48)*8,row*512+(y1+36)*8),outline=(255,160,50,255),width=2)
                rows.append({'page':pn,'form':form,'body_ref':n,'shot_ref':n+1,'muzzle_world':[mx,my],'shoulder_world':[sx,sy],'source_layers_sha256':{str(b):sha(v.tobytes())for b,v in layers.items()},'barrel_module':gm,'edit_target_sha256':sha((d/f'{form}_{n+1:03}_edit_target.png').read_bytes())})
        # Build annotations after all alpha compositing. A stale ImageDraw
        # handle across alpha_composite can drop copied pixels in Pillow.
        sheet.save(d/'edit_target.png');guide=sheet.copy();gd=ImageDraw.Draw(guide)
        for row in range(2):
            for col,n in enumerate(refs):
                gm=next(r for r in meta['rows']if r['body_ref']==n and r['form']=='base');mx,my=gm['muzzle_world'];sx,sy=SHOULDER[n]
                poly=[(mx+8,my-4),(sx+3,sy-4),(sx+3,sy+6),(mx+8,my+6)]
                gd.line([(col*768+(x+48)*8,row*512+(y+36)*8)for x,y in poly+[poly[0]]],fill=(60,255,150,255),width=3)
                x0,y0,x1,y1=ARM[n];gd.rectangle((col*768+(x0+48)*8,row*512+(y0+36)*8,col*768+(x1+48)*8,row*512+(y1+36)*8),outline=(255,160,50,255),width=2)
        guide.save(d/'arm_guide.png')
        prompt=f'''Precise localized sprite edit. Image1 is the EXACT new detailed Tenko Shibuki body-and-gun target: TWO columns by TWO rows, transparent1536x1024 canvas. Each768x512 cell is a native96x64 game window enlarged exactly8x; world origin is native48,36. Image2 is a positioning guide only: orange boxes mark the OLD BENT FOREGROUND ARM TO REMOVE, green marks the NEW FIRING ARM path. Never show the colored lines in output. Columns are original body poses{refs}, now firing refs{tuple(n+1 for n in refs)}. All four figures face LEFT.
ONLY replace the foreground/image-left bent arm with a short natural left-firing arm connected to the existing shoulder. Keep the exact new head, eyes, neck, lavender fox ears, layered hair, flower, torso, garment hem, rear/image-right arm and hand, both bent knees, all feet and every position in Image1. The lavender compact buster already placed at farLEFT is at the exact original muzzle position. Preserve its size, muzzle, every barrel pixel, colors and transparency; join its right edge to the same shoulder with an elbow/forearm and properly folded sleeve. REMOVE the old foreground fist/sleeve while creating the firing arm: exactly TWO arms/hands in the result. Never leave a third hand near the chin. The OTHER rear hand stays unchanged.
Top row BASE: short wide white/light-blue folded sleeve with red cuff, red shrine skirt. Bottom row FOURTH: SAME skeleton and pose, black/navy/purple folded sleeve with gold trim and fur collar, dark costume. Do not copy base white sleeves into Fourth. Preserve short full-bodied accepted proportions, small coherent sleeve volume and clean2~3tone fabric clusters. No stretched rectangular strip, long sausage arm, detached shoulder, pasted old coarse head, extra hand, enlarged body or shifted feet. Legitimately uncovered pixels behind the removed arm must contain the existing hair/cloth texture or transparency, not a flat flesh patch. Native fixed8x pixel-art style, clean dark outline and current detail density. Whole-figure scale and cell origins are LOCKED. Truly transparent background, no haze/glow, text, guide, floor, effects or extra pose.'''
        (d/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    write(o/'manifest.json',{'parent_sha256':sha(P.read_bytes()),'body_layers_report_sha256':sha((bdir/'registration.json').read_bytes()),'barrel_report_sha256':sha((gdir/'report.json').read_bytes()),'layout':{'source':[1536,1024],'cell':[768,512],'native_cell':[96,64],'native_origin':[48,36],'scale':0.125,'crop':[112,124,208,188]},'rows':rows,'page_body_refs':[list(v)for v in GROUPS],'new_shooting_art_generated':False,'resource_written':False})
    print(json.dumps({'out':str(o),'pages':len(GROUPS),'displays':len(rows)}))
if __name__=='__main__':main()
