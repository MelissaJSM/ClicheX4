"""Single-pose input crops; only authored-source registration, no painting."""
from pathlib import Path
import json,sys
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from prepare_fourth_joint_edits import registered_rgba
from preview_restore import need,write,digest

def main():
    out=D/'fourth51_edit_inputs';need(not out.exists(),'Fresh inputs');out.mkdir()
    base,br,bp=registered_rgba(51,'base');base.save(out/'base_pose.png')
    doc=json.loads((D/'fourth_joint_registered_v1/registration.json').read_text('utf8'));r=next(r for r in doc['frames']if r['ref']==51)
    p=ROOT/r['source'];need(digest(p)==r['source_sha256'],'Source');crop=Image.open(p).convert('RGBA').crop(r['source_crop']);scale=10
    width=r['native_width']*scale;hu=r['height_above']*scale;hl=r['height_below']*scale;split=r['split']
    figure=Image.new('RGBA',(width,hu+hl));figure.alpha_composite(crop.crop((0,0,crop.width,split)).resize((width,hu),Image.Resampling.LANCZOS));figure.alpha_composite(crop.crop((0,split,crop.width,crop.height)).resize((width,hl),Image.Resampling.LANCZOS),(0,hu))
    canvas=Image.new('RGBA',(800,800));ox,oy=r['native_position'];canvas.alpha_composite(figure,((ox+40)*10,(oy+36)*10));canvas.save(out/'fourth_edit_target.png')
    write(out/'manifest.json',{'ref':51,'source':r['source'],'source_sha256':r['source_sha256'],'registration':r,'base_source':str(bp.relative_to(ROOT)),'base_source_sha256':digest(bp),'scope':'동일 월드 좌표에 등록한 기존 생성 원화만 배치. 새로운 미술 픽셀 없음.'})
if __name__=='__main__':main()
