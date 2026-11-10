import math
import unittest

from src.psx_spu_audio import decode_spu, encode_fixed_oneshot, silence_fixed_oneshot, validate_oneshot_template


class SpuAudioTests(unittest.TestCase):
    def test_silence_preserves_duration_flags_and_unplayed_terminal(self):
        template = bytearray(16) + bytearray([0x20, 0] + [0x37] * 14) * 8
        template[17], template[-31], template[-15] = 4, 1, 7
        before = bytes(template)
        self.assertTrue(any(decode_spu(before).pcm))
        muted = silence_fixed_oneshot(before)
        self.assertEqual(template, before)
        self.assertEqual(len(muted), len(before))
        self.assertEqual(muted[1::16], before[1::16])
        self.assertEqual(muted[:16], before[:16])
        self.assertEqual(muted[-16:], before[-16:])
        decoded = decode_spu(muted)
        self.assertEqual(decoded.played_blocks, decode_spu(before).played_blocks)
        self.assertEqual(decoded.end_flag, 1)
        self.assertEqual(decoded.pcm, (0,) * len(decode_spu(before).pcm))
        self.assertEqual(silence_fixed_oneshot(muted), muted)

    def test_silence_refuses_unconfirmed_flags_and_leading_block(self):
        template = bytearray(64)
        template[17], template[33], template[49] = 4, 1, 7
        for offset, value in ((0, 1), (17, 3), (33, 3), (49, 0)):
            bad = bytearray(template)
            bad[offset] = value
            with self.assertRaises(ValueError):
                silence_fixed_oneshot(bytes(bad))

    def test_known_signed_nibbles_and_order(self):
        raw = bytes([12, 1]) + bytes([0xF1, 0x78]) + bytes(12)
        self.assertEqual(decode_spu(raw).pcm[:4], (1, -1, -8, 7))

    def test_end_mutes_before_terminal_block(self):
        raw = bytes([12, 1]) + bytes(14) + bytes([0, 7]) + bytes([0x77] * 14)
        decoded = decode_spu(raw)
        self.assertEqual(decoded.played_blocks, 1)
        self.assertEqual(decoded.pcm, (0,) * 28)

    def test_rejects_unconfirmed_headers(self):
        for raw in (b"", bytes(15), bytes([0x50, 1]) + bytes(14), bytes([13, 1]) + bytes(14)):
            with self.assertRaises(ValueError):
                decode_spu(raw)

    def test_fixed_sample_preserves_flags_and_signal(self):
        blocks = 22
        template = bytearray(blocks * 16)
        template[17], template[-31], template[-15] = 4, 1, 7
        pcm = [0] * 28 + [round(11000 * math.sin(i * 0.13)) for i in range((blocks - 2) * 28)]
        encoded, result = encode_fixed_oneshot(pcm, bytes(template))
        self.assertEqual(encoded[1::16], template[1::16])
        self.assertEqual(encoded[-16:], template[-16:])
        self.assertEqual(len(decode_spu(encoded).pcm), len(pcm))
        self.assertGreater(result["snr_db"], 30)
        with self.assertRaises(ValueError):
            encode_fixed_oneshot(pcm[:-1], bytes(template))
        template[17] = 3
        with self.assertRaises(ValueError):
            validate_oneshot_template(bytes(template))


if __name__ == "__main__":
    unittest.main()
