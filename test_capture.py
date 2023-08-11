import time
from picamera import PiCamera
from PIL import Image
import numpy as np

# LUT-таблицы
lut_sqrt = np.zeros((256), dtype=np.uint8)

for i in range(0, 256):
    lut_sqrt[i] = (i * 255) ** (1/2)

with PiCamera() as camera:
    camera.resolution = (2592, 1944)
    path = '/home/evgenii/plants_final/test_image.jpg'
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
    #rotated_image = processed_image.rotate(270, expand=True)

        # Сохраняем измененное изображение
    processed_image.save(path)
    #rotated_image.save(path)
