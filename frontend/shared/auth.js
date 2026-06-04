// Общий слой авторизации. Подключать ПЕРЕД nav.js на всех защищённых страницах.
(function () {
  const TOKEN_KEY = 'token';

  function getToken() { return localStorage.getItem(TOKEN_KEY); }
  function clearToken() { localStorage.removeItem(TOKEN_KEY); }
  function gotoLogin() { window.location.href = '/login'; }

  async function apiFetch(url, opts = {}) {
    const token = getToken();
    const headers = Object.assign({}, opts.headers || {});
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const res = await fetch(url, Object.assign({}, opts, { headers }));
    if (res.status === 401) { clearToken(); gotoLogin(); throw new Error('unauthorized'); }
    return res;
  }

  let _me = null;
  let _mePromise = null;
  function getMe() {
    if (_me) return Promise.resolve(_me);
    if (!_mePromise) {
      _mePromise = apiFetch('/api/auth/me')
        .then(r => r.json())
        .then(me => {
          _me = me;
          window.CURRENT_USER = me;
          window.CURRENT_ROLE = me && me.role ? me.role.code : null;
          return me;
        });
    }
    return _mePromise;
  }

  function roleAllowed(me, allowed) {
    if (!me) return false;
    if (me.is_superuser) return true;
    const code = me.role ? me.role.code : null;
    return allowed.indexOf(code) !== -1;
  }

  async function requireRole(allowed) {
    if (!getToken()) { gotoLogin(); return false; }
    try {
      const me = await getMe();
      if (!roleAllowed(me, allowed)) { window.location.href = '/'; return false; }
      return true;
    } catch (e) { return false; }
  }

  function logout() { clearToken(); gotoLogin(); }

  window.Auth = { apiFetch, getMe, requireRole, roleAllowed, logout, getToken };
  window.apiFetch = apiFetch; // удобный алиас
})();
