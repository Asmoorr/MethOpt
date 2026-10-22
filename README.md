<div align="center">

![Синяя волна](https://capsule-render.vercel.app/api?type=waving&color=3B82F6&height=100&section=header)

# 💙 Методы оптимизации

### Лабораторные работы · Артём Трикула

`Алгоритмы на Python` · `Пошаговые решения` · `Визуализация`

От симплекс-таблиц до поиска глобального минимума.<br />
Собственные реализации методов, примеры расчётов и **отчёты по каждой работе**.

![Python](https://img.shields.io/badge/Python-3B82F6?style=for-the-badge&logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-60A5FA?style=for-the-badge&logo=numpy&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-2563EB?style=for-the-badge&logo=scipy&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-93C5FD?style=for-the-badge&logo=poetry&logoColor=1E3A8A)

### 📚 Лабораторные работы

[![Работа 1 — Симплекс-метод](https://img.shields.io/badge/01_·_Симплекс--метод-8B5CF6?style=for-the-badge)](lab01/README.md)
[![Работа 2 — Метод ломаных](https://img.shields.io/badge/02_·_Метод_ломаных-14B8A6?style=for-the-badge)](lab02/README.md)

</div>

| Работа | Задача | Отчёт |
| --- | --- | --- |
| [💜 Симплекс-метод](lab01/README.md) | Линейное программирование, вариант 11. Двухфазный метод и сравнение с SciPy. | [PDF](<lab01/report/Трикула симплекс вариант 11 итоговый.pdf>) |
| [🩵 Метод ломаных](lab02/README.md) | Глобальная минимизация методом Пиявского. Пример на функции Растригина. | [PDF](<lab02/report/Трикула метод ломаных.pdf>) |

### Быстрый старт

Нужны **Python 3.14** и **Poetry**. Установите зависимости из корня репозитория:

```powershell
poetry install
```

**Работа 1:**

```powershell
poetry run python lab01/src/variant11.py
```

**Работа 2:** при первой настройке создайте `.env`, если его ещё нет:

```powershell
Copy-Item lab02/.env.example lab02/.env
```

```powershell
poetry run python lab02/src/main.py
```

Параметры и особенности запуска описаны в README каждой работы.

<div align="center">

<sub>Артём Трикула · Методы оптимизации · МетОпт 1.3</sub>

![Синяя волна](https://capsule-render.vercel.app/api?type=waving&color=3B82F6&height=100&section=footer)

</div>
