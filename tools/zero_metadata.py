from pathlib import Path
from collections import defaultdict
import json,struct,hashlib
ROOT=Path(__file__).resolve().parents[1]/"development"
LABELS={}

GROUND_BODY = {61,62,63,65,67,69,71,73,75,77,79,81,82,83,85,87,89,91,93,95,97,99,101,
               105,107,109,111,113,115,117,119,121,123,125,127,130,131,132,133,134}

AIR_BODY = {*range(213,230,2), *range(230,247,2)}

LADDER_EFFECT = {198,200,203,205,207,209,211}

SPECIAL_BODY = {86,87,88,91,93,95,96,98,99,101,103,105,107,108,110,112,114,116,119,122,125,128,129,130,131,
                *range(132,144), *range(144,161,2), 161,163,165,167,169,171,173,175, *range(177,190)}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def need(ok, why):
    if not ok:
        raise ValueError(why)

def classify(bank, number):
    if bank == 0:
        if number in {0,1,2,146,147,148}:
            return 'idle', 'body'
        for low, high, label in ((3,20,'run'),(21,34,'jump'),(35,43,'wall'),(44,52,'dash'),
                                 (53,60,'arrival_light'),(61,134,'ground_saber'),(135,145,'hurt'),
                                 (149,154,'low_hp'),(155,173,'shippuuga'),(174,212,'ladder'),
                                 (213,246,'air_saber'),(247,253,'arrival_body')):
            if low <= number <= high:
                effect = (label == 'arrival_light' or label == 'ground_saber' and number not in GROUND_BODY or
                          label == 'shippuuga' and number >= 157 and number % 2 == 1 or
                          label == 'ladder' and number in LADDER_EFFECT or
                          label == 'air_saber' and number not in AIR_BODY)
                return label, 'effect' if effect else 'body_with_effect' if number in {140,141,143,145,247,248} else 'body'
    else:
        if number < 9:
            return 'victory_return_body', 'body_with_effect' if number >= 7 else 'body'
        if number < 14:
            return 'return_light', 'effect'
        if number < 42:
            return 'ride_chaser', 'body'
        if number < 50:
            return 'ride_partial_unknown', 'partial_vram_update'
        if number < 66:
            return 'wall_saber', 'body' if number in {50,51,53,54,56,57,59,61,63,65} else 'effect'
        if number < 86:
            return 'ride_armor_head', 'blank' if number == 80 else 'head_only'
        for low, high, label in ((86,131,'raijingeki_shared'),(132,143,'hyouretsuzan'),
                                 (144,159,'ryuenjin'),(160,176,'air_spin'),(177,189,'rakuhouha')):
            if low <= number <= high:
                return label, 'body_with_effect' if number in {88,*range(177,182)} else 'body' if number in SPECIAL_BODY else 'effect'
    return 'unclassified', 'unknown'

def animations(exe):
    cfg = json.loads((ROOT / 'config/ps1_us_slus00561.json').read_text('utf8'))
    def get(address, length):
        start = address - 0x80010000 + 2048
        need(start >= 2048 and start + length <= len(exe), 'Sequence outside EXE')
        return exe[start:start + length]
    result, refs = [], defaultdict(list)
    for aid in range(144):
        pointer = struct.unpack('<I', get(cfg['zero_animation_table_address'] + 4 * aid, 4))[0]
        selector = get(cfg['zero_animation_bank_table_address'] + aid, 1)[0]
        need(selector in (0,1), 'Unexpected player bank selector')
        seen, seq, pos = set(), [], 0
        while pos not in seen:
            need(0 <= pos and len(seen) < 512, 'Invalid sequence traversal')
            seen.add(pos)
            duration, event, step, number = struct.unpack('<bbbB', get(pointer + pos * 4, 4))
            item = {'position':pos, 'duration_ticks':duration, 'event':event,
                    'relative_step':step, 'frame':number}
            seq.append(item)
            refs[selector,number].append({'id':aid, **item})
            pos += step
        result.append({'id':aid,'label':LABELS.get(aid),'graphics_bank':selector,
                       'parts_bank':0 if selector == 0 else 5,'table_address':hex(pointer),
                       'sequence':seq,'loop_to_position':pos,'timing_known':True,
                       'timing_unit':'animation_update_tick','wall_time_rate_known':False,
                       'event_behavior_verified':False,'label_evidence':
                       'scripts/inventory_zero_animations.py; scripts/prepare_zero_specials.py; '
                       'docs/RIKO_SPECIAL_TECHNIQUES.md; docs/RIKO_VICTORY_BEAM_OUT.md; docs/RIN_RIDE_PRODUCTION.md'})
    return result, refs, {key: {'address':hex(cfg[key]),'sha256':sha(get(cfg[key],size))}
                          for key,size in [('zero_animation_table_address',576),('zero_animation_bank_table_address',144)]}
