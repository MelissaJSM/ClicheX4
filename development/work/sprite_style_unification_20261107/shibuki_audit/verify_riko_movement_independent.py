"""리코 새 이동 14참조를 원화부터 별도로 재구성해 패킹 결과와 대조한다."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;W=H.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
P=W/'riko/prepared_movement_clothes_v1';p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='03fa9ef5b662a71963f1b4e2be5a00fb7f18202e834e33f595a2b6b672c1d6a3'
assert sha(new)==p['after_sha256']=='df73f6a50dc13c9b5c00b8cc60ab474e7b725011ea896f94712013f7fe411e7a'
D=W/'riko/movement_clothes14';colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in struct.unpack_from('<16H',entry(old,9))],np.int32)
head_path=ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'
head=np.array(Image.open(head_path))[:19,12:35];green=np.isin(head,[4,8,14]);height,width=head.shape;inside=np.zeros_like(head,bool)
for y,row in enumerate(head):
    xs=np.flatnonzero(row)
    if len(xs):inside[y,xs.min():xs.max()+1]=True
assert int(inside.sum())==316
def anchor(a,lo,hi):
    choices=[]
    for y in range(lo,hi):
        for x in range(125,170):
            q=a[y:y+height,x:x+width]
            score=np.count_nonzero(q[green]!=head[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green)
            choices.append((int(score),x,y))
    return min(choices)
targets={};masks={};sources=[];registered_count=0
for page_number in (2,3,4,5):
    d=D/f'page{page_number}';info=json.loads((d/'inputs.json').read_text('utf8'));reg=json.loads((d/'registered01/registration.json').read_text('utf8'))
    assert info['sha256']==reg['source_sha256']==sha(old)
    ip=d/'generated.png';im=Image.open(ip).convert('RGBA');assert sha(ip.read_bytes())==reg['generated_sha256']
    columns,rows=info['grid'];nw=96*columns;scale=im.width/nw;nh=round(im.height/scale)
    assert [nw,nh]==reg['native_canvas'] and list(im.size)==reg['generated_dimensions'] and scale==reg['uniform_source_scale']
    rgba=np.array(im.resize((nw,nh),Image.Resampling.NEAREST));idx=(1+((rgba[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);idx[rgba[:,:,3]<128]=0
    assert abs(nh-96*rows)<=1
    canvas=np.zeros((96*rows,nw),np.uint8);canvas[:min(nh,len(canvas))]=idx[:len(canvas)]
    allowed=set(info.get('apply_only_refs',[r['ref']for r in info['frames']]))
    for r in reg['frames']:
        n=r['ref'];spec=next(v for v in info['frames']if v['ref']==n);cy,cx=divmod(spec['cell'],columns)
        previous=render(old,0,0,n)[0];generated=np.zeros_like(previous);generated[112:208,112:208]=canvas[cy*96:(cy+1)*96,cx*96:(cx+1)*96]
        score,hx,hy=anchor(previous,115,155);assert np.array_equal(previous[hy:hy+height,hx:hx+width][inside],head[inside])
        _,gx,gy=anchor(generated,115,170);dx,dy=hx-gx,hy-gy
        assert [hx-160,hy-160]==r['source_head_anchor'] and [dx,dy]==r['generated_translation']
        authored=np.zeros_like(previous);yy,xx=np.nonzero(generated);assert ((xx+dx>=0)&(xx+dx<384)&(yy+dy>=0)&(yy+dy<384)).all();authored[yy+dy,xx+dx]=generated[yy,xx]
        assert np.array_equal(authored,np.array(Image.open(d/'registered01'/f'b0_{n:03}_authored.png')))
        mask=np.zeros_like(previous,bool);mask[hy:hy+height,hx:hx+width]=inside
        assert np.array_equal(mask,np.array(Image.open(d/'registered01'/f'b0_{n:03}_head_mask.png'))>0)
        result=authored.copy();result[mask]=previous[mask]
        rp=ROOT/r['target'];assert sha(rp.read_bytes())==r['target_sha256'];assert np.array_equal(result,np.array(Image.open(rp)))
        assert r['contact_rects']==[] and r['hand_contact_exact']is None;registered_count+=1
        if n not in allowed:continue
        targets[n]=result;masks[n]=mask
        sources.append({'ref':n,'page':page_number,'generated_sha256':reg['generated_sha256'],'fixed_scale':scale,'source_translation':[dx,dy],'head_anchor_world':[hx-160,hy-160],'head316_exact':True,'hand_pixel_guard':False})
assert set(targets)=={3,4,7,9,10,11,12,13,15,16,17,18,19,20}
adjust={4:(164,-2,0),12:(169,0,-2),13:(169,0,-2),15:(164,0,-3),16:(164,0,-3),17:(168,0,-1),19:(174,0,-1),20:(175,0,-1)}
contact=json.loads((D/'contacts_probe01/registration.json').read_text('utf8'));assert contact['source_sha256']==sha(old)
for r in contact['frames']:
    n=r['ref'];q=targets[n];result=q.copy();row0,dx,dy=adjust.get(n,(0,0,0))
    if n in adjust:
        selected=np.indices(q.shape)[0]>=row0;yy,xx=np.nonzero(selected&(q>0));result[selected]=0;result[yy+dy,xx+dx]=q[yy,xx]
    assert r['lower_module_rows_from']==row0 and r['lower_module_translation']==[dx,dy] and r['original_pixels_copied']==0
    assert r['original_sole_y']==r['new_sole_y']==int(np.nonzero(result)[0].max())==int(np.nonzero(render(old,0,0,n)[0])[0].max())
    rp=ROOT/r['target'];assert sha(rp.read_bytes())==r['target_sha256'] and np.array_equal(result,np.array(Image.open(rp)));targets[n]=result
for r in p['registration']['frames']:
    rp=ROOT/r['target'];assert sha(rp.read_bytes())==r['target_sha256'] and np.array_equal(targets[r['ref']],np.array(Image.open(rp)))
assert set(p['target_references'])=={f'b0_{n:03}'for n in targets} and p['shared_support_refs']==[]
assert len(old)==len(new) and [(e['type'],e['offset'],e['size'])for e in psx_arc(old)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
others=0
for e in psx_arc(old):
    if int(e['type'],16)not in(2,3):assert old[e['offset']:e['offset']+e['size']]==new[e['offset']:e['offset']+e['size']];others+=1
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3)
assert bank_offsets(g)==bank_offsets(ng) and bank_offsets(c)==bank_offsets(nc)
assert g[bank_offsets(g)[1]:]==ng[bank_offsets(ng)[1]:]
semantic=lambda cp:[(r['flags'],r['tile'],r['x'],r['y'])for r in cp['parts']]
counts={'raw':0,'non_target_raw':0,'display':0,'non_target_display':0,'target_display':0,'partial_raw_parts_only':0,'gpu_parts':0,'new_boundary_alpha':0}
changes=[]
for b in (0,1):
    oldbank,newbank=graphics_bank(g,b),graphics_bank(ng,b);assert len(oldbank['frames'])==len(newbank['frames'])
    for f,z in zip(oldbank['frames'],newbank['frames']):
        n=f['index'];selected=b==0 and n in targets;counts['raw']+=1;assert f['tile_count']==z['tile_count']<=32
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
        cp,np_=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
        if not selected:assert raw==nr and semantic(cp)==semantic(np_);counts['non_target_raw']+=1
        if b==1 and n in range(42,50):counts['partial_raw_parts_only']+=1;continue
        was=render(old,b,b*5,n)[0];actual=render(new,b,b*5,n)[0];assert np.array_equal(actual,targets[n]if selected else was),(b,n,'display')
        counts['display']+=1
        if not selected:counts['non_target_display']+=1;continue
        counts['target_display']+=1;assert np.array_equal(actual[masks[n]],was[masks[n]])
        ta=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);tb=np.frombuffer(indexed_atlas(nr,z['tile_count'])[0],np.uint8).reshape(-1,256)
        for r in np_['parts']:
            t=r['tile'];x=t%16*16;y=t//16*16
            if t%16==0:assert not np.any((ta[y:y+16,x]==0)&(tb[y:y+16,x]>0))
            if r['flip_y']and t//16%16==0:assert not np.any((ta[y,x:x+16]==0)&(tb[y,x:x+16]>0))
            counts['gpu_parts']+=1
        changes.append({'ref':n,'changed_display_pixels':int(np.count_nonzero(was!=actual))})
assert counts['raw']==444 and counts['non_target_raw']==430 and counts['display']==436 and counts['non_target_display']==422
changedparts=[];keptparts=0
for b in range(len(bank_offsets(c))):
    count=composition_frame(c,b,0)['bank_frame_count'];assert count==composition_frame(nc,b,0)['bank_frame_count']
    for n in range(count):
        x,y=composition_frame(c,b,n),composition_frame(nc,b,n)
        if semantic(x)==semantic(y):keptparts+=1;continue
        assert b==0 and n in(11,15,16,17,20)
        changedparts.append({'bank':b,'ref':n,'before':semantic(x),'after':semantic(y)})
assert {r['ref']for r in changedparts}=={11,15,16,17,20}
for n in(5,6,8,14,147):assert np.array_equal(render(old,0,0,n)[0],render(new,0,0,n)[0])
recipe=json.loads((P/'static_effects.json').read_text('utf8'));pr=json.loads((ROOT/p['source_arc']).with_name('static_effects.json').read_text('utf8'))
assert recipe['parts_sha256']==sha(nc) and {k:v for k,v in recipe.items()if k!='parts_sha256'}=={k:v for k,v in pr.items()if k!='parts_sha256'}
report={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'proposal_sha256':sha((P/'proposal.json').read_bytes()),'raw_source_art_reconstructions':registered_count,'selected_source_art_reconstructions':len(targets),'sources':sources,'lower_module_adjustments':{str(k):list(v)for k,v in adjust.items()},'source_pixels_recolored_or_scaled':False,'original_boot_pixels_copied':0,'all_original_sole_y_exact':True,'counts':counts,'changes':changes,'non_target_composition_refs_exact':keptparts,'changed_compositions':changedparts,'other_entries_exact':others,'bank1_graphics_bytes_exact':True,'palette_audio_timing_exact':True,'locked_refs_exact':[5,6,8,14,147],'static_recipe_sha256':sha((P/'static_effects.json').read_bytes()),'static_recipe_only_parts_hash_rebound':True,'producer_packer_or_generation_called':False,'runtime_verified':False,'actual_viewed_packed_sheets':[],'limitations':['손 접점 픽셀은 원래 손으로 고정한 것이 아니며 hand_contact_exact=None이다.','부분 VRAM bank1 42..49는 원시와 조립 보존만 검사했다.','원래 MIPS/GPU 실행 및 실제 플레이는 루트의 별도 검증이다.','15/16의 옷단/허벅지 겹침은 정적 검토에 더하여 연속 보행 검토가 남아 있다.']}
report['actual_viewed_packed_sheets']=[{'path':str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT)),'sha256':sha((P/f'{mode}_readback_{i:02}.png').read_bytes())}for mode in('normal','black')for i in range(4)]
report['visual_notes']=['실제 ARC 재독출 일반/블랙 각4장 총8장을 직접 열람했다. 같은 대기 머리에 칼라·소매·허리·부츠의 구조가 이어지고, 기존 큰 흰 면이 세분화되었다.','블랙에서도 회색 중간톤이 옷단과 관절을 나누며, 팔·몸통·허벅지의 새 단절은 보이지 않는다.','15/16의 피부 띠와 옷단 겹침은 정적 재독출에서도 연결되어 있다. 연속 보행의 부드러움은 이 검사만으로 완료 처리하지 않는다.']
O=H/'riko_movement_independent';O.mkdir(exist_ok=True);(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':counts,'registered_count':registered_count,'report':str(O/'verification.json')}))
