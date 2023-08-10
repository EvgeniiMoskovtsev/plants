from flask import Flask, render_template_string, send_from_directory, redirect, request
import serial
import time
import pytz
from datetime import datetime

conditioner_status = False 
is_rest_need = False
six_hours = 6 * 60 * 60 # 6 hours

rest_start_time = 0
rest_time = 60 * 10 # 10 min
last_turn_off_time = time.time() 


app = Flask(__name__)

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
def read_sensor_data():
	line = ser.readline()   # читайте строку из последовательного порта
	decoded_line = line.decode('utf-8').strip()
	t, h = map(float, decoded_line.split(',')) # Предположим, что температура и влажность разделены запятой
	print(f"Debug: Температура = {t} °C, Влажность = {h} %") # Отладочная информация
	return t, h
	
def is_rest_need_func(conditioner_status):
    global last_turn_off_time
    global rest_start_time
    global six_hours
    current_time = time.time()
    
    # Если кондиционер включен и пришло время для отдыха
    if conditioner_status and current_time - last_turn_off_time > six_hours:
        last_turn_off_time = current_time
        rest_start_time = current_time  # Записываем время начала отдыха
        return True
    
    # Если кондиционер выключен, но уже прошло 10 минут от начала отдыха
    elif not conditioner_status and (current_time - rest_start_time) > (10 * 60):
        rest_start_time = 0  # Сбросить время начала отдыха
        return False
    
    return False
	
def control_temperature(t):
	global conditioner_status
	
	is_rest_need = is_rest_need_func(conditioner_status)
	
	# Автоматическое выключение кондиционера каждые 6 часов на 10 минут
	if conditioner_status and is_rest_need:
		ser.write(b'P')  # Выключить кондиционер
		conditioner_status = False
		
	
	if not conditioner_status and not is_rest_need:
		ser.write(b'P')  # Включить кондиционер
		conditioner_status = True

	# Контроль температуры
	elif t > 28 and not conditioner_status:
		ser.write(b'P')  # Включить кондиционер
		conditioner_status = True
	elif t < 24 and conditioner_status:
		ser.write(b'P')  # Выключить кондиционер
		conditioner_status = False


@app.route('/')
def index():
    global conditioner_status
    t, h = read_sensor_data()
    control_temperature(t)

    tz = pytz.timezone('Asia/Tbilisi')

    # Получаем текущее время в заданной временной зоне
    current_time = datetime.now(tz)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

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
        <button onclick="location.href='/control?cmd=power'">Включить/Выключить</button>
        <button onclick="location.href='/control?cmd=up'">Повысить температуру</button>
        <button onclick="location.href='/control?cmd=down'">Понизить температуру</button>
        <button onclick="location.href='/control?cmd=fan'">Изменить скорость</button>
    </body>
    </html>
    ''', formatted_time=formatted_time, t=t, h=h, conditioner_status=conditioner_status)

@app.route('/control')
def control():
    cmd = request.args.get('cmd')
    if cmd == 'power':
        ser.write(b'P')
        global conditioner_status
        conditioner_status = not conditioner_status
    elif cmd == 'up':
        ser.write(b'I')
    elif cmd == 'down':
        ser.write(b'D')
    elif cmd == 'fan':
        ser.write(b'S')

	# Вернуться обратно на главную страницу
    return redirect('/')

@app.route('/image')
def serve_image():
    return send_from_directory('/home/evgenii/plants_final', 'image.jpg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
