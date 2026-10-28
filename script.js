/**
 * ============================================================================
 * PORTFÓLIO CYNDY PIMENTEL — MOTOR DE SLIDES 16:9 & EDITOR VISUAL
 * ============================================================================
 * Arquitetura Front-end por Agente 1 (Líder / Arquiteto)
 *
 * Módulos:
 *  1. State & Configurações Centrais
 *  2. ScaleEngine (Responsividade Proporcional 1920×1080)
 *  3. SlideNavigator (Navegação Suave e Indicadores)
 *  4. FullscreenController (Modo Apresentação Cinematográfica)
 *  5. Animation & CounterEngine (Micro-interações e Estatísticas)
 *  6. Keyboard & TouchGestures (Atalhos e Gestos Swipe Mobile)
 *  7. VisualEditorEngine (Mover, Redimensionar, Editar Texto e Salvar)
 *  8. ShortcutsModalController (Modal Informativo de Atalhos)
 * ============================================================================
 */

(() => {
  'use strict';

  /* ==========================================================================
     1. STATE & CONFIGURAÇÕES CENTRAIS
     ========================================================================== */
  const CONFIG = {
    DESIGN_W: 1920,
    DESIGN_H: 1080,
    ASPECT_RATIO: 16 / 9,
    ANIM_DURATION: 1600,
    SWIPE_THRESHOLD: 45 // Pixels mínimos para considerar gesto swipe
  };

  const STATE = {
    current: 0,
    isEditing: false,
    isEditingText: false,
    selectedEl: null,
    group: [], // seleção múltipla: [{ el, off }] (off = origem do bloco de referência)
    selectedSlide: null,
    dragMode: null, // 'move' ou alças: 'nw', 'ne', 'se', 'sw', 'n', 's', 'e', 'w'
    dragStart: { x: 0, y: 0 },
    initialBox: { left: 0, top: 0, width: 0, height: 0, scale: 1 },
    touchStart: { x: 0, y: 0, time: 0 },
    isPresentationMode: false
  };

  // Elementos do DOM principais
  const wraps = Array.from(document.querySelectorAll('.slide-wrap'));
  const slides = wraps.map(wrap => wrap.querySelector('.slide'));
  const totalSlides = wraps.length;
  const totalFormatted = String(totalSlides).padStart(2, '0');

  // Elementos da Interface Flutuante (Dock)
  const counterEl = document.getElementById('slide-count');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const btnFullscreen = document.getElementById('btn-fullscreen');
  const btnPdf = document.getElementById('btn-pdf');
  const btnEdit = document.getElementById('btn-edit');
  const btnSave = document.getElementById('btn-save');
  const txtEdit = document.getElementById('txt-edit');
  const btnShareSlide = document.getElementById('btn-share-slide');
  const btnShortcuts = document.getElementById('btn-shortcuts');
  const modalShortcuts = document.getElementById('modal-shortcuts');
  const btnCloseShortcuts = document.getElementById('btn-close-shortcuts');

  // Elementos do Reel Theater Modal
  const modalReelTheater = document.getElementById('modal-reel-theater');
  const reelVideoPlayer = document.getElementById('reel-video-player');
  const reelTheaterTitle = document.getElementById('reel-theater-title');
  const reelTheaterDesc = document.getElementById('reel-theater-desc');
  const reelInstagramLink = document.getElementById('reel-instagram-link');
  const btnCloseReel = document.getElementById('btn-close-reel');
  const btnReelPrev = document.getElementById('btn-reel-prev');
  const btnReelNext = document.getElementById('btn-reel-next');
  const reelFallback = document.getElementById('reel-fallback');
  const reelFallbackLink = document.getElementById('reel-fallback-link');
  const reelPillsContainer = document.getElementById('reel-pills');

  // Elementos do Overlay Mobile de Orientação Paisagem (Tarefa #020)
  const orientationOverlay = document.getElementById('orientation-overlay');
  const btnDismissOrientation = document.getElementById('btn-dismiss-orientation');

  if (!wraps.length) {
    console.warn('[Portfólio Cyndy] Nenhum slide encontrado com a classe .slide-wrap');
    return;
  }

  /* ==========================================================================
     SISTEMA DE NOTIFICAÇÕES (TOAST)
     ========================================================================== */
  function showToast(message, duration = 3800) {
    const existingToast = document.querySelector('.edit-toast');
    if (existingToast) existingToast.remove();

    const toast = document.createElement('div');
    toast.className = 'edit-toast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.innerHTML = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      if (toast.parentNode) {
        toast.style.opacity = '0';
        toast.style.transform = 'translate(-50%, -10px)';
        toast.style.transition = 'opacity 0.25s, transform 0.25s';
        setTimeout(() => toast.remove(), 260);
      }
    }, duration);
  }

  /* ==========================================================================
     2. SCALE ENGINE (Ajuste 1920×1080 com zero Layout Thrashing)
     ========================================================================== */
  let scaleRafId = null;

  function applySlideScale(wrap) {
    const slide = wrap.querySelector('.slide');
    if (!slide) return;
    const currentWidth = wrap.clientWidth;
    const scale = currentWidth / CONFIG.DESIGN_W;
    slide.style.setProperty('--scale', scale);
  }

  function recalculateAllScales() {
    if (scaleRafId) cancelAnimationFrame(scaleRafId);
    scaleRafId = requestAnimationFrame(() => {
      wraps.forEach(applySlideScale);
      if (STATE.isEditing) syncGizmo();
    });
  }

  const resizeObserver = new ResizeObserver(entries => {
    for (const entry of entries) {
      applySlideScale(entry.target);
    }
    if (STATE.isEditing) syncGizmo();
  });

  wraps.forEach(wrap => {
    applySlideScale(wrap);
    resizeObserver.observe(wrap);
  });

  window.addEventListener('resize', recalculateAllScales, { passive: true });

  /* ==========================================================================
     3. SLIDE NAVIGATOR (Navegação Precisa e Atualização de Estado)
     ========================================================================== */
  function updateCounter(index) {
    STATE.current = Math.max(0, Math.min(totalSlides - 1, index));
    if (counterEl) {
      const currentFormatted = String(STATE.current + 1).padStart(2, '0');
      counterEl.innerHTML = `<b>${currentFormatted}</b> / ${totalFormatted}`;
    }
  }

  function goToSlide(index, smooth = true, updateHash = true) {
    const targetIndex = Math.max(0, Math.min(totalSlides - 1, index));
    STATE.current = targetIndex;
    updateCounter(targetIndex);

    // Pausa e fecha o Reel Theater caso esteja aberto para não vazar áudio
    if (typeof closeReelTheater === 'function' && modalReelTheater && modalReelTheater.classList.contains('active')) {
      closeReelTheater();
    }

    const targetWrap = wraps[targetIndex];
    if (targetWrap) {
      targetWrap.scrollIntoView({
        behavior: smooth ? 'smooth' : 'auto',
        block: 'start'
      });

      // Sincronização limpa de Deep Linking via hash
      if (updateHash && targetWrap.id) {
        try {
          const newUrl = window.location.pathname + window.location.search + '#' + targetWrap.id;
          window.history.replaceState(null, '', newUrl);
        } catch (e) {
          // Ignora silenciosamente em ambientes restritos
        }
      }

      // Look-ahead prefetch no slide divisor de vídeos (índice 3)
      if (targetIndex === 3 && typeof prefetchFirstReel === 'function') {
        prefetchFirstReel();
      }
    }
  }

  function nextSlide() {
    if (STATE.current < totalSlides - 1) {
      goToSlide(STATE.current + 1);
    }
  }

  function prevSlide() {
    if (STATE.current > 0) {
      goToSlide(STATE.current - 1);
    }
  }

  function firstSlide() {
    goToSlide(0);
  }

  function lastSlide() {
    goToSlide(totalSlides - 1);
  }

  if (btnPrev) btnPrev.addEventListener('click', () => prevSlide());
  if (btnNext) btnNext.addEventListener('click', () => nextSlide());

  // Observador de interseção para sincronizar contador e hash no scroll manual
  const activeSlideObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const index = wraps.indexOf(entry.target);
        if (index !== -1) {
          updateCounter(index);
          if (entry.target.id && window.location.hash !== '#' + entry.target.id) {
            try {
              window.history.replaceState(null, '', window.location.pathname + window.location.search + '#' + entry.target.id);
            } catch (e) {}
          }
          if (index === 3 && typeof prefetchFirstReel === 'function') {
            prefetchFirstReel();
          }
        }
      }
    });
  }, { threshold: 0.55 });

  wraps.forEach(wrap => activeSlideObserver.observe(wrap));

  /* ==========================================================================
     4. FULLSCREEN CONTROLLER (Modo Apresentação)
     ========================================================================== */
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      const docEl = document.documentElement;
      const rfs = docEl.requestFullscreen || docEl.webkitRequestFullscreen || docEl.msRequestFullscreen;
      if (rfs) {
        rfs.call(docEl).catch(err => console.warn('Erro ao entrar em tela cheia:', err));
      }
    } else {
      const efs = document.exitFullscreen || document.webkitExitFullscreen || document.msExitFullscreen;
      if (efs) {
        efs.call(document).catch(err => console.warn('Erro ao sair de tela cheia:', err));
      }
    }
  }

  function updateFullscreenUI() {
    const isFull = !!document.fullscreenElement;
    document.body.classList.toggle('is-fullscreen', isFull);
    if (btnFullscreen) {
      btnFullscreen.classList.toggle('active', isFull);
      btnFullscreen.setAttribute('aria-pressed', String(isFull));
      btnFullscreen.title = isFull ? 'Sair da tela cheia (F / Esc)' : 'Apresentar em tela cheia (F)';
      const useEl = btnFullscreen.querySelector('use');
      if (useEl) {
        useEl.setAttribute('href', isFull ? '#i-minimize' : '#i-fullscreen');
      }
    }
    // Reajusta escalas após transição de tela
    setTimeout(recalculateAllScales, 150);
  }

  document.addEventListener('fullscreenchange', updateFullscreenUI);
  document.addEventListener('webkitfullscreenchange', updateFullscreenUI);
  if (btnFullscreen) btnFullscreen.addEventListener('click', toggleFullscreen);

  /* ==========================================================================
     5. ANIMATION & COUNTER ENGINE (Micro-interações e Contadores Numéricos)
     ========================================================================== */
  const prefersReducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isInIframe = window.self !== window.top;

  if (!prefersReducedMotion && !isInIframe) {
    document.documentElement.classList.add('js-anim');
  } else {
    slides.forEach(slide => slide.classList.add('in'));
  }

  function runCounter(el) {
    const target = parseFloat(el.dataset.count);
    if (isNaN(target)) return;
    const suffix = el.dataset.suffix || '';
    const decimals = el.dataset.decimals !== undefined ? parseInt(el.dataset.decimals, 10) : (target % 1 !== 0 ? 1 : 0);
    const duration = CONFIG.ANIM_DURATION;
    const startTime = performance.now();

    const step = (currentTime) => {
      const progress = Math.min((currentTime - startTime) / duration, 1);
      // Easing cúbico para desaceleração natural
      const easeOutCubic = 1 - Math.pow(1 - progress, 3);
      const rawVal = target * easeOutCubic;
      const currentVal = decimals > 0
        ? rawVal.toFixed(decimals).replace('.', ',')
        : Math.round(rawVal);
      el.textContent = currentVal + suffix;
      if (progress < 1) {
        requestAnimationFrame(step);
      }
    };
    requestAnimationFrame(step);
  }

  const animationObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const slide = entry.target.querySelector('.slide');
      if (!slide || slide.classList.contains('in')) return;

      slide.classList.add('in');
      if (!prefersReducedMotion) {
        slide.querySelectorAll('[data-count]').forEach(runCounter);
      }
    });
  }, { threshold: 0.35 });

  wraps.forEach(wrap => animationObserver.observe(wrap));

  // Preparação para exportação PDF / Impressão
  if (btnPdf) {
    btnPdf.addEventListener('click', () => window.print());
  }

  window.addEventListener('beforeprint', () => {
    slides.forEach(slide => {
      slide.classList.add('in');
      slide.querySelectorAll('[data-count]').forEach(el => {
        el.textContent = el.dataset.count + (el.dataset.suffix || '');
      });
    });
  });

  /* ==========================================================================
     6. KEYBOARD & TOUCH GESTURES (Atalhos Universais e Gestos Mobile)
     ========================================================================== */
  document.addEventListener('keydown', (e) => {
    // 1. Se estiver editando texto diretamente, não interceptar teclas
    if (STATE.isEditingText) return;

    // 2. Se o foco estiver em campo de formulário comum
    const activeTagName = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
    if (activeTagName === 'input' || activeTagName === 'textarea') return;

    // 3. Tecla Escape: fecha modais ou desseleciona elemento
    if (e.key === 'Escape') {
      if (modalReelTheater && modalReelTheater.classList.contains('active')) {
        closeReelTheater();
        return;
      }
      if (modalShortcuts && modalShortcuts.classList.contains('active')) {
        closeShortcutsModal();
        return;
      }
      if (STATE.isEditing) {
        deselectElement();
        return;
      }
    }

    // 3.1 Teclas com Reel Theater ativo (Play/Pause com espaço, Mudo com M, Anterior/Próximo)
    if (modalReelTheater && modalReelTheater.classList.contains('active')) {
      if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        toggleReelPlayback();
        return;
      }
      if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        toggleReelMute();
        return;
      }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        prevReel();
        return;
      }
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        nextReel();
        return;
      }
      if (['PageDown', 'PageUp', 'Home', 'End'].includes(e.key)) {
        e.preventDefault();
        return;
      }
    }

    // 4. Atalhos especiais de Apresentação e Ajuda (quando não em modo de ajuste fino)
    if (!STATE.isEditing) {
      if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        toggleFullscreen();
        return;
      }
      if (e.key === '?' || e.key === 'h' || e.key === 'H') {
        e.preventDefault();
        toggleShortcutsModal();
        return;
      }
      if (e.key === 'c' || e.key === 'C') {
        if (!e.ctrlKey && !e.metaKey) {
          e.preventDefault();
          copyCurrentSlideLink();
          return;
        }
      }
    }

    // 5. Ajuste fino de posição no Modo Edição com as setas
    if (STATE.isEditing && STATE.selectedEl) {
      const step = e.shiftKey ? 10 : 2;
      let handled = false;
      const delta = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key];

      if (delta) {
        STATE.group.forEach(({ el }) => {
          el.style.left = ((parseInt(el.style.left) || 0) + delta[0]) + 'px';
          el.style.top = ((parseInt(el.style.top) || 0) + delta[1]) + 'px';
        });
        handled = true;
      }

      if (handled) {
        e.preventDefault();
        syncGizmo();
        return;
      }
    }

    // 6. Navegação entre slides por teclado (Apresentação 16:9 completa)
    if (['ArrowDown', 'ArrowRight', 'PageDown'].includes(e.key) || (e.key === ' ' && !e.shiftKey)) {
      e.preventDefault();
      nextSlide();
      return;
    }

    if (['ArrowUp', 'ArrowLeft', 'PageUp'].includes(e.key) || (e.key === ' ' && e.shiftKey)) {
      e.preventDefault();
      prevSlide();
      return;
    }

    if (e.key === 'Home') {
      e.preventDefault();
      firstSlide();
      return;
    }

    if (e.key === 'End') {
      e.preventDefault();
      lastSlide();
      return;
    }
  });

  // Gestos de toque (Swipe) em dispositivos móveis
  document.addEventListener('touchstart', (e) => {
    if (STATE.isEditing || e.touches.length !== 1) return;
    const touch = e.touches[0];
    STATE.touchStart = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now()
    };
  }, { passive: true });

  document.addEventListener('touchend', (e) => {
    if (STATE.isEditing || !STATE.touchStart.time) return;
    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - STATE.touchStart.x;
    const deltaY = touch.clientY - STATE.touchStart.y;
    const deltaTime = Date.now() - STATE.touchStart.time;

    // Reseta ponto de toque
    STATE.touchStart.time = 0;

    // Descarta gestos muito longos (> 550ms)
    if (deltaTime > 550) return;

    // Se o Reel Theater estiver ativo, gestos de swipe navegam entre os vídeos verticais
    if (modalReelTheater && modalReelTheater.classList.contains('active')) {
      if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > CONFIG.SWIPE_THRESHOLD) {
        if (deltaY < 0) {
          nextReel();
        } else {
          prevReel();
        }
      } else if (Math.abs(deltaX) > CONFIG.SWIPE_THRESHOLD * 1.5) {
        if (deltaX < 0) {
          nextReel();
        } else {
          prevReel();
        }
      }
      return;
    }

    // Detecta swipe vertical com mais ênfase que horizontal
    if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > CONFIG.SWIPE_THRESHOLD) {
      if (deltaY < 0) {
        nextSlide();
      } else {
        prevSlide();
      }
    } else if (Math.abs(deltaX) > CONFIG.SWIPE_THRESHOLD * 1.5) {
      // Swipe horizontal também aceito
      if (deltaX < 0) {
        nextSlide();
      } else {
        prevSlide();
      }
    }
  }, { passive: true });

  /* ==========================================================================
     7. VISUAL EDITOR ENGINE (Gizmo, Drag & Drop, Resize, Inline Text & Save)
     ========================================================================== */

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
    el.style.position = 'absolute';
    el.style.left = (box.left - off.left) + 'px';
    el.style.top = (box.top - off.top) + 'px';
    el.style.width = box.width + 'px';
    el.style.height = box.height + 'px';
    el.style.right = 'auto';
    el.style.bottom = 'auto';
    el.style.margin = '0';
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
      STATE.selectedEl.style.zIndex = currentZ + 1;
      showToast(`Camada ajustada: z-index ${currentZ + 1}`, 1500);
    } else if (act === 'down') {
      const newZ = Math.max(0, currentZ - 1);
      STATE.selectedEl.style.zIndex = newZ;
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
    STATE.initialGroup = STATE.group.map(g => ({ ...g, box: getDesignBox(g.el, STATE.selectedSlide) }));

    document.addEventListener('mousemove', onGizmoMouseMove);
    document.addEventListener('mouseup', onGizmoMouseUp);
  });

  function onGizmoMouseMove(e) {
    if (!STATE.dragMode || !STATE.selectedEl) return;
    const curScale = STATE.initialBox.scale || 1;
    const dx = (e.clientX - STATE.dragStart.x) / curScale;
    const dy = (e.clientY - STATE.dragStart.y) / curScale;

    if (STATE.dragMode === 'move') {
      STATE.initialGroup.forEach(({ el, off, box }) => {
        el.style.left = (Math.round(box.left + dx) - off.left) + 'px';
        el.style.top = (Math.round(box.top + dy) - off.top) + 'px';
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

      STATE.selectedEl.style.width = newW + 'px';
      STATE.selectedEl.style.height = newH + 'px';
      const off = STATE.group[0].off;
      STATE.selectedEl.style.left = (newL - off.left) + 'px';
      STATE.selectedEl.style.top = (newT - off.top) + 'px';
    }

    syncGizmo();
  }

  function onGizmoMouseUp() {
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

  // Salvar Alterações
  if (btnSave) {
    btnSave.addEventListener('click', async () => {
      deselectElement();
      const wasEditing = STATE.isEditing;
      if (wasEditing) toggleEditing();

      // Limpa réplica do documento para salvar HTML limpo
      const cloneDoc = document.documentElement.cloneNode(true);
      cloneDoc.querySelectorAll('.editor-gizmo').forEach(g => g.remove());
      cloneDoc.querySelectorAll('.edit-toast').forEach(t => t.remove());
      cloneDoc.querySelectorAll('.modal-backdrop').forEach(m => m.classList.remove('active'));
      cloneDoc.querySelectorAll('.orientation-overlay').forEach(o => {
        o.classList.remove('dismissed');
        o.removeAttribute('aria-hidden');
      });
      cloneDoc.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
      cloneDoc.querySelectorAll('.elem-editing-text').forEach(el => el.classList.remove('elem-editing-text'));
      cloneDoc.querySelectorAll('.elem-multi').forEach(el => el.classList.remove('elem-multi'));
      cloneDoc.querySelectorAll('.editing-mode').forEach(el => el.classList.remove('editing-mode'));

      const cloneBtnSave = cloneDoc.querySelector('#btn-save');
      if (cloneBtnSave) cloneBtnSave.style.display = 'none';
      const cloneBtnEdit = cloneDoc.querySelector('#btn-edit');
      if (cloneBtnEdit) cloneBtnEdit.classList.remove('active');
      const cloneTxtEdit = cloneDoc.querySelector('#txt-edit');
      if (cloneTxtEdit) cloneTxtEdit.textContent = 'Editar';

      const fullHtml = '<!DOCTYPE html>\n' + cloneDoc.outerHTML;

      // Backup local no navegador
      try {
        localStorage.setItem('cyndy_deck_backup', fullHtml);
      } catch (e) {
        console.warn('Erro ao salvar no localStorage:', e);
      }

      // 1. Salvamento direto pelo seletor nativo do navegador
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

      // 2. Fallback por download
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
  }

  /* ==========================================================================
     8. SHORTCUTS MODAL CONTROLLER (Guia Rápido de Teclas de Atalho)
     ========================================================================== */
  function openShortcutsModal() {
    if (modalShortcuts) {
      modalShortcuts.classList.add('active');
      modalShortcuts.setAttribute('aria-hidden', 'false');
    }
  }

  function closeShortcutsModal() {
    if (modalShortcuts) {
      modalShortcuts.classList.remove('active');
      modalShortcuts.setAttribute('aria-hidden', 'true');
    }
  }

  function toggleShortcutsModal() {
    if (!modalShortcuts) return;
    if (modalShortcuts.classList.contains('active')) {
      closeShortcutsModal();
    } else {
      openShortcutsModal();
    }
  }

  if (btnShortcuts) btnShortcuts.addEventListener('click', toggleShortcutsModal);
  if (btnCloseShortcuts) btnCloseShortcuts.addEventListener('click', closeShortcutsModal);

  if (modalShortcuts) {
    modalShortcuts.addEventListener('click', (e) => {
      if (e.target === modalShortcuts) {
        closeShortcutsModal();
      }
    });
  }

  /* ==========================================================================
     9. REEL THEATER CONTROLLER (Player Vertical 9:16 com Streaming HTTP 206)
     ========================================================================== */
  const REELS_DATA = [
    {
      id: 'video-01',
      title: 'Honda Motobel — Que tal subir de nível? (HR-V)',
      desc: 'Campanha institucional HR-V · Ganchos dinâmicos e cortes rápidos',
      src: 'assets/videos/video-01.mp4',
      poster: 'assets/img/video-01-poster.webp',
      instagram: 'https://www.instagram.com/reel/DcRreoRh6B5/'
    },
    {
      id: 'video-02',
      title: 'Honda Nippon — Peças genuínas & revisão',
      desc: 'Pós-venda & manutenção autorizada · Credibilidade e confiança',
      src: 'assets/videos/video-02.mp4',
      poster: 'assets/img/video-02-poster.webp',
      instagram: 'https://www.instagram.com/reel/Dac_Pm4AYhp/'
    },
    {
      id: 'video-03',
      title: 'Giga Motos Bajaj — Condições especiais & modelos',
      desc: 'Ofertas comerciais & lançamento · Ritmo acelerado para conversão',
      src: 'assets/videos/video-03.mp4',
      poster: 'assets/img/video-03-poster.webp',
      instagram: 'https://www.instagram.com/reel/DeNSMxNh4e4/'
    },
    {
      id: 'video-04',
      title: 'Só Letrados — Comunicação, língua & cultura',
      desc: 'Educação & storytelling envolvente · Humanização e autoridade',
      src: 'assets/videos/video-04.mp4',
      poster: 'assets/img/video-04-poster.webp',
      instagram: 'https://www.instagram.com/reel/DRa8JF4EXNG/'
    },
    {
      id: 'video-05',
      title: 'Mônaco Motocenter — Lançamento Biz Kuromi',
      desc: 'Edição especial Kuromi · Estética jovem, moderna e trendy',
      src: 'assets/videos/video-05.mp4',
      poster: 'assets/img/video-05-poster.webp',
      instagram: 'https://www.instagram.com/reel/DdjMBk-oSbl/'
    },
    {
      id: 'video-06',
      title: 'Mônaco Dream — CBR1000RR-R a moto dos sonhos',
      desc: 'Superesportiva premium · Cinematografia, adrenalina e alto impacto',
      src: 'assets/videos/video-06.mp4',
      poster: 'assets/img/video-06-poster.webp',
      instagram: 'https://www.instagram.com/reel/Dd4L7VcI6zZ/'
    }
  ];

  let currentReelIndex = 0;
  let lastFocusedElement = null;
  const prefetchedMediaUrls = new Set();

  function prefetchReelMedia(url) {
    if (!url || prefetchedMediaUrls.has(url)) return;
    prefetchedMediaUrls.add(url);
    try {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.as = 'fetch';
      link.href = url;
      document.head.appendChild(link);
    } catch (e) {}
  }

  let hasPrefetchedFirstReel = false;
  function prefetchFirstReel() {
    if (hasPrefetchedFirstReel) return;
    hasPrefetchedFirstReel = true;
    prefetchReelMedia('assets/videos/video-01.mp4');
  }

  function updateReelPills(activeIndex) {
    if (!reelPillsContainer) return;
    const dots = reelPillsContainer.querySelectorAll('.reel-dot');
    dots.forEach((dot, i) => {
      const isActive = (i === activeIndex);
      dot.classList.toggle('active', isActive);
      dot.setAttribute('aria-selected', String(isActive));
    });
  }

  function openReelTheater(reelIdOrIndex) {
    if (!modalReelTheater || !reelVideoPlayer) return;

    let index = -1;
    if (typeof reelIdOrIndex === 'number') {
      index = reelIdOrIndex;
    } else if (!isNaN(Number(reelIdOrIndex)) && reelIdOrIndex !== '') {
      index = Number(reelIdOrIndex);
    } else {
      index = REELS_DATA.findIndex(r => r.id === reelIdOrIndex);
    }

    if (index < 0 || index >= REELS_DATA.length) {
      console.warn('Reel não encontrado:', reelIdOrIndex);
      return;
    }

    currentReelIndex = index;
    const reel = REELS_DATA[index];

    // Guarda o elemento com foco atual para restaurar na saída
    if (document.activeElement && typeof document.activeElement.focus === 'function') {
      lastFocusedElement = document.activeElement;
    }

    if (reelTheaterTitle) reelTheaterTitle.textContent = reel.title;
    if (reelTheaterDesc) {
      reelTheaterDesc.textContent = `Reel ${String(index + 1).padStart(2, '0')} de ${String(REELS_DATA.length).padStart(2, '0')} · ${reel.desc}`;
    }
    if (reelInstagramLink) {
      reelInstagramLink.href = reel.instagram;
      reelInstagramLink.setAttribute('aria-label', `Ver publicação oficial de ${reel.title} no Instagram`);
    }

    // Oculta aviso de fallback anterior
    if (reelFallback) reelFallback.style.display = 'none';

    // Atualiza indicadores de pills
    updateReelPills(index);

    // Configura poster e fonte sem comprometer LCP
    reelVideoPlayer.poster = reel.poster;
    reelVideoPlayer.src = reel.src;
    reelVideoPlayer.currentTime = 0;

    modalReelTheater.classList.add('active');
    modalReelTheater.setAttribute('aria-hidden', 'false');

    // Foco acessível no botão fechar
    if (btnCloseReel) {
      setTimeout(() => btnCloseReel.focus(), 60);
    }

    // Prefetch especulativo do próximo reel da sequência
    const nextIdx = (index + 1) % REELS_DATA.length;
    prefetchReelMedia(REELS_DATA[nextIdx].src);

    const playPromise = reelVideoPlayer.play();
    if (playPromise !== undefined) {
      playPromise.catch(err => {
        // Reprodução automática com áudio pausada pelo navegador até interação
        console.log('Autoplay bloqueado pelo navegador, aguardando clique do usuário.');
      });
    }
  }

  function closeReelTheater() {
    if (!modalReelTheater || !modalReelTheater.classList.contains('active')) return;

    if (reelVideoPlayer) {
      reelVideoPlayer.pause();
      reelVideoPlayer.removeAttribute('src');
      reelVideoPlayer.load();
    }

    if (reelFallback) {
      reelFallback.style.display = 'none';
    }

    modalReelTheater.classList.remove('active');
    modalReelTheater.setAttribute('aria-hidden', 'true');

    // Restaura o foco para o elemento original
    if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
      try {
        lastFocusedElement.focus();
      } catch (e) {}
      lastFocusedElement = null;
    }
  }

  function nextReel() {
    const nextIdx = (currentReelIndex + 1) % REELS_DATA.length;
    openReelTheater(nextIdx);
  }

  function prevReel() {
    const prevIdx = (currentReelIndex - 1 + REELS_DATA.length) % REELS_DATA.length;
    openReelTheater(prevIdx);
  }

  function toggleReelPlayback() {
    if (!reelVideoPlayer) return;
    if (reelVideoPlayer.paused) {
      reelVideoPlayer.play();
      showToast('▶️ Reproduzindo', 1000);
    } else {
      reelVideoPlayer.pause();
      showToast('⏸️ Pausado', 1000);
    }
  }

  function toggleReelMute() {
    if (!reelVideoPlayer) return;
    reelVideoPlayer.muted = !reelVideoPlayer.muted;
    showToast(reelVideoPlayer.muted ? '🔇 Áudio silenciado' : '🔊 Áudio ativado', 1500);
  }

  // Tratamento de falha de carregamento no vídeo
  if (reelVideoPlayer) {
    reelVideoPlayer.addEventListener('error', () => {
      const currentReel = REELS_DATA[currentReelIndex];
      if (reelFallback && currentReel) {
        reelFallback.style.display = 'flex';
        if (reelFallbackLink) {
          reelFallbackLink.href = currentReel.instagram;
        }
      }
    });
  }

  if (btnCloseReel) btnCloseReel.addEventListener('click', closeReelTheater);
  if (btnReelPrev) btnReelPrev.addEventListener('click', prevReel);
  if (btnReelNext) btnReelNext.addEventListener('click', nextReel);

  if (modalReelTheater) {
    modalReelTheater.addEventListener('click', (e) => {
      if (e.target === modalReelTheater) {
        closeReelTheater();
      }
    });
  }

  if (reelPillsContainer) {
    reelPillsContainer.querySelectorAll('.reel-dot').forEach(dot => {
      dot.addEventListener('click', () => {
        const idx = dot.dataset.reelIndex;
        if (idx !== undefined) {
          openReelTheater(Number(idx));
        }
      });
    });
  }

  // Desativado: o clique agora navega diretamente para o link externo (Instagram)
  // document.querySelectorAll('a.phone[data-reel-id], a.phone[data-reel-index]').forEach(link => {
  //   link.addEventListener('click', (e) => {
  //     e.preventDefault();
  //     const reelRef = link.dataset.reelId || link.dataset.reelIndex;
  //     openReelTheater(reelRef);
  //   });
  // });

  /* ==========================================================================
     10. DEEP LINKING & QUICK SHARE CONTROLLER
     ========================================================================== */
  function copyCurrentSlideLink() {
    const currentWrap = wraps[STATE.current];
    if (!currentWrap) return;

    const slideId = currentWrap.id || `slide-${STATE.current + 1}`;
    const url = new URL(window.location.href);
    url.hash = '#' + slideId;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url.href).then(() => {
        showToast(`🔗 <b>Link copiado:</b> Slide ${String(STATE.current + 1).padStart(2, '0')} (${slideId})`);
      }).catch(() => {
        fallbackCopyText(url.href);
      });
    } else {
      fallbackCopyText(url.href);
    }
  }

  function fallbackCopyText(text) {
    const input = document.createElement('input');
    input.value = text;
    document.body.appendChild(input);
    input.select();
    try {
      document.execCommand('copy');
      showToast(`🔗 <b>Link copiado com sucesso!</b>`);
    } catch (e) {
      showToast(`Erro ao copiar link.`);
    }
    input.remove();
  }

  if (btnShareSlide) {
    btnShareSlide.addEventListener('click', copyCurrentSlideLink);
  }

  // Sincronização inicial de Deep Linking
  function initDeepLinking() {
    const hash = window.location.hash;
    if (hash && hash.length > 1) {
      const targetWrap = document.querySelector(hash);
      if (targetWrap) {
        const targetIdx = wraps.indexOf(targetWrap);
        if (targetIdx !== -1) {
          // Desloca sem animação para carregamento instantâneo
          setTimeout(() => {
            goToSlide(targetIdx, false, false);
          }, 60);
        }
      }
    }
  }

  window.addEventListener('hashchange', () => {
    const hash = window.location.hash;
    if (hash) {
      const targetWrap = document.querySelector(hash);
      if (targetWrap) {
        const targetIdx = wraps.indexOf(targetWrap);
        if (targetIdx !== -1 && targetIdx !== STATE.current) {
          goToSlide(targetIdx, true, false);
        }
      }
    }
  });

  // Inicializa o roteamento
  initDeepLinking();

  /* ==========================================================================
     11. MOBILE ORIENTATION OVERLAY CONTROLLER (Tarefa #020)
     ========================================================================== */
  const ORIENTATION_STORAGE_KEY = 'orientation_dismissed';
  const landscapeMql = window.matchMedia ? window.matchMedia('(orientation: landscape)') : null;

  function dismissOrientationOverlay() {
    if (!orientationOverlay) return;
    orientationOverlay.classList.add('dismissed');
    orientationOverlay.setAttribute('aria-hidden', 'true');
    try {
      sessionStorage.setItem(ORIENTATION_STORAGE_KEY, 'true');
    } catch (e) {
      // Ignora caso sessionStorage esteja bloqueado no navegador
    }
  }

  function syncOrientationOverlay() {
    if (!orientationOverlay) return;

    let isDismissed = orientationOverlay.classList.contains('dismissed');
    if (!isDismissed) {
      try {
        if (sessionStorage.getItem(ORIENTATION_STORAGE_KEY) === 'true') {
          isDismissed = true;
          orientationOverlay.classList.add('dismissed');
        }
      } catch (e) {}
    }

    const isLandscape = landscapeMql ? landscapeMql.matches : (window.innerWidth > window.innerHeight);
    const isMobileViewport = window.innerWidth <= 900;
    const shouldShow = isMobileViewport && !isLandscape && !isDismissed;

    orientationOverlay.setAttribute('aria-hidden', String(!shouldShow));
    if (isLandscape) {
      recalculateAllScales();
    }
  }

  if (btnDismissOrientation) {
    btnDismissOrientation.addEventListener('click', dismissOrientationOverlay);
  }

  if (landscapeMql) {
    if (typeof landscapeMql.addEventListener === 'function') {
      landscapeMql.addEventListener('change', syncOrientationOverlay);
    } else if (typeof landscapeMql.addListener === 'function') {
      landscapeMql.addListener(syncOrientationOverlay);
    }
  }

  window.addEventListener('resize', syncOrientationOverlay, { passive: true });
  syncOrientationOverlay();

})();
