from flask import Flask, render_template_string, send_from_directory, redirect, request
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from flask_apscheduler import APScheduler

import serial
import time
import pytz
from datetime import datetime
import cv2
import numpy as np
from loguru import logger

@logger.catch
def is_conditioner_on_off_by_photo():
    h1, h2 = 640, 720
    w1, w2 = 210, 260
    img = cv2.imread("/home/evgenii/plants_final/image.jpg")
    img_cropped = img[h1:h2, w1:w2]
    hsv_frame = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 100, 100])
    upper_green = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv_frame, lower_green, upper_green)
    green_mask = green_mask / 255
    flag = None
    if np.sum(green_mask) > 100:
        logger.info("Зеленых пикселей больше 100")
        return True
    else:
        logger.info("Зеленых пикселей меньше 100")
        return False


# Класс пользователя
class User(UserMixin):
    def __init__(self, id):
        self.id = id


logger.add("/home/evgenii/plants_final/logs.log", rotation="500 MB", format="{time:YYYY-MM-DD at HH:mm:ss} | {message}")
logger.info("Старт приложения")
manual_control = False

logger.info("Спим 5 секунд и узнаем статус кондиционера")
time.sleep(5)
conditioner_status = is_conditioner_on_off_by_photo()
logger.info("Статус кондиционера {}", conditioner_status)
is_rest_need = False
six_hours = 6 * 60 * 60 # 6 hours

rest_start_time = 0
rest_time = 60 * 10 # 10 min
last_turn_off_time = time.time() 
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)



app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Не забудьте заменить на надежный ключ в продакшене

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()

@logger.catch
def read_sensor_data():
    line = ser.readline()   # читайте строку из последовательного порта
    try:
        decoded_line = line.decode('utf-8').strip()
        t, h = map(float, decoded_line.split(',')) # Предположим, что температура и влажность разделены запятой
    except:
        t, h = "Error", "Error"
    time.sleep(2) # Читать только раз в 2 секунды
    return t, h

@logger.catch
def toggle_conditioner_power():
    max_attempts = 3  # максимальное количество попыток
    attempts = 0
    global conditioner_status

    while attempts < max_attempts:
        ser.write(b'P')
        logger.info("Попытка изменить статус кондиционера. Спим 11 секунд")
        time.sleep(11)  # дайте некоторое время на включение/выключение
        is_on = is_conditioner_on_off_by_photo()
        if is_on is not None and is_on != conditioner_status:  # Если состояние изменилось
            conditioner_status = is_on
            logger.info(f"Статус кондиционера после смены флага и проверки фото: {'Включен' if conditioner_status else 'Выключен'}")
            return True
        attempts += 1
        logger.info(f"Попытка {attempts}: не удалось изменить состояние кондиционера, повторная попытка.")

    if attempts == max_attempts:
        logger.info("Не удалось изменить состояние кондиционера после максимального количества попыток.")
        return False
    
@scheduler.task('cron', minute='*')
def conditioner_scheduler():
    global conditioner_status
    if manual_control:
        return

    tz = pytz.timezone('Asia/Tbilisi')
    current_time = datetime.now(tz)
    if 4 <= current_time.hour < 7:
        if conditioner_status:
            logger.info("Время от 4 до 7 утра, выключаю кондиционер")
            conditioner_status = toggle_conditioner_power()
            #ser.write(b'P')  # Выключить кондиционер
            #conditioner_status = False
    elif not conditioner_status: # Если текущее время вне диапазона и кондиционер выключен
        logger.info("Время вне диапазона от 4 до 7 утра, включаю кондиционер")
        conditioner_status = toggle_conditioner_power()
    else:
        t,h = read_sensor_data()
        logger.info("Время: {}, температура: {}, влажность: {}", current_time, t, h) 
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'kakashka12345': # Замените на надежный метод проверки
            user = User(1)
            login_user(user)
            return redirect('/')
        else:
            return 'Неправильный логин или пароль'
    return '''
    <form method="post">
        Username: <input type="text" name="username"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/')
@login_required
def index():
    global conditioner_status
    global manual_control
    t, h = read_sensor_data()
    #print(f"Debug: Состояние кондиционера в index: {'Включен' if conditioner_status else 'Выключен'}")
    tz = pytz.timezone('Asia/Tbilisi')
    
    # Получаем текущее время в заданной временной зоне
    current_time = datetime.now(tz)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info("Статус кондиционера index {}", conditioner_status)
    return render_template_string('''
    <html>
    <head>
        <title>Image Viewer</title>
        <meta http-equiv="refresh" content="5">
    </head>
    <body>
        <img src="/image" width="480" height="736"><br>
        <p>Текущее время: {{ formatted_time }}</p>
        <p>Температура: {{ t }} °C</p>
		<p>Влажность: {{ h }} %</p>
        <p>Состояние кондиционера: {{ "Включен" if conditioner_status else "Выключен" }}</p>
        <p>Режим управления: {{ "Ручное Управление" if manual_control else "Автоматическое Управление" }}</p>
        <button onclick="location.href='/set_manual_control'">Переключить на {{ "Ручное Управление" if not manual_control else "Автоматическое Управление" }}</button>
        <button onclick="location.href='/control?cmd=power'">Включить/Выключить</button>
        <button onclick="location.href='/control?cmd=up'">Повысить температуру</button>
        <button onclick="location.href='/control?cmd=down'">Понизить температуру</button>
        <button onclick="location.href='/control?cmd=fan'">Изменить скорость</button>
    </body>
    </html>
    ''', manual_control=manual_control, formatted_time=formatted_time, t=t, h=h, conditioner_status=conditioner_status)

@app.route('/control')
@login_required
def control():
    cmd = request.args.get('cmd')
    if cmd == 'power':
     #   ser.write(b'P')
     #   global conditioner_status
        logger.info("Статус кондиционера control до смены флага {}", conditioner_status)
        toggle_conditioner_power()
     #   conditioner_status = not conditioner_status
        logger.info("Статус кондиционера control после смены флага {}", conditioner_status)
    elif cmd == 'up':
        ser.write(b'I')
    elif cmd == 'down':
        ser.write(b'D')
    elif cmd == 'fan':
        ser.write(b'S')

	# Вернуться обратно на главную страницу
    return redirect('/')

@app.route('/set_manual_control')
@login_required
def set_manual_control():
    global manual_control
    logger.info("Меняю режим управления")
    manual_control = not manual_control
    logger.info(f"Режим управления {'Manual' if manual_control else 'Auto'}") 
    return redirect('/')

@app.route('/image')
@login_required
def serve_image():
    return send_from_directory('/home/evgenii/plants_final', 'image.jpg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
