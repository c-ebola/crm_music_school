const form = document.getElementById('login-form');
const messageEl = document.getElementById('message');

function showMessage(text) {
    messageEl.textContent = text;
    messageEl.className = 'message error';
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    messageEl.classList.add('hidden');

    const body = new URLSearchParams();
    body.set('username', document.getElementById('email').value.trim());
    body.set('password', document.getElementById('password').value);

    try {
        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body,
        });
        if (resp.ok) {
            const data = await resp.json();
            localStorage.setItem('token', data.access_token);
            window.location.href = '/users';
        } else {
            const err = await resp.json();
            showMessage(err.detail || 'Ошибка входа');
        }
    } catch (err) {
        showMessage('Сетевая ошибка: ' + err.message);
    }
});
