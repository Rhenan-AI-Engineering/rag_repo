# rag_repo
leitura de pasta zipada para criação de rag de um projeto de programação

## Como utilizar:
clone o repositório e no mesmo diretório do clone instale as dependências no seu terminal linux ou windows cmd:

```Bash
pip install streamlit
```

### Execute o aplicativo via terminal:

```Bash
streamlit run app.py
```
Uma aba será aberta no seu navegador. Basta arrastar ou selecionar seu arquivo .zip na interface.

## O script irá:

- Ignorar arquivos desnecessários (node_modules, .git, arquivos binários/imagens, etc.).

- Desenhar a árvore completa de pastas e arquivos.

- Agrupar o path relativo de cada arquivo com seu respectivo conteúdo dentro de blocos de código formatados.

- Disponibilizar um botão para você baixar o arquivo .md resultante, pronto para ser colado ou anexado em qualquer conversa com uma LLM (como Claude, GPT-4, etc.).
