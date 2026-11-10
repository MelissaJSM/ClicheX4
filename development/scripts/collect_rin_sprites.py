"""현재 BIN의 린 몸체·메타데이터·오프라인 동작 미리보기를 한곳에 수집한다."""
import argparse,html,json,struct,sys
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_idle import entry,sha
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.build_riko_idle import SHIPPUUGA_BODY,SHIPPUUGA_NEW
from src.psx_air_spin import BODY as SPIN
from src.psx_ice import BODY as ICE
from src.psx_ryuenjin import BODY as RISE
from src.psx_rakuhouha import BODY as BURST
from src.psx_raijingeki import BODY as THRUST
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
from src.psx_static_effect import compose_static
GROUPS={'spin':(1,SPIN),'ice':(1,ICE),'rise':(1,RISE),'burst':(1,BURST),'thrust':(1,THRUST),'dashslash':(0,SHIPPUUGA_BODY),'ride_chaser':(1,set(range(14,50))),'ride_armor_head':(1,set(range(66,86)))}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path);args=ap.parse_args()
    build=(args.build or ROOT/json.loads((ROOT/'projects/ver_rin_nana/current_build.json').read_text('utf-8'))['build']).resolve()
    if not build.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Unexpected build')
    m=json.loads((build/'manifest.json').read_text('utf-8'));arc=(build/'modified.arc').read_bytes()
    if sha(arc)!=m['modified_archive_sha256'] or digest(build/'rin_nana.bin')!=m['modified_bin']['sha256']:raise ValueError('Build identity differs')
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'));extract=ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z';original=(extract/'original.arc').read_bytes();exe=(extract/'original.exe').read_bytes()
    if sha(original)!=profile['zero_archive']['sha256'] or sha(exe)!=profile['executable']['sha256']:raise ValueError('Original source identity differs')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'out/ver_rin_nana'/('sprite_review_'+stamp);out.mkdir();(out/'native').mkdir();(out/'animations').mkdir();(out/'original_guides').mkdir()
    _,g=entry(arc,2);_,parts=entry(arc,3);_,palette=entry(arc,9);words=struct.unpack_from('<64H',palette)
    _,og=entry(original,2);_,oparts=entry(original,3);_,opal=entry(original,9);owords=struct.unpack_from('<64H',opal)
    selected={0:set(m['cumulative_frames']),1:set(m.get('cumulative_bank1_frames',[]))};frames={};pictures={}
    def render(gfx,ps,bi,n):
        f=graphics_bank(gfx,bi)['frames'][n];c=composition_frame(ps,0 if bi==0 else 5,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128)
        return f,c,raw,compose_launch(raw.data,f['tile_count'],c)
    def cell(pic,bounds,scale=3):
        result=Image.new('RGBA',(112,112));result.alpha_composite(pic.convert('RGBA'),(56+bounds[0],56+bounds[1]));return result.resize((112*scale,112*scale),Image.Resampling.NEAREST)
    for bi,ids in selected.items():
        for n in sorted(ids):
            f,c,raw,(pixels,size,bounds,_)=render(g,parts,bi,n);key=f'bank{bi}_{n:03d}';path=out/'native'/f'{key}.png';pic=save_image(pixels,size,words,path);pictures[key]=pic
            (out/'native'/f'{key}.indices').write_bytes(pixels)
            frames[key]={'graphics_bank':bi,'parts_bank':0 if bi==0 else 5,'frame':n,'bounds':bounds,'origin':[-bounds[0],-bounds[1]],'size':size,'parts':c['parts'],'stream_offset':f['offset'],'tile_count':f['tile_count'],'decoded_sha256':sha(raw.data),'indices_sha256':sha(pixels),'png_sha256':digest(path),'opaque_pixels':sum(v!=0 for v in pixels),'image':path.relative_to(out).as_posix()}
    (out/'palette.bin').write_bytes(palette)
    static_frames={};static=m.get('verification',{}).get('embedded_static_bodies')
    if static:
        recipe=Path(static['recipe'])
        if digest(recipe)!=static['recipe_sha256']:raise ValueError('Static recipe changed')
        sm=json.loads(recipe.read_text('utf-8'));pal_path=recipe.parent/sm['palette_file'];sw=struct.unpack('<16H',pal_path.read_bytes())
        if digest(pal_path)!=sm['palette_sha256']:raise ValueError('Static palette changed')
        (out/'static_palette.bin').write_bytes(pal_path.read_bytes());texture=entry(arc,0x10206)[1]
        for n in (23,24):
            c=composition_frame(parts,6,n);px,sz,bb,_=compose_static(texture,c);key=f'static6_{n:03d}';path=out/'native'/f'{key}.png';save_image(px,sz,sw,path);(out/'native'/f'{key}.indices').write_bytes(px)
            static_frames[key]={'parts_bank':6,'frame':n,'bounds':bb,'parts':c['parts'],'image':path.relative_to(out).as_posix(),'png_sha256':digest(path),'palette':'static_palette.bin'}
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
    for bi,ids in selected.items():
        cols=10;sheet=Image.new('RGB',(cols*168,((len(ids)+cols-1)//cols)*184),(34,37,47));draw=ImageDraw.Draw(sheet)
        for i,n in enumerate(sorted(ids)):
            key=f'bank{bi}_{n:03d}';p=cell(pictures[key],frames[key]['bounds'],1).resize((168,168),Image.Resampling.NEAREST);x=i%cols*168;y=i//cols*184;sheet.paste(p,(x,y+16),p);draw.text((x+5,y+2),key,fill='white')
        sheet.save(out/f'bank{bi}_all.png')
    guides={}
    for name,(bi,ids) in GROUPS.items():
        sheet=Image.new('RGB',(5*224,((len(ids)+4)//5)*240),(34,37,47));draw=ImageDraw.Draw(sheet);records={}
        for i,n in enumerate(sorted(ids)):
            try:_,c,_,(pixels,size,bounds,_)=render(og,oparts,bi,n)
            except ValueError as error:
                if name!='ride_chaser' or n not in range(42,50):raise
                records[str(n)]={'bounds':None,'image':None,'already_authored':False,'status':'unresolved_original_source','error':str(error)};draw.text((i%5*224+5,i//5*240+2),f'{bi}:{n} SOURCE UNRESOLVED',fill='white');continue
            path=out/'original_guides'/f'{name}_{n:03d}.png';pic=save_image(pixels,size,owords,path);p=cell(pic,bounds,2);x=i%5*224;y=i//5*240;sheet.paste(p,(x,y+16),p);draw.text((x+5,y+2),f'{bi}:{n}',fill='white');records[str(n)]={'bounds':bounds,'parts':c['parts'],'image':path.relative_to(out).as_posix(),'already_authored':n in selected[bi]}
        if name=='ride_armor_head':records['80']['status']='intentional_blank_preserved'
        sheet.save(out/'original_guides'/f'{name}_original.png');guides[name]={'bank':bi,'frames':records,'remaining':[n for n in sorted(ids) if n not in selected[bi] and not (bi==1 and n==80)]}
    def read(address,length):
        off=address-profile['executable']['load_address']+2048
        if off<2048 or off+length>len(exe):raise ValueError('Animation outside executable')
        return exe[off:off+length]
    animations=[]
    for aid in range(144):
        address=struct.unpack('<I',read(profile['zero_animation_table_address']+aid*4,4))[0];selector=read(profile['zero_animation_bank_table_address']+aid,1)[0];bi=0 if selector==0 else 1;seen=set();seq=[];pos=0
        while pos not in seen:
            if pos<0 or len(seen)>=512:raise ValueError('Invalid sequence traversal')
            seen.add(pos);duration,event,step,n=struct.unpack('<bbbB',read(address+pos*4,4));seq.append({'position':pos,'duration_ticks':duration,'event':event,'relative_step':step,'frame':n});pos+=step
        rec={'id':aid,'graphics_bank':bi,'parts_bank':0 if bi==0 else 5,'bank_selector':selector,'table_address':address,'sequence':seq,'loop_to_position':pos,'runtime_video':False,'preview':None}
        if all(q['frame'] in selected[bi] for q in seq) and len(seq)<=80:
            images=[];durations=[]
            for q in seq:
                key=f"bank{bi}_{q['frame']:03d}";p=cell(pictures[key],frames[key]['bounds'],3);canvas=Image.new('RGB',p.size,(34,37,47));canvas.paste(p,(0,0),p);ImageDraw.Draw(canvas).text((8,8),f"오프라인 미리보기 · {aid} / {q['frame']}",font=font,fill='white');images.append(canvas);durations.append(round(max(1,q['duration_ticks'])/60*1000))
            gif=out/'animations'/f'animation_{aid:03d}.gif';images[0].save(gif,save_all=True,append_images=images[1:],duration=durations,loop=0,disposal=2);rec['preview']=gif.relative_to(out).as_posix()
        animations.append(rec)
    remaining={0:set(SHIPPUUGA_NEW)-selected[0],1:set().union(SPIN,ICE,RISE,BURST,THRUST,range(14,50),range(66,86))-selected[1]-{80}}
    report={'build':build.relative_to(ROOT).as_posix(),'bin_sha256':m['modified_bin']['sha256'],'archive_sha256':sha(arc),'original_exe_sha256':sha(exe),'authored_references':sum(map(len,selected.values())),'remaining_known_body_references':{str(b):sorted(v) for b,v in remaining.items()},'frames':frames,'palette_file':'palette.bin','animations':animations,'guides':guides,'limitations':['GIF is an offline reconstruction, not runtime video.','60 ticks/second is a preview assumption; event handlers and cancellations are not simulated.','Reference counts are not unique poses or runtime pass counts.']}
    (out/'collection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    report['embedded_static_bodies']=static_frames;report['preserved_blank_references']={'1':[80]}
    (out/'collection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    cards=''.join(f'<figure><img loading="lazy" src="{a["preview"]}"><figcaption>애니메이션 {a["id"]}</figcaption></figure>' for a in animations if a['preview'])
    doc='<!doctype html><meta charset="utf-8"><title>린 스프라이트 작업 모음</title><style>body{background:#181c26;color:#e8edf6;font:16px sans-serif;margin:24px}img{image-rendering:pixelated;max-width:100%}main{display:flex;flex-wrap:wrap}figure{margin:8px}a{color:#9cceff}code{overflow-wrap:anywhere}</style><h1>린 스프라이트 작업 모음</h1><p>현재 '+str(report['authored_references'])+'개 몸체 참조. 사용자 수용 완료본이 아닌 제작 중 결과입니다.</p><p>아래 GIF는 원작 프레임표를 사용한 오프라인 미리보기입니다. 실제 플레이 영상이나 게임 내 전수 검증이 아닙니다. 이벤트·취소를 재현하지 않습니다.</p><p><code>'+html.escape(report['build'])+'</code></p><p><a href="collection.json">팔레트·원점·파츠·원작 시간표·검증 식별자</a></p><h2>몸체 전체</h2><img src="bank0_all.png"><img src="bank1_all.png"><h2>동작 연결 미리보기</h2><main>'+cards+'</main>'
    if static_frames:doc+='<h2>낙봉파 별도 잔상</h2>'+''.join('<img style="width:320px" src="'+r['image']+'">' for r in static_frames.values())
    (out/'index.html').write_text(doc,'utf-8');print(json.dumps({'output':str(out),'body_refs':report['authored_references'],'embedded_static_refs':len(static_frames),'remaining':{b:len(v) for b,v in remaining.items()},'offline_animations':sum(bool(a['preview']) for a in animations)}))


if __name__=='__main__':main()
