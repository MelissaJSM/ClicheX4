"""SPU ADPCM의 블록 디코딩과 기존 one-shot 공간에 맞춘 인코딩.

XA에는 사용하지 않는다. VAB 명령, tone, 파형 경계와 재생 종료 플래그는
호출자가 보존한다. 디코더는 SPU 보간/ADSR/리버브 이전의 PCM을 반환한다.
"""
from dataclasses import dataclass
import math
import struct

FILTERS = ((0, 0), (60, 0), (115, -52), (98, -55), (122, -60))


@dataclass(frozen=True)
class DecodedSample:
    pcm: tuple[int, ...]
    played_blocks: int
    end_flag: int | None


def clamp16(value):
    return min(32767, max(-32768, int(value)))


def decode_spu(data: bytes, *, stop_at_end=True) -> DecodedSample:
    if not data or len(data) % 16:
        raise ValueError("SPU data must contain complete 16-byte blocks")
    previous, older, pcm, end_flag = 0, 0, [], None
    for index in range(0, len(data), 16):
        block = data[index:index + 16]
        shift, predictor = block[0] & 15, block[0] >> 4
        if predictor >= len(FILTERS) or shift > 12 or block[1] & ~7:
            raise ValueError("Unsupported SPU block header")
        a, b = FILTERS[predictor]
        for packed in block[2:]:
            for nibble in (packed & 15, packed >> 4):
                signed = nibble if nibble < 8 else nibble - 16
                sample = clamp16(((signed << 12) >> shift) + ((a * previous + b * older + 32) >> 6))
                pcm.append(sample)
                older, previous = previous, sample
        if block[1] & 1:
            end_flag = block[1]
            if stop_at_end:
                return DecodedSample(tuple(pcm), index // 16 + 1, end_flag)
    return DecodedSample(tuple(pcm), len(data) // 16, end_flag)


def validate_oneshot_template(template: bytes) -> int:
    if len(template) < 48 or len(template) % 16 or template[:16] != bytes(16):
        raise ValueError("Expected leading silent block and complete sample slots")
    blocks = len(template) // 16
    expected = [0] * blocks
    expected[1], expected[-2], expected[-1] = 4, 1, 7
    if list(template[1::16]) != expected:
        raise ValueError("Unconfirmed one-shot loop/end flag layout")
    decoded = decode_spu(template)
    if decoded.played_blocks != blocks - 1 or decoded.end_flag != 1:
        raise ValueError("Unexpected one-shot length")
    return len(decoded.pcm)


def silence_fixed_oneshot(template: bytes) -> bytes:
    """검증된 슬롯의 재생 길이·종료 플래그를 유지하고 가청 블록만 무음화한다."""
    capacity = validate_oneshot_template(template)
    output = bytearray(template)
    for offset in range(16, len(template) - 16, 16):
        # Predictor 0 discards history; zero residuals decode to exact silence.
        output[offset] = 0
        output[offset + 2:offset + 16] = bytes(14)
    result = bytes(output)
    restored = decode_spu(result)
    if len(restored.pcm) != capacity or any(restored.pcm):
        raise AssertionError("Muted sample is not exact, same-duration silence")
    return result


def encode_fixed_oneshot(pcm, template: bytes) -> tuple[bytes, dict]:
    capacity = validate_oneshot_template(template)
    if len(pcm) != capacity:
        raise ValueError("PCM length must exactly match the original playable capacity")
    values = [int(round(float(x))) for x in pcm]
    if any(not -32768 <= x <= 32767 for x in values) or any(values[:28]):
        raise ValueError("PCM must be int16-range and preserve the first silent block")
    output = bytearray(template)
    previous, older = 0, 0
    # Search every legal predictor and shift against the reconstructed history.
    for start in range(28, capacity, 28):
        target = values[start:start + 28]
        best = None
        for predictor, (a, b) in enumerate(FILTERS):
            for shift in range(13):
                step = 1 << (12 - shift)
                p, q, error, nibbles = previous, older, 0, []
                for wanted in target:
                    estimate = (a * p + b * q + 32) >> 6
                    quantized = min(7, max(-8, math.floor((wanted - estimate) / step + 0.5)))
                    reconstructed = clamp16(estimate + quantized * step)
                    error += (wanted - reconstructed) ** 2
                    nibbles.append(quantized & 15)
                    q, p = p, reconstructed
                if best is None or error < best[0]:
                    best = (error, predictor, shift, nibbles, p, q)
        _, predictor, shift, nibbles, previous, older = best
        offset = start // 28 * 16
        output[offset] = (predictor << 4) | shift
        for j in range(14):
            output[offset + 2 + j] = nibbles[2 * j] | (nibbles[2 * j + 1] << 4)
    result = bytes(output)
    if result[:16] != template[:16] or result[-16:] != template[-16:] or result[1::16] != template[1::16]:
        raise AssertionError("Reserved blocks or playback flags changed")
    restored = decode_spu(result).pcm
    signal = sum(x * x for x in values[28:])
    error = sum((a - b) ** 2 for a, b in zip(values[28:], restored[28:]))
    return result, {"pcm_samples": capacity, "bytes": len(result),
                    "snr_db": 10 * math.log10(signal / error) if signal and error else None,
                    "peak_error": max(abs(a - b) for a, b in zip(values, restored)),
                    "flags_preserved": True, "reserved_blocks_preserved": True}


def vag_container(adpcm: bytes, sample_rate: int, name="sample") -> bytes:
    if not 1000 <= sample_rate <= 192000 or len(adpcm) % 16:
        raise ValueError("Invalid VAG sample metadata")
    header = bytearray(48)
    header[:4] = b"VAGp"
    struct.pack_into(">I", header, 4, 0x20)
    struct.pack_into(">II", header, 12, len(adpcm), sample_rate)
    header[32:48] = name.encode("ascii")[:16].ljust(16, b"\0")
    return bytes(header) + adpcm
