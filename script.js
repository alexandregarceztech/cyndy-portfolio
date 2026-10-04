/* =========================================================
   Portfólio Cyndy — Escala dos slides, animações e navegação
   + Modo Edição Visual Turbinado (Drag, Resize & Inline Text)
   ========================================================= */
(() => {
  const DESIGN_W = 1920;
  const DESIGN_H = 1080;
  const wraps = [...document.querySelectorAll('.slide-wrap')];
  const slides = wraps.map(w => w.querySelector('.slide'));
  const counter = document.getElementById('slide-count');
  const total = String(wraps.length).padStart(2, '0');
  let current = 0;

  /* ---------- Escala 1920×1080 → largura disponível ---------- */
  const fit = (wrap) => {
    const s = wrap.clientWidth / DESIGN_W;
    wrap.querySelector('.slide').style.setProperty('--scale', s);
  };
  const ro = new ResizeObserver(entries => entries.forEach(e => fit(e.target)));
  wraps.forEach(w => { fit(w); ro.observe(w); });

  /* ---------- Contadores numéricos ---------- */
  const runCounter = (el) => {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || '';
    const dur = 1600;
    const t0 = performance.now();
    const tick = (now) => {
      const p = Math.min((now - t0) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  /* ---------- Entrada dos slides ---------- */
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const inEditor = window.self !== window.top;

  if (!reduce && !inEditor) {
    document.documentElement.classList.add('js-anim');
  } else {
    slides.forEach(s => s.classList.add('in'));
  }

  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const slide = e.target.querySelector('.slide');
      if (slide.classList.contains('in')) return;
      slide.classList.add('in');
      if (!reduce) slide.querySelectorAll('[data-count]').forEach(runCounter);
    });
  }, { threshold: 0.35 });
  wraps.forEach(w => io.observe(w));

  /* ---------- Slide atual (para o contador do dock) ---------- */
  const activeIO = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        current = wraps.indexOf(e.target);
        if (counter) counter.innerHTML = `<b>${String(current + 1).padStart(2, '0')}</b> / ${total}`;
      }
    });
  }, { threshold: 0.6 });
  wraps.forEach(w => activeIO.observe(w));

  const go = (i) => {
    current = Math.max(0, Math.min(wraps.length - 1, i));
    wraps[current].scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const btnPdf = document.getElementById('btn-pdf');

  if (btnPrev) btnPrev.addEventListener('click', () => go(current - 1));
  if (btnNext) btnNext.addEventListener('click', () => go(current + 1));
  if (btnPdf) btnPdf.addEventListener('click', () => window.print());

  document.addEventListener('keydown', (e) => {
    if (isEditingText) return;
    if (['ArrowDown', 'PageDown'].includes(e.key)) { e.preventDefault(); go(current + 1); }
    if (['ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); go(current - 1); }
  });

  /* ---------- Impressão: tudo visível e no estado final ---------- */
  window.addEventListener('beforeprint', () => slides.forEach(s => {
    s.classList.add('in');
    s.querySelectorAll('[data-count]').forEach(el => {
      el.textContent = el.dataset.count + (el.dataset.suffix || '');
    });
  }));

  /* =========================================================
     MODO EDIÇÃO VISUAL TURBINADO (Mover, Redimensionar e Texto)
     ========================================================= */
  const btnEdit = document.getElementById('btn-edit');
  const btnSave = document.getElementById('btn-save');
  const txtEdit = document.getElementById('txt-edit');
  let isEditing = false;
  let isEditingText = false;
  let selectedEl = null;
  let selectedSlide = null;

  function showToast(msg, dur = 4000) {
    const old = document.querySelector('.edit-toast');
    if (old) old.remove();
    const t = document.createElement('div');
    t.className = 'edit-toast';
    t.innerHTML = msg;
    document.body.appendChild(t);
    setTimeout(() => { if (t.parentNode) t.remove(); }, dur);
  }

  /* Cria o Gizmo (caixa delimitadora com controles e alças) */
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
    const rect = slide.getBoundingClientRect();
    return rect.width / DESIGN_W;
  }

  function getDesignBox(el, slide) {
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

  function syncGizmo() {
    if (!selectedEl || !selectedSlide) {
      gizmo.style.display = 'none';
      return;
    }
    const box = getDesignBox(selectedEl, selectedSlide);
    gizmo.style.display = 'block';
    gizmo.style.left = box.left + 'px';
    gizmo.style.top = box.top + 'px';
    gizmo.style.width = box.width + 'px';
    gizmo.style.height = box.height + 'px';
    gizmoCoords.textContent = `X: ${box.left} Y: ${box.top} | ${box.width}×${box.height}px`;
  }

  function selectElement(el) {
    if (selectedEl === el) return;
    deselectElement();
    if (!el) return;

    selectedEl = el;
    selectedSlide = el.closest('.slide');
    if (!selectedSlide) return;

    // Coloca o gizmo dentro do slide do elemento
    if (gizmo.parentNode !== selectedSlide) {
      selectedSlide.appendChild(gizmo);
    }

    const tag = el.tagName.toLowerCase();
    const cls = el.className.split(' ').filter(c => c && !c.startsWith('elem-') && c !== 'abs')[0] || tag;
    gizmoName.textContent = `<${tag}.${cls}>`;

    // Garante que o elemento esteja preparado para posicionamento absoluto livre
    const box = getDesignBox(selectedEl, selectedSlide);
    selectedEl.style.position = 'absolute';
    selectedEl.style.left = box.left + 'px';
    selectedEl.style.top = box.top + 'px';
    selectedEl.style.width = box.width + 'px';
    selectedEl.style.height = box.height + 'px';
    selectedEl.style.right = 'auto';
    selectedEl.style.bottom = 'auto';
    selectedEl.style.margin = '0';

    syncGizmo();
  }

  function deselectElement() {
    if (isEditingText && selectedEl) {
      selectedEl.removeAttribute('contenteditable');
      selectedEl.classList.remove('elem-editing-text');
      isEditingText = false;
    }
    selectedEl = null;
    selectedSlide = null;
    gizmo.style.display = 'none';
    if (gizmo.parentNode) gizmo.parentNode.removeChild(gizmo);
  }

  function startTextEdit(el) {
    if (!el) return;
    isEditingText = true;
    el.contentEditable = 'true';
    el.classList.add('elem-editing-text');
    el.focus();
  }

  /* Operações nos botões do Gizmo */
  gizmo.addEventListener('click', (e) => {
    const btn = e.target.closest('.gizmo-btn');
    if (!btn || !selectedEl) return;
    e.stopPropagation();

    const act = btn.dataset.act;
    const currentZ = parseInt(window.getComputedStyle(selectedEl).zIndex) || 1;

    if (act === 'up') {
      selectedEl.style.zIndex = currentZ + 1;
      showToast(`Camada: z-index ${currentZ + 1}`, 1500);
    } else if (act === 'down') {
      selectedEl.style.zIndex = Math.max(0, currentZ - 1);
      showToast(`Camada: z-index ${Math.max(0, currentZ - 1)}`, 1500);
    } else if (act === 'text') {
      startTextEdit(selectedEl);
    } else if (act === 'close') {
      deselectElement();
    }
  });

  /* Mover elemento arrastando o gizmo */
  let dragMode = null; // 'move' ou handle ('nw', 'se', etc.)
  let startX = 0, startY = 0;
  let initLeft = 0, initTop = 0, initW = 0, initH = 0;
  let curScale = 1;

  gizmo.addEventListener('mousedown', (e) => {
    if (e.target.closest('.gizmo-btn')) return; // ignora botões
    if (!selectedEl || !selectedSlide) return;
    e.preventDefault();
    e.stopPropagation();

    const handle = e.target.closest('.gizmo-handle');
    dragMode = handle ? handle.dataset.handle : 'move';

    const box = getDesignBox(selectedEl, selectedSlide);
    initLeft = box.left;
    initTop = box.top;
    initW = box.width;
    initH = box.height;
    curScale = box.scale;
    startX = e.clientX;
    startY = e.clientY;

    document.addEventListener('mousemove', onGizmoMouseMove);
    document.addEventListener('mouseup', onGizmoMouseUp);
  });

  function onGizmoMouseMove(e) {
    if (!dragMode || !selectedEl) return;
    const dx = (e.clientX - startX) / curScale;
    const dy = (e.clientY - startY) / curScale;

    if (dragMode === 'move') {
      const newL = Math.round(initLeft + dx);
      const newT = Math.round(initTop + dy);
      selectedEl.style.left = newL + 'px';
      selectedEl.style.top = newT + 'px';
    } else {
      // Redimensionamento pelas alças
      let newW = initW;
      let newH = initH;
      let newL = initLeft;
      let newT = initTop;

      if (dragMode.includes('e')) newW = Math.max(20, Math.round(initW + dx));
      if (dragMode.includes('s')) newH = Math.max(20, Math.round(initH + dy));
      if (dragMode.includes('w')) {
        newW = Math.max(20, Math.round(initW - dx));
        newL = Math.round(initLeft + (initW - newW));
      }
      if (dragMode.includes('n')) {
        newH = Math.max(20, Math.round(initH - dy));
        newT = Math.round(initTop + (initH - newH));
      }

      selectedEl.style.width = newW + 'px';
      selectedEl.style.height = newH + 'px';
      selectedEl.style.left = newL + 'px';
      selectedEl.style.top = newT + 'px';
    }

    syncGizmo();
  }

  function onGizmoMouseUp() {
    dragMode = null;
    document.removeEventListener('mousemove', onGizmoMouseMove);
    document.removeEventListener('mouseup', onGizmoMouseUp);
  }

  /* Clique nos slides para selecionar elementos */
  document.addEventListener('mousedown', (e) => {
    if (!isEditing) return;
    if (e.target.closest('.dock') || e.target.closest('.editor-gizmo') || e.target.closest('.edit-toast')) return;

    const slide = e.target.closest('.slide');
    if (!slide) {
      deselectElement();
      return;
    }

    // Busca o elemento mais adequado dentro do slide
    const target = e.target.closest('.abs, figure, article, blockquote, .phone, .cols, .slide > *');
    if (target && target !== slide && !target.classList.contains('editor-gizmo')) {
      selectElement(target);
    } else {
      deselectElement();
    }
  });

  /* Duplo clique ativa edição de texto direto */
  document.addEventListener('dblclick', (e) => {
    if (!isEditing) return;
    if (e.target.closest('.dock') || e.target.closest('.editor-gizmo')) return;
    const textTarget = e.target.closest('h1, h2, h3, h4, p, span, li, dt, dd, b, strong, small, blockquote, figcaption');
    if (textTarget) {
      startTextEdit(textTarget);
    }
  });

  /* Ajuste fino com setas do teclado */
  document.addEventListener('keydown', (e) => {
    if (!isEditing || !selectedEl || isEditingText) return;

    if (e.key === 'Escape') {
      deselectElement();
      return;
    }

    const step = e.shiftKey ? 10 : 2;
    let handled = false;
    let l = parseInt(selectedEl.style.left) || 0;
    let t = parseInt(selectedEl.style.top) || 0;

    if (e.key === 'ArrowLeft')  { selectedEl.style.left = (l - step) + 'px'; handled = true; }
    if (e.key === 'ArrowRight') { selectedEl.style.left = (l + step) + 'px'; handled = true; }
    if (e.key === 'ArrowUp')    { selectedEl.style.top  = (t - step) + 'px'; handled = true; }
    if (e.key === 'ArrowDown')  { selectedEl.style.top  = (t + step) + 'px'; handled = true; }

    if (handled) {
      e.preventDefault();
      syncGizmo();
    }
  });

  /* Alternar modo de edição */
  function toggleEditing() {
    isEditing = !isEditing;
    document.body.classList.toggle('editing-mode', isEditing);
    btnEdit.classList.toggle('active', isEditing);
    btnSave.style.display = isEditing ? 'inline-flex' : 'none';
    txtEdit.textContent = isEditing ? 'Concluir' : 'Editar';

    if (isEditing) {
      slides.forEach(s => s.classList.add('in'));
      showToast('🎯 <b>Modo Edição Turbinado Ativo!</b><br>• Clique para <b>Arrastar e Redimensionar</b> pelas alças.<br>• <b>Duplo clique</b> em qualquer texto para escrever.<br>• Use as <b>setas do teclado</b> para ajuste fino.');
    } else {
      deselectElement();
      showToast('Modo de edição finalizado.');
    }
  }

  btnEdit.addEventListener('click', toggleEditing);

  /* Salvar alterações */
  btnSave.addEventListener('click', async () => {
    // 1. Limpa seleção e fecha modo de edição para gerar HTML limpo
    deselectElement();
    const wasEditing = isEditing;
    if (wasEditing) toggleEditing();

    // 2. Extrai o conteúdo limpo do main.deck
    const deckEl = document.getElementById('deck');
    const deckClone = deckEl.cloneNode(true);
    deckClone.querySelectorAll('.editor-gizmo').forEach(g => g.remove());
    deckClone.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
    deckClone.querySelectorAll('.elem-editing-text').forEach(el => el.classList.remove('elem-editing-text'));

    const deckHtml = deckClone.outerHTML;

    // 3. Se estiver no WordPress com endpoint AJAX disponível:
    if (window.cyndyAjax && window.cyndyAjax.url) {
      try {
        const formData = new FormData();
        formData.append('action', 'cyndy_save_deck');
        formData.append('deck_html', deckHtml);

        const res = await fetch(window.cyndyAjax.url, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (data.success) {
          showToast('✅ <b>Salvo no WordPress com sucesso!</b> (front-page.php atualizado)');
          return;
        }
      } catch (err) {
        console.warn('Erro ao salvar via AJAX WordPress:', err);
      }
    }

    // 4. Salvar arquivo HTML estático (index.html)
    const cloneDoc = document.documentElement.cloneNode(true);
    cloneDoc.querySelectorAll('.editor-gizmo').forEach(g => g.remove());
    cloneDoc.querySelectorAll('.edit-toast').forEach(t => t.remove());
    cloneDoc.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
    cloneDoc.querySelectorAll('.editing-mode').forEach(el => el.classList.remove('editing-mode'));

    const cloneBtnSave = cloneDoc.querySelector('#btn-save');
    if (cloneBtnSave) cloneBtnSave.style.display = 'none';
    const cloneBtnEdit = cloneDoc.querySelector('#btn-edit');
    if (cloneBtnEdit) cloneBtnEdit.classList.remove('active');
    const cloneTxtEdit = cloneDoc.querySelector('#txt-edit');
    if (cloneTxtEdit) cloneTxtEdit.textContent = 'Editar';

    const fullHtml = '<!DOCTYPE html>\n' + cloneDoc.outerHTML;

    try {
      localStorage.setItem('cyndy_deck_backup', fullHtml);
    } catch (e) {}

    if (window.showSaveFilePicker) {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: 'index.html',
          types: [{ description: 'Arquivo HTML', accept: { 'text/html': ['.html'] } }]
        });
        const writable = await handle.createWritable();
        await writable.write(fullHtml);
        await writable.close();
        showToast('✅ <b>Alterações salvas com sucesso no arquivo!</b>');
        return;
      } catch (err) {
        if (err.name !== 'AbortError') console.error(err);
      }
    }

    // Fallback: download automático
    const blob = new Blob([fullHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'index.html';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('💾 <b>Download das alterações concluído!</b>');
  });
})();
