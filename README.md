# RednessBot (v1.15)

## Описание

**RednessBot** - это скрипт на Python, предназначенный для обработки данных телеметрии из CSV файла, экспортируемого из программы [Darknessbot для iOS](https://apps.apple.com/us/app/darknessbot/id1108403878) а так же программы [WheelLog для Android](https://play.google.com/store/apps/details?id=com.cooper.wheellog&hl=en_US) . Скрипт работает через консоль (в будущем планируется создание программу с привычным всем GUI интерфейсом) и позволяет создать видеофайл в формате mp4 с графическим отображением скорости, ШИМ, пробега поездки, мощности, заряда батареи и т.д., а также графиком "Скорость/ШИМ". Видео телеметрии создается с черным фоном в разрешении 4K, и его можно легко наложить на ваше видео заезда на электротранспорте (моноколесо/самокат) в любой монтажной программе, поддерживающей удаление хромокея.

<img width="351" alt="rednes115" src="https://github.com/PavelDemyanov/rednessbot/assets/59764924/f442dfb5-18d4-4c0c-a4cf-0ef4ed292699">
<img width="351" alt="rednes115" src="https://github.com/PavelDemyanov/rednessbot/assets/59764924/b0823420-bfe4-44b8-b7ab-166693992c52">


## Особенности

- **Анализ Даты**: Преобразование строковых представлений дат в объекты datetime для точной работы со временем.
- **Анализ Скорости**: Функция для анализа данных о скорости, категоризирующая скорость и ШИМ  в разные цвета (например, желтый для умеренной скорости, красный для высокой скорости и аналогично для ШИМ белый до 80%, желтый с 80% до 90% и красный при ШИМ выше 90%).

## Установка

Для запуска RednessBot вам необходимо иметь установленный Python на вашей системе вместе со следующими пакетами: `pandas`, `matplotlib`, `moviepy` `psutil`.

### Шаги для использования на WINDOWS:

1. Откройте браузер и перейдите на официальный сайт [Python](python.org)
2. Уставновите Python. В окне установки обязательно поставьте галочку напротив пункта `Add Python to PATH`.
3. Запустите консоль в MAC/Windows
5. Установите необходимые библиотеки: `pip install pandas matplotlib moviepy psutil`.
6. Убедитесь, что Python установлен в вашей системе. `datetime` и `gc` уже включены в стандартную библиотеку Python, поэтому дополнительных действий для их установки не требуется.
7. Запустите скрипт через ту же консоль `python /ВАША-ДИРЕКТОРИЯ/rednessbot.py`
8. Указываем программе директорию, откуда брать CSV, и директория, куда сохранить видеофайл (можно не указывать ничего, если не указано, программа сохранит видео в директорию, где лежит CSV).

### Шаги для использования на MAC/LINUX:

1. Запустите консоль в Mac/Linux
2. Установите ffmpeg `sudo dnf install ffmpeg` (unix) и ImageMagick `sudo apt-get install libmagickwand-dev` (unix) или Homebrew `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)`(mac) `brew install imagemagick` (mac) `brew install ffmpeg`(mac)
3. Установите необходимые библиотеки: `pip install pandas matplotlib moviepy psutil` (если Linux) и `pip3 install pandas matplotlib moviepy psutil` (если Mac)
4. Убедитесь, что Python установлен в вашей системе. `datetime` и `gc` уже включены в стандартную библиотеку Python, поэтому дополнительных действий для их установки не требуется.
5. Запустите скрипт через ту же консоль `python /ВАША-ДИРЕКТОРИЯ/rednessbot3.py ` (если Linux) и `python3 /ВАША-ДИРЕКТОРИЯ/rednessbot.py` (если Mac)
6. Указываем программе директорию, откуда брать CSV, и директория, куда сохранить видеофайл (можно не указывать ничего, если не указано, программа сохранит видео в директорию, где лежит CSV).

## Примеры

**Получаемый файл:**

![Пример видео телеметрии](https://github.com/GreypaX/rednessbot/assets/59764924/75a13390-8800-4021-a849-c534eea564c0)

**Результат после наложения в монтажной программе:**

![Пример наложенного видео](https://github.com/GreypaX/rednessbot/assets/59764924/cd123f7f-281c-48e1-9e50-32cac0102e6f)

**Получаемый файл с примером в динамике:**

![dark20240109_231823 2](https://github.com/GreypaX/rednessbot/assets/59764924/ce9b20ec-840b-4a7d-bf49-7f767e2f8086)

смотреть пример наложения телеметрии [на youtube](https://youtu.be/-AFmMTA96d0)

## Системные требования

- Не менее 8 ГБ оперативной памяти (скоро это значение будет меньше).
- Не менее 35 гб. свободного места на диске.

## Обсуждение

Обсуждение программы и её функционала в [telegram канале @rednessbot_tele](https://t.me/rednessbot_tele)
