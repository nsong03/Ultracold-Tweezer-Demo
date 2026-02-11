from pathlib import Path
import random
import struct


# Simulation configuration
TARGET_GRID_SIZE = 8
VISIBLE_GRID_SIZE = 14
MISSING_FRACTION = 0.35
RANDOM_SEED = 7
CELL_SIZE_PX = 44
ATOM_RADIUS_PX = 10
MARGIN_PX = 24
MOVE_FRAMES = 30
BLINK_CYCLES = 4
BLINK_FRAME_HOLD = 2
INITIAL_HOLD_FRAMES = 6
FINAL_HOLD_FRAMES = 8
FRAME_DURATION_CS = 8  # centiseconds

# Palette colors (RGB)
WHITE = (255, 255, 255)
BLUE = (49, 112, 214)
ORANGE = (240, 141, 52)
PALETTE = [WHITE, BLUE, ORANGE, (0, 0, 0)]
WHITE_IDX = 0
BLUE_IDX = 1
ORANGE_IDX = 2


class MovingAtom:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def position(self, t):
        sx, sy = self.source
        tx, ty = self.target
        return (sx + (tx - sx) * t, sy + (ty - sy) * t)


def border_points(size):
    points = []
    for x in range(size):
        points.append((x, 0))
        points.append((x, size - 1))
    for y in range(1, size - 1):
        points.append((0, y))
        points.append((size - 1, y))
    return points


def greedy_assign(sources, targets):
    available = list(sources)
    assignments = []
    for tx, ty in targets:
        best_idx = 0
        best_dist = None
        for i, (sx, sy) in enumerate(available):
            dist = abs(sx - tx) + abs(sy - ty)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_idx = i
        assignments.append((available.pop(best_idx), (tx, ty)))
    return assignments


def grid_to_px(point):
    x, y = point
    return (
        MARGIN_PX + x * CELL_SIZE_PX,
        MARGIN_PX + y * CELL_SIZE_PX,
    )


def draw_disk(pixels, width, height, cx, cy, radius, color_idx):
    r2 = radius * radius
    xmin = max(0, int(cx - radius))
    xmax = min(width - 1, int(cx + radius))
    ymin = max(0, int(cy - radius))
    ymax = min(height - 1, int(cy + radius))
    for y in range(ymin, ymax + 1):
        dy = y - cy
        for x in range(xmin, xmax + 1):
            dx = x - cx
            if dx * dx + dy * dy <= r2:
                pixels[y * width + x] = color_idx


def make_base_frame(width, height, occupied_targets):
    pixels = bytearray([WHITE_IDX] * (width * height))
    for point in occupied_targets:
        cx, cy = grid_to_px(point)
        draw_disk(pixels, width, height, cx, cy, ATOM_RADIUS_PX, BLUE_IDX)
    return pixels


def lzw_encode_gif_indices(indices, min_code_size):
    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    next_code = end_code + 1
    code_size = min_code_size + 1

    dictionary = {bytes([i]): i for i in range(clear_code)}

    codes = [clear_code]
    w = bytes([indices[0]])

    for k in indices[1:]:
        wk = w + bytes([k])
        if wk in dictionary:
            w = wk
        else:
            codes.append(dictionary[w])
            if next_code < 4096:
                dictionary[wk] = next_code
                next_code += 1
                if next_code == (1 << code_size) and code_size < 12:
                    code_size += 1
            else:
                codes.append(clear_code)
                dictionary = {bytes([i]): i for i in range(clear_code)}
                code_size = min_code_size + 1
                next_code = end_code + 1
            w = bytes([k])

    codes.append(dictionary[w])
    codes.append(end_code)

    # Re-encode with dynamic code sizes while packing bits
    output = bytearray()
    dictionary = {bytes([i]): i for i in range(clear_code)}
    next_code = end_code + 1
    code_size = min_code_size + 1

    bit_buffer = 0
    bit_count = 0

    def push_code(code, size):
        nonlocal bit_buffer, bit_count
        bit_buffer |= (code << bit_count)
        bit_count += size
        while bit_count >= 8:
            output.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

    push_code(clear_code, code_size)
    w = bytes([indices[0]])

    for k in indices[1:]:
        wk = w + bytes([k])
        if wk in dictionary:
            w = wk
        else:
            push_code(dictionary[w], code_size)
            if next_code < 4096:
                dictionary[wk] = next_code
                next_code += 1
                if next_code == (1 << code_size) and code_size < 12:
                    code_size += 1
            else:
                push_code(clear_code, code_size)
                dictionary = {bytes([i]): i for i in range(clear_code)}
                code_size = min_code_size + 1
                next_code = end_code + 1
            w = bytes([k])

    push_code(dictionary[w], code_size)
    push_code(end_code, code_size)

    if bit_count > 0:
        output.append(bit_buffer & 0xFF)

    return bytes(output)


def write_gif(path, width, height, frames, delay_cs):
    min_code_size = 2

    with path.open("wb") as f:
        f.write(b"GIF89a")
        f.write(struct.pack("<HH", width, height))

        packed = 0b11110001  # GCT flag=1, color res=111, sort=0, gct size=001 -> 4 colors
        f.write(bytes([packed, 0, 0]))

        for r, g, b in PALETTE:
            f.write(bytes([r, g, b]))

        # Netscape loop extension (loop forever)
        f.write(b"!\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00")

        for frame in frames:
            # Graphic Control Extension
            f.write(b"!\xF9\x04")
            f.write(bytes([0x00]))
            f.write(struct.pack("<H", delay_cs))
            f.write(bytes([0x00, 0x00]))

            # Image Descriptor
            f.write(b",")
            f.write(struct.pack("<HHHH", 0, 0, width, height))
            f.write(bytes([0x00]))

            compressed = lzw_encode_gif_indices(frame, min_code_size)
            f.write(bytes([min_code_size]))

            i = 0
            while i < len(compressed):
                block = compressed[i : i + 255]
                f.write(bytes([len(block)]))
                f.write(block)
                i += 255
            f.write(b"\x00")

        f.write(b";")


def write_ppm(path, width, height, frame):
    with path.open("wb") as f:
        f.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        rgb = bytearray()
        for idx in frame:
            r, g, b = PALETTE[idx]
            rgb.extend([r, g, b])
        f.write(rgb)


def generate(output_dir: Path):
    rng = random.Random(RANDOM_SEED)

    start = (VISIBLE_GRID_SIZE - TARGET_GRID_SIZE) // 2
    target_points = [
        (x, y)
        for y in range(start, start + TARGET_GRID_SIZE)
        for x in range(start, start + TARGET_GRID_SIZE)
    ]

    total_sites = len(target_points)
    missing_count = round(total_sites * MISSING_FRACTION)
    missing_indices = set(rng.sample(range(total_sites), missing_count))

    occupied_targets = [p for i, p in enumerate(target_points) if i not in missing_indices]
    missing_targets = [p for i, p in enumerate(target_points) if i in missing_indices]

    edge_pts = border_points(VISIBLE_GRID_SIZE)
    source_points = rng.sample(edge_pts, missing_count)

    assignments = greedy_assign(source_points, missing_targets)
    movers = [MovingAtom(src, tgt) for src, tgt in assignments]

    width = 2 * MARGIN_PX + CELL_SIZE_PX * (VISIBLE_GRID_SIZE - 1)
    height = 2 * MARGIN_PX + CELL_SIZE_PX * (VISIBLE_GRID_SIZE - 1)
    frames = []

    base = make_base_frame(width, height, occupied_targets)

    init_frame = bytearray(base)
    for p in source_points:
        cx, cy = grid_to_px(p)
        draw_disk(init_frame, width, height, cx, cy, ATOM_RADIUS_PX, ORANGE_IDX)
    for _ in range(INITIAL_HOLD_FRAMES):
        frames.append(bytearray(init_frame))

    for step in range(1, MOVE_FRAMES + 1):
        t = step / MOVE_FRAMES
        frame = bytearray(base)
        for atom in movers:
            cx, cy = grid_to_px(atom.position(t))
            draw_disk(frame, width, height, cx, cy, ATOM_RADIUS_PX, ORANGE_IDX)
        frames.append(frame)

    for blink in range(BLINK_CYCLES * 2):
        frame = bytearray(base)
        color = ORANGE_IDX if blink % 2 == 0 else BLUE_IDX
        for p in missing_targets:
            cx, cy = grid_to_px(p)
            draw_disk(frame, width, height, cx, cy, ATOM_RADIUS_PX, color)
        for _ in range(BLINK_FRAME_HOLD):
            frames.append(bytearray(frame))

    final_frame = bytearray(base)
    for p in missing_targets:
        cx, cy = grid_to_px(p)
        draw_disk(final_frame, width, height, cx, cy, ATOM_RADIUS_PX, BLUE_IDX)
    for _ in range(FINAL_HOLD_FRAMES):
        frames.append(bytearray(final_frame))

    output_dir.mkdir(parents=True, exist_ok=True)
    gif_path = output_dir / "refill_animation.gif"
    ppm_path = output_dir / "refill_initial_state.ppm"

    write_gif(gif_path, width, height, frames, FRAME_DURATION_CS)
    write_ppm(ppm_path, width, height, init_frame)

    return gif_path, ppm_path, missing_count, len(frames)


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    gif_path, ppm_path, missing_count, frame_count = generate(out_dir)
    print(f"Saved {gif_path}")
    print(f"Saved {ppm_path}")
    print(f"Missing/refill atoms: {missing_count}")
    print(f"Total frames: {frame_count}")
