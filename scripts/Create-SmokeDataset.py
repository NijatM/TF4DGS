"""Generate a tiny known-pose COLMAP fixture for software checks only.

Uses Python's standard library. This checks dataset loading/training; it does
not test SfM pose estimation, real capture quality or deformation accuracy.
"""
import argparse
import math
from pathlib import Path
import struct
import zlib


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def normalized(v):
    length = math.sqrt(dot(v, v))
    return tuple(x / length for x in v)


def quaternion(matrix):
    trace = sum(matrix[i][i] for i in range(3))
    if trace > 0:
        s = math.sqrt(trace + 1) * 2
        return (s/4, (matrix[2][1]-matrix[1][2])/s,
                (matrix[0][2]-matrix[2][0])/s, (matrix[1][0]-matrix[0][1])/s)
    i = max(range(3), key=lambda k: matrix[k][k])
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1 + matrix[i][i] - matrix[j][j] - matrix[k][k]) * 2
    result = [(matrix[k][j]-matrix[j][k])/s, 0, 0, 0]
    result[i+1] = s/4
    result[j+1] = (matrix[j][i]+matrix[i][j])/s
    result[k+1] = (matrix[k][i]+matrix[i][k])/s
    return tuple(result)


def intersect_cube(origin, direction):
    near, far = -math.inf, math.inf
    for o, d in zip(origin, direction):
        if abs(d) < 1e-12:
            if abs(o) > 0.5:
                return None
            continue
        a, b = (-0.5-o)/d, (0.5-o)/d
        near, far = max(near, min(a, b)), min(far, max(a, b))
    if far < max(near, 0):
        return None
    return tuple(o + max(near, 0)*d for o, d in zip(origin, direction))


def color(point):
    axis = max(range(3), key=lambda k: abs(point[k]))
    palette = ((210, 65, 45), (45, 185, 70), (55, 105, 220))
    u, v = point[(axis+1) % 3], point[(axis+2) % 3]
    checker = (math.floor((u+0.5)*8)+math.floor((v+0.5)*8)) % 2
    factor = 0.55 if checker else 1.0
    return tuple(round(channel*factor) for channel in palette[axis])


def write_png(path, width, height, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data))
    rows = b''.join(b'\x00' + pixels[y*width*3:(y+1)*width*3] for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' +
                     chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
                     chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def create_dataset(root):
    images, sparse = root / 'images', root / 'sparse' / '0'
    images.mkdir(parents=True, exist_ok=False)
    sparse.mkdir(parents=True, exist_ok=False)
    width, height, focal = 128, 128, 110.0
    points = []
    for axis in range(3):
        for sign in (-1, 1):
            for a in range(9):
                for b in range(9):
                    p = [0.0]*3
                    p[axis] = sign*0.5
                    p[(axis+1) % 3] = -0.45+a*0.1125
                    p[(axis+2) % 3] = -0.45+b*0.1125
                    points.append(tuple(p))
    tracks = [[] for _ in points]
    image_lines = []
    for index in range(8):
        angle = index*2*math.pi/8 + 0.17
        center = (2.3*math.cos(angle), 2.3*math.sin(angle), 1.1)
        forward = normalized(tuple(-x for x in center))
        right = normalized(cross(forward, (0, 0, 1)))
        down = cross(forward, right)
        rotation = (right, down, forward)
        translation = tuple(-dot(row, center) for row in rotation)
        pixels = bytearray()
        for y in range(height):
            for x in range(width):
                direction = tuple(forward[k] + right[k]*(x+0.5-width/2)/focal +
                                  down[k]*(y+0.5-height/2)/focal for k in range(3))
                hit = intersect_cube(center, direction)
                pixels.extend(color(hit) if hit is not None else (0, 0, 0))
        name = f'view_{index:02d}.png'
        write_png(images / name, width, height, pixels)
        observations = []
        for point_index, p in enumerate(points):
            relative = tuple(p[k]-center[k] for k in range(3))
            camera = tuple(dot(row, relative) for row in rotation)
            hit = intersect_cube(center, relative)
            if camera[2] <= 0 or hit is None or max(abs(hit[k]-p[k]) for k in range(3)) > 1e-6:
                continue
            x, y = focal*camera[0]/camera[2]+width/2, focal*camera[1]/camera[2]+height/2
            if 0 <= x < width and 0 <= y < height:
                tracks[point_index].append((index+1, len(observations)))
                observations.append((x, y, point_index+1))
        values = (index+1, *quaternion(rotation), *translation, 1, name)
        image_lines += [' '.join(map(str, values)),
                        ' '.join(' '.join(map(str, observation)) for observation in observations)]
    (sparse / 'cameras.txt').write_text(f'1 PINHOLE {width} {height} {focal} {focal} {width/2} {height/2}\n', encoding='ascii')
    (sparse / 'images.txt').write_text('\n'.join(image_lines)+'\n', encoding='ascii')
    point_lines = []
    for index, (p, track) in enumerate(zip(points, tracks)):
        if track:
            values = (index+1, *p, *color(p), 0.0, *(value for pair in track for value in pair))
            point_lines.append(' '.join(map(str, values)))
    (sparse / 'points3D.txt').write_text('\n'.join(point_lines)+'\n', encoding='ascii')
    print(f'Created software fixture: {root}; 8 images; {len(point_lines)} points')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    create_dataset(parser.parse_args().output.resolve())
