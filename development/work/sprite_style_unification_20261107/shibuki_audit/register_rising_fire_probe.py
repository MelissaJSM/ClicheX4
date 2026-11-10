"""라이징 파이어 원화를 고정 1/8 배율·기존 팔레트로만 등록한다."""
from pathlib import Path
import sys, argparse, json
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from PIL import Image
import numpy as np
from scipy.ndimage import label
from scripts.export_x_consistency import Archive, page, metrics
from native_pose_pack import need, sha, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--page', type=int, required=True)
    parser.add_argument('--source')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    metadata_path = H/'rising_fire_inputs01/structure.json'
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    layout = next(p for p in metadata['pages'] if p['page'] == args.page)
    src = H/(args.source or f'rising_fire_inputs01/page{args.page:02}/generated.png')
    out = (H/args.out).resolve()
    need(out.is_relative_to(H.resolve()) and out != H.resolve(), 'Output outside owned work')
    need(not out.exists(), 'Fresh output required')
    image = Image.open(src).convert('RGBA')
    need(image.size == (1536, 1024), 'Unexpected source resolution')
    full = np.array(image)
    sampled = np.array(image.resize((192,128), Image.Resampling.NEAREST))
    out.mkdir()
    rows, reviews = [], {}
    for slot in layout['slots']:
        form, ref, pal = slot['form'], slot['ref'], slot['palette']
        name = 'PL02_U.ARC' if form.startswith('ultimate') else 'PL00_U.ARC'
        resource = metadata['resources'][name]
        data = (ROOT/resource['path']).read_bytes()
        need(sha(data) == resource['sha256'], 'Parent resource changed')
        arc = Archive(data)
        mask = 15 if form in ('fourth','ultimate_before') else 0
        px, py = slot['page_origin']
        col, row = (px-256)//512, (py-288)//512
        cell = sampled[row*64:(row+1)*64,col*64:(col+1)*64]
        colors = np.array([[(int(w)>>s & 31)*255//31 for s in (0,5,10)]
                           for w in arc.words[pal:pal+16]],np.int32)
        distance = ((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3)
        quantized = (1+distance.argmin(2)).astype(np.uint8)
        quantized[cell[:,:,3] < 128] = 0
        indexed = np.zeros((384,384),np.uint8)
        indexed[124:188,128:192] = quantized
        stem = f'{form}_{ref:03}'
        Image.fromarray(indexed).save(out/f'{stem}_indices.png')
        native = arc.rgba(indexed,pal)
        native.save(out/f'{stem}.png')
        old = arc.composite(ref,mask)[0]
        idle = arc.composite(0,mask)[0]
        page([(f'{ref} previous',old),(f'{ref} new 1/8',native)],idle,out/f'{stem}_comparison.png',cols=2,scale=5)
        reviews.setdefault(form, {'idle':idle,'items':[]})['items'].extend([(f'{ref} previous',old),(f'{ref} new',native)])
        labels, count = label(quantized>0,np.ones((3,3)))
        sizes = sorted(np.bincount(labels.ravel())[1:].tolist(),reverse=True)
        pixel_crop = full[row*512:(row+1)*512,col*512:(col+1)*512]
        rows.append({'form':form,'ref':ref,'source':src.relative_to(ROOT).as_posix(),
                     'source_sha256':sha(src.read_bytes()),'resource_sha256':resource['sha256'],
                     'palette_start':pal,'scale':0.125,'world_crop':[-32,-36,32,28],
                     'alpha_threshold':128,'native_index_sha256':sha(indexed.tobytes()),
                     'old':metrics(old),'new':metrics(native),'idle':metrics(idle),
                     'connected_components':sizes,'sampled_alpha_ge128':int((cell[:,:,3]>=128).sum()),
                     'source_alpha_1_to127_discarded':int(((pixel_crop[:,:,3]>0)&(pixel_crop[:,:,3]<128)).sum()),
                     'old_pixels_pasted':0,'local_scaling':False,'registration_translation':[0,0]})
    for form, review in reviews.items():
        page(review['items'],review['idle'],out/f'{form}_comparison.png',cols=2,scale=4)
    write(out/'report.json',{'page':args.page,'source_sha256':sha(src.read_bytes()),
          'layout_sha256':sha(metadata_path.read_bytes()),'rows':rows,'artifact':'native_registration_probe',
          'notes':['전역 고정 1/8 변환과 기존 CLUT 양자화만 수행했다.',
                   '알파 128 미만은 동일 규칙으로 제외하며 배경만 별도 색상 제거하지 않았다.',
                   '모양·관절·효과 접점의 최종 검토 전 후보이며 게임 적용 증거가 아니다.'],
          'arc_or_game_written':False,'visual_review_complete':False})
    print(json.dumps([{'form':r['form'],'ref':r['ref'],'old':r['old']['bbox'],'new':r['new']['bbox'],
                      'components':r['connected_components']} for r in rows]))


if __name__ == '__main__':
    main()
