"""체이서 몸/리본을 원작 공유 타일에 별도로 넣고 최종28그림을 대조한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_chaser import OUT,PARENT
from scripts.build_rin_idle import entry,sha
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.prepare_rin_run import connected_groups
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_hurt_launch import compose_launch
from src.psx_frame_edit import edit_frame_set
from src.sprite_window_fit import fit_windows

FAMILIES={14:range(14,22),22:range(22,30),30:range(30,38),38:range(38,42)}
POSITIONS={14:(-20,-20),22:(-19,-21),30:(-18,-24),38:(-15,-26)}
# Authored layer ownership cut, inspected on the enlarged native sprites.
# Cut follows transparent separation between the flying ribbon and back.
CUTS={14:(27,14,.27),22:(27,13,.44),30:(27,16,.40),38:(27,16,.55)}

def make_world(a,x,y):
    w=np.zeros((256,256),np.uint8);w[128+y:128+y+a.shape[0],128+x:128+x+a.shape[1]]=a;return w

def fit(layer,parts):
    yy,xx=np.nonzero(layer);left=int(xx.min());top=int(yy.min());a=layer[top:int(yy.max())+1,left:int(xx.max())+1]
    result=fit_windows(parts,a,left-128,top-128)
    if result is None:raise ValueError('Layer does not fit original tile count')
    return {p['tile']:(x,y) for p,x,y in result}

def cropped(w,c):
    x=min(p['x'] for p in c['parts']);y=min(p['y'] for p in c['parts']);r=max(p['x']+16 for p in c['parts']);b=max(p['y']+16 for p in c['parts']);a=w[128+y:128+b,128+x:128+r]
    if np.count_nonzero(w)!=np.count_nonzero(a):raise ValueError('Layer cropped')
    return a.tobytes(),(r-x,b-y),(x,y,r,b)

def main():
    pm=json.loads((PARENT/'manifest.json').read_text());arc=(PARENT/'modified.arc').read_bytes();m=json.loads((OUT/'prepared.json').read_text());guide=json.loads((OUT/'guide.json').read_text());words=m['palette_words']
    if sha(arc)!=pm['modified_archive_sha256'] or digest(OUT/'generated.png')!=m['source_sha256']:raise ValueError('Source changed')
    g=entry(arc,2)[1];oldparts=entry(arc,3)[1];parts=bytearray(oldparts);bodies={};tails={};cut_info={}
    for n,r in m['frames'].items():
        n=int(n);p=OUT/r['file']
        if digest(p)!=r['sha256']:raise ValueError('Prepared art changed')
        a=np.array(Image.open(p));yy,xx=np.indices(a.shape);x,cut,slope=CUTS[n];mask=(xx>=x)&(yy<=cut+(xx-x)*slope)
        ribbon=np.where(mask,a,0).astype(np.uint8);body=np.where(mask,0,a).astype(np.uint8)
        ry,rx=np.nonzero(ribbon);l=int(rx.min());t=int(ry.min());ribbon=ribbon[t:int(ry.max())+1,l:int(rx.max())+1]
        ey=np.nonzero(ribbon[:,0])[0]
        if not len(ey):raise ValueError('Missing ribbon attachment')
        tails[n]=(ribbon,float(ey.mean()));bodies[n]=body;cut_info[str(n)]={'split_x':l,'split_top':t,'anchor_y':float(ey.mean())+t,'polygon_rule':CUTS[n]}
    frames={};stream_records=[];worlds={};body_checks=[]
    for base,ids in FAMILIES.items():
        cs={n:composition_frame(oldparts,5,n) for n in ids};body_tiles=set.intersection(*[set(p['tile'] for p in c['parts']) for c in cs.values()]);cbase=cs[base]
        f=graphics_bank(g,1)['frames'][base];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        aliases=[q['index'] for q in graphics_bank(g,1)['frames'] if q['offset']==f['offset']]
        if aliases!=list(ids):raise ValueError('Unexpected stream alias')
        x,y=POSITIONS[base];body=make_world(bodies[base],x,y);body_layout=fit(body,[p for p in cbase['parts'] if p['tile'] in body_tiles]);phase_layers={};phase_layout={}
        # Four generated ribbon shapes, translated to the same attached root.
        root=cut_info[str(base)];anchor_x=x+root['split_x'];anchor_y=y+root['anchor_y']
        for phase,source in enumerate(FAMILIES):
            tail,ey=tails[source];tx=anchor_x;ty=round(anchor_y-ey);ribbon=make_world(tail,tx,ty)
            w=np.where(body,body,ribbon).astype(np.uint8)
            if len(connected_groups(w>0))!=1:raise ValueError(f'Ribbon disconnected {base}:{phase}')
            phase_layers[phase]=ribbon;ps=cs[base+phase]['parts'];first_body=next(i for i,p in enumerate(ps) if p['tile'] in body_tiles)
            early=ps[:first_body];late=[p for p in ps[first_body:] if p['tile'] not in body_tiles]
            # Keep the original draw order: ribbon is behind the body. Its
            # complete source pixels remain stored even when the shoulder
            # naturally occludes them. Late hair tiles are kept transparent.
            phase_layout[phase]=fit(ribbon,early)
            yy,xx=np.nonzero(ribbon);empty=(int(xx.max())-128+2,int(yy.min())-128)
            phase_layout[phase].update({p['tile']:empty for p in late})
        edits=[];meta=[]
        for n,c in cs.items():
            phase=([0,1,2,3,1,2,3,1][n-base]);dy=([0,0,0,0,1,2,1,-1][n-base]);layout={**body_layout,**phase_layout[phase]}
            old_by={p['tile']:p for p in cs[base+phase]['parts']}
            for p in c['parts']:
                if p['x']!=old_by[p['tile']]['x'] or p['y']!=old_by[p['tile']]['y']+dy:raise ValueError('Unexpected source bob')
                xx,yy=layout[p['tile']];parts[p['record_offset']+2]=xx&255;parts[p['record_offset']+3]=(yy+dy)&255
            cc=composition_frame(parts,5,n);wb=np.roll(body,dy,axis=0);wr=np.roll(phase_layers[phase],dy,axis=0);w=np.where(wb,wb,wr).astype(np.uint8);worlds[n]=w
            for layer,select in ((wb,body_tiles),(wr,set(layout)-body_tiles)):
                sub={**cc,'parts':[p for p in cc['parts'] if p['tile'] in select]};px,sz,b=cropped(layer,sub);edits.append((sub,px,sz))
            px,sz,b=cropped(w,cc);path=OUT/f'frame_{n}.png';save_image(px,sz,words,path);frames[str(n)]={'file':path.name,'sha256':digest(path),'bounds':b,'body_source':base,'ribbon_phase':phase,'ribbon_source':list(FAMILIES)[phase],'bob_y':dy,'opaque_pixels':int(np.count_nonzero(w))};meta.append(n)
        # All referenced body/ribbon texels are owned. Preserve any unreferenced
        # tile verbatim. Layer editing starts from equal transparent sources.
        from src.psx_frame_edit import frame_coverage,_apply_writes
        owned={s for c,_,_ in edits for q in frame_coverage(raw,f['tile_count'],c)[0] for s in q}
        seeded=_apply_writes(raw,dict.fromkeys(owned,0));packed=edit_frame_set(seeded,f['tile_count'],edits,overlap_policy='equal_sources')
        for n in ids:
            c=composition_frame(parts,5,n);actual=compose_launch(packed,f['tile_count'],c);expected=cropped(worlds[n],c)
            if actual[:3]!=expected:raise ValueError('Layered final readback differs')
            atlas,_,_=indexed_atlas(packed,f['tile_count'])
            for q in c['parts']:
                if q['tile']%16==0 and any(atlas[(q['tile']//16*16+yy)*256] for yy in range(16)):raise ValueError('U0 edge occupied')
        (OUT/f'stream_{base}.bin').write_bytes(packed);stream_records.append({'base':base,'references':list(ids),'file':f'stream_{base}.bin','sha256':sha(packed),'source_sha256':sha(raw),'body_tiles':sorted(body_tiles),'unused_source_texels_preserved':True,'native_root':[anchor_x,anchor_y]})
    permitted={p['record_offset']+axis for n in worlds for p in composition_frame(oldparts,5,n)['parts'] for axis in (2,3)}
    changes=[i for i,(a,b) in enumerate(zip(oldparts,parts)) if a!=b]
    if not set(changes)<=permitted:raise ValueError('Non-position part changes')
    (OUT/'composition_entry.bin').write_bytes(parts);report={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha(arc),'frames':frames,'streams':stream_records,'parts_sha256':sha(parts),'coordinate_change_count':len(changes),'ribbon_cut':cut_info,'uniform_scale':m['scale'],'common_head_scale_adjustment':.9,'per_pose_scaling':False,'body_bob_preserved':True,'part_counts_tiles_flags_order_preserved':True,'issues':[],'runtime_verified':False}
    (OUT/'recipe.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
    sheet=Image.new('RGB',(8*256,4*280),(32,35,44));d=ImageDraw.Draw(sheet)
    for row,(base,ids) in enumerate(FAMILIES.items()):
        for col,n in enumerate(ids):
            w=worlds[n][80:176,80:176];p=save_image(w.tobytes(),(96,96),words,OUT/f'world_{n}.png').convert('RGBA').resize((256,256),Image.Resampling.NEAREST);sheet.paste(p,(col*256,row*280+24),p);d.text((col*256+8,row*280+4),str(n),fill='white')
    sheet.save(OUT/'comparison.png');print(json.dumps({'frames':len(frames),'streams':len(stream_records),'coordinate_changes':len(changes)}))

if __name__=='__main__':main()
