"""Read current staged arcs; arrange exact pixels, without editing art."""
from pathlib import Path
import sys,json,hashlib,math
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,animation_map,usage
from scripts.c01_audio_build import read_disc
sha=lambda b:hashlib.sha256(b).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
D=W/'x_vehicle_review01';D.mkdir(exist_ok=False)
forms=[('base','PL00_U.ARC',0),('fourth','PL00_U.ARC',15),('ultimate_before','PL02_U.ARC',15),('ultimate_after','PL02_U.ARC',0)]
groups={'chaser':list(range(162,175)),'ride_head':list(range(184,204)),'nova_hover':list(range(213,231))}
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13)
manifest={'scope':'BR14/RN16 미수정 원픽셀의 차량/호버 추가 열람용. 생성만으로 실제 열람/완료가 아니다.',
          'origin':[160,160],'scale':3,'sources':{},'frames':[],'pages':[],
          'game_or_art_modified':False,'actually_viewed':False}
for char,planname in [('shibuki','staging_br_v14.json'),('nana','staging_rn_v16.json')]:
    plan=json.loads((W/planname).read_text('utf8'));arcs={}
    for name in ('PL00_U.ARC','PL02_U.ARC'):
        rec=plan['resources'][name];p=ROOT/rec['path'];data=p.read_bytes();assert sha(data)==rec['after'];arcs[name]=Archive(data)
        manifest['sources'][char+'/'+name]={'path':rel(p),'sha256':sha(data)}
    ims={};metadata={}
    for form,name,mask in forms:
        arc=arcs[name];idle,_=arc.composite(0,mask,2);ims[form,0]=idle
        for group,refs in groups.items():
            for ref in refs:
                actual_mask=15 if form=='ultimate_after' and 217<=ref<=230 else mask
                im,layers=arc.composite(ref,actual_mask,2);ims[form,ref]=im
                rec={'character':char,'form':form,'ref':ref,'group':group,'display_mask':actual_mask,
                     'rgba_sha256':sha(im.tobytes()),'bbox':im.getbbox(),'usage':usage(form,ref),
                     'layers':[{'bank':x['composition_bank'],'stream_offset':x['stream_offset'],'tile_count':x['tile_count'],'part_count':len(x['parts'])} for x in layers]}
                metadata[form,ref]=rec;manifest['frames'].append(rec)
    for group,refs in groups.items():
        # Exact full-form duplicates may share one viewing column. All IDs kept.
        keygroups={}
        for ref in refs:
            key=tuple(metadata[f,ref]['rgba_sha256'] for f,_,_ in forms)
            keygroups.setdefault(key,[]).append(ref)
        aliases=list(keygroups.values())
        for ix in range(0,len(aliases),5):
            batch=aliases[ix:ix+5];shown=[0]+[a[0] for a in batch]
            boxes=[ims[f,n].getbbox() for f,_,_ in forms for n in shown];boxes=[b for b in boxes if b]
            box=(min(145,min(b[0] for b in boxes)-3),min(125,min(b[1] for b in boxes)-3),max(180,max(b[2] for b in boxes)+3),max(184,max(b[3] for b in boxes)+3))
            assert min(box)>=0 and max(box)<=384
            pw,ph=(box[2]-box[0])*3,(box[3]-box[1])*3;cw=max(pw+12,170);ch=ph+48
            board=Image.new('RGB',(cw*len(shown),ch*4),(29,35,47));draw=ImageDraw.Draw(board)
            for row,(form,_,_) in enumerate(forms):
                for col,n in enumerate(shown):
                    x,y=col*cw,row*ch;labels='idle 0' if col==0 else ','.join(map(str,batch[col-1]))
                    draw.text((x+4,y+3),char+' '+form,font=font,fill='white');draw.text((x+4,y+20),labels,font=font,fill='#a8ced7')
                    dx=x+(cw-pw)//2;dy=y+44
                    draw.line((dx+(160-box[0])*3,dy,dx+(160-box[0])*3,dy+ph),fill='#42505c')
                    draw.line((dx,dy+(160-box[1])*3,dx+pw,dy+(160-box[1])*3),fill='#42505c')
                    src=ims[form,n].crop(box).resize((pw,ph),Image.Resampling.NEAREST);board.paste(src,(dx,dy),src)
            path=D/f'{char}_{group}_{ix//5:02}.png';board.save(path)
            manifest['pages'].append({'path':rel(path),'sha256':sha(path.read_bytes()),'character':char,'group':group,'ref_aliases':batch,'window':box,'scale':3})
    print(char,len(manifest['pages']),flush=True)
(D/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'pages':len(manifest['pages']),'frames':len(manifest['frames']),'manifest_sha256':sha((D/'manifest.json').read_bytes())}))
