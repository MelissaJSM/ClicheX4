from pathlib import Path
import tempfile
import unittest

from PIL import Image

from src.psx_player import compose_indices
from src.psx_frame_edit import edit_frame_indices, read_indexed_png, edit_frame_set, edit_base_layer_set


def part(tile=0, x=0, flip=False):
    return {'index': 0, 'tile': tile, 'x': x, 'y': 0, 'page': 0, 'clut': 0,
            'unknown_flags': 0, 'flip_x': flip, 'flip_y': False}


class FrameEditTests(unittest.TestCase):
    def test_preserved_overlays_retain_hidden_pixels(self):
        raw=bytearray([0x21]*384);raw[8]=0x43
        overlap={'parts':[part(),part(tile=1)]};body={'parts':[part(tile=2)]}
        desired=bytes([5]*256)
        result=edit_frame_set(bytes(raw),3,[(body,desired,(16,16))],preserved_compositions=[overlap])
        self.assertEqual(compose_indices(result,3,body)[0],desired)
        self.assertEqual(compose_indices(result,3,overlap),compose_indices(raw,3,overlap))
        self.assertEqual(result[8],0x43)
        self.assertEqual(edit_frame_set(bytes(raw),3,[],preserved_compositions=[overlap]),raw)

    def test_preserved_hidden_source_alias_rejects_edits(self):
        raw=bytes([0x21]*256)
        overlap={'parts':[part(),part(tile=1)]};hidden={'parts':[part()]}
        with self.assertRaisesRegex(ValueError,'conflicting'):
            edit_frame_set(raw,2,[(hidden,bytes([3]*256),(16,16))],preserved_compositions=[overlap])

    def test_base_layers_clear_distinct_overlay_and_preserve_shared_mirror(self):
        raw=bytes([0x21])*256
        normal={'parts':[{**part(), 'flags':0},{**part(tile=1), 'flags':0}]}
        flipped={'parts':[{**part(flip=True), 'flags':0x40},{**part(tile=1,flip=True), 'flags':0x40}]}
        left=bytes([0,3]+[0]*254);right=bytes([0]*14+[3,0]+[0]*240)
        result=edit_base_layer_set(raw,2,[(normal,left,(16,16),1),(flipped,right,(16,16),1)])
        self.assertEqual(compose_indices(result,2,normal)[0],left)
        self.assertEqual(compose_indices(result,2,flipped)[0],right)
        overlay={'parts':[normal['parts'][1]]}
        self.assertEqual(compose_indices(result,2,overlay)[0],bytes(256))
        self.assertEqual(raw,bytes([0x21])*256)
        with self.assertRaisesRegex(ValueError,'conflicting'):
            edit_base_layer_set(raw,2,[(normal,left,(16,16),1),(flipped,left,(16,16),1)])

    def test_base_layer_rejects_aliases_and_pixels_outside_selected_layer(self):
        raw=bytes(256)
        alias={'parts':[{**part(),'flags':0},{**part(),'flags':0}]}
        with self.assertRaisesRegex(ValueError,'share'):
            edit_base_layer_set(raw,2,[(alias,bytes(256),(16,16),1)])
        outside={'parts':[{**part(),'flags':0},{**part(tile=1,x=16),'flags':0}]}
        image=bytearray(512);image[20]=4
        with self.assertRaisesRegex(ValueError,'represented'):
            edit_base_layer_set(raw,2,[(outside,bytes(image),(32,16),1)])
        outside['parts'][1]['flags']=0x80
        with self.assertRaisesRegex(ValueError,'flags'):
            edit_base_layer_set(raw,2,[(outside,bytes(512),(32,16),1)])

    def test_equal_source_overlap_is_explicit_and_order_independent(self):
        raw=bytes([0x21])*256
        plain={'parts':[part()]};overlap={'parts':[part(),part(tile=1)]}
        original,size,_,_=compose_indices(raw,2,overlap)
        self.assertEqual(edit_frame_indices(raw,2,overlap,original,size,overlap_policy='equal_sources'),raw)
        desired=bytes([0,15])+original[2:]
        edits=[(plain,desired,size),(overlap,desired,size)]
        result=edit_frame_set(raw,2,edits,overlap_policy='equal_sources')
        self.assertEqual(result,edit_frame_set(raw,2,list(reversed(edits)),overlap_policy='equal_sources'))
        for comp in (plain,overlap):
            self.assertEqual(compose_indices(result,2,comp)[:2],(desired,size))
        with self.assertRaisesRegex(ValueError,'conflicting'):
            edit_frame_set(raw,2,[(plain,original,size),(overlap,desired,size)],overlap_policy='equal_sources')

    def test_equal_source_policy_rejects_hidden_or_different_original_pixels(self):
        overlap={'parts':[part(),part(tile=1)]}
        for value in (0,0x43):
            raw=bytearray([0x21]*256);raw[8]=value
            pixels,size,_,_=compose_indices(raw,2,overlap)
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'sources differ'):
                edit_frame_indices(raw,2,overlap,pixels,size,overlap_policy='equal_sources')
        with self.assertRaisesRegex(ValueError,'Unknown'):
            edit_frame_indices(bytes(256),2,overlap,bytes(256),(16,16),overlap_policy='flatten')

    def test_exact_duplicate_part_is_idempotent_but_distinct_overlap_is_rejected(self):
        raw=bytes([0x21])*128
        once={'parts':[part()]};twice={'parts':[part(),part()]}
        indices,size,_,_=compose_indices(raw,1,twice)
        self.assertEqual(edit_frame_indices(raw,1,twice,indices,size),raw)
        changed=bytes([3])+indices[1:]
        self.assertEqual(edit_frame_indices(raw,1,twice,changed,size),
                         edit_frame_indices(raw,1,once,changed,size))
        for duplicate in (part(tile=1),part(flip=True),part(x=1)):
            comp={'parts':[part(),duplicate]}
            pixels,dimensions,_,_=compose_indices(bytes(256),2,comp)
            with self.assertRaisesRegex(ValueError,'Overlapping'):
                edit_frame_indices(bytes(256),2,comp,pixels,dimensions)

    def test_frame_set_shared_tile_conflict_and_consistent_flip(self):
        raw = bytes(128)
        normal = {'parts': [part()]}
        flipped = {'parts': [part(flip=True)]}
        left = bytes([1]+[0]*255)
        right = bytes([0]*15+[1]+[0]*240)
        result = edit_frame_set(raw, 1, [(normal, left, (16,16)), (flipped, right, (16,16))])
        self.assertEqual(result[0], 1)
        self.assertEqual(raw, bytes(128))
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            edit_frame_set(raw, 1, [(normal, left, (16,16)), (flipped, left, (16,16))])
        with self.assertRaises(ValueError):
            edit_frame_set(raw, 1, [])

    def test_transparency_outline_and_flip_roundtrip(self):
        frame = {'parts': [part(flip=True)]}
        raw = bytes([0x21])*128
        indices, size, _, _ = compose_indices(raw, 1, frame)
        changed = bytearray(indices)
        changed[0] = 0
        changed[1] = 15
        result = edit_frame_indices(raw, 1, frame, changed, size)
        self.assertEqual(result[7], 0x0f)
        self.assertEqual(result[:7]+result[8:], raw[:7]+raw[8:])
        self.assertEqual(edit_frame_indices(result, 1, frame, indices, size), raw)

    def test_shared_tiles_overlap_holes_and_index_refused(self):
        frame = {'parts': [part(x=0), part(x=32)]}
        raw = bytes(128)
        indices, size, _, _ = compose_indices(raw, 1, frame)
        for position, value in [(0, 1), (16, 1), (0, 16)]:
            changed = bytearray(indices); changed[position] = value
            with self.assertRaises(ValueError):
                edit_frame_indices(raw, 1, frame, changed, size)
        frame['parts'][1]['x'] = 8
        with self.assertRaises(ValueError):
            edit_frame_indices(raw, 1, frame, bytes(24*16), (24,16))

    def test_png_palette_transparency_and_mode_validation(self):
        palette = list(range(16))
        rgb = [v for word in palette for v in ((word & 31)*255//31,0,0)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'frame.png'
            picture = Image.new('P', (16,16)); picture.putpalette(rgb+[0]*720)
            picture.save(path, transparency=0)
            self.assertEqual(read_indexed_png(path, palette), (bytes(256),(16,16)))
            picture.putpixel((0,0),16); picture.save(path,transparency=0)
            with self.assertRaises(ValueError): read_indexed_png(path,palette)
            picture.convert('RGBA').save(path)
            with self.assertRaises(ValueError): read_indexed_png(path,palette)
            picture.putpixel((0,0),0); picture.save(path,transparency=1)
            with self.assertRaises(ValueError): read_indexed_png(path,palette)
            picture.save(path,transparency=0)
            with self.assertRaises(ValueError): read_indexed_png(path,list(reversed(palette)))


if __name__ == '__main__':
    unittest.main()
