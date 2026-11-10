"""새 기본85..92를 기존 선택1..8의 원점으로 복사하는 별도 후보."""
from pathlib import Path
import sys, json, struct, hashlib
import numpy as np
H=Path(__file__).resolve().parent; ROOT=H.parents[2]; W=H.parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(W))
from scripts.export_x_consistency import Archive,page
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ultimate_production import repack_parts
from scripts.discover_inputs import psx_arc
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
from src.psx_ui_atlas import aliased_composition,local_composition,repack_frames,tile_pixels
from src.psx_static_effect import compose_static
from pack_selection_mirrors import repack as repack_mirrors
sha=lambda b:hashlib.sha256(b).hexdigest()
UI=W/'selection_shibuki_beam13/ST0E_U1.ARC'
OLD=H/'prepared_standing_special_base01/PL00_U.ARC'
NEW=H/'prepared_standing_fire_base01/PL00_U.ARC'
HASHES=['ea2167e98f8ae045c4353cca18cc571614e34949160cd85cc14ac9a6cb8e1c54','fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e','4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175']
DY={1:-1,2:0,3:0,4:0,5:0,6:-1,7:-2,8:0}
def decode(texture,parts,n):
    c=aliased_composition(parts,2,n)
    px,size,bb,_=compose_static(texture,local_composition(c))
    z=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);out=np.zeros((384,384),np.uint8)
    yy,xx=np.nonzero(z);out[yy+bb[1]+160,xx+bb[0]+160]=z[yy,xx]
    return out,c,(size,bb)
def shifted(z,dy):
    out=np.zeros_like(z);yy,xx=np.nonzero(z);assert np.all((yy+dy>=0)&(yy+dy<384));out[yy+dy,xx]=z[yy,xx];return out
def main(name):
    out=H/name;assert out.parent==H and not out.exists();out.mkdir()
    blobs=[p.read_bytes()for p in(UI,OLD,NEW)];assert [sha(b)for b in blobs]==HASHES
    ui=blobs[0];old,new=map(Archive,blobs[1:]);assert old.p==new.p
    g,p=entry(ui,0x10102),entry(ui,10);texture=g[90112:]
    offsets=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',p)[0]//4),p)
    lo=offsets[2];hi=min((v for v in offsets if v>lo),default=len(p));one=struct.pack('<I',4)+p[lo:hi]
    assert all(v!=lo for i,v in enumerate(offsets)if i!=2),'선택 은행 외부별칭 미해결'
    targets={};previous={};changes={};rows=[]
    owned={q['page']*256+q['tile']for n in DY for q in aliased_composition(p,2,n)['parts']}
    for n,dy in DY.items():
        ref=n+84;z,comp,meta=decode(texture,p,n);previous[n]=z
        assert np.array_equal(z,shifted(old.layer(ref)[0],dy)),('부모원점 불일치',n)
        target=shifted(new.layer(ref)[0],dy);targets[n]=target
        rr=[]
        for q in composition_frame(new.c,0,ref)['parts']:
            assert q['page']==0 and q['clut']==0 and not q['unknown_flags']
            rr.append(struct.pack('<BBbb',q['flags'],q['tile'],q['x'],q['y']+dy))
        changes[n]=b''.join(rr)
        rows.append({'selection_ref':n,'player_ref':ref,'transform':{'dx':0,'dy':dy,'flip_x':False},'old_parts':len(comp['parts']),'new_parts':len(rr),'old_indexed_sha256':sha(z.tobytes()),'new_indexed_sha256':sha(target.tobytes())})
    positioned,slack=repack_parts(one,0,changes);small={}
    for n,z in targets.items():
        _,size,bb,_=compose_static(texture,local_composition(composition_frame(positioned,0,n)))
        cut=z[bb[1]+160:bb[3]+160,bb[0]+160:bb[2]+160];assert np.count_nonzero(cut)==np.count_nonzero(z)
        small[n]=(cut.tobytes(),size)
    reserved=set(range(len(texture)//128))-owned
    ng,np_,packing=repack_mirrors(texture,one,positioned,0,small,{})
    # Helper compares the positioned input counts, not the historical counts.
    packing['positioned_part_counts_preserved']=packing.pop('original_part_counts_preserved')
    packing['historical_part_counts_preserved']=all(r['old_parts']==r['new_parts']for r in rows)
    newp=p[:lo]+np_[4:]+p[hi:]
    result=replace_entry(replace_entry(ui,0x10102,g[:90112]+ng),10,newp)
    assert len(result)==len(ui)and newp[:lo]==p[:lo]and newp[hi:]==p[hi:]
    assert entry(result,0x10102)[:90112]==g[:90112]
    count=aliased_composition(p,2,0)['bank_frame_count'];preserved=[];gpu=[]
    for n in range(count):
        z,oc,meta=decode(texture,p,n);actual,nc,newmeta=decode(ng,newp,n)
        if n in targets:
            assert np.array_equal(actual,targets[n]),('새선택 불일치',n)
            assert new.rgba(actual).tobytes()==new.rgba(targets[n]).tobytes()
            for q in nc['parts']:
                t=q['page']*256+q['tile'];px=tile_pixels(ng,t)
                assert t%16!=0 or not any(px[::16]),('U0',n,t)
                assert t%256>=16 or not any(px[:16]),('V0',n,t)
                gpu.append({'ref':n,'record':q['record_offset'],'tile':t})
        else:
            assert meta==newmeta and np.array_equal(z,actual),('비대상선택 변경',n)
            assert len(oc['parts'])==len(nc['parts'])
            for a,b in zip(oc['parts'],nc['parts']):assert p[a['record_offset']:a['record_offset']+4]==newp[b['record_offset']:b['record_offset']+4]
            preserved.append(n)
    changed_tiles=[t for t in range(len(texture)//128)if tile_pixels(texture,t)!=tile_pixels(ng,t)]
    assert set(changed_tiles)<=owned
    protected=[e for e in psx_arc(ui)if int(e['type'],16)not in(0x10102,10)]
    for e in protected:assert entry(ui,int(e['type'],16))==entry(result,int(e['type'],16))
    assert [(e['type'],e['offset'],e['size'])for e in psx_arc(ui)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(result)]
    plan=json.loads((W/'staging_br_v23.json').read_text('utf8'));source=ROOT/plan['source_bin']
    h=hashlib.sha256()
    with source.open('rb')as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    assert h.hexdigest()==plan['source_sha256']
    col=read_disc(source,('COL0E_U1.ARC',))[0]['COL0E_U1.ARC']
    assert entry(col,5)[512:544]==new.p[:32]
    dest=out/'ST0E_U1.ARC';dest.write_bytes(result)
    for n,dy in DY.items():
        actual=decode(ng,newp,n)[0]
        page([('기존 선택'+str(n),old.rgba(previous[n])),('새 선택'+str(n),new.rgba(actual)),('새 게임'+str(n+84),new.rgba(new.layer(n+84)[0]))],new.composite(0)[0],out/f'copy_{n:02}.png',cols=3,scale=5)
    report={'passed':True,'inputs':[{'path':q.relative_to(ROOT).as_posix(),'sha256':s}for q,s in zip((UI,OLD,NEW),HASHES)],'output':{'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(result)},'mapping':rows,'selected_frames':list(DY),'nonselected_ui_frames_exact':preserved,'nonselected_record_bytes_exact':True,'other_banks_and_entries_exact':True,'prefix_bytes_exact':90112,'parts_bank_bounds':[lo,hi],'parts_slack':slack,'original_target_owned_tiles':sorted(owned),'changed_tiles':changed_tiles,'packing':packing,'gpu_parts':gpu,'palette_proof':{'bin_path':plan['source_bin'],'bin_sha256':plan['source_sha256'],'COL0E_sha256':sha(col),'COL_entry5_row16_matches_game_CLUT0':True},'no_new_art':True,'builder_v4_guard_pending':True,'independent_pending':True,'new_mips_or_runtime':False}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'passed':True,'after':sha(result),'slack':slack,'changed_tiles':len(changed_tiles),'gpu_parts':len(gpu),'other_frames':len(preserved)}))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',default='selection_standing_sync01');main(p.parse_args().out)
