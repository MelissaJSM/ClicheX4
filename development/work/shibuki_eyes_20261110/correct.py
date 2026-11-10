"""Register generated iris colors in indexed game resources, preserving geometry."""
import hashlib,json,struct,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from native import D,decode,world
from audit import find
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from scripts.build_steam_selection import render_frame
from scripts.verify_steam_get_boss import render_background
def sha(b):return hashlib.sha256(b).hexdigest()

# Bounds were inspected in the native canvas. They deliberately exclude skin,
# white highlights, eyelashes, and ornaments which share iris palette entries.
ROIS={
 'select':((74,48,80,55),(86,53,90,58)),
 'dialogue':((60,46,65,52),(73,51,77,55)),
 'pause':((29,37,32,41),(38,40,41,43)),
 'base':{0:((83,55,86,59),(89,55,92,59)),3:((85,55,88,58),(89,55,92,58)),6:((89,65,93,68),(94,65,98,68)),9:((68,63,71,65),(73,63,77,65))},
 'force':{0:((84,52,87,55),(89,53,92,56)),3:((84,52,87,55),(89,53,92,56)),6:((89,63,92,66),(95,63,98,66)),9:((67,62,71,64),(74,62,78,65))},
 'jacket':{0:((86,52,89,55),(91,52,94,55)),3:((86,52,89,55),(91,52,94,55)),6:((93,62,97,65),(99,62,103,65)),9:((68,61,71,63),(74,61,78,64))},
 'swim':{0:((86,52,89,54),(91,52,95,54)),3:((86,52,89,54),(91,52,95,54)),6:((93,61,97,64),(100,61,104,64)),9:((69,61,72,64),(75,61,79,64))}
}
WARM=[9,10,11,14]
def boxes(r):
    if r['kind'] in ('select','dialogue','pause'):return ROIS[r['kind']]
    if r['kind']!='hq':return []
    n=r['frame'];state=int(r['target'][-6:-4])if 'hqx_'in r['target'] else 0
    kind='jacket' if state==16 else 'swim' if state==17 else 'force' if state&1 else 'base'
    # Force slot 2 closes the near eye but retains its tiny far-eye pixel.
    if n==2 and kind!='force':return []
    group=0 if n in (0,1,2,10,11) else 3 if n<6 else 6 if n<9 else 9
    bb=ROIS[kind][group]
    if n==10:bb=tuple((160-x1,y0,160-x0,y1)for x0,y0,x1,y1 in bb)
    left,top=r['bounds'][:2]
    return tuple((x0-80-left,y0-80-top,x1-80-left,y1-80-top)for x0,y0,x1,y1 in bb)

def recolor(px,bb):
    result=px.copy();changes={}
    for side,(x0,y0,x1,y1)in enumerate(bb):
        for y in range(y0,y1):
            for x in range(x0,x1):
                value=int(px[y,x])
                if value not in WARM or (side==0 and value==11):continue
                # Color registration to the existing 16-color native palette.
                new=(8 if value in (9,10)else 7)if side==0 else 14
                if value!=new:result[y,x]=new;changes[x,y]=(value,new,side)
    return result,changes

def background_changes(a,screen):
    # Assemble the screen's ownership map using its original tile/palette map.
    t=find(a,b'TEX\0','\\dds\\');mp=find(a,b'OMP\0','');cells=find(a,b'OCL\0','')
    px=np.zeros((256,256),np.uint8);owners=np.full((256,256),-1,np.int32)
    for j,v in enumerate(struct.unpack_from('<256H',mp.payload,12+screen*512)):
        if not v:continue
        attr=struct.unpack_from('<I',cells.payload,12+(v&16383)*4)[0];tile=attr>>16&4095;page,local=divmod(tile,256)
        tx=(page%8)*256+(local%16)*16;ty=(page//8)*256+(local//16)*16
        for dy in range(16):
            for dx in range(16):
                pos=20+(ty+(15-dy if v&32768 else dy))*2048+tx+(15-dx if v&16384 else dx)
                yy=j//16*16+dy;xx=j%16*16+dx;px[yy,xx]=t.payload[pos];owners[yy,xx]=pos
    # Weapon-get/title share the same action illustration and native canvas.
    bb=((96,49,101,55),(107,53,112,58))
    new,changes=recolor(px,bb)
    return t,{int(owners[y,x]):(old,value)for (x,y),(old,value,_)in changes.items()},changes

def main():
    out=D/'candidate';out.mkdir(exist_ok=True);(out/'frames').mkdir(exist_ok=True)
    rows=json.loads((D/'records.json').read_text());arcs={p.name:SteamArc(p.read_bytes())for p in (D/'before').glob('*.arc')}
    edits={};desired={};proof=[]
    for r in rows:
        if r['kind']not in ('select','dialogue','pause','hq'):continue
        px,owners=decode(r,arcs[r['target']]);new,changes=recolor(px,boxes(r));desired[r['id']]=new
        key=r['target'],tuple(r['texture_key']);edits.setdefault(key,{})
        for (x,y),(old,value,side)in changes.items():
            pos=int(owners[y,x]);assert pos>=20
            prior=edits[key].setdefault(pos,(old,value))
            if prior!=(old,value):raise ValueError(('Shared iris color conflict',r['id'],pos,prior,(old,value)))
        proof.append({'id':r['id'],'iris_changes':[[x,y,*c]for (x,y),c in changes.items()]})
    # Shared cache in LOAD must remain byte-identical to PL00/PL02.
    ref=next((k,v)for k,v in edits.items()if k[0]=='pl00_eng.arc')
    key=('load_eng.arc',ref[0][1]);edits[key]=dict(ref[1])
    assert arcs[key[0]].by_key[key[1]].payload==arcs['pl00_eng.arc'].by_key[key[1]].payload
    for name in ('st0f_0x_eng.arc','st0f_0z_eng.arc','st0e_00_eng.arc'):
        a=arcs[name];t,changes,coords=background_changes(a,6 if name.startswith('st0e')else 5);edits[name,t.key]=changes
        proof.append({'id':'background_'+name,'iris_changes':[[x,y,*c]for (x,y),c in coords.items()]})
    candidates={};updates_by_payload={};reports=[]
    for name,a in arcs.items():
        updates={}
        for (target,key),changes in edits.items():
            if target!=name or not changes:continue
            b=a.by_key[key].payload;new=bytearray(b)
            for pos,(old,value)in changes.items():
                assert b[pos]==old;new[pos]=value
            updates[key]=bytes(new);prior=updates_by_payload.setdefault(sha(b),bytes(new))
            assert prior==bytes(new),'Equivalent source has different output'
        if updates:
            raw=a.rebuild(updates);b=SteamArc(raw);b.validate_stream_order();candidates[name]=b
            for e in a.entries:assert b.by_key[e.key].payload==updates.get(e.key,e.payload)
            (out/name).write_bytes(raw)
            reports.append({'target_arc':name,'parent_sha256':sha(a.raw),'output_sha256':sha(raw),'changed_texture_bytes':sum(sum(x!=y for x,y in zip(a.by_key[k].payload,v))for k,v in updates.items()),'changed_entries':[list(k)for k in updates]})
    mismatches=[]
    for r in rows:
        if r['id']not in desired:continue
        got,_=decode(r,candidates.get(r['target'],arcs[r['target']]))
        if not np.array_equal(got,desired[r['id']]):
            yy,xx=np.nonzero(got!=desired[r['id']]);mismatches.append({'id':r['id'],'positions':list(zip(xx.tolist(),yy.tolist()))})
        a=candidates.get(r['target'],arcs[r['target']]);t=a.by_key[tuple(r['texture_key'])].payload;p=a.by_key[tuple(r['palette_key'])].payload[12:]
        im=render_frame(t[:20]+t[20+r['yoffset']*256:],bytes.fromhex(r['record_hex']),p,r['row']);im.save(out/'frames'/(r['id']+'.png'))
    for name in ('st0f_0x_eng.arc','st0f_0z_eng.arc','st0e_00_eng.arc'):
        render_background(candidates.get(name,arcs[name]),6 if name.startswith('st0e')else 5).save(out/('background_'+name+'.png'))
    (out/'iris_changes.json').write_text(json.dumps(proof,indent=2)+'\n');(out/'reports.json').write_text(json.dumps(reports,indent=2)+'\n')
    (out/'shared_conflicts.json').write_text(json.dumps(mismatches,indent=2)+'\n')
    assert not mismatches, 'Unintended shared-tile changes'
    print(json.dumps({'candidate_arcs':len(reports),'rendered_frames':len(desired),'shared_conflicts':len(mismatches),'changed_tex_bytes':sum(r['changed_texture_bytes']for r in reports)}))
    # Comparison boards are only previews; no resizing is written to game assets.
    for kind in ('select','dialogue','pause'):
        unique={r['image_sha256']:r for r in rows if r['kind']==kind};cw,ch=320,240;values=list(unique.values());board=Image.new('RGB',(cw*6,ch*((len(values)+5)//6)),'#252d40');d=ImageDraw.Draw(board)
        for i,r in enumerate(values):
            im=Image.open(out/'frames'/(r['id']+'.png'));factor=min((cw-10)//im.width,(ch-30)//im.height);im=im.resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST);x=i%6*cw;y=i//6*ch;board.paste(im,(x,y+25),im);d.text((x,y),r['id'],fill='white')
        board.save(out/(kind+'.png'))
if __name__=='__main__':main()
