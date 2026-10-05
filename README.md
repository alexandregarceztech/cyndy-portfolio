# Portfólio Cyndy Pimentel — Apresentação em Slides 16:9

Este projeto contém a versão oficial e definitiva do portfólio interativo de **Cyndy Pimentel**, formatado em proporção **16:9** (1920×1080), responsivo para qualquer monitor, com suporte a animações, links sociais, exportação para PDF, **Modo Apresentação em Tela Cheia** e um **Editor Visual Turbinado** integrado.

---

## 📁 Estrutura de Arquivos

```
cyndy-portifolio/
├── index.html       → Todo o conteúdo estruturado com comentários por slide e SEO
├── style.css        → Folha de estilos organizada com sumário no topo
├── script.js        → Motor de escala 16:9, atalhos, swipe, Fullscreen e Editor
├── README.md        → Guia de uso e edição
└── assets/
    └── img/         → As 15 imagens essenciais do portfólio
```

---

## 🚀 Como Visualizar
Basta dar **dois cliques** no arquivo `index.html` ou abrir no seu navegador favorito (Chrome, Edge, Brave, Firefox, etc.). Não precisa de servidor nem de instalação.

---

## 🎬 Modo Apresentação & Navegação por Teclado
O portfólio foi desenhado para reuniões com clientes, projeções ou envio de proposta comercial:

- **Modo Tela Cheia (Fullscreen):** Aperte a tecla <kbd>F</kbd> ou clique no botão **"Apresentar"** na barra inferior para uma imersão cinematográfica total.
- **Avançar slide:** Teclas <kbd>→</kbd>, <kbd>↓</kbd>, <kbd>PageDown</kbd> ou <kbd>Espaço</kbd>.
- **Voltar slide:** Teclas <kbd>←</kbd>, <kbd>↑</kbd>, <kbd>PageUp</kbd> ou <kbd>Shift</kbd> + <kbd>Espaço</kbd>.
- **Ir para o início / fim:** Teclas <kbd>Home</kbd> e <kbd>End</kbd>.
- **Guia de Atalhos:** Aperte a tecla <kbd>?</kbd> ou clique no ícone de teclado na barra inferior para abrir o resumo rápido.
- **Navegação no Celular/Tablet:** Basta **deslizar o dedo (swipe)** para cima ou para baixo para avançar e voltar entre os slides.

---

## ✏️ Como Editar os Slides

Você tem duas formas muito fáceis de editar:

### 1. Editor Visual Direto na Tela (Estilo Canva)
1. Abra o `index.html` no navegador.
2. Na barra inferior, clique no botão **"✏️ Editar"**.
3. **Mover:** Clique em qualquer foto, texto ou card e **arraste com o mouse**.
4. **Mudar Tamanho:** Puxe as **8 alças nos cantos** do elemento selecionado.
5. **Editar Texto:** Dê um **duplo clique** sobre qualquer frase ou número e digite diretamente.
6. **Ajuste Fino:** Use as **setas do teclado** para mover com precisão milimétrica (<kbd>Shift</kbd> move de 10 em 10px).
7. **Salvar:** Clique em **"Salvar HTML"** para gravar as novas posições no arquivo limpo sem sujeiras no código.

---

### 2. Pelo Código (HTML e CSS)

O código foi inteiramente organizado para que você encontre qualquer coisa em segundos:

* No **`index.html`**, cada slide tem uma divisão clara de comentários:
  * `01 · SLIDE DE CAPA`
  * `02 · SLIDE DE APRESENTAÇÃO`
  * `03 · SLIDE SERVIÇOS — O QUE EU FAÇO`
  * `04 · SLIDE DIVISOR — EDIÇÃO DE VÍDEOS`
  * `05 · SLIDE VÍDEOS — PARTE 1`
  * `06 · SLIDE VÍDEOS — PARTE 2`
  * `07 · SLIDE DIVISOR — RESULTADOS`
  * `08 · SLIDE CASO REAL — STORE PHONE`
  * `09 · SLIDE CASO REAL — VÍDEO VIRAL TIKTOK`
  * `10 · SLIDE CLIENTES ATENDIDOS`
  * `11 · SLIDE CONTATO`

* No **`style.css`**, há um sumário no topo listando as seções. Se quiser alterar o estilo do slide 05, basta buscar por `/* 08. SLIDES 05 E 06` no CSS.

---

## 📄 Como Exportar para PDF
1. Abra o site no navegador.
2. Clique no botão **"Baixar PDF"** no menu inferior (ou aperte `Ctrl + P`).
3. Nas opções de impressão:
   * **Destino:** Salvar como PDF
   * **Layout:** Paisagem (Landscape)
   * **Margens:** Nenhuma (None)
   * **Gráficos de segundo plano:** Marcado (Checked)
4. Clique em **Salvar**. Cada slide será gerado perfeitamente em 1 página sem quebras indesejadas.
