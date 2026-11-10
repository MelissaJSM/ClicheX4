"""Trace native141 dust tiles separately from stale body pixels."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame,decode_stream,compose_indices,indexed_atlas
O=D/'nana_arrival141_dust01';O.mkdir(exist_ok=True);tracked={}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def read(p):
    z=p.read_bytes();tracked[rel(p)]=sha(z);return z
current=D.parent/'nana_audit/ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC'
historical=ROOT/'out/ver_rin_nana/nana_ultimate_ladder_20261104T104212237140Z/PL02_U.ARC'
a=Archive(read(current));h=Archive(read(historical))
assert sha(a.data)=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
assert sha(h.data)=='f26be08d15f57687ba489a9b47d8e834abe23b9d53c383bb2e1528b64aab653c'
def raw(ar):
    f=ar.banks[0]['frames'][141];return decode_stream(ar.g,f['offset'],f['limit'],f['tile_count']*128).data
def render(ar,ps):
    z=np.zeros((384,384),np.uint8)
    if not ps:return z
    f=ar.banks[0]['frames'][141];px,size,bb,_=compose_indices(raw(ar),f['tile_count'],{'parts':ps},allowed_cluts={0,1,2,3})
    v=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);y,x=np.nonzero(v);z[y+160+bb[1],x+160+bb[0]]=v[y,x];return z
def points(z):return [[int(x)-160,int(y)-160,int(z[y,x])]for y,x in np.argwhere(z>0)]
def full(ar,n):
    z=ar.layer(n)[0].copy()
    for pb in(8,5,7,6):
        t=ar.layer(n,pb)[0];z[t>0]=t[t>0]
    return z
hp=composition_frame(h.c,0,141)['parts'];dp=[p for p in hp if p['tile']==7]
assert [(p['index'],p['flags'],p['tile'],p['x'],p['y'])for p in dp]==[(7,128,7,-34,-10),(8,0,7,19,-8)]
dust=render(h,dp);assert np.count_nonzero(dust)==12
atlas=np.frombuffer(indexed_atlas(raw(h),h.banks[0]['frames'][141]['tile_count'])[0],np.uint8).reshape(-1,256)
tile7=atlas[:16,112:128].copy();assert np.count_nonzero(tile7)==6
np.save(O/'historical_tile7.npy',tile7);np.save(O/'dust141_indices.npy',dust)
effectpng=ROOT/'work/ver_rin_nana/nana_ultimate_armor/ceremony_packed_v1/effect_141.png';read(effectpng)
e=np.array(Image.open(effectpng));large=np.zeros((384,384),np.uint8);large[80:240,80:240]=e;assert np.array_equal(large,dust)
cp=composition_frame(a.c,0,141)['parts'];current_dust_parts=[];rendered=np.zeros_like(dust)
for p in cp:
    v=render(a,[p])
    if np.any((v>0)&(dust>0)):
        assert not np.any((v>0)&(dust==0)),('mixed current part',p)
        rendered[v>0]=v[v>0];current_dust_parts.append(p)
assert np.array_equal(rendered,dust)
rows=[]
for mask,form in[(15,'before'),(0,'after')]:
    idle=full(a,0)if mask else a.layer(0)[0];pose=full(a,141)if mask else a.layer(141)[0]
    assert np.array_equal(pose[dust>0],dust[dust>0]) and not np.any(idle[dust>0])
    external=np.where((idle==0)&(pose>0),pose,0).astype(np.uint8)
    extra=external.copy();extra[dust>0]=0
    inside=(idle>0)&(pose!=idle)
    details=[]
    for x,y,index in points(extra):
        owners=[]
        for pb in(0,8,5,7,6):
            # The five extra after pixels belong to base body; retain every record evidence.
            for p in composition_frame(a.c,pb,141)['parts']:
                v=render(a,[p])
                if v[y+160,x+160]:owners.append({'part_bank':pb,'part_index':p['index'],'tile':p['tile'],'value':int(v[y+160,x+160])})
        details.append({'x':x,'y':y,'index':index,'records_reading_pixel':owners})
    rows.append({'form':form,'current_external_pixels':int(np.count_nonzero(external)),'original_dust_exact':True,
                 'extra_non_dust_pixels':details,'body_pixels_different_from_current_idle':int(inside.sum())})
    np.save(O/f'{form}_extra_non_dust.npy',extra)
assert rows[0]['current_external_pixels']==12 and not rows[0]['extra_non_dust_pixels'] and rows[0]['body_pixels_different_from_current_idle']==0
assert rows[1]['current_external_pixels']==17 and len(rows[1]['extra_non_dust_pixels'])==5
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',14);window=(-40,-45,40,28);scale=5;cw,ch=400,390
items=[('현재 재킷141',a.composite(141,15)[0]),('입증된 먼지12px',a.rgba(dust)),('현재 맨팔141',a.composite(141)[0]),('현재 맨팔대기0',a.composite(0)[0])]
board=Image.new('RGB',(cw*4,ch),'#27313f');dr=ImageDraw.Draw(board)
for i,(s,im)in enumerate(items):
    dr.text((i*cw+4,4),s,font=font,fill='white');z=im.crop(tuple(v+160 for v in window)).resize((400,365),Image.Resampling.NEAREST);board.paste(z,(i*cw,25),z)
board.save(O/'dust_source_comparison.png')
for p,v in tracked.items():assert sha((ROOT/p).read_bytes())==v
report={'scope':'현재141 먼지와 구형몸체 잔여5픽셀을 역사12픽셀/전체tile7 실제소비로 분리한 읽기 감사. 제작함수·게임 실행 없음.',
        'sources':tracked,'historical_frame141':h.banks[0]['frames'][141],'historical_effect_parts':dp,
        'historical_logical_tile7_atlas_rect':[112,0,128,16],'historical_tile7_opaque':6,
        'historical_whole_tile7_sha256':sha(tile7.tobytes()),'effect_placed_pixels':points(dust),
        'effect_indexed_sha256':sha(dust.tobytes()),'historical_effect_png_exact':True,
        'current_frame141':a.banks[0]['frames'][141],'current_effect_parts':current_dust_parts,
        'forms':rows,
        'recommendation':'입증된12픽셀 또는 해당 역사tile7 두기록을 현재idle0 각폼 위에 별도 합성한다. 현재맨팔의 추가5픽셀은먼지타일이 아닌구형몸체이므로 복원효과로 보존하지 않는다.',
        'note':'현재 재패킹에서는 먼지가tile4/5 두기록으로 나뉜다. 현재tile7은몸체이며 역사tile7과동일번호로취급하면안된다.',
        'runtime_verified':False,'producer_functions_called':False,
        'comparison':{'path':rel(O/'dust_source_comparison.png'),'sha256':sha((O/'dust_source_comparison.png').read_bytes()),'actually_viewed':False}}
out=O/'report.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':sha(out.read_bytes()),'report':rel(out),'dust':points(dust),'extra5':rows[1]['extra_non_dust_pixels']},ensure_ascii=False))
