#!/usr/bin/env python3
"""
Monitor Control
"""

import sys
import os
import traceback
import threading
import time
import json
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QPen, QLinearGradient, QRadialGradient, QColor
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal, QRectF

# Константы анимации
TARGET_ANIMATION_DURATION_MS = 400  # Целевая длительность анимации
ANIMATION_TOLERANCE_MS = 200        # Допустимое отклонение (±200ms)
MIN_ANIMATION_STEPS = 20            # Минимальное количество шагов
MAX_ANIMATION_STEPS = 80            # Максимальное количество шагов
DEFAULT_ANIMATION_STEPS = 40        # Начальное количество шагов
UPDATE_INTERVAL_MS = 10000          # Интервал обновления информации о яркости (10 секунд)

# Путь для сохранения настроек адаптивной анимации
SETTINGS_FILE = os.path.expanduser("~/.monitor_control_settings.json")

def create_monitor_icon():
    """Создает красивую иконку монитора с градиентами"""
    # Создаем pixmap большего размера для лучшего качества
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    # Масштабируем координаты под размер 64x64
    scale = size / 32.0
    
    # === КОРПУС МОНИТОРА ===
    # Создаем градиент для корпуса
    monitor_gradient = QLinearGradient(0, 8*scale, 0, 20*scale)
    monitor_gradient.setColorAt(0.0, QColor(60, 60, 65))      # Темно-серый сверху
    monitor_gradient.setColorAt(0.5, QColor(45, 45, 50))      # Средний серый
    monitor_gradient.setColorAt(1.0, QColor(30, 30, 35))      # Темный снизу
    
    painter.setBrush(QBrush(monitor_gradient))
    painter.setPen(QPen(QColor(20, 20, 25), 1*scale))
    painter.drawRoundedRect(QRectF(4*scale, 4*scale, 24*scale, 16*scale), 3*scale, 3*scale)
    
    # === РАМКА ЭКРАНА ===
    # Внутренняя рамка (светлая)
    frame_gradient = QLinearGradient(0, 6*scale, 0, 18*scale)
    frame_gradient.setColorAt(0.0, QColor(200, 200, 205))     # Светло-серый сверху
    frame_gradient.setColorAt(1.0, QColor(150, 150, 155))     # Темнее снизу
    
    painter.setBrush(QBrush(frame_gradient))
    painter.setPen(QPen(QColor(120, 120, 125), 0.5*scale))
    painter.drawRoundedRect(QRectF(6*scale, 6*scale, 20*scale, 12*scale), 2*scale, 2*scale)
    
    # === ЭКРАН ===
    # Создаем радиальный градиент для экрана (эффект включенного монитора)
    screen_gradient = QRadialGradient(16*scale, 12*scale, 12*scale)
    screen_gradient.setColorAt(0.0, QColor(100, 150, 255))    # Яркий голубой в центре
    screen_gradient.setColorAt(0.6, QColor(30, 100, 200))     # Синий
    screen_gradient.setColorAt(1.0, QColor(10, 50, 120))      # Темно-синий по краям
    
    painter.setBrush(QBrush(screen_gradient))
    painter.setPen(QPen(QColor(5, 25, 60), 0.5*scale))
    painter.drawRoundedRect(QRectF(8*scale, 8*scale, 16*scale, 8*scale), 1*scale, 1*scale)
    
    # === БЛИК НА ЭКРАНЕ ===
    # Добавляем реалистичный блик
    highlight_gradient = QLinearGradient(9*scale, 8.5*scale, 12*scale, 11*scale)
    highlight_gradient.setColorAt(0.0, QColor(255, 255, 255, 80))  # Полупрозрачный белый
    highlight_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))   # Прозрачный
    
    painter.setBrush(QBrush(highlight_gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(9*scale, 8.5*scale, 6*scale, 3*scale), 0.5*scale, 0.5*scale)
    
    # === ПОДСТАВКА ===
    # Стойка монитора
    stand_gradient = QLinearGradient(0, 20*scale, 0, 24*scale)
    stand_gradient.setColorAt(0.0, QColor(70, 70, 75))
    stand_gradient.setColorAt(1.0, QColor(40, 40, 45))
    
    painter.setBrush(QBrush(stand_gradient))
    painter.setPen(QPen(QColor(25, 25, 30), 0.5*scale))
    painter.drawRoundedRect(QRectF(14*scale, 20*scale, 4*scale, 4*scale), 1*scale, 1*scale)
    
    # Основание подставки
    base_gradient = QLinearGradient(0, 24*scale, 0, 27*scale)
    base_gradient.setColorAt(0.0, QColor(60, 60, 65))
    base_gradient.setColorAt(1.0, QColor(35, 35, 40))
    
    painter.setBrush(QBrush(base_gradient))
    painter.setPen(QPen(QColor(20, 20, 25), 0.5*scale))
    painter.drawRoundedRect(QRectF(10*scale, 24*scale, 12*scale, 3*scale), 1.5*scale, 1.5*scale)
    
    # === ИНДИКАТОР ПИТАНИЯ ===
    # Маленький светодиод питания
    power_gradient = QRadialGradient(26*scale, 18*scale, 1*scale)
    power_gradient.setColorAt(0.0, QColor(0, 255, 100))       # Яркий зеленый
    power_gradient.setColorAt(1.0, QColor(0, 150, 50))        # Темнее зеленый
    
    painter.setBrush(QBrush(power_gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(25.5*scale, 17.5*scale, 1*scale, 1*scale))
    
    painter.end()
    
    # Масштабируем до нужного размера для system tray (обычно 16x16 или 22x22)
    final_size = 32
    scaled_pixmap = pixmap.scaled(final_size, final_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    return QIcon(scaled_pixmap)

def create_dynamic_monitor_icon(brightness_level=None):
    """Создает иконку монитора с индикатором яркости"""
    # Создаем базовую иконку
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    scale = size / 32.0
    
    # === КОРПУС МОНИТОРА ===
    monitor_gradient = QLinearGradient(0, 8*scale, 0, 20*scale)
    monitor_gradient.setColorAt(0.0, QColor(60, 60, 65))
    monitor_gradient.setColorAt(0.5, QColor(45, 45, 50))
    monitor_gradient.setColorAt(1.0, QColor(30, 30, 35))
    
    painter.setBrush(QBrush(monitor_gradient))
    painter.setPen(QPen(QColor(20, 20, 25), 1*scale))
    painter.drawRoundedRect(QRectF(4*scale, 4*scale, 24*scale, 16*scale), 3*scale, 3*scale)
    
    # === РАМКА ЭКРАНА ===
    frame_gradient = QLinearGradient(0, 6*scale, 0, 18*scale)
    frame_gradient.setColorAt(0.0, QColor(200, 200, 205))
    frame_gradient.setColorAt(1.0, QColor(150, 150, 155))
    
    painter.setBrush(QBrush(frame_gradient))
    painter.setPen(QPen(QColor(120, 120, 125), 0.5*scale))
    painter.drawRoundedRect(QRectF(6*scale, 6*scale, 20*scale, 12*scale), 2*scale, 2*scale)
    
    # === ЭКРАН С ДИНАМИЧЕСКОЙ ЯРКОСТЬЮ ===
    if brightness_level is not None:
        # Цвет экрана зависит от уровня яркости
        intensity = brightness_level / 100.0
        screen_color = QColor(
            int(10 + 90 * intensity),    # Красный: от 10 до 100
            int(50 + 100 * intensity),   # Зеленый: от 50 до 150
            int(120 + 135 * intensity)   # Синий: от 120 до 255
        )
        
        screen_gradient = QRadialGradient(16*scale, 12*scale, 12*scale)
        screen_gradient.setColorAt(0.0, screen_color.lighter(150))
        screen_gradient.setColorAt(0.6, screen_color)
        screen_gradient.setColorAt(1.0, screen_color.darker(200))
    else:
        # Стандартный синий экран
        screen_gradient = QRadialGradient(16*scale, 12*scale, 12*scale)
        screen_gradient.setColorAt(0.0, QColor(100, 150, 255))
        screen_gradient.setColorAt(0.6, QColor(30, 100, 200))
        screen_gradient.setColorAt(1.0, QColor(10, 50, 120))
    
    painter.setBrush(QBrush(screen_gradient))
    painter.setPen(QPen(QColor(5, 25, 60), 0.5*scale))
    painter.drawRoundedRect(QRectF(8*scale, 8*scale, 16*scale, 8*scale), 1*scale, 1*scale)
    
    # === БЛИК НА ЭКРАНЕ ===
    if brightness_level is None or brightness_level > 20:
        highlight_alpha = 80 if brightness_level is None else min(80, int(brightness_level * 0.8))
        highlight_gradient = QLinearGradient(9*scale, 8.5*scale, 12*scale, 11*scale)
        highlight_gradient.setColorAt(0.0, QColor(255, 255, 255, highlight_alpha))
        highlight_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(highlight_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(9*scale, 8.5*scale, 6*scale, 3*scale), 0.5*scale, 0.5*scale)
    
    # === ИНДИКАТОР ЯРКОСТИ ===
    if brightness_level is not None:
        # Индикатор сбоку от монитора
        indicator_height = 10 * scale
        indicator_width = 2 * scale
        
        # Фон индикатора
        painter.setBrush(QBrush(QColor(40, 40, 45)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(29*scale, 8*scale, indicator_width, indicator_height), 1*scale, 1*scale)
        
        # Заполнение индикатора
        fill_height = (brightness_level / 100.0) * indicator_height
        fill_y = 8*scale + indicator_height - fill_height
        
        # Цвет зависит от уровня яркости
        if brightness_level < 30:
            fill_color = QColor(255, 100, 100)  # Красный (низкая яркость)
        elif brightness_level < 70:
            fill_color = QColor(255, 200, 100)  # Желтый (средняя яркость)
        else:
            fill_color = QColor(100, 255, 100)  # Зеленый (высокая яркость)
        
        painter.setBrush(QBrush(fill_color))
        painter.drawRoundedRect(QRectF(29*scale, fill_y, indicator_width, fill_height), 1*scale, 1*scale)
    
    # === ПОДСТАВКА ===
    stand_gradient = QLinearGradient(0, 20*scale, 0, 24*scale)
    stand_gradient.setColorAt(0.0, QColor(70, 70, 75))
    stand_gradient.setColorAt(1.0, QColor(40, 40, 45))
    
    painter.setBrush(QBrush(stand_gradient))
    painter.setPen(QPen(QColor(25, 25, 30), 0.5*scale))
    painter.drawRoundedRect(QRectF(14*scale, 20*scale, 4*scale, 4*scale), 1*scale, 1*scale)
    
    # Основание подставки
    base_gradient = QLinearGradient(0, 24*scale, 0, 27*scale)
    base_gradient.setColorAt(0.0, QColor(60, 60, 65))
    base_gradient.setColorAt(1.0, QColor(35, 35, 40))
    
    painter.setBrush(QBrush(base_gradient))
    painter.setPen(QPen(QColor(20, 20, 25), 0.5*scale))
    painter.drawRoundedRect(QRectF(10*scale, 24*scale, 12*scale, 3*scale), 1.5*scale, 1.5*scale)
    
    # === ИНДИКАТОР ПИТАНИЯ ===
    power_gradient = QRadialGradient(26*scale, 18*scale, 1*scale)
    if brightness_level is not None and brightness_level == 0:
        # Красный индикатор когда экран выключен
        power_gradient.setColorAt(0.0, QColor(255, 50, 50))
        power_gradient.setColorAt(1.0, QColor(150, 25, 25))
    else:
        # Зеленый индикатор когда экран включен
        power_gradient.setColorAt(0.0, QColor(0, 255, 100))
        power_gradient.setColorAt(1.0, QColor(0, 150, 50))
    
    painter.setBrush(QBrush(power_gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(25.5*scale, 17.5*scale, 1*scale, 1*scale))
    
    painter.end()
    
    # Масштабируем до нужного размера
    final_size = 32
    scaled_pixmap = pixmap.scaled(final_size, final_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    return QIcon(scaled_pixmap)

class UIUpdater(QObject):
    """Класс для безопасного обновления UI из других потоков"""
    update_display = pyqtSignal()
    update_icon = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._do_update)
        self.pending_update = False
        
    def request_update(self):
        """Запрашивает обновление с дебаунсингом"""
        if not self.pending_update:
            self.pending_update = True
            self.update_timer.start(500)  # Обновление через 500ms
            
    def _do_update(self):
        """Выполняет фактическое обновление"""
        self.pending_update = False
        self.update_display.emit()
    
class BrightnessAnimator:
    """Класс для плавной анимации изменения яркости с адаптивным timing'ом"""
    
    def __init__(self, monitor, monitor_name: str, ui_updater=None):
        self.monitor = monitor
        self.monitor_name = monitor_name
        self.current_value = 50
        self.target_value = 50
        self.is_animating = False
        self.lock = threading.Lock()
        self.ui_updater = ui_updater  # Объект для отправки сигналов
        
        # Адаптивные параметры анимации
        self.optimal_steps = DEFAULT_ANIMATION_STEPS
        self.performance_history = []  # История производительности
        self.last_step_duration_ms = 10  # Средняя длительность одного шага в мс
        
        # Загружаем сохраненные настройки
        self._load_settings()
        
    def _load_settings(self):
        """Загружает сохраненные настройки производительности"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    monitor_settings = settings.get(self.monitor_name, {})
                    if monitor_settings:
                        self.optimal_steps = monitor_settings.get('optimal_steps', DEFAULT_ANIMATION_STEPS)
                        self.performance_history = monitor_settings.get('performance_history', [])[:3]  # Берем только последние 3
                        print(f"📂 Загружены настройки для {self.monitor_name}: {self.optimal_steps} шагов, история: {self.performance_history}")
        except Exception as e:
            print(f"⚠️  Ошибка загрузки настроек: {e}")
            
    def _save_settings(self):
        """Сохраняет текущие настройки производительности"""
        try:
            settings = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
            
            settings[self.monitor_name] = {
                'optimal_steps': self.optimal_steps,
                'performance_history': self.performance_history[-3:]  # Сохраняем только последние 3
            }
            
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            print(f"💾 Настройки сохранены для {self.monitor_name}")
        except Exception as e:
            print(f"⚠️  Ошибка сохранения настроек: {e}")
        
    def _calculate_optimal_steps(self, distance):
        """Вычисляет оптимальное количество шагов на основе истории производительности"""
        if len(self.performance_history) < 2:
            print(f"📈 Недостаточно данных для адаптации, используем {self.optimal_steps} шагов")
            return self.optimal_steps
        
        # Берем среднее время за последние 3 анимации
        recent_times = self.performance_history[-3:]
        avg_duration = sum(recent_times) / len(recent_times)
        
        print(f"📊 Анализ производительности: среднее время {avg_duration:.1f}ms, цель {TARGET_ANIMATION_DURATION_MS}ms")
        
        # Если анимация слишком медленная, уменьшаем количество шагов
        if avg_duration > TARGET_ANIMATION_DURATION_MS + ANIMATION_TOLERANCE_MS:
            new_steps = max(MIN_ANIMATION_STEPS, int(self.optimal_steps * 0.75))
            print(f"⚡ Уменьшаем шаги: {self.optimal_steps} → {new_steps} (медленно: {avg_duration:.1f}ms > {TARGET_ANIMATION_DURATION_MS + ANIMATION_TOLERANCE_MS}ms)")
            self.optimal_steps = new_steps
            self._save_settings()  # Сохраняем изменения
        # Если анимация слишком быстрая, увеличиваем количество шагов
        elif avg_duration < TARGET_ANIMATION_DURATION_MS - ANIMATION_TOLERANCE_MS:
            new_steps = min(MAX_ANIMATION_STEPS, int(self.optimal_steps * 1.25))
            print(f"⚡ Увеличиваем шаги: {self.optimal_steps} → {new_steps} (быстро: {avg_duration:.1f}ms < {TARGET_ANIMATION_DURATION_MS - ANIMATION_TOLERANCE_MS}ms)")
            self.optimal_steps = new_steps
            self._save_settings()  # Сохраняем изменения
        else:
            print(f"✅ Производительность в норме: {avg_duration:.1f}ms, оставляем {self.optimal_steps} шагов")
        
        return self.optimal_steps
        
    def set_target(self, value: int):
        """Устанавливает новое целевое значение яркости"""
        with self.lock:
            self.target_value = value
            print(f"🎯 Цель яркости для {self.monitor_name}: {value}%")
            
            if not self.is_animating:
                try:
                    with self.monitor:
                        current_brightness = self.monitor.get_luminance()
                        if current_brightness is not None:
                            self.current_value = current_brightness
                            print(f"📊 Текущая яркость: {self.current_value}%")
                        else:
                            print(f"⚠️  Яркость не получена (None), используем значение по умолчанию: {self.current_value}%")
                except Exception as e:
                    print(f"⚠️  Ошибка получения яркости: {e}")
                    self.current_value = 50
                
                self.is_animating = True
                thread = threading.Thread(target=self._animate)
                thread.daemon = True
                thread.start()
    
    def _animate(self):
        """Основной цикл анимации с адаптивным timing'ом"""
        import time as time_module
        
        animation_start_time = time_module.time()
        print(f"🎬 Начинаем анимацию для {self.monitor_name}")
        
        # Запоминаем начальное значение и вычисляем общее расстояние
        start_value = self.current_value
        
        # Проверяем, что start_value не None
        if start_value is None:
            print(f"⚠️  Начальное значение яркости None, используем 50%")
            start_value = 50
            self.current_value = 50
        
        total_distance = abs(self.target_value - start_value)
        
        # Если расстояние 0, то анимация не нужна
        if total_distance == 0:
            self.is_animating = False
            print(f"✅ Анимация не требуется: уже {self.current_value}%")
            return
        
        # Вычисляем оптимальное количество шагов
        animation_steps = self._calculate_optimal_steps(total_distance)
        step_delay_ms = TARGET_ANIMATION_DURATION_MS / animation_steps
        
        print(f"📏 Расстояние анимации: {start_value}% → {self.target_value}% (Δ={total_distance})")
        print(f"⚡ Адаптивные параметры: {animation_steps} шагов по {step_delay_ms:.1f}ms")
        print(f"🎯 Целевая длительность: {TARGET_ANIMATION_DURATION_MS}ms (±{ANIMATION_TOLERANCE_MS}ms)")
        
        step_count = 0
        while self.is_animating and step_count < animation_steps:
            with self.lock:
                step_count += 1
                
                # Вычисляем прогресс от 0.0 до 1.0
                progress = step_count / animation_steps
                
                # Интерполируем между начальным и целевым значением
                interpolated_value = start_value + (self.target_value - start_value) * progress
                self.current_value = round(interpolated_value)
                
                # На последнем шаге точно устанавливаем целевое значение
                if step_count >= animation_steps:
                    self.current_value = self.target_value
                    self.is_animating = False
                    
                    animation_end_time = time_module.time()
                    actual_duration = (animation_end_time - animation_start_time) * 1000
                    
                    # Сохраняем результат в историю производительности
                    self.performance_history.append(actual_duration)
                    if len(self.performance_history) > 5:  # Храним только последние 5 результатов
                        self.performance_history.pop(0)
                    
                    # Сохраняем настройки после каждой анимации
                    self._save_settings()
                    
                    print(f"✅ Анимация завершена: {self.current_value}% за {actual_duration:.1f}ms")
                    print(f"📊 История производительности: {[f'{t:.0f}ms' for t in self.performance_history[-3:]]}")
                    
                    if self.ui_updater:
                        self.ui_updater.request_update()
                
                try:
                    # Проверяем, что current_value не None перед установкой
                    if self.current_value is None:
                        print(f"⚠️  current_value is None, устанавливаем значение по умолчанию")
                        self.current_value = self.target_value
                    
                    with self.monitor:
                        self.monitor.set_luminance(self.current_value)
                        print(f"🔆 Яркость установлена: {self.current_value}% (шаг {step_count}/{animation_steps})")
                        
                        # Обновляем иконку каждые несколько шагов или на последнем шаге
                        if self.ui_updater and (step_count % max(1, animation_steps // 5) == 0 or step_count >= animation_steps):
                            self.ui_updater.update_icon.emit(self.current_value)
                        
                except Exception as e:
                    print(f"❌ Ошибка установки яркости: {e}")
                    self.is_animating = False
                    break
                    
            # Если анимация ещё продолжается, ждём до следующего шага
            if self.is_animating:
                time.sleep(step_delay_ms / 1000.0)

def scan_monitors():
    """Сканирует мониторы (импорт ВНУТРИ функции)"""
    try:
        print("Импортируем monitorcontrol...")
        import monitorcontrol
        print("✅ monitorcontrol импортирован")
        
        print("Сканируем мониторы...")
        monitors = monitorcontrol.get_monitors()
        print(f"✅ Найдено мониторов: {len(monitors)}")
        return monitors
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()
        return []

# Глобальные переменные для управления мониторами
animators = []
update_timer = None
tray_icon_global = None
monitors_global = []
ui_updater_global = None
g_menu_items = {} # Глобальный словарь для хранения элементов меню

def refresh_monitors(tray_icon):
    """Обновляет список мониторов"""
    print("🔄 Обновление мониторов...")
    # TODO: Реализовать обновление списка мониторов
    print("✅ Мониторы обновлены")

def update_brightness_display():
    """Обновляет отображение текущей яркости в меню (только текст)"""
    global monitors_global, g_menu_items, animators
    
    # Не обновляем меню, если идет анимация, чтобы избежать гонки состояний
    if any(anim.is_animating for anim in animators):
        print("🔄 Пропускаем обновление меню, идет анимация.")
        return
        
    if not tray_icon_global or not monitors_global:
        return
        
    print("🔄 Обновляем отображение яркости в меню...")
    
    # Получаем среднюю яркость всех мониторов для иконки
    total_brightness = 0
    monitor_count = 0
    
    for monitor in monitors_global:
        try:
            with monitor:
                brightness = monitor.get_luminance()
                if brightness is not None:
                    total_brightness += brightness
                    monitor_count += 1
        except Exception:
            pass
    
    # Обновляем иконку со средней яркостью
    if monitor_count > 0:
        avg_brightness = total_brightness // monitor_count
        update_tray_icon_brightness(avg_brightness)
    
    # Обновляем текст существующих элементов меню
    for i, monitor in enumerate(monitors_global):
        monitor_key = f"monitor_{i}"
        if monitor_key not in g_menu_items:
            continue

        try:
            # Получаем актуальные данные
            with monitor:
                current_brightness = monitor.get_luminance()
                if current_brightness is None:
                    current_brightness = "?"
            
            current_input, _, model_name = get_monitor_capabilities(monitor, i)
            monitor_name = model_name if model_name else f"Монитор {i + 1}"
            
            # Обновляем заголовок
            header_action = g_menu_items[monitor_key].get("header")
            if header_action:
                header_action.setText(f"📺 {monitor_name} (🔆 {current_brightness}%)")
            
            # Обновляем информацию о входе
            input_info_action = g_menu_items[monitor_key].get("input_info")
            if input_info_action:
                if current_input is not None:
                    input_info_action.setText(f"   🔌 Текущий: {get_input_name(current_input)}")
                    input_info_action.setVisible(True)
                else:
                    input_info_action.setVisible(False)
            
            # Обновляем маркеры текущего входа
            input_actions = g_menu_items[monitor_key].get("inputs", {})
            for code, action in input_actions.items():
                input_name = get_input_name(code)
                current_marker = " ◀" if code == current_input else ""
                action.setText(f"     ▸ {input_name}{current_marker}")

        except Exception as e:
            print(f"❌ Ошибка обновления меню для монитора {i + 1}: {e}")
            header_action = g_menu_items[monitor_key].get("header")
            if header_action:
                header_action.setText(f"❌ Монитор {i + 1}: Ошибка")

def get_monitor_capabilities(monitor, monitor_index):
    """Получает возможности монитора, включая доступные входы и модель"""
    try:
        with monitor:
            # Получаем текущий источник входа
            try:
                current_input = monitor.get_input_source()
                print(f"📍 Монитор {monitor_index + 1} - текущий вход: {current_input}")
            except Exception:
                current_input = None
                
            # Получаем возможности монитора включая модель
            try:
                capabilities = monitor.get_vcp_capabilities()
                available_inputs = []
                model_name = None
                
                if capabilities:
                    # Получаем доступные входы
                    if 'inputs' in capabilities:
                        available_inputs = capabilities['inputs']
                        print(f"📋 Монитор {monitor_index + 1} - доступные входы: {available_inputs}")
                    
                    # Получаем название модели
                    if 'model' in capabilities:
                        model_name = capabilities['model']
                        print(f"📺 Монитор {monitor_index + 1} - модель: {model_name}")
                
                if not available_inputs:
                    # Стандартные входы если не удалось получить
                    available_inputs = [15, 17, 18]  # DP1, HDMI1, HDMI2
                    print(f"📋 Монитор {monitor_index + 1} - используем стандартные входы")
            except Exception:
                available_inputs = [15, 17, 18]  # DP1, HDMI1, HDMI2
                model_name = None
                print(f"📋 Монитор {monitor_index + 1} - ошибка получения входов, используем стандартные")
                
        return current_input, available_inputs, model_name
    except Exception as e:
        print(f"❌ Ошибка получения возможностей монитора {monitor_index + 1}: {e}")
        return None, [15, 17, 18], None

def get_input_name(input_code):
    """Возвращает название входа по коду"""
    input_names = {
        15: "DP-1",
        17: "HDMI-1", 
        18: "HDMI-2",
        25: "Type-C"  # Некоторые мониторы используют этот код для USB-C
    }
    return input_names.get(input_code, f"Вход {input_code}")

def create_monitor_menus(menu, monitors):
    """Создает плоскую структуру меню для мониторов и сохраняет ссылки на элементы"""
    global animators, ui_updater_global, g_menu_items
    
    if monitors:
        for i, monitor in enumerate(monitors):
            monitor_key = f"monitor_{i}"
            g_menu_items[monitor_key] = {}
            
            try:
                # Получаем текущую яркость
                try:
                    with monitor:
                        current_brightness = monitor.get_luminance()
                        if current_brightness is None:
                            current_brightness = 50
                except Exception:
                    current_brightness = 50
                
                # Получаем возможности монитора
                current_input, available_inputs, model_name = get_monitor_capabilities(monitor, i)
                
                # Формируем название монитора
                monitor_name = model_name if model_name else f"Монитор {i + 1}"
                
                # Заголовок монитора с текущей яркостью
                monitor_header = menu.addAction(f"📺 {monitor_name} (🔆 {current_brightness}%)")
                monitor_header.setEnabled(False)
                g_menu_items[monitor_key]["header"] = monitor_header
                
                # Показать текущий вход если известен
                input_info = menu.addAction(f"   🔌 Текущий: {get_input_name(current_input)}")
                input_info.setEnabled(False)
                g_menu_items[monitor_key]["input_info"] = input_info
                if current_input is None:
                    input_info.setVisible(False)
                
                # Inline кнопки яркости с эмодзи
                brightness_emojis = ["🌑", "🌘", "🌗", "🌖", "🌕"]
                brightness_values = [0, 25, 50, 75, 100]
                for j, (emoji, brightness) in enumerate(zip(brightness_emojis, brightness_values)):
                    action = menu.addAction(f"   {emoji} {brightness}%")
                    action.triggered.connect(lambda checked, mon=monitor, val=brightness, idx=i: set_monitor_brightness(mon, val, idx))
                
                # Inline кнопки громкости
                volume_emojis = ["🔇", "🔈", "🔉", "🔊"]
                volume_values = [0, 25, 50, 100]
                for j, (emoji, volume) in enumerate(zip(volume_emojis, volume_values)):
                    action = menu.addAction(f"   {emoji} Громкость {volume}%")
                    action.triggered.connect(lambda checked, mon=monitor, val=volume, idx=i: set_monitor_volume(mon, val, idx))
                
                # Доступные источники входа
                if available_inputs:
                    menu.addAction("   🔌 Источники входа:").setEnabled(False)
                    g_menu_items[monitor_key]["inputs"] = {}
                    for input_code in available_inputs:
                        input_name = get_input_name(input_code)
                        current_marker = " ◀" if input_code == current_input else ""
                        action = menu.addAction(f"     ▸ {input_name}{current_marker}")
                        action.triggered.connect(lambda checked, mon=monitor, code=input_code, idx=i: set_monitor_input(mon, code, idx))
                        g_menu_items[monitor_key]["inputs"][input_code] = action
                
                # Разделитель между мониторами
                if i < len(monitors) - 1:
                    menu.addSeparator()
                    
                # Создаем аниматор для этого монитора
                if i >= len(animators):
                    # Используем более точное имя для сохранения настроек
                    animator_name = model_name if model_name else f"Монитор {i + 1}"
                    animator = BrightnessAnimator(
                        monitor, 
                        animator_name,
                        ui_updater_global
                    )
                    animators.append(animator)
                    
            except Exception as e:
                print(f"Ошибка создания меню для монитора {i + 1}: {e}")
                error_action = menu.addAction(f"❌ Монитор {i + 1}: Ошибка")
                error_action.setEnabled(False)
    else:
        no_monitors_action = menu.addAction("❌ Мониторы не найдены")
        no_monitors_action.setEnabled(False)
        
        help_action = menu.addAction("💡 Включите DDC/CI в настройках монитора")
        help_action.setEnabled(False)

def set_monitor_brightness(monitor, brightness, monitor_index):
    """Устанавливает яркость монитора с анимацией"""
    global animators
    
    print(f"🎛️  Brightness change requested: {brightness}% for Monitor {monitor_index + 1}")
    
    # Используем аниматор если он существует
    if monitor_index < len(animators) and animators[monitor_index]:
        animators[monitor_index].set_target(brightness)
    else:
        # Если аниматора нет, устанавливаем напрямую
        try:
            print(f"🔧 Setting brightness directly to {brightness}% for Monitor {monitor_index + 1}...")
            with monitor:
                monitor.set_luminance(brightness)
            print(f"✅ Brightness set to {brightness}% for Monitor {monitor_index + 1}")
            
            # Обновляем иконку в system tray
            update_tray_icon_brightness(brightness)
            
        except Exception as e:
            print(f"❌ Error setting brightness for Monitor {monitor_index + 1}: {e}")

def set_monitor_volume(monitor, volume, monitor_index):
    """Устанавливает громкость монитора"""
    try:
        print(f"🔧 Setting volume to {volume}% for Monitor {monitor_index + 1}...")
        with monitor:
            monitor.vcp.set_vcp_feature(0x62, volume)
        print(f"✅ Volume set to {volume}% for Monitor {monitor_index + 1}")
    except Exception as e:
        print(f"❌ Error setting volume for Monitor {monitor_index + 1}: {e}")

def set_monitor_input(monitor, input_code, monitor_index):
    """Устанавливает источник входа монитора"""
    global ui_updater_global
    try:
        input_name = get_input_name(input_code)
        print(f"🔧 Переключаем на {input_name} для Монитора {monitor_index + 1}...")
        with monitor:
            monitor.set_input_source(input_code)
        print(f"✅ Источник переключен на {input_name} для Монитора {monitor_index + 1}")
        # Обновляем меню после переключения с дебаунсингом
        if ui_updater_global:
            ui_updater_global.request_update()
    except Exception as e:
        print(f"❌ Ошибка переключения источника для Монитора {monitor_index + 1}: {e}")

def update_tray_icon_brightness(brightness=None):
    """Обновляет иконку в system tray с текущим уровнем яркости"""
    global tray_icon_global
    
    if tray_icon_global:
        try:
            new_icon = create_dynamic_monitor_icon(brightness)
            tray_icon_global.setIcon(new_icon)
            
            # Обновляем tooltip с информацией о яркости
            if brightness is not None:
                tooltip = f"Monitor Control - Яркость: {brightness}%"
            else:
                tooltip = "Monitor Control - С анимацией и автообновлением"
            tray_icon_global.setToolTip(tooltip)
            
        except Exception as e:
            print(f"⚠️  Ошибка обновления иконки: {e}")

def main():
    """Основная функция"""
    global tray_icon_global, monitors_global, update_timer, ui_updater_global
    
    print("=== Monitor Control - Основная версия ===")
    print()
    
    # Шаг 1: Проверяем GUI
    print("1. Проверяем GUI окружение...")
    if not os.environ.get('DISPLAY'):
        print("❌ Ошибка: DISPLAY не установлен")
        return 1
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Создаем UI updater для безопасного обновления из потоков
    ui_updater_global = UIUpdater()
    ui_updater_global.update_display.connect(update_brightness_display)
    ui_updater_global.update_icon.connect(update_tray_icon_brightness)
    
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("❌ Ошибка: System tray недоступен")
        return 1
    
    print("✅ GUI окружение готово")
    
    # Шаг 2: Сканирование мониторов (импорт ВНУТРИ функции)
    print("2. Сканируем мониторы...")
    monitors = scan_monitors()
    monitors_global = monitors
    print()
    
    # Шаг 3: Создание system tray и МЕНЮ (ОДИН РАЗ)
    print("3. Создаем system tray и меню...")
    tray_icon = QSystemTrayIcon(create_monitor_icon(), app)
    tray_icon.setToolTip("Monitor Control - С анимацией и автообновлением")
    tray_icon_global = tray_icon
    
    # Создаем меню ОДИН РАЗ
    menu = QMenu()
    menu.setStyleSheet("""
        QMenu {
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
            border-radius: 6px;
            padding: 5px;
        }
        QMenu::item {
            padding: 5px 10px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: #3498db;
            color: white;
        }
    """)
    
    # Заполняем меню и сохраняем ссылки на его элементы
    create_monitor_menus(menu, monitors)
    
    # Служебные функции
    menu.addSeparator()
    
    refresh_action = menu.addAction("🔄 Обновить мониторы")
    refresh_action.triggered.connect(lambda: refresh_monitors(tray_icon))
    
    quit_action = menu.addAction("❌ Выход")
    quit_action.triggered.connect(app.quit)
    
    tray_icon.setContextMenu(menu)
    tray_icon.show()
    
    # Шаг 4: Настройка автоматического обновления
    print("4. Настраиваем автоматическое обновление...")
    update_timer = QTimer()
    update_timer.timeout.connect(update_brightness_display)
    update_timer.start(UPDATE_INTERVAL_MS)
    print(f"✅ Автообновление настроено (каждые {UPDATE_INTERVAL_MS/1000} секунд)")
    
    print("✅ System tray создан и отображен")
    
    print()
    print("✅ Приложение запущено успешно!")
    print("📍 Проверьте системный трей для управления мониторами")
    print("🎬 Включена адаптивная анимация изменения яркости")
    print(f"🎯 Целевое время анимации: {TARGET_ANIMATION_DURATION_MS}ms ±{ANIMATION_TOLERANCE_MS}ms")
    print(f"⚙️  Диапазон шагов: {MIN_ANIMATION_STEPS}-{MAX_ANIMATION_STEPS} (начальное: {DEFAULT_ANIMATION_STEPS})")
    print("🔄 Включено автоматическое обновление меню")
    print("🛑 Для выхода используйте меню в трее или нажмите Ctrl+C")
    print()
    
    try:
        return app.exec()
    except KeyboardInterrupt:
        print("\n🛑 Прерывание пользователем")
        return 0
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
