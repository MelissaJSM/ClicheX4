"""73/74의 몸체와 별도9조립 효과를 원래 native 자원에서 분리·검증한다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write
from src.psx_player import composition_frame,compose_indices
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent');out=D/'effects';out.mkdir(exist_ok=True);records=[]
    for original,n in((71,73),(72,74)):
        old=a.layer(original)[0];full=a.layer(n)[0];f=a.banks[0]['frames'][n];raw=a.raw[f['offset'],f['tile_count']].data;cp=composition_frame(a.c,0,n);base=composition_frame(a.c,0,original);keys=('flags','tile','x','y');need([{k:q[k]for k in keys}for q in cp['parts'][:len(base['parts'])]]==[{k:q[k]for k in keys}for q in base['parts']],'Body prefix exact');extra=copy.deepcopy(cp);extra['parts']=cp['parts'][len(base['parts']):];need(len(extra['parts'])==9,'Original9 effects');pix,size,box,_=compose_indices(raw,f['tile_count'],extra,allowed_cluts={0});small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);fx=np.zeros((384,384),np.uint8);yy,xx=np.nonzero(small);fx[yy+box[1]+160,xx+box[0]+160]=small[yy,xx];rebuilt=old.copy();rebuilt[fx>0]=fx[fx>0];need(np.array_equal(full,rebuilt),'Original reconstructed full');Image.fromarray(fx).save(out/f'effect_{n:03}.png');a.rgba(fx).save(out/f'effect_{n:03}_rgba.png');records.append({'ref':n,'body_ref':original,'parts':extra['parts'],'effect_pixels':int(np.count_nonzero(fx)),'effect_sha256':sha(fx.tobytes()),'original_reconstructed_exact':True,'layer_order':'effect on top of base body; armor layers afterward'})
    write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':records,'scope':'원본 효과 추출만. 이후 새 몸체 등록에도 이 효과의 색/알파/좌표를 유지해야 한다.'});print(json.dumps(records))
if __name__=='__main__':main()
