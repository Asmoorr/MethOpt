<div align="center">

![Бирюзовая волна](https://capsule-render.vercel.app/api?type=waving&color=14B8A6&height=100&section=header)

# 🩵 Метод ломаных

### Лабораторная работа № 2 · Метод Пиявского

`Глобальный минимум` · `Липшицева функция` · `Ломаная миноранта`

Поиск **глобального минимума** функции одной переменной на отрезке.<br />
Демонстрация на функции **Растригина** с несколькими локальными минимумами.

![Python](https://img.shields.io/badge/Python-14B8A6?style=for-the-badge&logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-2DD4BF?style=for-the-badge&logo=numpy&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-0D9488?style=for-the-badge&logoColor=white)
![Rich](https://img.shields.io/badge/Rich-5EEAD4?style=for-the-badge&logoColor=134E4A)

### 📖 Отчёт

[Описание метода, визуализация и результаты](<report/Трикула метод ломаных.pdf>)

</div>

### Что делает программа

- Один раз оценивает константу Липшица с коэффициентом запаса `1.2`.
- Строит ломаную по пересечениям ветвей и проверяет заданный критерий точности.
- Выводит таблицу шагов, статус, минимум, число итераций и время расчёта.
- Сохраняет графики функции, миноранты и сходимости в `imgs/solution.png`.

### Запуск

Из корня репозитория, с Python 3.14 и Poetry:

```powershell
poetry install
```

При первой настройке, если `lab02/.env` ещё нет:

```powershell
Copy-Item lab02/.env.example lab02/.env
```

Запуск расчёта:

```powershell
poetry run python lab02/src/main.py
```

Функция, границы и точность задаются в `lab02/.env` — ввод в консоли не нужен.
Образец параметров: [.env.example](.env.example). Алгоритм: [piyavsky.py](src/piyavsky.py).

<div align="center">

<sub>Артём Трикула · Методы оптимизации · МетОпт 1.3</sub>

![Бирюзовая волна](https://capsule-render.vercel.app/api?type=waving&color=14B8A6&height=100&section=footer)

</div>
