/**
 * Social Media Downloader Landing Page Client Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initMockupTabs();
  initMockupDemo();
  initFaqAccordion();
});

/* --------------------------------------------------------------------------
   Theme Switcher (Light / Dark)
   -------------------------------------------------------------------------- */
function initTheme() {
  const themeToggle = document.getElementById('theme-toggle');
  const root = document.documentElement;

  // Retrieve saved preference or default to auto
  const savedTheme = localStorage.getItem('theme-preference') || 'auto';
  setTheme(savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = root.getAttribute('data-theme');
      let nextTheme;

      if (current === 'light') {
        nextTheme = 'dark';
      } else if (current === 'dark') {
        nextTheme = 'light';
      } else {
        // If currently auto, toggle based on actual system preference
        const isSystemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        nextTheme = isSystemDark ? 'light' : 'dark';
      }

      setTheme(nextTheme);
    });
  }

  // Listen for OS system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (localStorage.getItem('theme-preference') === 'auto') {
      root.setAttribute('data-theme', 'auto');
    }
  });

  function setTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem('theme-preference', theme);
  }
}

/* --------------------------------------------------------------------------
   Mockup Tab Switcher (Single Video vs Playlist)
   -------------------------------------------------------------------------- */
function initMockupTabs() {
  const tabSingle = document.getElementById('tab-single');
  const tabPlaylist = document.getElementById('tab-playlist');
  const viewSingle = document.getElementById('view-single');
  const viewPlaylist = document.getElementById('view-playlist');

  if (tabSingle && tabPlaylist && viewSingle && viewPlaylist) {
    tabSingle.addEventListener('click', () => {
      tabSingle.classList.add('active');
      tabPlaylist.classList.remove('active');
      viewSingle.style.display = 'block';
      viewPlaylist.style.display = 'none';
    });

    tabPlaylist.addEventListener('click', () => {
      tabPlaylist.classList.add('active');
      tabSingle.classList.remove('active');
      viewSingle.style.display = 'none';
      viewPlaylist.style.display = 'block';
    });
  }
}

/* --------------------------------------------------------------------------
   Interactive Mockup UI Demo
   -------------------------------------------------------------------------- */
function initMockupDemo() {
  const pasteBtn = document.querySelector('.mockup-btn-paste');
  const inputPlaceholder = document.querySelector('.mockup-placeholder');
  const pills = document.querySelectorAll('.mockup-pill');
  const progressPercent = document.querySelector('.progress-percent');
  const progressFill = document.querySelector('.progress-bar-fill');
  const progressTitle = document.querySelector('.progress-title');

  const demoItems = [
    {
      url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
      title: 'Never Gonna Give You Up (Official Music Video).mp4',
      type: 'mp4'
    },
    {
      url: 'https://www.tiktok.com/@creator/video/7345678901234567890',
      title: 'TikTok_Dance_Challenge_NoWatermark_HD.mp4',
      type: 'mp4'
    },
    {
      url: 'https://soundcloud.com/artist/hit-song-remix',
      title: 'Summer_Chill_Vibes_Remix_320kbps.mp3',
      type: 'mp3'
    }
  ];

  let currentIndex = 0;

  if (pasteBtn && inputPlaceholder) {
    pasteBtn.addEventListener('click', () => {
      currentIndex = (currentIndex + 1) % demoItems.length;
      const item = demoItems[currentIndex];

      // Simulate typing/paste
      inputPlaceholder.style.opacity = '0';
      setTimeout(() => {
        inputPlaceholder.textContent = item.url;
        inputPlaceholder.style.opacity = '1';
        if (progressTitle) progressTitle.textContent = item.title;

        // Animate progress bar simulation
        animateProgressBar();
      }, 150);
    });
  }

  // Pill tab selection
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
    });
  });

  function animateProgressBar() {
    if (!progressFill || !progressPercent) return;
    progressFill.style.width = '0%';
    progressPercent.textContent = '0% • 0 MB/s';

    let width = 0;
    const interval = setInterval(() => {
      if (width >= 100) {
        clearInterval(interval);
        progressPercent.textContent = 'Hoàn tất! ✓';
      } else {
        width += Math.floor(Math.random() * 15) + 8;
        if (width > 100) width = 100;
        progressFill.style.width = width + '%';
        const speed = (Math.random() * 8 + 14).toFixed(1);
        progressPercent.textContent = `${width}% • ${speed} MB/s`;
      }
    }, 120);
  }
}

/* --------------------------------------------------------------------------
   Single-Open FAQ Accordion
   -------------------------------------------------------------------------- */
function initFaqAccordion() {
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach(item => {
    item.addEventListener('toggle', () => {
      if (item.open) {
        faqItems.forEach(other => {
          if (other !== item && other.open) {
            other.removeAttribute('open');
          }
        });
      }
    });
  });
}
