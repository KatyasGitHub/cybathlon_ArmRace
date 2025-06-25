import random, shutil
from pathlib import Path

# ❶ Folders you already have
src_img = Path('dataset/images_all')   # all 70 jpg/png files

# ❷ Shuffle once and cut 80 : 20
imgs = list(src_img.glob('*.*'))
random.shuffle(imgs)
cut = int(0.8 * len(imgs))             # 56 train, 14 val

def copy_batch(batch, split):
    (Path(f'dataset/images/{split}')).mkdir(parents=True, exist_ok=True)
    for img in batch:
        shutil.copy2(img, f'dataset/images/{split}/{img.name}')
       
copy_batch(imgs[:cut], 'train')
copy_batch(imgs[cut:], 'val')
print('Split complete.')