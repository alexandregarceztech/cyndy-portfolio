/**
 * ============================================================================
 * EDITOR VISUAL — carregado pelo script.js só quando a URL tem ?edit
 * ============================================================================
 * Mover, redimensionar (com seleção múltipla via Shift+clique), editar texto
 * e salvar. O Salvar grava só o que mudou no layout.js (não toca o index.html).
 */

(() => {
  'use strict';

  const DECK = window.CyndyDeck;
  if (!DECK) return;
  const { STATE, CONFIG, slides, showToast, LAYOUT, elementKey, btnEdit, btnSave, txtEdit } = DECK;

  // Estado que só o editor usa
  Object.assign(STATE, {
    selectedEl: null,
    dirty: new Set(),     // elementos com posição/tamanho/camada alterados (vão para o layout.js)
    dirtyText: new Set(), // elementos com texto alterado
    moved: false,
    group: [], // seleção múltipla: [{ el, off }] (off = origem do bloco de referência)
    selectedSlide: null,
    dragMode: null, // 'move' ou alças: 'nw', 'ne', 'se', 'sw', 'n', 's', 'e', 'w'
    dragStart: { x: 0, y: 0 },
    initialBox: { left: 0, top: 0, width: 0, height: 0, scale: 1 }
  });

  // Grava com !important: o layout.js aplica as posições salvas com !important, e o editor precisa vencê-las
  function put(el, prop, value) {
    el.style.setProperty(prop, value, 'important');
  }

  // Criação do Gizmo de controle com alças de redimensionamento
  const gizmo = document.createElement('div');
  gizmo.className = 'editor-gizmo';
  gizmo.style.display = 'none';
  gizmo.innerHTML = `
    <div class="gizmo-bar">
      <span class="gizmo-name">Elemento</span>
      <span class="gizmo-coords">X: 0 Y: 0</span>
      <button type="button" class="gizmo-btn" data-act="up" title="Trazer para frente">▲ Frente</button>
      <button type="button" class="gizmo-btn" data-act="down" title="Enviar para trás">▼ Trás</button>
      <button type="button" class="gizmo-btn" data-act="text" title="Editar texto">✏️ Texto</button>
      <button type="button" class="gizmo-btn" data-act="close" title="Desmarcar">✕</button>
    </div>
    <div class="gizmo-handle handle-nw" data-handle="nw"></div>
    <div class="gizmo-handle handle-ne" data-handle="ne"></div>
    <div class="gizmo-handle handle-se" data-handle="se"></div>
    <div class="gizmo-handle handle-sw" data-handle="sw"></div>
    <div class="gizmo-handle handle-n"  data-handle="n"></div>
    <div class="gizmo-handle handle-s"  data-handle="s"></div>
    <div class="gizmo-handle handle-w"  data-handle="w"></div>
    <div class="gizmo-handle handle-e"  data-handle="e"></div>
  `;

  const gizmoCoords = gizmo.querySelector('.gizmo-coords');
  const gizmoName = gizmo.querySelector('.gizmo-name');

  function getSlideScale(slide) {
    if (!slide) return 1;
    const rect = slide.getBoundingClientRect();
    return rect.width / CONFIG.DESIGN_W || 1;
  }

  function getDesignBox(el, slide) {
    // Medida pelo layout (offset*): ignora zoom do :hover e animações de entrada, que distorcem getBoundingClientRect
    if (el instanceof HTMLElement) {
      let left = 0;
      let top = 0;
      let node = el;
      while (node && node !== slide) {
        left += node.offsetLeft;
        top += node.offsetTop;
        node = node.offsetParent;
        if (node && node !== slide) {
          left += node.clientLeft;
          top += node.clientTop;
        }
      }
      if (node === slide) {
        return { left, top, width: el.offsetWidth, height: el.offsetHeight, scale: getSlideScale(slide) };
      }
    }
    const sRect = slide.getBoundingClientRect();
    const eRect = el.getBoundingClientRect();
    const scale = getSlideScale(slide);
    return {
      left: Math.round((eRect.left - sRect.left) / scale),
      top: Math.round((eRect.top - sRect.top) / scale),
      width: Math.round(eRect.width / scale),
      height: Math.round(eRect.height / scale),
      scale
    };
  }

  // Origem (em px de design) do bloco que contém o elemento: left/top precisam ser relativos a ele
  function getParentOffset(el, slide) {
    const parent = el.offsetParent;
    if (!parent || parent === slide || !slide.contains(parent)) return { left: 0, top: 0 };
    const box = getDesignBox(parent, slide);
    return { left: box.left, top: box.top };
  }

  function syncGizmo() {
    if (!STATE.selectedEl || !STATE.selectedSlide) {
      gizmo.style.display = 'none';
      return;
    }
    // Caixa envolvente de todos os itens selecionados
    const boxes = (STATE.group.length ? STATE.group.map(g => g.el) : [STATE.selectedEl])
      .map(el => getDesignBox(el, STATE.selectedSlide));
    const left = Math.min(...boxes.map(b => b.left));
    const top = Math.min(...boxes.map(b => b.top));
    const width = Math.max(...boxes.map(b => b.left + b.width)) - left;
    const height = Math.max(...boxes.map(b => b.top + b.height)) - top;
    gizmo.classList.toggle('multi', boxes.length > 1);
    gizmo.style.display = 'block';
    gizmo.style.left = left + 'px';
    gizmo.style.top = top + 'px';
    gizmo.style.width = width + 'px';
    gizmo.style.height = height + 'px';
    if (gizmoCoords) {
      gizmoCoords.textContent = `X: ${left} Y: ${top} | ${width}×${height}px`;
    }
  }

  function selectElement(el) {
    if (STATE.selectedEl === el) return;
    deselectElement();
    if (!el) return;

    STATE.selectedEl = el;
    STATE.selectedSlide = el.closest('.slide');
    if (!STATE.selectedSlide) return;

    if (gizmo.parentNode !== STATE.selectedSlide) {
      STATE.selectedSlide.appendChild(gizmo);
    }

    const tag = el.tagName.toLowerCase();
    const cls = el.className.split(' ').filter(c => c && !c.startsWith('elem-') && c !== 'abs')[0] || tag;
    if (gizmoName) gizmoName.textContent = `<${tag}.${cls}>`;

    STATE.group = [{ el, off: makeFreeform(el, STATE.selectedSlide) }];
    syncGizmo();
  }

  // Posicionamento absoluto padrão para manipulação livre; devolve a origem do bloco de referência
  function makeFreeform(el, slide) {
    const box = getDesignBox(el, slide);
    // Mede o bloco de referência antes de forçar position: absolute no elemento
    const off = getParentOffset(el, slide);
    put(el, 'position', 'absolute');
    put(el, 'left', (box.left - off.left) + 'px');
    put(el, 'top', (box.top - off.top) + 'px');
    put(el, 'width', box.width + 'px');
    put(el, 'height', box.height + 'px');
    put(el, 'right', 'auto');
    put(el, 'bottom', 'auto');
    put(el, 'margin', '0');
    return off;
  }

  // Shift+clique: adiciona/remove um item da seleção múltipla (mesmo slide)
  function toggleInSelection(el) {
    if (!STATE.selectedEl || el.closest('.slide') !== STATE.selectedSlide) {
      selectElement(el);
      return;
    }
    const idx = STATE.group.findIndex(g => g.el === el);
    if (idx >= 0) {
      if (STATE.group.length === 1) return;
      STATE.group.splice(idx, 1);
      el.classList.remove('elem-multi');
      STATE.selectedEl = STATE.group[0].el;
    } else {
      STATE.group.push({ el, off: makeFreeform(el, STATE.selectedSlide) });
    }
    STATE.group.forEach(g => g.el.classList.toggle('elem-multi', STATE.group.length > 1));
    if (gizmoName) {
      gizmoName.textContent = STATE.group.length > 1 ? `${STATE.group.length} itens` : `<${STATE.selectedEl.tagName.toLowerCase()}>`;
    }
    syncGizmo();
  }

  function deselectElement() {
    if (STATE.isEditingText && STATE.selectedEl) {
      STATE.selectedEl.removeAttribute('contenteditable');
      STATE.selectedEl.classList.remove('elem-editing-text');
      STATE.dirtyText.add(STATE.selectedEl);
      STATE.isEditingText = false;
    }
    STATE.group.forEach(g => g.el.classList.remove('elem-multi'));
    STATE.group = [];
    STATE.selectedEl = null;
    STATE.selectedSlide = null;
    gizmo.style.display = 'none';
    if (gizmo.parentNode) {
      gizmo.parentNode.removeChild(gizmo);
    }
  }

  function startTextEdit(el) {
    if (!el) return;
    STATE.isEditingText = true;
    el.contentEditable = 'true';
    el.classList.add('elem-editing-text');
    el.focus();
  }

  // Operações nos botões do Gizmo
  gizmo.addEventListener('click', (e) => {
    const btn = e.target.closest('.gizmo-btn');
    if (!btn || !STATE.selectedEl) return;
    e.stopPropagation();

    const act = btn.dataset.act;
    const currentZ = parseInt(window.getComputedStyle(STATE.selectedEl).zIndex) || 1;

    if (act === 'up') {
      put(STATE.selectedEl, 'z-index', String(currentZ + 1));
      STATE.dirty.add(STATE.selectedEl);
      showToast(`Camada ajustada: z-index ${currentZ + 1}`, 1500);
    } else if (act === 'down') {
      const newZ = Math.max(0, currentZ - 1);
      put(STATE.selectedEl, 'z-index', String(newZ));
      STATE.dirty.add(STATE.selectedEl);
      showToast(`Camada ajustada: z-index ${newZ}`, 1500);
    } else if (act === 'text') {
      startTextEdit(STATE.selectedEl);
    } else if (act === 'close') {
      deselectElement();
    }
  });

  // Mover elemento e redimensionar via alças
  gizmo.addEventListener('mousedown', (e) => {
    if (e.target.closest('.gizmo-btn')) return;
    if (!STATE.selectedEl || !STATE.selectedSlide) return;
    e.preventDefault();
    e.stopPropagation();

    const handle = e.target.closest('.gizmo-handle');
    STATE.dragMode = handle ? handle.dataset.handle : 'move';

    const box = getDesignBox(STATE.selectedEl, STATE.selectedSlide);
    STATE.initialBox = {
      left: box.left,
      top: box.top,
      width: box.width,
      height: box.height,
      scale: box.scale
    };
    STATE.dragStart = { x: e.clientX, y: e.clientY };
    STATE.moved = false;
    STATE.initialGroup = STATE.group.map(g => ({ ...g, box: getDesignBox(g.el, STATE.selectedSlide) }));

    document.addEventListener('mousemove', onGizmoMouseMove);
    document.addEventListener('mouseup', onGizmoMouseUp);
  });

  function onGizmoMouseMove(e) {
    if (!STATE.dragMode || !STATE.selectedEl) return;
    const curScale = STATE.initialBox.scale || 1;
    const dx = (e.clientX - STATE.dragStart.x) / curScale;
    const dy = (e.clientY - STATE.dragStart.y) / curScale;
    STATE.moved = true;

    if (STATE.dragMode === 'move') {
      STATE.initialGroup.forEach(({ el, off, box }) => {
        put(el, 'left', (Math.round(box.left + dx) - off.left) + 'px');
        put(el, 'top', (Math.round(box.top + dy) - off.top) + 'px');
      });
    } else {
      let newW = STATE.initialBox.width;
      let newH = STATE.initialBox.height;
      let newL = STATE.initialBox.left;
      let newT = STATE.initialBox.top;

      if (STATE.dragMode.includes('e')) newW = Math.max(20, Math.round(STATE.initialBox.width + dx));
      if (STATE.dragMode.includes('s')) newH = Math.max(20, Math.round(STATE.initialBox.height + dy));
      if (STATE.dragMode.includes('w')) {
        newW = Math.max(20, Math.round(STATE.initialBox.width - dx));
        newL = Math.round(STATE.initialBox.left + (STATE.initialBox.width - newW));
      }
      if (STATE.dragMode.includes('n')) {
        newH = Math.max(20, Math.round(STATE.initialBox.height - dy));
        newT = Math.round(STATE.initialBox.top + (STATE.initialBox.height - newH));
      }

      put(STATE.selectedEl, 'width', newW + 'px');
      put(STATE.selectedEl, 'height', newH + 'px');
      const off = STATE.group[0].off;
      put(STATE.selectedEl, 'left', (newL - off.left) + 'px');
      put(STATE.selectedEl, 'top', (newT - off.top) + 'px');
    }

    syncGizmo();
  }

  function onGizmoMouseUp() {
    if (STATE.moved) STATE.group.forEach(g => STATE.dirty.add(g.el));
    STATE.dragMode = null;
    document.removeEventListener('mousemove', onGizmoMouseMove);
    document.removeEventListener('mouseup', onGizmoMouseUp);
  }

  // Clique nos slides para selecionar elementos
  document.addEventListener('mousedown', (e) => {
    if (!STATE.isEditing) return;
    if (e.target.closest('.dock') || e.target.closest('.editor-gizmo') || e.target.closest('.edit-toast') || e.target.closest('.modal-backdrop') || e.target.closest('.orientation-overlay')) return;

    const slide = e.target.closest('.slide');
    if (!slide) {
      deselectElement();
      return;
    }

    const target = e.target.closest('.client-logo, .c-box, .badge, .stat, .card, .abs, figure, article, blockquote, .phone, .cols, .slide > *');
    if (target && target !== slide && !target.classList.contains('editor-gizmo')) {
      if (e.shiftKey) toggleInSelection(target);
      else selectElement(target);
    } else {
      deselectElement();
    }
  });

  // Duplo clique ativa edição direta de texto
  document.addEventListener('dblclick', (e) => {
    if (!STATE.isEditing) return;
    if (e.target.closest('.dock') || e.target.closest('.editor-gizmo') || e.target.closest('.modal-backdrop') || e.target.closest('.orientation-overlay')) return;

    const textTarget = e.target.closest('h1, h2, h3, h4, p, span, li, dt, dd, b, strong, small, blockquote, figcaption');
    if (textTarget) {
      startTextEdit(textTarget);
    }
  });

  // Alternar Modo Edição
  function toggleEditing() {
    STATE.isEditing = !STATE.isEditing;
    document.body.classList.toggle('editing-mode', STATE.isEditing);

    if (btnEdit) btnEdit.classList.toggle('active', STATE.isEditing);
    if (btnSave) btnSave.style.display = STATE.isEditing ? 'inline-flex' : 'none';
    if (txtEdit) txtEdit.textContent = STATE.isEditing ? 'Concluir' : 'Editar';

    if (STATE.isEditing) {
      slides.forEach(s => s.classList.add('in'));
      showToast('🎯 <b>Modo Edição Ativado!</b><br>• Clique para <b>Arrastar e Redimensionar</b>.<br>• <b>Duplo clique</b> em qualquer texto para escrever.<br>• <b>Setas do teclado</b> para ajuste fino.');
    } else {
      deselectElement();
      showToast('Modo de edição finalizado.');
    }
  }

  if (btnEdit) btnEdit.addEventListener('click', toggleEditing);

  // Salvar Alterações: grava só o que foi mexido, no layout.js (o index.html não é tocado)
  if (btnSave) {
    btnSave.addEventListener('click', async () => {
      deselectElement();
      if (STATE.isEditing) toggleEditing();

      STATE.dirty.forEach(el => {
        const key = elementKey(el);
        if (!key) return;
        const st = {};
        ['left', 'top', 'width', 'height'].forEach(k => {
          const v = parseFloat(el.style[k]);
          if (!isNaN(v)) st[k] = Math.round(v);
        });
        if (el.style.zIndex !== '') st.zIndex = parseInt(el.style.zIndex);
        LAYOUT.styles[key] = st;
      });
      STATE.dirtyText.forEach(el => {
        const key = elementKey(el);
        if (key) LAYOUT.text[key] = el.innerHTML;
      });

      const total = Object.keys(LAYOUT.styles).length + Object.keys(LAYOUT.text).length;
      const content = '/* Ajustes feitos no editor visual (index.html?edit → Salvar). Gerado automaticamente; pode ser editado à mão. */\n'
        + 'window.CYNDY_LAYOUT = ' + JSON.stringify(LAYOUT, null, 2) + ';\n';

      // Backup local no navegador
      try {
        localStorage.setItem('cyndy_layout_backup', content);
      } catch (e) {
        console.warn('Erro ao salvar no localStorage:', e);
      }

      // 1. Salvamento direto pelo seletor nativo do navegador (escolha o layout.js do projeto)
      if (window.showSaveFilePicker) {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: 'layout.js',
            types: [{ description: 'Layout (JavaScript)', accept: { 'text/javascript': ['.js'] } }]
          });
          const writable = await handle.createWritable();
          await writable.write(content);
          await writable.close();
          showToast(`✅ <b>Layout salvo</b> (${total} ajustes). Escolha o <b>layout.js</b> do projeto.`);
          return;
        } catch (err) {
          if (err.name !== 'AbortError') console.error(err);
          else return;
        }
      }

      // 2. Fallback por download
      const blob = new Blob([content], { type: 'text/javascript;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'layout.js';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showToast('💾 <b>layout.js baixado.</b> Substitua o arquivo do projeto por ele.');
    });
  }

  // Ajuste fino com as setas (Shift = passo maior); devolve true se tratou a tecla
  function handleKey(e) {
    if (!STATE.selectedEl) return false;
    const step = e.shiftKey ? 10 : 2;
    const delta = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key];
    if (!delta) return false;
    STATE.group.forEach(({ el }) => {
      put(el, 'left', ((parseInt(el.style.left) || 0) + delta[0]) + 'px');
      put(el, 'top', ((parseInt(el.style.top) || 0) + delta[1]) + 'px');
      STATE.dirty.add(el);
    });
    e.preventDefault();
    syncGizmo();
    return true;
  }

  DECK.editor = { deselect: deselectElement, sync: syncGizmo, handleKey };
})();
