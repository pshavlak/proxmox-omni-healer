/**
 * API client for Золотаревка admin panel.
 * All functions return Promises with parsed JSON.
 */

// Проверка ответа — если 401, редирект на логин
async function apiFetch(url, options = {}) {
  const res = await window.fetch(url, options);
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Сессия истекла');
  }
  return res;
}

const api = {
  // ====== Pages ======
  getPages: () =>
    apiFetch('/api/pages').then(r => {
      if (!r.ok) throw new Error('Ошибка загрузки страниц');
      return r.json();
    }),

  createPage: (data) =>
    apiFetch('/api/pages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Ошибка создания'); });
      return r.json();
    }),

  updatePage: (id, data) =>
    apiFetch(`/api/pages/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Ошибка обновления'); });
      return r.json();
    }),

  deletePage: (id) =>
    apiFetch(`/api/pages/${id}`, {
      method: 'DELETE',
    }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Ошибка удаления'); });
      return r.json();
    }),

  reorderPages: (items) =>
    apiFetch('/api/pages/reorder', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
    }).then(r => {
      if (!r.ok) throw new Error('Ошибка сортировки');
      return r.json();
    }),

  // ====== Blocks ======
  getBlocks: (pageId) =>
    apiFetch(`/api/pages/${pageId}/blocks`).then(r => {
      if (!r.ok) throw new Error('Ошибка загрузки блоков');
      return r.json();
    }),

  saveBlocks: (pageId, blocks) =>
    apiFetch(`/api/pages/${pageId}/blocks`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(blocks),
    }).then(r => {
      if (!r.ok) throw new Error('Ошибка сохранения блоков');
      return r.json();
    }),

  moveBlock: (id, direction) =>
    apiFetch(`/api/blocks/${id}/move?direction=${direction}`, {
      method: 'POST',
    }).then(r => {
      if (!r.ok) throw new Error('Ошибка перемещения блока');
      return r.json();
    }),

  // ====== Roles ======
  getRoles: () =>
    apiFetch('/api/roles').then(r => {
      if (!r.ok) throw new Error('Ошибка загрузки ролей');
      return r.json();
    }),

  createRole: (data) =>
    apiFetch('/api/roles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Ошибка создания'); });
      return r.json();
    }),

  updateRole: (id, data) =>
    apiFetch(`/api/roles/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Ошибка обновления'); });
      return r.json();
    }),

  deleteRole: (id) =>
    apiFetch(`/api/roles/${id}`, {
      method: 'DELETE',
    }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Ошибка удаления'); });
      return r.json();
    }),

  // ====== Settings ======
  getSettings: () =>
    apiFetch('/api/settings').then(r => {
      if (!r.ok) throw new Error('Ошибка загрузки настроек');
      return r.json();
    }),

  saveSettings: (settings) =>
    apiFetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    }).then(r => {
      if (!r.ok) throw new Error('Ошибка сохранения настроек');
      return r.json();
    }),

  // ====== Media ======
  getMedia: () =>
    apiFetch('/api/media').then(r => {
      if (!r.ok) throw new Error('Ошибка загрузки медиа');
      return r.json();
    }),

  uploadFile: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return apiFetch('/api/media/upload', {
      method: 'POST',
      body: fd,
    }).then(r => {
      if (!r.ok) throw new Error('Ошибка загрузки файла');
      return r.json();
    });
  },

  deleteMedia: (id) =>
    apiFetch(`/api/media/${id}`, {
      method: 'DELETE',
    }).then(r => {
      if (!r.ok) throw new Error('Ошибка удаления файла');
      return r.json();
    }),

  // ====== Users ======
  getUsers: () =>
    apiFetch('/api/users').then(r => {
      if (!r.ok) throw new Error('Ошибка загрузки пользователей');
      return r.json();
    }),

  createUser: (username, password, role) =>
    apiFetch('/api/users', {
      method: 'POST',
      body: new URLSearchParams({ username, password, role }),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Ошибка создания'); });
      return r.json();
    }),

  deleteUser: (id) =>
    apiFetch(`/api/users/${id}`, {
      method: 'DELETE',
    }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Ошибка удаления'); });
      return r.json();
    }),

  changePassword: (oldPassword, newPassword) =>
    apiFetch('/api/change-password', {
      method: 'POST',
      body: new URLSearchParams({ old_password: oldPassword, new_password: newPassword }),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Ошибка'); });
      return r.json();
    }),
};
