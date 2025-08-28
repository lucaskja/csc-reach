# Q Developer - Prompts

## 1) Criar documentação

###  1.1) Salvar no local adequado

Crie esta regra e salve em .amazonq/rules no seu projeto ou adicione ao /context do seu /agent no CLI

#### Arquivos de Aprendizado do Amazon Q

Este documento explica a convenção padronizada de nomenclatura para arquivos de aprendizado do Amazon Q em diferentes projetos e diretórios.


## Convenção de Nomenclatura

Todos os arquivos de aprendizado do Amazon Q seguem este padrão de nomenclatura:

```
q-learning-{contexto}.md
```


Onde `{contexto}` é um descritor do projeto ou área (por exemplo, "datalake", "streaming", "geral").


## Localização dos Arquivos

|	|	|	|
|---	|---	|---	|
|	|	|	|
|	|	|	|
|	|	|	|



## Objetivo

Esses arquivos servem como uma base de conhecimento para o Amazon Q:


1. Entender melhor seu estilo de trabalho e preferências
2. Melhorar a colaboração e assistência
3. Fornecer ajuda mais relevante e contextual
4. Otimizar o uso de tokens da CLI do Q mantendo o contexto

## Uso

Ao trabalhar com o Amazon Q em um contexto de projeto específico, ele automaticamente referenciará o arquivo de aprendizado relevante para fornecer assistência mais personalizada.

Você pode atualizar esses arquivos manualmente ou pedir ao Amazon Q para atualizá-los com novos insights de suas interações.


## Formato

Todos os arquivos usam o formato Markdown (.md) para:

* Melhor estrutura e legibilidade
* Suporte para formatação rica (cabeçalhos, listas, blocos de código)
* Compatibilidade com sistemas de controle de versão
* Fácil visualização na maioria dos editores de texto e ferramentas de documentação

## Diretrizes de Atualização

Ao atualizar arquivos q-learning:

* PRESERVE a estrutura e o conteúdo existentes
* ADICIONE novos aprendizados às seções apropriadas em vez de reformatar o documento inteiro
* MANTENHA a organização e formatação estabelecidas
* ESTENDA as seções existentes com novos insights em vez de substituí-las
* RESPEITE a estrutura original e o fluxo do documento



### 1.2) Gerar documentação



#### Você é um escritor técnico experiente e engenheiro de software especialista.

Sua tarefa é criar um sistema de documentação estruturado e abrangente que permita ao Amazon Q Developer manter o contexto entre as sessões. Isso transforma o Amazon Q Developer de um assistente sem estado em um parceiro de desenvolvimento persistente que pode efetivamente lembrar detalhes do projeto ao longo do tempo.


## Detalhes

### Arquivos Principais

O sistema de documentação consiste na seguinte hierarquia de arquivos, todos em formato Markdown:


```
flowchart TD
    P[projeto.md]
    P --> A[arquitetura.md]
    P --> T[pilha-tecnica.md]
    P --> PS[progresso.md]
```



#### projeto.md

* Explica por que este projeto existe
* Descreve o problema sendo resolvido
* Descreve como o projeto deve funcionar
* Contém uma visão geral de alto nível do que está sendo desenvolvido
* Descreve requisitos e objetivos principais

#### arquitetura.md

* Documenta a arquitetura do sistema descrevendo a estrutura do sistema e as características arquitetônicas que o sistema deve suportar
* Registra princípios-chave de design
* Lista padrões de design sendo utilizados
* Explica relacionamentos entre componentes

#### pilha-tecnica.md

* Descreve tecnologias e frameworks sendo utilizados
* Documenta a configuração de desenvolvimento e configurações de ferramentas
* Registra restrições conhecidas

#### progresso.md

* Acompanha o que funciona e o que ainda precisa ser construído
* Registra o status atual das funcionalidades
* Lista problemas conhecidos e limitações a serem melhoradas no futuro

### Passos

Estes são os passos obrigatórios para completar as tarefas:


1. Criar uma nova pasta `project-intelligence` dentro da pasta `.amazonq/rules`
2. Analisar a aplicação para obter um entendimento abrangente do projeto
3. Analisar o histórico do git para entender o estado atual do desenvolvimento
4. Criar o arquivo projeto.md
5. Criar o arquivo arquitetura.md
6. Criar o arquivo pilha-tecnica.md
7. Criar o arquivo progresso.md

### Formato de Saída

* Todos os arquivos devem ser formatados em markdown
* Usar sintaxe mermaid para aspectos como visualizações de arquitetura, fluxos de usuário ou relacionamentos entre componentes

## Verificação

Depois de concluído, revise todos os arquivos para confirmar que a documentação é significativa, abrangente e cumpre o objetivo descrito. Se não for o caso, continue iterando nos passos e revise novamente até considerar que a tarefa está completa.


### 1.3) Diagramas adicionais

#### 1.3.1) Projeto

Crie um diagrama de projeto usando o modelo C4 para o projeto CSC-Reach, contendo os seguintes diagramas: contexto do sistema, container, componente e código. Além disso, crie um diagrama de sequência usando PlantUML baseado no código Python do diretório especificado. O projeto é uma aplicação desktop Python que utiliza PySide6 como framework GUI e interage com Microsoft Outlook e WhatsApp Web para automação de mensagens. Os diagramas são necessários para documentação e comunicação com stakeholders. Siga estes passos:

1. Crie o diagrama de contexto do sistema para mostrar os limites do projeto CSC-Reach e sua relação com sistemas externos (Outlook, WhatsApp Web).
2. Crie o diagrama de container para ilustrar as principais escolhas tecnológicas (Python, PySide6, SQLite) e como elas interagem.
3. Crie o diagrama de componentes para detalhar os componentes dentro dos containers (core/, gui/, services/) e seus relacionamentos.
4. Crie o diagrama de código para mostrar a estrutura da base de código Python com padrões MVC.
5. Por fim, crie um diagrama de sequência usando PlantUML para representar o fluxo de interação de envio de mensagens.

#### 1.3.2) Dados

Crie uma documentação abrangente para o sistema de dados do projeto CSC-Reach localizado no diretório especificado. A documentação deve incluir diagramas e descrições detalhadas para facilitar a compreensão e manutenção da estrutura de dados. O projeto utiliza SQLite para logging e armazenamento local. Siga estes passos:

1. Crie um diagrama entidade-relacionamento (ER) que mostre todas as tabelas SQLite, suas relações e cardinalidades.
2. Para cada tabela, forneça:
   * Nome da tabela
   * Descrição do propósito da tabela
   * Lista de colunas com:
     * Nome da coluna
     * Tipo de dado SQLite
     * Se é chave primária, chave estrangeira ou índice
     * Descrição do propósito da coluna
     * Quaisquer restrições (por exemplo, NOT NULL, UNIQUE)

3. Documente o sistema de processamento de dados multi-formato:
   * Formatos suportados (CSV, Excel, JSON, JSONL, TSV)
   * Processo de detecção automática de formato
   * Mapeamento de colunas e validação

4. Crie um diagrama de fluxo de dados mostrando como os dados fluem entre importação, processamento, templates e envio.
5. Documente as políticas de backup e limpeza de dados locais.
6. Liste todas as otimizações de performance implementadas (índices, cache, streaming).
7. Descreva os processos de ETL para diferentes formatos de arquivo.
8. Documente as práticas de segurança e proteção de dados pessoais.
9. Crie um glossário de termos de negócio relacionados aos dados de clientes e templates.
10. Inclua informações sobre versionamento de esquema e migrações de dados.

Use ferramentas como dbdiagram.io, Lucidchart ou PlantUML para criar os diagramas necessários.

## 2) Modernização de Aplicação Python Desktop

### Prompt para Evolução de Sistema CSC-Reach

Divida as tarefas. Gere documentos e adicione ao /context ou às /rules a cada fase.

## Objetivo

Criar um plano detalhado e estruturado para evoluir e modernizar a aplicação CSC-Reach, mantendo a funcionalidade existente enquanto implementamos novas funcionalidades e melhorias arquiteturais.

### FASE 1

## Análise Inicial

1. **Avaliação do Sistema Atual**
   * Versão atual do Python e dependências (Python 3.8+, PySide6)
   * Frameworks utilizados e suas versões (pandas, PyInstaller, etc.)
   * Estrutura do projeto (MVC com core/, gui/, services/)
   * Cobertura de testes atual
   * Métricas de qualidade de código (Black, flake8, mypy)
   * Documentação existente

2. **Análise de Complexidade**
   * Identificar componentes complexos no core/
   * Mapear dependências entre gui/ e services/
   * Localizar duplicações de código
   * Avaliar acoplamento entre camadas MVC
   * Identificar violações de padrões estabelecidos

### FASE 2

## Plano de Modernização

### 1. Preparação
* Fortalecer ambiente de CI/CD existente
* Expandir testes automatizados (pytest, pytest-qt)
* Estabelecer métricas de qualidade aprimoradas
* Configurar ferramentas de análise estática (bandit, mypy)
* Documentar APIs internas e comportamentos

### 2. Atualizações Técnicas

```
Sequência de atualizações:
1. Python 3.8 → 3.11 → 3.12
2. PySide6 → versão mais recente
3. Dependências secundárias (pandas, requests)
4. Build system (PyInstaller, packaging)
```

### 3. Refatoração Arquitetural
* Fortalecer arquitetura MVC existente
* Implementar padrões modernos:
  * Clean Architecture para core/
  * Component-based UI para gui/
  * Plugin system para services/
* Introduzir práticas modernas:
  * Async/await para operações I/O
  * Type hints completos
  * Dependency injection
  * Event-driven architecture

### 4. Melhorias de Código
* Aplicar princípios SOLID consistentemente
* Implementar padrões de projeto adequados
* Refatorar para recursos modernos do Python:
  * Dataclasses e Pydantic
  * Context managers
  * Pathlib para manipulação de arquivos
  * F-strings e type annotations

### 5. Observabilidade
* Implementar logging estruturado aprimorado
* Adicionar métricas de performance detalhadas
* Configurar health checks para integrações
* Implementar error tracking
* Melhorar sistema de analytics

### FASE 3

## Estratégia de Implementação

1. **Abordagem Gradual**

```
graph LR
    A[Análise] --> B[Testes]
    B --> C[Refatoração]
    C --> D[Validação]
    D --> E[Deploy]
```

2. **Para Cada Módulo/Componente:**
   * Identificar dependências internas
   * Criar testes de comportamento
   * Refatorar gradualmente
   * Validar funcionalidade
   * Atualizar documentação

## Garantias de Qualidade

1. **Verificações Contínuas**
   * Testes automatizados (pytest suite)
   * Análise de código estática (mypy, bandit)
   * Revisões de código
   * Testes de integração GUI (pytest-qt)
   * Testes de performance

2. **Critérios de Aceitação**
   * Manter comportamento existente
   * Melhorar métricas de código
   * Reduzir complexidade ciclomática
   * Aumentar cobertura de testes
   * Manter ou melhorar performance

## Documentação

1. **Documentar:**
   * Decisões arquiteturais
   * Padrões implementados
   * APIs internas
   * Processos de negócio
   * Configurações do sistema

2. **Manter:**
   * Diagramas de arquitetura atualizados
   * Documentação de API interna
   * Guias de desenvolvimento
   * Procedimentos de build e deploy

## Monitoramento de Progresso

1. **Métricas de Sucesso:**
   * Cobertura de código (>80%)
   * Complexidade ciclomática
   * Acoplamento entre módulos
   * Tempo de build
   * Performance da aplicação

2. **Indicadores de Qualidade:**
   * Bugs reportados pelos usuários
   * Tempo de resolução de issues
   * Facilidade de manutenção
   * Satisfação dos desenvolvedores

## Considerações de Segurança

1. **Implementar:**
   * Análise de dependências (safety, pip-audit)
   * Verificações de segurança (bandit)
   * Validação de entrada robusta
   * Criptografia para dados sensíveis
   * Audit logging

## Entregáveis

1. **Para Cada Fase:**
   * Código refatorado e testado
   * Testes automatizados expandidos
   * Documentação atualizada
   * Métricas de qualidade
   * Relatórios de progresso

## 3) Testes

### 3.1) Analisar cobertura e plano de melhoria

Analise a cobertura de testes atual do projeto CSC-Reach e crie um plano de melhoria:

1. **Análise Atual:**
   * Execute `pytest --cov=src/multichannel_messaging --cov-report=html`
   * Identifique módulos com baixa cobertura
   * Analise tipos de testes existentes (unit, integration, GUI)

2. **Plano de Melhoria:**
   * Priorize componentes críticos (core/, services/)
   * Defina metas de cobertura por módulo
   * Identifique gaps em testes de integração
   * Planeje testes de GUI com pytest-qt

### 3.2) Teste unitário

Implemente testes unitários abrangentes:

```python
# Exemplo para core/template_manager.py
import pytest
from multichannel_messaging.core.template_manager import TemplateManager

class TestTemplateManager:
    def setup_method(self):
        self.manager = TemplateManager()
    
    def test_create_template(self):
        template_data = {
            'name': 'Test Template',
            'category': 'Welcome',
            'content': 'Hello {name}'
        }
        result = self.manager.create_template(template_data)
        assert result.success
        assert result.template_id is not None
```

### 3.3) Testes de integração

Desenvolva testes de integração para workflows completos:

```python
# Exemplo para workflow de envio
def test_complete_messaging_workflow():
    # 1. Import data
    processor = CSVProcessor()
    customers = processor.process_file('test_data.csv')
    
    # 2. Apply template
    template_manager = TemplateManager()
    template = template_manager.get_template('welcome')
    
    # 3. Send messages (mock)
    email_service = MockEmailService()
    results = email_service.send_bulk(customers, template)
    
    assert all(r.success for r in results)
```

### 3.4) TDD (Test-Driven Development)

Implemente TDD para novas funcionalidades:

1. **Red**: Escreva teste que falha
2. **Green**: Implemente código mínimo para passar
3. **Refactor**: Melhore o código mantendo testes passando

```python
# Exemplo TDD para nova funcionalidade
def test_telegram_integration_not_implemented():
    """Test for future Telegram integration"""
    telegram_service = TelegramService()
    with pytest.raises(NotImplementedError):
        telegram_service.send_message("chat_id", "message")
```

