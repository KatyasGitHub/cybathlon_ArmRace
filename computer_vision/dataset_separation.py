import random, shutil
from pathlib import Path

# src_img, src_lbl = Path('dataset/images_all'), Path('computer_vision/dataset/labels_all')
src_img = Path('computer_vision/dataset/images_all')
src_lbl = Path('computer_vision/dataset/labels_all')

imgs = list(src_img.glob('*.*')); random.shuffle(imgs)
cut = int(0.8 * len(imgs))                          # 80 : 20 split

def copy_batch(batch, split):
    Path(f'computer_vision/dataset/images/{split}').mkdir(parents=True, exist_ok=True)
    Path(f'computer_vision/dataset/labels/{split}').mkdir(parents=True, exist_ok=True)
    for img in batch:
        shutil.copy2(img, f'computer_vision/dataset/images/{split}/{img.name}')
        lbl = src_lbl / f'{img.stem}.txt'           # label filename matches image stem
        if lbl.exists():
            shutil.copy2(lbl, f'computer_vision/dataset/labels/{split}/{lbl.name}')

copy_batch(imgs[:cut], 'train')
copy_batch(imgs[cut:], 'val')
print('Split complete.')