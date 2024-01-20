import os
import pandas as pd
import matplotlib.pyplot as plt
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, concatenate_videoclips, VideoFileClip, ImageClip
import datetime
import gc
import psutil  # гребаная память кудато утекает и всё крашится, сделаем проверку памяти
import subprocess
import shutil
import platform
import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading
import sys
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tkinter import ttk

# Настройка логирования
logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')



def create_or_clean_hidden_folder():
    logging.info("Начало выполнения функции create_speed_video")
    # Определение пути к скрытой папке в той же директории, что и скрипт
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hidden_folder_path = os.path.join(script_dir, '.redness_temp_files')

    # Проверяем, существует ли папка
    if os.path.exists(hidden_folder_path):
        # Удаляем папку вместе с содержимым
        shutil.rmtree(hidden_folder_path)

    # Создаем папку
    os.makedirs(hidden_folder_path)

    # Для Windows устанавливаем атрибут 'hidden'
    if platform.system() == 'Windows':
        subprocess.call(['attrib', '+H', hidden_folder_path])

    print(f"Создана скрытая папка: {hidden_folder_path}")
    return hidden_folder_path


def check_memory():
    memory = psutil.virtual_memory()
    available_memory = int(memory.available / (1024 * 1024))  # В мегабайтах, округлено до целого числа
    print(f"Доступная память: {available_memory} MB")
    if available_memory < 8 * 1024:  # Порог в 8 ГБ
        print("Предупреждение: низкий уровень доступной памяти!")
        return False
    return True

# Функция для преобразования строки даты в объект datetime
def parse_date(date_str):
    return datetime.datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S.%f')

def get_speed_color(speed):
    if 70 <= speed < 80:
        return 'yellow'
    elif speed >= 80:
        return 'red'
    else:
        return 'white'

def get_pwm_color(pwm):
    if 80 <= pwm < 90:
        return 'yellow'
    elif pwm >= 90:
        return 'red'
    else:
        return 'white'

def update_progress_bar(progress):
    progress_bar["value"] = progress
    app.update_idletasks()  # Обновление GUI


def create_speed_video(csv_file, output_path):
    print("Начало выполнения функции create_speed_video")
    hidden_folder = create_or_clean_hidden_folder()

    # Определение имени файла для сохранения видео
    if not output_path:
        base_dir = os.path.dirname(csv_file)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file_name = f"rednessbot{timestamp}.mp4"
        output_path = os.path.join(base_dir, output_file_name)
    else:
        base_dir, output_file_name = os.path.split(output_path)

    # Определение путей к шрифтам
    font_regular_path = os.path.join(os.path.dirname(__file__), 'fonts', 'sf-ui-display-regular.otf')
    font_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'sf-ui-display-bold.otf')
    
    total_processed = 0  # для инициализации счетчика обработанных записей
    # Чтение данных из файла
    data = pd.read_csv(csv_file, nrows=0)  # Сначала читаем только заголовки

    # Определение типа файла по названиям колонок
    if 'Date' in data.columns and 'Speed' in data.columns:
        file_type = 1
    elif 'date' in data.columns and 'time' in data.columns:
        file_type = 2
    else:
        raise ValueError("Неверный формат файла")

    # Полное чтение файла в зависимости от типа
    if file_type == 1:
        data = pd.read_csv(csv_file)
        data['Date'] = data['Date'].apply(parse_date)
    elif file_type == 2:
        # Чтение файла с разделением даты и времени и последующее объединение
        data = pd.read_csv(csv_file)
        data['Date'] = pd.to_datetime(data['date'] + ' ' + data['time'])
        # Переименовываем остальные колонки, чтобы соответствовали типу 1
        data.rename(columns={'speed': 'Speed', 'pwm': 'PWM', 'voltage': 'Voltage',
                             'power': 'Power', 'battery_level': 'Battery level',
                             'temp2': 'Temperature', 'totaldistance': 'Total mileage',
                             'gps_speed': 'GPS Speed'}, inplace=True)
        
        # Преобразование пробега из метров в километры для файла типа 2
        data['Total mileage'] = data['Total mileage'] / 1000

    data['Duration'] = data['Date'].diff().dt.total_seconds().fillna(0)

    # Установка начального значения пробега
    initial_mileage = data.iloc[0]['Total mileage']

    # Определяем размер части данных для обработки
    chunk_size = 50
    temp_video_files = []

    # Обрабатываем данные частями
    for start in range(0, len(data), chunk_size):
        end = min(start + chunk_size, len(data))
        chunk_data = data[start:end]
        print(f"Обработка чанка данных с {start} по {start + chunk_size}")

        if not check_memory():
            print(f"Прерывание обработки на чанке {start}, недостаточно памяти.")
            break       
        
        # Создание видеоклипов для текущей части
        clips = []
        for index, row in chunk_data.iterrows():
            # Создаем клип графика для текущего кадра
            graph_clip = create_graph(data, row['Date'], row['Duration'])
            # Размещаем клип с графиком в правом нижнем углу экрана
            graph_clip = graph_clip.set_position(('left', 'top'), relative=True)
            # Отступы от краев экрана (10 пикселей)
            graph_clip = graph_clip.margin(left=40, top=50, opacity=0)

            speed = int(row['Speed'])
            pwm = int(row['PWM'])
            speed_color = get_speed_color(speed)
            pwm_color = get_pwm_color(pwm)

            # Расчет текущего пробега относительно начального значения
            current_mileage = round(int(row['Total mileage']) - initial_mileage)

            # Формирование текста с данными
            parameters = [

                ("Напряжение", int(row['Voltage']), "В"),
                ("Мощность", int(row['Power']), "Вт"),
                ("Температура", int(row['Temperature']), "°C"),
                ("Батарея", int(row['Battery level']), "%"),
                ("Пробег", current_mileage, "км"),
                ("ШИМ", pwm, "%"),
                ("GPS", int(row['GPS Speed']), "км/ч") if not pd.isna(row['GPS Speed']) else ("GPS", "", "")


            ]

            # Создаем фоновый клип для этого кадра
            background_clip = ColorClip(size=(3840, 2160), color=(0, 0, 0), duration=row['Duration'])

            # Создаем текстовые клипы для всех элементов, кроме скорости
            text_clips = []
            total_height = sum(78 for _ in parameters)  # Высота каждой строки
            y_start = (576 - total_height) // 2 + 30  # Начальная позиция по Y для центрирования + отступ от верха

            for param_name, param_value, unit in parameters:

                #ЕСЛИ КРАШИТСЯ ПРОГРАММА ВКЛЮЧИ ЭТОТ ЛОГ
                #print(f"Creating TextClip for: {param_name} {param_value} {unit}")

                if param_name == "GPS" and param_value == "":
                    continue  # Пропускаем создание клипов для пустого значения
                    
                # Выбор цвета текста в зависимости от параметра
                text_color = 'white'  # цвет по умолчанию
                if param_name == "ШИМ":
                    text_color = get_pwm_color(param_value)    

                # Создаем отдельные клипы для каждой части параметра
                name_clip = TextClip(param_name, fontsize=70 , color='white', font=font_regular_path)
                value_clip = TextClip(str(param_value), fontsize=85 , color=text_color, font=font_bold_path)  # применение цвета только здесь
                unit_clip = TextClip(unit, fontsize=70 , color='white', font=font_regular_path)

                # Рассчитываем x_position
                x_position = 3840 - name_clip.size[0] - value_clip.size[0] - unit_clip.size[0] - 100 #отступ вторичных показателей от правого края экрана

                # Определяем максимальную высоту среди трех клипов
                max_height = max(name_clip.size[1], value_clip.size[1], unit_clip.size[1])

                # Рассчитываем Y-координату так, чтобы клипы были выровнены по нижнему краю
                name_y = y_start + (max_height - name_clip.size[1]) 
                value_y = y_start + (max_height - value_clip.size[1]) + 4 # Двигаем значение ЦИРФ выше или ниже относительно других чем больше тем оно ниже чем меньше тем выше
                unit_y = y_start + (max_height - unit_clip.size[1])

                # Устанавливаем позиции клипов
                name_clip = name_clip.set_position((x_position, name_y)).set_duration(row['Duration'])
                value_clip = value_clip.set_position((x_position + name_clip.size[0] + 20, value_y)).set_duration(row['Duration'])
                unit_clip = unit_clip.set_position((x_position + name_clip.size[0] + value_clip.size[0] + 40, unit_y)).set_duration(row['Duration'])

                # ЕСЛИ ПРОГРАММА КРАШИТСЯ СНИМИ ЭТИ КОММЕНТАРИИ будет видно почему крашится
                #print(f"Created TextClip for {param_name}. Size: {name_clip.size}")
                #print(f"Created TextClip for {param_value}. Size: {value_clip.size}")
                #print(f"Created TextClip for {unit}. Size: {unit_clip.size}")

                # Добавляем клипы в список
                text_clips.extend([name_clip, value_clip, unit_clip])

                # Увеличиваем y_start для следующего параметра
                y_start += max_height  # Используем max_height для учета выравнивания по нижнему краю

            # Создаем текстовый клип для значения скорости (TextClip1)
            speed_value_clip = TextClip(f"{int(row['Speed'])}", fontsize=210, color=speed_color, font=font_bold_path)
            speed_value_clip = speed_value_clip.set_position(lambda t: ('center', 2160 - speed_value_clip.size[1] - 100)).set_duration(row['Duration'])

            # Создаем текстовый клип для единиц измерения скорости (TextClip2)
            speed_unit_clip = TextClip("км/ч", fontsize=60, color='white', font=font_regular_path)
            speed_unit_clip = speed_unit_clip.set_position(lambda t: ((3840 - speed_unit_clip.size[0]) / 2, speed_value_clip.pos(t)[1] + speed_value_clip.size[1] + -25)).set_duration(row['Duration']) # отступ от нижнего края для скорости КРУПНЫЙ

            # Объединяем фоновый клип с текстовыми клипами и центральным текстовым клипом
            video_clip = CompositeVideoClip([background_clip] + text_clips + [speed_value_clip, speed_unit_clip, graph_clip])
            clips.append(video_clip)

            total_processed += 1
            if total_processed % 10 == 0:  # Изменено с 100 на 10
                print(f"Обработано {total_processed}/{len(data)} записей...")
                progress = (total_processed / len(data)) * 100  # Вычисление прогресса
                app.after(0, lambda: update_progress_bar(progress))  # Обновление прогресс-бара 

        # Сохранение временного видеофайла для текущей части
        temp_output_path = os.path.join(hidden_folder, f"{output_file_name}_part_{start//chunk_size}.mp4")
        concatenate_videoclips(clips, method="compose").write_videofile(temp_output_path, fps=5, bitrate="20000k")
        temp_video_files.append(temp_output_path)
        print(f"Временный видеофайл {temp_output_path} создан.")
        # print(f"output_path: {output_path}") #для отладки
        # Очистка памяти после обработки и сохранения каждого чанка
        gc.collect()


    # Объединение всех временных видеофайлов в один финальный с проверкой гребаной памяти!
    final_clips = [VideoFileClip(file) for file in temp_video_files]

    if check_memory():
        final_clip = concatenate_videoclips(final_clips, method="compose")
        final_clip.write_videofile(output_path, fps=5, codec='libx264', bitrate="20000k")
        print(f"Финальное видео сохранено в {output_path}")
    else:
        print("Прерывание создания финального видео, недостаточно памяти.")

    # Удаление временных видеофайлов
    for file in temp_video_files:
        os.remove(file)
        print(f"Временный файл {file} удален.")
    # Удаление самой скрытой папки
    shutil.rmtree(hidden_folder)
    print(f"Скрытая папка {hidden_folder} удалена.")
    on_thread_complete()
    progress_bar["value"] = 0    
    print("Окончание выполнения функции create_speed_video")

    logging.info("Функция create_speed_video завершила выполнение")

def create_graph(data, current_time, duration):
    # Фильтрация данных за последние 30 секунд
    time_window = datetime.timedelta(seconds=30)
    start_time = current_time - time_window
    filtered_data = data[(data['Date'] >= start_time) & (data['Date'] <= current_time)]

    # Построение графика
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(filtered_data['Date'], filtered_data['Speed'], color='red', label='Скорость', linewidth=7)
    ax.plot(filtered_data['Date'], filtered_data['PWM'], color='blue', label='PWM', linewidth=7)

    # Настройка осей
    ax.set_yticks(ax.get_yticks())  # Оставляем цифры на оси Y
    ax.set_yticklabels([f"{int(y)}" for y in ax.get_yticks()], color='white')  # Форматируем цифры на оси Y в белый цвет

    # Скрываем ось X
    ax.xaxis.set_visible(False)

    # Оставляем видимой ось Y
    ax.yaxis.set_visible(True)

    # Изменение цвета меток оси Y на белый и увеличение их размера, а также увеличение размера делений
    ax.tick_params(axis='y', colors='white', labelsize=25, length=10, width=2)

    # Убираем лишние элементы
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # Скрываем линию оси Y, но оставляем деления и метки видимыми
    ax.spines['left'].set_visible(False)


    # Убираем фон
    ax.set_facecolor('none')
    fig.patch.set_facecolor('none')

    if ax.get_legend():
        ax.get_legend().remove()  # Убираем легенду, если она существует

    plt.tight_layout()

    # Сохранение графика во временный файл изображения
    temp_image_path = 'temp_plot.png'
    plt.savefig(temp_image_path, transparent=True)
    plt.close()

    # Преобразование изображения в клип MoviePy
    graph_clip = ImageClip(temp_image_path).set_duration(duration)
    os.remove(temp_image_path)  # Удаление временного файла

    return graph_clip


class TextRedirector(object):
    def __init__(self, widget, stdout, stderr, max_lines=50):
        self.widget = widget
        self.stdout = stdout
        self.stderr = stderr
        self.max_lines = max_lines

    def write(self, message):
        self.widget.insert(tk.END, message)
        self.widget.see(tk.END)
        
        # Удаление старых строк, если превышен лимит
        lines = self.widget.get(1.0, tk.END).split('\n')
        if len(lines) > self.max_lines:
            self.widget.delete(1.0, 2.0)

        # Печатаем в stdout или stderr в зависимости от типа сообщения
        if 'Traceback' in message or 'Error' in message:
            self.stderr.write(message)
        else:
            self.stdout.write(message)

    def flush(self):
        pass

def redirect_to_textbox(textbox):
    sys.stdout = TextRedirector(textbox, sys.stdout, sys.stderr)
    sys.stderr = sys.stdout  # Перенаправляем stderr в тот же объект, что и stdout



def choose_csv_file():
    filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if filepath:  # Проверяем, был ли выбран файл
        csv_file_path.set(filepath)
        csv_file_entry.delete(0, tk.END)
        csv_file_entry.insert(0, filepath)
        start_button.config(state=tk.NORMAL)  # Активируем кнопку "Начать процесс"
    else:
        start_button.config(state=tk.DISABLED)  # Деактивируем кнопку, если файл не выбран

def choose_output_directory():
    directory = filedialog.askdirectory()
    output_dir_path.set(directory)
    output_dir_entry.delete(0, tk.END)
    output_dir_entry.insert(0, directory)


def start_processing():
    csv_file = csv_file_path.get()
    output_path = determine_output_path(csv_file, output_dir_path.get())

    # Запуск тяжелых вычислений в отдельном потоке
    processing_thread = threading.Thread(target=create_speed_video, args=(csv_file, output_path))
    processing_thread.start()

    # Деактивация кнопок
    choose_csv_button.config(state=tk.DISABLED)
    choose_output_dir_button.config(state=tk.DISABLED)
    start_button.config(state=tk.DISABLED)

    # Ожидание завершения потока и обновление интерфейса
    app.after(100, lambda: check_thread(processing_thread))


def determine_output_path(csv_file, output_dir):
    if not output_dir:
        base_dir = os.path.dirname(csv_file)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file_name = f"rednessbot{timestamp}.mp4"
        return os.path.join(base_dir, output_file_name)
    else:
        # Проверяем, указано ли имя файла в output_dir
        if os.path.splitext(output_dir)[1] == "":
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file_name = f"rednessbot{timestamp}.mp4"
            return os.path.join(output_dir, output_file_name)
        else:
            return output_dir

def check_thread(thread):
    if thread.is_alive():
        app.after(100, lambda: check_thread(thread))
    else:
        on_thread_complete()



def on_thread_complete():
    print("Обработка завершена.")
    # Активация кнопок
    choose_csv_button.config(state=tk.NORMAL)
    choose_output_dir_button.config(state=tk.NORMAL)
    start_button.config(state=tk.NORMAL)
    # Здесь можно добавить код для обновления GUI или уведомления пользователя

if __name__ == "__main__":
    app = tk.Tk()
    app.title("RednessBot 1.1")

    # Установка начального размера окна
    current_width = 800  # Пример текущей ширины
    current_height = 450  # Пример текущей высоты
    new_width = int(current_width * 0.5)  # Уменьшение ширины на 30%
    
    app.geometry(f"{new_width}x{current_height}")  # Установка нового размера окна
    app.resizable(False, True)  # Запрет изменения размера окна

    description_label = tk.Label(app, text="Приложение накладывает телеметрию на ваше видео из файла экспорта DarknessBot и WheelLog, отображая скорость, остальные параметры и график скорость/ШИМ.", wraplength=400)
    description_label.pack(pady=(20, 0))  # 10 пикселей отступа сверху, 0 пикселей снизу

    csv_file_path = tk.StringVar()
    choose_csv_button = tk.Button(app, text="Выбрать CSV файл DarknessBot или WheelLog", command=choose_csv_file)
    choose_csv_button.pack(pady=(20, 0))  # 10 пикселей отступа сверху, 0 пикселей снизу
    csv_file_entry = tk.Entry(app, textvariable=csv_file_path, width=50)
    csv_file_entry.pack()

    output_dir_path = tk.StringVar()
    choose_output_dir_button = tk.Button(app, text="Выбрать директорию для сохранения видео", command=choose_output_directory)
    choose_output_dir_button.pack(pady=(10, 0))  # 10 пикселей отступа сверху, 0 пикселей снизу
    output_dir_entry = tk.Entry(app, textvariable=output_dir_path, width=50)
    output_dir_entry.pack()

    # Создаем фрейм для размещения кнопки
    button_frame = tk.Frame(app, width=200, height=50)  # Задаем размеры в пикселях
    button_frame.pack_propagate(False)  # Отключаем автоматическое изменение размера
    button_frame.pack(pady=(20, 0))  # 10 пикселей отступа сверху, 0 пикселей снизу

    # Создаем кнопку внутри фрейма
    start_button = tk.Button(button_frame, text="Начать процесс", command=start_processing, state=tk.DISABLED)  # Изначально кнопка неактивна
    start_button.pack(fill=tk.BOTH, expand=True)  # Заполняем весь фрейм

    progress_bar = ttk.Progressbar(app, orient="horizontal", length=350, mode="determinate")
    progress_bar.pack(pady=(20, 0))  # 10 пикселей отступа сверху, 0 пикселей снизу

    console_log = scrolledtext.ScrolledText(app, height=10)
    console_log.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=(20, 0))

    redirect_to_textbox(console_log)


    app.mainloop()
