"""Assets RXEA do Aurora (texturas DXT5 lineares do Xbox 360, bytes trocados 8-in-16)."""
import struct
import numpy as np

HDR = 0x800


def info(d):
    i = d.find(bytes.fromhex('0000000300000001'))
    fc = struct.unpack('>6I', d[i+28:i+52])
    return dict(off=i, pitch=((fc[0] >> 22) & 0x1ff) * 32, tiled=fc[0] >> 31, fmt=fc[1] & 0x3f,
                endian=(fc[1] >> 6) & 3, w=(fc[2] & 0x1fff) + 1, h=((fc[2] >> 13) & 0x1fff) + 1)


def _swap16(b):
    a = np.frombuffer(b, dtype=np.uint8).reshape(-1, 2)
    return a[:, ::-1].tobytes()


def _c565(v):
    r = ((v >> 11) & 31) * 255 // 31; g = ((v >> 5) & 63) * 255 // 63; b = (v & 31) * 255 // 31
    return np.stack([r, g, b], -1).astype(np.float32)


def decode(d):
    t = info(d); assert t['fmt'] == 20 and not t['tiled']
    bw = t['pitch'] // 4; w, h = t['w'], t['h']; bh = (h + 3) // 4
    raw = _swap16(d[HDR:HDR + bw * bh * 16])
    blk = np.frombuffer(raw, dtype=np.uint8).reshape(bh, bw, 16)
    c0 = blk[..., 8].astype(np.uint32) | (blk[..., 9].astype(np.uint32) << 8)
    c1 = blk[..., 10].astype(np.uint32) | (blk[..., 11].astype(np.uint32) << 8)
    idx = (blk[..., 12].astype(np.uint32) | (blk[..., 13].astype(np.uint32) << 8) |
           (blk[..., 14].astype(np.uint32) << 16) | (blk[..., 15].astype(np.uint32) << 24))
    p0, p1 = _c565(c0), _c565(c1)
    pal = np.stack([p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3], -2)          # bh,bw,4,3
    out = np.zeros((bh * 4, bw * 4, 3), np.float32)
    for k in range(16):
        sel = (idx >> (2 * k)) & 3
        px = np.take_along_axis(pal, sel[..., None, None].repeat(3, -1), -2)[..., 0, :]
        out[(k // 4)::4, (k % 4)::4] = px
    return out[:h, :w].clip(0, 255).astype(np.uint8)


def encode_bc3(rgb, pitch_px, rows_px):
    """RGB uint8 (h,w,3) -> blocos DXT5 opacos (alfa 255), com pitch/altura alinhados, bytes trocados 8-in-16."""
    h, w, _ = rgb.shape
    img = np.zeros((rows_px, pitch_px, 3), np.float32); img[:h, :w] = rgb
    img[h:, :w] = rgb[-1:, :, :]                                             # repete a última linha
    bh, bw = rows_px // 4, pitch_px // 4
    b = img.reshape(bh, 4, bw, 4, 3).transpose(0, 2, 1, 3, 4).reshape(bh, bw, 16, 3)
    lum = b @ np.array([0.299, 0.587, 0.114], np.float32)
    lo = np.take_along_axis(b, lum.argmin(-1)[..., None, None].repeat(3, -1), 2)[..., 0, :]
    hi = np.take_along_axis(b, lum.argmax(-1)[..., None, None].repeat(3, -1), 2)[..., 0, :]
    def to565(c):
        c = c.clip(0, 255)
        return ((np.round(c[..., 0] * 31 / 255).astype(np.uint32) << 11) |
                (np.round(c[..., 1] * 63 / 255).astype(np.uint32) << 5) |
                np.round(c[..., 2] * 31 / 255).astype(np.uint32))
    c0, c1 = to565(hi), to565(lo)
    swap = c0 < c1
    c0, c1 = np.where(swap, c1, c0), np.where(swap, c0, c1)
    p0, p1 = _c565(c0), _c565(c1)
    pal = np.stack([p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3], -2)           # bh,bw,4,3
    dist = ((b[..., :, None, :] - pal[..., None, :, :]) ** 2).sum(-1)       # bh,bw,16,4
    sel = dist.argmin(-1).astype(np.uint32)
    eq = (c0 == c1)
    sel[eq] = 0
    idx = np.zeros((bh, bw), np.uint32)
    for k in range(16):
        idx |= sel[..., k] << (2 * k)
    out = np.zeros((bh, bw, 16), np.uint8)
    out[..., 0] = 255; out[..., 1] = 255                                    # alfa: 255 em todos os pixels
    out[..., 8] = c0 & 255; out[..., 9] = c0 >> 8
    out[..., 10] = c1 & 255; out[..., 11] = c1 >> 8
    for k in range(4):
        out[..., 12 + k] = (idx >> (8 * k)) & 255
    return _swap16(out.tobytes())


def encode_bc3_alpha(rgb, alpha, pitch_px, rows_px):
    """Como encode_bc3, mas com o canal alfa codificado (8 níveis interpolados por bloco)."""
    h, w = alpha.shape
    color = encode_bc3(rgb, pitch_px, rows_px)
    blocks = bytearray(_swap16(color))                              # volta para a ordem normal
    a = np.zeros((rows_px, pitch_px), np.float32); a[:h, :w] = alpha
    bh, bw = rows_px // 4, pitch_px // 4
    b = a.reshape(bh, 4, bw, 4).transpose(0, 2, 1, 3).reshape(bh, bw, 16)
    a0 = b.max(-1); a1 = b.min(-1)
    a0 = np.where(a0 == a1, np.minimum(a1 + 1, 255), a0)             # a0 > a1 -> modo de 8 níveis
    a1 = np.where(a0 == a1, a1 - 1, a1)
    levels = np.stack([a0, a1] + [((7 - k) * a0 + k * a1) / 7 for k in range(1, 7)], -1)   # bh,bw,8
    sel = np.abs(b[..., None] - levels[..., None, :]).argmin(-1).astype(np.uint64)          # bh,bw,16
    bits = np.zeros((bh, bw), np.uint64)
    for k in range(16):
        bits |= sel[..., k] << np.uint64(3 * k)
    out = np.frombuffer(bytes(blocks), np.uint8).reshape(bh, bw, 16).copy()
    out[..., 0] = a0.astype(np.uint8); out[..., 1] = a1.astype(np.uint8)
    for k in range(6):
        out[..., 2 + k] = ((bits >> np.uint64(8 * k)) & np.uint64(255)).astype(np.uint8)
    return _swap16(out.tobytes())


def decode_alpha(raw_swapped, pitch_px, w, h):
    raw = _swap16(raw_swapped)
    bw = pitch_px // 4; bh = (h + 3) // 4
    blk = np.frombuffer(raw[:bw * bh * 16], np.uint8).reshape(bh, bw, 16)
    a0 = blk[..., 0].astype(np.float32); a1 = blk[..., 1].astype(np.float32)
    lv = np.stack([a0, a1] + [((7 - k) * a0 + k * a1) / 7 for k in range(1, 7)], -1)
    bits = np.zeros((bh, bw), np.uint64)
    for k in range(6):
        bits |= blk[..., 2 + k].astype(np.uint64) << np.uint64(8 * k)
    out = np.zeros((bh * 4, bw * 4), np.float32)
    for k in range(16):
        s = ((bits >> np.uint64(3 * k)) & np.uint64(7)).astype(np.int64)
        out[(k // 4)::4, (k % 4)::4] = np.take_along_axis(lv, s[..., None], -1)[..., 0]
    return out[:h, :w]
