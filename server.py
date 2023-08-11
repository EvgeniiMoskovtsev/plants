from flask import Flask, render_template_string, send_from_directory, redirect, request
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
import serial
import time
import pytz
from datetime import datetime

# Класс пользователя
class User(UserMixin):
    def __init__(self, id):
        self.id = id

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Не забудьте заменить на надежный ключ в продакшене

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

manual_control = False
conditioner_status = False 
is_rest_need = False
six_hours = 6 * 60 * 60 # 6 hours

rest_start_time = 0
rest_time = 60 * 10 # 10 min
last_turn_off_time = time.time() 


ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
def read_sensor_data():
    line = ser.readline()   # читайте строку из последовательного порта
    try:
        decoded_line = line.decode('utf-8').strip()
        t, h = map(float, decoded_line.split(',')) # Предположим, что температура и влажность разделены запятой
        print(f"Debug: Температура = {t} °C, Влажность = {h} %") # Отладочная информация
    except:
        t, h = "Error", "Error"
        print("Debug: Температура и Влажность вернули ошибку")
    return t, h
	
def is_rest_need_func(conditioner_status):
    global last_turn_off_time
    global rest_start_time
    global six_hours
    current_time = time.time()
    
    # Если кондиционер включен и пришло время для отдыха
    if conditioner_status and current_time - last_turn_off_time > six_hours:
        print("Прошло 6 часов работы кондиционера. Выключаем")
        last_turn_off_time = current_time
        rest_start_time = current_time  # Записываем время начала отдыха
        return True
    
    # Если кондиционер выключен, но уже прошло 10 минут от начала отдыха
    elif not conditioner_status and (current_time - rest_start_time) > (10 * 60):
        print("Прошло 10 минут как кондиционер не работает. Включаем")
        rest_start_time = 0  # Сбросить время начала отдыха
        return False
    
    return None
	
def control_temperature(t):
    global conditioner_status
    if manual_control:
        return

    tz = pytz.timezone('Asia/Tbilisi')
    current_time = datetime.now(tz)
    if 4 <= current_time.hour < 7:
        if conditioner_status:
            print("Время от 3 до 7 утра, выключаю кондиционер")
            ser.write(b'P')  # Выключить кондиционер
            conditioner_status = False
    elif not conditioner_status: # Если текущее время вне диапазона и кондиционер выключен
        print("Время вне диапазона от 3 до 7 утра, включаю кондиционер")
        ser.write(b'P')  # Включить кондиционер
        conditioner_status = True
    #is_rest_need = is_rest_need_func(conditioner_status)
    #if is_rest_need is not None:	
	# Автоматическое выключение кондиционера каждые 6 часов на 10 минут
    #    if conditioner_status and is_rest_need:
    #        print("Кондиционеру нужен отдых. Выключаю")
    #        ser.write(b'P')  # Выключить кондиционер
    #        conditioner_status = False
		
	
     #   if not conditioner_status and not is_rest_need:
     #       print("Кондиционер отдохнул. Включаю")
     #       ser.write(b'P')  # Включить кондиционер
     #       conditioner_status = True
    #else:
    #    pass

	# Контроль температуры
    #elif t > 28 and not conditioner_status:
    #    print("Температура больше 28, включаю кондиционер")
    #    ser.write(b'P')  # Включить кондиционер
    #    conditioner_status = True
    #elif t < 24 and conditioner_status:
    #    print("Температура меньше 24, выключаю кондиционер")
    #    ser.write(b'P')  # Выключить кондиционер
    #    conditioner_status = False

    #print(f"Debug: Состояние кондиционера после управления температурой: {'Включен' if conditioner_status else 'Выключен'}")

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
    control_temperature(t)
    #print(f"Debug: Состояние кондиционера в index: {'Включен' if conditioner_status else 'Выключен'}")
    tz = pytz.timezone('Asia/Tbilisi')
    
    # Получаем текущее время в заданной временной зоне
    current_time = datetime.now(tz)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print("Статус кондиционера index", conditioner_status)
    return render_template_string('''
    <html>
    <head>
        <title>Image Viewer</title>
        <meta http-equiv="refresh" content="5">
    </head>
    <body>
        <img src="/image" width="480" height="720"><br>
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
        ser.write(b'P')
        global conditioner_status
        print("Статус кондиционера control до смены флага", conditioner_status)
        conditioner_status = not conditioner_status
        print("Статус кондиционера control после смены флага", conditioner_status)
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
    manual_control = not manual_control
    return redirect('/')

@app.route('/image')
@login_required
def serve_image():
    return send_from_directory('/home/evgenii/plants_final', 'image.jpg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
