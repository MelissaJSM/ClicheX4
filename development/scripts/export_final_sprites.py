"""수용된 최종 ARC에서 원점·팔레트·레이어를 보존한 참고용 스프라이트 묶음을 만든다."""
import argparse,hashlib,html,json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from scripts.compact_builds import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_ui_atlas import local_composition
from src.psx_static_effect import compose_static
from src.sprite_sheet import pack_frames,unpack_frames
FINAL_SHA='8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a'

def save(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def entries(path):
    raw=path.read_bytes();es=psx_arc(raw)
    return {k:raw[e['offset']:e['offset']+e['size']] for k in [2,3,9,0x10206] for e in es if int(e['type'],16)==k}

def export(release):
    if digest(release/'game/shibuki_riko.bin')!=FINAL_SHA:raise ValueError('Unsupported final BIN')
    out=release/'sprites';out.mkdir(exist_ok=False)
    resources=release/'resources';groups=[];failures=[]
    # Earlier master supplies only a body-reference classification; pixels are always re-read from the final ARC.
    classification_path=ROOT/'work/ver_buki_riko/production_master/20261025T233021338172Z/master.local.json'
    body_keys=set(json.loads(classification_path.read_text('utf-8'))['source_frames'])
    datasets={n:entries(resources/f'PL{pl:02}_U.ARC') for n,pl in [('riko',1),('shibuki',0),('ultimate',2)]}
    banks={}
    def frame(who,gb,pb,n,normalize=False):
        es=datasets[who];bank=banks.setdefault((who,gb),graphics_bank(es[2],gb,allow_bank_aliases=True));f=bank['frames'][n]
        raw=decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data;comp=composition_frame(es[3],pb,n)
        use=local_composition(comp) if normalize else comp
        if comp['parts']:pixels,size,bounds,_=compose_indices(raw,f['tile_count'],use,allowed_cluts={0,1,2,3})
        else:pixels,size,bounds=bytes(1),(1,1),(0,0,1,1)
        return (pixels,size,bounds),{'graphics_bank':gb,'composition_bank':pb,'frame':n,'stream_offset':f['offset'],'tile_count':f['tile_count'],'composition':comp,'stream_sha256':sha(raw),'empty_composition':not comp['parts']}
    def make_group(name,frames,records,words,note):
        if not frames:raise ValueError('Empty export group')
        folder=out/name;folder.mkdir();native=folder/'frames';native.mkdir()
        lo_x=min(f[2][0] for f in frames.values());lo_y=min(f[2][1] for f in frames.values());hi_x=max(f[2][2] for f in frames.values());hi_y=max(f[2][3] for f in frames.values())
        cell=(hi_x-lo_x+8,hi_y-lo_y+8);origin=(-lo_x+4,-lo_y+4)
        pixels,layout=pack_frames(frames,columns=8,cell=cell,origin=origin,max_index=63 if len(words)>16 else 15)
        save_image(pixels,layout['size'],words,folder/'sheet_indexed.png')
        reread=Image.open(folder/'sheet_indexed.png');unpacked=unpack_frames(reread.tobytes(),reread.size,layout)
        if any(unpacked[k]!=f[:2] for k,f in frames.items()):raise ValueError('Sheet roundtrip mismatch')
        for key,(data,size,bounds) in frames.items():
            save_image(data,size,words,native/f'{key}.png')
            records[key].update(bounds=list(bounds),size=list(size),indices_sha256=sha(data),png_sha256=digest(native/f'{key}.png'))
        save(folder/'layout.json',layout);save(folder/'frames.json',records)
        save(folder/'palette.json',{'words_rgb555_stp':list(words),'transparent_index':0,'note':'RGB 미리보기는 원작 반투명 합성·동적 팔레트 효과를 재현하지 않음'})
        # Paginated 1x reference sheets; browser provides nearest-neighbor zoom.
        thumbs=[];keys=list(frames)
        for start in range(0,len(keys),64):
            pagekeys=keys[start:start+64];board=Image.new('RGBA',(8*cell[0],((len(pagekeys)+7)//8)*(cell[1]+16)),(30,36,49,255));draw=ImageDraw.Draw(board)
            for i,key in enumerate(pagekeys):
                im=Image.open(native/f'{key}.png').convert('RGBA');b=frames[key][2];x=i%8*cell[0];y=i//8*(cell[1]+16)
                board.alpha_composite(im,(x+origin[0]+b[0],y+16+origin[1]+b[1]));draw.text((x+2,y+2),key,fill='white')
            filename=f'preview_{start//64:02}.png';board.convert('RGB').save(folder/filename);thumbs.append(filename)
        groups.append({'name':name,'count':len(frames),'kind':'indexed_native_frames','note':note,'previews':thumbs,'sheet_roundtrip_verified':True})
        return folder
    rframes={};rrecords={};extras={};extra_records={}
    for gb,pb in [(0,0),(1,5)]:
        bank=graphics_bank(datasets['riko'][2],gb)
        for n in range(len(bank['frames'])):
            key=f'bank{gb}_{n:03}'
            try:f,r=frame('riko',gb,pb,n)
            except ValueError as e:failures.append({'character':'riko','key':key,'reason':str(e)});continue
            target,meta=(rframes,rrecords) if key in body_keys else (extras,extra_records);target[key]=f;meta[key]=r
    if set(rframes)!=body_keys:raise ValueError('Final export lost an accepted body reference')
    pal=struct.unpack_from('<64H',datasets['riko'][9]);make_group('riko',rframes,rrecords,pal,'과거 승인 마스터의 몸체 참조 266개를 최종 ARC에서 다시 추출. 애니메이션 순서가 아닌 참조 번호순.')
    make_group('riko_effect_references',extras,extra_records,pal,'나머지 해독 가능한 참조. 원작 유지 효과·워프 포함. 효과별 런타임 CLUT는 이 미리보기와 다를 수 있음.')
    static={};meta={}
    for n in (23,24):
        comp=composition_frame(datasets['riko'][3],6,n);f=compose_static(datasets['riko'][0x10206],local_composition(comp))[:3];key=f'static6_{n:03}';static[key]=f;meta[key]={'composition':comp,'source_type':'0x10206','composition_bank':6,'frame':n}
    make_group('riko_static_body',static,meta,pal[:16],'압축 몸체 뱅크 밖의 정적 몸체 참조. 최종 정적 텍스처에서 추출.')
    valid=sorted(set(range(237))-{105,*range(175,183)})
    for who,prefix in [('shibuki','shibuki'),('ultimate','shibuki_ultimate')]:
        words=struct.unpack_from('<64H',datasets[who][9]);all_layers={}
        for pb,label in [(0,'base'),(5,'head'),(6,'body'),(7,'arm'),(8,'leg')]:
            fs={};rs={}
            for n in valid:
                key=f'frame_{n:03}';f,r=frame(who,0,pb,n,normalize=True);fs[key]=f;rs[key]=r
            all_layers[pb]=fs
            group=(prefix+'_base') if pb==0 else prefix+'_layer_'+label
            note='PL00 기본 몸체' if who=='shibuki' and pb==0 else ('PL02 캡슐 전 기본 몸체; 획득 후에는 아머 레이어와 합성' if pb==0 else ('포스아머 개별 레이어' if who=='shibuki' else '얼티밋 파츠뱅크; head 뱅크가 전체 의상이며 다른 뱅크는 대부분 투명'))
            folder=make_group(group,fs,rs,words[:16] if pb==0 else words[16:32],note)
            if pb==7:save(folder/'alternate_arm_palette.json',{'words_rgb555_stp':list(words[32:48]),'note':'arm_type=2일 때 이 팔레트로 재색인 표시. 픽셀은 동일.'})
        # 16 partial armor masks, both arm palettes. Full previews are convenience RGBA, layers remain editable indexed PNGs.
        combined=out/(prefix+'_full');combined.mkdir();fulls={};checks=[]
        union=[f[2] for layer in all_layers.values() for f in layer.values()]
        minx=min(b[0] for b in union);miny=min(b[1] for b in union);maxx=max(b[2] for b in union);maxy=max(b[3] for b in union)
        full_size=(maxx-minx+8,maxy-miny+8);full_origin=(-minx+4,-miny+4)
        def rgba(f,palette):
            data,size,bounds=f;im=Image.frombytes('P',size,data);rgb=[]
            for w in palette:rgb.extend([(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31])
            im.putpalette(rgb+[0]*(768-len(rgb)));im.info['transparency']=0;return im.convert('RGBA')
        for armtype in (1,2):
            for mask in range(16):
                for n in valid:
                    key=f'frame_{n:03}';selected=[(0,words[:16])]+[(pb,words[32:48] if pb==7 and armtype==2 else words[16:32]) for bit,pb in [(8,8),(1,5),(4,7),(2,6)] if mask&bit]
                    canvas=Image.new('RGBA',full_size);bounds=[]
                    for pb,wp in selected:
                        f=all_layers[pb][key];im=rgba(f,wp);x,y,x1,y1=f[2]
                        ox,oy=full_origin
                        if min(ox+x,oy+y)<0 or ox+x1>full_size[0] or oy+y1>full_size[1]:raise ValueError('Layer outside reference canvas')
                        canvas.alpha_composite(im,(ox+x,oy+y));bounds.append(f[2])
                    if mask==15:
                        folder=combined/f'arm_type_{armtype}';folder.mkdir(exist_ok=True);canvas.save(folder/f'{key}.png')
                        if armtype==2:fulls[key]=canvas
                    checks.append([n,mask,armtype])
        # Full sheet: fixed world origins, no per-frame scale normalization.
        cell=(full_size[0],full_size[1]+16);pagefiles=[];keys=list(fulls)
        for start in range(0,len(keys),48):
            pagekeys=keys[start:start+48];board=Image.new('RGBA',(8*cell[0],6*cell[1]),(30,36,49,255));draw=ImageDraw.Draw(board)
            for i,key in enumerate(pagekeys):
                x=i%8*cell[0];y=i//8*cell[1];board.alpha_composite(fulls[key],(x,y+16));draw.text((x+2,y+2),key,fill='white')
            filename=f'preview_{start//48:02}.png';board.convert('RGB').save(combined/filename);pagefiles.append(filename)
        save(combined/'composition.json',{'world_origin':full_origin,'canvas':full_size,'layer_order':[0,8,5,7,6],'bits':{'head':1,'body':2,'arm':4,'leg':8},'geometry_checks':len(checks),'checks':checks,'static_export_only':True,'not_an_additional_runtime_test':True})
        groups.append({'name':combined.name,'count':len(valid),'kind':'rgba_composites','note':'전체 장착 정적 합성, 팔 타입 1/2. 부분 장착 16조합도 범위 검사함. 실제 게임 캡처 아님.','previews':pagefiles})
    manifest={'final_bin_sha256':FINAL_SHA,'source':'../resources/PL00_U.ARC, PL01_U.ARC, PL02_U.ARC','groups':groups,'unsupported_references':failures,'known_x_placeholder_references':[105,*range(175,183)],'riko_body_classification_source':classification_path.relative_to(ROOT).as_posix(),'riko_body_classification_sha256':digest(classification_path),'animation_timing':'원본 ARC type 4/기존 분석문서 보존. 시트 순서를 재생 순서로 사용하지 않음.','runtime_palette_note':'색상은 저장된 팔레트의 정적 표시. 반투명·점멸·특수 무기 색 순환은 게임에서 검증할 것.'}
    save(out/'manifest.json',manifest)
    sections=[]
    for g in groups:
        imgs=''.join(f'<img loading="lazy" src="{g["name"]}/{p}" alt="{g["name"]} {p}">' for p in g['previews'])
        sections.append(f'<details {"open" if g["name"] in ["riko","shibuki_base","shibuki_full","shibuki_ultimate_full"] else ""}><summary>{g["name"]} · {g["count"]} references</summary><p>{html.escape(g["note"])}</p><a href="{g["name"]}/">파일 폴더</a>{imgs}</details>')
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>ClichéX4 최종 스프라이트</title><style>body{background:#151a25;color:#eee;font:16px sans-serif;margin:24px}a{color:#9ed}img{display:block;image-rendering:pixelated;max-width:none;margin:12px 0}details{margin:24px 0}summary{cursor:pointer;font-size:22px}button{padding:8px}</style><h1>ClichéX4 · 시부키 / 리코 · v1.0.0</h1><p>최종 BIN에서 추출한 정적 자료. 게임 내 재생 화면이 아닙니다. PNG는 원래 크기, 시트는 공통 좌표 원점입니다. 효과·반투명 색상은 게임에서 달라질 수 있습니다.</p><button onclick="document.querySelectorAll(\'img\').forEach(i=>i.style.zoom=i.style.zoom==2?1:2)">1× / 2× 확대</button>'+''.join(sections),'utf-8')
    print(json.dumps({'groups':len(groups),'riko_body':len(rframes),'riko_extra':len(extras),'unrendered':len(failures),'release':str(out)},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',type=Path,default=ROOT/'out/ver_buki_riko/final_v1_0_0');a=p.parse_args();export(a.release.resolve())
