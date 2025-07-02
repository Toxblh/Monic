#!/bin/bash

# Monitor Control Installation Script
# Этот скрипт устанавливает Monitor Control как системное приложение

echo "=== Monitor Control - Установка ==="
echo

# Проверяем права
if [ "$EUID" -eq 0 ]; then
    echo "❌ Не запускайте этот скрипт от root!"
    echo "💡 Запустите как обычный пользователь: ./install.sh"
    exit 1
fi

# Получаем директорию скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/monitor-control"
DESKTOP_FILE="$HOME/.local/share/applications/monitor-control.desktop"

echo "📁 Директория приложения: $SCRIPT_DIR"
echo "📦 Место установки: $APP_DIR"
echo

# Создаем директории если нужно
echo "📁 Создаем необходимые директории..."
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/monitor-control"

# Копируем файлы приложения
echo "📋 Копируем файлы приложения..."
cp "$SCRIPT_DIR/monitor_control.py" "$APP_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$APP_DIR/"
cp "$SCRIPT_DIR/icon.png" "$APP_DIR/"
cp "$SCRIPT_DIR/README.md" "$APP_DIR/" 2>/dev/null || true

# Копируем скрипт запуска
echo "📝 Копируем скрипт запуска..."
cp "$SCRIPT_DIR/run_monitor_control.sh" "$APP_DIR/"
chmod +x "$APP_DIR/run_monitor_control.sh"

# Создаем desktop файл
echo "🖥️  Создаем desktop файл..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Monitor Control
Comment=Управление мониторами с анимацией и автообновлением
Exec=$APP_DIR/run_monitor_control.sh
Icon=$APP_DIR/icon.png
Terminal=false
Categories=System;Settings;
StartupNotify=true
Keywords=monitor;brightness;volume;display;
X-Desktop-File-Install-Version=0.26
EOF

# Делаем desktop файл исполняемым
chmod +x "$DESKTOP_FILE"

# Обновляем базу данных приложений
echo "🔄 Обновляем базу данных приложений..."
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo
echo "✅ Установка завершена!"
echo
echo "📍 Теперь вы можете найти 'Monitor Control' в меню приложений"
echo "🚀 Или запустить напрямую: $APP_DIR/run_monitor_control.sh"
echo
echo "📁 Файлы установлены в: $APP_DIR"
echo "🖥️  Desktop файл: $DESKTOP_FILE"
echo
echo "❌ Для удаления используйте: ./uninstall.sh"
echo
