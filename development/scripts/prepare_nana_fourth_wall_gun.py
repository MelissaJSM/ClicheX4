"""생성한 사랑이의 총열·손잡이를 벽 사격의 기존 총구에 등록한다."""
from pathlib import Path
import copy
import numpy as np
from PIL import Image
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_nana_fourth_pilot import require
from scripts.project import digest
from src.psx_player import indexed_atlas
from src.psx_sprite_batch import canvas_from_parts

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'work/ver_rin_nana/nana_fourth_armor/wall_gun_v1/generated.png'
CROP=(89,178,193,244)


def refit(target,eye_x,rgb,minimum_shift=3):
    require(digest(SOURCE)=='5ea6687e0686f3ce0dadee333ec86a1814ef75ebcadafb1c0bbdd3a19891ff32','Gun source changed')
    source=Image.open(SOURCE).convert('RGBA')
    gun=normalize(source.crop(CROP),7,rgb,width=12)
    yy,xx=np.indices(target.shape)
    xmin=int(np.nonzero((target>0)&(xx<eye_x-8))[1].min())
    rows=np.flatnonzero(target[:,xmin]);top=int(rows.min())
    before=target.copy();patch=target[top:top+7,xmin:xmin+12]
    # The armor overlay cannot erase a base pixel. Cover the former finger
    # pixels with the dark lower frame of the longer pistol, not skin.
    target[top:top+7,xmin:xmin+12]=np.where(gun,gun,np.where(patch,1,0))
    target[:,xmin]=before[:,xmin]
    require(np.array_equal(target[:,xmin],before[:,xmin]),'Muzzle column moved')
    old_hand=np.argwhere(np.isin(before,(11,12,13))&(xx<eye_x-8))
    new_hand=np.argwhere(np.isin(target,(11,12,13))&(xx<xmin+12))
    shift=float(np.median(new_hand[:,1])-np.median(old_hand[:,1]))
    require(shift>=minimum_shift,'Hand did not move toward shoulder')
    changed=np.argwhere(target!=before)
    return target,{'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':digest(SOURCE),
        'crop':list(CROP),'registered_box':[xmin,top,xmin+12,top+7],
        'muzzle_column_preserved':True,'grip_shift_toward_shoulder_pixels':shift,
        'changed_pixels':[[int(x),int(y)] for y,x in changed]}


def patch_base(raw,count,regular,shoot,target,box):
    """기존 사격 전용 타일의 해당 사각형만 편집하고 모든 표시를 대조."""
    before=canvas_from_parts(raw,count,shoot);yy,xx=np.indices(before.shape)
    x,y,x2,y2=box;allowed=(xx>=x)&(xx<x2)&(yy>=y)&(yy<y2)
    require(not np.any((target!=before)&~allowed),'Base correction escapes pistol')
    reserved={p['tile'] for p in regular['parts']}
    _,locations,_=indexed_atlas(raw,count);result=bytearray(raw);changed_tiles=set()
    for py,px in np.argwhere(target!=before):
        parts=[p for p in shoot['parts'] if p['x']+80<=px<p['x']+96 and p['y']+80<=py<p['y']+96]
        require(parts and target[py,px]>0,'Uncovered or erased base pixel')
        writable=[p for p in parts if p['tile'] not in reserved]
        require(writable,'Regular pose shares corrected tile');p=writable[-1]
        tx=int(px-80-p['x']);ty=int(py-80-p['y'])
        if p['flip_x']:tx=15-tx
        if p['flip_y']:ty=15-ty
        off,shift=locations[(p['tile']//16*16+ty)*256+p['tile']%16*16+tx]
        result[off]=(result[off]&~(15<<shift))|(int(target[py,px])<<shift);changed_tiles.add(p['tile'])
    result=bytes(result)
    require(np.array_equal(canvas_from_parts(result,count,shoot),target),'Base correction readback differs')
    require(np.array_equal(canvas_from_parts(result,count,regular),canvas_from_parts(raw,count,regular)),'Regular wall pose changed')
    return result,changed_tiles


def fit_pistol_coverage(raw,count,regular,shoot,target):
    """빈 위쪽 행만 쓰던 사격 전용 슬롯을 아래로 최대3px 옮긴다.

    텍셀을 반대로 이동하여 기존 표시 위치는 그대로 유지한다.
    """
    yy,xx=np.indices(target.shape);covered=np.zeros(target.shape,bool)
    for p in shoot['parts']:covered|=(xx>=p['x']+80)&(xx<p['x']+96)&(yy>=p['y']+80)&(yy<p['y']+96)
    missing=np.argwhere((target>0)&~covered)
    if not len(missing):return raw,shoot,[]
    reserved={p['tile'] for p in regular['parts']}
    candidates=[p for p in shoot['parts'] if p['tile'] not in reserved and np.all((missing[:,1]>=p['x']+80)&(missing[:,1]<p['x']+96))]
    require(len(candidates)==1,'Ambiguous pistol slot coverage')
    p=candidates[0];delta=int(missing[:,0].max()-(p['y']+95));require(1<=delta<=3,'Pistol slot shift too large')
    atlas,loc,_=indexed_atlas(raw,count);t=p['tile'];pix=np.frombuffer(atlas,np.uint8).reshape(-1,256)[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    require(not(p['flip_x'] or p['flip_y']) and not np.any(pix[:delta]),'Pistol slot has protected pixels above')
    moved=np.zeros_like(pix);moved[:-delta]=pix[delta:];result=bytearray(raw)
    for y in range(16):
        for x in range(16):
            off,shift=loc[(t//16*16+y)*256+t%16*16+x];result[off]=(result[off]&~(15<<shift))|(int(moved[y,x])<<shift)
    comp=copy.deepcopy(shoot);q=next(q for q in comp['parts'] if q['record_offset']==p['record_offset']);q['y']+=delta
    require(np.array_equal(canvas_from_parts(bytes(result),count,comp),canvas_from_parts(raw,count,shoot)),'Slot shift moved original art')
    return bytes(result),comp,[{'record_offset':q['record_offset'],'tile':t,'x':q['x'],'y':q['y'],'flags':q['flags'],'shift_y':delta}]
