"""Prepare remaining twelve poses with exact head masks and fixed native origins."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
OUT=D/'riko_cloth_inputs/run_inputs';OUT.mkdir(exist_ok=True)
source=D/'riko_restore/prepared_rear_v1/PL01_U.ARC';arc=source.read_bytes()
assert hashlib.sha256(arc).hexdigest()=='f8f346691709107a4ae774b49f0f46d662941442f75bf92ee0eead97bbf671c8'
original=json.loads((D/'riko_cloth_inputs/inputs.json').read_text('utf8'))
inventory=json.loads((D/'shared_masters/inventory.json').read_text('utf8'))
heads={r['id']:r for r in inventory['riko']['head_masters'][0]['matches']}
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,128,208,192);pages=[]
for name,ns in [('run01',[7,9,10,11]),('run02',[12,13,15,16]),('run03',[17,18,19,20])]:
    folder=OUT/name;folder.mkdir(exist_ok=True);sheet=Image.new('RGBA',(192,128));rows=[]
    for i,n in enumerate(ns):
        key=f'b0_{n:03d}';a=render(arc,0,0,n)[0];pic=rgba(a,pal);cut=pic.crop(crop)
        assert np.count_nonzero(np.array(cut.getchannel('A')))==np.count_nonzero(a)
        sheet.alpha_composite(cut,((i%2)*96,(i//2)*64));pic.save(folder/(key+'_native.png'));Image.fromarray(a).save(folder/(key+'_indices.png'))
        x,y=heads[key]['origin_world'];mask=np.zeros((384,384),bool);mask[160+y:160+y+19,160+x:160+x+23]=front>0
        assert np.array_equal(a[160+y:160+y+19,160+x:160+x+23][front>0],front[front>0])
        Image.fromarray(mask.astype(np.uint8)*255).save(folder/(key+'_preserve_head_mask.png'))
        rows.append({'key':key,'bank':0,'ref':n,'cell':[i%2,i//2],'bounds':pic.getbbox(),'preserve_head_mask':key+'_preserve_head_mask.png','head_origin_world':[x,y],'head_template_dimensions':[23,19],'head_opaque_pixels':int(mask.sum())})
    sheet.resize((1536,1024),Image.Resampling.NEAREST).save(folder/'input.png')
    meta={k:original[k]for k in('source_bin','source_sha256','archive_sha256','working_arc','working_arc_sha256','character','palette_words')}
    meta.update({'crop':crop,'native_cell':[96,64],'columns':2,'rows':2,'scale':8,'frames':rows,'native_origin':[160,160],'editing_scope':'기존 정밀 머리는 보존한다. 수용된 새 8/14의 소매·가슴 주름·부츠 명암을 이 연속 자세에 맞춘다. 보폭·무릎·발끝·손 접점은 원래 자세와 유지한다.','game_changed':False})
    (folder/'inputs.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8');pages.append({'name':name,'refs':ns,'input':str((folder/'input.png').relative_to(ROOT))})
style=Image.new('RGBA',(288,64))
for i,n in enumerate([147,8,14]):
    a=render(arc,0,0,147)[0]if n==147 else np.array(Image.open(D/'riko_cloth_inputs/registered_candidate_v1'/f'b0_{n:03d}_indices.png'))
    style.alpha_composite(rgba(a,pal).crop(crop),(i*96,0))
style.resize((2304,512),Image.Resampling.NEAREST).save(OUT/'accepted_style_8x.png')
(OUT/'manifest.json').write_text(json.dumps({'pages':pages,'style_reference':str((OUT/'accepted_style_8x.png').relative_to(ROOT)),'all_head_pixels_per_pose':309,'old_head_preservation_intentional':True,'generated':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(pages))
