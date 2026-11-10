"""Read existing Ultimate hurt body/FX sharing, without invoking art or packing."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,label
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame,compose_indices,decode_stream,indexed_atlas
D=Path(__file__).parent;N=D.parent/'nana_audit';O=D/'nana_ultimate_hurt_relations01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
p=N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC';blob=p.read_bytes()
assert sha(blob)=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
oldpath=N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC';oldblob=oldpath.read_bytes()
assert sha(oldblob)=='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'
a=Archive(blob);b=Archive(oldblob);refs=[*range(106,115),*range(233,237)];PBS=(0,5,6,7,8)
def sig(p):return p['flags'],p['tile'],p['x'],p['y']
def render(archive,n,parts):
    out=np.zeros((384,384),np.uint8)
    if not parts:return out
    f=archive.banks[0]['frames'][n];raw=decode_stream(archive.g,f['offset'],f['limit'],f['tile_count']*128).data
    pix,size,box,_=compose_indices(raw,f['tile_count'],{'parts':parts},allowed_cluts={0,1,2,3})
    v=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);ys,xs=np.nonzero(v);out[ys+box[1]+160,xs+box[0]+160]=v[ys,xs]
    return out
def parts(archive,n,pb):return composition_frame(archive.c,pb,n)['parts']
def layer(archive,n,pb):return render(archive,n,parts(archive,n,pb))
def compare(x,y):
    m=x!=y; yy,xx=np.nonzero(m)
    return {'equal':not np.any(m),'pixels':int(m.sum()),'bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)]if len(xx)else None}
rows=[];rels=[];panels=[]
for n in refs:
    f=a.banks[0]['frames'][n];r={'ref':n,'stream':f['offset'],'tiles':f['tile_count'],'owners':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],'layers':{}}
    for pb in PBS:
        v=layer(a,n,pb);original=layer(b,n,pb)
        r['layers'][str(pb)]={'parts':[{k:q[k]for k in('flags','tile','x','y','clut')}for q in parts(a,n,pb)],'visible_index_pixels':int(np.count_nonzero(v)),'indexed_sha256':sha(v.tobytes()),'original_PL00_comparison':compare(v,original)}
    rows.append(r)
    reference=106 if n in(107,108)else 110 if n==111 else None
    if reference is not None:
        rr={'ref':n,'core':reference,'layers':{}}
        for pb in PBS:
            remain=collections.Counter(sig(q)for q in parts(a,reference,pb));core=[];extra=[]
            for q in parts(a,n,pb):
                if remain[sig(q)]:core.append(q);remain[sig(q)]-=1
                else:extra.append(q)
            v=render(a,n,core);fx=render(a,n,extra)
            rr['layers'][str(pb)]={'all_core_records_found':not any(remain.values()),'core_render_comparison':compare(v,layer(a,reference,pb)),
                'unmatched_records':[{k:q[k]for k in('flags','tile','x','y','clut')}for q in extra],'unmatched_tiles':sorted({q['tile']for q in extra}),
                'unmatched_pixels':int(np.count_nonzero(fx)),'unmatched_indexed_sha256':sha(fx.tobytes()),
                'unmatched_are_only_effects_proven':not any(remain.values())}
        rels.append(rr)
    for mask in(0,15):panels.append((f'{n} '+('before jacket'if mask else'after body'),a.composite(n,mask,1)[0]))
flash=layer(a,109,0);m=layer(a,106,0)>0
def full_indices(archive,n):
    x=layer(archive,n,0).copy()
    for pb in(8,5,7,6):
        v=layer(archive,n,pb);x[v>0]=v[v>0]
    return x
before_flash=full_indices(a,109);before_shape=full_indices(a,106)>0
flashrule={'base_body_index13_exact':bool(np.array_equal(flash==13,m)),
    'base_outline_index9_exact':bool(np.array_equal(flash==9,binary_dilation(m)&~m)),
    'before_body_index13_exact':bool(np.array_equal(before_flash==13,before_shape)),
    'before_outline_index9_exact':bool(np.array_equal(before_flash==9,binary_dilation(before_shape)&~before_shape)),
    'other_layer_nonzero':{str(pb):int(np.count_nonzero(layer(a,109,pb)))for pb in PBS[1:]}}
histpath=ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC';historic=Archive(histpath.read_bytes())
source_110=layer(historic,110,0)>0;launch=full_indices(historic,110);newshape=launch>0
derived=[]
for n in(112,113,114):
    native=layer(historic,n,0)%16;v=native.copy();v[binary_dilation(source_110,iterations=2)]=0
    if n==114:v[np.isin(v,[3,5])]=0
    residual=v.copy()
    if n==112:v[binary_dilation(newshape)]=6;v[newshape]=14
    elif n==113:v[binary_dilation(newshape)]=1
    else:
        v[binary_dilation(newshape)]=1;v[newshape]=3
        v[np.isin(launch%16,[1,2,4,8,15])&newshape]=5;v[np.isin(launch%16,[6,9])&newshape]=1
    v=np.where(v,v+32,0).astype(np.uint8)
    np.save(O/f'{n}_external_residual.npy',residual)
    derived.append({'ref':n,'base_exact_to_old_PL00':compare(layer(a,n,0),layer(b,n,0)),
        'empty_layers':{str(pb):not np.any(layer(a,n,pb))for pb in PBS[1:]},
        'source_body110_base_exact_to_old_PL00':compare(layer(a,110,0),layer(b,110,0)),
        'historical_before_jacket110_reconstructed':compare(v,layer(a,n,0)),
        'current_jacket110_exact_to_historical':compare(full_indices(a,110),launch),
        'external_residual_pixels':int(np.count_nonzero(residual)),
        'external_residual_path':(O/f'{n}_external_residual.npy').relative_to(ROOT).as_posix()})
semantic=[]
for n,core in((107,106),(108,106),(111,110)):
    if n in(107,108):
        c=collections.Counter(sig(q)for q in parts(a,core,5));fxparts=[]
        for q in parts(a,n,5):
            if c[sig(q)]:c[sig(q)]-=1
            else:fxparts.append(q)
        fx=render(a,n,fxparts)
    else:fxparts=[q for q in parts(a,n,0)if q['clut']==2];fx=render(a,n,fxparts)
    base=layer(a,core,0);pred=base.copy();pred[fx>0]=fx[fx>0]
    diff=compare(pred,layer(a,n,0))
    semantic.append({'ref':n,'body_ref':core,'effect_source_layer':5 if n in(107,108)else 0,
        'effect_tiles':sorted({q['tile']for q in fxparts}),'effect_records':[{k:q[k]for k in('flags','tile','x','y','clut')}for q in fxparts],
        'effect_pixels':int(np.count_nonzero(fx)),'base_core_plus_fx_comparison':diff})
    np.save(O/f'{n}_separate_effect.npy',fx)
aura=[]
for n in(235,236):
    body=layer(a,234,0);q=layer(a,n,0);effect=np.where(body==0,q,0).astype(np.uint8)
    hist=ROOT/f'work/ver_rin_nana/nana_fourth_armor/hurt_aura_packed_v1/effect_{n}.png'
    src=np.array(Image.open(hist));h=np.zeros((384,384),np.uint8);h[80:80+src.shape[0],80:80+src.shape[1]]=src
    record={'ref':n,'core':234,'base_body_exact_where_body_opaque':bool(np.array_equal(q[body>0],body[body>0])),'base_effect_pixels':int(np.count_nonzero(effect)),
        'historical_aura_exact':bool(np.array_equal(effect,h)),'aura_source':hist.relative_to(ROOT).as_posix(),'aura_source_sha256':sha(hist.read_bytes()),
        'overlay_comparisons':{str(pb):compare(layer(a,n,pb),layer(a,234,pb))for pb in PBS[1:]},'composite':[]}
    for key,mask in(('after',0),('before',15)):
        coreidx=layer(a,234,0)if not mask else full_indices(a,234)
        idx=layer(a,n,0)if not mask else full_indices(a,n)
        ext=np.where(coreidx==0,idx,0).astype(np.uint8)
        diff=(coreidx!=idx)&(coreidx>0)
        record[key+'_body_index_differences']=int(diff.sum())
        record[key+'_external_index_pixels']=int(np.count_nonzero(ext))
        np.save(O/f'{n}_{key}_external_current.npy',ext)
    for mask in(0,15):
        bdy=np.array(a.composite(234,mask,1)[0]);actual=np.array(a.composite(n,mask,1)[0]);fx=np.array(a.rgba(effect));prediction=bdy.copy();mfx=fx[:,:,3]>0;prediction[mfx]=fx[mfx]
        em=np.any(actual!=prediction,axis=2);bm=bdy[:,:,3]>0
        record['composite'].append({'mask':mask,'whole_rgba_equal_to_234_plus_original_aura':bool(np.array_equal(prediction,actual)),
            'different_rgba_pixels':int(em.sum()),'old_aura_overlaps_body_pixels':int(np.count_nonzero(mfx&bm)),
            'body_rgba_exact_where_234_opaque':bool(np.array_equal(actual[bm],bdy[bm]))})
    aura.append(record)
images=[];crop=(128,118,196,202);cw,ch=360,450
for page in range((len(panels)+5)//6):
    board=Image.new('RGB',(cw*3,ch*2),'#263345');dr=ImageDraw.Draw(board)
    for i,(title,im)in enumerate(panels[page*6:page*6+6]):
        x,y=(i%3)*cw,(i//3)*ch;dr.text((x+4,y+4),title,fill='white');im=im.crop(crop).resize((340,420),Image.Resampling.NEAREST);board.paste(im,(x+10,y+24),im)
    path=O/f'current_{page:02}.png';board.save(path);images.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes())})
report={'scope':'현재Nana Ultimate 피격13의기존몸체/효과/재킷층읽기. 새원화/ARC/게임변경없음.',
    'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(blob)},{'path':oldpath.relative_to(ROOT).as_posix(),'sha256':sha(oldblob)}],
    'refs':rows,'record_subset_probe':rels,'semantic_effect_comparisons':semantic,'flash109':flashrule,'derived112_114':derived,'aura235_236':aura,
    'previous_base_rules':{'path':(D/'nana_hurt_relations01/report.json').relative_to(ROOT).as_posix(),'sha256':sha((D/'nana_hurt_relations01/report.json').read_bytes())},
    'historical_sources':[{'path':z.relative_to(ROOT).as_posix(),'sha256':sha(z.read_bytes()),'invoked':False}for z in(histpath,ROOT/'scripts/prepare_nana_ultimate_reaction.py',ROOT/'scripts/overhaul_sprites_state_layers.py',ROOT/'scripts/overhaul_sprites_costume.py')],
    'sheets':images,'actual_sheet_views':True,'viewed_sheets':[x['path']for x in images],
    'visual_notes':'실제13참조의두폼26표시5판을열람했다.107/108의분홍지그재그는머리장식이아니라피격효과다.109는양폼각실루엣이며112..114는현재재킷몸체에맞춘공통CLUT2빛이다.235/236의맨팔몸은234와내부표현이달라지지만재킷은234몸이이어진다. 새원화수용/새게임실기는이판에서판정하지않았다.',
    'conclusions':[
        '106/107/108은같은30tile stream이다. overlay5는106몸체기록에17/18효과타일5/4기록을추가한구조이며그99/76px효과는정확히분리된다. base0는별도의합성그림이재패킹돼있어106파트집합을빼는방식이실패한다. 보고의unmatched_records를효과라고간주하지말것.',
        '현재base107/108은106+overlay5의효과를그대로합성한결과와98/49px다르다. 이것은기존맨팔등록차이이며새106공유를원래after표시exact라고설명할수없다. 새몸을공유하더라도효과원타일17/18·원위상/좌표를별도로보호하고새가림관계를검토한다.',
        '110/111은같은stream이다.111의현재CLUT2기록10개(타일6,8,10..17)188px를110위에합성하면base표시exact이다.타일7/9를PL00처럼무조건효과12개라고가정하지말고실제소비기록을사용한다. overlay5의몸체는110/111 exact이다.',
        '109는두폼각각의106알파13+Manhattan1px외곽9가정확히재현된다. base는after,overlay5는before실루엣이다. 두층을새각몸에동기화하고부분/의상합성시after가before밖으로나오는지별도검사한다.',
        '112/113/114는현재빈아머층+CLUT2공통base이며두폼표시가같다. 역사overhaul_sprites_state_layers규칙을과거baseline의재킷110으로독립재구성하여현재색인exact확인. 외부원효과잔여82/76/276px를보존하고새재킷110기준으로재현하는것이현방식이다. 두폼별로각각그려서overlay5에넣는경로가아니다.',
        '235/236은234와raw공유하지않는다. 재킷합성에서는234몸체색인/RGBA exact이고몸바깥오라가66/135px다. 맨팔은234몸체영역에서155/138px달라지므로새234+현오라단순합성과같지않다. base바깥효과76/146px 역시기존PL00별도Nana오라85/172px전체와다르다.',
        '현재235 overlay5는234와6px차이(머리/오라경계),236 overlay5는234와exact이다. 이차이와양폼의오라가림을분리검토해야한다. 새원화몸체를옛파생그림으로덮거나PL00오라85/172를현재Ultimate와동일하다고간주하지않는다.'
    ],
    'limits':['관계분석은새원화수용/MIPS/실기검사가아니다. 원표의트리거는기존보고를참조한다.',
        '기존after107/108·235/236의프레임별원화양자화전과정을다시재구성하지않았다. 현재실제색인/조립과역사builder의의도를구분해기록했다.',
        '현재표시의몸바깥부분을external_current.npy로따로저장했지만그마스크는새몸의효과원형을완전히정의하는제작승인이아니다. 새몸이변하면가려졌던효과와몸영역의차이를수동으로확인해야한다.']}
path=O/'report.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha':sha(path.read_bytes()),'semantic':semantic,'flash':flashrule,'derived':derived,'aura':aura},ensure_ascii=False))
