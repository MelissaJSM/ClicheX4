"""완성 기본형과 남은 아머의 공유 관계를 추출한다. 입력 전용."""
import json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_armor import entries
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts

def main():
    out=ROOT/'work/ver_buki_riko/shibuki_art/fourth_armor_remaining_v1';out.mkdir(exist_ok=True)
    parent=ROOT/'out/ver_buki_riko/shibuki_fourth_run_20261027T010834425294Z'
    es=entries((parent/'modified.arc').read_bytes());g,c,pal=es[2],es[3],es[9]
    bank=graphics_bank(g,0,allow_bank_aliases=True);words=struct.unpack_from('<16H',pal)
    done={0,*range(1,33),*range(115,120)};blank={105,*range(175,183),198}
    groups={};items=[]
    for f in bank['frames']:
        n=f['index']
        if n in done|blank:continue
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        v=canvas_from_parts(raw,f['tile_count'],composition_frame(c,0,n))
        im=save_image(v.tobytes(),(160,160),words,out/f'base_{n:03}.png').convert('RGBA')
        groups.setdefault(f['offset'],[]).append(n)
        items.append({'frame':n,'bbox':im.getbbox(),'counts':{str(b):len(composition_frame(c,b,n)['parts']) for b in (0,5,6,7,8)},'opaque':{str(b):int((canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,n))>0).sum()) for b in (5,6,7,8)},'stream':f['offset'],'tiles':f['tile_count']})
    for start in range(0,len(items),48):
        sheet=Image.new('RGB',(1440,1104),'#253546');d=ImageDraw.Draw(sheet)
        for i,item in enumerate(items[start:start+48]):
            im=Image.open(out/f"base_{item['frame']:03}.png").convert('RGBA').crop((30,30,130,122)).resize((180,166),Image.Resampling.NEAREST)
            x=i%8*180;y=i//8*184;sheet.paste(im,(x,y+18),im);d.text((x+8,y+2),str(item['frame']),fill='white')
        sheet.save(out/f'base_contact_{start//48}.png')
    (out/'plan.json').write_text(json.dumps({'parent':str(parent.relative_to(ROOT)),'done':sorted(done),'blank_or_placeholder':sorted(blank),'frames':items,'shared_groups':list(groups.values()),'user_authorized_all_remaining':True},indent=2),encoding='utf-8')
    print(json.dumps({'output':str(out),'remaining':len(items),'streams':len(groups),'special_counts':[v for v in items if any(v['counts'][str(b)]==0 for b in (5,6,7,8))]}))
if __name__=='__main__':main()
