import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from scripts.build_steam_selection import render_frame
W=ROOT/'work/steam_port_20261109';D=Path(__file__).parent
GAME=Path(json.loads((W/'backup_manifest.json').read_text('utf8'))['steam_root'])
def sha(b):return hashlib.sha256(b).hexdigest()
def find(a,magic,part):
    v=[e for e in a.entries if e.payload[:4]==magic and part.lower() in e.name.lower()]
    if len(v)!=1:raise ValueError((magic,part,len(v)))
    return v[0]
def main():
    D.mkdir(exist_ok=True);(D/'before').mkdir(exist_ok=True);(D/'frames').mkdir(exist_ok=True)
    installed=json.loads((W/'install_state.json').read_text('utf8'))
    (D/'install_state_before.json').write_text(json.dumps(installed,indent=2)+'\n')
    names=['st0e_01_eng.arc','st00_00_eng.arc','pl00_eng.arc','pl02_eng.arc','load_eng.arc','cliche_br_st0d_0x.arc','st0f_0x_eng.arc','st0f_0z_eng.arc','st0e_00_eng.arc']
    names += [f'cliche_br_hqx_{n:02}.arc' for n in range(1,18)]
    records=[];summary=[]
    expected={r['relative_path']:r['installed_sha256']for r in installed['files']}
    def emit(a,target,kind,b,f,t,p,row,rec,yoffset=0,tilebase=0):
        rec=bytearray(rec)
        for pos in range(0,len(rec),4):
            tid=(rec[pos]&3)*256+rec[pos+1]+tilebase
            rec[pos]=(rec[pos]&~3)|(tid//256);rec[pos+1]=tid%256
        tex=t.payload[:20]+t.payload[20+yoffset*256:]
        pal=p.payload[12:];im=render_frame(tex,rec,pal,row)
        ident=f'{kind}_{target[:-4]}_{b:02}_{f:02}'
        im.save(D/'frames'/(ident+'.png'))
        parts=list(struct.iter_unpack('<BBbb',rec));bounds=[min(r[2]for r in parts),min(r[3]for r in parts),max(r[2]+16 for r in parts),max(r[3]+16 for r in parts)]
        records.append({'id':ident,'target':target,'kind':kind,'bank':b,'frame':f,'texture_key':list(t.key),'palette_key':list(p.key),'row':row,'yoffset':yoffset,'record_hex':rec.hex(),'bounds':bounds,'image_sha256':sha(im.tobytes()),'size':list(im.size)})
    for target in names:
        raw=(GAME/'nativeDX10/X4/romPC'/target).read_bytes();assert sha(raw)==expected['nativeDX10/X4/romPC/'+target]
        (D/'before'/target).write_bytes(raw)
        a=SteamArc(raw);ts=sorted([e for e in a.entries if e.payload[:4]==b'TEX\0' and '\\chr\\' in e.name],key=lambda e:e.name)
        summary.append({'target':target,'entries':[{'name':e.name,'key':list(e.key),'magic':e.payload[:4].hex(),'length':len(e.payload)}for e in a.entries if e.payload[:4]in (b'TEX\0',b'PAT\0',b'COL\0')]})
        if target.startswith('st0e_01'):
            p=find(a,b'COL\0','\\stage\\col\\');bs=pat_frames(find(a,b'PAT\0','').payload)
            emit(a,target,'select',1,0,ts[1],p,4,bs[1][0])
        elif target.startswith('st00_00'):
            p=find(a,b'COL\0','COL00_0X');bs=pat_frames(find(a,b'PAT\0','').payload)
            for f,rec in enumerate(bs[11]):emit(a,target,'dialogue',11,f,ts[12],p,62,rec)
        elif target.startswith(('pl','load')):
            if not target.startswith('pl'):continue
            t=find(a,b'TEX\0','\\wsel\\');p=find(a,b'COL\0','\\wsel\\');bs=pat_frames(find(a,b'PAT\0','\\wsel\\').payload)
            # LOAD's PAT includes a cache owner alias; only player PAT owns variants.
            if not target.startswith('pl'):continue
            c=find(a,b'COF\0','\\wsel\\').payload;at=17+c[16]
            for f in range(38,44):emit(a,target,'pause',0,f,t,p,10,bs[0][f],struct.unpack_from('<I',c,at+4+f*4)[0],96)
        elif 'hqx_' in target or target=='cliche_br_st0d_0x.arc':
            p=find(a,b'COL\0','COL0D_0X');bs=pat_frames(find(a,b'PAT\0','').payload)
            for f,rec in enumerate(bs[2]):emit(a,target,'hq',2,f,ts[2],p,35,rec)
        elif target.startswith(('st0f','st0e_00')):
            from scripts.verify_steam_get_boss import render_background
            screen=6 if target.startswith('st0e') else 5
            render_background(a,screen).save(D/('background_'+target+'.png'))
            if target.startswith('st0e'):continue
            # Weapon-get character is in the background map; keep static atlas for inventory.
            p=find(a,b'COL\0','\\stage\\col\\');bs=pat_frames(find(a,b'PAT\0','').payload)
            for f,rec in enumerate(bs[0]):
                if rec:emit(a,target,'get_static',0,f,ts[0],p,0,rec)
    (D/'records.json').write_text(json.dumps(records,indent=2)+'\n');(D/'resources.json').write_text(json.dumps(summary,indent=2)+'\n')
    for kind in ('select','dialogue','pause','hq','get_static'):
        unique={}
        for r in records:
            if r['kind']==kind:unique.setdefault(r['image_sha256'],r)
        values=list(unique.values());cw,ch=(260,230) if kind=='hq' else (320,240);cols=6
        board=Image.new('RGB',(cols*cw,((len(values)+cols-1)//cols)*ch),'#252d40');d=ImageDraw.Draw(board)
        for i,r in enumerate(values):
            im=Image.open(D/'frames'/(r['id']+'.png'));im.thumbnail((cw-10,ch-35),Image.Resampling.NEAREST)
            # Nearest-neighbor magnification is a review-only display, not edited art.
            factor=min((cw-10)//im.width,(ch-35)//im.height)
            if factor>1:im=im.resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST)
            x=i%cols*cw;y=i//cols*ch;board.paste(im,(x+5,y+30),im);d.text((x+4,y+4),r['id'].replace('cliche_br_',''),fill='white')
        board.save(D/(kind+'_before.png'));print(kind,len(values),'unique',flush=True)
    print('frames',len(records))
if __name__=='__main__':main()
