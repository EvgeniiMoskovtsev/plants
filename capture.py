import time
import os
from picamera import PiCamera
from fractions import Fraction
from PIL import Image
import numpy as np
import datetime

logged_path = '/home/evgenii/plants_final/logged_images'
logged_last_saved_time = 0
# LUT-таблицы
lut_sqrt = np.zeros((256), dtype=np.uint8)

for i in range(0, 256):
    lut_sqrt[i] = (i * 255) ** (1/2) 

with PiCamera() as camera:
#with PiCamera(framerate=Fraction(1,6), sensor_mode=3) as camera:
    #camera.shutter_speed = 3000000
    #camera.iso = 400
    #time.sleep(30)
    #camera.exposure_mode = 'off'
    path = '/home/evgenii/plants_final/image.jpg'
    while True:
        camera.capture(path)

        # Открываем изображение с помощью PIL
        image = Image.open(path)

        # Преобразуем изображение в массив numpy
        img_array = np.array(image)

        # Применяем LUT (например, lut_sqrt для корневой функции)
        img_array = lut_sqrt[img_array]

        # Создаем изображение из обновленного массива
        processed_image = Image.fromarray(img_array)
        # Поворачиваем изображение на 90 градусов
        rotated_image = processed_image.rotate(270, expand=True)

        # Сохраняем измененное изображение
        #print(rotated_image.size)
        rotated_image.save(path)
        # Сохраняем копию изображения каждый час
        if time.time() - logged_last_saved_time >= 3600:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            logged_image_path = os.path.join(logged_path, f'image_{timestamp}.jpg')
            rotated_image.save(logged_image_path)
            logged_last_saved_time = time.time()

        time.sleep(5)
