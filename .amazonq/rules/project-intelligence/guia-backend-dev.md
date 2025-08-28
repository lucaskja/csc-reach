# CSC-Reach - Guia do Desenvolvedor Backend

## Visão Geral

Este guia orienta desenvolvedores backend na criação de novas funcionalidades para CSC-Reach, seguindo a arquitetura MVC estabelecida e os padrões de design implementados.

## Arquitetura Backend

### Estrutura de Camadas
```
src/multichannel_messaging/core/     # Lógica de Negócio
src/multichannel_messaging/services/ # Integrações Externas
src/multichannel_messaging/utils/    # Utilitários
```

### Padrões Obrigatórios
- **MVC Pattern**: Separação clara entre Model, View, Controller
- **Strategy Pattern**: Implementações específicas por plataforma
- **Observer Pattern**: Comunicação via eventos
- **Factory Pattern**: Criação dinâmica de componentes
- **Singleton Pattern**: Gerenciadores globais

## Adicionando Novas Funcionalidades

### 1. Processamento de Dados

#### Novo Formato de Arquivo
```python
# src/multichannel_messaging/core/csv_processor.py
class CSVProcessor:
    def __init__(self):
        self.supported_formats.append('xml')  # Adicionar novo formato
    
    def _detect_format(self, file_path: str) -> str:
        # Adicionar lógica de detecção
        if file_path.endswith('.xml'):
            return 'xml'
    
    def _parse_xml(self, file_path: str) -> List[Dict]:
        """Parse XML file format"""
        import xml.etree.ElementTree as ET
        # Implementar parser XML
        pass
```

#### Validação de Dados
```python
# src/multichannel_messaging/core/data_validator.py
class DataValidator:
    def validate_xml_data(self, data: List[Dict]) -> ValidationResult:
        """Validar dados específicos de XML"""
        errors = []
        warnings = []
        
        for record in data:
            # Implementar validações específicas
            pass
        
        return ValidationResult(
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

### 2. Sistema de Templates

#### Nova Categoria de Template
```python
# src/multichannel_messaging/core/template_manager.py
class TemplateManager:
    def __init__(self):
        self.categories = [
            'Welcome',       # Mensagens de boas-vindas (Verde #4CAF50)
            'Follow-up',     # Follow-up (Laranja #FF9800)
            'Promotional',   # Promocional (Rosa #E91E63)
            'Support',       # Suporte (Azul #2196F3)
            'General',       # Geral (Cinza #607D8B)
            'Newsletter',    # Nova categoria
            'Reminder',      # Nova categoria
            'Survey'         # Nova categoria
        ]
    
    def create_newsletter_template(self, template_data: Dict) -> str:
        """Criar template específico para newsletter"""
        template_data['category'] = 'Newsletter'
        template_data['channel'] = 'email'  # Newsletter só por email
        return self.create_template(template_data)
```

#### Sistema de Mapeamento de Canais
```python
# src/multichannel_messaging/core/channel_mapper.py
class ChannelMapper:
    def __init__(self):
        self.channel_options = [
            ("email_only", "email_only"),
            ("whatsapp_business_api", "whatsapp_business"),
            ("whatsapp_web", "whatsapp_web"),
            ("email_whatsapp_business", "email_whatsapp_business"),
            ("email_whatsapp_web", "email_whatsapp_web")
        ]
    
    def get_channel_config(self, channel_id: str) -> Dict:
        """Obter configuração do canal"""
        channel_configs = {
            'email_only': {'channels': ['email'], 'priority': 'email'},
            'whatsapp_business': {'channels': ['whatsapp'], 'api': 'business'},
            'whatsapp_web': {'channels': ['whatsapp'], 'api': 'web'},
            'email_whatsapp_business': {'channels': ['email', 'whatsapp'], 'api': 'business'},
            'email_whatsapp_web': {'channels': ['email', 'whatsapp'], 'api': 'web'}
        }
        return channel_configs.get(channel_id, {})
```

#### Variáveis Dinâmicas Customizadas
```python
# src/multichannel_messaging/core/dynamic_variable_manager.py
class DynamicVariableManager:
    def register_custom_variable(self, name: str, resolver: Callable):
        """Registrar nova variável customizada"""
        self.custom_variables[name] = resolver
    
    def resolve_date_variable(self, customer: Customer) -> str:
        """Resolver variável de data personalizada"""
        from datetime import datetime
        return datetime.now().strftime('%d/%m/%Y')
    
    def substitute_variables(self, template: str, customer: Customer) -> str:
        # Adicionar suporte a {date}, {time}, etc.
        template = template.replace('{date}', self.resolve_date_variable(customer))
        return super().substitute_variables(template, customer)
```

### 3. Integrações de Serviços

#### Sistema de Formatação de Email (macOS)
```python
# src/multichannel_messaging/services/outlook_macos.py
class OutlookMacOSService:
    def _build_email_script(self, subject: str, content: str, email: str, send: bool = True) -> str:
        """Sistema multi-abordagem com fallbacks para formatação de email"""
        # 1. Tentar abordagem baseada em arquivo (mais confiável)
        try:
            return self._build_file_based_email_script(subject, content, email, send)
        except Exception as e:
            logger.warning(f"File-based approach failed: {e}")
            
        # 2. Fallback para abordagem de texto simples
        try:
            return self._build_simple_text_email_script(subject, content, email, send)
        except Exception as e:
            logger.error(f"All email formatting approaches failed: {e}")
            raise EmailFormattingError("Cannot format email for AppleScript")
    
    def _build_file_based_email_script(self, subject: str, content: str, email: str, send: bool) -> str:
        """Abordagem baseada em arquivo para conteúdo complexo"""
        # Salvar conteúdo em arquivo temporário
        temp_file = self._create_temp_content_file(content)
        
        script = f'''
        tell application "Microsoft Outlook"
            set newMessage to make new outgoing message with properties {{
                subject: "{self._escape_applescript_string(subject)}",
                content: (read file "{temp_file}" as «class utf8»)
            }}
            make new recipient at newMessage with properties {{email address: {{address: "{email}"}}}}
            {"send newMessage" if send else ""}
        end tell
        '''
        return script
```

#### Novo Canal de Comunicação
```python
# src/multichannel_messaging/services/telegram_service.py
from abc import ABC, abstractmethod

class TelegramService(ABC):
    @abstractmethod
    def send_message(self, chat_id: str, message: str) -> SendResult:
        """Enviar mensagem via Telegram"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verificar se Telegram está disponível"""
        pass

class TelegramBotService(TelegramService):
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, chat_id: str, message: str) -> SendResult:
        import requests
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(f"{self.api_url}/sendMessage", json=payload)
            return SendResult(
                success=response.status_code == 200,
                message_id=response.json().get('result', {}).get('message_id'),
                error=None if response.status_code == 200 else response.text
            )
        except Exception as e:
            return SendResult(success=False, error=str(e))
```

#### Registro de Serviço
```python
# src/multichannel_messaging/core/service_registry.py
class ServiceRegistry:
    def __init__(self):
        self.services = {}
    
    def register_service(self, name: str, service_class: type):
        """Registrar novo serviço"""
        self.services[name] = service_class
    
    def get_service(self, name: str, **kwargs):
        """Obter instância do serviço"""
        if name in self.services:
            return self.services[name](**kwargs)
        raise ValueError(f"Service {name} not found")

# Uso
registry = ServiceRegistry()
registry.register_service('telegram', TelegramBotService)
```

### 4. Sistema de Logging e Analytics

#### Métricas Customizadas
```python
# src/multichannel_messaging/core/message_logger.py
class MessageLogger:
    def log_custom_metric(self, metric_name: str, value: float, tags: Dict = None):
        """Registrar métrica customizada"""
        metric_data = {
            'name': metric_name,
            'value': value,
            'timestamp': datetime.now(),
            'tags': tags or {}
        }
        
        self._store_metric(metric_data)
    
    def get_conversion_rate(self, campaign_id: str) -> float:
        """Calcular taxa de conversão de campanha"""
        sent = self.get_sent_count(campaign_id)
        opened = self.get_opened_count(campaign_id)
        return (opened / sent) * 100 if sent > 0 else 0
```

#### Exportação de Dados
```python
# src/multichannel_messaging/core/data_exporter.py
class DataExporter:
    def export_campaign_analytics(self, campaign_id: str, format: str = 'csv') -> str:
        """Exportar analytics de campanha"""
        data = self.message_logger.get_campaign_data(campaign_id)
        
        if format == 'csv':
            return self._export_to_csv(data)
        elif format == 'json':
            return self._export_to_json(data)
        elif format == 'excel':
            return self._export_to_excel(data)
        
        raise ValueError(f"Format {format} not supported")
```

### 5. Configuração e Gerenciamento

#### Novas Configurações
```python
# src/multichannel_messaging/core/config_manager.py
class ConfigManager:
    def get_telegram_config(self) -> Dict:
        """Obter configurações do Telegram"""
        return self.get('telegram', {
            'bot_token': '',
            'enabled': False,
            'rate_limit': 30  # mensagens por minuto
        })
    
    def validate_telegram_config(self, config: Dict) -> bool:
        """Validar configurações do Telegram"""
        required_fields = ['bot_token']
        return all(field in config for field in required_fields)
```

## Padrões de Desenvolvimento

### 1. Tratamento de Erros
```python
# src/multichannel_messaging/utils/exceptions.py
class TelegramError(CSCReachException):
    """Erro específico do Telegram"""
    pass

class RateLimitError(TelegramError):
    """Erro de limite de taxa"""
    pass

# Uso no serviço
try:
    result = telegram_service.send_message(chat_id, message)
except RateLimitError:
    # Implementar backoff exponencial
    time.sleep(60)
    result = telegram_service.send_message(chat_id, message)
```

### 2. Logging Estruturado
```python
from multichannel_messaging.utils.logger import get_logger

logger = get_logger(__name__)

def process_telegram_message(chat_id: str, message: str):
    logger.info("Processing Telegram message", extra={
        'chat_id': chat_id,
        'message_length': len(message),
        'service': 'telegram'
    })
    
    try:
        result = send_message(chat_id, message)
        logger.info("Message sent successfully", extra={
            'chat_id': chat_id,
            'message_id': result.message_id
        })
    except Exception as e:
        logger.error("Failed to send message", extra={
            'chat_id': chat_id,
            'error': str(e)
        }, exc_info=True)
```

### 3. Testes Unitários
```python
# tests/unit/test_telegram_service.py
import pytest
from unittest.mock import Mock, patch
from multichannel_messaging.services.telegram_service import TelegramBotService

class TestTelegramService:
    def setup_method(self):
        self.service = TelegramBotService(bot_token="test_token")
    
    @patch('requests.post')
    def test_send_message_success(self, mock_post):
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'message_id': 123}}
        mock_post.return_value = mock_response
        
        # Act
        result = self.service.send_message("chat123", "Hello World")
        
        # Assert
        assert result.success is True
        assert result.message_id == 123
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_message_failure(self, mock_post):
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        # Act
        result = self.service.send_message("chat123", "Hello World")
        
        # Assert
        assert result.success is False
        assert "Bad Request" in result.error
```

### 4. Integração com Sistema de Eventos
```python
# src/multichannel_messaging/core/event_manager.py
class EventManager:
    def emit_telegram_message_sent(self, chat_id: str, message_id: str):
        """Emitir evento de mensagem Telegram enviada"""
        self.emit(EventType.TELEGRAM_MESSAGE_SENT, {
            'chat_id': chat_id,
            'message_id': message_id,
            'timestamp': datetime.now()
        })

# Uso no serviço
def send_telegram_message(self, chat_id: str, message: str):
    result = self.telegram_service.send_message(chat_id, message)
    
    if result.success:
        self.event_manager.emit_telegram_message_sent(chat_id, result.message_id)
        self.message_logger.log_message_sent(
            customer=self.get_customer_by_chat_id(chat_id),
            channel='telegram',
            status='sent'
        )
    
    return result
```

## Checklist para Novas Features

### Antes de Implementar
- [ ] Definir interface/contrato da funcionalidade
- [ ] Identificar padrões de design aplicáveis
- [ ] Planejar tratamento de erros
- [ ] Definir estrutura de testes
- [ ] Verificar impacto em componentes existentes

### Durante a Implementação
- [ ] Seguir padrões de código estabelecidos
- [ ] Implementar logging estruturado
- [ ] Adicionar validação de dados
- [ ] Criar testes unitários
- [ ] Documentar APIs públicas

### Após a Implementação
- [ ] Executar suite completa de testes
- [ ] Verificar cobertura de código
- [ ] Testar integração com componentes existentes
- [ ] Atualizar documentação
- [ ] Criar testes de integração

## Recursos e Ferramentas

### Sistema de Build e Release

#### Makefile - Comandos Essenciais
```bash
# Desenvolvimento
make install-dev         # Instalar dependências de desenvolvimento
make test               # Executar todos os testes
make lint               # Verificar qualidade do código
make format             # Formatar código com black

# Gerenciamento de Versões
make version-check      # Verificar versão atual
make version-patch      # Incrementar patch (1.0.0 → 1.0.1)
make version-minor      # Incrementar minor (1.0.0 → 1.1.0)
make version-major      # Incrementar major (1.0.0 → 2.0.0)

# Build e Release
make build              # Build para todas as plataformas
make build-macos        # Build apenas macOS
make build-windows      # Build apenas Windows
make release-patch      # Release patch completo
```

#### GitHub Actions Workflows
- **`.github/workflows/build-macos.yml`**: Build automático para macOS
- **`.github/workflows/build-windows.yml`**: Build automático para Windows
- **Triggers**: Mudanças em `pyproject.toml`, tags `v*`, workflow manual
- **Outputs**: Executáveis `.app`/`.dmg` (macOS), `.exe`/`.zip` (Windows)

### Debugging
```bash
# Ativar modo debug
export CSC_REACH_DEBUG=1

# Executar com profiling
python -m cProfile -o profile.stats src/multichannel_messaging/main.py

# Analisar performance
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

### Testes de Performance
```python
# tests/performance/test_telegram_performance.py
import time
import pytest
from multichannel_messaging.services.telegram_service import TelegramBotService

def test_telegram_bulk_sending_performance():
    service = TelegramBotService("test_token")
    messages = ["Test message"] * 100
    
    start_time = time.time()
    
    for i, message in enumerate(messages):
        result = service.send_message(f"chat{i}", message)
        assert result.success
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Deve processar pelo menos 10 mensagens por segundo
    assert duration < 10.0
```

### Monitoramento
```python
# src/multichannel_messaging/core/health_monitor.py
class HealthMonitor:
    def check_telegram_health(self) -> HealthStatus:
        """Verificar saúde do serviço Telegram"""
        try:
            # Tentar operação simples
            result = self.telegram_service.get_me()
            return HealthStatus.HEALTHY if result.success else HealthStatus.DEGRADED
        except Exception:
            return HealthStatus.UNHEALTHY
```

Este guia fornece a base para desenvolver novas funcionalidades backend mantendo a consistência arquitetural e qualidade do código do CSC-Reach.
