"""고정 ARC 재추출의 밝은배경 손목·원탄환/15추진 위상을 같은 원점에서 진단한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,label,distance_transform_cdt
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,digest
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
FINAL='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba'
def static(a,b,n):
    c=composition_frame(a.c,b,n);raw,size,bb,_=compose_static(entry(a.data,0x10206),local_composition(c));z=np.zeros((384,384),np.uint8)
    if raw:z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(raw,np.uint8).reshape(size[1],size[0])
    return z,c
def sig(c):return[(p['flags'],p['tile'],p['x'],p['y'])for p in c['parts']]
def fx(z,color):
    a=np.zeros((384,384,4),np.uint8);a[z>0]=color;return Image.fromarray(a)
def overlay(body,effect):
    out=effect.copy();out.alpha_composite(body);return out
def board(path,rows,scale=6,crop=(118,126,188,194)):
    w,h=crop[2]-crop[0],crop[3]-crop[1];cw,ch=w*scale+12,h*scale+32;out=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#e9e8e4');dr=ImageDraw.Draw(out)
    for y,row in enumerate(rows):
        for x,(title,im,bg)in enumerate(row):
            dr.rectangle((x*cw,y*ch,x*cw+cw-1,y*ch+ch-1),fill=bg);dr.text((x*cw+4,y*ch+4),title,fill='#111111'if bg!='#263345'else'white');cut=im.crop(crop).resize((w*scale,h*scale),Image.Resampling.NEAREST);out.paste(cut,(x*cw+6,y*ch+26),cut)
    out.save(path)
def main():
    d=H/'hover_ultimate_final_contacts01';need(not d.exists(),'새 검토폴더');p=H/'prepared_hover_ultimate01/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)==FINAL,'후보 변경');parent=H/'prepared_nova_strike_ultimate01/PL02_U.ARC';old=Archive(parent.read_bytes())
    disk=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v29/shibuki_riko.bin';need(digest(disk)=='753928a3cf2101caabf05cbe112217aa6d4b95b6320674632692831297a52252','BR29 변경');ce=read_disc(disk,('SLUS_005.61',))[0]['SLUS_005.61'];original=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC','SLUS_005.61'))[0];u=Archive(original['PL02_U.ARC']);oe=original['SLUS_005.61'];off=lambda x:x-0x80010000+2048
    rp=H.parent/'zero_audit/shibuki_base_hover_ownership01/report.json';r=json.loads(rp.read_text('utf8'));d.mkdir();jets=[];jetcases=[];bullets=[];wrist=[];inputs={str(p.relative_to(ROOT)):sha(p.read_bytes()),str(parent.relative_to(ROOT)):sha(parent.read_bytes()),str(rp.relative_to(ROOT)):sha(rp.read_bytes()),str(Path(__file__).relative_to(ROOT)):sha(Path(__file__).read_bytes())}
    need(entry(a.data,0x10206)==entry(old.data,0x10206),'효과static 변경');alltiles=set()
    for q in r['jets']['sequences']:
        n=q['refs'][0];aid=q['animation'];at=off(0x8011bf40+aid*4);ptr=struct.unpack_from('<I',oe,at)[0];need(oe[at:at+4]==ce[at:at+4],'제트표 포인터 변경');steps=[list(struct.unpack_from('<bbbB',ce,off(ptr)+4*i))for i in range(3)];need(steps==q['steps']and ce[off(ptr):off(ptr)+12]==oe[off(ptr):off(ptr)+12],'제트 원표변경');rows=[]
        for frame in[s[3]for s in steps]:
            z,c=static(a,12,frame);uz,uc=static(u,12,frame);need(np.array_equal(z,uz)and sig(c)==sig(uc),'원제트변경');ts={v['tile']+v['page']*256 for v in c['parts']};alltiles|=ts
            for t in ts:need(tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(u.data,0x10206),t),'원제트 전체타일변경')
            Image.fromarray(z).save(d/f'jet_{frame:02}_indices.png');jet=fx(z,(68,173,179,255));rows.append([(f'{n} parent jet{frame}',overlay(old.composite(n,15)[0],jet),'#e9e8e4'),(f'{n} new jet{frame}',overlay(a.composite(n,15)[0],jet),'#e9e8e4'),(f'{n+1} shot jet{frame}',overlay(a.composite(n+1,15)[0],jet),'#e9e8e4')]);lower=a.layer(n,5)[0]>0;dist=distance_transform_cdt(~lower,metric='chessboard');jetcases.append({'ref':n,'shot':n+1,'phase':frame,'parts':c['parts'],'indices_sha256':sha(z.tobytes()),'full_tiles_US_exact':sorted(ts),'lower_overlap':int(((z>0)&lower).sum()),'minimum_lower_distance':int(dist[z>0].min()),'world_shift':[0,0]})
        board(d/f'jet_{n:03}.png',rows,5);jets.append({'animation':aid,'pointer':ptr,'steps':steps,'original_bytes_exact':True})
    need(alltiles==set(range(504,510)),'원6타일');lp=struct.unpack_from('<I',oe,off(0x8011bf40+21*4))[0];need(ce[off(lp):off(lp)+28]==oe[off(lp):off(lp)+28],'첫탄환7표 변경');lemon=[]
    for i in range(7):
        st=list(struct.unpack_from('<bbbB',ce,off(lp)+4*i));z,c=static(a,1,st[3]);uz,uc=static(u,1,st[3]);need(np.array_equal(z,uz)and sig(c)==sig(uc),'원탄환변경');ts={v['tile']+v['page']*256 for v in c['parts']}
        for t in ts:need(tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(u.data,0x10206),t),'원탄환전체타일변경')
        Image.fromarray(z).save(d/f'bullet_{i:02}_indices.png');lemon.append(z);bullets.append({'step':st,'parts':c['parts'],'indices_sha256':sha(z.tobytes()),'opaque':int((z>0).sum()),'whole_tiles_US_exact':sorted(ts)})
    need(int((lemon[0]>0).sum())==188,'첫탄환188');need(ce[off(0x80108768):off(0x80108768)+4]==oe[off(0x80108768):off(0x80108768)+4]==bytes(4),'type0offset');originrows=[]
    for n in(222,224,226,228,230):
        at=off(0x8011b230+n*2);need(ce[at:at+2]==oe[at:at+2],'총구표 변경');x,y=struct.unpack_from('<bb',ce,at);body=a.composite(n,15)[0];body.save(d/f'actual_{n}.png');alpha=np.array(body)[:,:,3]>0;gm=np.array(Image.open(H/f'hover_ultimate_shot_inputs01/{n:03}_barrel_mask.png'))>0;gi=np.array(Image.open(H/f'hover_ultimate_shot_inputs01/{n:03}_barrel_indices.png'));gun=gm&(gi>0);rest=alpha&~gm;touch=binary_dilation(gun,np.array([[0,1,0],[1,1,1],[0,1,0]],bool))&rest;need(touch.any(),'정본총과팔4방향접촉없음');need(label(alpha,np.ones((3,3)))[1]==1,'몸분리');effects=[];ims=[]
        for i,z in enumerate(lemon):
            world=np.roll(np.roll(z,y,0),x,1);need(int((world>0).sum())==int((z>0).sum()),'탄환clip');im=overlay(body,fx(world,(194,150,35,255)));draw=ImageDraw.Draw(im);draw.point((x+160,y+160),fill=(0,230,235,255));ims.append((f'{n} original FX step{i}',im,'#e9e8e4'));effects.append({'step':i,'origin':[x,y],'overlap_with_body':int(((world>0)&alpha).sum()),'overlap_with_canonical':int(((world>0)&gun).sum())})
        board(d/f'muzzle_{n:03}.png',[[('actual dark',body,'#263345'),('actual light',body,'#e9e8e4'),ims[0]]],7)
        if n in(222,228):
            crop=(x+156,y+155,160,y+171);board(d/f'wrist_{n:03}.png',[[('actual dark',body,'#263345'),('actual light',body,'#e9e8e4'),ims[0]]],14,crop)
            board(d/f'first7_{n:03}.png',[ims[:4],ims[4:]+[('actual no effect',body,'#e9e8e4')]],5)
        wrist.append({'ref':n,'canonical_contact4_cells':[[int(xx-160),int(yy-160)]for yy,xx in np.argwhere(touch)],'alpha_connected8':True,'actual_RGBA_sha256':sha(np.array(body).tobytes()),'original_projectile_origin':[x,y],'bullet_cases':effects});originrows.append([n,x,y])
    write(d/'report.json',{'passed':True,'candidate_sha256':FINAL,'parent_sha256':sha(old.data),'BR29_EXE_sha256':sha(ce),'US_EXE_sha256':sha(oe),'original_jet_sequences':jets,'jet_cases':jetcases,'original_static_tiles':sorted(alltiles),'original_bullet7':bullets,'muzzle_origins':originrows,'wrist_cases':wrist,'inputs':inputs,'pngs':{p.name:sha(p.read_bytes())for p in sorted(d.glob('*.png'))},'effects_are_neutral_occupancy_colors':True,'actual_effect_CLUT_or_blending_reproduced':False,'runtime_verified':False,'limits':['효과는 원색인형상·원좌표 보존을 중립색으로 보이는 진단이다. 실제0x7802/블렌딩/그리기순서 실기 재현 아님.','탄환7단계는 각각 같은 최초발사점에 놓았다. 발사후 탄환 이동을 재현하지 않는다.','제트하체 최소거리0이나 총-팔4방향 접촉만으로 미술수용을 선언하지 않는다.','표의 상대분기·정지96은 실제호버 시간/물리이동 전체를 뜻하지 않는다.']});print(json.dumps({'report':sha((d/'report.json').read_bytes()),'sheets':len(list(d.glob('*.png'))),'wrist_contacts':{q['ref']:len(q['canonical_contact4_cells'])for q in wrist}}))
if __name__=='__main__':main()
