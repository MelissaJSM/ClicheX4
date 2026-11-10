"""Integrate the approved dialogue relocation and native dash fix into the UI BIN."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_armor_dash_fix import PARENT,PARENT_SHA
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import sha256,DiscReader
from scripts.project import digest,working_cue,load_project,inspect_references
from src.psx_shibuki_text import rename_shibuki
from src.psx_ui_text_space import expand_dialogue,expand_dialogue_from_parts
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

APPROVAL={'date':'2026-10-27','user_quote':'이거 적용하면서 한가지 문제점좀 고쳐줄래? 아머 다먹고 혹은 개별적으로 파츠먹은 상태에서 땅에서 대시할때 일부 파츠가 사라짐. 봐서는 일반 상태의 의상이 레이어위로올라온것처럼 보임. 현상이있어','scope':'PL00/PL02 same-size internal dialogue relocation and Shibuki naming; ground dash armor registration fix','record':'docs/DECISIONS.md'}
PARENT_BIN='f51d27a7dc3aa4e4b1d30e8437c3e5b2ef63e48f0abdb0dd35f7c8ac2386a2b0'

def build(fix,save_ui):
    fix=fix.resolve()
    if not fix.is_relative_to(ROOT/'work/ver_buki_riko/shibuki_armor_dash_fix'):raise ValueError('Wrong fix directory')
    report=json.loads((fix/'recipe.json').read_text('utf8'));fixed=(fix/'modified.arc').read_bytes()
    if report['parent_arc_sha256']!=PARENT_SHA or sha256(fixed)!=report['output_sha256']:raise ValueError('Dash source mismatch')
    parent=PARENT/'shibuki_riko.bin';pm=json.loads((PARENT/'manifest.json').read_text('utf8'))
    if digest(parent)!=PARENT_BIN or pm['modified_bin']['sha256']!=PARENT_BIN:raise ValueError('UI BIN mismatch')
    project=load_project(ROOT,'ver_buki_riko');inspect_references(ROOT,project)
    if digest(ROOT/project['source_bin'])!=project['source_sha256']:raise ValueError('Original hash mismatch')
    if APPROVAL['user_quote'] not in (ROOT/APPROVAL['record']).read_text('utf8'):raise ValueError('Approval record missing')
    ui=json.loads((PARENT/'recipe.json').read_text('utf8'));items={x['file']:x for x in ui['files']}
    save_ui=save_ui.resolve()
    if not save_ui.is_relative_to(ROOT/'work/ver_buki_riko/shibuki_ui_v1'):raise ValueError('Wrong save UI directory')
    save_recipe=json.loads((save_ui/'recipe.json').read_text('utf8'));save_items={x['file']:x for x in save_recipe['files']}
    if set(save_items)!=set(items):raise ValueError('Unexpected UI resource set')
    changed_ui={n for n in items if save_items[n]['sha256']!=items[n]['sha256']}
    if changed_ui!={'LOAD_U.ARC','MOJIPAT.ARC','COL0E_U1.ARC'}:raise ValueError('Save/selection fix changes unrelated UI assets')
    replacements=[];proofs={};payloads={};arcs={}
    with parent.open('rb') as f:
        reader=DiscReader(f,parent.stat().st_size)
        for name,fn in [('PL00_U.ARC',expand_dialogue),('PL02_U.ARC',expand_dialogue_from_parts)]:
            item=items[name];rec=item['source'];old=reader.read(rec['lba'],rec['size'])
            if sha256(old)!=item['sha256']:raise ValueError('Parent archive binding mismatch')
            source=fixed if name=='PL00_U.ARC' else old
            text,changes=rename_shibuki(entry(source,0x15));new,proof=fn(source,text)
            if rename_shibuki(entry(new,0x15))[1]['name_count']:raise ValueError('Old name remains')
            if len(new)!=len(old):raise ValueError('Archive size changed')
            proofs[name]={**proof,'dialogue':changes};arcs[name]=new
            replacements.append(({**rec,'sha256':sha256(old)},new))
            for i in range((len(new)+2047)//2048):payloads[rec['lba']+i]=new[i*2048:(i+1)*2048]
        for name in sorted(changed_ui):
            item=items[name];rec=item['source'];old=reader.read(rec['lba'],rec['size']);new=(save_ui/name).read_bytes()
            if sha256(old)!=item['sha256'] or sha256(new)!=save_items[name]['sha256'] or len(new)!=len(old):raise ValueError('Save UI hash/size mismatch')
            arcs[name]=new;replacements.append(({**rec,'sha256':sha256(old)},new))
            for i in range((len(new)+2047)//2048):payloads[rec['lba']+i]=new[i*2048:(i+1)*2048]
    out=ROOT/'out/ver_buki_riko'/('shibuki_ui_dash_fix_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(exist_ok=False)
    target=out/'shibuki_riko.bin';result=write_archive_copies(parent,target,replacements,PARENT_BIN)
    expected={r['lba'] for r in result['changed_sectors']};actual=[]
    with parent.open('rb') as a,target.open('rb') as b:
        for sector in range(result['size']//2352):
            before,after=a.read(2352),b.read(2352)
            if before==after:continue
            if sector not in expected or before[:24]!=after[:24]:raise ValueError('Unexpected raw-sector change')
            validate_checks(after);chunk=payloads[sector]
            if after[24:24+len(chunk)]!=chunk or after[24+len(chunk):2072]!=before[24+len(chunk):2072]:raise ValueError('Payload mismatch')
            actual.append(sector)
    if set(actual)!=expected:raise ValueError('Sector proof incomplete')
    with target.open('rb') as f:
        reader=DiscReader(f,target.stat().st_size)
        for rec,data in replacements:
            if reader.read(rec['lba'],rec['size'])!=data:raise ValueError('Disc archive readback mismatch')
    if digest(parent)!=PARENT_BIN or digest(ROOT/project['source_bin'])!=project['source_sha256']:raise ValueError('Protected input changed')
    inspect_references(ROOT,project)
    (out/'shibuki_riko.cue').write_text(working_cue((PARENT/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
    for name,data in arcs.items():(out/name).write_bytes(data)
    (out/'modified.arc').write_bytes(arcs['PL00_U.ARC']);shutil.copyfile(fix/'review.png',out/'dash_review.png')
    recipe={'kind':'shibuki_ui_dialogue_dash_integrated','approval':APPROVAL,'parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_BIN,'dash_recipe':str((fix/'recipe.json').relative_to(ROOT)),'dash_recipe_sha256':digest(fix/'recipe.json'),'dialogue':proofs,'ui_recipe':ui['kind'],'save_ui_candidate':str(save_ui.relative_to(ROOT)),'save_ui_recipe_sha256':digest(save_ui/'recipe.json'),'save_icon_fix':{'slot_mapping':{'45':1,'46':2,'47':4,'48':8},'arm_type2_palette_row':11,'user_quote':'잠시만!! 이것도봐줄래? 로드데이터에 들어와있는데 파츠가 다깨져있어!'}}
    manifest={'project':'ver_buki_riko','task':'fourth_armor_shibuki','active_tasks':['x_shibuki_ui','fourth_armor_shibuki'],'stage':'EXPANSION','kind':'ui_dialogue_dash_fix_candidate','source_sha256':project['source_sha256'],'parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_BIN,'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'modified_archive_sha256':sha256(arcs['PL00_U.ARC']),'resource_count':2,'inherited_ui_resource_count':39,'changed_sectors':len(actual),'full_disc_sectors_compared':result['size']//2352,'dialogue_text_applied':True,'dialogue_relocation_approval_pending':False,'approved':APPROVAL,'archive_sizes_lbas_preserved':True,'exe_changed':False,'riko_preserved':True,'runtime_verified':False,'user_review_pending':True}
    manifest['resource_count']=len(replacements);manifest['save_icon_fix_applied']=True
    recipe['selection_palette_fix']={'runtime_clut':'0x7840','player_palette_row':16,'restored_background_row':64,'user_quote':'추가로 플레이어 셀렉트에서 스프라이트도 깨졌네!'}
    manifest['selection_palette_fix_applied']=True
    for name,obj in [('recipe.json',recipe),('manifest.json',manifest),('sector_changes.json',result)]: (out/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(actual),'full_disc_verified':True}))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fix',type=Path,required=True);p.add_argument('--save-ui',type=Path,required=True);a=p.parse_args();build(a.fix,a.save_ui)
