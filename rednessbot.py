import os
import pandas as pd
import matplotlib.pyplot as plt
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, concatenate_videoclips, VideoFileClip, ImageClip
import datetime
import gc

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

def create_speed_video(csv_file, output_path):
    # Чтение данных из файла
    data = pd.read_csv(csv_file)
    data['Date'] = data['Date'].apply(parse_date)
    data['Duration'] = data['Date'].diff().dt.total_seconds().fillna(0)

    # Установка начального значения пробега
    initial_mileage = data.iloc[0]['Total mileage']

    # Определяем размер части данных для обработки
    chunk_size = 250
    temp_video_files = []

    # Обрабатываем данные частями
    for start in range(0, len(data), chunk_size):
        end = min(start + chunk_size, len(data))
        chunk_data = data[start:end]
        
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
                print(f"Creating TextClip for: {param_name} {param_value} {unit}")

                if param_name == "GPS" and param_value == "":
                    continue  # Пропускаем создание клипов для пустого значения
                    
                # Выбор цвета текста в зависимости от параметра
                text_color = 'white'  # цвет по умолчанию
                if param_name == "ШИМ":
                    text_color = get_pwm_color(param_value)    

                # Создаем отдельные клипы для каждой части параметра
                name_clip = TextClip(param_name, fontsize=70 , color='white', font='SF-UI-Display')
                value_clip = TextClip(str(param_value), fontsize=85 , color=text_color, font='SF-UI-Display-Bold')  # применение цвета только здесь
                unit_clip = TextClip(unit, fontsize=70 , color='white', font='SF-UI-Display')

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

                print(f"Created TextClip for {param_name}. Size: {name_clip.size}")
                print(f"Created TextClip for {param_value}. Size: {value_clip.size}")
                print(f"Created TextClip for {unit}. Size: {unit_clip.size}")

                # Добавляем клипы в список
                text_clips.extend([name_clip, value_clip, unit_clip])

                # Увеличиваем y_start для следующего параметра
                y_start += max_height  # Используем max_height для учета выравнивания по нижнему краю

            # Создаем текстовый клип для значения скорости (TextClip1)
            speed_value_clip = TextClip(f"{int(row['Speed'])}", fontsize=210, color=speed_color, font='SF-UI-Display-Bold')
            speed_value_clip = speed_value_clip.set_position(lambda t: ('center', 2160 - speed_value_clip.size[1] - 100)).set_duration(row['Duration'])

            # Создаем текстовый клип для единиц измерения скорости (TextClip2)
            speed_unit_clip = TextClip("км/ч", fontsize=60, color='white', font='SF-UI-Display')
            speed_unit_clip = speed_unit_clip.set_position(lambda t: ((3840 - speed_unit_clip.size[0]) / 2, speed_value_clip.pos(t)[1] + speed_value_clip.size[1] + -25)).set_duration(row['Duration']) # отступ от нижнего края для скорости КРУПНЫЙ

            # Объединяем фоновый клип с текстовыми клипами и центральным текстовым клипом
            video_clip = CompositeVideoClip([background_clip] + text_clips + [speed_value_clip, speed_unit_clip, graph_clip])
            clips.append(video_clip)

            if index % 100 == 0:
                print(f"Обработано {index + start}/{len(data)} записей...")

        # Сохранение временного видеофайла для текущей части
        temp_output_path = f"{output_path}_part_{start//chunk_size}.mp4"
        concatenate_videoclips(clips, method="compose").write_videofile(temp_output_path, fps=5, bitrate="20000k")
        temp_video_files.append(temp_output_path)
        print(f"Временный видеофайл {temp_output_path} создан.")
        # Очистка памяти после обработки и сохранения каждого чанка
        gc.collect()

    # Объединение всех временных видеофайлов в один финальный
    final_clips = [VideoFileClip(file) for file in temp_video_files]
    final_clip = concatenate_videoclips(final_clips, method="compose")
    final_clip.write_videofile(output_path, fps=5, bitrate="20000k")
    print(f"Финальное видео сохранено в {output_path}")

    # Удаление временных видеофайлов
    for file in temp_video_files:
        os.remove(file)
        print(f"Временный файл {file} удален.")


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




if __name__ == "__main__":
    print("Эта программа создаёт видео телеметрии (в 4K разрешении) из данных CSV файла программы darknessbot.")
    csv_file = input("Пожалуйста, введите путь к вашему CSV файлу: ")
    output_path = input("Введите директорию для сохранения видео (можете не вводить ничего, видео сохранится в директирию к csv файлу): ").strip()

    # Если директория для сохранения не указана, формируем имя файла в текущей директории CSV файла
    if not output_path:
        base_dir = os.path.dirname(csv_file)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(base_dir, f"dark{timestamp}.mp4")

    create_speed_video(csv_file, output_path)

