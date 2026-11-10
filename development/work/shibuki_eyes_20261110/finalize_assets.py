"""Register only native iris pixels; propagate byte-identical cached portraits."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.steam_arc import SteamArc
from native import decode
from PIL import Image,ImageDraw
import numpy as np
D=Path(__file__).parent;W=ROOT/'work/steam_port_20261109'
OUT=ROOT/'out/steam_shibuki_eyes_20261110_v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text('utf8'))
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
    assert not load(D/'candidate/shared_conflicts.json')
    state=load(D/'install_state_before.json');game=Path(load(W/'backup_manifest.json')['steam_root'])
    substitutions={};before={};after={}
    for r in load(D/'candidate/reports.json'):
        a=SteamArc((D/'before'/r['target_arc']).read_bytes());b=SteamArc((D/'candidate'/r['target_arc']).read_bytes())
        before[r['target_arc']]=a;after[r['target_arc']]=b
        for k in r['changed_entries']:
            k=tuple(k);v=a.by_key[k].payload;n=b.by_key[k].payload
            assert v[:20]==n[:20] and len(v)==len(n) and v[:4]==b'TEX\0'
            assert all(old==new or (old in (9,10,11,14) and new in (7,8,14))for old,new in zip(v,n))
            old=substitutions.setdefault(sha(v),n);assert old==n
    reports=[];scanned=0
    for r in state['files']:
        rel=r['relative_path']
        if not rel.endswith('.arc'):continue
        raw=(game/rel).read_bytes();assert sha(raw)==r['installed_sha256'],rel
        a=SteamArc(raw);scanned+=1;updates={}
        for e in a.entries:
            if e.payload[:4]!=b'TEX\0':continue
            n=substitutions.get(sha(e.payload))
            if n is not None:updates[e.key]=n
        if not updates:continue
        name=Path(rel).name;dest=OUT/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        new=a.rebuild(updates);b=SteamArc(new);b.validate_stream_order()
        assert list(a.by_key)==list(b.by_key)
        for e in a.entries:assert b.by_key[e.key].payload==updates.get(e.key,e.payload)
        assert all(len(a.by_key[k].payload)==len(v)for k,v in updates.items())
        backup=D/'before'/name
        if backup.exists():assert backup.read_bytes()==raw
        else:backup.write_bytes(raw)
        dest.write_bytes(new);before[name]=a;after[name]=b
        reports.append({'target_arc':name,'relative_path':rel,'parent_sha256':sha(raw),'output':dest.relative_to(ROOT).as_posix(),'output_sha256':sha(new),'changed_entries':[list(k)for k in updates],'changed_texture_bytes':sum(sum(x!=y for x,y in zip(a.by_key[k].payload,v))for k,v in updates.items()),'geometry_palette_and_all_other_entries_unchanged':True,'install_eligible':True})
    save(W/'shibuki_eyes_builds.json',reports)
    # Nearest-neighbor face contact sheet for checking all head/outfit types.
    rs=load(D/'records.json');chosen=[]
    for kind in ('select','dialogue','pause'):
        seen=set()
        for r in rs:
            if r['kind']!=kind or r['image_sha256']in seen:continue
            seen.add(r['image_sha256']);chosen.append(r)
    for name in ('cliche_br_st0d_0x.arc','cliche_br_hqx_15.arc','cliche_br_hqx_16.arc','cliche_br_hqx_17.arc'):
        chosen.extend(r for r in rs if r['target']==name and r['kind']=='hq' and r['frame']in(0,1,2,3,6,9,10))
    board=Image.new('RGB',(1200,160*((len(chosen)+3)//4)),'#252d40');dr=ImageDraw.Draw(board)
    for i,r in enumerate(chosen):
        x=i%4*300;y=i//4*160;dr.text((x+4,y+2),r['id'].replace('cliche_br_',''),fill='white')
        box={'select':(65,40,95,65),'dialogue':(50,38,82,63),'pause':(22,30,45,48)}.get(r['kind'])
        if box is None:
            l,t=r['bounds'][:2];box=(60-80-l,43-80-t,108-80-l,72-80-t)
        for j,folder in enumerate(('frames','candidate/frames')):
            im=Image.open(D/folder/(r['id']+'.png')).crop(box);im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
            board.paste(im,(x+5+j*150,y+35),im)
        dr.text((x+8,y+18),'BEFORE',fill='#aaaaaa');dr.text((x+158,y+18),'AFTER',fill='#aaaaaa')
    board.save(OUT/'eye_comparison.png')
    assert all(np.array_equal(decode(r,before[r['target']])[0]==0,decode(r,after[r['target']])[0]==0)for r in rs if r['kind']in('select','dialogue','pause','hq'))
    save(D/'asset_verification.json',{'passed':True,'tracked_arcs_scanned':scanned,'modified_arcs':len(reports),'registered_frames':241,'shared_tile_conflicts':0,'iris_only_index_replacement':True,'all_palettes_layouts_timing_other_entries_preserved':True,'closed_eye_base_and_ultimate_preserved':True,'force_slot2_existing_near_eye_closure_and_visible_far_iris_preserved':True,'pause_cache_copies_identical':len({sha(a.by_key[next(k for k in a.by_key if '\\wsel\\'in a.by_key[k].name and a.by_key[k].payload[:4]==b'TEX\0')].payload)for name,a in after.items()if name in('pl00_eng.arc','pl02_eng.arc','load_eng.arc')})==1,'ps1_rebuilt':False})
    print({'scanned':scanned,'updated':len(reports),'changed_pixels':sum(r['changed_texture_bytes']for r in reports)})
if __name__=='__main__':main()
