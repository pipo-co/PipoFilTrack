import os
import glob
import cv2
import shutil
from PIL import Image, ImageSequence
from cairosvg import svg2png
from werkzeug.utils import secure_filename
from matplotlib import pyplot as plt
import matplotlib
import numpy as np

matplotlib.use('Agg')

# TODO(tobi): When we are happy with the tracking algorithm we should review all image manipulation algorithms. They probably suck
def get_frame(cell_path, invert: bool = False):
    img16 = cv2.imread(cell_path, cv2.IMREAD_UNCHANGED)
    img16 = ((img16 - img16.min()) / (img16.max() - img16.min())) * 255 
    img8 = img16.astype('uint8')
    if len(img8.shape) == 3:  # Image is not grayscale
        # Conversion to grayscale
        img8 = cv2.cvtColor(img8, cv2.COLOR_BGR2GRAY)
    if invert or ((img8 >= 128).sum() > (img8 < 128).sum()):
        img8 = cv2.bitwise_not(img8)
        invert = True
    return img8, invert


def gauss_img(img):
    img2 = blur_img(img, 5)
    return cv2.adaptiveThreshold(img2, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)


def blur_img(img, factor: int = 5):
    return cv2.medianBlur(img, factor)


def add_img_to_plot(img) -> None:
    plt.imshow(img, 'gray')


def add_points_to_plot(points: np.ndarray, color='darkgrey', scatter: bool = False) -> None:
    if points is None:
        return

    if color == 'rainbow':
        pass

    if scatter:
        plt.scatter(points[:, 0], points[:, 1], s=1, c=color)
    else:
        plt.plot(points[:, 0], points[:, 1], color)

def add_normal_lines(nomal_points: np.ndarray, color='darkgrey') -> None:
    if nomal_points is None:
        return

    if color == 'rainbow':
        pass

    for points in nomal_points:
        plt.plot(points[:, 0], points[:, 1], color)


def save_plot(folder, name):
    plt.axis('off')
    filename = f'{folder}/results/result_{name}.svg'
    if os.path.exists(filename):
        os.remove(filename)
    plt.savefig(filename, bbox_inches='tight', pad_inches=0, format="svg")
    # plt.gca().invert_yaxis()
    plt.close()


def resize_image(image: Image, length: int) -> Image:
    """
    Resize an image to a square. Can make an image bigger to make it fit or smaller if it doesn't fit. It also crops
    part of the image.

    :param image: Image to resize.
    :param length: Width and height of the output image.
    :return: Return the resized image.
    """

    """
    Resizing strategy : 
     1) We resize the smallest side to the desired dimension (e.g. 1080)
     2) We crop the other side so as to make it fit with the same length as the smallest side (e.g. 1080)
    """
    if image.size[0] < image.size[1]:
        # The image is in portrait mode. Height is bigger than width.

        # This makes the width fit the LENGTH in pixels while conserving the ration.
        resized_image = image.resize((length, int(image.size[1] * (length / image.size[0]))))

        # Amount of pixel to lose in total on the height of the image.
        required_loss = (resized_image.size[1] - length)

        # Crop the height of the image so as to keep the center part.
        resized_image = resized_image.crop(
            box=(0, required_loss / 2, length, resized_image.size[1] - required_loss / 2))

        # We now have a length*length pixels image.
        return resized_image
    else:
        # This image is in landscape mode or already squared. The width is bigger than the height.

        # This makes the height fit the LENGTH in pixels while conserving the ration.
        resized_image = image.resize((int(image.size[0] * (length / image.size[1])), length))

        # Amount of pixel to lose in total on the width of the image.
        required_loss = resized_image.size[0] - length

        # Crop the width of the image so as to keep 1080 pixels of the center part.
        resized_image = resized_image.crop(
            box=(required_loss / 2, 0, resized_image.size[0] - required_loss / 2, length))

        # We now have a length*length pixels image.
        return resized_image


# Create a jpg file with the first tiff image from the imported ones so the user can mark the points on the interface
def save_first_frame_as_jpg(server_folder, filename, complete_filename):
    first_image = '/'.join([server_folder, os.path.splitext(filename)[0] + ".jpg"])
    first_image_filter = '/'.join([server_folder, os.path.splitext(filename)[0] + "filter.jpg"])
    try:
        im = cv2.imread(complete_filename, cv2.IMREAD_UNCHANGED)
        im = ((im - im.min()) / (im.max() - im.min())) * 255 
        im = im.astype('uint8')
        if len(im.shape) == 3:  # Image is not grayscale
            # Conversion to grayscale
            im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

        im_filter = gauss_img(im)

        cv2.imwrite(first_image, im)
        cv2.imwrite(first_image_filter, im_filter)
    except Exception as e:
        print('Warning. Exception on save_first_frame_as_jpg. First image was probably not saved. ', e)

    return first_image, first_image_filter, im.shape


def check_is_multitiff(server_folder, complete_filename, extension):
    img = Image.open(complete_filename)
    if img.n_frames > 1:  # If there is more than 1 frame, it's a multi tiff image
        os.rename(complete_filename, f'{server_folder}/multi{extension}')
        # Save each frame as an individual tiff file
        for i, frame in enumerate(ImageSequence.Iterator(img)):
            filename = secure_filename(str(i) + extension)
            complete_filename = '/'.join([server_folder, filename])
            if frame.height != frame.width:
                frame = resize_image(frame, min(frame.size[0], frame.size[1]))
            frame.save(complete_filename)

        # Delete the multi tiff file because we already saved each frame
        os.remove(f'{server_folder}/multi{extension}')


def convert_jpg_to_tif(complete_filename):
    img = Image.open(complete_filename)
    if img.height != img.width:
        img = resize_image(img, min(img.height, img.width))
    img.save(complete_filename)

    jpg_image = cv2.imread(complete_filename)
    tif_complete_filename = complete_filename.replace('jpg', 'tif').replace('jpeg', 'tif')
    cv2.imwrite(tif_complete_filename, jpg_image)
    os.remove(complete_filename)


def convert_avi_to_tif(server_folder, complete_filename):
    video = cv2.VideoCapture(complete_filename)

    i = 0
    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        filename = secure_filename(str(i) + '.tif')
        complete_filename = '/'.join([server_folder, filename])
        cv2.imwrite(complete_filename, frame)

        img = Image.open(complete_filename)
        if img.height != img.width:
            img = resize_image(img, min(img.height, img.width))
        img.save(complete_filename)

        if i == 0:
            save_first_frame_as_jpg(server_folder, filename, complete_filename)
        i += 1

    video.release()
    cv2.destroyAllWindows()
    # Delete the avi file because we already saved each frame
    os.remove('/'.join([server_folder, '0.avi']))


def create_film(folder):
    img_array = []
    size = 0
    frames = sorted(glob.glob(f'{folder}/*.svg'), key=os.path.getmtime)
    for filename in frames:
        png = svg2png(url=filename)
        par = np.fromstring(png, np.uint8)
        img = cv2.imdecode(par, cv2.IMREAD_UNCHANGED)
        height, width, layers = img.shape
        size = (width, height)
        img_array.append(img)

    fps = 5 if len(frames) > 10 else 1
    out = cv2.VideoWriter(f'{folder}/download/film.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, size)

    for i in range(len(img_array)):
        out.write(img_array[i])

    out.release()


def create_result_zip(folder):
    shutil.make_archive(f'{folder}/results', 'zip', f'{folder}/download')
