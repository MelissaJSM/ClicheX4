"""삽입 ARC를 다시 읽어 이동 아머의 파츠와 부분 장착 조합을 검증한다."""
import argparse, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.analyze_shibuki_armor import entries
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank, decode_stream, composition_frame
from src.psx_sprite_batch import canvas_from_parts

def main():
    p = argparse.ArgumentParser(); p.add_argument('--build', type=Path, required=True); args = p.parse_args()
    build = args.build.resolve()
    if not build.is_relative_to(ROOT/'out/ver_buki_riko'): raise ValueError('Isolated build required')
    manifest = json.loads((build/'manifest.json').read_text(encoding='utf-8'))
    recipe = json.loads((build/'recipe.json').read_text(encoding='utf-8'))
    arc = (build/'modified.arc').read_bytes()
    if manifest['task'] != 'fourth_armor_shibuki' or sha256(arc) != manifest['modified_archive_sha256']: raise ValueError('Wrong armor build')
    art = ROOT/recipe['source_art']; es = entries(arc); g,c,pal = es[2],es[3],es[9]
    bank = graphics_bank(g,0,allow_bank_aliases=True)
    words = [list(struct.unpack_from('<16H',pal,i*32)) for i in range(3)]
    out = build/'armor_motion_review'; out.mkdir(exist_ok=False)
    pictures = {}; checks = []
    def rgba(a, row):
        return save_image(a.tobytes(),(160,160),words[row],out/'temporary_layer.png').convert('RGBA')
    for n in recipe['edited_frame_references']:
        f = bank['frames'][n]; raw = decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        layers = {bi:canvas_from_parts(raw,f['tile_count'],composition_frame(c,bi,n)) for bi in (0,5,6,7,8)}
        targets = {bi:np.array(Image.open(art/f'{kind}_{n:03}.png')) for kind,bi in (('head',5),('body',6),('arm',7),('leg',8))}
        for bi in targets:
            if not np.array_equal(layers[bi], targets[bi]): raise ValueError(f'Inserted layer differs {n}/{bi}')
        base = Image.open(art/f'base_{n:03}.png').convert('RGBA')
        if not np.array_equal(np.array(base),np.array(rgba(layers[0],0))): raise ValueError('Base art differs')
        for arm_type in (1,2):
            for mask in range(16):
                pic = rgba(layers[0],0); expected = base.copy()
                for bit,bi in ((8,8),(1,5),(4,7),(2,6)):
                    if mask&bit:
                        row = 2 if bi==7 and arm_type==2 else 1
                        pic.alpha_composite(rgba(layers[bi],row)); expected.alpha_composite(rgba(targets[bi],row))
                if not np.array_equal(np.array(pic),np.array(expected)): raise ValueError('Part combination differs')
                if mask==15 and not np.array_equal(np.array(pic),np.array(Image.open(art/f'full_{n:03}.png').convert('RGBA'))): raise ValueError('Full outfit differs')
                checks.append({'frame':n,'mask':mask,'arm_type':arm_type,'raster_equal':True})
                if arm_type==2:
                    pic.save(out/f'frame_{n:03}_mask{mask:02}.png')
                    if mask==15: pictures[n] = pic
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
    order = [1,3,29,31,5,7,9,11,13,15,17,19,21,23,25,27]
    sheet = Image.new('RGB',(1344,1130),'#253546'); draw = ImageDraw.Draw(sheet)
    for i,n in enumerate(order):
        x = i%4*336; y=i//4*270
        draw.text((x+8,y+6),f'{n}/{n+1} 이동 / 이동 사격',font=font,fill='white')
        for j,f in enumerate((n,n+1)):
            im=pictures[f].crop((45,48,101,108)).resize((168,180),Image.Resampling.NEAREST)
            sheet.paste(im,(x+j*168,y+40),im)
    draw.text((12,1090),'패치 ARC 재조립 미리보기 / 게임 실행 화면 아님',font=font,fill='white')
    sheet.save(out/'run_shoot_review.png')
    plan=json.loads((ROOT/'work/ver_buki_riko/shibuki_run_plan/20261026T044831801392Z/plan.json').read_text(encoding='utf-8'))
    steps=plan['run_animation']['steps']
    frames=[];durations=[]
    for shooting in (0,1):
        for _ in range(3):
            for step in steps:
                if step['frame'] not in pictures or step['duration_ticks']>10: continue
                im=pictures[step['frame']+shooting]; bg=Image.new('RGB',(160,160),'#253546'); bg.paste(im,(0,0),im)
                frames.append(bg.crop((40,45,110,115)).resize((420,420),Image.Resampling.NEAREST))
                durations.append(max(20,round((step['duration_ticks']+1)*1000/60)))
    frames[0].save(out/'run_and_shoot.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2)
    report={'source_arc_sha256':sha256(arc),'static_only':True,'runtime_verified':False,'combinations_checked':len(checks),'checks':checks,'animation_source':str(plan['run_animation']['address']),'timing_note':'Preview uses duration+1 ticks at 60Hz; game data itself unchanged'}
    (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(out),'combinations_checked':len(checks)}))
if __name__=='__main__': main()
