# CSC-Reach - Pilha Técnica

## Tecnologias Principais

### Framework de Interface
- **PySide6 (>=6.5.0)**: Framework Qt para Python
  - Interface nativa multiplataforma
  - Componentes ricos e responsivos
  - Suporte completo a temas e acessibilidade
  - Integração com sistema operacional

### Linguagem de Programação
- **Python 3.8+**: Linguagem principal
  - Compatibilidade com versões 3.8 até 3.12
  - Type hints para melhor manutenibilidade
  - Async/await para operações não-bloqueantes
  - Rich ecosystem de bibliotecas

### Processamento de Dados
- **pandas (>=2.0.0)**: Manipulação de dados estruturados
  - Suporte a CSV, Excel, JSON, JSONL, TSV
  - Operações eficientes em grandes datasets
  - Detecção automática de tipos de dados
  - Validação e limpeza de dados

- **openpyxl (>=3.1.0)**: Leitura/escrita de arquivos Excel
- **xlrd (>=2.0.0)**: Suporte a arquivos Excel legados
- **chardet (>=5.0.0)**: Detecção automática de encoding

### Integrações Multiplataforma

#### Windows
- **pywin32 (>=306)**: Integração COM com Microsoft Outlook
  - Acesso direto às APIs do Outlook
  - Controle completo de emails e calendário
  - Integração nativa com sistema Windows

#### macOS
- **pyobjc-framework-Cocoa (>=9.0)**: Integração com Cocoa
- **pyobjc-framework-ScriptingBridge (>=9.0)**: AppleScript automation
  - Controle do Microsoft Outlook via AppleScript
  - Integração nativa com sistema macOS
  - Suporte a permissões de automação

### Configuração e Logging
- **PyYAML (>=6.0)**: Processamento de arquivos YAML
  - Configurações estruturadas e legíveis
  - Suporte a comentários e documentação
  - Validação de esquemas

- **colorlog (>=6.7.0)**: Sistema de logging colorido
  - Logs estruturados e coloridos
  - Rotação automática de arquivos
  - Múltiplos níveis de logging
  - Integração com sistema de monitoramento

### Internacionalização
- **Babel (>=2.12.0)**: Internacionalização e localização
  - Suporte a múltiplos idiomas (EN/PT/ES)
  - Formatação de datas e números por região
  - Pluralização automática
  - Extração e compilação de traduções

### Validação e Configuração
- **Cerberus (>=1.3.0)**: Validação de dados e configurações
  - Esquemas flexíveis de validação
  - Mensagens de erro personalizadas
  - Validação aninhada e condicional
  - Integração com configurações YAML

### Utilitários do Sistema
- **psutil (>=5.9.0)**: Monitoramento de sistema
  - Monitoramento de CPU e memória
  - Detecção de processos em execução
  - Informações de sistema operacional
  - Health checks da aplicação

- **python-dateutil (>=2.8.0)**: Manipulação avançada de datas
- **requests (>=2.31.0)**: Cliente HTTP para integrações web

## Ferramentas de Desenvolvimento

### Testes
- **pytest (>=7.4.0)**: Framework de testes principal
- **pytest-qt (>=4.2.0)**: Testes para aplicações Qt
- **pytest-cov (>=4.1.0)**: Cobertura de código
- **pytest-mock (>=3.11.0)**: Mocking para testes
- **pytest-timeout (>=2.1.0)**: Timeout para testes longos

### Qualidade de Código
- **black (>=23.0.0)**: Formatação automática de código
- **flake8 (>=6.0.0)**: Linting e verificação de estilo
- **mypy (>=1.5.0)**: Verificação de tipos estáticos
- **bandit (>=1.7.0)**: Análise de segurança
- **isort (>=5.12.0)**: Organização de imports

### Build e Distribuição
- **PyInstaller (>=5.13.0)**: Criação de executáveis
  - Empacotamento para Windows e macOS
  - Inclusão automática de dependências
  - Otimização de tamanho
  - Suporte a recursos estáticos

### Automação de Build
- **Makefile**: Sistema de build automatizado
  - Gerenciamento de versões (patch/minor/major)
  - Comandos de release automatizados
  - Build multiplataforma (macOS/Windows)
  - Integração com GitHub Actions

- **GitHub Actions**: CI/CD automatizado
  - `.github/workflows/build-macos.yml`: Build automático para macOS
  - `.github/workflows/build-windows.yml`: Build automático para Windows
  - Triggers automáticos em mudanças de versão
  - Release automático com artifacts

## Sistema de Build e Release

### Makefile - Comandos Principais

#### Gerenciamento de Versões
```bash
# Verificar versão atual
make version-check

# Incrementar versões
make version-patch        # 1.0.0 → 1.0.1
make version-minor        # 1.0.0 → 1.1.0  
make version-major        # 1.0.0 → 2.0.0

# Preview de mudanças
make version-dry-run-patch
make version-dry-run-minor
make version-dry-run-major
```

#### Comandos de Release
```bash
# Release completo (versão + build + deploy)
make release-patch        # Patch release para todas as plataformas
make release-minor        # Minor release para todas as plataformas
make release-major        # Major release para todas as plataformas
```

#### Build Multiplataforma
```bash
# Build completo
make build               # Build para todas as plataformas
make build-macos         # Build apenas macOS
make build-windows       # Build apenas Windows
make build-clean         # Clean build para todas as plataformas

# Build rápido
make quick               # Build rápido todas as plataformas
make quick-macos         # Build rápido macOS
make quick-windows       # Build rápido Windows
```

### GitHub Actions Workflows

#### Workflow macOS (`.github/workflows/build-macos.yml`)
- **Triggers**: 
  - Push em `main` com mudanças em `pyproject.toml`
  - Tags `v*`
  - Workflow manual
- **Funcionalidades**:
  - Detecção automática de mudanças de versão
  - Build do executável `.app`
  - Criação do instalador `.dmg`
  - Upload de artifacts
  - Release automático no GitHub

#### Workflow Windows (`.github/workflows/build-windows.yml`)
- **Triggers**:
  - Push em `main` com mudanças em `pyproject.toml`
  - Tags `v*`
  - Workflow manual
- **Funcionalidades**:
  - Detecção automática de mudanças de versão
  - Build do executável `.exe`
  - Criação do instalador ZIP
  - Upload de artifacts
  - Release automático no GitHub

### Fluxo de Release Automatizado

1. **Desenvolvedor executa**: `make release-patch`
2. **Makefile**:
   - Incrementa versão no `pyproject.toml`
   - Commit e push das mudanças
3. **GitHub Actions detecta**:
   - Mudança em `pyproject.toml`
   - Inicia builds para Windows e macOS
4. **Workflows executam**:
   - Build dos executáveis
   - Criação dos instaladores
   - Upload dos artifacts
   - Criação do release no GitHub

## Arquitetura de Dados

### Banco de Dados
- **SQLite**: Banco de dados local para logging
  - Armazenamento de histórico de mensagens
  - Analytics e métricas de performance
  - Configurações de usuário
  - Cache de templates

### Formatos de Arquivo Suportados
- **CSV**: Comma-separated values
- **TSV**: Tab-separated values
- **Excel**: .xlsx e .xls
- **JSON**: JavaScript Object Notation
- **JSONL**: JSON Lines (newline-delimited JSON)
- **YAML**: Configurações e templates

## Configuração de Desenvolvimento

### Estrutura de Projeto
```
src/multichannel_messaging/
├── core/                    # Lógica de negócio
├── gui/                     # Interface do usuário
├── services/                # Integrações externas
├── utils/                   # Utilitários
└── localization/            # Traduções
```

### Configuração de Build
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "multichannel-messaging"
version = "1.0.4"
requires-python = ">=3.8"
```

### Configuração de Qualidade
```toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
```

## Restrições e Limitações

### Dependências de Sistema
- **Microsoft Outlook**: Deve estar instalado e configurado
- **Navegador Web**: Para automação do WhatsApp Web
- **Permissões macOS**: Automation permissions necessárias

### Limitações Técnicas
- **WhatsApp Web**: Dependente de estabilidade do navegador
- **Rate Limiting**: Limitações impostas pelos serviços externos
- **Encoding**: Suporte limitado a alguns encodings específicos

### Requisitos de Sistema
- **Windows**: 10 ou superior
- **macOS**: 10.14 (Mojave) ou superior
- **RAM**: Mínimo 4GB, recomendado 8GB
- **Espaço em Disco**: 500MB para instalação

## Configurações de Produção

### Otimizações
- **Lazy Loading**: Carregamento sob demanda de recursos
- **Caching**: Cache inteligente de templates e configurações
- **Memory Management**: Limpeza automática de memória
- **Connection Pooling**: Reutilização de conexões

### Monitoramento
- **Health Checks**: Verificações automáticas de saúde
- **Performance Metrics**: Coleta de métricas de performance
- **Error Tracking**: Rastreamento detalhado de erros
- **Usage Analytics**: Analytics de uso da aplicação

### Segurança
- **Input Validation**: Validação rigorosa de todas as entradas
- **Secure Storage**: Armazenamento seguro de configurações
- **Audit Logging**: Log de auditoria para ações críticas
- **Data Encryption**: Criptografia de dados sensíveis
