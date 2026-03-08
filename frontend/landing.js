function toggleTheme() {
  const body = document.documentElement;
  const currentTheme = body.getAttribute('data-theme');
  const btn = document.querySelectorAll('.theme-toggle span');
  if (currentTheme === 'dark') {
    body.removeAttribute('data-theme');
    btn.forEach(el => el.textContent = '🌙');
  } else {
    body.setAttribute('data-theme', 'dark');
    btn.forEach(el => el.textContent = '☀️');
  }
}

function openModal(title, description) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-description').textContent = description;
  document.getElementById('modal').classList.add('active');
}

function closeModal() {
  document.getElementById('modal').classList.remove('active');
}

function notifyMe() {
  const email = document.getElementById('modal-email').value;
  if (email) {
    alert(`Thanks! We'll notify you at ${email}`);
    document.getElementById('modal-email').value = '';
    closeModal();
  } else {
    alert('Please enter your email');
  }
}

window.onclick = function(event) {
  const modal = document.getElementById('modal');
  if (event.target === modal) closeModal();
}

document.querySelector('.mobile-menu-btn').addEventListener('click', function() {
  document.querySelector('.mobile-menu').classList.toggle('active');
});

document.querySelectorAll('.mobile-link, .mobile-launch').forEach(link => {
  link.addEventListener('click', () => {
    document.querySelector('.mobile-menu').classList.remove('active');
  });
});

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  });
});

window.addEventListener('scroll', () => {
  const sections = document.querySelectorAll('section');
  const navLinks = document.querySelectorAll('.nav-link');
  let current = '';
  sections.forEach(section => {
    if (scrollY >= (section.offsetTop - 200)) current = section.getAttribute('id');
  });
  navLinks.forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('href') === `#${current}`) link.classList.add('active');
  });
});