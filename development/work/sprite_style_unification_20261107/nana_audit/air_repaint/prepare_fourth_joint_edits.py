"""등록 메타데이터에서 고해상도 원화 비율을 복원한 관절 보완 가이드."""
from pathlib import Path
import sys,json
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import digest,write,need
SCALE=10;CELL=800
def source_reg(n,form):
    if form=='base':
        folder='basic_middle_registered_v2'if n==37 else'basic_registered_v2';art='basic_middle_v1'if n==37 else'basic_keys_v1'
    else:
        key={37:'a',47:'b',51:'c'}[n];folder=f'fourth_{key}_registered_v1';art=f'fourth_air_{key}_v1'
    doc=json.loads((D/folder/'registration.json').read_text('utf8'));r=next(r for r in doc['frames']if r['ref']==n);p=D/art/'generated.png';expected=r.get('source_sha256',doc.get('source_art_sha256'));need(digest(p)==expected,'Source art')
    return r,p
def registered_rgba(n,form):
    r,p=source_reg(n,form);crop=Image.open(p).convert('RGBA').crop(r['source_crop']);width=r['native_width']*SCALE;split=r['split'];hu=r['height_above']*SCALE;hl=r['height_below']*SCALE
    top=crop.crop((0,0,crop.width,split)).resize((width,hu),Image.Resampling.LANCZOS);lower=crop.crop((0,split,crop.width,crop.height)).resize((width,hl),Image.Resampling.LANCZOS)
    figure=Image.new('RGBA',(width,hu+hl));figure.alpha_composite(top);figure.alpha_composite(lower,(0,hu));out=Image.new('RGBA',(CELL,CELL));ox,oy=r['native_position'];out.alpha_composite(figure,((ox+40)*SCALE,(oy+36)*SCALE));return out,r,p
def main():
    out=D/'fourth_joint_edit_inputs';out.mkdir(exist_ok=True);report=[]
    for form in('base','fourth'):
        sheet=Image.new('RGBA',(CELL*2,CELL*2))
        for i,n in enumerate((37,47,51)):
            cell,r,p=registered_rgba(n,form);sheet.alpha_composite(cell,(i%2*CELL,i//2*CELL));report.append({'form':form,'ref':n,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'registration':r,'note':'Original RGBA resized according to the already used eye/foot registration; no clothing recolouring or newly drawn pixels.'})
        sheet.save(out/f'{form}_registered_source.png')
    write(out/'manifest.json',{'frames':report,'positions':['top-left37','top-right47','bottom-left51'],'note':'Both sheets share world-origin and actual head/eye/foot scale. Basic51 sole correction is in native index only; final foot anchors will be checked separately.','new_art':False})
if __name__=='__main__':main()
