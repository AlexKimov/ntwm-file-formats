# Описание  
Форматы файлов и инструменты для игры Nosferatu Wrath of Malachi (2003). Описание форматов в виде шаблонов для 16ричного редактора.  

## Краткое введение в форматы файлов  

#### Игровые ресурсы  
Основные игровые файлы находятся в архиве .csa. Сжатие в архиве не используется.

#### Форматы для моделей и текстур  
Модели строений, персонажей, монстров хранятся в файлах .anb и .fxm. Первые хранят вершинную анимацию, вторые данные для скелетной анимации, сами анимации ждя .fxm моделей находятся в файлах .mot. Для текстур используются .jpg, .tga.  

## Вопросы/Ответы  
0. Как распаковать и запаковать архивы игры .csa?  
  Использовать скрипт для Quickbms ([ссылка](#quickBms)). Только распаковка.  
1. Как достать модели из игры Nosferatu Wrath of Malachi?   
  Распаковать архив игры. Для моделей использовать плагины для Noesis ([ссылка](#noesis)).  

## Форматы  

Nosferatu Wrath of Malachi (2003) / Вампиры (2003)

| №   | Формат | Прогресс | Шаблон (010 Editor) | Описание |
| :-- | :-------- | :------ | :------- | :--   |
| 1   | .anb | 90% |  [ANB.bt](templates/ANB.bt)  | Строения, объекты, модели с вершинной анимацией |
| 2   | .fxm | 90% |  [FXM.bt](templates/FXM.bt)  | Модели |
| 3   | .fxm | 90% |  [FFXM(keypose).bt](templates/FXM(keypose).bt)  | Модели (слово keypose в названии) |
| 4   |  .mot | 90% |  [MOT.bt](templates/MOT.bt)  | Анимации для fxm моделей |
| 5   |  .csa | 90% |  [CSA.bt](templates/CSA.bt)  | Файл ресурсов игры |

    Для чего нужны шаблоны
    Отображение структуры файла в удобном для изучения и редактирования виде, другими словами - описание формата файла.

    Как использовать шаблоны 010Editor
    0. Установить 010Editor.
    1. Открыть нужный файл игры.
    2. Применить шаблон через меню Templates-Run template.   

## Инструменты

### QuickBms
| №	| Скрипт	| Описание| 
| :-- | :-------- | :------ |
| 1	| [unpack_csa.bms](scripts/qbms/unpack_csa.bms)| Распаковка архивов игры  |

    Как использовать quickbms скрипты
    1. Нужен quickbms https://aluigi.altervista.org/quickbms.htm
    2. Для запуска в репозитории лежит bat файл с настройками, нужно открыть его и задать свои пути: до места, где находится quickbms, папки с игрой и места куда нужно сохранить результат.
    3. Запустить процесс через bat файл или вручную (задав свои параметры для запуска quickbms, документация на английском есть здесь https://aluigi.altervista.org/papers/quickbms.txt ). 

### noesis
| №	| Плагин	| Описание	| 
| :-- | :-------- | :------ |
| 1 | [fmt_ntwm_anb.py](plugins/noesis/fmt_ntwm_anb.py) |  Просмотр .anb файлов  |
| 2 | [fmt_ntwm_fxm.py](plugins/noesis/fmt_ntwm_fxm.py) |  Просмотр .fxm файлов  |

    Как использовать Noesis плагины
    1. Скачать и распаковать Noesis https://richwhitehouse.com/index.php?content=inc_projects.php&showproject=91 .
    2. Скопировать нужный вам скрипт в папку ПапкасNoesis/plugins/python.
    3. Запустить Noesis.
    4. Открыть файл через File-Open.
    5. В случае плагина для моделей на экране отобразиться модель, если используется плагин для распаковки архивов, то вы увидите меню с выбором параметров распаковки.
    6. Если файл с нужным вам расширением отсутствует в меню, то или вы поместили файл плагина в другую папку или произошла ошибка при загрузке плагина.

---

# About
Nosferatu The Wrath of Malachi file formats.

#### Links
https://github.com/MeinerI/Nosferatu-The-Wrath-of-Malachi - almost everything is based on this repository.

### Templates
| №   | Format/Ext | Progress | Template (010 Editor) | Description |
| :-- | :-------- | :------ | :------- | :--   |
| 1   | .anb | 90% |  [ANB.bt](templates/ANB.bt)  | 3d Objects, buildings, enemies with morphing animation |
| 2   | .fxm | 90% |  [FXM.bt](templates/FXM.bt)  | Characters, enemies |
| 3   | .fxm | 90% |  [FFXM(keypose).bt](https://github.com/AlexKimov/ntwm-file-formats/blob/master/templates/FXM(keypose).bt)  | Characters, enemies (files named "keypose") |
| 4   |  .mot | 90% |  [MOT.bt](templates/MOT.bt)  | motions (skeletal animation)  |
| 5   |  .csa | 90% |  [CSA.bt](templates/CSA.bt)  | motions (skeletal animation)  |

### Plugins
[Noesis](https://richwhitehouse.com/index.php?content=inc_projects.php) python scripts 
* [fmt_ntwm_anb.py](https://github.com/AlexKimov/ntwm-file-formats/blob/master/plugins/noesis/fmt_ntwm_anb.py) - open .anb files
* [fmt_ntwm_fxm.py](https://github.com/AlexKimov/ntwm-file-formats/blob/master/plugins/noesis/fmt_ntwm_fxm.py) - open .fxm files
