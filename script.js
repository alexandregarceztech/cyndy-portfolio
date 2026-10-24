/**
 * ============================================================================
 * CYNDY PIMENTEL PORTFOLIO — INTERACTIVE ENGINE
 * ============================================================================
 * Módulos:
 *  1. Data de Vídeos & Configuração dos Reels
 *  2. Reel Theater Modal (Player 9:16 com controles e atalhos)
 *  3. Hover Video Preview nos Cards
 *  4. Filtros de Categorias de Reels
 *  5. Animated Number Counters (Estatísticas & Casos Reais)
 *  6. Mobile Navigation Drawer
 *  7. Copiar E-mail & Toast System
 *  8. Active Link Highlight no Scroll
 * ============================================================================
 */

(() => {
  'use strict';

  /* ==========================================================================
     01. BASE DE DADOS DOS REELS (MÍDIAS & LINKS ORIGINAIS PRESERVADOS)
     ========================================================================== */
  const REELS_DATA = [
    {
      id: 'video-01',
      title: 'Honda Motobel — Que tal subir de nível? (HR-V)',
      niche: 'Automotivo',
      category: 'auto',
      desc: 'Lançamento SUV Honda HR-V · Roteiro de desejo e cortes no ritmo da trilha',
      src: 'assets/videos/video-01.mp4',
      poster: 'assets/img/video-01-new.jpg',
      instagram: 'https://www.instagram.com/reel/DcRreoRh6B5/'
    },
    {
      id: 'video-02',
      title: 'Honda Nippon — Peças genuínas & revisão',
      niche: 'Pós-Venda',
      category: 'auto',
      desc: 'Pós-venda e credibilidade · Humanização e valorização de autorizada',
      src: 'assets/videos/video-02.mp4',
      poster: 'assets/img/video-02-new.jpg',
      instagram: 'https://www.instagram.com/reel/Dac_Pm4AYhp/'
    },
    {
      id: 'video-03',
      title: 'Giga Motos Bajaj — Condições especiais & modelos',
      niche: 'Duas Rodas',
      category: 'motos',
      desc: 'Campanha de ofertas e lançamentos · Ritmo ágil para conversão no WhatsApp',
      src: 'assets/videos/video-03.mp4',
      poster: 'assets/img/video-03-new.jpg',
      instagram: 'https://www.instagram.com/reel/DeNSMxNh4e4/'
    },
    {
      id: 'video-04',
      title: 'Só Letrados — Comunicação, língua & cultura',
      niche: 'Educação',
      category: 'vendas',
      desc: 'Educação e storytelling de autoridade · Humanização e didática envolvente',
      src: 'assets/videos/video-04.mp4',
      poster: 'assets/img/video-04-new.jpg',
      instagram: 'https://www.instagram.com/reel/DRa8JF4EXNG/'
    },
    {
      id: 'video-05',
      title: 'Mônaco Motocenter — Lançamento Biz Kuromi',
      niche: 'Lançamento',
      category: 'motos',
      desc: 'Edição especial Honda Biz Kuromi · Estética pop jovem conectada com o público',
      src: 'assets/videos/video-05.mp4',
      poster: 'assets/img/video-05-new.jpg',
      instagram: 'https://www.instagram.com/reel/DdjMBk-oSbl/'
    },
    {
      id: 'video-06',
      title: 'Mônaco Dream — CBR1000RR-R a moto dos sonhos',
      niche: 'Alta Performance',
      category: 'motos',
      desc: 'Superesportiva premium · Cinematografia de impacto valorizando o ronco do motor',
      src: 'assets/videos/video-06.mp4',
      poster: 'assets/img/video-06-new.jpg',
      instagram: 'https://www.instagram.com/reel/Dd4L7VcI6zZ/'
    }
  ];

  let currentReelIndex = 0;
  let lastFocusedElement = null;

  /* ==========================================================================
     02. TOAST SYSTEM
     ========================================================================== */
  const toastContainer = document.getElementById('toast-container');

  function showToast(message, duration = 3000) {
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = 'toast-msg';
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  /* ==========================================================================
     03. CINEMA REEL THEATER MODAL (PLAYER 9:16)
     ========================================================================== */
  const modalTheater = document.getElementById('modal-reel-theater');
  const theaterVideo = document.getElementById('theater-video');
  const theaterTitle = document.getElementById('reel-modal-title');
  const theaterDesc = document.getElementById('reel-modal-desc');
  const theaterInstagramBtn = document.getElementById('theater-instagram-btn');
  const btnCloseTheater = document.getElementById('btn-close-theater');
  const btnTheaterPrev = document.getElementById('btn-theater-prev');
  const btnTheaterNext = document.getElementById('btn-theater-next');
  const theaterDotsContainer = document.getElementById('theater-dots');
  const theaterFallback = document.getElementById('theater-fallback');
  const theaterFallbackLink = document.getElementById('theater-fallback-link');

  // Inicializa indicadores de dots no modal
  function initTheaterDots() {
    if (!theaterDotsContainer) return;
    theaterDotsContainer.innerHTML = '';
    REELS_DATA.forEach((reel, idx) => {
      const dot = document.createElement('span');
      dot.className = `theater-dot ${idx === 0 ? 'active' : ''}`;
      dot.title = reel.title;
      dot.addEventListener('click', () => openReelTheater(idx));
      theaterDotsContainer.appendChild(dot);
    });
  }

  function updateTheaterDots(activeIndex) {
    if (!theaterDotsContainer) return;
    const dots = theaterDotsContainer.querySelectorAll('.theater-dot');
    dots.forEach((dot, idx) => {
      dot.classList.toggle('active', idx === activeIndex);
    });
  }

  function openReelTheater(index) {
    if (!modalTheater || !theaterVideo) return;
    if (index < 0 || index >= REELS_DATA.length) return;

    lastFocusedElement = document.activeElement;
    currentReelIndex = index;
    const reel = REELS_DATA[index];

    // Atualiza metadados
    if (theaterTitle) theaterTitle.textContent = reel.title;
    if (theaterDesc) theaterDesc.textContent = `[${reel.niche}] — ${reel.desc}`;
    if (theaterInstagramBtn) theaterInstagramBtn.href = reel.instagram;

    // Reseta fallback
    if (theaterFallback) theaterFallback.style.display = 'none';

    // Carrega vídeo e poster
    theaterVideo.poster = reel.poster;
    theaterVideo.src = reel.src;
    theaterVideo.currentTime = 0;

    // Atualiza dots
    updateTheaterDots(index);

    // Abre modal
    modalTheater.classList.add('active');
    modalTheater.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    // Foco no fechar
    if (btnCloseTheater) btnCloseTheater.focus();

    // Inicia reprodução
    const playPromise = theaterVideo.play();
    if (playPromise !== undefined) {
      playPromise.catch(() => {
        // Autoplay silenciado ou aguardando interação do usuário
      });
    }
  }

  function closeReelTheater() {
    if (!modalTheater || !modalTheater.classList.contains('active')) return;

    if (theaterVideo) {
      theaterVideo.pause();
      theaterVideo.removeAttribute('src');
      theaterVideo.load();
    }

    modalTheater.classList.remove('active');
    modalTheater.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';

    if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
      try { lastFocusedElement.focus(); } catch (e) {}
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

  if (btnCloseTheater) btnCloseTheater.addEventListener('click', closeReelTheater);
  if (btnTheaterPrev) btnTheaterPrev.addEventListener('click', prevReel);
  if (btnTheaterNext) btnTheaterNext.addEventListener('click', nextReel);

  // Fecha clicando no backdrop
  if (modalTheater) {
    modalTheater.addEventListener('click', (e) => {
      if (e.target === modalTheater) closeReelTheater();
    });
  }

  // Tratamento de erro caso falte codec local
  if (theaterVideo) {
    theaterVideo.addEventListener('error', () => {
      const reel = REELS_DATA[currentReelIndex];
      if (theaterFallback && reel) {
        theaterFallback.style.display = 'flex';
        if (theaterFallbackLink) theaterFallbackLink.href = reel.instagram;
      }
    });
  }

  initTheaterDots();

  /* ==========================================================================
     04. HOVER VIDEO PREVIEW & TRIGGER DE REEL
     ========================================================================== */
  const reelCards = Array.from(document.querySelectorAll('.reel-card'));

  reelCards.forEach(card => {
    const index = parseInt(card.dataset.index, 10);
    const ambientVideo = card.querySelector('.reel-ambient-video');

    // Hover preview (desktop)
    card.addEventListener('mouseenter', () => {
      if (ambientVideo) {
        ambientVideo.currentTime = 0;
        const p = ambientVideo.play();
        if (p !== undefined) p.catch(() => {});
      }
    });

    card.addEventListener('mouseleave', () => {
      if (ambientVideo) {
        ambientVideo.pause();
      }
    });

    // Clique abre o Theater
    card.addEventListener('click', (e) => {
      // Evita abrir se clicou direto no link do instagram
      if (e.target.closest('.reel-ext-btn')) return;
      openReelTheater(index);
    });
  });

  /* ==========================================================================
     05. FILTROS DE CATEGORIA DE REELS
     ========================================================================== */
  const filterTabs = Array.from(document.querySelectorAll('.filter-tab'));

  filterTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      filterTabs.forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      });
      tab.classList.add('active');
      tab.setAttribute('aria-selected', 'true');

      const filter = tab.dataset.filter;

      reelCards.forEach(card => {
        const cat = card.dataset.category;
        if (filter === 'all' || cat === filter) {
          card.classList.remove('hidden');
          card.style.opacity = '0';
          card.style.transform = 'translateY(15px)';
          setTimeout(() => {
            card.style.transition = 'all 0.35s cubic-bezier(0.16, 1, 0.3, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
          }, 30);
        } else {
          card.classList.add('hidden');
        }
      });
    });
  });

  /* ==========================================================================
     06. ANIMATED NUMBER COUNTERS (ESTATÍSTICAS & CASOS REAIS)
     ========================================================================== */
  const countElements = Array.from(document.querySelectorAll('[data-count]'));

  function animateCounter(el) {
    const target = parseFloat(el.dataset.count);
    if (isNaN(target)) return;

    const suffix = el.dataset.suffix || '';
    const decimals = el.dataset.decimals !== undefined ? parseInt(el.dataset.decimals, 10) : (target % 1 !== 0 ? 1 : 0);
    const duration = 1600;
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = Math.min((currentTime - startTime) / duration, 1);
      // Easing cubic out
      const ease = 1 - Math.pow(1 - elapsed, 3);
      const current = target * ease;

      const formatted = decimals > 0 
        ? current.toFixed(decimals).replace('.', ',')
        : Math.round(current);

      el.textContent = formatted + suffix;

      if (elapsed < 1) {
        requestAnimationFrame(update);
      }
    }

    requestAnimationFrame(update);
  }

  const counterObserver = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.35 });

  countElements.forEach(el => counterObserver.observe(el));

  /* ==========================================================================
     07. MOBILE NAVIGATION DRAWER
     ========================================================================== */
  const btnMobileToggle = document.getElementById('btn-mobile-toggle');
  const btnDrawerClose = document.getElementById('btn-drawer-close');
  const mobileDrawer = document.getElementById('mobile-drawer');
  const drawerLinks = Array.from(document.querySelectorAll('.drawer-item'));

  function openDrawer() {
    if (!mobileDrawer) return;
    mobileDrawer.classList.add('active');
    mobileDrawer.setAttribute('aria-hidden', 'false');
    btnMobileToggle?.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer() {
    if (!mobileDrawer) return;
    mobileDrawer.classList.remove('active');
    mobileDrawer.setAttribute('aria-hidden', 'true');
    btnMobileToggle?.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  if (btnMobileToggle) btnMobileToggle.addEventListener('click', openDrawer);
  if (btnDrawerClose) btnDrawerClose.addEventListener('click', closeDrawer);
  drawerLinks.forEach(link => link.addEventListener('click', closeDrawer));

  /* ==========================================================================
     08. COPIAR E-MAIL COM TOAST
     ========================================================================== */
  const btnCopyEmail = document.getElementById('btn-copy-email');
  const labelCopyEmail = document.getElementById('label-copy-email');

  if (btnCopyEmail) {
    const handleCopy = () => {
      const email = 'pimentelcryssy@gmail.com';
      navigator.clipboard.writeText(email).then(() => {
        if (labelCopyEmail) labelCopyEmail.textContent = 'Copiado!';
        showToast('✓ E-mail copiado para a área de transferência: ' + email);
        setTimeout(() => {
          if (labelCopyEmail) labelCopyEmail.textContent = 'Copiar E-mail';
        }, 3000);
      }).catch(() => {
        showToast('E-mail: ' + email);
      });
    };

    btnCopyEmail.addEventListener('click', handleCopy);
    btnCopyEmail.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleCopy();
      }
    });
  }

  /* ==========================================================================
     09. ATALHOS DE TECLADO (CINEMA THEATER & ESC)
     ========================================================================== */
  document.addEventListener('keydown', (e) => {
    if (modalTheater && modalTheater.classList.contains('active')) {
      if (e.key === 'Escape') {
        e.preventDefault();
        closeReelTheater();
        return;
      }
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        nextReel();
        return;
      }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        prevReel();
        return;
      }
      if (e.key === ' ' || e.code === 'Space') {
        if (theaterVideo) {
          e.preventDefault();
          if (theaterVideo.paused) {
            theaterVideo.play();
            showToast('▶ Reproduzindo');
          } else {
            theaterVideo.pause();
            showToast('⏸ Pausado');
          }
        }
      }
    }
  });

  /* ==========================================================================
     10. ACTIVE LINK HIGHLIGHT NO SCROLL
     ========================================================================== */
  const navItems = Array.from(document.querySelectorAll('.nav-links .nav-item'));
  const trackedSections = navItems
    .map(link => {
      const id = link.getAttribute('href')?.replace('#', '');
      return id ? document.getElementById(id) : null;
    })
    .filter(Boolean);

  window.addEventListener('scroll', () => {
    const scrollPos = window.scrollY + 200;
    trackedSections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute('id');

      if (scrollPos >= top && scrollPos < top + height) {
        navItems.forEach(item => {
          const href = item.getAttribute('href');
          item.classList.toggle('active', href === `#${id}`);
        });
      }
    });
  }, { passive: true });

  console.log('[Cyndy Portfolio] Haute Luxe Engine inicializado com sucesso.');
})();
