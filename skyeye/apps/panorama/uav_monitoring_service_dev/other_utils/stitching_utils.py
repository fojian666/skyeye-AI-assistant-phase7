from pathlib import Path
from configs.device_config import *


def get_image_paths(img_set):
    return [str(path.relative_to('.')) for path in Path(img_set).rglob(f'*.JPG')]


if __name__ == '__main__':
    res = get_image_paths(PANORAMA_PATH)
    print(res)