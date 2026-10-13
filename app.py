import os
import zipfile
import tempfile
import fnmatch
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="ZIP to LLM RAG Generator",
    page_icon="📦",
    layout="wide"
)

# Pastas e arquivos comuns a serem ignorados para manter o contexto limpo
DEFAULT_IGNORE_PATTERNS = [
    "*.pyc", "*.pyo", "*.pyd", "__pycache__", ".git", ".svn", ".hg",
    "node_modules", "venv", "env", ".env", "dist", "build",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.pdf", "*.zip",
    "*.tar", "*.gz", "*.rar", "*.exe", "*.dll", "*.so", "*.DS_Store"
]

def should_ignore(path, patterns):
    """Verifica se o arquivo ou pasta deve ser ignorado com base nos padrões."""
    name = os.path.basename(path)
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(path, pattern):
            return True
    return False

def generate_tree(startpath, prefix="", ignore_patterns=DEFAULT_IGNORE_PATTERNS):
    """Gera uma representação em árvore de diretórios em texto."""
    tree_str = ""
    try:
        contents = sorted(os.listdir(startpath))
    except PermissionError:
        return ""

    # Filtrar itens ignorados
    valid_contents = []
    for item in contents:
        full_path = os.path.join(startpath, item)
        if not should_ignore(full_path, ignore_patterns):
            valid_contents.append(item)

    # Linha corrigida (sem artefatos estranhos)
    pointers = [ "├── " ] * (len(valid_contents) - 1) + [ "└── " ] if valid_contents else []
    
    for pointer, item in zip(pointers, valid_contents):
        full_path = os.path.join(startpath, item)
        tree_str += f"{prefix}{pointer}{item}\n"
        if os.path.isdir(full_path):
            extension = "│   " if pointer == "├── " else "    "
            tree_str += generate_tree(full_path, prefix + extension, ignore_patterns)
            
    return tree_str

def is_text_file(file_path):
    """Tenta detectar se o arquivo é de texto para evitar leitura de binários."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except UnicodeDecodeError:
        return False

def build_rag_context(extract_path, ignore_patterns):
    """Constrói o documento consolidado de contexto para a LLM."""
    markdown_content = "# Contexto do Repositório / Projeto\n\n"
    
    # 1. Adicionar Estrutura de Diretórios
    markdown_content += "## 1. Estrutura de Diretórios\n\n```text\n"
    markdown_content += "project_root/\n"
    markdown_content += generate_tree(extract_path, "", ignore_patterns)
    markdown_content += "```\n\n---\n\n"
    
    # 2. Adicionar Conteúdo dos Arquivos
    markdown_content += "## 2. Conteúdo dos Arquivos\n\n"
    
    for root, dirs, files in os.walk(extract_path):
        # Modificar dirs in-place para ignorar pastas indesejadas na varredura
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d), ignore_patterns)]
        
        for file in files:
            file_path = os.path.join(root, file)
            if should_ignore(file_path, ignore_patterns):
                continue
                
            if is_text_file(file_path):
                rel_path = os.path.relpath(file_path, extract_path)
                ext = os.path.splitext(file)[1].lstrip('.')
                lang_map = {
                    'py': 'python', 'js': 'javascript', 'ts': 'typescript',
                    'html': 'html', 'css': 'css', 'json': 'json', 'md': 'markdown',
                    'yml': 'yaml', 'yaml': 'yaml', 'sh': 'bash', 'sql': 'sql',
                    'rs': 'rust', 'go': 'go', 'java': 'java', 'cpp': 'cpp'
                }
                lang = lang_map.get(ext.lower(), '')
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    markdown_content += f"### Arquivo: `{rel_path}`\n\n"
                    markdown_content += f"```{lang}\n{content}\n```\n\n"
                except Exception as e:
                    markdown_content += f"### Arquivo: `{rel_path}`\n\n*Erro ao ler o arquivo: {str(e)}*\n\n"
                    
    return markdown_content

# --- Interface Streamlit ---
st.title("📦 ZIP para RAG LLM Context Generator")
st.markdown("Faça o upload de um arquivo `.zip` contendo o código-fonte da sua aplicação. O sistema vai extrair, mapear a árvore de diretórios e consolidar todo o conteúdo em um único arquivo Markdown otimizado para alimentar LLMs.")

uploaded_file = st.file_uploader("Escolha um arquivo ZIP", type=["zip"])

if uploaded_file is not None:
    with st.spinner("Processando o arquivo ZIP e gerando o RAG..."):
        # Criar diretório temporário para extração
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            extract_path = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_path, exist_ok=True)
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            except zipfile.BadZipFile:
                st.error("O arquivo enviado não é um arquivo ZIP válido.")
                st.stop()
                
            # Gerar o RAG
            rag_output = build_rag_context(extract_path, DEFAULT_IGNORE_PATTERNS)
            
            st.success("RAG gerado com sucesso!")
            
            # Opções de visualização e download
            st.text_area("Pré-visualização do RAG gerado:", value=rag_output[:3000] + "\n\n... [Visualização truncada para exibição]", height=250)
            
            st.download_button(
                label="📥 Baixar arquivo RAG (.md)",
                data=rag_output,
                file_name="project_llm_context.md",
                mime="text/markdown"
            )
