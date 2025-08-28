# Q Learning - CSC-Reach

## Contexto do Projeto

CSC-Reach é uma aplicação desktop multiplataforma para comunicação em massa através de integração com Microsoft Outlook e WhatsApp Web. O projeto utiliza Python com PySide6 e segue arquitetura MVC com padrões de design bem estabelecidos.

## Estilo de Trabalho e Preferências

### Abordagem de Desenvolvimento
- **Documentação Estruturada**: Preferência por documentação organizada em hierarquias claras (project-intelligence, generated-docs, user/dev docs)
- **Consolidação sobre Duplicação**: Eliminar redundâncias e manter single source of truth
- **Padrões Estabelecidos**: Seguir arquiteturas MVC, Strategy Pattern, Observer Pattern consistentemente
- **Qualidade de Código**: Emphasis em testes, logging estruturado, tratamento de erros robusto

### Organização de Documentação
- **Separação Clara**: User docs vs developer docs vs project intelligence
- **Foco no Usuário**: Documentação orientada a casos de uso práticos
- **Exemplos Práticos**: Preferência por código funcional e implementações reais
- **Manutenibilidade**: Estruturas que facilitam atualizações futuras

### Tecnologias e Ferramentas
- **Stack Principal**: Python 3.8+, PySide6, pandas, PyInstaller
- **Integrações**: Microsoft Outlook (COM/AppleScript), WhatsApp Web automation
- **Qualidade**: Black, flake8, mypy, pytest, bandit
- **Build**: PyInstaller para executáveis multiplataforma

## Colaboração e Assistência

### Tipos de Ajuda Mais Relevantes
1. **Arquitetura e Design Patterns**: Orientação sobre implementação de novos componentes seguindo padrões estabelecidos
2. **Consolidação de Documentação**: Identificar redundâncias e oportunidades de melhoria
3. **Qualidade de Código**: Sugestões para manter padrões de desenvolvimento
4. **Cross-Platform Development**: Considerações para Windows e macOS

### Contexto Técnico Importante
- **Padrões MVC**: Separação clara entre core/, gui/, services/
- **Strategy Pattern**: Implementações específicas por plataforma (Windows COM vs macOS AppleScript)
- **Observer Pattern**: Sistema de eventos para atualizações de progresso
- **Template Management**: Sistema profissional com categorias, import/export, analytics
- **Multi-Format Processing**: CSV, Excel, JSON, JSONL, TSV com detecção automática

## Otimização de Tokens

### Informações Essenciais para Contexto
- **Estrutura do Projeto**: src/multichannel_messaging/ com core/, gui/, services/, utils/
- **Documentação Oficial**: .amazonq/rules/project-intelligence/ contém arquitetura, progresso, guias
- **User vs Developer**: docs/user/ para usuários finais, docs/dev/ para desenvolvedores
- **Generated Docs**: generated-docs/ para documentação técnica estruturada

### Referências Rápidas
- **Backend Development**: Consultar guia-backend-dev.md para novos serviços/processadores
- **Frontend Development**: Consultar guia-frontend-dev.md para novos componentes GUI
- **Architecture**: arquitetura.md para padrões e componentes principais
- **Progress**: progresso.md para status atual e funcionalidades implementadas

## Insights de Interações

### Padrões de Trabalho Observados
- **Documentação First**: Sempre criar/atualizar documentação junto com código
- **Consolidação Proativa**: Identificar e eliminar duplicações regularmente
- **Estrutura Hierárquica**: Preferência por organização clara e navegável
- **Exemplos Práticos**: Documentação deve incluir código funcional e casos de uso reais

### Preferências de Comunicação
- **Direto e Conciso**: Respostas focadas no essencial sem verbosidade
- **Estruturado**: Informações organizadas em seções claras
- **Acionável**: Instruções práticas com passos específicos
- **Contextual**: Considerar sempre o contexto do projeto CSC-Reach

### Áreas de Foco Recorrentes
1. **Qualidade da Documentação**: Manter padrões altos e consistência
2. **Arquitetura Limpa**: Seguir padrões estabelecidos em novas implementações
3. **User Experience**: Documentação acessível para usuários não-técnicos
4. **Developer Experience**: Guias completos para onboarding de desenvolvedores

## Contexto de Negócio

### Objetivo do Projeto
Facilitar comunicação empresarial em massa através de automação inteligente, integrando nativamente com ferramentas existentes (Outlook, WhatsApp Web) para campanhas personalizadas e profissionais.

### Usuários Alvo
- **Usuários Finais**: Profissionais de marketing, vendas, comunicação corporativa
- **Desenvolvedores**: Equipe técnica trabalhando em backend/frontend
- **Administradores**: Responsáveis por deployment e manutenção

### Características Técnicas Importantes
- **Cross-Platform**: Windows e macOS com integrações nativas específicas
- **Multi-Channel**: Email (Outlook) e WhatsApp Web em plataforma unificada
- **Professional Grade**: Sistema de templates, analytics, logging, configuração robusta
- **User-Friendly**: Interface intuitiva com internacionalização completa (EN/PT/ES)
