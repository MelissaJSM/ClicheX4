"""Read-only layer diagnostics for Nana arrival and Shibuki standing arm."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
from src.psx_ui_atlas import tile_pixels
D=Path(__file__).parent;W=ROOT/'work/sprite_style_unification_20261107'
sha=lambda b:hashlib.sha256(b).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def board(items,path,box,cols=5,scale=6):
    w,h=(box[2]-box[0])*scale,(box[3]-box[1])*scale;cw,ch=w+16,h+40
    out=Image.new('RGB',(cw*cols,ch*((len(items)+cols-1)//cols)),'#263345');dr=ImageDraw.Draw(out)
    for i,(label,im) in enumerate(items):
        x,y=(i%cols)*cw,(i//cols)*ch
        dr.text((x+4,y+4),label,fill='white')
        im=im.crop(box).resize((w,h),Image.Resampling.NEAREST);out.paste(im,(x+8,y+32),im)
    out.save(path)

O=D/'nana_arrival_endpoint_audit01';O.mkdir(exist_ok=True)
p=W/'nana_audit/ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC'
historic=ROOT/'work/ultimate_costume_swap_20261105/core/prepared_complete_v1/ver_rin_nana/PL02_U.ARC'
a,old=Archive(p.read_bytes()),Archive(historic.read_bytes())
assert sha(a.data)=='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
bp=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v15/rin_nana.bin'
assets,_=read_disc(bp,('PL02_U.ARC','SLUS_005.61'))
assert assets['PL02_U.ARC']==a.data
exe=assets['SLUS_005.61'];off=lambda addr:addr-0x80010000+2048
code=exe[off(0x800257BC):off(0x8002588C)]
assert sha(code)=='46c1fe4c8c01be08e49c733c24e99fe7e4e2416b93a2dc50585a3503854038c5'
caller=struct.unpack_from('<I',exe,off(0x80023EA4))[0]
assert caller>>26==3 and ((caller&0x3ffffff)<<2|0x80000000)==0x800257BC
rows=[];items=[]
for n in range(133,138):
    layers=[]
    for b in (0,5,6,7,8):
        px,m=a.layer(n,b);op,om=old.layer(n,b)
        assert np.array_equal(px,op),(n,b)
        layers.append({'bank':b,'opaque':int((px>0).sum()),'parts':m['parts'],'indexed_sha256':sha(px.tobytes()),'historical_pixels_exact':True})
    before=np.array(a.composite(n,15)[0]);after=np.array(a.composite(n,0)[0])
    assert np.array_equal(before,np.array(old.composite(n,15)[0]))
    rows.append({'ref':n,'layers':layers,'mask15_vs0_changed_rgba_pixels':int(np.any(before!=after,axis=2).sum()),'historical_full_rgba_exact':True})
    items.extend([(f'{n} current mask0',Image.fromarray(after)),(f'{n} layer5 palette row1',a.rgba(a.layer(n,5)[0],16)),(f'{n} current mask15',Image.fromarray(before)),(f'{n} historical mask15',old.composite(n,15)[0]),('current idle mask15',a.composite(0,15)[0])])
board(items,O/'arrival_layers_133_137.png',(120,100,206,186),cols=5,scale=4)
write(O/'report.json',{'passed':True,'source':rel(p),'source_sha256':sha(a.data),'actual_disc':rel(bp),'historical':rel(historic),'historical_sha256':sha(old.data),
 'refs':rows,'palette_full_exact_to_history':a.p==old.p,'renderer_208B_sha256':sha(code),'caller_address':'0x80023EA4','caller_word':f'{caller:08x}',
 'code_rule':'Ultimate flag !=0, engine armor0 => visualmask15; owned armor>0 => mask0. 217..230만 mask15 예외. player transient armor=0은 이 판단에 사용하지 않음.',
 'actual_layer_clut':'pb5/6/8=0x7843(row1), pb7 arm2=0x7844(row2); 133..137의pb7은투명',
 'remaining_review_mask':'collect_current.py는 ultimate_before15, ultimate_after0을 사용하므로 해당 정적판은 mask 뒤집힘 아님.',
 'conclusion':'133..137 재킷5층은 존재하고 현재before 합성은 11/05 당시와 exact. 최근새그림 덮어쓰기 회귀/마스크오인 없음. 의상이 수영복처럼 읽히는 정도는 당시 국소 재킷 원화의 미술 문제로 별도 판단해야 함.',
 'native_executed':False,'runtime_verified':False,'artwork_changed':False,'comparison':rel(O/'arrival_layers_133_137.png'),'comparison_actually_viewed':False})

O=D/'shibuki_standing02_layer_audit01';O.mkdir(exist_ok=True)
p=W/'shibuki_audit/prepared_dash_base01/PL00_U.ARC';a=Archive(p.read_bytes())
roi=(144,168,152,176);yy,xx=np.indices((384,384));region=(xx>=roi[0])&(xx<roi[2])&(yy>=roi[1])&(yy<roi[3]);layers=[];items=[]
for b in (0,5,6,7,8):
    px,m=a.layer(0,b)
    pixels=[{'world':[int(x)-160,int(y)-160],'index':int(px[y,x])} for y,x in zip(*np.nonzero(region&(px>0)))]
    relevant=[q for q in m['parts'] if q['x']<roi[2]-160 and q['x']+16>roi[0]-160 and q['y']<roi[3]-160 and q['y']+16>roi[1]-160]
    layers.append({'bank':b,'roi_opaque_pixels':pixels,'intersecting_parts':relevant})
    im=a.rgba(px,0 if b==0 else 16)
    dr=ImageDraw.Draw(im);dr.rectangle((roi[0]-1,roi[1]-1,roi[2],roi[3]),outline='#ff6060')
    items.append((f'idle0 layer{b}',im))
for label,mask in (('base',0),('fourth',15)):
    im=a.composite(0,mask)[0];dr=ImageDraw.Draw(im);dr.rectangle((roi[0]-1,roi[1]-1,roi[2],roi[3]),outline='#ff6060');items.append((f'idle0 {label}',im))
    im=Image.open(W/f'shibuki_audit/base_run_standing02_registered02/{label}_002.png').convert('RGBA');dr=ImageDraw.Draw(im);dr.rectangle((roi[0]-1,roi[1]-1,roi[2],roi[3]),outline='#ff6060');items.append((f'candidate2 {label}',im))
board(items,O/'layers_and_shot.png',(136,133,181,186),cols=5,scale=8)
write(O/'report.json',{'scope':'서서0 기준의 작은 옛소매 후보 부분과 layer8의 기술 소유를 읽기 분리. 아트/패킹 미변경.',
 'source':rel(p),'source_sha256':sha(a.data),'roi_world':[-16,8,-8,16],'layers':layers,
 'code':'compose_base_run_shots.py:38의 bn0 guard는 layer8 전체opaque를 무릎으로 간주하여 새팔patch에서 제외함. layer8은 기술적 소유이며 신체 의미의 보증 아님.',
 'comparison':rel(O/'layers_and_shot.png'),'comparison_actually_viewed':False,'runtime_verified':False})
print('read-only endpoint diagnostics written')
