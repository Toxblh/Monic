#!/bin/bash

# Monitor Control Uninstall Script
# Этот скрипт удаляет Monitor Control из системы

echo "=== Monitor Control - Удаление ==="
echo

# Проверяем права
if [ "$EUID" -eq 0 ]; then
    echo "❌ Не запускайте этот скрипт от root!"
    echo "💡 Запустите как обычный пользователь: ./uninstall.sh"
    exit 1
fi

APP_DIR="$HOME/.local/share/monitor-control"
DESKTOP_FILE="$HOME/.local/share/applications/monitor-control.desktop"

echo "📁 Директория приложения: $APP_DIR"
echo "🖥️  Desktop файл: $DESKTOP_FILE"
echo

# Спрашиваем подтверждение
read -p "❓ Вы уверены, что хотите удалить Monitor Control? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Удаление отменено"
    exit 0
fi

echo "🗑️  Удаляем файлы..."

# Удаляем директорию приложения
if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
    echo "✅ Удалена директория: $APP_DIR"
else
    echo "ℹ️  Директория не найдена: $APP_DIR"
fi

# Удаляем desktop файл
if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    echo "✅ Удален desktop файл: $DESKTOP_FILE"
else
    echo "ℹ️  Desktop файл не найден: $DESKTOP_FILE"
fi

# Обновляем базу данных приложений
echo "🔄 Обновляем базу данных приложений..."
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo
echo "✅ Monitor Control успешно удален!"
echo "📍 Приложение больше не будет отображаться в меню"
echo
