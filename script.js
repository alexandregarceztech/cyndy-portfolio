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
 *  7. Layout salvo (layout.js) + carga sob demanda do editor visual (editor.js)
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
      if (STATE.isEditing && DECK.editor) DECK.editor.sync();
    });
  }

  const resizeObserver = new ResizeObserver(entries => {
    for (const entry of entries) {
      applySlideScale(entry.target);
    }
    if (STATE.isEditing && DECK.editor) DECK.editor.sync();
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
      if (modalShortcuts && modalShortcuts.classList.contains('active')) {
        closeShortcutsModal();
        return;
      }
      if (STATE.isEditing && DECK.editor) {
        DECK.editor.deselect();
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

    // 5. Ajuste fino de posição no Modo Edição com as setas (editor.js)
    if (STATE.isEditing && DECK.editor && DECK.editor.handleKey(e)) return;

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
     7. LAYOUT SALVO + CARGA DO EDITOR VISUAL (o editor em si está em editor.js)
     ========================================================================== */

  /* --- Layout salvo (layout.js): só o que foi mexido no editor, aplicado por cima do CSS --- */
  const LAYOUT = window.CYNDY_LAYOUT || { styles: {}, text: {} };
  LAYOUT.styles = LAYOUT.styles || {};
  LAYOUT.text = LAYOUT.text || {};

  // Chave estável: id do slide + caminho de índices de filhos dentro do .slide
  function elementKey(el) {
    const wrap = el.closest('.slide-wrap');
    const slide = el.closest('.slide');
    if (!wrap || !slide || !wrap.id || el === slide) return null;
    const path = [];
    for (let n = el; n !== slide; n = n.parentElement) {
      path.unshift(Array.prototype.indexOf.call(n.parentElement.children, n));
    }
    return wrap.id + ':' + path.join('/');
  }

  function resolveKey(key) {
    const [id, path] = key.split(':');
    let node = document.querySelector('#' + id + ' .slide');
    if (!node || !path) return null;
    for (const i of path.split('/')) {
      node = node && node.children[Number(i)];
    }
    return node || null;
  }

  function applyLayout() {
    const rules = [];
    Object.entries(LAYOUT.styles).forEach(([key, st]) => {
      const el = resolveKey(key);
      if (!el) return;
      el.setAttribute('data-lk', key);
      const decl = ['left', 'top', 'width', 'height']
        .filter(k => st[k] !== undefined)
        .map(k => `${k}: ${st[k]}px !important`);
      if (decl.length) decl.push('position: absolute !important', 'right: auto !important', 'bottom: auto !important', 'margin: 0 !important');
      if (st.zIndex !== undefined) decl.push(`z-index: ${st.zIndex} !important`);
      rules.push(`[data-lk="${key}"] { ${decl.join('; ')} }`);
    });
    Object.entries(LAYOUT.text).forEach(([key, html]) => {
      const el = resolveKey(key);
      if (el) el.innerHTML = html;
    });
    if (!rules.length) return;
    const style = document.createElement('style');
    style.id = 'layout-overrides';
    // Só no layout de computador: no celular o CSS responsivo manda
    style.textContent = '@media (min-width: 901px), (min-width: 769px) and (orientation: landscape) {\n'
      + rules.join('\n') + '\n}';
    document.head.appendChild(style);
  }
  applyLayout();

  /* --- Editor visual: arquivo separado (editor.js), baixado só com ?edit na URL --- */
  const DECK = window.CyndyDeck = { STATE, CONFIG, slides, showToast, LAYOUT, elementKey, btnEdit, btnSave, txtEdit, editor: null };
  if (new URLSearchParams(window.location.search).has('edit')) {
    if (btnEdit) btnEdit.hidden = false;
    document.body.classList.add('edit-enabled');
    const editorScript = document.createElement('script');
    editorScript.src = 'editor.js' + (document.currentScript ? new URL(document.currentScript.src).search : '');
    document.body.appendChild(editorScript);
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
