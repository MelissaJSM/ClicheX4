"""기존 Ultimate 호버5와 원추진15위상을 같은 원점에서 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_cdt
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
from prepare_hover_ultimate_inputs import P,PARENT,CUTS
def plane(a,f):
    c=composition_frame(a.c,12,f);b,s,bb,_=compose_static(entry(a.data,0x10206),local_composition(c));z=np.zeros((384,384),np.uint8);z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(b,np.uint8).reshape(s[1],s[0]);return z,c
def main():
    d=H/'hover_ultimate_contact_sources01';need(not d.exists(),'기존자료보호');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경');rp=H.parent/'zero_audit/shibuki_nova_hover_relations01/report.json';m=json.loads(rp.read_text('utf8'));d.mkdir();rows=[];pal=np.zeros((16,4),np.uint8)
    for i in range(1,16):pal[i]=[60+i*10,70+i*8,110+i*5,255]
    sig=lambda q:tuple(q[k]for k in('flags','tile','x','y'))
    for n in(221,223,225,227,229):
        old=a.composite(n,15)[0];alpha=np.array(old)[:,:,3]>0;lower=alpha.copy();lower[:160+CUTS[n]]=False;dist=distance_transform_cdt(~lower,metric='chessboard');imgs=[];cases=[];old.save(d/f'old_{n}.png')
        for r in m['jet']['frames']:
            if n not in r['player_refs']:continue
            f=r['frame'];z,c=plane(a,f);need([sig(q)for q in c['parts']]==[sig(q)for q in r['parts']] and int((z>0).sum())==r['opaque'],'원효과표 불일치');Image.fromarray(z).save(d/f'jet_{f:02}_indices.png');fx=Image.fromarray(pal[z]);com=fx.copy();com.alpha_composite(old);imgs.append((f'{n} original jet{f}',com));cases.append({'effect_frame':f,'indices_sha256':sha(z.tobytes()),'parts':c['parts'],'overlap_original_lower':int(((z>0)&lower).sum()),'min_chessboard_to_any_lower_cell':int(dist[z>0].min()),'world_translation':[0,0]})
        page(imgs,a.composite(0,0)[0],d/f'original_contacts_{n}.png',cols=3,scale=5);rows.append({'ref':n,'original_metrics':metrics(old),'cut_world_y':CUTS[n],'lower_bounds':metrics(Image.fromarray(np.where(lower[:,:,None],np.array(old),0).astype(np.uint8))),'cases':cases})
    write(d/'manifest.json',{'parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'relation_report':{'path':rp.relative_to(ROOT).as_posix(),'sha256':sha(rp.read_bytes())},'frames':rows,'original_muzzle_origins':m['original_muzzle_origins'],'whole_effect_tiles':{str(t):sha(bytes(tile_pixels(entry(a.data,0x10206),t)))for t in m['jet']['whole_tiles']},'source_static_entry_sha256':sha(entry(a.data,0x10206)),'effect_phases':15,'source_colours_diagnostic_only':True,'limits':['불꽃은 실제0x7802 팔레트를 재현하지 않은 중립색 위치 진단이다.','최소거리 수치는 하체의 아무 셀과의 거리이므로 의미상 뒤꿈치 접점 확정값은 아니다. 실제 시트와 새 신발위치를 함께 확인한다.','원점/facing0 위치합성만이며 화면상 이동·실제60Hz·모든위상시간 검증은 별도다.'],'runtime_verified':False,'files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()}})
    print(json.dumps({'phases':15,'sheets':5,'manifest':sha((d/'manifest.json').read_bytes())}))
if __name__=='__main__':main()
