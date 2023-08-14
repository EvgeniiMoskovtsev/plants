import time
import os
from picamera import PiCamera
from PIL import Image
import numpy as np
import datetime
import cv2

logged_path = '/home/evgenii/plants_final/logged_images'
logged_last_saved_time = 0
# LUT-таблицы
lut_sqrt = np.zeros((256), dtype=np.uint8)

for i in range(0, 256):
    lut_sqrt[i] = (i * 255) ** (1/2)

with PiCamera() as camera:
    path = '/home/evgenii/plants_final/image.jpg'
    camera.resolution = (736, 480)
    time.sleep(2)
    while True:
        img_array = np.empty((480, 736, 3), dtype=np.uint8)
        camera.capture(img_array, 'rgb')
        # Применяем LUT (например, lut_sqrt для корневой функции)
        img_array = lut_sqrt[img_array]

        # Создаем изображение из обновленного массива
        rotated_image = np.rot90(img_array,3)
        # Сохраняем копию изображения каждый час
        if time.time() - logged_last_saved_time >= 3600:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            logged_image_path = os.path.join(logged_path, f'image_{timestamp}.jpg')
            cv2.imwrite(logged_image_path, rotated_image)
            logged_last_saved_time = time.time()
        cv2.imwrite(path, rotated_image)
        time.sleep(5)
