#!/bin/bash

# Monitor Control Launcher Script
# Этот скрипт обеспечивает правильную среду для запуска приложения

set -e  # Прерываем выполнение при ошибке

# Переходим в директорию приложения
cd "$(dirname "$0")"

echo "🚀 Запуск Monitor Control..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден!"
    if command -v zenity &> /dev/null; then
        zenity --error --text="Python3 не найден! Установите Python3 для работы приложения."
    fi
    exit 1
fi

echo "✅ Python3 найден: $(python3 --version)"

# Проверяем наличие pip
if ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip не найден!"
    if command -v zenity &> /dev/null; then
        zenity --error --text="pip не найден! Установите python3-pip для работы приложения."
    fi
    exit 1
fi

echo "✅ pip найден: $(python3 -m pip --version)"

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создаем виртуальное окружение..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Не удалось создать виртуальное окружение!"
        if command -v zenity &> /dev/null; then
            zenity --error --text="Не удалось создать виртуальное окружение!\nПроверьте, что установлен python3-venv"
        fi
        exit 1
    fi
    echo "✅ Виртуальное окружение создано"
fi

# Активируем виртуальное окружение
echo "🔄 Активируем виртуальное окружение..."
source venv/bin/activate

# Обновляем pip в виртуальном окружении
echo "🔄 Обновляем pip..."
python -m pip install --upgrade pip wheel setuptools

# Устанавливаем системные зависимости если нужно
echo "🔄 Проверяем системные зависимости..."

# Проверяем наличие requirements.txt и устанавливаем зависимости
if [ -f "requirements.txt" ]; then
    echo "📋 Устанавливаем зависимости Python..."
    
    # Пробуем установить зависимости
    if ! python -m pip install -r requirements.txt; then
        echo "❌ Ошибка установки зависимостей!"
        echo "💡 Попробуйте установить системные пакеты:"
        echo "   sudo apt install python3-pyqt6 python3-pyqt6-dev"
        echo "   или:"
        echo "   sudo dnf install python3-qt6 python3-qt6-devel"
        
        if command -v zenity &> /dev/null; then
            zenity --error --text="Ошибка установки зависимостей!\n\nПопробуйте:\nsudo apt install python3-pyqt6 python3-pyqt6-dev"
        fi
        exit 1
    fi
    
    echo "✅ Зависимости установлены"
else
    echo "⚠️  requirements.txt не найден"
fi

# Проверяем, что все модули импортируются
echo "🔍 Проверяем импорт модулей..."
if ! python -c "import PyQt6.QtWidgets; print('PyQt6 OK')" 2>/dev/null; then
    echo "❌ PyQt6 не может быть импортирован!"
    echo "💡 Попробуйте установить системный пакет:"
    echo "   sudo apt install python3-pyqt6"
    
    if command -v zenity &> /dev/null; then
        zenity --error --text="PyQt6 не найден!\n\nУстановите:\nsudo apt install python3-pyqt6"
    fi
    exit 1
fi

if ! python -c "import monitorcontrol; print('monitorcontrol OK')" 2>/dev/null; then
    echo "❌ monitorcontrol не может быть импортирован!"
    echo "💡 Переустанавливаем monitorcontrol..."
    python -m pip install --force-reinstall monitorcontrol
fi

echo "✅ Все модули импортируются успешно"

# Запускаем приложение
echo "🎯 Запускаем Monitor Control..."
python monitor_control.py

# При ошибке показываем уведомление
if [ $? -ne 0 ]; then
    echo "❌ Ошибка запуска Monitor Control!"
    if command -v zenity &> /dev/null; then
        zenity --error --text="Ошибка запуска Monitor Control!\nПроверьте терминал для подробностей."
    fi
    exit 1
fi
