"""심볼판 제거 후 열린 잔기칸의 왼쪽 마감을 전용 HUD 타일 안에서 복구한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,working_cue
from scripts.prepare_rin_common import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import all_compositions,composed,render_pixels
from scripts.discover_inputs import sha256,psx_arc
from src.psx_ui_atlas import tile_pixels
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

SOURCES={'ver_buki_riko':('shibuki_riko','bcdc219a1fa90ed277eecdf7b28ac196489d3297f49914470bf45e0844db2171'),
         'ver_rin_nana':('rin_nana','1a2d97272bb0dde2395aa7f1daa9136dd247125456090ff519fe3c484e3be2e2')}
TARGETS={(1,n)for n in range(69,78)}
CAP=['..DDD','.DCAA','DCAAD',*['DCADE']*6,'DCAAD','.DCAA','.DBBB','..DDD','...DD']
NAMES=('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC')
WORK=ROOT/'work/hud_frame_fix_20261105'
SOURCE_FOLDER='overhaul_20261105_candidate04'
BUILD_KIND='hud_life_holder_closed_left_cap'

def require(ok,message):
    if not ok:raise ValueError(message)

def patch(arc):
    texture,parts=entry(arc,0x10206),entry(arc,3)
    comps=all_compositions(parts);users={}
    for key,c in comps.items():
        for part in c['parts']:users.setdefault(part['page']*256+part['tile'],set()).add(key)
    demands={};wanted={};changed_tiles=set();frames=[]
    for key in sorted(TARGETS):
        before,size,box,sources=composed(texture,comps[key]);after=before.copy()
        for y,row in enumerate(CAP,25):
            for x,char in enumerate(row):
                # x<2 belonged to the emblem region. Retain every emblem pixel.
                old=int(before[y-box[1],x-box[0]])
                if x<2 and old:
                    require(char=='.','New frame overlaps the accepted emblem')
                    continue
                after[y-box[1],x-box[0]]=0 if char=='.'else int(char,16)
        for y in(24,39,40):after[y-box[1],2-box[0]]=0
        require(np.array_equal(before[:24-box[1]],after[:24-box[1]]),'Health bar body changed')
        require(np.array_equal(before[:,5-box[0]:],after[:,5-box[0]:]),'Life glyph area changed')
        emblem=before[24-box[1]:41-box[1],:2-box[0]]
        new_emblem=after[24-box[1]:41-box[1],:2-box[0]]
        require(np.array_equal(emblem[emblem>0],new_emblem[emblem>0]),'Emblem pixels changed')
        wanted[key]=after
        for y,x in zip(*np.where(after!=before)):
            locations=sources[int(y)*size[0]+int(x)]
            require(bool(locations),'Frame extension outside allocated parts')
            for index,(offset,shift)in enumerate(locations):
                tile=(offset//128//16)*16+(offset%128)//8
                require(users[tile]<=TARGETS,'Frame tile shared outside HUD')
                value=int(after[y,x])if index==len(locations)-1 else 0
                require((offset,shift)not in demands or demands[offset,shift]==value,'Shared pixel conflict')
                demands[offset,shift]=value;changed_tiles.add(tile)
        frames.append(dict(frame=key[1],changed_pixels=int(np.count_nonzero(after!=before))))
    result=bytearray(texture)
    for(offset,shift),value in demands.items():result[offset]=(result[offset]&~(15<<shift))|(value<<shift)
    result=bytes(result);count=struct.unpack_from('<I',parts)[0]//4
    static={1,2,3,4,6}if count==7 else{1,2,3,4,*range(9,count)}
    checked=0
    for key,c in comps.items():
        if key[0]not in static:continue
        old,size,bounds,_=composed(texture,c);new,ns,nb,_=composed(result,c)
        require(size==ns and bounds==nb and np.array_equal(new,wanted.get(key,old)),'Unexpected static frame difference '+str(key));checked+=1
    for tile in range(len(texture)//128):
        if tile not in changed_tiles:require(tile_pixels(texture,tile)==tile_pixels(result,tile),'Unrelated tile changed')
    patched=replace_entry(arc,0x10206,result)
    for e in psx_arc(arc):
        kind=int(e['type'],16)
        if kind!=0x10206:require(entry(arc,kind)==entry(patched,kind),'Nontexture entry changed')
    return patched,dict(frames=frames,private_tiles=sorted(changed_tiles),static_frames_checked=checked,
        emblem_pixels_unchanged=True,health_bar_body_unchanged=True,life_digit_area_unchanged=True,
        geometry_palette_timing_audio_and_all_nontexture_entries_unchanged=True)

def prepare(destination):
    destination=destination.resolve();require(destination.is_relative_to(WORK)and not destination.exists(),'Fresh task output required')
    destination.mkdir(parents=True);panels=[];manifest={}
    for project,(stem,expected)in SOURCES.items():
        source=ROOT/'out'/project/SOURCE_FOLDER/(stem+'.bin')
        require(digest(source)==expected,'Unexpected source BIN')
        assets,records=read_disc(source,[*NAMES,'COL00_0X.ARC']);pal=entry(assets['COL00_0X.ARC'],5)[544:576]
        folder=destination/project;folder.mkdir();checks={};files={}
        chars=['Shibuki','Riko','Shibuki Ultimate']if project=='ver_buki_riko'else['Nana','Rin','Nana Ultimate']
        for name,char in zip(NAMES,chars):
            new,proof=patch(assets[name]);path=folder/name;path.write_bytes(new);checks[name]=proof
            files[name]=dict(before=sha256(assets[name]),after=sha256(new),path=path.relative_to(ROOT).as_posix(),size=len(new),record=records[name])
            for label,arc in(('BEFORE',assets[name]),('AFTER',new)):
                px,size,bounds,_=composed(entry(arc,0x10206),all_compositions(entry(arc,3))[1,69]);pic=render_pixels(px,pal)
                # Actual digit0 native sprite, drawn at the original relative offset(+7,+32).
                digit,ds,db,_=composed(entry(arc,0x10206),all_compositions(entry(arc,3))[1,59]);dp=render_pixels(digit,pal)
                pic.alpha_composite(dp,(7+db[0]-bounds[0],32+db[1]-bounds[1]))
                pic.save(folder/(name+'_'+label.lower()+'.png'));panels.append((char+' '+label,pic))
        proposal=dict(project=project,baseline=source.relative_to(ROOT).as_posix(),baseline_sha256=expected,files=files,checks=checks)
        (folder/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n','utf8');manifest[project]=proposal
    cell=(270,290);board=Image.new('RGB',(4*cell[0],((len(panels)+3)//4)*cell[1]),'#536273');draw=ImageDraw.Draw(board)
    for i,(label,pic)in enumerate(panels):
        x,y=(i%4)*cell[0],(i//4)*cell[1];draw.text((x+6,y+5),label,fill='white')
        pic=pic.resize((pic.width*4,pic.height*4),Image.Resampling.NEAREST);board.paste(pic,(x+6,y+26),pic)
    board.save(destination/'comparison.png')
    (destination/'verification.json').write_text(json.dumps(manifest,indent=2)+'\n','utf8')
    print(json.dumps({'prepared':str(destination),'resources':len(manifest)*len(NAMES),'HUD_frames':len(manifest)*len(NAMES)*len(TARGETS),'preview':str(destination/'comparison.png')}))

def build(project,proposal_path,output):
    proposal_path=proposal_path.resolve();require(proposal_path.is_relative_to(WORK),'Unexpected proposal path')
    stem,expected=SOURCES[project];source=ROOT/'out'/project/SOURCE_FOLDER/(stem+'.bin')
    output=output.resolve();require(output.is_relative_to(ROOT/'out'/project)and not output.exists(),'Fresh variant output required')
    require(digest(source)==expected,'Unexpected source BIN');proposal=json.loads(proposal_path.read_text('utf8'))
    require(proposal['project']==project and proposal['baseline_sha256']==expected,'Wrong proposal')
    old,records=read_disc(source,NAMES);changes=[]
    for name in NAMES:
        f=proposal['files'][name];path=(ROOT/f['path']).resolve();require(path.is_relative_to(WORK),'Unexpected resource path')
        data=path.read_bytes();require(sha256(old[name])==f['before']and sha256(data)==f['after'],'Resource hash differs')
        require(data==patch(old[name])[0],'Resource not reproduced by exact frame correction')
        changes.append(({**records[name],'sha256':sha256(old[name])},data))
    output.mkdir(parents=True);target=output/(stem+'.bin');result=write_archive_copies(source,target,changes,expected)
    changed={r['lba']for r in result['changed_sectors']};count=0
    with source.open('rb')as a,target.open('rb')as b:
        while before:=a.read(2352):
            after=b.read(2352);require((before!=after)==(count in changed),'Undeclared sector difference')
            if count in changed:validate_checks(after)
            count+=1
        require(not b.read(1),'Output size changed')
    readback,_=read_disc(target,NAMES)
    require(all(readback[n]==data for(n,data)in[(r['name'].split(';')[0],d)for r,d in changes]),'Disc readback differs')
    require(digest(source)==expected,'Source changed')
    result['sha256']=digest(target);cue=source.with_suffix('.cue')
    (output/(stem+'.cue')).write_text(working_cue(cue.read_text('ascii'),stem+'.bin'),'ascii')
    report=dict(project=project,task='hud_frame_fix',kind=BUILD_KIND,stage='EXPANSION',
        parent=source.parent.relative_to(ROOT).as_posix(),parent_sha256=expected,modified_bin=result,
        source_sha256='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',
        all_disc_sectors_compared=count,all_changes_declared=True,resource_readback_verified=True,
        edc_ecc_verified=True,proposal=proposal_path.relative_to(ROOT).as_posix(),runtime_verified=False,user_accepted=False)
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
    print(json.dumps({'project':project,'sha256':result['sha256'],'changed_sectors':len(changed),'sectors_checked':count,'output':str(output)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','build']);p.add_argument('--output',type=Path,required=True);p.add_argument('--project',choices=SOURCES);p.add_argument('--proposal',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.output)
    else:build(a.project,a.proposal,a.output)
