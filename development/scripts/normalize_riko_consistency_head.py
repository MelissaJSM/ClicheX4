"""Register generated wall-head art to the existing palette and pixel scale."""
import json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'work/sprite_consistency_20261105/zero/riko/wall_fix/art'

def main():
    old=Image.open(ROOT/'work/ver_buki_riko/art_pilot/wall_v1/rear_head_indexed.png')
    source=Image.open(D/'generated_v2.png').convert('RGBA')
    a=np.array(source);a[:,:,3]=np.where(a[:,:,3]>=192,255,0);source=Image.fromarray(a)
    bounds=source.getbbox();crop=source.crop(bounds);data=np.array(crop)
    colors=np.array(old.getpalette()[:48],np.int32).reshape(16,3)[1:]
    nearest=np.zeros(data.shape[:2],np.uint8)
    for y in range(data.shape[0]):nearest[y]=np.argmin(((data[y,:,:3].astype(np.int32)[:,None]-colors[None])**2).sum(2),axis=1)+1
    scale=23/crop.width;size=(23,round(crop.height*scale))
    coverage=np.stack([np.array(Image.fromarray(np.where(nearest==i,data[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX),dtype=np.float32) for i in range(1,16)])
    alpha=np.array(crop.getchannel('A').resize(size,Image.Resampling.BOX))
    # Preserve the narrow purple eye actually present in generated art. This is
    # color-coverage quantization, not a new hand-painted eye or a palette edit.
    weights=np.ones(15,np.float32);weights[4]=2.5
    px=np.where(alpha>=128,np.argmax(coverage*weights[:,None,None],axis=0)+1,0).astype(np.uint8)
    if not np.count_nonzero(px==5):raise ValueError('Generated purple eye disappeared during registration')
    im=Image.fromarray(px,'P');im.putpalette(old.getpalette());im.save(D/'head_v2_registered.png',transparency=0)
    im.convert('RGBA').resize((size[0]*20,size[1]*20),Image.Resampling.NEAREST).save(D/'head_v2_registered_20x.png')
    report={'source_sha256':hashlib.sha256((D/'generated_v2.png').read_bytes()).hexdigest(),'crop':bounds,'uniform_scale':scale,'native_size':size,
      'palette_preserved':True,'purple_eye_coverage_weight':2.5,'purple_eye_pixels':int(np.count_nonzero(px==5)),
      'native_png':'head_v2_registered.png','head_only':True,'anchor_not_yet_registered':True,'art_method':'built-in imagegen; coverage-vote native palette normalization'}
    (D/'registration.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))

if __name__=='__main__':main()
