/**
 * Золотаревка — Admin Panel Logic
 * All data operations go through api.js (HTTP API calls).
 */

// ====== STATE ======
let pages = [];
let pageBlocks = {}; // { pageId: [Block, ...] }
let roles = [];
let settings = {};
let mediaItems = [];
let currentPageId = null;
let editingBlockId = null;
let nextBlockIdCounter = 1000;
let currentView = 'pages'; // 'pages' | 'users' | 'settings' | 'media'

// ====== UTILITY ======
function escapeHtml(s) {
  if (typeof s !== 'string') return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2500);
}

function generatePageSlug() {
  const name = document.getElementById('new-page-name').value.trim();
  const slug = name.toLowerCase()
    .replace(/[^а-яa-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
  document.getElementById('new-page-slug').value = slug;
}

function showLoading(el) {
  el.innerHTML = '<div class="loading-spinner"><div class="spinner"></div> Загрузка...</div>';
}

// ====== INIT ======
async function init() {
  try {
    await loadPages();
    await loadRoles();
    renderTree();
    if (pages.length > 0) {
      selectPage(pages[0].id);
    }
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

// ====== PAGES: LOAD ======
async function loadPages() {
  pages = await api.getPages();
}

// ====== TREE RENDER ======
function renderTree() {
  const roots = pages.filter(p => !p.parent).sort((a,b) => (a.sort_order || 0) - (b.sort_order || 0));
  const el = document.getElementById('page-tree');
  el.innerHTML = '';
  roots.forEach(p => {
    el.appendChild(renderTreeNode(p, 0));
  });
  document.getElementById('page-count-badge').textContent = pages.length + ' стр.';
  updateParentSelects();
}

function renderTreeNode(page, depth) {
  const node = document.createElement('div');
  node.className = 'tree-node';

  const children = pages.filter(c => c.parent === page.id).sort((a,b) => (a.sort_order || 0) - (b.sort_order || 0));
  const blockCount = (pageBlocks[page.id] || []).length;

  const item = document.createElement('div');
  item.className = 'tree-node__item' + (currentPageId === page.id ? ' active' : '');
  item.dataset.pageId = page.id;

  item.innerHTML = `
    <span class="icon">${page.icon || '📄'}</span>
    <span class="name">${escapeHtml(page.name)}</span>
    <span class="page-count">${blockCount} бл.</span>
    <span class="actions">
      <button title="Редактировать страницу" onclick="event.stopPropagation(); openEditPageModal('${escapeHtml(page.id)}')">✏️</button>
      ${page.id !== 'home' ? `<button title="Удалить" onclick="event.stopPropagation(); deletePage('${escapeHtml(page.id)}')">🗑️</button>` : ''}
    </span>
  `;

  item.addEventListener('click', () => selectPage(page.id));
  node.appendChild(item);

  if (children.length > 0) {
    const childrenEl = document.createElement('div');
    childrenEl.className = 'tree-node__children';
    children.forEach(c => childrenEl.appendChild(renderTreeNode(c, depth + 1)));
    node.appendChild(childrenEl);
  }

  return node;
}

function updateParentSelects() {
  const roots = pages.filter(p => !p.parent).sort((a,b) => (a.sort_order || 0) - (b.sort_order || 0));

  ['new-page-parent', 'edit-page-parent'].forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.innerHTML = '<option value="">— Корень сайта (главное меню) —</option>';
    roots.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = (p.icon || '📄') + ' ' + p.name;
      sel.appendChild(opt);
    });
  });
}

// ====== PAGE SELECTION ======
async function selectPage(pageId) {
  currentPageId = pageId;
  const page = pages.find(p => p.id === pageId);
  if (!page) return;

  switchToView('pages');

  // Update tree highlight
  document.querySelectorAll('.tree-node__item').forEach(el => el.classList.remove('active'));
  const activeItem = document.querySelector(`.tree-node__item[data-page-id="${pageId}"]`);
  if (activeItem) activeItem.classList.add('active');

  // Update header
  document.getElementById('current-page-icon').textContent = page.icon || '📄';
  document.getElementById('current-page-name').textContent = page.name;
  const statusEl = document.getElementById('current-page-status');
  const statuses = { draft: '✏️ Черновик', published: '✅ Опубликовано', new: '🆕 Новая' };
  const classes = { draft: 'status-draft', published: 'status-published', new: 'status-new' };
  statusEl.textContent = statuses[page.status] || '🆕 Новая';
  statusEl.className = 'status ' + (classes[page.status] || 'status-new');

  // Show editor
  document.getElementById('empty-state').style.display = 'none';
  document.getElementById('page-editor').style.display = 'block';

  // Load blocks from API
  showLoading(document.getElementById('blocks-list'));
  try {
    const blocks = await api.getBlocks(pageId);
    pageBlocks[pageId] = blocks;
    // Update counter to avoid ID conflicts with existing blocks
    blocks.forEach(b => {
      const m = b.id && b.id.match(/^b(\d+)$/);
      if (m) {
        const n = parseInt(m[1], 10);
        if (n >= nextBlockIdCounter) nextBlockIdCounter = n + 1;
      }
    });
    renderBlocks();
  } catch (e) {
    toast('⚠️ ' + e.message);
    pageBlocks[pageId] = [];
    renderBlocks();
  }
}

// ====== BLOCKS RENDER ======
function renderBlocks() {
  const blocks = pageBlocks[currentPageId] || [];
  const list = document.getElementById('blocks-list');
  list.innerHTML = '';

  if (blocks.length === 0) {
    list.innerHTML = '<div style="padding:16px;text-align:center;color:#999;background:#f8f9fa;border-radius:8px;font-size:13px;">Страница пуста. Добавьте первый блок 👇</div>';
    return;
  }

  blocks.forEach((b, idx) => {
    const div = document.createElement('div');
    div.className = 'block-item';
    div.innerHTML = `
      <div class="block-header">
        <span class="drag-handle">⠿</span>
        <span class="icon">${getBlockIcon(b.type)}</span>
        <span class="name">${escapeHtml(b.name)}</span>
        <span class="type-label">${getBlockTypeLabel(b.type)}</span>
      </div>
      <div class="block-preview">${getBlockPreview(b)}</div>
      <div class="block-actions">
        <button class="btn-config" onclick="openBlockConfig('${escapeHtml(b.id)}')">⚙️ Настроить</button>
        <button onclick="moveBlock(${idx}, -1)" ${idx === 0 ? 'disabled' : ''}>⬆</button>
        <button onclick="moveBlock(${idx}, 1)" ${idx === blocks.length - 1 ? 'disabled' : ''}>⬇</button>
        <button class="btn-del" onclick="deleteBlock('${escapeHtml(b.id)}')">🗑️</button>
      </div>
    `;
    list.appendChild(div);
  });
}

function getBlockIcon(type) {
  const icons = { hero:'🧱', text:'📝', image:'🖼️', gallery:'📸', video:'🎬', table:'📊', cards:'🏗️', documents:'📄', form:'📋', divider:'➖' };
  return icons[type] || '📦';
}

function getBlockTypeLabel(type) {
  const labels = { hero:'Баннер', text:'Текст', image:'Изображение', gallery:'Галерея', video:'Видео', table:'Таблица', cards:'Плитки', documents:'Документы', form:'Форма', divider:'Разделитель' };
  return labels[type] || type;
}

function getBlockPreview(block) {
  switch(block.type) {
    case 'hero':
      return `🏞️ "${block.config.title || ''}" | Фон: ${block.config.bg_color || '#1b4332'}${block.config.bg_image ? ' + изображение' : ''}`;
    case 'text':
      return `📝 ${(block.config.content || '').replace(/<[^>]*>/g, '').slice(0, 100)}`;
    case 'image':
      return block.config.src ? `🖼️ ${block.config.src.slice(0, 60)}` : '🖼️ Изображение не выбрано';
    case 'gallery':
      return `📸 ${(block.config.images || []).length} фото · ${block.config.columns || 3} кол.`;
    case 'video':
      return `🎬 ${block.config.url || 'Ссылка не указана'}`;
    case 'table':
      return `📊 ${block.config.rows || 0} строк · заголовки: ${(block.config.headers || []).join(', ')}`;
    case 'cards': {
      const autoFrom = block.config.auto_from_tree;
      if (autoFrom) {
        const roots = pages.filter(p => !p.parent && p.id !== 'home');
        return `🏗️ ${roots.length} карточек · авто из меню сайта${block.config.columns ? ' · ' + block.config.columns + ' кол.' : ''}`;
      }
      return `🏗️ ${(block.config.items || []).length} карточек · ${block.config.columns || 3} кол.`;
    }
    case 'documents':
      return `📄 ${(block.config.docs || []).length} документов`;
    case 'form':
      return `📋 ${block.config.form_type === 'suggest' ? 'Предложить новость' : 'Обратная связь'}`;
    case 'divider':
      return `➖ Разделитель (${block.config.style || 'solid'})`;
    default:
      return '';
  }
}

// ====== BLOCK CRUD ======
async function addBlock() {
  const type = document.getElementById('new-block-type').value;
  if (!type) { toast('⚠️ Выберите тип блока'); return; }

  const blocks = pageBlocks[currentPageId] || [];
  const id = 'b' + Date.now().toString(36) + (nextBlockIdCounter++).toString(36);

  const defaultConfigs = {
    hero: { title: 'Заголовок', subtitle: 'Подзаголовок', btn_text: '', btn_url: '', bg_color: '#1b4332', bg_image: '' },
    text: { content: '<p>Введите текст</p>' },
    image: { src: '', alt: '', caption: '' },
    gallery: { images: [], columns: 3 },
    video: { url: '', title: '', description: '' },
    table: { headers: ['Колонка 1', 'Колонка 2'], rows: 3, cols: 2 },
    cards: { items: [{ title: 'Название', text: 'Описание', link: '#' }], columns: 3 },
    documents: { docs: [{ title: 'Название', url: '#', description: '' }] },
    form: { form_type: 'suggest', title: 'Форма' },
    divider: { style: 'solid' },
  };

  const names = { hero:'Баннер', text:'Текстовый блок', image:'Изображение', gallery:'Галерея', video:'Видео', table:'Таблица', cards:'Плитки', documents:'Документы', form:'Форма', divider:'Разделитель' };
  const newBlock = { id, type, name: names[type], config: defaultConfigs[type], page_id: currentPageId, sort_order: blocks.length };

  blocks.push(newBlock);
  pageBlocks[currentPageId] = blocks;

  // Save to API
  try {
    await api.saveBlocks(currentPageId, blocks);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }

  renderBlocks();
  document.getElementById('new-block-type').value = '';
  toast(`✅ Блок «${names[type]}» добавлен`);
  renderTree();
}

async function moveBlock(idx, dir) {
  const blocks = pageBlocks[currentPageId] || [];
  const newIdx = idx + dir;
  if (newIdx < 0 || newIdx >= blocks.length) return;

  // Swap locally
  [blocks[idx], blocks[newIdx]] = [blocks[newIdx], blocks[idx]];
  // Update sort orders
  blocks.forEach((b, i) => b.sort_order = i);
  pageBlocks[currentPageId] = blocks;

  renderBlocks();

  // Save to API
  try {
    await api.saveBlocks(currentPageId, blocks);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

async function deleteBlock(id) {
  if (!confirm('Удалить этот блок?')) return;
  const blocks = pageBlocks[currentPageId] || [];
  pageBlocks[currentPageId] = blocks.filter(b => b.id !== id);

  renderBlocks();
  renderTree();

  // Save to API
  try {
    await api.saveBlocks(currentPageId, pageBlocks[currentPageId]);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }

  toast('🗑️ Блок удалён');
}

// ====== BLOCK CONFIG MODAL ======
function openBlockConfig(id) {
  const blocks = pageBlocks[currentPageId] || [];
  const block = blocks.find(b => b.id === id);
  if (!block) return;
  editingBlockId = id;

  document.getElementById('modal-icon').textContent = getBlockIcon(block.type);
  document.getElementById('modal-title').textContent = 'Настройка: ' + block.name;

  const fields = document.getElementById('modal-fields');
  fields.innerHTML = '';

  addModalField('text', 'Название блока', 'block-name', block.name);

  switch(block.type) {
    case 'hero':
      addModalField('text', 'Заголовок', 'hero-title', block.config.title);
      addModalField('textarea', 'Подзаголовок', 'hero-subtitle', block.config.subtitle);
      addModalField('text', 'Текст кнопки', 'hero-btn', block.config.btn_text);
      addModalField('text', 'Ссылка кнопки', 'hero-url', block.config.btn_url);
      addModalField('color', 'Цвет фона', 'hero-bg', block.config.bg_color);
      addModalField('text', 'Фоновое изображение (URL)', 'hero-image', block.config.bg_image);
      break;
    case 'text':
      addModalField('textarea', 'Текст (HTML)', 'text-content', block.config.content);
      break;
    case 'image':
      addModalField('text', 'URL изображения', 'image-src', block.config.src);
      addModalField('text', 'Alt-текст', 'image-alt', block.config.alt);
      addModalField('text', 'Подпись', 'image-caption', block.config.caption);
      break;
    case 'gallery':
      addModalField('number', 'Колонок в сетке', 'gallery-cols', block.config.columns || 3);
      addModalField('textarea', 'URL фото (каждый с новой строки)', 'gallery-images', (block.config.images || []).join('\n'));
      break;
    case 'video':
      addModalField('text', 'Ссылка (Rutube / VK Video)', 'video-url', block.config.url);
      addModalField('text', 'Название', 'video-title', block.config.title);
      addModalField('textarea', 'Описание', 'video-desc', block.config.description);
      break;
    case 'table':
      addModalField('text', 'Заголовки колонок (через |)', 'table-headers', (block.config.headers || []).join(' | '));
      addModalField('number', 'Количество строк', 'table-rows', block.config.rows || 3);
      break;
    case 'cards':
      addModalField('number', 'Колонок', 'cards-cols', block.config.columns || 3);
      addModalField('select', 'Режим', 'cards-mode', block.config.auto_from_tree ? 'auto' : 'manual', [
        { value: 'auto', label: '🌳 Автоматически из разделов сайта' },
        { value: 'manual', label: '✏️ Ручной ввод' },
      ]);
      addModalField('text', 'Подпись «Смотреть все»', 'cards-all-link', block.config.all_link_text || 'Все разделы →');

      if (block.config.auto_from_tree) {
        addModalField('textarea', 'Карточки разделов (редактирование описаний):', 'cards-auto-items',
          pages.filter(p => !p.parent && p.id !== 'home').sort((a,b) => (a.sort_order||0)-(b.sort_order||0)).map(p => {
            const cardConfig = (block.config.card_overrides && block.config.card_overrides[p.id]) || {};
            return `${p.id} | ${cardConfig.image || ''} | ${cardConfig.text || ''}`;
          }).join('\n')
        );
        const helpDiv = document.createElement('div');
        helpDiv.style.cssText = 'font-size:11px;color:#888;margin-top:-8px;margin-bottom:12px;';
        helpDiv.innerHTML = 'Формат: <strong>id_раздела | URL_картинки | описание</strong><br>Оставь картинку пустой — будет иконка раздела. Разделы автоматически из меню.';
        document.getElementById('modal-fields').appendChild(helpDiv);
      }

      if (!block.config.auto_from_tree) {
        addModalField('textarea', 'Карточки (каждая с новой строки: Название | Описание | Ссылка | Иконка/URL)', 'cards-items', (block.config.items || []).map(i => `${i.title} | ${i.text} | ${i.link} | ${i.image || i.icon || ''}`).join('\n'));
      }
      break;
    case 'documents':
      addModalField('textarea', 'Документы (каждый с новой строки: Название | URL | Описание)', 'docs-items', (block.config.docs || []).map(d => `${d.title} | ${d.url} | ${d.description || ''}`).join('\n'));
      break;
    case 'form':
      addModalField('select', 'Тип формы', 'form-type', block.config.form_type, [
        { value: 'suggest', label: '📋 Предложить новость' },
        { value: 'feedback', label: '💬 Обратная связь' },
      ]);
      addModalField('text', 'Заголовок формы', 'form-title', block.config.title);
      break;
    case 'divider':
      addModalField('select', 'Стиль', 'divider-style', block.config.style, [
        { value: 'solid', label: 'Сплошная' },
        { value: 'dashed', label: 'Пунктирная' },
        { value: 'dotted', label: 'Точечная' },
      ]);
      break;
  }

  document.getElementById('block-modal').classList.add('open');
}

function addModalField(type, label, name, value, options) {
  const fields = document.getElementById('modal-fields');
  const div = document.createElement('div');
  div.className = 'field';

  let input = '';
  if (type === 'textarea') {
    input = `<textarea id="field-${name}" rows="4">${escapeHtml(value || '')}</textarea>`;
  } else if (type === 'select' && options) {
    input = `<select id="field-${name}">${options.map(o => `<option value="${o.value}" ${(value||'') === o.value ? 'selected' : ''}>${o.label}</option>`).join('')}</select>`;
  } else if (type === 'color') {
    input = `<input type="color" id="field-${name}" value="${value || '#1b4332'}">`;
  } else if (type === 'number') {
    input = `<input type="number" id="field-${name}" value="${value || 0}" min="1" max="20">`;
  } else {
    input = `<input type="text" id="field-${name}" value="${escapeHtml(value || '')}">`;
  }

  div.innerHTML = `<label>${label}</label>${input}`;
  fields.appendChild(div);
}

async function saveBlockConfig() {
  const blocks = pageBlocks[currentPageId] || [];
  const block = blocks.find(b => b.id === editingBlockId);
  if (!block) return;

  block.name = document.getElementById('field-block-name')?.value || block.name;

  switch(block.type) {
    case 'hero':
      block.config.title = getFieldVal('hero-title');
      block.config.subtitle = getFieldVal('hero-subtitle');
      block.config.btn_text = getFieldVal('hero-btn');
      block.config.btn_url = getFieldVal('hero-url');
      block.config.bg_color = getFieldVal('hero-bg');
      block.config.bg_image = getFieldVal('hero-image');
      break;
    case 'text':
      block.config.content = getFieldVal('text-content');
      break;
    case 'image':
      block.config.src = getFieldVal('image-src');
      block.config.alt = getFieldVal('image-alt');
      block.config.caption = getFieldVal('image-caption');
      break;
    case 'gallery':
      block.config.columns = parseInt(getFieldVal('gallery-cols')) || 3;
      block.config.images = getFieldVal('gallery-images').split('\n').map(s => s.trim()).filter(Boolean);
      break;
    case 'video':
      block.config.url = getFieldVal('video-url');
      block.config.title = getFieldVal('video-title');
      block.config.description = getFieldVal('video-desc');
      break;
    case 'table':
      block.config.headers = getFieldVal('table-headers').split('|').map(s => s.trim()).filter(Boolean);
      block.config.rows = parseInt(getFieldVal('table-rows')) || 3;
      block.config.cols = block.config.headers.length;
      break;
    case 'cards':
      block.config.columns = parseInt(getFieldVal('cards-cols')) || 3;
      block.config.all_link_text = getFieldVal('cards-all-link') || 'Все разделы →';

      const mode = getFieldVal('cards-mode');
      if (mode === 'auto') {
        block.config.auto_from_tree = true;
        block.config.card_overrides = {};
        const autoLines = getFieldVal('cards-auto-items').split('\n').filter(Boolean);
        autoLines.forEach(line => {
          const parts = line.split('|').map(s => s.trim());
          if (parts[0]) {
            block.config.card_overrides[parts[0]] = {
              image: parts[1] || '',
              text: parts[2] || '',
            };
          }
        });
        block.config.items = [];
      } else {
        block.config.auto_from_tree = false;
        block.config.card_overrides = {};
        block.config.items = getFieldVal('cards-items').split('\n').filter(Boolean).map(line => {
          const parts = line.split('|').map(s => s.trim());
          return { title: parts[0] || '', text: parts[1] || '', link: parts[2] || '#', icon: parts[3] || '', image: parts[3] || '' };
        });
      }
      break;
    case 'documents':
      block.config.docs = getFieldVal('docs-items').split('\n').filter(Boolean).map(line => {
        const parts = line.split('|').map(s => s.trim());
        return { title: parts[0] || '', url: parts[1] || '#', description: parts[2] || '' };
      });
      break;
    case 'form':
      block.config.form_type = getFieldVal('form-type');
      block.config.title = getFieldVal('form-title');
      break;
    case 'divider':
      block.config.style = getFieldVal('divider-style');
      break;
  }

  closeModal();
  renderBlocks();

  // Save to API
  try {
    await api.saveBlocks(currentPageId, pageBlocks[currentPageId]);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }

  toast('💾 Блок сохранён');
}

function getFieldVal(name) {
  const el = document.getElementById('field-' + name);
  return el ? el.value : '';
}

function closeModal() {
  document.getElementById('block-modal').classList.remove('open');
  editingBlockId = null;
}

// ====== PAGE CRUD ======
function showNewSectionModal() {
  document.getElementById('new-page-modal-icon').textContent = '📄';
  document.getElementById('new-page-modal-title').textContent = 'Новый раздел (главное меню)';
  document.getElementById('new-page-name').value = '';
  document.getElementById('new-page-icon').value = '📄';
  document.getElementById('new-page-parent').value = '';
  document.getElementById('new-page-parent').disabled = true;
  document.getElementById('new-page-slug').value = '';
  document.getElementById('new-page-order').value = '99';
  document.getElementById('new-page-modal').classList.add('open');
  setTimeout(() => document.getElementById('new-page-name').focus(), 100);
}

function showNewSubSectionModal() {
  document.getElementById('new-page-modal-icon').textContent = '📑';
  document.getElementById('new-page-modal-title').textContent = 'Новый подраздел';
  document.getElementById('new-page-name').value = '';
  document.getElementById('new-page-icon').value = '📄';
  document.getElementById('new-page-parent').disabled = false;
  document.getElementById('new-page-parent').value = '';
  document.getElementById('new-page-slug').value = '';
  document.getElementById('new-page-order').value = '99';
  document.getElementById('new-page-modal').classList.add('open');
  setTimeout(() => document.getElementById('new-page-name').focus(), 100);
}

async function confirmNewPage() {
  const name = document.getElementById('new-page-name').value.trim();
  const icon = document.getElementById('new-page-icon').value;
  const parent = document.getElementById('new-page-parent').value || null;
  const slug = document.getElementById('new-page-slug').value.trim() || name.toLowerCase().replace(/\s+/g, '-');
  const sort_order = parseInt(document.getElementById('new-page-order').value) || 99;

  if (!name) { toast('⚠️ Введите название страницы'); return; }

  try {
    const newPage = await api.createPage({
      id: slug,
      name,
      icon,
      parent,
      sort_order,
    });

    pages.push(newPage);
    pageBlocks[newPage.id] = [];

    document.getElementById('new-page-modal').classList.remove('open');
    renderTree();
    selectPage(newPage.id);
    toast(`✅ Страница «${name}» создана!`);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

function closeNewPageModal() {
  document.getElementById('new-page-modal').classList.remove('open');
}

function openEditPageModal(id) {
  const page = pages.find(p => p.id === id);
  if (!page) return;

  document.getElementById('edit-page-modal-title').textContent = page.name;
  document.getElementById('edit-page-name').value = page.name;
  document.getElementById('edit-page-icon').value = page.icon || '📄';
  document.getElementById('edit-page-parent').value = page.parent || '';
  document.getElementById('edit-page-slug').value = page.id;
  document.getElementById('edit-page-order').value = page.sort_order || 0;

  document.getElementById('edit-page-parent').disabled = (id === 'home');

  document.getElementById('edit-page-modal').dataset.pageId = id;
  document.getElementById('edit-page-modal').classList.add('open');
}

async function confirmEditPage() {
  const id = document.getElementById('edit-page-modal').dataset.pageId;
  const page = pages.find(p => p.id === id);
  if (!page) return;

  const newName = document.getElementById('edit-page-name').value.trim() || page.name;
  const newIcon = document.getElementById('edit-page-icon').value;
  const newParent = document.getElementById('edit-page-parent').value || null;
  const newOrder = parseInt(document.getElementById('edit-page-order').value) || 99;
  const newSlug = document.getElementById('edit-page-slug').value.trim();

  try {
    await api.updatePage(id, {
      name: newName,
      icon: newIcon,
      parent: newParent,
      sort_order: newOrder,
    });

    page.name = newName;
    page.icon = newIcon;
    page.parent = newParent;
    page.sort_order = newOrder;

    document.getElementById('edit-page-modal').classList.remove('open');

    // Handle slug change
    if (newSlug && newSlug !== id) {
      // Move blocks to new id in local state
      pageBlocks[newSlug] = pageBlocks[id] || [];
      delete pageBlocks[id];
      page.id = newSlug;

      // We need to reload pages from server to get the new id
      await loadPages();
    }

    renderTree();
    selectPage(page.id);
    toast(`💾 Страница «${page.name}» обновлена`);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

function closeEditPageModal() {
  document.getElementById('edit-page-modal').classList.remove('open');
}

async function deletePage(id) {
  if (id === 'home') { toast('⚠️ Главную страницу нельзя удалить'); return; }
  const page = pages.find(p => p.id === id);
  if (!page) return;

  const children = pages.filter(c => c.parent === id);
  let confirmMsg = `Удалить страницу «${page.name}»?`;
  if (children.length > 0) {
    confirmMsg = `Удалить «${page.name}» и все её подразделы (${children.length})?`;
  }
  if (!confirm(confirmMsg)) return;

  try {
    await api.deletePage(id);

    // Remove from local state
    const childIds = [id, ...children.map(c => c.id)];
    childIds.forEach(cid => {
      const idx = pages.findIndex(p => p.id === cid);
      if (idx >= 0) pages.splice(idx, 1);
      delete pageBlocks[cid];
    });

    if (currentPageId === id || childIds.includes(currentPageId)) {
      currentPageId = null;
      document.getElementById('empty-state').style.display = 'block';
      document.getElementById('page-editor').style.display = 'none';
      if (pages.length > 0) {
        selectPage(pages[0].id);
      }
    }

    renderTree();
    toast(`🗑️ «${page.name}» удалена`);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

// ====== SAVE / PUBLISH / PREVIEW ======
async function savePage() {
  if (!currentPageId) return;
  const page = pages.find(p => p.id === currentPageId);
  if (!page) return;

  try {
    await api.updatePage(currentPageId, { status: 'draft' });
    page.status = 'draft';

    // Save blocks too
    if (pageBlocks[currentPageId]) {
      await api.saveBlocks(currentPageId, pageBlocks[currentPageId]);
    }

    toast(`💾 Черновик «${page.name}» сохранён`);
    renderTree();
    selectPage(page.id);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

async function publishPage() {
  if (!currentPageId) return;
  const page = pages.find(p => p.id === currentPageId);
  if (!page) return;

  try {
    await api.updatePage(currentPageId, { status: 'published' });
    page.status = 'published';

    // Save blocks too
    if (pageBlocks[currentPageId]) {
      await api.saveBlocks(currentPageId, pageBlocks[currentPageId]);
    }

    toast(`📢 «${page.name}» опубликована!`);
    renderTree();
    selectPage(page.id);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

function previewPage() {
  if (!currentPageId) return;
  const page = pages.find(p => p.id === currentPageId);
  if (!page) return;
  window.open(`/${page.id}`, '_blank');
  toast(`👁️ Предпросмотр «${page.name}» (откроется в новом окне)`);
}

// ====== ROLES ======
async function loadRoles() {
  try {
    roles = await api.getRoles();
  } catch (e) {
    console.error('Failed to load roles:', e);
    roles = [];
  }
}

function renderRoles() {
  const tbody = document.getElementById('roles-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  roles.forEach(role => {
    const tr = document.createElement('tr');
    tr.style.borderTop = '1px solid #e9ecef';

    let sectionsLabel = '';
    if (role.sections === '__all__' || (Array.isArray(role.sections) && role.sections.includes('__all__'))) {
      sectionsLabel = '🔓 Все разделы';
    } else if (!role.sections || role.sections.length === 0) {
      sectionsLabel = '—';
    } else {
      sectionsLabel = role.sections.map(sid => {
        const p = pages.find(p => p.id === sid);
        return p ? (p.icon || '📄') + ' ' + p.name : sid;
      }).join(', ');
    }

    tr.innerHTML = `
      <td style="padding:10px 14px; font-weight:600;">${role.icon || '🎭'} ${escapeHtml(role.name)}</td>
      <td style="padding:10px 14px;">${role.users || 0}</td>
      <td style="padding:10px 14px; font-size:11px; color:#555;">${sectionsLabel}</td>
      <td style="padding:10px 14px;">
        <button onclick="editRole('${role.id}')" style="padding:4px 8px; font-size:11px; border:1px solid #dee2e6; border-radius:4px; background:#fff; cursor:pointer;">✏️</button>
        ${role.id !== 'admin' ? `<button onclick="deleteRole('${role.id}')" style="padding:4px 8px; font-size:11px; border:1px solid #c62828; border-radius:4px; background:#fff; color:#c62828; cursor:pointer; margin-left:4px;">🗑️</button>` : ''}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function showAddRoleModal() {
  document.getElementById('new-role-modal-title').textContent = 'Новая роль';
  document.getElementById('new-role-name').value = '';
  document.getElementById('new-role-icon').value = '📚';
  document.getElementById('role-cap-moderation').checked = false;
  document.getElementById('role-cap-upload').checked = true;
  document.getElementById('role-cap-publish').checked = true;

  const sectionsDiv = document.getElementById('new-role-sections');
  sectionsDiv.innerHTML = '';

  const roots = pages.filter(p => !p.parent).sort((a,b) => (a.sort_order||0) - (b.sort_order||0));

  const allLabel = document.createElement('label');
  allLabel.style.cssText = 'font-weight:400;font-size:13px;display:flex;align-items:center;gap:8px;cursor:pointer;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid #dee2e6;';
  allLabel.innerHTML = '<input type="checkbox" class="role-section-cb" data-section="__all__" onchange="toggleAllSections(this)"> 🔓 Все разделы (полный доступ)';
  sectionsDiv.appendChild(allLabel);

  roots.forEach(p => {
    addSectionCheckbox(sectionsDiv, p, 0);
  });

  document.getElementById('new-role-modal').dataset.mode = 'create';
  document.getElementById('new-role-modal').dataset.editId = '';
  document.getElementById('new-role-modal').classList.add('open');
  setTimeout(() => document.getElementById('new-role-name').focus(), 100);
}

function addSectionCheckbox(container, page, depth) {
  const label = document.createElement('label');
  label.style.cssText = `font-weight:400;font-size:13px;display:flex;align-items:center;gap:8px;cursor:pointer;padding-left:${depth * 20 + 4}px;margin-bottom:2px;`;
  label.innerHTML = `<input type="checkbox" class="role-section-cb" data-section="${page.id}" value="${page.id}"> ${page.icon || '📄'} ${escapeHtml(page.name)}`;
  container.appendChild(label);

  const children = pages.filter(c => c.parent === page.id).sort((a,b) => (a.sort_order||0) - (b.sort_order||0));
  children.forEach(c => addSectionCheckbox(container, c, depth + 1));
}

function toggleAllSections(el) {
  const cbs = document.querySelectorAll('.role-section-cb');
  cbs.forEach(cb => { if (cb.dataset.section !== '__all__') cb.checked = el.checked; });
}

async function confirmAddRole() {
  const name = document.getElementById('new-role-name').value.trim();
  const icon = document.getElementById('new-role-icon').value;
  if (!name) { toast('⚠️ Введите название роли'); return; }

  const selectedSections = [];
  document.querySelectorAll('.role-section-cb:checked').forEach(cb => {
    if (cb.dataset.section === '__all__') {
      selectedSections.length = 0;
      selectedSections.push('__all__');
    } else if (selectedSections.indexOf('__all__') === -1) {
      selectedSections.push(cb.dataset.section);
    }
  });

  const caps = {
    moderation: document.getElementById('role-cap-moderation').checked,
    upload: document.getElementById('role-cap-upload').checked,
    publish: document.getElementById('role-cap-publish').checked,
  };

  const mode = document.getElementById('new-role-modal').dataset.mode;
  const editId = document.getElementById('new-role-modal').dataset.editId;

  try {
    if (mode === 'edit' && editId) {
      await api.updateRole(editId, { name, icon, sections: selectedSections, caps, id: editId });
      toast(`💾 Роль «${name}» обновлена`);
    } else {
      const rid = 'role_' + name.toLowerCase().replace(/[^a-zа-я0-9]/g, '_');
      await api.createRole({ id: rid, name, icon, sections: selectedSections, caps });
      toast(`✅ Роль «${name}» создана`);
    }

    await loadRoles();
    closeModalById('new-role-modal');
    renderRoles();
    renderUserStats();
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

function editRole(id) {
  const role = roles.find(r => r.id === id);
  if (!role) return;

  document.getElementById('new-role-modal-title').textContent = 'Редактирование: ' + role.name;
  document.getElementById('new-role-name').value = role.name;
  document.getElementById('new-role-icon').value = role.icon || '📚';
  document.getElementById('role-cap-moderation').checked = role.caps?.moderation || false;
  document.getElementById('role-cap-upload').checked = role.caps?.upload || false;
  document.getElementById('role-cap-publish').checked = role.caps?.publish || false;

  const sectionsDiv = document.getElementById('new-role-sections');
  sectionsDiv.innerHTML = '';

  const allLabel = document.createElement('label');
  allLabel.style.cssText = 'font-weight:400;font-size:13px;display:flex;align-items:center;gap:8px;cursor:pointer;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid #dee2e6;';
  allLabel.innerHTML = '<input type="checkbox" class="role-section-cb" data-section="__all__" onchange="toggleAllSections(this)"> 🔓 Все разделы (полный доступ)';
  sectionsDiv.appendChild(allLabel);

  const roots = pages.filter(p => !p.parent).sort((a,b) => (a.sort_order||0) - (b.sort_order||0));
  roots.forEach(p => addSectionCheckbox(sectionsDiv, p, 0));

  const sections = role.sections || [];
  if (sections === '__all__' || sections.includes('__all__')) {
    document.querySelectorAll('.role-section-cb').forEach(cb => cb.checked = true);
  } else {
    sections.forEach(sid => {
      const cb = document.querySelector(`.role-section-cb[data-section="${sid}"]`);
      if (cb) cb.checked = true;
    });
  }

  document.getElementById('new-role-modal').dataset.mode = 'edit';
  document.getElementById('new-role-modal').dataset.editId = id;
  document.getElementById('new-role-modal').classList.add('open');
}

async function deleteRole(id) {
  const role = roles.find(r => r.id === id);
  if (!role) return;
  if (!confirm(`Удалить роль «${role.name}»?`)) return;

  try {
    await api.deleteRole(id);
    roles = roles.filter(r => r.id !== id);
    renderRoles();
    renderUserStats();
    toast(`🗑️ Роль «${role.name}» удалена`);
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

function renderUserStats() {
  const total = roles.reduce((s, r) => s + (r.users || 0), 0);
  const statEl = document.querySelector('#editor-users .page-indicator .status');
  if (statEl) {
    statEl.textContent = `${roles.length} ролей · ${total} пользователей`;
  }
}

function closeModalById(id) {
  document.getElementById(id).classList.remove('open');
}

// ====== VIEW SWITCHING ======
function switchToView(view) {
  currentView = view;
  document.getElementById('editor-pages').style.display = view === 'pages' ? 'block' : 'none';
  document.getElementById('editor-users').style.display = view === 'users' ? 'block' : 'none';
  document.getElementById('editor-settings').style.display = view === 'settings' ? 'block' : 'none';
  document.getElementById('editor-media').style.display = view === 'media' ? 'block' : 'none';

  const dim = view !== 'pages';
  document.querySelector('.left-panel__header').style.opacity = dim ? '0.5' : '1';
  document.querySelector('.left-panel__actions').style.opacity = dim ? '0.3' : '1';

  if (view === 'users') {
    renderRoles();
    renderUserStats();
  }
  if (view === 'settings') {
    renderSettings();
  }
  if (view === 'media') {
    renderMedia();
  }
}

// ====== USERS ======
async function loadUsers() {
  try {
    const users = await api.getUsers();
    const tbody = document.getElementById('users-tbody');
    const label = document.getElementById('users-count-label');
    label.textContent = users.length + ' пользователей';

    tbody.innerHTML = users.map(u => {
      const canDelete = !(users.length === 1 && u.id === users[0].id); // не последнего
      <tr>
        <td style="padding:10px 14px; font-weight:600; color:#495057; font-size:13px;">${escapeHtml(u.id)}</td>
        <td style="padding:10px 14px; font-weight:600;">${escapeHtml(u.username)}</td>
        <td style="padding:10px 14px;"><span class="badge" style="background:#d0bfff; color:#1a1a2e; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600;">${escapeHtml(u.role)}</span></td>
        <td style="padding:10px 14px; color:#6c757d; font-size:12px;">${u.created_at ? u.created_at.substring(0, 10) : ''}</td>
        <td style="padding:10px 14px;">
          ${canDelete ? `<button onclick="deleteUser(${escapeHtml(u.id)})" style="background:none; border:none; color:#e53e3e; cursor:pointer; font-size:13px;" title="Удалить">✕</button>` : ''}
        </td>
      </tr>
    }).join('');
  } catch (e) {
    showToast('Ошибка загрузки пользователей: ' + e.message, 'error');
  }
}

function switchToUsers() {
  switchToView('users');
  loadUsers();
}

function showAddUserForm() {
  const form = document.getElementById('add-user-form');
  form.style.display = form.style.display === 'none' ? 'block' : 'none';
  if (form.style.display === 'block') {
    document.getElementById('new-user-username').focus();
  }
}

function hideAddUserForm() {
  document.getElementById('add-user-form').style.display = 'none';
}

async function confirmAddUser() {
  const username = document.getElementById('new-user-username').value.trim();
  const password = document.getElementById('new-user-password').value;
  const errEl = document.getElementById('add-user-error');
  errEl.textContent = '';

  if (!username || !password) {
    errEl.textContent = 'Заполните логин и пароль';
    return;
  }
  if (password.length < 8) {
    errEl.textContent = 'Пароль должен быть минимум 8 символов';
    return;
  }
  try {
    await api.createUser(username, password, 'admin');
    showToast('✅ Пользователь «' + username + '» создан', 'success');
    hideAddUserForm();
    document.getElementById('new-user-username').value = '';
    document.getElementById('new-user-password').value = '';
    loadUsers();
    loadRoles();
  } catch (e) {
    errEl.textContent = e.message;
  }
}

async function deleteUser(id) {
  if (!confirm('Удалить пользователя? Его сессии будут сброшены.')) return;
  try {
    await api.deleteUser(id);
    showToast('✅ Пользователь удалён', 'success');
    loadUsers();
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function changePassword() {
  const oldPw = document.getElementById('pw-old').value;
  const newPw = document.getElementById('pw-new').value;
  const msgEl = document.getElementById('pw-message');

  if (!oldPw || !newPw) {
    msgEl.innerHTML = '<span style="color:#e53e3e;">Заполните оба поля</span>';
    return;
  }
  if (newPw.length < 4) {
    msgEl.innerHTML = '<span style="color:#e53e3e;">Новый пароль минимум 4 символа</span>';
    return;
  }

  try {
    const result = await api.changePassword(oldPw, newPw);
    msgEl.innerHTML = '<span style="color:#2d6a4f; font-weight:600;">✅ ' + result.message + '</span>';
    document.getElementById('pw-old').value = '';
    document.getElementById('pw-new').value = '';
  } catch (e) {
    msgEl.innerHTML = '<span style="color:#e53e3e;">❌ ' + e.message + '</span>';
  }
}

function switchToPages() {
  switchToView('pages');
}

function switchToSettings() {
  switchToView('settings');
}

function switchToMedia() {
  switchToView('media');
}

// ====== SETTINGS ======
async function loadSettings() {
  try {
    settings = await api.getSettings();
  } catch (e) {
    console.error('Failed to load settings:', e);
    settings = {};
  }
}

function renderSettings() {
  const fields = document.getElementById('settings-fields');
  if (!fields) return;
  fields.innerHTML = '';

  const settingFields = [
    { section: 'Основные', key: 'site_name', label: 'Название сайта', type: 'text' },
    { section: 'Основные', key: 'site_description', label: 'Описание сайта', type: 'text' },
    { section: 'Основные', key: 'logo_text', label: 'Текст логотипа', type: 'text' },
    { section: 'Основные', key: 'logo_icon', label: 'Иконка логотипа', type: 'text' },
    { section: 'Оформление', key: 'header_bg_color', label: 'Цвет фона шапки', type: 'color' },
    { section: 'Оформление', key: 'footer_bg_color', label: 'Цвет фона подвала', type: 'color' },
    { section: 'Оформление', key: 'primary_color', label: 'Основной цвет', type: 'color' },
    { section: 'Оформление', key: 'accent_color', label: 'Акцентный цвет', type: 'color' },
    { section: 'Главная', key: 'hero_title', label: 'Заголовок главной', type: 'text' },
    { section: 'Главная', key: 'hero_subtitle', label: 'Подзаголовок главной', type: 'text' },
    { section: 'Главная', key: 'hero_btn_text', label: 'Текст кнопки главной', type: 'text' },
    { section: 'Главная', key: 'hero_bg_color', label: 'Цвет фона главной', type: 'color' },
    { section: 'Соцсети', key: 'social_vk', label: 'VK ссылка', type: 'text' },
    { section: 'Соцсети', key: 'social_telegram', label: 'Telegram ссылка', type: 'text' },
    { section: 'Соцсети', key: 'social_ok', label: 'OK ссылка', type: 'text' },
    { section: 'Контакты', key: 'contact_email', label: 'Email для связи', type: 'text' },
    { section: 'Формы', key: 'suggest_title', label: 'Заголовок формы предложить', type: 'text' },
    { section: 'Формы', key: 'suggest_text', label: 'Текст формы предложить', type: 'textarea' },
    { section: 'Подвал', key: 'footer_copyright', label: 'Копирайт', type: 'text' },
  ];

  let currentSection = '';
  settingFields.forEach(f => {
    if (f.section !== currentSection) {
      currentSection = f.section;
      const title = document.createElement('div');
      title.className = 'settings-section-title';
      title.textContent = f.section;
      fields.appendChild(title);
    }

    const div = document.createElement('div');
    div.className = 'field';

    const value = settings[f.key] || '';
    let input = '';
    if (f.type === 'color') {
      input = `<input type="color" id="setting-${f.key}" value="${value || '#1b4332'}">`;
    } else if (f.type === 'textarea') {
      input = `<textarea id="setting-${f.key}" rows="3">${escapeHtml(value)}</textarea>`;
    } else {
      input = `<input type="text" id="setting-${f.key}" value="${escapeHtml(value)}">`;
    }

    div.innerHTML = `<label>${f.label}</label>${input}`;
    fields.appendChild(div);
  });
}

async function saveSettings() {
  const newSettings = {};
  const keys = ['site_name','site_description','logo_text','logo_icon','header_bg_color','footer_bg_color','primary_color','accent_color','hero_title','hero_subtitle','hero_btn_text','hero_bg_color','social_vk','social_telegram','social_ok','contact_email','suggest_title','suggest_text','footer_copyright'];

  keys.forEach(k => {
    const el = document.getElementById('setting-' + k);
    if (el) newSettings[k] = el.value;
  });

  try {
    await api.saveSettings(newSettings);
    settings = newSettings;
    toast('💾 Настройки сохранены');
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

// ====== MEDIA ======
async function loadMedia() {
  try {
    mediaItems = await api.getMedia();
  } catch (e) {
    console.error('Failed to load media:', e);
    mediaItems = [];
  }
}

function renderMedia() {
  const grid = document.getElementById('media-grid');
  if (!grid) return;
  grid.innerHTML = '';

  if (mediaItems.length === 0) {
    grid.innerHTML = '<div class="media-empty">📸 Медиафайлов пока нет. Загрузите первый файл.</div>';
    return;
  }

  mediaItems.forEach(item => {
    const div = document.createElement('div');
    div.className = 'media-item';

    const isImage = item.mime_type?.startsWith('image/');
    div.innerHTML = `
      ${isImage ? `<img src="${item.url}" alt="${escapeHtml(item.alt_text || '')}" loading="lazy">` : '<div style="height:120px;display:flex;align-items:center;justify-content:center;background:#f0f2f5;font-size:40px;">📁</div>'}
      <div class="media-info">
        <div class="filename" title="${escapeHtml(item.original_name || item.filename)}">${escapeHtml(item.original_name || item.filename)}</div>
        <div>${item.size ? Math.round(item.size/1024) + ' KB' : ''}</div>
      </div>
      <div class="media-actions">
        <button onclick="copyMediaUrl('${item.url}')">📋 Копировать URL</button>
        <button class="btn-media-del" onclick="deleteMedia(${item.id})">🗑️</button>
      </div>
    `;
    grid.appendChild(div);
  });
}

async function uploadMedia() {
  const input = document.getElementById('media-file-input');
  if (!input.files || input.files.length === 0) {
    toast('⚠️ Выберите файл');
    return;
  }

  const btn = document.getElementById('media-upload-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Загрузка...';

  try {
    const result = await api.uploadFile(input.files[0]);
    mediaItems.unshift(result);
    renderMedia();
    input.value = '';
    toast('✅ Файл загружен');
  } catch (e) {
    toast('⚠️ ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '📤 Загрузить';
  }
}

async function deleteMedia(id) {
  if (!confirm('Удалить этот файл?')) return;
  try {
    await api.deleteMedia(id);
    mediaItems = mediaItems.filter(m => m.id !== id);
    renderMedia();
    toast('🗑️ Файл удалён');
  } catch (e) {
    toast('⚠️ ' + e.message);
  }
}

function copyMediaUrl(url) {
  navigator.clipboard.writeText(url).then(() => {
    toast('📋 URL скопирован: ' + url);
  }).catch(() => {
    toast('📋 ' + url);
  });
}

// ====== INIT ======
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  init();
});
