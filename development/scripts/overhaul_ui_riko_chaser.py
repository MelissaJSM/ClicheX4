"""승인 리코 기준의 체이서 네 원화를28참조에 적용하는 제한 자원 패치."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_inventory import BUILDS,D,load
from scripts.overhaul_ui_fixes import require
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render,rgba,sha
from scripts.assemble_rin_chaser import make_world,fit,cropped
from scripts.prepare_rin_run import connected_groups
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_hurt_launch import compose_launch
from src.psx_frame_edit import edit_frame_set,frame_coverage,_apply_writes,read_indexed_png
from src.psx_compress import replace_stream,encode_stream

ART=D/'riko_chaser'
FAMILIES={14:range(14,22),22:range(22,30),30:range(30,38),38:range(38,42)}
POSITIONS={14:(-20,-20),22:(-19,-17),30:(-18,-24),38:(-15,-25)}
# Layer ownership boundaries in authored native pixel space. These exclude the
# complete green hair and the white lower coat; only the flowing cape moves.
CAPE_CUTS={14:(24,0,19),22:(21,0,16),30:(22,0,19),38:(24,11,22)}

def prepare(out):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh UI work directory required')
    assets,records=load('ver_buki_riko');arc=assets['PL01_U.ARC'];g=entry(arc,2);oldparts=entry(arc,3);parts=bytearray(oldparts)
    m=json.loads((ART/'prepared.json').read_text('utf8'));words=struct.unpack_from('<16H',entry(arc,9));require(list(words)==m['palette_words'],'Palette changed')
    require(sha((ART/'generated.png').read_bytes())==m['source_sha256'],'Authored sheet changed')
    bodies={};capes={};cuts={};streamdata={};worlds={};metadata={};checks=[]
    for n in FAMILIES:
        p=ART/m['frames'][str(n)]['file'];require(sha(p.read_bytes())==m['frames'][str(n)]['sha256'],'Native art changed')
        px,sz=read_indexed_png(p,words);a=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);yy,xx=np.indices(a.shape);x,y0,y1=CAPE_CUTS[n]
        mask=(xx>=x)&(yy>=y0)&(yy<=y1);cape=np.where(mask,a,0).astype(np.uint8);body=np.where(mask,0,a).astype(np.uint8)
        cy,cx=np.nonzero(cape);l,t=int(cx.min()),int(cy.min());cap=cape[t:int(cy.max())+1,l:int(cx.max())+1];edge=np.nonzero(cap[:,0])[0]
        require(len(edge)>0,'Missing cape attachment');capes[n]=(cap,float(edge.mean()));bodies[n]=body;cuts[n]={'x':l,'y':t,'anchor_y':float(edge.mean())+t,'rule':CAPE_CUTS[n]}
    for base,ids in FAMILIES.items():
        cs={n:composition_frame(oldparts,5,n) for n in ids};common=set.intersection(*[{p['tile'] for p in c['parts']} for c in cs.values()]);f=graphics_bank(g,1)['frames'][base]
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;require([q['index'] for q in graphics_bank(g,1)['frames'] if q['offset']==f['offset']]==list(ids),'Unexpected aliases')
        x,y=POSITIONS[base];body=make_world(bodies[base],x,y);body_layout=fit(body,[p for p in cs[base]['parts'] if p['tile'] in common]);root=cuts[base]
        phases={};layouts={}
        for phase,source in enumerate(FAMILIES):
            cap,ey=capes[source];layer=make_world(cap,x+root['x'],round(y+root['anchor_y']-ey));combined=np.where(body,body,layer).astype(np.uint8)
            require(len(connected_groups(combined>0))==1,f'Disconnected cape {base}:{phase}')
            ps=cs[base+phase]['parts'];first=next(i for i,p in enumerate(ps) if p['tile'] in common);early=ps[:first];late=[p for p in ps[first:] if p['tile'] not in common]
            layout=fit(layer,early);cy,cx=np.nonzero(layer);empty=(int(cx.max())-128+2,int(cy.min())-128);layout.update({p['tile']:empty for p in late});phases[phase]=layer;layouts[phase]=layout
        edits=[]
        for n,c in cs.items():
            phase=[0,1,2,3,1,2,3,1][n-base];dy=[0,0,0,0,1,2,1,-1][n-base];layout={**body_layout,**layouts[phase]};old_by={p['tile']:p for p in cs[base+phase]['parts']}
            for p in c['parts']:
                require(p['x']==old_by[p['tile']]['x'] and p['y']==old_by[p['tile']]['y']+dy,'Source timing/bob changed')
                xx,yy=layout[p['tile']];parts[p['record_offset']+2]=xx&255;parts[p['record_offset']+3]=(yy+dy)&255
            cc=composition_frame(parts,5,n);wb=np.roll(body,dy,axis=0);wc=np.roll(phases[phase],dy,axis=0);worlds[n]=np.where(wb,wb,wc).astype(np.uint8)
            for layer,selection in ((wb,common),(wc,set(layout)-common)):
                sub={**cc,'parts':[p for p in cc['parts'] if p['tile'] in selection]};px,sz,b=cropped(layer,sub);edits.append((sub,px,sz))
            metadata[str(n)]={'body_source':base,'cape_phase':phase,'cape_source':list(FAMILIES)[phase],'world_top_left':[x,y],'bob_y':dy}
        owned={s for c,_,_ in edits for q in frame_coverage(raw,f['tile_count'],c)[0] for s in q};seeded=_apply_writes(raw,dict.fromkeys(owned,0));packed=edit_frame_set(seeded,f['tile_count'],edits,overlap_policy='equal_sources')
        for n in ids:
            co=composition_frame(parts,5,n);require(compose_launch(packed,f['tile_count'],co)[:3]==cropped(worlds[n],co),'Layered readback mismatch')
            atlas,_,_=indexed_atlas(packed,f['tile_count'])
            for p in co['parts']:
                require(p['tile']%16!=0 or not any(atlas[(p['tile']//16*16+i)*256] for i in range(16)),'U0 seam occupied')
        streamdata[base]=packed
    # The four new paintings need more bytes than the original four slots.
    # Compact only this bounded existing region, ending BEFORE the separately
    # authored Ride Armor heads. All unedited compressed payloads remain exact.
    start,limit=135000,145718;bank=graphics_bank(g,1);changed=bytearray(g);cursor=start;locations={}
    for oldstart in sorted({f['offset'] for f in bank['frames'] if start<=f['offset']<limit}):
        f=next(f for f in bank['frames'] if f['offset']==oldstart);dec=decode_stream(g,oldstart,f['limit'],f['tile_count']*128)
        code=encode_stream(streamdata[f['index']]) if f['index'] in streamdata else g[oldstart:dec.end]
        require(cursor+len(code)<=limit,'Limited chaser region capacity exceeded')
        changed[cursor:cursor+len(code)]=code;locations[oldstart]=cursor
        checks.append({'first_frame':f['index'],'old_offset':oldstart,'new_offset':cursor,'old_bytes':dec.end-oldstart,'new_bytes':len(code),'unchanged_encoded_payload':f['index'] not in streamdata})
        cursor+=len(code)
    for f in bank['frames']:
        if f['offset'] in locations:struct.pack_into('<I',changed,bank['base']+4*f['index'],f['tile_count']<<20|(locations[f['offset']]-bank['base']))
    changed=bytes(changed)
    require(changed[145718:146344]==g[145718:146344],'Protected Ride Armor head region changed')
    require(changed[:graphics_bank(g,1)['base']]==g[:graphics_bank(g,1)['base']],'Other bank changed')
    checked=0;preserved=0
    for bank,pb in ((0,0),(1,5)):
        for f,nf in zip(graphics_bank(g,bank)['frames'],graphics_bank(changed,bank)['frames']):
            n=f['index'];before=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;after=decode_stream(changed,nf['offset'],nf['limit'],nf['tile_count']*128).data
            require(f['tile_count']==nf['tile_count'],'Tile count changed')
            if bank!=1 or not start<=f['offset']<limit:require(f['offset']==nf['offset'],'Outside-region stream address changed')
            if bank==1 and n in worlds:require(after==streamdata[next(base for base,ids in FAMILIES.items() if n in ids)],'Target readback mismatch')
            else:require(before==after and composition_frame(oldparts,pb,n)==composition_frame(parts,pb,n),'Protected reference changed');preserved+=1
            checked+=1
    permitted={p['record_offset']+axis for n in worlds for p in composition_frame(oldparts,5,n)['parts'] for axis in (2,3)}
    require(all(a==b or i in permitted for i,(a,b) in enumerate(zip(oldparts,parts))),'Non-position part changed')
    result=replace_entry(replace_entry(arc,2,changed),3,bytes(parts));require(len(result)==len(arc),'ARC size changed')
    out.mkdir();path=out/'PL01_U.ARC';path.write_bytes(result)
    verify={'decoded_references_checked':checked,'decoded_references_preserved':preserved,'changed_references':sorted(worlds),'parts_only_selected_xy':True,'palette_timing_exact':True,'limited_repack_region':[start,limit],'new_region_used_bytes':cursor-start,'region_free_bytes':limit-cursor,'outside_region_stream_addresses_exact':True,'protected_ridearmor_head_bytes':[145718,146344],'protected_ridearmor_head_exact':True,'incomplete_unselected_42_49_payload_exact':True,'compression':checks,'art_source_sha256':m['source_sha256'],'native_scale':m['scale'],'frames':metadata,'cape_cuts':cuts,'runtime_verified':False}
    proposal={'project':'ver_buki_riko','baseline':BUILDS['ver_buki_riko'][0],'baseline_sha256':BUILDS['ver_buki_riko'][1],'files':{'PL01_U.ARC':{'before':sha(arc),'after':sha(result),'size':len(result),'path':path.relative_to(ROOT).as_posix(),'record':records['PL01_U.ARC'],'changed_bytes':sum(a!=b for a,b in zip(arc,result))}},'issues':['C-04','R-03'],'checks':verify,'runtime_verified':False}
    for name,data in [('proposal.json',proposal),('verification.json',verify)]: (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
    board=Image.new('RGB',(8*256,4*280),(32,38,50));draw=ImageDraw.Draw(board)
    for row,(base,ids) in enumerate(FAMILIES.items()):
        for col,n in enumerate(ids):
            actual,_=render(result,1,5,n);p=rgba(actual,words);p.save(out/f'frame_{n}.png');pic=p.crop((112,112,208,208)).resize((256,256),Image.Resampling.NEAREST);board.paste(pic,(col*256,row*280+24),pic);draw.text((col*256+4,row*280+4),str(n),fill='white')
    board.save(out/'comparison.png');print(json.dumps({'output':str(out),'sha256':sha(result),'checked':checked,'preserved':preserved,'compression':checks}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();prepare(a.output)
