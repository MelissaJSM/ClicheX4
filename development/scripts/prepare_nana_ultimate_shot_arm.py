"""사격 팔의 검은 소매와 사격 전용 분리 점8픽셀을 수정한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_nana_fourth_pilot import entry,require,render,write
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_nana_ultimate_run import verify
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records,fast_fit
from src.psx_paired_layout import pack_variant_pair
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.prepare_riko_ui import replace_entry
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,composition_frame,decode_stream,indexed_atlas
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
D=ROOT/'work/ver_rin_nana/nana_ultimate_armor'
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_run_hand_20261104T070400903192Z'
PARENT_SHA='c81bd78b87bd15b87458cb2852ab8118b2696015e18037a6f88498beb96c69c2'
ARC_SHA='899e6e5a9ba16bc5c166ac96492ac1141756594e8e8b786057d4b0544b47607b'
SOURCE_SHA='229eab7f7882f956bd45ee8bbf59ca088f854da2b4ccf814a7d6b37aa909ab7f'
FRAMES=[*range(1,33),85,86]
SHOTS=[*range(2,33,2),85,86]
SPECKS={2:[(70,83),(71,83),(72,83)],4:[(70,83),(71,83),(72,83)],26:[(67,84),(68,84)]}

def correct_base(arc):
    """기존 기본형 타일을 재분할해 사격에서만 분리 점을 지운다."""
    require(sha256(arc)==ARC_SHA,'Unsupported base correction source')
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};changes={};proof=[]
    for n in SPECKS:
        coords=SPECKS.get(n,[])
        f=bank['frames'][n];ns=[x['index'] for x in bank['frames'] if x['offset']==f['offset']];require(ns==[n-1,n],'Unexpected base aliases');raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        protected={q['tile'] for v in ns for cb in (6,7,8) for q in composition_frame(c,cb,v)['parts']};pool={q['tile'] for v in ns for q in composition_frame(c,0,v)['parts']}-protected
        images=[raster(g,c,0,0,v) for v in ns]
        for x,y in coords:require(images[1][y,x] in (1,2),'Unexpected speck color');images[1][y,x]=0
        try:new,rr=pack_shared(raw,f['tile_count'],images,pool,[len(pool)]*2)
        except ValueError:
            if coords:raise
            continue
        for v,parts in zip(ns,rr):
            changes[v]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80) for t,x,y,flag in parts);replacements[v]=encode_stream(new)
        proof.append({'frame':n,'removed_pixels':coords,'base_repacked_frames':ns,'base_tile_pool':sorted(pool),'parts':[len(p) for p in rr],'regular_and_other_layers_preserved':True})
    nc,slack=repack_parts(c,0,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc)
    # Independently compare every displayed base/other-part layer, including aliases.
    for n in range(len(bank['frames'])):
        for cb in (0,6,7,8):
            try:old=raster(g,c,0,cb,n)
            except ValueError:
                require(n not in changes,'Changed base frame cannot be decoded')
                f=bank['frames'][n];nf=graphics_bank(ng,0,allow_bank_aliases=True)['frames'][n]
                require(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data==decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data and records(c,cb,n)==records(nc,cb,n),'Placeholder changed');continue
            want=old.copy()
            if cb==0:
                for x,y in SPECKS.get(n,[]):want[y,x]=0
            require(np.array_equal(raster(ng,nc,0,cb,n),want),'Base repack changed an unapproved pixel')
    return result,proof

def full(arc,n):
    g,c=entry(arc,2),entry(arc,3);v=raster(g,c,0,0,n)
    for cb in (8,5,7,6):
        layer=raster(g,c,0,cb,n);v=np.where(layer,layer,v)
    return v

def pack_with_overpaint(raw,count,a,b,cr,ar,pool,limit):
    """공통 파츠 위에 일반 자세의 독립 팔을 덧그려 같은 픽셀을 보존한다."""
    cm=np.zeros(a.shape,bool);am=cm.copy()
    for x,y in cr:cm[y:y+16,x:x+16]=True
    for x,y in ar:am[y:y+16,x:x+16]=True
    changed=cm&am&(a>0)&(b>0)&(a!=b);shared_a=a.copy();shared_a[changed]=b[changed]
    common=cm&(shared_a==b)&(b>0);br=fast_fit((b>0)&~common,limit-len(cr));require(br is not None,'Overpaint shot does not fit')
    new,aa,bb,_,_=pack_variant_pair(raw,count,shared_a,b,cr,ar,br,pool);data=bytearray(new);_,locations,_=indexed_atlas(new,count)
    for y,x in np.argwhere(changed):
        hits=[(t,rx,ry) for t,rx,ry in aa[len(cr):] if rx<=x<rx+16 and ry<=y<ry+16];require(bool(hits),'Missing overpaint tile');t,rx,ry=hits[-1];pos,shift=locations[(t//16*16+int(y)-ry)*256+t%16*16+int(x)-rx];data[pos]=(data[pos]&~(15<<shift))|(int(a[y,x])<<shift)
    return bytes(data),[[(t,x,y,0) for t,x,y in rows] for rows in (aa,bb)]

def artwork(out):
    src=D/'hand_shot_review/generated.png';require(digest(src)==SOURCE_SHA,'Arm artwork changed');source=Image.open(src).convert('RGBA');arc=(PARENT/'PL02_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.int32)
    cell=source.crop((0,source.height//2,source.width//3,source.height));template=normalize(cell,40,rgb,width=60)
    # The authored frame2 forearm occupies this native crop after restoring
    # the contact-sheet scale. Separate skin, cuff and sleeve material spans.
    skin=template[16:20,13:17].copy();cuff=template[16:20,18:20].copy();sleeve=template[16:20,20:34].copy()
    def material_patch(a,allowed):
        good=np.isin(a,allowed);require(np.any(good),'Missing authored arm material')
        from scipy.ndimage import distance_transform_edt
        _,near=distance_transform_edt(~good,return_indices=True);return a[near[0],near[1]]
    skin=material_patch(skin,(10,11,12,13));cuff=material_patch(cuff,(13,15));sleeve=material_patch(sleeve,(5,6,7,8,9));targets={n:full(arc,n) for n in FRAMES};records=[];yy,xx=np.indices((160,160))
    for n in SHOTS:
        old=targets[n].copy();base=render(arc,n)[1];ey,ex=np.nonzero((base==14)&(yy<80));ex=int(round(float(np.median(ex))));ey=int(round(float(np.median(ey))));left=(old>0)&(xx<ex-7)&(yy>=ey)&(yy<ey+11);require(np.any(left),'Missing shooting pistol');xmin=int(np.nonzero(left)[1].min());start=xmin+6;end=ex-2;mask=(xx>=start)&(xx<end)&(yy>=ey+2)&(yy<ey+10)&(old>0);new=old.copy();width=end-start;require(width>=5,'Forearm too short');strip=np.concatenate((np.array(Image.fromarray(skin).resize((3,4),Image.Resampling.NEAREST)),np.array(Image.fromarray(cuff).resize((2,4),Image.Resampling.NEAREST)),np.array(Image.fromarray(sleeve).resize((max(1,width-5),4),Image.Resampling.NEAREST))),axis=1)
        for x in range(start,end):
            ys=np.flatnonzero(mask[:,x])
            if not len(ys):continue
            lo,hi=int(ys.min()),int(ys.max())
            for y in ys:
                if y in (lo,hi):new[y,x]=1
                else:new[y,x]=strip[min(3,max(0,round((y-lo-1)*3/max(1,hi-lo-2)))),x-start]
        allowed=mask.copy()
        shoulder=[]
        for x,y in SPECKS.get(n,[]):new[y,x]=0;allowed[y,x]=True
        require(np.array_equal(new[~allowed],old[~allowed]),'Body changed outside forearm');require(np.array_equal(new[:,xmin:start],old[:,xmin:start]),'Pistol moved');targets[n]=new
        records.append({'frames':[n,n],'eye':[ex,ey],'arm_box':[start,ey+2,max(end,75) if shoulder else end,ey+10],'pistol_mask_bbox':[xmin,ey,start,ey+11],'changed_pixels':int(np.count_nonzero(old!=new)),'removed_detached_pixels':SPECKS.get(n,[]),'shoulder_join_pixels':shoulder,'all_other_body_pixels_preserved':True,'gun_pixels_preserved':True})
    for n,v in targets.items():save_image(v.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
    board=Image.new('RGB',(1440,640),'#252c3c');draw=ImageDraw.Draw(board)
    for i,n in enumerate((85,2,6)):
        for row in (0,1):
            v=full(arc,n) if row==0 else targets[n];rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);pic=Image.fromarray(rgba,'RGBA').crop((44,60,104,96)).resize((480,288),Image.Resampling.NEAREST);board.paste(pic,(i*480,row*320+26),pic);draw.text((i*480+4,row*320+4),('BEFORE ' if row==0 else 'AFTER ')+str(n),fill='white')
    board.save(out/'arm_before_after_8x.png');return targets,records

def pack_resources(arc,targets,frames):
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};changes={};reports=[];groups={}
    for n in frames:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
    for off,ns in groups.items():
        f=bank['frames'][ns[0]];require([q['index'] for q in bank['frames'] if q['offset']==off]==ns,'Unexpected aliases');raw=decode_stream(g,off,f['limit'],f['tile_count']*128).data;keep={q['tile'] for v in ns for cb in (0,6,7,8) for q in composition_frame(c,cb,v)['parts']};pool=set(range(f['tile_count']))-keep;limits=[len(pool)]*len(ns);overlays=[]
        for v in ns:
            base=raster(g,c,0,0,v);require(not np.any((base>0)&(targets[v]==0)),'Base escapes new arm');overlays.append(np.where((targets[v]==base)&(base!=15),0,targets[v]).astype(np.uint8))
        paired_effect_aliases=len(ns)==4 and all(np.array_equal(targets[ns[i+2]],np.where(targets[ns[i]]>0,targets[ns[i]],raster(g,c,0,0,ns[i+2]))) for i in range(2))
        paint=[targets[v] for v in ns[:2]] if paired_effect_aliases else overlays;paint_limits=limits[:2] if paired_effect_aliases else limits
        edge=[t for t in sorted(pool) if t%16==0];pools=[pool] if len(edge)<2 else [pool-(set(edge)-{t}) for t in edge];failure=None
        for available in pools:
            try:new,rr=pack_shared(raw,f['tile_count'],paint,available,paint_limits);break
            except ValueError as e:failure=e
        else:
            require(len(ns)==2 or paired_effect_aliases,'Single pose does not fit');a,b=[targets[v].copy() for v in ns[:2]];ba,bb=[raster(g,c,0,0,v) for v in ns[:2]];clear=(a==ba)&(b==bb)&(a!=15)&(b!=15)
            if not paired_effect_aliases:a[clear]=0;b[clear]=0
            first,second=[composition_frame(c,5,v)['parts'] for v in ns[:2]];other={(q['tile'],q['x'],q['y'],q['flags']) for q in second};cr=[[q['x']+80,q['y']+80] for q in first if (q['tile'],q['x'],q['y'],q['flags']) in other];mask=np.zeros(a.shape,bool)
            for x,y in cr:mask[y:y+16,x:x+16]=True
            common=mask&(a==b)&(a>0);ar=fast_fit((a>0)&~common,limits[0]-len(cr));br=fast_fit((b>0)&~common,limits[1]-len(cr));require(ar is not None and br is not None,'Previous shared-body layout does not fit')
            for available in pools:
                try:
                    new,aa,bb,_,_=pack_variant_pair(raw,f['tile_count'],a,b,cr,ar,br,available);rr=[[(t,x,y,0) for t,x,y in rows] for rows in (aa,bb)];break
                except ValueError as e:failure=e
            else:
                for available in pools:
                    try:new,rr=pack_with_overpaint(raw,f['tile_count'],a,b,cr,ar,available,limits[1]);break
                    except ValueError as e:failure=e
                else:raise failure
        if paired_effect_aliases:rr=rr+rr
        for v,parts in zip(ns,rr):changes[v]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80) for t,x,y,fl in parts);replacements[v]=encode_stream(new)
        reports.append({'frames':ns,'free_tiles':len(pool),'parts':[len(r) for r in rr]});print(json.dumps(reports[-1]),flush=True)
    nc,slack=repack_parts(c,5,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc);check=verify(arc,result,targets,{})
    return result,{'packing':reports,'graphics_repack':rep,'parts_bank5_remaining':slack,'verification':check}

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,registration=artwork(out);write(out/'registration.json',registration)
    if art_only:return
    arc,baseproof=correct_base((PARENT/'PL02_U.ARC').read_bytes());result,packed=pack_resources(arc,targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',{'task':'ultimate_armor_nana','kind':'ultimate_shot_arm','parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'generated_sha256':SOURCE_SHA,'frames':FRAMES,'registration':registration,'base_correction':baseproof,**packed,'files':{'PL02_U.ARC':sha256(result)},'full_ultimate_complete':False});print(json.dumps({'output':str(out),'verification':packed['verification'],'sha256':sha256(result)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
