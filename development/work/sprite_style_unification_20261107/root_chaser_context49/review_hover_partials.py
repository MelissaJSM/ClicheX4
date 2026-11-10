"""발 파츠를 가진 부분 아머의 최신 호버를 대기와 같은 축척으로 비교한다."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[];pages=[]
for char,tag in [('shibuki','br_v31'),('nana','rn_v43')]:
    plan=json.loads((W/f'staging_{tag}.json').read_text('utf8'));src=plan['resources']['PL00_U.ARC'];blob=(ROOT/src['path']).read_bytes();assert sha(blob)==src['after'];a=Archive(blob)
    refs=[0,221,223,225,227,229,222,224,226,228,230];masks=[8,9,10,12,15]
    box=(128,120,196,188);scale=2;cw=144;ch=160
    sheet=Image.new('RGB',(cw*len(refs),ch*len(masks)),'#26313f');d=ImageDraw.Draw(sheet)
    for row,mask in enumerate(masks):
        for col,ref in enumerate(refs):
            im=a.composite(ref,mask)[0];p=im.crop(box).resize((136,136),Image.Resampling.NEAREST)
            sheet.paste(p,(col*cw+4,row*ch+22),p);d.text((col*cw+4,row*ch+4),f'mask {mask:X} ref {ref}',fill='white')
            rows.append({'character':char,'mask':mask,'ref':ref,'rgba_sha256':sha(im.tobytes())})
    p=O/f'{char}_hover_partial_masks.png';sheet.save(p);pages.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())})
(O/'hover_partial_manifest.json').write_text(json.dumps({'scope':'현재 기본/포스 발파츠 보유 마스크8/9/A/C/F의 대기+호버10그림 정적 검토','rows':rows,'pages':pages,'runtime_verified':False,'actually_viewed':False,'game_assets_changed':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'canvases':len(rows),'pages':len(pages)}))
