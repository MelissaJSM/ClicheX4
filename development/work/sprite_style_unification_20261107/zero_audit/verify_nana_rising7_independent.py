"""Independent native readback. Never import producer registration/packing modules."""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import decode_stream,composition_frame,bank_offsets,indexed_atlas
D=Path(__file__).parent;N=D.parent/'nana_audit';R=N/'rising_repaint'
P=R/'packed_base_candidate_v1';T=R/'joint_layers_probe_v2';O=D/'nana_rising7_independent01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()
oldpath=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';newpath=P/'PL00_U.ARC'
old,new=oldpath.read_bytes(),newpath.read_bytes()
assert sha(old)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa'
assert sha(new)=='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'
a,b=Archive(old),Archive(new);PBS=(0,5,6,7,8);refs={100,101,102,103,104,231,232};reserved={105,*range(175,183)}
frozen=read(P/'INPUT_FROZEN.json');assert frozen['input_fixed'] and frozen['candidate_sha256']==sha(new)
for q in frozen['files']:assert sha((ROOT/q['path']).read_bytes())==q['sha256'],q['path']
m=read(T/'manifest.json');rows={r['ref']:r for r in m['frames']};assert set(rows)==refs and m['source_arc_sha256']==sha(old)
count=collections.Counter();target={}
assert replace_entry(replace_entry(new,2,a.g),3,a.c)==old and a.p==b.p
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)
assert bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ob,nb) in enumerate(zip(a.banks,b.banks)):
    assert (ob['base'],ob['end'])==(nb['base'],nb['end']) and len(ob['frames'])==len(nb['frames'])
    if gb:
        assert a.g[ob['base']:ob['end']]==b.g[nb['base']:nb['end']]
        count['auxiliary_effect_graphics_banks_byte_exact']+=1
    for f,g in zip(ob['frames'],nb['frames']):
        assert f['index']==g['index'];n=f['index']
        x=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128)
        y=decode_stream(b.g,g['offset'],g['limit'],g['tile_count']*128)
        assert x.serialize()==a.g[x.start:x.end] and y.serialize()==b.g[y.start:y.end]
        count['raw_checked']+=1
        if gb==0 and n in refs:
            assert g['tile_count']==32
            atlas=np.frombuffer(indexed_atlas(y.data,32)[0],np.uint8).reshape(-1,256)
            assert not atlas[:32,:16].any()
            count['target_32tile_buffers']+=1
        else:
            assert x.data==y.data and f['tile_count']==g['tile_count'];count['non_target_raw_exact']+=1
f231,f232=[b.banks[0]['frames'][n] for n in (231,232)]
assert f231['offset']!=f232['offset']
assert decode_stream(b.g,f231['offset'],f231['limit'],4096).data==decode_stream(b.g,f232['offset'],f232['limit'],4096).data
assert all(np.array_equal(a.layer(231,p)[0],a.layer(232,p)[0]) for p in PBS)
for n in range(237):
    if n in reserved:continue
    for pb in PBS:
        px=b.layer(n,pb)[0];count['layers_checked']+=1
        if n in refs:
            q=T/f'layer{pb}_{n:03}.png';want=np.array(Image.open(q))
            assert want.shape==(384,384) and want.dtype==np.uint8 and want.max()<16
            assert sha(want.tobytes())==(rows[n]['base_sha256'] if pb==0 else rows[n]['layers'][str(pb)])
            assert np.array_equal(px,want);target[n,pb]=want;count['authored_layers_exact']+=1
        else:
            assert np.array_equal(px,a.layer(n,pb)[0]);count['non_target_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
    for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
        x,y=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n)
        sem=lambda c:[(p['flags'],p['tile'],p['x'],p['y']) for p in c['parts']]
        if pb in PBS and n in refs:
            for part in y['parts']:
                assert 0<=part['page']*256+part['tile']<32 and part['tile']%16!=0 and not part['flip_y']
                count['safe_target_GPU_parts']+=1
        else:
            assert sem(x)==sem(y);count['non_target_compositions_exact']+=1

def color(px,start=0):
    words=b.words[start:];table=np.array([[(int(w)>>s&31)*255//31 for s in (0,5,10)]+[0 if i%16==0 else 255]for i,w in enumerate(words)],np.uint8)
    return table[px]
def join(n,mask,arm):
    out=color(target[n,0])
    for bit,pb in ((8,8),(1,5),(4,7),(2,6)):
        if mask&bit:
            q=color(target[n,pb],32 if pb==7 and arm==2 else 16);z=q[:,:,3]>0;out[z]=q[z]
    return out
for n in refs:
    full=np.array(Image.open(T/f'full_{n:03}.png').convert('RGBA'))
    assert sha(full.tobytes())==rows[n]['full_rgba_sha256']
    for mask in range(16):
        for arm in (1,2):
            actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,join(n,mask,arm));count['authored_partial_RGBA']+=1
            if mask==15:
                assert np.array_equal(actual,full);count['full_forms_RGBA_exact']+=1

# Reconstruct the source's 20 canonical gun texels from the accepted native 85.
gunpath=N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC';gunarc=Archive(gunpath.read_bytes())
gm=read(R/'canonical_weapon_probe_v2/manifest.json');assert sha(gunarc.data)==gm['donor_arc_sha256']
donor=gunarc.layer(85)[0];yy,xx=np.indices(donor.shape);xx-=160;yy-=160
mask=(xx>=-22)&(xx<=-15)&(yy>=-11)&(yy<=-6)&np.isin(donor,range(1,10))
coords=[[int(x)-160,int(y)-160,int(donor[y,x])]for y,x in zip(*np.nonzero(mask))]
assert coords==gm['canonical_source_texels'] and len(coords)==20
assert sha(donor[mask].tobytes())==gm['canonical_sha256']
weapons=[]
for n in sorted(refs):
    s=231 if n==232 else n;gr=next(v for v in gm['frames']if v['ref']==s and v['form']=='base')
    dx,dy=gr['translation'];case=np.zeros((384,384),np.uint8)
    for sx,sy,v in coords:case[160+sx+dy,160-sy+dx]=v
    path=R/'canonical_weapon_probe_v2'/f'base_{s:03}_case.png'
    assert np.array_equal(case,np.array(Image.open(path))) and np.count_nonzero(case)==20
    ys,xs=np.nonzero(case);assert int(ys.max()-ys.min()+1)==8
    pxs={form:np.array(Image.open(R/'canonical_weapon_probe_v2'/f'{form}_{s:03}_indices.png'))for form in ('base','fourth')}
    for form,maskval,start in (('base',0,0),('fourth',15,16)):
        actual=np.array(b.composite(n,maskval)[0]);want=color(pxs[form],start)
        assert np.array_equal(actual[case>0],want[case>0]);count['canonical_gun_and_fingers_full_checks']+=1
    exposed=(case>0)&(pxs['base']==pxs['fourth'])
    for maskval in range(16):
        for arm in (1,2):
            assert np.array_equal(np.array(b.composite(n,maskval,arm)[0])[exposed],color(pxs['base'])[exposed])
            count['canonical_gun_partial_checks']+=1
    weapons.append({'ref':n,'module20_exact_from_native85':True,'rotation':'(-y,x)','translation':[dx,dy],'vertical_extent':8,'unoccluded_texels':int(exposed.sum())})

# Compact new readback from the candidate bytes, independent of producer sheets.
images=[]
for page,ns in enumerate(((100,101),(102,103),(104,231,232))):
    box=(126,112,192,190);scale=4;cw,ch=280,348
    im=Image.new('RGB',(cw*6,ch*len(ns)),'#263345');dr=ImageDraw.Draw(im)
    for row,n in enumerate(ns):
        panels=[('old basic',a.composite(n)[0]),('new basic',b.composite(n)[0]),('old Fourth',a.composite(n,15)[0]),('new Fourth',b.composite(n,15)[0]),('idle basic',b.composite(0)[0]),('idle Fourth',b.composite(0,15)[0])]
        for col,(label,pic) in enumerate(panels):
            x,y=col*cw,row*ch;dr.text((x+4,y+6),f'{n} {label}',fill='white')
            pic=pic.crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST);im.paste(pic,(x+8,y+28),pic)
    path=O/f'readback_{page:02}.png';im.save(path);images.append({'path':rel(path),'sha256':sha(path.read_bytes())})
assert count['raw_checked']==508 and count['non_target_raw_exact']==501
assert count['layers_checked']==1140 and count['non_target_layers_exact']==1105 and count['authored_layers_exact']==35
assert count['authored_partial_RGBA']==224 and count['canonical_gun_partial_checks']==224
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
report={'passed':True,'scope':'나나 기본/포스 라이징7 후보를 제작/정합/패킹 함수 미호출로 독립 읽기 검사했다.',
 'parent':rel(oldpath),'parent_sha256':sha(old),'candidate':rel(newpath),'candidate_sha256':sha(new),
 'target_manifest':rel(T/'manifest.json'),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),
 'input_frozen_sha256':sha((P/'INPUT_FROZEN.json').read_bytes()),'input_files_hash_checked':len(frozen['files']),'counts':dict(count),
 'all_other_entries_audio_static_palette_exact':True,'bank_boundaries_exact':True,'231_232_original_and_new_display_exact_relation':True,'231_232_separate_streams_with_equal_new_decoded_data':True,
 'non_target7072_RGBA_implied_by_exact1105_layers_and_palette':True,'weapons':weapons,
 'raw_effect_banks_and_all_nontarget_effect_composition_exact':True,'new_readback_sheets':images,'readback_actually_viewed':False,
 'artwork_generation_reconstructed':False,'native_MIPS_executed_here':False,'runtime_verified':False,'producer_functions_called':False,'source_files_unchanged':True,
 'limits':['권총은 수용85의20텍셀 정본을90도회전한 새 통일형이다. 모든옛권총모양exact라는 주장이 아니다.','각색상 폼의 새 손가림과224부분창을 검사했으나 실제 불꽃 시간표/게임 혼합은 이번 읽기 범위 밖이다.','원화생성/양자화 전과정 재현이나 사용자수용을 주장하지 않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(count),'report_sha256':sha((O/'report.json').read_bytes())}))
