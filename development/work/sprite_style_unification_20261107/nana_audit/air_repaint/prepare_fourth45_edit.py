"""Newly authored RGBA 45 pose references, at the existing world origin."""
from pathlib import Path
import sys,json
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(D.parent/'native_restore')]
from preview_restore import need,write,digest
def main():
    out=D/'fourth45_edit_inputs';need(not out.exists(),'Fresh');out.mkdir();rows=[]
    for name,folder in [('base','basic_landing_registered_v2'),('fourth','fourth_b_registered_v1')]:
        doc=json.loads((D/folder/'registration.json').read_text('utf8'));r=next(r for r in doc['frames']if r['ref']==45);p=D/folder/'source_045.png';crop=Image.open(p).convert('RGBA');width=r['native_width']*10;hu=r['height_above']*10;hl=r['height_below']*10;split=r['split'];ox,oy=r['native_position'];figure=Image.new('RGBA',(width,hu+hl));figure.alpha_composite(crop.crop((0,0,crop.width,split)).resize((width,hu),Image.Resampling.LANCZOS));figure.alpha_composite(crop.crop((0,split,crop.width,crop.height)).resize((width,hl),Image.Resampling.LANCZOS),(0,hu));canvas=Image.new('RGBA',(800,800));canvas.alpha_composite(figure,((ox+40)*10,(oy+36)*10));canvas.save(out/f'{name}_pose.png');rows.append({'name':name,'source_crop':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'registration':r})
    write(out/'manifest.json',{'ref':45,'inputs':rows,'new_art':False})
if __name__=='__main__':main()
