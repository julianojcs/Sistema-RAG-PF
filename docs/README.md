# 📚 Documentação Técnica - Sistema RAG PF

Este diretório contém toda a documentação técnica e guias do projeto.

## 📁 Arquivos Disponíveis

### 📋 [CHANGELOG.md](./CHANGELOG.md)
**Histórico detalhado de mudanças do projeto**
- Todas as versões e releases documentadas
- Categorização por tipo de mudança (Adicionado, Modificado, Corrigido)
- Métricas de performance e melhorias
- Roadmap futuro detalhado

### 🏗️ [ARCHITECTURE.md](./ARCHITECTURE.md)
**Documentação técnica detalhada do sistema**
- Arquitetura modular e decisões de design
- Log histórico de implementações
- Análise de trade-offs e métricas
- Roadmap técnico futuro

### 📝 [DOCUMENTATION_GUIDE.md](./DOCUMENTATION_GUIDE.md)
**Guia para manutenção da documentação**
- Estrutura de documentação unificada
- Templates e exemplos práticos
- Fluxo de trabalho para atualizações
- Diretrizes e boas práticas

### 🔧 [TECHNICAL_OVERVIEW.md](./TECHNICAL_OVERVIEW.md)
**Visão geral técnica detalhada**
- Pipeline PF-específico com parsing hierárquico
- Backends de banco vetorial (FAISS/Qdrant)
- Integração Docling para extração layout-aware
- Sistema de rebuild incremental

### 📊 [sgp_calibration.md](./sgp_calibration.md)
**Calibração e métricas do sistema**
- Metodologia de avaliação
- Benchmarks de performance
- Métricas de qualidade das respostas

## 🎯 Como Usar Esta Documentação

### Para Desenvolvedores
1. **Começar por**: [ARCHITECTURE.md](./ARCHITECTURE.md) - Entender a arquitetura atual
2. **Ver histórico**: [CHANGELOG.md](./CHANGELOG.md) - Evolução do sistema
3. **Detalhes técnicos**: [TECHNICAL_OVERVIEW.md](./TECHNICAL_OVERVIEW.md) - Pipeline PF e integrações
4. **Implementar mudanças**: Seguir [DOCUMENTATION_GUIDE.md](./DOCUMENTATION_GUIDE.md)
5. **Documentar**: Usar templates do guia de documentação

### Para Novos Integrantes da Equipe
1. **Visão geral**: [../README.md](../README.md) - Entender o projeto
2. **Histórico**: [CHANGELOG.md](./CHANGELOG.md) - Ver evolução detalhada do sistema
3. **Arquitetura**: [ARCHITECTURE.md](./ARCHITECTURE.md) - Detalhes técnicos
4. **Pipeline PF**: [TECHNICAL_OVERVIEW.md](./TECHNICAL_OVERVIEW.md) - Funcionalidades específicas
5. **Contribuição**: [DOCUMENTATION_GUIDE.md](./DOCUMENTATION_GUIDE.md) - Como documentar

### Para Gestores e Stakeholders
1. **Funcionalidades**: [../README.md](../README.md) - O que o sistema faz
2. **Releases**: [CHANGELOG.md](./CHANGELOG.md) - O que foi entregue e roadmap
3. **Decisões técnicas**: [ARCHITECTURE.md](./ARCHITECTURE.md) - Próximos passos técnicos
4. **Métricas**: [sgp_calibration.md](./sgp_calibration.md) - Performance e qualidade

## � Funcionalidades Principais

### RAG PF-Específico
- **Pipeline hierárquico**: Parsing estruturado de normas (Art., §, Incisos, Alíneas)
- **Offline-first**: Execução 100% local via Ollama
- **Dual backend**: FAISS (rápido) ou Qdrant (recursos avançados)
- **Docling**: Extração layout-aware com detecção de tabelas e bbox

### Interface Web Moderna
- **Streamlit**: Interface web responsiva
- **Upload PDFs**: Envio direto pela interface
- **Reindex incremental**: Detecção automática de mudanças via manifest
- **Preview retrieval**: Visualização de trechos relevantes com páginas e tabelas

### Auditoria e Qualidade
- **Export JSONL**: Auditoria completa dos chunks com layout_refs
- **Cache inteligente**: Respostas persistidas com clear automático pós-rebuild
- **Monitoramento**: Status Ollama e métricas em tempo real
- Novas implementações técnicas
- Decisões de design importantes
- Lições aprendidas relevantes

## 📞 Suporte

Para dúvidas sobre a documentação técnica:
1. Consulte os arquivos específicos acima
2. Verifique o [guia de documentação](./DOCUMENTATION_GUIDE.md)
3. Entre em contato com a equipe técnica

---

**Mantido pela equipe de desenvolvimento do Sistema RAG PF** 🇧🇷
