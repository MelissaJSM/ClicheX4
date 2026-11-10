"""원본 X 이동/사격 공유 구조와 동일 배율 제작 기준을 읽기 전용으로 추출한다."""
import json,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from scripts.project import new_run,write_json
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame,bank_offsets

def main():
    pointer=json.loads((ROOT/'projects/ver_buki_riko/shibuki_source_inventory.json').read_text(encoding='utf-8'))
    source=(ROOT/pointer['inventory']).parent;inv=json.loads((source/'inventory.json').read_text(encoding='utf-8'))
    if sha256((source/'original.arc').read_bytes())!=inv['archive']['sha256']:raise ValueError('Changed source ARC')
    selected=json.loads((ROOT/'projects/ver_buki_riko/shibuki_art_selection.json').read_text(encoding='utf-8'))
    if selected['status']!='accepted_design_basis':raise ValueError('Accepted design required')
    art=ROOT/selected['indexed_png']
    if sha256(art.read_bytes())!=selected['indexed_sha256']:raise ValueError('Changed design')
    run=inv['animations'][8];steps=run['steps'];order=[s['frame'] for s in steps]
    if order!=[29,31,5,7,9,11,13,15,17,19,21,23,25,27]:raise ValueError('Unexpected run sequence')
    parts=(source/'composition_entry.bin').read_bytes();pairs=[]
    for n in range(1,33,2):
        a,b=inv['base_frames'][n:n+2]
        if a['offset']!=b['offset'] or inv['stream_sharing'][str(a['offset'])]!=[[0,n],[0,n+1]]:
            raise ValueError('Unexpected run/shot stream sharing')
        base=set(q['tile'] for q in a['composition']['parts']);shot=set(q['tile'] for q in b['composition']['parts'])
        overlays={str(bank):sorted({q['tile'] for q in composition_frame(parts,bank,n)['parts']}|
                                  {q['tile'] for q in composition_frame(parts,bank,n+1)['parts']}) for bank in (5,6,7,8)}
        pairs.append({'frames':[n,n+1],'stream':a['offset'],'budget':a['compressed_end']-a['offset'],
                      'tile_count':a['tile_count'],'common_base_tiles':sorted(base&shot),
                      'nonshoot_only_tiles':sorted(base-shot),'shoot_only_tiles':sorted(shot-base),
                      'armor_overlay_tiles':overlays,'bounds':[a['bounds'],b['bounds']]})
    out=new_run(ROOT,'ver_buki_riko','shibuki_run_plan')
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
    def frame(n):
        item=inv['base_frames'][n];im=Image.open(source/item['image']).convert('RGBA')
        if not item['rendered']:raise ValueError('Run frame not rendered')
        return im,item['bounds']
    def draw_cell(sheet,n,x,y,scale=3,label=True):
        im,bb=frame(n);d=ImageDraw.Draw(sheet)
        if label:d.text((x+5,y+3),f'X {n:03}',font=font,fill='white')
        big=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
        ox,oy=x+44*scale,y+37*scale
        sheet.paste(big,(ox+bb[0]*scale,oy+bb[1]*scale),big)
        d.line((x+6,oy+23*scale,x+82*scale,oy+23*scale),fill='#45556b')
    sheet=Image.new('RGB',(8*264,4*216),'#222630')
    numbers=[n for n in range(1,33,2)]+[n for n in range(2,33,2)]
    for i,n in enumerate(numbers):draw_cell(sheet,n,(i%8)*264,(i//8)*216)
    sheet.save(out/'original_run_and_shot_3x.png')
    keyframes=[29,7,15,21];key=Image.new('RGBA',(4*352,288),(0,0,0,0))
    for i,n in enumerate(keyframes):draw_cell(key,n,i*352,0,4,False)
    key.save(out/'original_keyposes_4x.png')
    for shot in (False,True):
        pictures=[]
        for n in order:
            im=Image.new('RGB',(264,216),'#222630');draw_cell(im,n+int(shot),0,0);pictures.append(im)
        pictures[0].save(out/('original_shot_preview.gif' if shot else 'original_run_preview.gif'),save_all=True,
                         append_images=pictures[1:],duration=[round(s['duration_ticks']*1000/60) for s in steps],loop=0,disposal=2)
    write_json(out/'plan.json',{'task':'x_shibuki','source_inventory':pointer['inventory'],
        'source_sha256':inv['source_sha256'],'arc_sha256':inv['archive']['sha256'],
        'accepted_art':selected['candidate'],'start_animation':inv['animations'][7],'run_animation':run,
        'loop_ticks':sum(s['duration_ticks'] for s in steps),'paired_frames':pairs,'keyposes':keyframes,
        'evidence':['work/research/decomp/src/main/player.c:192','work/research/decomp/src/main/player.c:209',
                    'work/research/decomp/src/main/player_animations.c:354','work/research/decomp/src/main/player_animations.c:360'],
        'shooting_pair_semantics':'Shared streams and distinct arm compositions locally verified; live shooting test pending',
        'generated_art':False,'game_applied':False,'runtime_verified':False,
        'preview_timing_assumption':'60 updates/sec; GIF is not runtime evidence'})
    print(json.dumps({'output':str(out),'shared_pairs':len(pairs),'run_frames':len(order),'loop_ticks':sum(s['duration_ticks'] for s in steps)}))

if __name__=='__main__':main()
