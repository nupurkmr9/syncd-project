import numpy as np
from PIL import Image, ImageFile, ImageOps
from torchvision import transforms

Image.MAX_IMAGE_PIXELS = None
ImageFile.LOAD_TRUNCATED_IMAGES = True


def square_crop_with_mask(img, mask, random=False, scale=None, min_padding=200, max_padding=None):
    # Calculate dimensions to get the largest possible square
    width, height = img.size

    bbox = mask_to_bbox(np.array(mask)/255, square=False)
    if bbox is None:
        return img, Image.new('L', color=255, size=img.size), 1.0

    if random:
        newbbox = _jitter_bbox(bbox, width, height, min_padding=min_padding, max_padding=max_padding)  # max_dim, max_dim)

        if newbbox[2] - newbbox[0] > width or newbbox[3] - newbbox[1] > height:
            print(newbbox, width, bbox)
        img_cropped = transforms.functional.crop(
                img,
                top=newbbox[1],
                left=newbbox[0],
                height=newbbox[3] - newbbox[1],
                width=newbbox[2] - newbbox[0],
            )
        mask_cropped = transforms.functional.crop(
                    mask,
                    top=newbbox[1],
                    left=newbbox[0],
                    height=newbbox[3] - newbbox[1],
                    width=newbbox[2] - newbbox[0],
                )
    else:
        img_cropped = img
        mask_cropped = mask
    return img_cropped, mask_cropped, scale


def _jitter_bbox(bbox, w, h, min_padding=200, max_padding=None):
    if max_padding is not None:
        ul0 = np.random.randint(max(0, bbox[0] - max_padding), max(1, bbox[0] - min_padding))
        ul1 = np.random.randint(max(0, bbox[1] - max_padding), max(1, bbox[1] - min_padding))
    else:
        ul0 = np.random.randint(0, max(1, bbox[0] - min_padding))
        ul1 = np.random.randint(0, max(1, bbox[1] - min_padding))

    if max_padding is not None:
        lr0 = np.random.randint(min(bbox[2] + min_padding, w-1), min(w, bbox[2] + max_padding))
        lr1 = np.random.randint(min(bbox[3] + min_padding, h-1), min(h, bbox[3] + max_padding))
    else:
        lr0 = np.random.randint(min(bbox[2] + min_padding, w-1), w)
        lr1 = np.random.randint(min(bbox[3] + min_padding, h-1), h)

    bbox = np.array([ul0, ul1, lr0, lr1])
    center = ((bbox[:2] + bbox[2:]) / 2).round().astype(int)
    s = min(lr0 - ul0, lr1 - ul1) // 2
    square_bbox = np.array(
        [center[0] - s, center[1] - s, center[0] + s, center[1] + s],
        dtype=np.float32,
    )

    return square_bbox


def square_bbox(bbox, padding=0.0, astype=None):
    if astype is None:
        astype = type(bbox[0])
    bbox = np.array(bbox)
    center = ((bbox[:2] + bbox[2:]) / 2).round().astype(int)
    extents = (bbox[2:] - bbox[:2]) / 2
    s = (max(extents) * (1 + padding)).round().astype(int)
    square_bbox = np.array(
        [center[0] - s, center[1] - s, center[0] + s, center[1] + s],
        dtype=astype,
    )

    return square_bbox


def mask_to_bbox(mask, square=False):
    """
    xyxy format
    """

    mask = mask > 0.1
    if not np.any(mask):
        return None
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    if cmax <= cmin or rmax <= rmin:
        return None
    bbox = np.array([int(cmin), int(rmin), int(cmax) + 1, int(rmax) + 1])
    if square:
        bbox = square_bbox(bbox.astype(np.float32))
    return bbox


def crop_by_mask(img, mask):
    width, height = img.size
    max_dim = max(width, height)
    # bbox = np.array([0,0,max_dim,max_dim])
    maskarray = np.array(mask)/255
    bbox = mask_to_bbox(maskarray, square=True)
    # print(bbox, maskarray.min(), maskarray.max())
    if bbox is None:
        return img, Image.new('L', color=255, size=img.size)
    if not np.any(bbox - np.array([0, 0, max_dim, max_dim])):
        mask = ImageOps.invert(mask)
        bbox = mask_to_bbox(np.array(mask)/255, square=True)

    image_crop = transforms.functional.crop(
                img,
                top=bbox[1],
                left=bbox[0],
                height=bbox[3] - bbox[1],
                width=bbox[2] - bbox[0],
            )
    mask_crop = transforms.functional.crop(
                mask,
                top=bbox[1],
                left=bbox[0],
                height=bbox[3] - bbox[1],
                width=bbox[2] - bbox[0],
            )
    return image_crop, mask_crop


def square_crop_shortest_side(img):
    # Calculate dimensions to get the largest possible square
    width, height = img.size
    max_dim = min(width, height)

    # Calculate new bounding box dimensions
    top = left = 0
    new_top = max(0, top - (max_dim - height) // 2)
    new_left = max(0, left - (max_dim - width) // 2)
    new_bottom = min(height, new_top + max_dim)
    new_right = min(width, new_left + max_dim)
    img = img.crop((new_left, new_top, new_right, new_bottom))
    return img
