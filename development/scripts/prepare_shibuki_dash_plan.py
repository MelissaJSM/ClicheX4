"""미국판 X 지상 대시의 몸/사격 공유와 속도선 파츠를 읽기 전용 조사한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko');args=parser.parse_args();name='nana' if args.project=='ver_rin_nana' else 'shibuki'
    source=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z'
    inv=json.loads((source/'inventory.json').read_text());parts=(source/'composition_entry.bin').read_bytes()
    if sha256((source/'original.arc').read_bytes())!=inv['archive']['sha256']:raise ValueError('Original extraction changed')
    out=ROOT/'work'/args.project/(name+'_art')/'dash_v1';out.mkdir(parents=True,exist_ok=True);pairs=[]
    numbers=[67,69,71,75,77,79,81,83]
    aliases={71:[73],72:[74]}
    for n in numbers:
        a,b=inv['base_frames'][n:n+2]
        expected=[[0,n],[0,n+1]]+([[0,73],[0,74]] if n==71 else [])
        if a['offset']!=b['offset'] or inv['stream_sharing'][str(a['offset'])]!=expected:raise ValueError('Unexpected alias')
        aa={q['tile'] for q in a['composition']['parts']};bb={q['tile'] for q in b['composition']['parts']}
        armor={str(bank):sorted({q['tile'] for k in (n,n+1) for q in composition_frame(parts,bank,k)['parts']}) for bank in (5,6,7,8)}
        if (aa|bb)&{t for ts in armor.values() for t in ts}:raise ValueError('Base overlaps armor')
        if n==71:
            for primary,alias in ((71,73),(72,74)):
                p=composition_frame(parts,0,primary)['parts'];q=composition_frame(parts,0,alias)['parts']
                signature=lambda r:(r['flags'],r['tile'],r['x'],r['y'])
                if sorted(map(signature,p))!=sorted(map(signature,q[:len(p)])):raise ValueError('Alias body differs')
                if len(q[len(p):])!=9 or {r['tile'] for r in q[len(p):]}!={6}:raise ValueError('Unexpected speed streak records')
                if 6 in aa|bb:raise ValueError('Speed tile overlaps body')
        pairs.append({'frames':[n,n+1],'stream':a['offset'],'budget':a['compressed_end']-a['offset'],'tile_count':a['tile_count'],
            'common_base_tiles':sorted(aa&bb),'nonshoot_only_tiles':sorted(aa-bb),'shoot_only_tiles':sorted(bb-aa),
            'armor_overlay_tiles':armor,'part_counts':[len(a['composition']['parts']),len(b['composition']['parts'])],'bounds':[a['bounds'],b['bounds']]})
    frames=list(range(67,85));animations={str(a['id']):a for a in inv['animations'] if any(s['frame'] in frames for s in a.get('steps',[]))}
    plan={'task':'x_'+name,'source_inventory':str((source/'inventory.json').relative_to(ROOT)),'frames':frames,
        'body_frames':numbers,'aliases':aliases,'preserved_speed_streak_tile':6,'animations':animations,
        'run_animation':inv['animations'][16],'end_animation':inv['animations'][17],'paired_frames':pairs,
        'evidence':'US extracted animations; work/research/decomp/src/main/player.c:506-603',
        'other_uses':'71/73/75 also air dash animation18; 81 also39/101/104/105. These entire actions are not completed by this group.',
        'art_produced':False,'runtime_verified':False}
    (out/'plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps({'out':str(out),'pairs':pairs,'other_uses':plan['other_uses']}))
    if name=='nana':
        from PIL import Image,ImageDraw
        board=Image.new('RGB',(4*288,4*260),'#28394b');draw=ImageDraw.Draw(board)
        for i,n in enumerate(numbers):
            for j in range(2):
                q=inv['base_frames'][n+j];pic=Image.open(source/q['image']).convert('RGBA');pic=pic.resize((pic.width*3,pic.height*3),Image.Resampling.NEAREST);x,y=i%4*288,(i//4*2+j)*260;board.paste(pic,(x+144+q['bounds'][0]*3,y+100+q['bounds'][1]*3),pic);draw.text((x+8,y+8),f"X {n+j:03d}",fill='white')
        board.save(out/'native_dash_reference.png')

if __name__=='__main__':main()
