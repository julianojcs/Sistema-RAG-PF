## 📋 Resumo Completo: Como Funciona a Hierarquização no seu Sistema RAG

Com base na análise do código e do arquivo desserializado, aqui está a explicação completa sobre como é feita a criação de chunks com hierarquização:

### 🔄 **Como é Feita a Criação de Chunks**

1. **📄 Extração PDF**: O sistema usa **Docling** para extrair texto e layout dos PDFs
2. **🧹 Normalização**: Remove headers/footers, corrige hifenização (normalize.py)
3. **🔍 Parsing Hierárquico**: Usa regex para detectar estrutura jurídica (parse_norma.py)
4. **✂️ Chunking Inteligente**: Cria chunks respeitando limites de tokens e hierarquia (chunker.py)
5. **🧠 Vetorização**: Gera embeddings de 768 dimensões
6. **💾 Indexação**: Armazena no Qdrant com metadados ricos

### 🏗️ **Estrutura Hierárquica Detectada**

O sistema reconhece a seguinte hierarquia jurídica:
```
documento → parte → livro → título → capítulo → seção → subsecao →
artigo → parágrafo → inciso → alínea → item → anexo
```

### 📍 **Onde a Hierarquia é Salva**

A hierarquia é armazenada no **Qdrant** em múltiplos locais:

1. **Banco Principal**: pf_normativos
2. **Metadados do Chunk**: Cada chunk contém:
   - `caminho_hierarquico`: breadcrumb completo
   - `parent_id`: referência ao pai
   - `siblings_prev_id/next_id`: navegação horizontal
   - `anchor_id`: identificador único e SEO-friendly

### 🎯 **Para Que Servem os Metadados**

Os metadados têm múltiplas funções críticas:

#### 🧭 **Navegação Hierárquica**
- **Breadcrumb**: "Capítulo I > Art. 5º > § 1º > a)"
- **Relações Familiares**: parent-child, siblings
- **Contexto**: permite expandir/contrair níveis

#### 🔍 **Busca Inteligente**
- **Filtros Estruturais**: busca por "Art. 5º", "§ 1º"
- **Escopo**: documentos específicos ou tipo de norma
- **Rastreabilidade**: volta ao PDF original

#### 🏛️ **Compliance Institucional**
- **Órgão**: Polícia Federal (DPF)
- **Unidade**: DG/DPF, SR/PF-SP, etc.
- **Tipo**: Portaria, Instrução Normativa, etc.
- **Temporal**: datas de publicação/vigência

#### 📊 **Controle de Qualidade**
- **Versionamento**: `versao_parser: "1.0.0"`
- **Integridade**: hash para detectar mudanças
- **Performance**: `tokens_estimados` para otimização

#### 🎨 **Layout Intelligence**
- **Tabelas**: `layout_refs` evita cortes ruins
- **Páginas**: localização no PDF original
- **Estrutural**: preserva formatação importante

### 💡 **Casos de Uso Práticos**

1. **"Mostre o Art. 5º da Portaria 123"** → filtro por `nivel + rotulo`
2. **"Contexto do §1º"** → usar `parent_id` para pegar artigo pai
3. **"Próximo dispositivo"** → usar `siblings_next_id`
4. **"Documentos da DG/DPF"** → filtro por `unidade_emitente`
5. **"Tabelas do Capítulo II"** → filtro por `nivel + layout_refs`

### 🚀 **Vantagens do Sistema**

- **🎯 Precisão**: busca específica por dispositivos jurídicos
- **🧭 Contexto**: navegação natural pela estrutura normativa
- **📊 Layout**: preservação de tabelas e formatação
- **🏛️ Compliance**: metadados específicos da Polícia Federal
- **🔍 Auditoria**: rastreabilidade completa ao documento fonte
- **⚡ Performance**: chunks otimizados por estrutura jurídica

Este sistema permite que o RAG entenda não apenas o **conteúdo** dos documentos, mas também sua **estrutura jurídica**, possibilitando buscas muito mais precisas e contextualmente relevantes para o domínio da Polícia Federal.