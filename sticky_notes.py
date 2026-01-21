import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QTextEdit, QVBoxLayout, 
                             QPushButton, QHBoxLayout, QSystemTrayIcon, 
                             QMenu, QAction, QColorDialog, QFontDialog,
                             QCheckBox)
from PyQt5.QtCore import Qt, QPoint, QSettings, QRect, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QColor

# Настройка High DPI должна быть ДО создания QApplication
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

def get_icon_path():
    """Получает путь к иконке"""
    # Пробуем найти иконку рядом с EXE
    if getattr(sys, 'frozen', False):
        # Если запущено как EXE
        base_path = sys._MEIPASS
    else:
        # Если запущено как скрипт
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Пробуем разные пути
    icon_paths = [
        os.path.join(base_path, 'icon.ico'),
        os.path.join(os.getcwd(), 'icon.ico'),
        'icon.ico'
    ]
    
    for path in icon_paths:
        if os.path.exists(path):
            return path
    
    return None

class ResizableStickyNote(QWidget):
    def __init__(self, note_id=1, content="", color="#FFFF99", font_family="Arial", 
                 font_size=10, size=(300, 300), always_on_top=True, pinned_to_screen=False):
        super().__init__()
        self.note_id = note_id
        self.color = color
        self.font_family = font_family
        self.font_size = font_size
        self.init_width, self.init_height = size
        self.always_on_top = always_on_top
        self.pinned_to_screen = pinned_to_screen
        
        # Для управления видимостью кнопок
        self.buttons_visible = False
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hideButtons)
        
        self.initUI()
        self.text_edit.setPlainText(content)
        self.loadSettings()
        
    def initUI(self):
        # Устанавливаем флаги окна
        flags = Qt.FramelessWindowHint
        if self.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Флаг для отслеживания изменения размера
        self.resizing = False
        self.resize_direction = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        
        # Главный виджет с закругленными углами
        self.main_widget = QWidget(self)
        self.main_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.color};
                border-radius: 10px;
                border: 2px solid #CCCCCC;
            }}
        """)
        
        # Текстовое поле
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont(self.font_family, self.font_size))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                padding: 10px;
            }
        """)
        
        # Кнопки управления (изначально скрытые)
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
                opacity: 0;
            }
            QPushButton:hover {
                background-color: #FF6666;
            }
        """)
        self.close_btn.clicked.connect(self.closeNote)
        
        self.color_btn = QPushButton("🎨")
        self.color_btn.setFixedSize(30, 30)
        self.color_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border-radius: 15px;
                font-size: 14px;
                opacity: 0;
            }
            QPushButton:hover {
                background-color: #888888;
            }
        """)
        self.color_btn.clicked.connect(self.changeColor)
        
        self.font_btn = QPushButton("A")
        self.font_btn.setFixedSize(30, 30)
        self.font_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 14px;
                opacity: 0;
            }
            QPushButton:hover {
                background-color: #888888;
            }
        """)
        self.font_btn.clicked.connect(self.changeFont)
        
        self.new_btn = QPushButton("+")
        self.new_btn.setFixedSize(30, 30)
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: #44AA44;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
                opacity: 0;
            }
            QPushButton:hover {
                background-color: #66CC66;
            }
        """)
        self.new_btn.clicked.connect(self.createNewNote)
        
        # Кнопка "Поверх всех окон"
        self.top_btn = QPushButton("📌")
        self.top_btn.setFixedSize(30, 30)
        self.top_btn.setCheckable(True)
        self.top_btn.setChecked(self.always_on_top)
        self.top_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border-radius: 15px;
                font-size: 14px;
                opacity: 0;
            }
            QPushButton:checked {
                background-color: #FFAA00;
                color: black;
            }
            QPushButton:hover {
                background-color: #888888;
            }
            QPushButton:checked:hover {
                background-color: #FFCC00;
            }
        """)
        self.top_btn.clicked.connect(self.toggleAlwaysOnTop)
        
        # Кнопка "Прикрепить к экрану"
        self.pin_btn = QPushButton("📍")
        self.pin_btn.setFixedSize(30, 30)
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(self.pinned_to_screen)
        self.pin_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border-radius: 15px;
                font-size: 14px;
                opacity: 0;
            }
            QPushButton:checked {
                background-color: #00AA00;
                color: white;
            }
            QPushButton:hover {
                background-color: #888888;
            }
            QPushButton:checked:hover {
                background-color: #00CC00;
            }
        """)
        self.pin_btn.clicked.connect(self.togglePinnedToScreen)
        
        # Контейнер для кнопок
        self.buttons_container = QWidget()
        self.buttons_container.setStyleSheet("background: transparent;")
        
        # Панель кнопок (верхняя)
        button_layout = QHBoxLayout(self.buttons_container)
        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.color_btn)
        button_layout.addWidget(self.font_btn)
        button_layout.addWidget(self.top_btn)
        button_layout.addWidget(self.pin_btn)
        button_layout.addWidget(self.close_btn)
        button_layout.setAlignment(Qt.AlignRight)
        button_layout.setContentsMargins(5, 5, 5, 5)
        
        # Основной лэйаут
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.addWidget(self.buttons_container)
        main_layout.addWidget(self.text_edit)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Лэйаут окна
        window_layout = QVBoxLayout(self)
        window_layout.addWidget(self.main_widget)
        window_layout.setContentsMargins(5, 5, 5, 5)
        
        # Позиционируем заметку
        self.setGeometry(100 + (self.note_id - 1) * 20, 100 + (self.note_id - 1) * 20, 
                         self.init_width, self.init_height)
        
        # Для перемещения окна
        self.old_pos = None
        self.dragging = False
        
        # Минимальный размер
        self.setMinimumSize(150, 150)
        
        # Сохраняем изменения
        self.text_edit.textChanged.connect(self.saveNote)
        
        # Таймер для проверки положения прикрепленного стикера
        self.pin_timer = QTimer()
        self.pin_timer.timeout.connect(self.checkPinnedPosition)
        if self.pinned_to_screen:
            self.pin_timer.start(100)
        
        # Получаем информацию о мониторах
        self.updateMonitorInfo()
        
        # Скрываем кнопки через 2 секунды после создания
        QTimer.singleShot(2000, self.hideButtons)
        
    def enterEvent(self, event):
        """При наведении курсора на стикер показываем кнопки"""
        self.showButtons()
        self.hide_timer.stop()
        
    def leaveEvent(self, event):
        """При уходе курсора со стикера скрываем кнопки через 1 секунду"""
        if not self.underMouse():
            self.hide_timer.start(1000)
        
    def showButtons(self):
        """Плавно показываем кнопки"""
        if not self.buttons_visible:
            self.buttons_visible = True
            self.animateButtonsOpacity(0, 1)
                
    def hideButtons(self):
        """Плавно скрываем кнопки"""
        if self.buttons_visible and not self.underMouse():
            self.buttons_visible = False
            self.animateButtonsOpacity(1, 0)
                
    def animateButtonsOpacity(self, start, end):
        """Анимируем изменение прозрачности кнопок"""
        for btn in [self.new_btn, self.color_btn, self.font_btn, self.top_btn, self.pin_btn, self.close_btn]:
            animation = QPropertyAnimation(btn, b"windowOpacity")
            animation.setDuration(200)
            animation.setStartValue(start)
            animation.setEndValue(end)
            animation.setEasingCurve(QEasingCurve.InOutQuad)
            animation.start()
            
    def toggleAlwaysOnTop(self):
        if self.always_on_top:
            self.always_on_top = False
            self.top_btn.setChecked(False)
        else:
            self.always_on_top = True
            self.top_btn.setChecked(True)
            
            if self.pinned_to_screen:
                self.pinned_to_screen = False
                self.pin_btn.setChecked(False)
                self.pin_timer.stop()
                
        self.updateWindowFlagsSilent()
        self.saveSettings()
        
    def togglePinnedToScreen(self):
        if self.pinned_to_screen:
            self.pinned_to_screen = False
            self.pin_btn.setChecked(False)
            self.pin_timer.stop()
        else:
            self.pinned_to_screen = True
            self.pin_btn.setChecked(True)
            
            if self.always_on_top:
                self.always_on_top = False
                self.top_btn.setChecked(False)
                self.updateWindowFlagsSilent()
                
            self.pin_timer.start(100)
            self.pinToCurrentScreen()
            
        self.saveSettings()
        
    def updateWindowFlagsSilent(self):
        """Обновляем флаги окна без пересоздания и скрытия"""
        was_visible = self.isVisible()
        geometry = self.geometry()
        
        flags = Qt.FramelessWindowHint
        if self.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        
        self.hide()
        self.setWindowFlags(flags)
        
        self.setGeometry(geometry)
        if was_visible:
            self.show()
            
    def updateMonitorInfo(self):
        """Получаем информацию о доступных мониторах"""
        try:
            desktop = QApplication.desktop()
            screen_count = desktop.screenCount()
            self.monitors = []
            
            for i in range(screen_count):
                screen_geometry = desktop.screenGeometry(i)
                self.monitors.append({
                    'x': screen_geometry.x(),
                    'y': screen_geometry.y(),
                    'width': screen_geometry.width(),
                    'height': screen_geometry.height(),
                    'right': screen_geometry.x() + screen_geometry.width(),
                    'bottom': screen_geometry.y() + screen_geometry.height()
                })
        except:
            screen = QApplication.primaryScreen().geometry()
            self.monitors = [{
                'x': screen.x(),
                'y': screen.y(),
                'width': screen.width(),
                'height': screen.height(),
                'right': screen.x() + screen.width(),
                'bottom': screen.y() + screen.height()
            }]
            
    def getCurrentScreen(self):
        """Определяем, на каком экране находится центр стикера"""
        if not hasattr(self, 'monitors'):
            self.updateMonitorInfo()
            
        center_x = self.x() + self.width() // 2
        center_y = self.y() + self.height() // 2
        
        for monitor in self.monitors:
            if (monitor['x'] <= center_x <= monitor['right'] and 
                monitor['y'] <= center_y <= monitor['bottom']):
                return monitor
        return self.monitors[0] if self.monitors else None
        
    def pinToCurrentScreen(self):
        """Прикрепляем стикер к текущему экрану"""
        screen = self.getCurrentScreen()
        if not screen:
            return
            
        geom = self.geometry()
        margin = 5
        screen_left = screen['x'] + margin
        screen_top = screen['y'] + margin
        screen_right = screen['right'] - margin - geom.width()
        screen_bottom = screen['bottom'] - margin - geom.height()
        
        new_x = max(screen_left, min(geom.x(), screen_right))
        new_y = max(screen_top, min(geom.y(), screen_bottom))
        
        if new_x != geom.x() or new_y != geom.y():
            self.move(new_x, new_y)
            
    def checkPinnedPosition(self):
        if self.pinned_to_screen:
            self.pinToCurrentScreen()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.showButtons()
            self.hide_timer.stop()
            
            rect = self.rect()
            border_size = 10
            
            if event.x() <= border_size:
                if event.y() <= border_size:
                    self.resize_direction = 'top-left'
                elif event.y() >= rect.height() - border_size:
                    self.resize_direction = 'bottom-left'
                else:
                    self.resize_direction = 'left'
            elif event.x() >= rect.width() - border_size:
                if event.y() <= border_size:
                    self.resize_direction = 'top-right'
                elif event.y() >= rect.height() - border_size:
                    self.resize_direction = 'bottom-right'
                else:
                    self.resize_direction = 'right'
            elif event.y() <= border_size:
                self.resize_direction = 'top'
            elif event.y() >= rect.height() - border_size:
                self.resize_direction = 'bottom'
            else:
                self.dragging = True
                self.old_pos = event.globalPos()
                return
            
            self.resizing = True
            self.resize_start_pos = event.globalPos()
            self.resize_start_geometry = self.geometry()
            
    def mouseMoveEvent(self, event):
        if self.dragging and self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
            self.saveSettings()
            
        elif self.resizing and self.resize_start_pos and self.resize_start_geometry:
            delta = event.globalPos() - self.resize_start_pos
            new_geometry = QRect(self.resize_start_geometry)
            
            if 'left' in self.resize_direction:
                new_geometry.setLeft(new_geometry.left() + delta.x())
                if new_geometry.width() < self.minimumWidth():
                    new_geometry.setLeft(new_geometry.right() - self.minimumWidth())
                    
            if 'right' in self.resize_direction:
                new_geometry.setRight(new_geometry.right() + delta.x())
                if new_geometry.width() < self.minimumWidth():
                    new_geometry.setRight(new_geometry.left() + self.minimumWidth())
                    
            if 'top' in self.resize_direction:
                new_geometry.setTop(new_geometry.top() + delta.y())
                if new_geometry.height() < self.minimumHeight():
                    new_geometry.setTop(new_geometry.bottom() - self.minimumHeight())
                    
            if 'bottom' in self.resize_direction:
                new_geometry.setBottom(new_geometry.bottom() + delta.y())
                if new_geometry.height() < self.minimumHeight():
                    new_geometry.setBottom(new_geometry.top() + self.minimumHeight())
            
            self.setGeometry(new_geometry)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_direction = None
            self.old_pos = None
            self.resize_start_pos = None
            self.resize_start_geometry = None
            self.saveSettings()
            self.hide_timer.start(1000)
            
    def changeColor(self):
        color = QColorDialog.getColor(QColor(self.color), self, "Выберите цвет заметки")
        if color.isValid():
            self.color = color.name()
            self.main_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.color};
                    border-radius: 10px;
                    border: 2px solid #CCCCCC;
                }}
            """)
            self.saveSettings()
            
    def changeFont(self):
        font, ok = QFontDialog.getFont(QFont(self.font_family, self.font_size), self, "Выберите шрифт")
        if ok:
            self.font_family = font.family()
            self.font_size = font.pointSize()
            self.text_edit.setFont(font)
            self.saveSettings()
            
    def createNewNote(self):
        if hasattr(self, 'main_window'):
            self.main_window.createNewNote()
            
    def closeNote(self):
        if hasattr(self, 'main_window'):
            self.main_window.closeNote(self.note_id)
        else:
            self.close()
            
    def saveNote(self):
        if hasattr(self, 'main_window'):
            self.main_window.saveNotes()
            
    def saveSettings(self):
        settings = QSettings("StickyNotes", "NoteSettings")
        settings.setValue(f"note_{self.note_id}_geometry", self.geometry())
        settings.setValue(f"note_{self.note_id}_color", self.color)
        settings.setValue(f"note_{self.note_id}_font_family", self.font_family)
        settings.setValue(f"note_{self.note_id}_font_size", self.font_size)
        settings.setValue(f"note_{self.note_id}_always_on_top", self.always_on_top)
        settings.setValue(f"note_{self.note_id}_pinned_to_screen", self.pinned_to_screen)
        
    def loadSettings(self):
        settings = QSettings("StickyNotes", "NoteSettings")
        geometry = settings.value(f"note_{self.note_id}_geometry")
        if geometry:
            self.setGeometry(geometry)
        color = settings.value(f"note_{self.note_id}_color", self.color)
        if color:
            self.color = color
            self.main_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.color};
                    border-radius: 10px;
                    border: 2px solid #CCCCCC;
                }}
            """)
        font_family = settings.value(f"note_{self.note_id}_font_family", self.font_family)
        font_size = int(settings.value(f"note_{self.note_id}_font_size", self.font_size))
        self.font_family = font_family
        self.font_size = font_size
        self.text_edit.setFont(QFont(font_family, font_size))
        
        self.always_on_top = settings.value(f"note_{self.note_id}_always_on_top", "true").lower() == "true"
        self.pinned_to_screen = settings.value(f"note_{self.note_id}_pinned_to_screen", "false").lower() == "true"
        
        self.top_btn.setChecked(self.always_on_top)
        self.pin_btn.setChecked(self.pinned_to_screen)
        
        if self.pinned_to_screen:
            self.pin_timer.start(100)
            QTimer.singleShot(100, self.pinToCurrentScreen)

class StickyNotesApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("Sticky Notes")
        self.app.setApplicationDisplayName("Стикеры-заметки")
        
        # Устанавливаем иконку приложения
        icon_path = get_icon_path()
        if icon_path and os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            print(f"Иконка загружена: {icon_path}")
        else:
            # Создаем простую иконку если файл не найден
            from PyQt5.QtGui import QPixmap, QPainter
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QColor("#FFFF99"))
            painter.setPen(Qt.black)
            painter.drawRect(10, 10, 44, 44)
            painter.drawText(20, 35, "N")
            painter.end()
            app_icon = QIcon(pixmap)
            print("Используется стандартная иконка")
        
        self.app.setWindowIcon(app_icon)
        
        # Создаем иконку в системном трее
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(app_icon)
        
        # Создаем меню для трея
        tray_menu = QMenu()
        
        new_note_action = QAction("Новая заметка", self.app)
        new_note_action.triggered.connect(self.createNewNote)
        tray_menu.addAction(new_note_action)
        
        show_all_action = QAction("Показать все", self.app)
        show_all_action.triggered.connect(self.showAllNotes)
        tray_menu.addAction(show_all_action)
        
        hide_all_action = QAction("Скрыть все", self.app)
        hide_all_action.triggered.connect(self.hideAllNotes)
        tray_menu.addAction(hide_all_action)
        
        tray_menu.addSeparator()
        
        manage_menu = QMenu("Управление всеми заметками")
        
        toggle_all_top = QAction("Вкл/Выкл 'Поверх всех'", self.app)
        toggle_all_top.triggered.connect(self.toggleAllAlwaysOnTop)
        manage_menu.addAction(toggle_all_top)
        
        toggle_all_pinned = QAction("Вкл/Выкл 'Прикрепленные'", self.app)
        toggle_all_pinned.triggered.connect(self.toggleAllPinned)
        manage_menu.addAction(toggle_all_pinned)
        
        resize_all_small = QAction("Маленькие", self.app)
        resize_all_small.triggered.connect(lambda: self.resizeAllNotes(200, 200))
        manage_menu.addAction(resize_all_small)
        
        resize_all_medium = QAction("Средние", self.app)
        resize_all_medium.triggered.connect(lambda: self.resizeAllNotes(300, 300))
        manage_menu.addAction(resize_all_medium)
        
        resize_all_large = QAction("Большие", self.app)
        resize_all_large.triggered.connect(lambda: self.resizeAllNotes(400, 400))
        manage_menu.addAction(resize_all_large)
        
        tray_menu.addMenu(manage_menu)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("Выход", self.app)
        exit_action.triggered.connect(self.exitApp)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.trayIconActivated)
        
        # Загружаем заметки
        self.notes = {}
        self.loadNotes()
        
        # Если нет заметок, создаем одну
        if not self.notes:
            self.createNewNote()
            
        sys.exit(self.app.exec_())
        
    def createNewNote(self):
        note_id = max(self.notes.keys(), default=0) + 1
        note = ResizableStickyNote(note_id)
        note.main_window = self
        note.show()
        self.notes[note_id] = note
        self.saveNotes()
        
    def showAllNotes(self):
        for note in self.notes.values():
            note.show()
            
    def hideAllNotes(self):
        for note in self.notes.values():
            note.hide()
            
    def toggleAllAlwaysOnTop(self):
        if not self.notes:
            return
            
        first_note = list(self.notes.values())[0]
        new_state = not first_note.always_on_top
        
        for note in self.notes.values():
            note.always_on_top = new_state
            note.top_btn.setChecked(new_state)
            
            if new_state and note.pinned_to_screen:
                note.pinned_to_screen = False
                note.pin_btn.setChecked(False)
                note.pin_timer.stop()
                
            note.updateWindowFlagsSilent()
            note.saveSettings()
            
    def toggleAllPinned(self):
        if not self.notes:
            return
            
        first_note = list(self.notes.values())[0]
        new_state = not first_note.pinned_to_screen
        
        for note in self.notes.values():
            note.pinned_to_screen = new_state
            note.pin_btn.setChecked(new_state)
            
            if new_state and note.always_on_top:
                note.always_on_top = False
                note.top_btn.setChecked(False)
                note.updateWindowFlagsSilent()
                
            if new_state:
                note.pin_timer.start(100)
                note.pinToCurrentScreen()
            else:
                note.pin_timer.stop()
            note.saveSettings()
            
    def resizeAllNotes(self, width, height):
        for note in self.notes.values():
            note.resize(width, height)
            note.saveSettings()
            
    def closeNote(self, note_id):
        if note_id in self.notes:
            note = self.notes.pop(note_id)
            note.hide()
            note.deleteLater()
            self.saveNotes()
            
    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.createNewNote()
            
    def saveNotes(self):
        notes_data = {}
        for note_id, note in self.notes.items():
            notes_data[str(note_id)] = {
                "content": note.text_edit.toPlainText(),
                "color": note.color,
                "font_family": note.font_family,
                "font_size": note.font_size,
                "width": note.width(),
                "height": note.height(),
                "always_on_top": note.always_on_top,
                "pinned_to_screen": note.pinned_to_screen
            }
        
        settings = QSettings("StickyNotes", "Notes")
        settings.setValue("notes", json.dumps(notes_data))
        
    def loadNotes(self):
        settings = QSettings("StickyNotes", "Notes")
        notes_json = settings.value("notes", "{}")
        
        try:
            notes_data = json.loads(notes_json)
            for note_id_str, note_data in notes_data.items():
                note_id = int(note_id_str)
                width = note_data.get("width", 300)
                height = note_data.get("height", 300)
                always_on_top = note_data.get("always_on_top", True)
                pinned_to_screen = note_data.get("pinned_to_screen", False)
                
                note = ResizableStickyNote(
                    note_id,
                    note_data.get("content", ""),
                    note_data.get("color", "#FFFF99"),
                    note_data.get("font_family", "Arial"),
                    note_data.get("font_size", 10),
                    (width, height),
                    always_on_top,
                    pinned_to_screen
                )
                note.main_window = self
                note.show()
                self.notes[note_id] = note
        except Exception as e:
            print(f"Ошибка загрузки заметок: {e}")
            
    def exitApp(self):
        self.saveNotes()
        self.app.quit()

if __name__ == "__main__":
    QApplication.setStyle("Fusion")
    StickyNotesApp()