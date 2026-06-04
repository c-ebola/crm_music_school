// Единое боковое меню по роли. Требует подключённый ранее auth.js.
// На странице нужен пустой контейнер: <aside id="sidebar"></aside>
(function () {
  const ROLE_NAMES = {
    admin: 'Админ сети',
    branch_admin: 'Админ филиала',
    methodist: 'Методист',
    accountant: 'Бухгалтер',
    manager: 'Менеджер',
    teacher: 'Преподаватель',
  };

  const HOME = { label: 'Главный экран', href: '/' };

  const NAV = {
    manager: [HOME,
      { label: 'Новый лид', href: '/leads' },
      { label: 'Конверсия в ученика', href: '/convert' }],
    accountant: [HOME,
      { label: 'Каталог абонементов', href: '/plans' },
      { label: 'Оформить абонемент', href: '/subscription-new' },
      { label: 'Фиксация оплаты', href: '/payment-new' },
      { label: 'Финансы ученика', href: '/student-finance' }],
    methodist: [HOME,
      { label: 'Расписание', href: '/schedule' },
      { label: 'Уроки', href: '/lessons' },
      { label: 'Расписание ученика', href: '/student-schedule' }],
    teacher: [HOME,
      { label: 'Моё расписание', href: '/my-schedule' },
      { label: 'Домашние задания', href: '/homeworks' }],
    branch_admin: [HOME,
      { label: 'Новый лид', href: '/leads' },
      { label: 'Конверсия в ученика', href: '/convert' },
      { label: 'Расписание', href: '/schedule' },
      { label: 'Расписание ученика', href: '/student-schedule' },
      { label: 'Уроки', href: '/lessons' },
      { label: 'Подтверждение оплат', href: '/confirm-payments' }],
    // У админа сети сайдбар лёгкий — все ролевые формы вынесены на главную
    admin: [HOME,
      { label: 'Пользователи', href: '/users' }],
  };

  function esc(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : s; return d.innerHTML; }
  function norm(p) { return (p || '').replace(/\/+$/, '') || '/'; }

  function render(me) {
    const role = me && me.role ? me.role.code : null;
    const items = NAV[role] || (me && me.is_superuser ? NAV.admin : [HOME]);
    const path = norm(window.location.pathname);
    const links = items.map(function (it) {
      const active = norm(it.href) === path ? ' active' : '';
      return '<a href="' + it.href + '" class="nav-item' + active + '">' + esc(it.label) + '</a>';
    }).join('');
    const name = me ? (me.full_name || me.email || '') : '';
    const roleName = ROLE_NAMES[role] || (me && me.is_superuser ? 'Админ сети' : '—');
    return '' +
      '<div class="brand">♪ МузCRM</div>' +
      '<div class="brand-sub">' + esc(roleName) + '</div>' +
      '<nav class="nav">' + links + '</nav>' +
      '<div style="margin-top:24px; padding-top:16px; border-top:1px solid #e5e5ea;">' +
        '<div style="font-size:13px; color:#86868b; margin-bottom:8px;">' + esc(name) + '</div>' +
        '<button id="nav-logout" style="width:100%; padding:8px; border:1px solid #d2d2d7; border-radius:8px; background:#fff; cursor:pointer; font-size:13px;">Выход</button>' +
      '</div>';
  }

  async function mount() {
    const aside = document.getElementById('sidebar');
    if (!aside) return;
    aside.classList.add('sidebar');
    let me = null;
    try { me = await window.Auth.getMe(); } catch (e) { return; }
    aside.innerHTML = render(me);
    const lo = document.getElementById('nav-logout');
    if (lo) lo.addEventListener('click', function () { window.Auth.logout(); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
