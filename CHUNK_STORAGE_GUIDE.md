## 🧩 COMO OS CHUNKS SÃO ARMAZENADOS NO QDRANT

### 📍 **Localização Física dos Chunks:**
```
qdrantDB/
├── meta.json                              # ⚙️ Configuração da coleção
└── collection/
    └── pf_normativos/                     # 📁 Coleção dos chunks
        ├── storage.sqlite                 # 🗃️ CHUNKS ARMAZENADOS AQUI
        └── storage.sqlite-x-points-1-point.bin  # 🔍 Índice binário
```

### 🏗️ **Estrutura de Armazenamento:**

#### **1. Tabela SQLite (`storage.sqlite`)**
```sql
CREATE TABLE points (
    id TEXT,        -- 🆔 ID único do chunk (hash MD5 encoded)
    point BLOB      -- 🧩 CHUNK COMPLETO (serializado com pickle)
);
```

#### **2. Estrutura de Cada CHUNK (PointStruct)**
```python
PointStruct {
    🆔 id: "hash_md5_unico"
    🔢 vector: [768 dimensões float32]  # Embedding do texto
    📋 payload: {
        📄 page_content: "texto_do_chunk"    # CONTEÚDO PRINCIPAL
        📊 metadata: {
            # === IDENTIFICAÇÃO ===
            🆔 doc_id: "documento-pf"
            🏷️ anchor_id: "documento-pf-artigo-1-paragrafo-2"

            # === HIERARQUIA NORMATIVA ===
            🏗️ nivel: "artigo" | "paragrafo" | "inciso" | "alinea"
            🏷️ rotulo: "Art. 1º", "§ 2º", "I", "a)"
            📊 ordinal_normalizado: "1", "2", "I", "A"
            🗂️ caminho_hierarquico: [
                {"nivel": "artigo", "rotulo": "Art. 1º"},
                {"nivel": "paragrafo", "rotulo": "§ 2º"}
            ]

            # === NAVEGAÇÃO ===
            👆 parent_id: "id_do_elemento_pai"
            ⬅️ siblings_prev_id: "id_anterior"
            ➡️ siblings_next_id: "id_proximo"

            # === ORIGEM ===
            📁 origem_pdf: {
                📄 arquivo: "SGP\\LEI 8112.pdf"
                📄 paginas: [1, 2, 3, ...]
            }

            # === MÉTRICAS ===
            🔤 tokens_estimados: 150
            🔐 hash_conteudo: "sha256_do_texto"
            ✅ texto_limpo: true
            📌 versao_parser: "1.0.0"

            # === METADADOS PF ===
            🏛️ orgao: "Polícia Federal"
            🏷️ sigla_orgao: "DPF"
            🌍 ambito: "federal"
            🇧🇷 pais: "Brasil"
            📅 data_publicacao: "2019-11-12"
            📋 especie_normativa: "lei"
            🔢 numero: "8112"
            📊 situacao: "vigente"

            # === LAYOUT DOCLING ===
            📐 layout_refs: [
                {
                    "page": 1,
                    "bbox": [x1, y1, x2, y2],
                    "type": "text" | "table" | "heading"
                }
            ]
        }
    }
}
```

### 🔍 **Como Visualizar os Chunks:**

#### **Análise Estrutural:**
```bash
# Ver estrutura geral dos chunks
python show_points.py --mode chunks

# Ver exemplos detalhados
python show_points.py --mode examples

# Análise completa
python show_points.py --mode all
```

#### **Estatísticas dos Chunks:**
- **📊 Total**: 7.954 chunks indexados
- **💾 Tamanho médio**: ~8.5KB por chunk
- **📄 Texto médio**: 83-273 caracteres
- **🔢 Embedding**: 768 dimensões (nomic-embed-text)
- **🏗️ Tipos**: artigo, parágrafo, inciso, alínea

### 📋 **Campos Principais dos Chunks:**

#### **🔝 Nível Raiz (payload):**
- `page_content`: Texto principal do chunk
- `metadata`: Todos os metadados estruturados

#### **🏷️ Metadados Hierárquicos:**
- `nivel`, `rotulo`, `caminho_hierarquico`: Estrutura normativa
- `parent_id`, `siblings_*`: Navegação entre elementos
- `tokens_estimados`: Tamanho em tokens

#### **📁 Metadados de Origem:**
- `origem_pdf`: Arquivo e páginas de origem
- `hash_conteudo`: Integridade do chunk
- `layout_refs`: Posição no PDF (Docling)

#### **🏛️ Metadados PF:**
- `orgao`, `sigla_orgao`: Instituição
- `data_publicacao`, `situacao`: Status temporal
- `especie_normativa`, `numero`: Identificação legal

### 🎯 **Como o Sistema Usa os Chunks:**

1. **🔍 Busca Semântica**: Embeddings (768D) para similaridade
2. **📋 Retrieval**: Metadados para filtros e ranking
3. **🗂️ Breadcrumbs**: Caminho hierárquico para navegação
4. **📄 Context**: page_content como resposta base
5. **🔗 Navegação**: IDs para relacionamentos entre chunks

### 💡 **Vantagens desta Estrutura:**

- ✅ **Hierarquia Preservada**: Estrutura legal mantida
- ✅ **Navegação Rica**: Links entre elementos
- ✅ **Rastreabilidade**: Origem até o PDF
- ✅ **Flexibilidade**: Metadados extensíveis
- ✅ **Performance**: Embeddings otimizados para busca
- ✅ **Auditoria**: Hashes e versioning completo
