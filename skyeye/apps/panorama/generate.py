from __future__ import print_function
import argparse
import shutil

from PIL import Image
import os
import sys
import math
import ast
from shutil import which as find_executable
import subprocess
import base64
import io
import numpy as np

Image.MAX_IMAGE_PIXELS = None

try:
    nona = find_executable('nona')
except KeyError:
    nona = None

ANTIALIAS = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS

genPreview = False
try:
    import pyshtools as pysh
    genPreview = True
except:
    sys.stderr.write("Unable to import pyshtools. Not generating SHT preview.\n")

b83chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%*+,-.:;=?@[]^_{|}~"


def b83encode(vals, length):
    result = ""
    for val in vals:
        for i in range(1, length + 1):
            result += b83chars[int(val // (83 ** (length - i))) % 83]
    return result


def img2shtHash(img, lmax=5):
    '''
    Create spherical harmonic transform (SHT) hash preview.
    '''

    def encodeFloat(f, maxVal):
        return np.maximum(0,
                          np.minimum(2 * maxVal, np.round(np.sign(f) * np.sqrt(np.abs(f)) * maxVal + maxVal))).astype(
            int)

    def encodeCoeff(r, g, b, maxVal):
        quantR = encodeFloat(r / maxVal, 9)
        quantG = encodeFloat(g / maxVal, 9)
        quantB = encodeFloat(b / maxVal, 9)
        return quantR * 19 ** 2 + quantG * 19 + quantB

    # Calculate SHT coefficients
    r = pysh.expand.SHExpandDH(img[..., 0], sampling=2, lmax_calc=lmax)
    g = pysh.expand.SHExpandDH(img[..., 1], sampling=2, lmax_calc=lmax)
    b = pysh.expand.SHExpandDH(img[..., 2], sampling=2, lmax_calc=lmax)

    # Remove values above diagonal for both sine and cosine components
    # Also remove first row and column for sine component
    # These values are always zero
    r = np.append(r[0][np.tril_indices(lmax + 1)], r[1, 1:, 1:][np.tril_indices(lmax)])
    g = np.append(g[0][np.tril_indices(lmax + 1)], g[1, 1:, 1:][np.tril_indices(lmax)])
    b = np.append(b[0][np.tril_indices(lmax + 1)], b[1, 1:, 1:][np.tril_indices(lmax)])

    # Encode as string
    maxVal = np.max([np.max(r), np.max(b), np.max(g)])
    vals = encodeCoeff(r, g, b, maxVal).flatten()
    asstr = b83encode(vals, 2)
    lmaxStr = b83encode([lmax], 1)
    maxValStr = b83encode(encodeFloat([2 * maxVal / 255 - 1], 41), 1)
    return lmaxStr + maxValStr + asstr


# Subclass parser to add explaination for semi-option nona flag
class GenParser(argparse.ArgumentParser):
    def error(self, message):
        if '--nona' in message:
            sys.stderr.write('''IMPORTANT: The location of the nona utility (from Hugin) must be specified
           with -n, since it was not found on the PATH!\n\n''')
        super(GenParser, self).error(message)


def start_progress(input_path,output_path):
    global genPreview
    if os.path.exists(output_path):
        shutil.rmtree(output_path)

    os.makedirs(output_path)

    # Process input image information
    print('Processing input image information...')
    origWidth, origHeight = Image.open(input_path).size
    haov = -1
    if haov == -1:
        haov = 360.0
    vaov = -1
    if vaov == -1:
        vaov = 180.0
    cubeSize = 0
    if cubeSize != 0:
        cubeSize = 0
    else:
        cubeSize = 8 * math.ceil((360 / haov) * origWidth / math.pi / 8)
    tileSize = min(512, cubeSize)
    levels = int(math.ceil(math.log(float(cubeSize) / tileSize, 2))) + 1
    if int(cubeSize / 2 ** (levels - 2)) == tileSize:
        levels -= 1  # Handle edge case
    origHeight = str(origHeight)
    origWidth = str(origWidth)
    origFilename = os.path.join(os.getcwd(), input_path)

    extension = '.png'
    partialPano =  False
    colorList = ast.literal_eval('[0.0, 0.0, 0.0]')
    colorTuple = (int(colorList[0] * 255), int(colorList[1] * 255), int(colorList[2] * 255))

    # Don't generate preview for partial panoramas
    if haov < 360 or vaov < 180:
        genPreview = False

    faceLetters = ['f', 'b', 'u', 'd', 'l', 'r']
    projection = "f4"
    pitch = 0
    text = []
    facestr = 'i a0 b0 c0 d0 e' + str(
        0.0) + ' ' + projection + ' h' + origHeight + ' w' + origWidth + ' n"' + origFilename + '" r0 v' + str(
        haov)
    text.append('p E0 R0 f0 h' + str(cubeSize) + ' w' + str(cubeSize) + ' n"TIFF_m" u0 v90')
    text.append('m g1 i0 m2 p0.00784314')
    text.append(facestr + ' p' + str(pitch + 0) + ' y0')
    text.append(facestr + ' p' + str(pitch + 0) + ' y180')
    text.append(facestr + ' p' + str(pitch - 90) + ' y0')
    text.append(facestr + ' p' + str(pitch + 90) + ' y0')
    text.append(facestr + ' p' + str(pitch + 0) + ' y90')
    text.append(facestr + ' p' + str(pitch + 0) + ' y-90')
    text.append('v')
    text.append('*')
    text = '\n'.join(text)
    with open(os.path.join(output_path, 'cubic.pto'), 'w') as f:
        f.write(text)

    print('output_path',output_path)
    print('output_path',os.path.join(output_path, 'face'), os.path.join(output_path, 'cubic.pto'))
    subprocess.check_call([nona, '-g', '-o', os.path.join(output_path, 'face'),
                           os.path.join(output_path, 'cubic.pto')])
    faces = ['face0000.tif', 'face0001.tif', 'face0002.tif', 'face0003.tif', 'face0004.tif', 'face0005.tif']

    # Generate tiles
    print('Generating tiles...')
    missingTiles = []
    for f in range(0, 6):
        size = cubeSize
        faceExists = os.path.exists(os.path.join(output_path, faces[f]))
        if faceExists:
            face = Image.open(os.path.join(output_path, faces[f]))
            for level in range(levels, 0, -1):
                if not os.path.exists(os.path.join(output_path, str(level))):
                    os.makedirs(os.path.join(output_path, str(level)))
                tiles = int(math.ceil(float(size) / tileSize))
                if (level < levels):
                    face = face.resize([size, size], ANTIALIAS)
                for i in range(0, tiles):
                    for j in range(0, tiles):
                        left = j * tileSize
                        upper = i * tileSize
                        right = min(j * 512 + 512, size)  # 512 = args.tileSize
                        lower = min(i * 512 + 512, size)  # min(...) not really needed
                        tile = face.crop([left, upper, right, lower])
                        colors = tile.getcolors(1)
                        if not partialPano or colors == None or colors[0][1] != colorTuple:
                            # More than just one color (the background), i.e., non-empty tile
                            if tile.mode in ('RGBA', 'LA'):
                                background = Image.new(tile.mode[:-1], tile.size, colorTuple)
                                background.paste(tile, tile.split()[-1])
                                tile = background
                            colors = tile.getcolors(1)
                            if not genPreview and colors is not None and colors[0][1] == colorTuple:
                                missingTiles.append((f, level, j, i))
                            else:
                                tile.save(os.path.join(output_path, str(level),
                                                       faceLetters[f] + str(i) + '_' + str(j) + extension),
                                          quality=75)
                        else:
                            missingTiles.append((f, level, j, i))
                size = int(size / 2)
        else:
            missingTiles.append((f, level, 0, 0))

    # Tell viewer not to load missing tiles
    if len(missingTiles) > 0:
        # Remove children of missing tiles, since they won't be loaded anyway
        tilesToRemove = []
        for t in missingTiles:
            tilesToRemove.append((t[0], t[1] + 1, t[2] * 2, t[3] * 2))
            tilesToRemove.append((t[0], t[1] + 1, t[2] * 2, t[3] * 2 + 1))
            tilesToRemove.append((t[0], t[1] + 1, t[2] * 2 + 1, t[3] * 2))
            tilesToRemove.append((t[0], t[1] + 1, t[2] * 2 + 1, t[3] * 2 + 1))
        for t in tilesToRemove:
            if t in missingTiles:
                missingTiles.pop(missingTiles.index(t))
        # Encode missing tile list as string
        missingTilesStr = ''
        prevFace = prevLevel = None
        for missingTile in sorted(missingTiles):
            face = missingTile[0]
            level = missingTile[1]
            if face != prevFace:
                missingTilesStr += '!' + faceLetters[face]
            if level != prevLevel:
                missingTilesStr += '>' + b83encode([level], 1)
                maxTileNum = math.ceil(cubeSize / 2 ** (levels - level) / tileSize) - 1
                numTileDigits = math.ceil(math.log(maxTileNum + 1, 83))
            missingTilesStr += b83encode(missingTile[2:], numTileDigits)
            prevFace = face
            prevLevel = level

    print('Generating fallback tiles...')
    for f in range(0, 6):
        if not os.path.exists(os.path.join(output_path, 'fallback')):
            os.makedirs(os.path.join(output_path, 'fallback'))
        if os.path.exists(os.path.join(output_path, faces[f])):
            face = Image.open(os.path.join(output_path, faces[f]))
            if face.mode in ('RGBA', 'LA'):
                background = Image.new(face.mode[:-1], face.size, colorTuple)
                background.paste(face, face.split()[-1])
                face = background
            face = face.resize([1024, 1024], ANTIALIAS)
            face.save(os.path.join(output_path, 'fallback', faceLetters[f] + extension), quality=75)

    # Clean up temporary files

    os.remove(os.path.join(output_path, 'cubic.pto'))
    for face in faces:
        if os.path.exists(os.path.join(output_path, face)):
            os.remove(os.path.join(output_path, face))

    if genPreview:
        # Generate SHT-hash preview
        shtHash = img2shtHash(np.array(Image.open(input_path).resize((1024, 512))))

    # Generate config file
    text = []
    text.append('{')
    text.append('    "hfov": ' + str(100.0) + ',')
    if haov < 360:
        text.append('    "haov": ' + str(haov) + ',')
        text.append('    "minYaw": ' + str(-haov / 2 + 0) + ',')
        text.append('       "yaw": ' + str(-haov / 2 + 100 / 2) + ',')
        text.append('    "maxYaw": ' + str(+haov / 2 + 0) + ',')
    if vaov < 180:
        text.append('    "vaov": ' + str(vaov) + ',')
        text.append('    "vOffset": ' + str(0.0) + ',')
        text.append('    "minPitch": ' + str(-vaov / 2 + 0.0) + ',')
        text.append('       "pitch": ' + str(0.0) + ',')
        text.append('    "maxPitch": ' + str(+vaov / 2 + 0.0) + ',')
    if colorTuple != (0, 0, 0):
        text.append('    "backgroundColor": ' + '[0.0, 0.0, 0.0]' + ',')
    # if args.avoidbackground and (haov < 360 or vaov < 180):
    #     text.append('    "avoidShowingBackground": true,')

    text.append('    "autoLoad": true,')
    text.append('    "type": "multires",')
    text.append('    "multiRes": {')
    if genPreview:
        text.append('        "shtHash": "' + shtHash + '",')
    if len(missingTiles) > 0:
        text.append('        "missingTiles": "' + missingTilesStr + '",')
    text.append('        "path": "/%l/%s%y_%x",')
    text.append('        "fallbackPath": "/fallback/%s",')
    text.append('        "extension": "' + extension[1:] + '",')
    text.append('        "tileResolution": ' + str(tileSize) + ',')
    text.append('        "maxLevel": ' + str(levels) + ',')
    text.append('        "cubeResolution": ' + str(cubeSize))
    text.append('    }')
    text.append('}')
    text = '\n'.join(text)
    with open(os.path.join(output_path, 'config.json'), 'w') as f:
        f.write(text)

if __name__ == '__main__':
    input_path = r'G:\t2\DJI_20240724111055_0001_V.JPG'
    output_path = r'./output'
    start_progress(input_path,output_path)
