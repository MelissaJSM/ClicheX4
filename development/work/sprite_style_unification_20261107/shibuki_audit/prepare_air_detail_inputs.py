"""기본/포스 공중의 옛 제작물과 실제 현재 자원을 대조하고 새3키 입력을 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
P=H/'prepared_arrival_victory01/PL00_U.ARC';PSHA='78b329a07d888682c24b440386cb365f826572402346b3ee6620216ce951617e'
B=ROOT/'work/ver_buki_riko/shibuki_art';O=H/'air_detail_inputs01';KEYS=(33,35,39);CROP=(128,124,192,188)
def main():
    need(not O.exists(),'Fresh air input required');data=P.read_bytes();need(sha(data)==PSHA,'Wrong parent');a=Archive(data);O.mkdir()
    base=[];armor=[]
    for n in range(33,55):
        path=B/'air_v1/production05'/f'{"run"if n%2 else"shoot"}_{n if n%2 else n-1:03}.png'
        q=np.zeros((384,384),np.uint8);q[120:200,112:208]=np.array(Image.open(path));need(np.array_equal(q,a.layer(n)[0]),'Base air provenance differs')
        base.append({'ref':n,'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes()),'current_native_exact':True})
        for part,bank in [('head',5),('body',6),('arm',7),('leg',8)]:
            path=B/'fourth_armor_remaining_v1/layers06'/f'{part}_{n:03}.png';q=np.zeros((384,384),np.uint8);q[80:240,80:240]=np.array(Image.open(path));need(np.array_equal(q,a.layer(n,bank)[0]),'Fourth air provenance differs')
            armor.append({'ref':n,'part':part,'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes()),'current_native_exact':True})
    art=[B/'air_v1/generated_with_backdrop.png',B/'fourth_armor_remaining_v1/air_dash_generated.png'];source=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'actual_viewed':True}for p in art]
    write(O/'provenance.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PSHA,'base22_exact':base,'fourth88_parts_exact':armor,'source_art':source,'historical_scope':'기본 공중은2026-10-26 air_v1/production05, 포스는2026-10-27 layers06다. 이번11/07 상세화에서33..54 본체를 새로 만든 기록이 아니며 현재와 전부 일치한다.','historical_registration':'포스 register_remaining.py는 원 기본 머리/얼굴을 보호하고 생성 의상만 정렬했다. 옛 원화의 큰꼬리/다른체형을 전체 재등록하지 않는다.','new_repaint_is_not_duplicate':True,'limits':'이 비교는33..54의22참조다.93/94 별도공중대시는 이출처 검사에 포함하지 않았다.'})
    sheet=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1024));positions=[]
    for row,(form,mask)in enumerate([('base',0),('fourth',15)]):
        for col,n in enumerate(KEYS):
            im=a.composite(n,mask)[0];sub=im.crop(CROP);need(np.count_nonzero(np.array(sub)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Input crop clips sprite');sheet.alpha_composite(sub.resize((512,512),Image.Resampling.NEAREST),(col*512,row*512));im.save(O/f'{form}_{n:03}.png')
            yy,xx=np.nonzero(np.array(im)[:,:,3]);positions.append({'form':form,'ref':n,'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'foot_y_world':int(yy.max()-160),'world_origin':[160,160]})
        for col,n in enumerate((0,55,204)):
            im=a.composite(n,mask)[0];style.alpha_composite(im.crop(CROP).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
        page([(f'{n} old air',a.composite(n,mask)[0])for n in range(33,55,2)],a.composite(0,mask)[0],O/f'{form}_old_air_review.png',cols=3,scale=4)
    sheet.save(O/'page01_poses.png');style.save(O/'accepted_style.png')
    pairs_path=B/'air_v1/production05/pairs.json';pairs=json.loads(pairs_path.read_text('utf8'))['frames'];refs=[]
    for n in range(33,55,2):
        r=next(v for v in pairs if v['run']==n);f=a.banks[0]['frames'][n];aliases=[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']]
        refs.append({'body':n,'shot':n+1,'original_muzzle_world':r['original_muzzle_world'],'shared_raw_refs':aliases,'part_counts':{str(b):len(a.layer(n,b)[1]['parts'])for b in (0,5,6,7,8)}})
    prompt='''Redraw the six fully clothed Tenko Shibuki sprites in page01_poses.png into the detailed compact game-pixel style in accepted_style.png. This is one character wearing two existing costumes. Transparent 1536x1024 canvas: three512x512 cells across, two rows. Each cell is a native64x64 window, world(-32,-36) to(32,28), origin(32,36). Keep the exact action, facing direction, eye/neck location, hand height, bent knees and foot contact positions. No entire-figure bounding-box resize or lengthened limbs. Match accepted idle's short torso/limbs, head about23 native pixels including ears and compact full-bodied proportions.
Columns correspond to33 compact early jump with fists close to chest,35 one-knee-raised jump,39 raised hands overhead. Use the identical skeleton and face/hair scale across the two costume rows. The top row is BASE: lavender fox ears and layered long hair, human face with gold eyes, red side floral ornament/ribbon, white loose sleeves with light-blue shadow and red trim, red shrine outfit/skirt and front cord, striped pale-lavender leg wraps and white/red boots. Bottom row is FOURTH: same character, dark navy/black cape with white fur edge, purple sleeves with gold trim, fitted dark dress with gold edging, dark stockings and white/gold boots. Retain the short layered outer cape appropriate to this costume. No mechanical armor.
This is a deliberate style/detail repaint: replace the old large flat lavender rear-head patch, blank white sleeves and simplified torso with coherent hair locks in 2-3 middle tones, distinct facial planes, readable collar/cord, short sleeve folds and layered hem/boots, comparable to accepted_style's idle/wall/victory. Thin clean dark contour and compact shading clusters, not noisy tiny repeated scratches, puffy amorphous blobs or thick black masses. Do not revert to the old coarse head. Do not add an animal muzzle, big fox tail, extra hair ornaments, gold sunglasses (those belong only to the different Ultimate costume), open midriff or a new garment. This is air body artwork only, no buster or firing effect. Keep all six complete sprites inside their cells with transparent margins, no background, labels, platform, guide lines, cast shadow or additional poses.'''
    (O/'prompt.txt').write_text(prompt+'\n','utf8')
    write(O/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PSHA,'first_page':list(KEYS),'forms':['base','fourth'],'layout':{'source':[1536,1024],'native_cell':[64,64],'crop':CROP,'scale':8},'anchors':positions,'refs':refs,'muzzle_source_sha256':sha(pairs_path.read_bytes()),'source_images':{p.name:sha(p.read_bytes())for p in(O/'page01_poses.png',O/'accepted_style.png')},'generation_started':False,'game_written':False,'full_air_scope_not_finished':True})
    print({'provenance_base':len(base),'provenance_armor':len(armor),'first_page':KEYS,'out':str(O)})
if __name__=='__main__':main()
