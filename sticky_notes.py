import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QTextEdit, QVBoxLayout, 
                             QPushButton, QHBoxLayout, QSystemTrayIcon, 
                             QMenu, QAction, QColorDialog, QFontDialog,
                             QCheckBox, QDialog, QLabel, QDialogButtonBox,
                             QVBoxLayout as QVBoxLayout2, QMessageBox, QFrame,
                             QGraphicsDropShadowEffect, QSlider, QGroupBox,
                             QTabWidget, QGridLayout)
from PyQt5.QtCore import Qt, QPoint, QSettings, QRect, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap, QPainter
import requests
import webbrowser
from update_manager import UpdateManager
from packaging import version
from datetime import datetime

# Настройка High DPI должна быть ДО создания QApplication
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

def get_icon_path():
    """Получает путь к иконке"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    icon_paths = [
        os.path.join(base_path, 'icon.ico'),
        os.path.join(os.getcwd(), 'icon.ico'),
        'icon.ico'
    ]
    
    for path in icon_paths:
        if os.path.exists(path):
            return path
    
    return None

class UpdateDialog(QDialog):
    """Диалоговое окно обновления"""
    def __init__(self, update_info, current_version, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.current_version = current_version
        self.setWindowTitle("Доступно обновление!")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout2(self)
        
        title = QLabel(f"Доступна новая версия: {self.update_info.get('version')}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0066CC;")
        layout.addWidget(title)
        
        current_version = QLabel(f"Текущая версия: {self.current_version}")
        current_version.setStyleSheet("color: #666666;")
        layout.addWidget(current_version)
        
        if 'changelog' in self.update_info:
            changelog_label = QLabel("Что нового:")
            changelog_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(changelog_label)
            
            changelog_text = QLabel(self.update_info['changelog'])
            changelog_text.setWordWrap(True)
            changelog_text.setStyleSheet("""
                QLabel {
                    background-color: #F5F5F5;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #DDDDDD;
                }
            """)
            layout.addWidget(changelog_text)
        
        button_box = QDialogButtonBox()
        
        self.update_btn = QPushButton("Обновить")
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.update_btn.clicked.connect(self.updateClicked)
        
        self.later_btn = QPushButton("Напомнить позже")
        self.later_btn.clicked.connect(self.laterClicked)
        
        self.skip_btn = QPushButton("Пропустить эту версию")
        self.skip_btn.clicked.connect(self.skipClicked)
        
        button_box.addButton(self.update_btn, QDialogButtonBox.AcceptRole)
        button_box.addButton(self.later_btn, QDialogButtonBox.RejectRole)
        button_box.addButton(self.skip_btn, QDialogButtonBox.DestructiveRole)
        
        layout.addWidget(button_box)
        
        self.dont_show_again = QCheckBox("Больше не показывать обновления для этой версии")
        layout.addWidget(self.dont_show_again)
        
    def updateClicked(self):
        webbrowser.open(self.update_info.get('download_url', 'https://github.com/DaniiL-Buzakov/Stikers/releases'))
        if self.dont_show_again.isChecked():
            settings = QSettings("StickyNotes", "Updates")
            settings.setValue(f"skip_version_{self.update_info.get('version')}", True)
        self.accept()
        
    def laterClicked(self):
        if self.dont_show_again.isChecked():
            settings = QSettings("StickyNotes", "Updates")
            settings.setValue(f"skip_version_{self.update_info.get('version')}", True)
        self.reject()
        
    def skipClicked(self):
        settings = QSettings("StickyNotes", "Updates")
        settings.setValue(f"skip_version_{self.update_info.get('version')}", True)
        self.reject()

class ColorGradientDialog(QDialog):
    """Диалог для выбора цвета или градиента"""
    def __init__(self, current_color="#FFFF99", gradient_color1=None, gradient_color2=None, parent=None):
        super().__init__(parent)
        self.current_color = current_color
        self.gradient_color1 = gradient_color1 or current_color
        self.gradient_color2 = gradient_color2 or self.lighten_color(current_color, 20)
        self.result_type = "solid"  # "solid" или "gradient"
        self.result_color = current_color
        self.result_gradient1 = self.gradient_color1
        self.result_gradient2 = self.gradient_color2
        
        self.setWindowTitle("Цвет и градиент")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout2(self)
        
        # Вкладки для выбора типа
        self.tab_widget = QTabWidget()
        
        # Вкладка "Сплошной цвет"
        solid_tab = QWidget()
        solid_layout = QVBoxLayout2(solid_tab)
        
        self.solid_color_btn = QPushButton("Выбрать цвет")
        self.solid_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color};
                color: {'black' if self.is_light_color(self.current_color) else 'white'};
                border: 2px solid #666666;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 80px;
            }}
            QPushButton:hover {{
                border: 2px solid #000000;
            }}
        """)
        self.solid_color_btn.clicked.connect(self.chooseSolidColor)
        solid_layout.addWidget(self.solid_color_btn)
        
        solid_layout.addStretch()
        self.tab_widget.addTab(solid_tab, "Сплошной цвет")
        
        # Вкладка "Градиент"
        gradient_tab = QWidget()
        gradient_layout = QVBoxLayout2(gradient_tab)
        
        # Превью градиента
        self.gradient_preview = QFrame()
        self.gradient_preview.setMinimumHeight(80)
        self.gradient_preview.setStyleSheet(f"""
            QFrame {{
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.gradient_color1}, 
                    stop:1 {self.gradient_color2});
            }}
        """)
        gradient_layout.addWidget(self.gradient_preview)
        
        # Кнопки выбора цветов градиента
        colors_layout = QHBoxLayout()
        
        self.gradient_color1_btn = QPushButton("Первый цвет")
        self.gradient_color1_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.gradient_color1};
                color: {'black' if self.is_light_color(self.gradient_color1) else 'white'};
                border: 2px solid #666666;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid #000000;
            }}
        """)
        self.gradient_color1_btn.clicked.connect(lambda: self.chooseGradientColor(1))
        colors_layout.addWidget(self.gradient_color1_btn)
        
        self.gradient_color2_btn = QPushButton("Второй цвет")
        self.gradient_color2_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.gradient_color2};
                color: {'black' if self.is_light_color(self.gradient_color2) else 'white'};
                border: 2px solid #666666;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid #000000;
            }}
        """)
        self.gradient_color2_btn.clicked.connect(lambda: self.chooseGradientColor(2))
        colors_layout.addWidget(self.gradient_color2_btn)
        
        gradient_layout.addLayout(colors_layout)
        
        gradient_layout.addStretch()
        self.tab_widget.addTab(gradient_tab, "Градиент")
        
        layout.addWidget(self.tab_widget)
        
        # Кнопки OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def is_light_color(self, hex_color):
        """Определяет, светлый ли цвет для выбора цвета текста"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness > 128
        
    def lighten_color(self, hex_color, percent):
        """Осветляет цвет на заданный процент"""
        hex_color = hex_color.lstrip('#')
        r = min(255, int(int(hex_color[0:2], 16) * (1 + percent/100)))
        g = min(255, int(int(hex_color[2:4], 16) * (1 + percent/100)))
        b = min(255, int(int(hex_color[4:6], 16) * (1 + percent/100)))
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def chooseSolidColor(self):
        """Выбор сплошного цвета"""
        color = QColorDialog.getColor(QColor(self.current_color), self, "Выберите цвет")
        if color.isValid():
            self.current_color = color.name()
            self.solid_color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.current_color};
                    color: {'black' if self.is_light_color(self.current_color) else 'white'};
                    border: 2px solid #666666;
                    padding: 15px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    min-height: 80px;
                }}
                QPushButton:hover {{
                    border: 2px solid #000000;
                }}
            """)
            
    def chooseGradientColor(self, color_num):
        """Выбор цвета градиента"""
        if color_num == 1:
            current_color = self.gradient_color1
        else:
            current_color = self.gradient_color2
            
        color = QColorDialog.getColor(QColor(current_color), self, "Выберите цвет")
        if color.isValid():
            if color_num == 1:
                self.gradient_color1 = color.name()
                self.gradient_color1_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.gradient_color1};
                        color: {'black' if self.is_light_color(self.gradient_color1) else 'white'};
                        border: 2px solid #666666;
                        padding: 10px;
                        border-radius: 5px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        border: 2px solid #000000;
                    }}
                """)
            else:
                self.gradient_color2 = color.name()
                self.gradient_color2_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.gradient_color2};
                        color: {'black' if self.is_light_color(self.gradient_color2) else 'white'};
                        border: 2px solid #666666;
                        padding: 10px;
                        border-radius: 5px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        border: 2px solid #000000;
                    }}
                """)
            
            # Обновляем превью
            self.gradient_preview.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid #CCCCCC;
                    border-radius: 8px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.gradient_color1}, 
                        stop:1 {self.gradient_color2});
                }}
            """)
    
    def accept(self):
        """Сохраняем результаты"""
        if self.tab_widget.currentIndex() == 0:  # Сплошной цвет
            self.result_type = "solid"
            self.result_color = self.current_color
        else:  # Градиент
            self.result_type = "gradient"
            self.result_gradient1 = self.gradient_color1
            self.result_gradient2 = self.gradient_color2
        
        super().accept()

class FontTextColorDialog(QDialog):
    """Диалог для выбора шрифта и цвета текста"""
    def __init__(self, current_font_family="Arial", current_font_size=10, 
                 current_text_color="#000000", parent=None):
        super().__init__(parent)
        self.font_family = current_font_family
        self.font_size = current_font_size
        self.text_color = current_text_color
        
        self.setWindowTitle("Шрифт и цвет текста")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout2(self)
        
        # Группа для настроек шрифта
        font_group = QGroupBox("Настройки шрифта")
        font_layout = QGridLayout()
        
        # Кнопка выбора шрифта
        self.font_btn = QPushButton("Выбрать шрифт")
        self.font_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #888888;
            }
        """)
        self.font_btn.clicked.connect(self.chooseFont)
        font_layout.addWidget(self.font_btn, 0, 0, 1, 2)
        
        # Превью шрифта
        self.font_preview = QLabel(f"{self.font_family}, {self.font_size}pt")
        self.font_preview.setStyleSheet(f"""
            QLabel {{
                font-family: '{self.font_family}';
                font-size: {self.font_size}pt;
                padding: 10px;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                background-color: #F5F5F5;
            }}
        """)
        self.font_preview.setMinimumHeight(60)
        font_layout.addWidget(self.font_preview, 1, 0, 1, 2)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Группа для цвета текста
        color_group = QGroupBox("Цвет текста")
        color_layout = QVBoxLayout2()
        
        # Кнопка выбора цвета текста
        self.text_color_btn = QPushButton("Выбрать цвет текста")
        self.text_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.text_color};
                color: {'black' if self.is_light_color(self.text_color) else 'white'};
                border: 2px solid #666666;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                min-height: 80px;
            }}
            QPushButton:hover {{
                border: 2px solid #000000;
            }}
        """)
        self.text_color_btn.clicked.connect(self.chooseTextColor)
        color_layout.addWidget(self.text_color_btn)
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        layout.addStretch()
        
        # Кнопки OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def is_light_color(self, hex_color):
        """Определяет, светлый ли цвет для выбора цвета текста"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness > 128
        
    def chooseFont(self):
        """Выбор шрифта"""
        font, ok = QFontDialog.getFont(QFont(self.font_family, self.font_size), self, "Выберите шрифт")
        if ok:
            self.font_family = font.family()
            self.font_size = font.pointSize()
            self.font_preview.setText(f"{self.font_family}, {self.font_size}pt")
            self.font_preview.setStyleSheet(f"""
                QLabel {{
                    font-family: '{self.font_family}';
                    font-size: {self.font_size}pt;
                    padding: 10px;
                    border: 1px solid #CCCCCC;
                    border-radius: 5px;
                    background-color: #F5F5F5;
                }}
            """)
            
    def chooseTextColor(self):
        """Выбор цвета текста"""
        color = QColorDialog.getColor(QColor(self.text_color), self, "Выберите цвет текста")
        if color.isValid():
            self.text_color = color.name()
            self.text_color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.text_color};
                    color: {'black' if self.is_light_color(self.text_color) else 'white'};
                    border: 2px solid #666666;
                    padding: 15px;
                    border-radius: 8px;
                    font-weight: bold;
                    min-height: 80px;
                }}
                QPushButton:hover {{
                    border: 2px solid #000000;
                }}
            """)

class SettingsPopup(QWidget):
    """Всплывающее окно с настройками"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_note = parent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid #CCCCCC;
                border-radius: 8px;
            }
        """)
        
        # Тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Кнопка "Новая заметка"
        self.new_btn = QPushButton("+ Новая заметка")
        self.new_btn.setFixedHeight(32)
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: #44AA44;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                text-align: left;
                padding-left: 10px;
            }
            QPushButton:hover {
                background-color: #66CC66;
            }
        """)
        self.new_btn.clicked.connect(self.parent_note.createNewNote)
        layout.addWidget(self.new_btn)
        
        # Кнопка "Цвет и градиент"
        self.color_gradient_btn = QPushButton("🎨🌈 Цвет и градиент")
        self.color_gradient_btn.setFixedHeight(32)
        self.color_gradient_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border-radius: 6px;
                text-align: left;
                padding-left: 10px;
            }
            QPushButton:hover {
                background-color: #888888;
            }
        """)
        self.color_gradient_btn.clicked.connect(self.parent_note.openColorGradientDialog)
        layout.addWidget(self.color_gradient_btn)
        
        # Кнопка "Шрифт и цвет текста"
        self.font_textcolor_btn = QPushButton("A T Шрифт и цвет текста")
        self.font_textcolor_btn.setFixedHeight(32)
        self.font_textcolor_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #666666;
                color: {self.parent_note.text_color};
                border-radius: 6px;
                text-align: left;
                padding-left: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #888888;
            }}
        """)
        self.font_textcolor_btn.clicked.connect(self.parent_note.openFontTextColorDialog)
        layout.addWidget(self.font_textcolor_btn)
        
        # Кнопка "Тема"
        self.theme_btn = QPushButton("🎭 Тема")
        self.theme_btn.setFixedHeight(32)
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border-radius: 6px;
                text-align: left;
                padding-left: 10px;
            }
            QPushButton:hover {
                background-color: #888888;
            }
        """)
        self.theme_btn.clicked.connect(self.parent_note.changeTheme)
        layout.addWidget(self.theme_btn)
        
        # Овальный переключатель "Поверх всех окон"
        top_toggle_widget = QWidget()
        top_toggle_layout = QHBoxLayout(top_toggle_widget)
        top_toggle_layout.setContentsMargins(0, 0, 0, 0)
        
        self.top_toggle_slider = QSlider(Qt.Horizontal)
        self.top_toggle_slider.setMinimum(0)
        self.top_toggle_slider.setMaximum(1)
        self.top_toggle_slider.setValue(1 if self.parent_note.always_on_top else 0)
        self.top_toggle_slider.setFixedWidth(80)
        self.top_toggle_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #CCCCCC;
                height: 20px;
                border-radius: 10px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFAA00, stop:1 #FFCC00);
                width: 30px;
                margin: -5px 0;
                border-radius: 15px;
                border: 2px solid #FF8800;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFCC00, stop:1 #FFEE00);
                border: 2px solid #FFAA00;
            }
            QSlider::sub-page:horizontal {
                background: #FFAA00;
                border-radius: 10px;
            }
            QSlider::add-page:horizontal {
                background: #CCCCCC;
                border-radius: 10px;
            }
        """)
        self.top_toggle_slider.valueChanged.connect(self.onTopToggleChanged)
        top_toggle_layout.addWidget(self.top_toggle_slider)
        
        self.top_toggle_label = QLabel("Поверх всех окон" if self.parent_note.always_on_top else "Обычный режим")
        self.top_toggle_label.setStyleSheet("color: #666666; font-weight: bold;")
        top_toggle_layout.addWidget(self.top_toggle_label)
        top_toggle_layout.addStretch()
        
        layout.addWidget(top_toggle_widget)
        
        # Кнопка "Закрыть"
        self.close_btn = QPushButton("× Закрыть заметку")
        self.close_btn.setFixedHeight(32)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                text-align: left;
                padding-left: 10px;
            }
            QPushButton:hover {
                background-color: #FF6666;
            }
        """)
        self.close_btn.clicked.connect(self.parent_note.closeNote)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
        
    def updateButtons(self):
        """Обновляет состояние кнопок"""
        self.top_toggle_slider.setValue(1 if self.parent_note.always_on_top else 0)
        self.top_toggle_label.setText("Поверх всех окон" if self.parent_note.always_on_top else "Обычный режим")
        self.font_textcolor_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #666666;
                color: {self.parent_note.text_color};
                border-radius: 6px;
                text-align: left;
                padding-left: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #888888;
            }}
        """)
        
    def onTopToggleChanged(self, value):
        """Обработка изменения переключателя"""
        self.parent_note.always_on_top = (value == 1)
        self.top_toggle_label.setText("Поверх всех окон" if value == 1 else "Обычный режим")
        self.parent_note.updateWindowFlagsSilent()
        self.parent_note.saveSettings()

class ResizableStickyNote(QWidget):
    def __init__(self, note_id=1, content="", color="#FFFF99", font_family="Arial", 
                 font_size=10, text_color="#000000", size=(300, 300), 
                 always_on_top=True, pinned_to_screen=False, theme="default",
                 gradient_color1=None, gradient_color2=None, gradient_direction="horizontal"):
        super().__init__()
        self.note_id = note_id
        self.color = color
        self.font_family = font_family
        self.font_size = font_size
        self.text_color = text_color
        self.init_width, self.init_height = size
        self.always_on_top = always_on_top
        self.pinned_to_screen = pinned_to_screen
        self.theme = theme
        self.gradient_color1 = gradient_color1 or color
        self.gradient_color2 = gradient_color2 or self.lighten_color(color, 20)
        self.gradient_direction = gradient_direction
        
        # Для управления видимостью кнопки настроек
        self.settings_btn_visible = False
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hideSettingsButton)
        
        # Всплывающее окно настроек
        self.settings_popup = None
        
        self.initUI()
        self.text_edit.setPlainText(content)
        self.loadSettings()
        
    def initUI(self):
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
        self.applyTheme()
        
        # Текстовое поле с настройкой цвета текста
        self.text_edit = QTextEdit()
        font = QFont(self.font_family, self.font_size)
        self.text_edit.setFont(font)
        self.updateTextColor()
        
        # Кнопка настроек (изначально скрытая, с прозрачным фоном)
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(25, 25)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(100, 100, 100, 0.8);
                border-radius: 12px;
                font-size: 12px;
                border: none;
                opacity: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
                color: rgba(50, 50, 50, 1);
            }
        """)
        self.settings_btn.clicked.connect(self.showSettingsPopup)
        
        # Основной лэйаут
        main_layout = QVBoxLayout(self.main_widget)
        
        # Верхняя панель для кнопки настроек
        top_panel = QWidget()
        top_panel.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(top_panel)
        top_layout.addStretch()
        top_layout.addWidget(self.settings_btn)
        top_layout.setContentsMargins(0, 5, 5, 0)
        
        main_layout.addWidget(top_panel)
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
        
        # Скрываем кнопку через 2 секунды после создания
        QTimer.singleShot(2000, self.hideSettingsButton)
        
    def applyTheme(self):
        """Применяет тему к заметке"""
        if self.theme == "glass":
            style = f"""
                QWidget {{
                    background-color: rgba{self.hex_to_rgba(self.color, 0.8)};
                    border-radius: 8px;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }}
            """
        elif self.theme == "gradient":
            # Определяем направление градиента
            if self.gradient_direction == "horizontal":
                gradient = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self.gradient_color1}, stop:1 {self.gradient_color2})"
            elif self.gradient_direction == "vertical":
                gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {self.gradient_color1}, stop:1 {self.gradient_color2})"
            elif self.gradient_direction == "diagonal":
                gradient = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {self.gradient_color1}, stop:1 {self.gradient_color2})"
            else:  # radial
                gradient = f"qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 {self.gradient_color1}, stop:1 {self.gradient_color2})"
            
            style = f"""
                QWidget {{
                    background: {gradient};
                    border-radius: 8px;
                    border: 1px solid rgba(100, 100, 100, 0.2);
                }}
            """
        else:  # default
            style = f"""
                QWidget {{
                    background-color: {self.color};
                    border-radius: 8px;
                    border: 1px solid rgba(100, 100, 100, 0.2);
                }}
            """
        
        self.main_widget.setStyleSheet(style)
        
    def hex_to_rgba(self, hex_color, alpha=1.0):
        """Конвертирует hex в rgba"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    
    def lighten_color(self, hex_color, percent):
        """Осветляет цвет на заданный процент"""
        hex_color = hex_color.lstrip('#')
        r = min(255, int(int(hex_color[0:2], 16) * (1 + percent/100)))
        g = min(255, int(int(hex_color[2:4], 16) * (1 + percent/100)))
        b = min(255, int(int(hex_color[4:6], 16) * (1 + percent/100)))
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def updateTextColor(self):
        """Обновляет цвет текста в текстовом поле"""
        style = f"""
            QTextEdit {{
                background: transparent;
                border: none;
                padding: 10px;
                color: {self.text_color};
                font-size: {self.font_size}px;
            }}
        """
        self.text_edit.setStyleSheet(style)
        
    def enterEvent(self, event):
        """При наведении курсора на стикер показываем кнопку настроек"""
        self.showSettingsButton()
        self.hide_timer.stop()
        
    def leaveEvent(self, event):
        """При уходе курсора со стикера скрываем кнопку через 1 секунду"""
        if not self.underMouse():
            self.hide_timer.start(1000)
        
    def showSettingsButton(self):
        """Плавно показываем кнопку настроек"""
        if not self.settings_btn_visible:
            self.settings_btn_visible = True
            self.animateSettingsButtonOpacity(0, 1)
                
    def hideSettingsButton(self):
        """Плавно скрываем кнопку настроек"""
        if self.settings_btn_visible and not self.underMouse():
            self.settings_btn_visible = False
            self.animateSettingsButtonOpacity(1, 0)
                
    def animateSettingsButtonOpacity(self, start, end):
        """Анимируем изменение прозрачности кнопки настроек"""
        animation = QPropertyAnimation(self.settings_btn, b"windowOpacity")
        animation.setDuration(200)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()
        
    def showSettingsPopup(self):
        """Показывает всплывающее окно с настройками"""
        if not self.settings_popup:
            self.settings_popup = SettingsPopup(self)
        
        self.settings_popup.updateButtons()
        
        # Позиционируем всплывающее окно рядом с кнопкой настроек
        btn_pos = self.settings_btn.mapToGlobal(QPoint(0, 0))
        popup_x = btn_pos.x() - self.settings_popup.width() + self.settings_btn.width()
        popup_y = btn_pos.y() + self.settings_btn.height() + 5
        
        self.settings_popup.move(popup_x, popup_y)
        self.settings_popup.show()
        
    def closeSettingsPopup(self):
        """Закрывает всплывающее окно с настройками"""
        if self.settings_popup:
            self.settings_popup.close()
            
    def openColorGradientDialog(self):
        """Открывает диалог для выбора цвета или градиента"""
        self.closeSettingsPopup()
        
        dialog = ColorGradientDialog(self.color, self.gradient_color1, self.gradient_color2, self)
        if dialog.exec_() == QDialog.Accepted:
            if dialog.result_type == "solid":
                self.color = dialog.result_color
                self.theme = "default"
            else:
                self.gradient_color1 = dialog.result_gradient1
                self.gradient_color2 = dialog.result_gradient2
                self.theme = "gradient"
            
            self.applyTheme()
            self.saveSettings()
            
    def openFontTextColorDialog(self):
        """Открывает диалог для выбора шрифта и цвета текста"""
        self.closeSettingsPopup()
        
        dialog = FontTextColorDialog(self.font_family, self.font_size, self.text_color, self)
        if dialog.exec_() == QDialog.Accepted:
            self.font_family = dialog.font_family
            self.font_size = dialog.font_size
            self.text_color = dialog.text_color
            
            font = QFont(self.font_family, self.font_size)
            self.text_edit.setFont(font)
            self.updateTextColor()
            self.saveSettings()
        
    def changeTheme(self):
        """Меняет тему заметки"""
        themes = ["default", "gradient", "glass"]
        current_index = themes.index(self.theme) if self.theme in themes else 0
        next_theme = themes[(current_index + 1) % len(themes)]
        self.theme = next_theme
        self.applyTheme()
        self.saveSettings()
        self.closeSettingsPopup()
        
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
            self.showSettingsButton()
            self.hide_timer.stop()
            self.closeSettingsPopup()
            
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
            
    def createNewNote(self):
        if hasattr(self, 'main_window'):
            self.main_window.createNewNote()
        self.closeSettingsPopup()
            
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
        settings.setValue(f"note_{self.note_id}_text_color", self.text_color)
        settings.setValue(f"note_{self.note_id}_always_on_top", self.always_on_top)
        settings.setValue(f"note_{self.note_id}_pinned_to_screen", self.pinned_to_screen)
        settings.setValue(f"note_{self.note_id}_theme", self.theme)
        settings.setValue(f"note_{self.note_id}_gradient_color1", self.gradient_color1)
        settings.setValue(f"note_{self.note_id}_gradient_color2", self.gradient_color2)
        settings.setValue(f"note_{self.note_id}_gradient_direction", self.gradient_direction)
        
    def loadSettings(self):
        settings = QSettings("StickyNotes", "NoteSettings")
        geometry = settings.value(f"note_{self.note_id}_geometry")
        if geometry:
            self.setGeometry(geometry)
        color = settings.value(f"note_{self.note_id}_color", self.color)
        if color:
            self.color = color
        font_family = settings.value(f"note_{self.note_id}_font_family", self.font_family)
        font_size = int(settings.value(f"note_{self.note_id}_font_size", self.font_size))
        self.font_family = font_family
        self.font_size = font_size
        self.text_edit.setFont(QFont(font_family, font_size))
        
        # Загружаем цвет текста
        text_color = settings.value(f"note_{self.note_id}_text_color", self.text_color)
        self.text_color = text_color
        
        # Загружаем тему
        theme = settings.value(f"note_{self.note_id}_theme", self.theme)
        self.theme = theme
        
        # Загружаем настройки градиента
        gradient_color1 = settings.value(f"note_{self.note_id}_gradient_color1")
        if gradient_color1:
            self.gradient_color1 = gradient_color1
            
        gradient_color2 = settings.value(f"note_{self.note_id}_gradient_color2")
        if gradient_color2:
            self.gradient_color2 = gradient_color2
            
        gradient_direction = settings.value(f"note_{self.note_id}_gradient_direction", "horizontal")
        self.gradient_direction = gradient_direction
        
        self.always_on_top = settings.value(f"note_{self.note_id}_always_on_top", "true").lower() == "true"
        self.pinned_to_screen = settings.value(f"note_{self.note_id}_pinned_to_screen", "false").lower() == "true"
        
        # Применяем тему после загрузки всех настроек
        self.applyTheme()
        self.updateTextColor()
        
        if self.pinned_to_screen:
            self.pin_timer.start(100)
            QTimer.singleShot(100, self.pinToCurrentScreen)

class StickyNotesApp:
    def __init__(self):
        self.VERSION = "1.1.0"
        self.UPDATE_URL = "https://raw.githubusercontent.com/DaniiL-Buzakov/Stikers/main/version.json"
        self.RELEASES_URL = "https://github.com/DaniiL-Buzakov/Stikers/releases"
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
        
        # Пункт для ручной проверки обновлений
        check_update_action = QAction("Проверить обновления", self.app)
        check_update_action.triggered.connect(self.checkForUpdatesManual)
        tray_menu.addAction(check_update_action)
        
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
            
        # Запускаем проверку обновлений при старте (с задержкой)
        QTimer.singleShot(2000, self.checkForUpdatesAuto)
        
        sys.exit(self.app.exec_())
    
    def checkForUpdatesAuto(self):
        """Автоматическая проверка обновлений при запуске"""
        self.checkForUpdates(show_message=False)
    
    def checkForUpdatesManual(self):
        """Ручная проверка обновлений из меню"""
        self.checkForUpdates(show_message=True)
    
    def checkForUpdates(self, show_message=False):
        """Проверяет наличие обновлений"""
        try:
            settings = QSettings("StickyNotes", "Updates")
            
            # Проверяем, когда последний раз проверяли
            last_check = settings.value("last_update_check")
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Проверяем не чаще раза в день (если не ручная проверка)
            if not show_message and last_check == today:
                return
                
            response = requests.get(self.UPDATE_URL, timeout=5)
            response.raise_for_status()
            update_info = response.json()
            
            if version.parse(update_info.get('version', '0.0.0')) > version.parse(self.VERSION):
                self.show_update_dialog(update_info, show_message)
            else:
                if show_message:
                    QMessageBox.information(None, "Проверка обновлений", 
                                           f"У вас установлена последняя версия ({self.VERSION})")
                    
            # Сохраняем дату проверки
            settings.setValue("last_update_check", today)
            
        except requests.RequestException as e:
            if show_message:
                QMessageBox.warning(None, "Ошибка проверки обновлений", 
                                   f"Ошибка подключения: {str(e)}")
        except Exception as e:
            if show_message:
                QMessageBox.warning(None, "Ошибка проверки обновлений", 
                                   f"Ошибка: {str(e)}")
    
    def show_update_dialog(self, update_info, show_message=False):
        """Показывает диалог обновления"""
        # Проверяем, не пропущена ли эта версия
        settings = QSettings("StickyNotes", "Updates")
        if settings.value(f"skip_version_{update_info.get('version')}", False):
            if show_message:
                QMessageBox.information(None, "Проверка обновлений", 
                                       f"У вас установлена последняя версия ({self.VERSION})")
            return
            
        dialog = UpdateDialog(update_info, self.VERSION)
        if dialog.exec_() == QDialog.Accepted:
            # Показываем уведомление в трее
            self.tray_icon.showMessage(
                "Обновление Sticky Notes",
                f"Загружается версия {update_info.get('version')}",
                QSystemTrayIcon.Information,
                3000
            )
        
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
            note.updateWindowFlagsSilent()
            note.saveSettings()
            
    def toggleAllPinned(self):
        if not self.notes:
            return
            
        first_note = list(self.notes.values())[0]
        new_state = not first_note.pinned_to_screen
        
        for note in self.notes.values():
            note.pinned_to_screen = new_state
            
            if new_state and note.always_on_top:
                note.always_on_top = False
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
                "text_color": note.text_color,
                "width": note.width(),
                "height": note.height(),
                "always_on_top": note.always_on_top,
                "pinned_to_screen": note.pinned_to_screen,
                "theme": note.theme,
                "gradient_color1": note.gradient_color1,
                "gradient_color2": note.gradient_color2,
                "gradient_direction": note.gradient_direction
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
                theme = note_data.get("theme", "default")
                gradient_color1 = note_data.get("gradient_color1")
                gradient_color2 = note_data.get("gradient_color2")
                gradient_direction = note_data.get("gradient_direction", "horizontal")
                
                note = ResizableStickyNote(
                    note_id,
                    note_data.get("content", ""),
                    note_data.get("color", "#FFFF99"),
                    note_data.get("font_family", "Arial"),
                    note_data.get("font_size", 10),
                    note_data.get("text_color", "#000000"),
                    (width, height),
                    always_on_top,
                    pinned_to_screen,
                    theme,
                    gradient_color1,
                    gradient_color2,
                    gradient_direction
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