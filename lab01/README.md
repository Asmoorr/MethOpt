<div align="center">

![Фиолетовая волна](https://capsule-render.vercel.app/api?type=waving&color=8B5CF6&height=100&section=header)

# 💜 Симплекс-метод

### Лабораторная работа № 1 · Вариант 11

`Линейное программирование` · `Две фазы` · `Симплекс-таблицы`

Собственная реализация **двухфазного симплекс-метода** на Python.<br />
Пошаговое решение задачи и сравнение результата с **SciPy**.

![Python](https://img.shields.io/badge/Python-8B5CF6?style=for-the-badge&logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-A78BFA?style=for-the-badge&logo=numpy&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-7C3AED?style=for-the-badge&logo=scipy&logoColor=white)
![Rich](https://img.shields.io/badge/Rich-C4B5FD?style=for-the-badge&logoColor=white)

### 📖 Отчёт

[Постановка задачи, ход решения и результаты](<report/Трикула симплекс вариант 11 итоговый.pdf>)

</div>

### Что делает программа

- Приводит задачу к канонической форме и находит начальный допустимый базис.
- Выполняет симплекс-итерации и показывает таблицы в консоли.
- Выводит найденное решение и сравнивает его с `scipy.optimize.linprog`.

### Запуск

Из корня репозитория, с Python 3.14 и Poetry:

```powershell
poetry install
poetry run python lab01/src/variant11.py
```

Условия варианта заданы в [сценарии запуска](src/variant11.py), алгоритм — в [simplex.py](src/simplex.py).

<div align="center">

<sub>Артём Трикула · Методы оптимизации · МетОпт 1.3</sub>

![Фиолетовая волна](https://capsule-render.vercel.app/api?type=waving&color=8B5CF6&height=100&section=footer)

</div>
