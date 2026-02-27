// ===== Dark Mode Toggle =====
(function () {
  const toggle = document.getElementById('theme-toggle');
  const root = document.documentElement;

  // Load saved theme
  const savedTheme = localStorage.getItem('reviewshield-theme') || 'light';
  root.setAttribute('data-theme', savedTheme);

  toggle.addEventListener('click', () => {
    const current = root.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('reviewshield-theme', next);
  });
})();
