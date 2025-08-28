# 🧩 Inspetor de Chunks - Interface Web

## 📋 Visão Geral

A nova funcionalidade **Inspetor de Chunks** foi adicionada à interface web do Sistema RAG-PF, permitindo visualizar e explorar detalhadamente os chunks armazenados no banco Qdrant através de uma interface moderna e intuitiva.

## 🚀 Como Acessar

1. **Inicie a aplicação web:**
   ```bash
   python -m streamlit run web/app.py
   ```

2. **Acesse no navegador:** http://localhost:8501

3. **Navegue para a aba:** 🧩 **Inspetor de Chunks**

## 🎯 Funcionalidades

### 📊 **Dashboard de Métricas**
- **Total de Chunks**: Quantidade total indexada
- **Tamanho do Banco**: Tamanho em MB do banco Qdrant
- **Dimensões do Vetor**: Dimensionalidade dos embeddings (768D)
- **Distância**: Método de cálculo de similaridade (Cosine)

### 🔍 **Filtros de Busca Avançados**

#### **Por Nível Hierárquico:**
- Artigo
- Parágrafo
- Inciso
- Alínea
- Item

#### **Por Documento:**
- Busca parcial no nome do arquivo
- Ex: "LEI 8112", "Emenda Constitucional"

#### **Por Rótulo:**
- Busca exata do rótulo do elemento
- Ex: "Art. 1º", "§ 2º", "I", "a)"

#### **Controles de Visualização:**
- **Limite de Resultados**: 1-50 chunks
- **Texto Completo**: Ver chunks sem truncamento
- **Busca Automática**: Buscar ao alterar filtros

### 🎨 **Design Moderno dos Cards**

#### **Header do Card:**
- 🧩 **Título**: Nível + Rótulo (ex: "Artigo Art. 1º")
- 📊 **Métricas**: Tokens estimados e tamanho em caracteres

#### **Informações Principais:**
- 📁 **Documento**: Nome do arquivo PDF origem
- 📄 **Páginas**: Quantidade de páginas no documento
- 🗂️ **Caminho Hierárquico**: Breadcrumb navegável
- 🆔 **ID Técnico**: Hash único do chunk
- 🔢 **Vector**: Dimensionalidade do embedding
- 💾 **Tamanho**: Tamanho do BLOB em bytes
- 🏛️ **Órgão**: Instituição responsável

#### **Conteúdo:**
- 📄 **Texto**: Preview ou texto completo
- 🔍 **Metadados Detalhados**: Expandível com categorias:
  - **Identificação**: IDs e hashes
  - **Hierarquia**: Estrutura normativa
  - **Processamento**: Versão do parser, tokens
  - **Institucional**: Órgão, âmbito, país
  - **Temporal**: Datas de publicação e vigência
  - **Documental**: Tipo de norma, número, fonte

## 💡 **Casos de Uso**

### 🔧 **Para Desenvolvedores:**
- **Debug**: Verificar se chunks foram indexados corretamente
- **Análise**: Entender a estrutura dos dados
- **Otimização**: Avaliar tamanho e qualidade dos chunks
- **Auditoria**: Validar metadados e hierarquia

### 👥 **Para Usuários Finais:**
- **Exploração**: Navegar pela base de conhecimento
- **Verificação**: Confirmar presença de documentos específicos
- **Análise**: Entender como o sistema organiza os dados
- **Pesquisa**: Encontrar chunks específicos por critérios

### 📊 **Para Administradores:**
- **Monitoramento**: Verificar saúde da base de dados
- **Estatísticas**: Métricas de indexação e uso
- **Manutenção**: Identificar problemas de dados
- **Planejamento**: Avaliar crescimento da base

## 🎨 **Características do Design**

### 🌟 **Interface Moderna:**
- **Cards Responsivos**: Layout adaptável
- **Métricas Visuais**: Informações destacadas
- **Cores Organizadas**: Categorização visual
- **Expansibilidade**: Detalhes sob demanda

### ⚡ **Performance Otimizada:**
- **Cache Inteligente**: Dados temporariamente armazenados
- **Busca Limitada**: Máximo 1000 pontos por busca
- **Carregamento Progressivo**: Interface responsiva
- **Fallbacks**: Amostras quando sem resultados

### 🛡️ **Robustez:**
- **Tratamento de Erros**: Mensagens claras
- **Validação**: Filtros e entradas verificadas
- **Fallbacks**: Alternativas quando dados indisponíveis
- **Debugging**: Informações técnicas disponíveis

## 🔗 **Integração com Sistema**

### 🔄 **Sincronização:**
- **Automática**: Reflete mudanças na base Qdrant
- **Cache**: Atualização periódica (5 minutos TTL)
- **Consistency**: Dados sempre atualizados

### 🎯 **Compatibilidade:**
- **Backend Qdrant**: Funciona com base atual
- **Metadados PF**: Suporte completo aos campos específicos
- **Multi-documento**: Suporta múltiplos PDFs indexados
- **Hierarquia Completa**: Todos os níveis normativos

## 📈 **Benefícios**

### ✅ **Para o Sistema:**
- **Transparência**: Visualização interna dos dados
- **Debug**: Identificação rápida de problemas
- **Qualidade**: Verificação de integridade dos chunks
- **Confiança**: Usuários podem verificar a base

### ✅ **Para os Usuários:**
- **Compreensão**: Entender como o RAG funciona
- **Controle**: Verificar se documentos estão indexados
- **Exploração**: Navegar pela base de conhecimento
- **Confiabilidade**: Ver exatamente o que o sistema sabe

---

**Acesse agora:** http://localhost:8501 → Aba "🧩 Inspetor de Chunks" 🎉
