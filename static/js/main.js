// static/js/main.js — финальная версия (январь 2026)

function getUserId() {
  return localStorage.getItem('user_id') || null;
}

function saveUserId(userId) {
  if (userId) localStorage.setItem('user_id', userId);
}

function logout() {
  if (confirm('Выйти из аккаунта?')) {
    localStorage.removeItem('user_id');
    localStorage.removeItem('cart');
    window.location.href = '/static/login.html';
  }
}

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.style.display = 'block';
  }
}

function showSuccess(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 5000);
  }
}

async function apiFetch(url, options = {}) {
  try {
    const fetchOptions = { ...options };

    // НЕ трогаем Content-Type для FormData — браузер сам ставит multipart/form-data
    if (fetchOptions.body instanceof FormData) {
      if (fetchOptions.headers) delete fetchOptions.headers['Content-Type'];
    } else if (fetchOptions.body && typeof fetchOptions.body === 'object' && !(fetchOptions.body instanceof Blob)) {
      fetchOptions.body = JSON.stringify(fetchOptions.body);
      fetchOptions.headers = { 'Content-Type': 'application/json', ...fetchOptions.headers };
    }

    const res = await fetch(url, fetchOptions);

    let data;
    try {
      data = await res.json();
    } catch {
      data = { message: await res.text() || 'Нет ответа' };
    }

    if (!res.ok) {
      const errorMsg = data.detail || data.message || `Ошибка ${res.status}: ${res.statusText}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (err) {
    console.error('apiFetch ошибка:', err);
    throw err;
  }
}

window.addEventListener('load', () => {
  const path = window.location.pathname.toLowerCase();
  if (!getUserId() && 
      !path.includes('login.html') && 
      !path.includes('register.html') &&
      !path.includes('index.html') &&
      !path.includes('test.html')) {
    window.location.href = '/static/login.html';
  }
});

console.log('main.js загружен — финальная версия 2026-01');