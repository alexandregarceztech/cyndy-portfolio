/**
 * ============================================================================
 * CYNDY PIMENTEL — PORTFÓLIO EDITORIAL 2026 (BEHANCE ENGINE)
 * ============================================================================
 * Módulos Integrados:
 *  1. Base de dados dos 6 Reels & Casos
 *  2. Reel Theater Modal (Player 9:16 com atalhos e dots)
 *  3. Video Preview Dinâmico nos Mockups de Smartphone
 *  4. Filtros por Nicho (Automotivo, Duas Rodas, Educação/Vendas)
 *  5. Contadores Numéricos Animados & Gráfico Donut de Seguidores
 *  6. Mobile Navigation Drawer (Painel Lateral Editorial)
 *  7. Copiar E-mail Profissional & Sistema de Toast
 *  8. Active Link Highlight no Scroll
 * ============================================================================
 */

(() => {
  'use strict';

  /* ==========================================================================
     01. BASE DE DADOS DOS REELS (6 VÍDEOS REAIS & METADADOS PRESERVADOS)
     ========================================================================== */
  const REELS_DATA = [
    {
      id: 'video-01',
      title: 'Honda Motobel — Que tal subir de nível? (HR-V)',
      niche: 'Automotivo',
      category: 'auto',
      desc: 'Lançamento SUV Honda HR-V · Roteiro de desejo e cortes no ritmo da trilha sonora',
      src: 'assets/videos/video-01.mp4',
      poster: 'assets/img/video-01-new.jpg',
      instagram: 'https://www.instagram.com/reel/DcRreoRh6B5/'
    },
    {
      id: 'video-02',
      title: 'Honda Nippon — Peças genuínas & revisão',
      niche: 'Pós-Venda',
      category: 'auto',
      desc: 'Pós-venda e credibilidade autorizada · Humanização e valorização de marca',
      src: 'assets/videos/video-02.mp4',
      poster: 'assets/img/video-02-new.jpg',
      instagram: 'https://www.instagram.com/reel/Dac_Pm4AYhp/'
    },
    {
      id: 'video-03',
      title: 'Giga Motos Bajaj — Condições especiais & modelos',
      niche: 'Duas Rodas',
      category: 'motos',
      desc: 'Campanha comercial e ofertas · Ritmo ágil para conversão direta no WhatsApp',
      src: 'assets/videos/video-03.mp4',
      poster: 'assets/img/video-03-new.jpg',
      instagram: 'https://www.instagram.com/reel/DeNSMxNh4e4/'
    },
    {
      id: 'video-04',
      title: 'Só Letrados — Comunicação, língua & cultura',
      niche: 'Educação',
      category: 'vendas',
      desc: 'Educação e storytelling de autoridade · Didática envolvente e humanização',
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
     02. TOAST NOTIFICATION SYSTEM
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
      toast.style.transform = 'translateY(12px)';
      toast.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
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

    if (theaterTitle) theaterTitle.textContent = reel.title;
    if (theaterDesc) theaterDesc.textContent = `[${reel.niche}] — ${reel.desc}`;
    if (theaterInstagramBtn) theaterInstagramBtn.href = reel.instagram;

    if (theaterFallback) theaterFallback.style.display = 'none';

    theaterVideo.poster = reel.poster;
    theaterVideo.src = reel.src;
    theaterVideo.currentTime = 0;

    updateTheaterDots(index);

    modalTheater.classList.add('active');
    modalTheater.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    if (btnCloseTheater) btnCloseTheater.focus();

    const playPromise = theaterVideo.play();
    if (playPromise !== undefined) {
      playPromise.catch(() => {
        // Bloqueio de autoplay do navegador aguardando clique explícito
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

  if (modalTheater) {
    modalTheater.addEventListener('click', (e) => {
      if (e.target === modalTheater) closeReelTheater();
    });
  }

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
     04. HOVER & CLIQUE NOS REEL FIGURES
     ========================================================================== */
  const reelFigures = Array.from(document.querySelectorAll('.reel-figure'));

  reelFigures.forEach(fig => {
    const index = parseInt(fig.dataset.index, 10);
    const videoPreview = fig.querySelector('.reel-video-preview');

    // Desktop hover preview
    fig.addEventListener('mouseenter', () => {
      if (videoPreview) {
        videoPreview.currentTime = 0;
        const p = videoPreview.play();
        if (p !== undefined) p.catch(() => {});
      }
    });

    fig.addEventListener('mouseleave', () => {
      if (videoPreview) {
        videoPreview.pause();
      }
    });

    // Clique abre o Reel Theater
    fig.addEventListener('click', (e) => {
      if (e.target.closest('.link-ig-corner')) return;
      openReelTheater(index);
    });
  });

  /* ==========================================================================
     05. FILTROS POR NICHO DE REELS
     ========================================================================== */
  const filterPills = Array.from(document.querySelectorAll('.f-pill'));

  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => {
        p.classList.remove('active');
        p.setAttribute('aria-selected', 'false');
      });
      pill.classList.add('active');
      pill.setAttribute('aria-selected', 'true');

      const filter = pill.dataset.filter;

      reelFigures.forEach(fig => {
        const cat = fig.dataset.category;
        if (filter === 'all' || cat === filter) {
          fig.classList.remove('hidden');
          fig.style.opacity = '0';
          fig.style.transform = 'translateY(14px)';
          setTimeout(() => {
            fig.style.transition = 'all 0.35s cubic-bezier(0.16, 1, 0.3, 1)';
            fig.style.opacity = '1';
            fig.style.transform = 'translateY(0)';
          }, 30);
        } else {
          fig.classList.add('hidden');
        }
      });
    });
  });

  /* ==========================================================================
     06. CONTADORES NUMÉRICOS ANIMADOS & DONUT SVG
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

  // Animação do Gráfico Donut (58,1% novos seguidores)
  const donutFill = document.querySelector('.donut-svg .d-fill');
  if (donutFill) {
    const donutObserver = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          // Raio = 48 -> Perímetro = 2 * PI * 48 ≈ 301.6
          // 58.1% preenchido -> offset = 301.6 * (1 - 0.581) ≈ 126
          donutFill.style.strokeDashoffset = '126';
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });

    donutObserver.observe(donutFill);
  }

  /* ==========================================================================
     07. PAINEL DE NAVEGAÇÃO MOBILE
     ========================================================================== */
  const btnBurger = document.getElementById('btn-burger');
  const btnClosePanel = document.getElementById('btn-close-panel');
  const mobileNavPanel = document.getElementById('mobile-nav-panel');
  const mobileLinks = Array.from(document.querySelectorAll('.mobile-nav-links .m-link'));

  function openMobileNav() {
    if (!mobileNavPanel) return;
    mobileNavPanel.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeMobileNav() {
    if (!mobileNavPanel) return;
    mobileNavPanel.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (btnBurger) btnBurger.addEventListener('click', openMobileNav);
  if (btnClosePanel) btnClosePanel.addEventListener('click', closeMobileNav);
  mobileLinks.forEach(link => link.addEventListener('click', closeMobileNav));

  /* ==========================================================================
     08. COPIAR E-MAIL COM FEEDBACK TOAST
     ========================================================================== */
  const btnCopyEmail = document.getElementById('btn-copy-email');
  const labelCopyEmail = document.getElementById('label-copy-email');

  if (btnCopyEmail) {
    const handleCopy = () => {
      const email = 'pimentelcryssy@gmail.com';
      navigator.clipboard.writeText(email).then(() => {
        if (labelCopyEmail) labelCopyEmail.textContent = 'Copiado!';
        showToast('✓ E-mail copiado: ' + email);
        setTimeout(() => {
          if (labelCopyEmail) labelCopyEmail.textContent = 'Copiar';
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
     09. ATALHOS DE TECLADO (PLAYER THEATER)
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
  const headerLinks = Array.from(document.querySelectorAll('.header-menu .menu-link'));
  const trackedSections = headerLinks
    .map(link => {
      const id = link.getAttribute('href')?.replace('#', '');
      return id ? document.getElementById(id) : null;
    })
    .filter(Boolean);

  window.addEventListener('scroll', () => {
    const scrollPos = window.scrollY + 180;
    trackedSections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute('id');

      if (scrollPos >= top && scrollPos < top + height) {
        headerLinks.forEach(item => {
          const href = item.getAttribute('href');
          item.classList.toggle('active', href === `#${id}`);
        });
      }
    });
  }, { passive: true });

  console.log('[Cyndy Portfolio 2026] Behance Editorial Engine ativo com sucesso.');
})();
