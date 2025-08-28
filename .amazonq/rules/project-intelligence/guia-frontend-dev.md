# CSC-Reach - Guia do Desenvolvedor Frontend

## Visão Geral

Este guia orienta desenvolvedores frontend na criação de novas interfaces e componentes para CSC-Reach, seguindo os padrões estabelecidos com PySide6 e as práticas de UX/UI implementadas.

## Arquitetura Frontend

### Estrutura de Componentes
```
src/multichannel_messaging/gui/
├── main_window.py                  # Janela principal
├── dialogs/                        # Diálogos modais
│   ├── template_library_dialog.py
│   ├── preferences_dialog.py
│   └── progress_dialog.py
├── widgets/                        # Widgets reutilizáveis
│   ├── variables_panel.py
│   └── custom_widgets.py
└── resources/                      # Recursos visuais
    ├── icons/
    └── styles/
```

### Padrões de Design Obrigatórios
- **Component-Based Architecture**: Componentes reutilizáveis e modulares
- **Signal/Slot Pattern**: Comunicação entre componentes via Qt signals
- **MVC Separation**: View separada da lógica de negócio
- **Theme System**: Suporte a temas claro/escuro
- **Internationalization**: Suporte completo a múltiplos idiomas

## Criando Novos Componentes

### 1. Diálogos Modais

#### Estrutura Base de Diálogo
```python
# src/multichannel_messaging/gui/dialogs/new_feature_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QTextEdit
)
from PySide6.QtCore import Signal, Qt
from ..core.i18n_manager import I18nManager
from ..core.theme_manager import ThemeManager

class NewFeatureDialog(QDialog):
    # Signals para comunicação com componentes pai
    feature_created = Signal(dict)
    feature_updated = Signal(str, dict)
    
    def __init__(self, parent=None, feature_data=None):
        super().__init__(parent)
        self.i18n = I18nManager()
        self.theme_manager = ThemeManager()
        self.feature_data = feature_data
        
        self.setup_ui()
        self.setup_connections()
        self.apply_theme()
        
        if feature_data:
            self.load_feature_data(feature_data)
    
    def setup_ui(self):
        """Configurar interface do usuário"""
        self.setWindowTitle(self.i18n.translate("new_feature_dialog.title"))
        self.setModal(True)
        self.resize(600, 400)
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Campos de entrada
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(
            self.i18n.translate("new_feature_dialog.name_placeholder")
        )
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            self.i18n.translate("new_feature_dialog.description_placeholder")
        )
        
        # Botões
        button_layout = QHBoxLayout()
        self.save_button = QPushButton(self.i18n.translate("common.save"))
        self.cancel_button = QPushButton(self.i18n.translate("common.cancel"))
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        # Adicionar ao layout principal
        layout.addWidget(QLabel(self.i18n.translate("new_feature_dialog.name_label")))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel(self.i18n.translate("new_feature_dialog.description_label")))
        layout.addWidget(self.description_edit)
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Configurar conexões de sinais"""
        self.save_button.clicked.connect(self.save_feature)
        self.cancel_button.clicked.connect(self.reject)
        
        # Validação em tempo real
        self.name_edit.textChanged.connect(self.validate_input)
        self.description_edit.textChanged.connect(self.validate_input)
    
    def apply_theme(self):
        """Aplicar tema atual"""
        theme = self.theme_manager.get_current_theme()
        self.setStyleSheet(theme.get_dialog_stylesheet())
    
    def validate_input(self):
        """Validar entrada do usuário"""
        name_valid = len(self.name_edit.text().strip()) > 0
        description_valid = len(self.description_edit.toPlainText().strip()) > 0
        
        self.save_button.setEnabled(name_valid and description_valid)
    
    def save_feature(self):
        """Salvar nova funcionalidade"""
        feature_data = {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'created_at': datetime.now()
        }
        
        if self.feature_data:
            # Atualizar funcionalidade existente
            self.feature_updated.emit(self.feature_data['id'], feature_data)
        else:
            # Criar nova funcionalidade
            self.feature_created.emit(feature_data)
        
        self.accept()
```

### 2. Widgets Customizados

#### Widget Reutilizável
```python
# src/multichannel_messaging/gui/widgets/feature_card_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QPainter, QBrush

class FeatureCardWidget(QWidget):
    edit_requested = Signal(dict)
    delete_requested = Signal(str)
    
    def __init__(self, feature_data, parent=None):
        super().__init__(parent)
        self.feature_data = feature_data
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configurar interface do card"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header com título e botões
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(self.feature_data['name'])
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.edit_button = QPushButton("✏️")
        self.edit_button.setFixedSize(24, 24)
        self.edit_button.setToolTip("Edit feature")
        
        self.delete_button = QPushButton("🗑️")
        self.delete_button.setFixedSize(24, 24)
        self.delete_button.setToolTip("Delete feature")
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.edit_button)
        header_layout.addWidget(self.delete_button)
        
        # Descrição
        self.description_label = QLabel(self.feature_data['description'])
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #666; font-size: 12px;")
        
        layout.addLayout(header_layout)
        layout.addWidget(self.description_label)
        
        # Estilo do card
        self.setStyleSheet("""
            FeatureCardWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            FeatureCardWidget:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
    
    def setup_connections(self):
        """Configurar conexões"""
        self.edit_button.clicked.connect(lambda: self.edit_requested.emit(self.feature_data))
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.feature_data['id']))
```

### 3. Integração com Sistema de Temas

#### Suporte a Temas Customizados
```python
# src/multichannel_messaging/core/theme_manager.py (extensão)
class ThemeManager:
    def register_component_theme(self, component_name: str, theme_data: Dict):
        """Registrar tema para componente específico"""
        self.component_themes[component_name] = theme_data
    
    def get_component_stylesheet(self, component_name: str) -> str:
        """Obter stylesheet para componente"""
        theme = self.get_current_theme()
        component_theme = self.component_themes.get(component_name, {})
        
        return self._generate_stylesheet(theme, component_theme)

# Uso no componente
class MyCustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def apply_theme(self):
        """Aplicar tema ao widget"""
        stylesheet = self.theme_manager.get_component_stylesheet('my_custom_widget')
        self.setStyleSheet(stylesheet)
```

### 4. Sistema de Internacionalização

#### Componente Multilíngue
```python
# src/multichannel_messaging/gui/widgets/multilingual_widget.py
class MultilingualWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n = I18nManager()
        self.i18n.language_changed.connect(self.update_translations)
        
        self.setup_ui()
        self.update_translations()
    
    def setup_ui(self):
        """Configurar interface (sem textos hardcoded)"""
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel()
        self.description_label = QLabel()
        self.action_button = QPushButton()
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.action_button)
    
    def update_translations(self):
        """Atualizar textos com idioma atual"""
        self.title_label.setText(self.i18n.translate("widget.title"))
        self.description_label.setText(self.i18n.translate("widget.description"))
        self.action_button.setText(self.i18n.translate("widget.action_button"))
        
        # Atualizar tooltips
        self.action_button.setToolTip(self.i18n.translate("widget.action_tooltip"))
```

### 5. Acessibilidade e Navegação

#### Widget Acessível
```python
class AccessibleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_accessibility()
    
    def setup_accessibility(self):
        """Configurar recursos de acessibilidade"""
        # Definir roles ARIA
        self.setAccessibleName("Feature Management Panel")
        self.setAccessibleDescription("Panel for managing application features")
        
        # Configurar navegação por teclado
        self.setFocusPolicy(Qt.StrongFocus)
        self.setTabOrder(self.first_input, self.second_input)
        
        # Atalhos de teclado
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_action)
    
    def keyPressEvent(self, event):
        """Manipular eventos de teclado"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
            self.save_action()
        else:
            super().keyPressEvent(event)
```

## Padrões de Desenvolvimento Frontend

### 1. Gerenciamento de Estado
```python
# src/multichannel_messaging/gui/state_manager.py
class UIStateManager:
    def __init__(self):
        self.state = {}
        self.observers = []
    
    def set_state(self, key: str, value: Any):
        """Atualizar estado e notificar observadores"""
        old_value = self.state.get(key)
        self.state[key] = value
        
        if old_value != value:
            self.notify_observers(key, value, old_value)
    
    def get_state(self, key: str, default=None):
        """Obter valor do estado"""
        return self.state.get(key, default)
    
    def subscribe(self, observer: Callable):
        """Inscrever observador para mudanças de estado"""
        self.observers.append(observer)
    
    def notify_observers(self, key: str, new_value: Any, old_value: Any):
        """Notificar observadores sobre mudanças"""
        for observer in self.observers:
            observer(key, new_value, old_value)
```

### 2. Validação de Formulários
```python
# src/multichannel_messaging/gui/validators.py
class FormValidator:
    def __init__(self):
        self.rules = {}
        self.errors = {}
    
    def add_rule(self, field: str, validator: Callable, message: str):
        """Adicionar regra de validação"""
        if field not in self.rules:
            self.rules[field] = []
        self.rules[field].append((validator, message))
    
    def validate(self, data: Dict) -> bool:
        """Validar dados do formulário"""
        self.errors.clear()
        
        for field, rules in self.rules.items():
            value = data.get(field, '')
            
            for validator, message in rules:
                if not validator(value):
                    if field not in self.errors:
                        self.errors[field] = []
                    self.errors[field].append(message)
        
        return len(self.errors) == 0
    
    def get_errors(self) -> Dict:
        """Obter erros de validação"""
        return self.errors.copy()

# Uso em formulário
class FeatureForm(QWidget):
    def setup_validation(self):
        self.validator = FormValidator()
        
        # Regras de validação
        self.validator.add_rule('name', 
            lambda x: len(x.strip()) > 0, 
            "Name is required")
        self.validator.add_rule('name', 
            lambda x: len(x) <= 100, 
            "Name must be less than 100 characters")
    
    def validate_form(self) -> bool:
        data = {
            'name': self.name_edit.text(),
            'description': self.description_edit.toPlainText()
        }
        
        if self.validator.validate(data):
            return True
        else:
            self.show_validation_errors(self.validator.get_errors())
            return False
```

### 3. Componentes Responsivos
```python
class ResponsiveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_responsive_layout()
    
    def setup_responsive_layout(self):
        """Configurar layout responsivo"""
        self.main_layout = QVBoxLayout(self)
        self.content_widget = QWidget()
        self.main_layout.addWidget(self.content_widget)
        
        # Layout adaptável
        self.update_layout()
    
    def resizeEvent(self, event):
        """Responder a mudanças de tamanho"""
        super().resizeEvent(event)
        self.update_layout()
    
    def update_layout(self):
        """Atualizar layout baseado no tamanho"""
        width = self.width()
        
        if width < 600:
            # Layout mobile/pequeno
            self.setup_compact_layout()
        elif width < 1000:
            # Layout médio
            self.setup_medium_layout()
        else:
            # Layout desktop/grande
            self.setup_full_layout()
    
    def setup_compact_layout(self):
        """Layout para telas pequenas"""
        # Implementar layout vertical compacto
        pass
    
    def setup_medium_layout(self):
        """Layout para telas médias"""
        # Implementar layout híbrido
        pass
    
    def setup_full_layout(self):
        """Layout para telas grandes"""
        # Implementar layout completo
        pass
```

## Testes de Interface

### 1. Testes de Componentes
```python
# tests/gui/test_feature_dialog.py
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from multichannel_messaging.gui.dialogs.new_feature_dialog import NewFeatureDialog

class TestNewFeatureDialog:
    def setup_method(self):
        self.app = QApplication.instance() or QApplication([])
        self.dialog = NewFeatureDialog()
    
    def test_dialog_initialization(self):
        """Testar inicialização do diálogo"""
        assert self.dialog.windowTitle() != ""
        assert self.dialog.isModal()
        assert not self.dialog.save_button.isEnabled()  # Deve estar desabilitado inicialmente
    
    def test_input_validation(self):
        """Testar validação de entrada"""
        # Entrada inválida
        self.dialog.name_edit.setText("")
        self.dialog.description_edit.setPlainText("")
        assert not self.dialog.save_button.isEnabled()
        
        # Entrada válida
        self.dialog.name_edit.setText("Test Feature")
        self.dialog.description_edit.setPlainText("Test Description")
        assert self.dialog.save_button.isEnabled()
    
    def test_signal_emission(self):
        """Testar emissão de sinais"""
        # Configurar spy para sinal
        signal_spy = []
        self.dialog.feature_created.connect(lambda data: signal_spy.append(data))
        
        # Preencher dados e salvar
        self.dialog.name_edit.setText("Test Feature")
        self.dialog.description_edit.setPlainText("Test Description")
        self.dialog.save_feature()
        
        # Verificar sinal emitido
        assert len(signal_spy) == 1
        assert signal_spy[0]['name'] == "Test Feature"
```

### 2. Testes de Integração UI
```python
# tests/integration/test_feature_workflow.py
def test_complete_feature_workflow(qtbot):
    """Testar workflow completo de funcionalidade"""
    from multichannel_messaging.gui.main_window import MainWindow
    
    # Inicializar janela principal
    main_window = MainWindow()
    qtbot.addWidget(main_window)
    
    # Abrir diálogo de nova funcionalidade
    qtbot.mouseClick(main_window.new_feature_button, Qt.LeftButton)
    
    # Verificar se diálogo foi aberto
    dialog = main_window.findChild(NewFeatureDialog)
    assert dialog is not None
    assert dialog.isVisible()
    
    # Preencher formulário
    qtbot.keyClicks(dialog.name_edit, "Test Feature")
    qtbot.keyClicks(dialog.description_edit, "Test Description")
    
    # Salvar
    qtbot.mouseClick(dialog.save_button, Qt.LeftButton)
    
    # Verificar se funcionalidade foi adicionada
    assert "Test Feature" in main_window.get_feature_names()
```

## Checklist para Novos Componentes

### Design e UX
- [ ] Seguir guidelines de design estabelecidos
- [ ] Implementar estados visuais (hover, focus, disabled)
- [ ] Garantir consistência com componentes existentes
- [ ] Testar em diferentes tamanhos de tela
- [ ] Validar fluxo de usuário

### Funcionalidade
- [ ] Implementar validação de entrada
- [ ] Adicionar tratamento de erros
- [ ] Configurar sinais e slots apropriados
- [ ] Implementar undo/redo se aplicável
- [ ] Adicionar feedback visual para ações

### Acessibilidade
- [ ] Definir roles e labels acessíveis
- [ ] Configurar navegação por teclado
- [ ] Implementar atalhos de teclado
- [ ] Testar com leitores de tela
- [ ] Garantir contraste adequado

### Internacionalização
- [ ] Usar sistema de tradução para todos os textos
- [ ] Testar com idiomas de texto longo
- [ ] Configurar formatação de data/hora por locale
- [ ] Implementar suporte a RTL se necessário

### Performance
- [ ] Otimizar renderização para listas grandes
- [ ] Implementar lazy loading quando apropriado
- [ ] Minimizar redraws desnecessários
- [ ] Testar performance com dados reais

### Testes
- [ ] Criar testes unitários para lógica do componente
- [ ] Implementar testes de integração
- [ ] Testar interações de usuário
- [ ] Validar comportamento em edge cases
- [ ] Testar em diferentes plataformas

Este guia fornece a base para desenvolver interfaces consistentes e de alta qualidade no CSC-Reach.
