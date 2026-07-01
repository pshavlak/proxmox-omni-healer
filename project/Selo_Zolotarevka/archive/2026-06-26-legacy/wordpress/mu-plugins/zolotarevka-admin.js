/**
 * Zolotarevka Admin v2 — конструктор сайта
 * Точная копия функциональности HTML-прототипа site-builder-v2.html
 * Адаптирована для AJAX в WordPress
 */
(function($) {
    'use strict';

    var zoloApp = {
        pages: [],
        roles: [],
        users: [],
        currentPageId: null,
        currentBlocks: [],
        isDirty: false,
        toastTimer: null,
        currentSection: 'pages',
        editingBlockIdx: -1,

        init: function() {
            this.loadData();
            this.bindEvents();
        },

        // ── DATA LOADING ──

        loadData: function() {
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_get_data',
                nonce: zoloData.nonce
            }).done(function(resp) {
                if (!resp.success) return;
                zoloApp.pages = resp.data.pages || [];
                zoloApp.roles = resp.data.roles || [];
                zoloApp.users = resp.data.users_data || [];
                zoloApp._settings = resp.data.settings || {};
                zoloApp._videos = resp.data.videos || [];
                zoloApp._galleryItems = resp.data.gallery_items || [];
                zoloApp._recentContent = resp.data.recent_content || {};
                zoloApp.renderTree();
                zoloApp.updatePageCount();
                // Select home by default
                if (zoloApp.pages.length > 0) {
                    zoloApp.selectPage(zoloApp.pages[0].id);
                }
                zoloApp.renderRoles();
                zoloApp.renderUsers();
                zoloApp.renderUsersStats();
                zoloApp.updateUsersSummary();
            });
        },

        // ── TREE ──

        renderTree: function() {
            var $tree = $('#zolo-tree');
            $tree.empty();
            var roots = this.getRoots();
            if (!roots.length) {
                $tree.html('<p style="padding:20px;color:#888;text-align:center;">Нет страниц</p>');
                return;
            }
            var self = this;
            roots.forEach(function(p) {
                self.renderNode($tree, p, 0);
            });
        },

        getRoots: function() {
            return this.pages.filter(function(p) { return !p.parent; })
                .sort(function(a, b) { return a.order - b.order; });
        },

        getChildren: function(parentId) {
            return this.pages.filter(function(p) { return p.parent === parentId; })
                .sort(function(a, b) { return a.order - b.order; });
        },

        renderNode: function($container, page, depth) {
            var self = this;
            var children = this.getChildren(page.id);
            var indent = 16 + depth * 20;

            var $item = $(
                '<div class="zolo-tree-node">' +
                '<div class="zolo-tree-item' + (this.currentPageId === page.id ? ' active' : '') + '" data-id="' + page.id + '" style="padding-left:' + indent + 'px;">' +
                    '<span class="zolo-tree-icon">' + (page.icon || '📄') + '</span>' +
                    '<span class="zolo-tree-name">' + this.esc(page.name) + '</span>' +
                    '<span class="zolo-page-count">' + children.length + '</span>' +
                    '<span class="zolo-tree-actions">' +
                        '<button class="zolo-tree-edit" title="Редактировать">✏️</button>' +
                        '<button class="zolo-tree-delete" title="Удалить">🗑️</button>' +
                    '</span>' +
                '</div></div>'
            );

            var $itemDiv = $item.find('.zolo-tree-item');
            $itemDiv.on('click', function(e) {
                if ($(e.target).closest('.zolo-tree-actions').length) return;
                self.selectPage(page.id);
            });
            $itemDiv.find('.zolo-tree-edit').on('click', function(e) {
                e.stopPropagation();
                self.showEditPageModal(page.id);
            });
            $itemDiv.find('.zolo-tree-delete').on('click', function(e) {
                e.stopPropagation();
                self.deletePage(page.id);
            });
            $container.append($item);

            if (children.length) {
                var $childContainer = $('<div class="zolo-tree-children"></div>');
                children.forEach(function(child) {
                    self.renderNode($childContainer, child, depth + 1);
                });
                $container.append($childContainer);
            }
        },

        updatePageCount: function() {
            $('#zolo-page-count').text(this.pages.length + ' стр.');
        },

        // ── PAGE SELECTION ──

        selectPage: function(pageId) {
            this.currentPageId = pageId;
            var page = this.getPage(pageId);
            if (!page) return;

            // Highlight
            $('#zolo-tree .zolo-tree-item').removeClass('active');
            $('#zolo-tree .zolo-tree-item[data-id="' + pageId + '"]').addClass('active');

            // Show editor
            $('#zolo-empty').hide();
            $('#zolo-editor').show();

            // Update header
            $('#zolo-current-icon').text(page.icon || '📄');
            $('#zolo-current-name').text(page.name);

            // Update status
            var statuses = { draft: '✏️ Черновик', published: '✅ Опубликовано', new: '🆕 Новая' };
            var classes = { draft: 'zolo-status-draft', published: 'zolo-status-published', new: 'zolo-status-new' };
            var $status = $('#zolo-current-status');
            $status.text(statuses[page.status] || '🆕 Новая').attr('class', 'zolo-status ' + (classes[page.status] || 'zolo-status-new'));

            // Load blocks from server
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_get_blocks',
                nonce: zoloData.nonce,
                page_id: pageId
            }).done(function(resp) {
                if (!resp.success) return;
                zoloApp.currentBlocks = resp.data.blocks || [];
                zoloApp.isDirty = resp.data.has_draft;
                zoloApp.renderBlocks();
                zoloApp.updateDraftStatus();
            });
        },

        getPage: function(id) {
            for (var i = 0; i < this.pages.length; i++) {
                if (this.pages[i].id === id) return this.pages[i];
            }
            return null;
        },

        updateDraftStatus: function() {
            var $status = $('#zolo-current-status');
            if (this.isDirty) {
                $status.text('✏️ Черновик').attr('class', 'zolo-status zolo-status-draft');
            } else {
                $status.text('✅ Опубликовано').attr('class', 'zolo-status zolo-status-published');
            }
        },

        // ── BLOCKS ──

        renderBlocks: function() {
            var $list = $('#zolo-blocks-list');
            $list.empty();
            var self = this;

            var blockIcons = {
                hero:'🧱', text:'📝', image:'🖼️', gallery:'📸', video:'🎬',
                table:'📊', cards:'🏗️', documents:'📄', form:'📋', divider:'➖'
            };
            var blockTypeLabels = {
                hero:'Баннер', text:'Текст', image:'Изображение', gallery:'Галерея',
                video:'Видео', table:'Таблица', cards:'Плитки', documents:'Документы',
                form:'Форма', divider:'Разделитель'
            };

            if (this.currentBlocks.length === 0) {
                $list.html('<div style="padding:16px;text-align:center;color:#999;background:#f8f9fa;border-radius:8px;font-size:13px;">Страница пуста. Добавьте первый блок 👇</div>');
                return;
            }

            this.currentBlocks.forEach(function(b, i) {
                var icon = blockIcons[b.type] || '📦';
                var typeLabel = blockTypeLabels[b.type] || b.type;
                var preview = self.getBlockPreview(b);

                var $block = $(
                    '<div class="zolo-block" data-index="' + i + '">' +
                    '<div class="zolo-block-header">' +
                        '<span class="zolo-drag">⠿</span>' +
                        '<span class="zolo-bicon">' + icon + '</span>' +
                        '<span class="zolo-bname">' + self.esc(b.name) + '</span>' +
                        '<span class="zolo-btype">' + typeLabel + '</span>' +
                    '</div>' +
                    '<div class="zolo-bpreview">' + preview + '</div>' +
                    '<div class="zolo-bactions">' +
                        '<button class="btn-cfg" data-index="' + i + '">⚙️ Настроить</button>' +
                        '<button class="btn-up" data-index="' + i + '"' + (i === 0 ? ' disabled' : '') + '>⬆</button>' +
                        '<button class="btn-down" data-index="' + i + '"' + (i === self.currentBlocks.length - 1 ? ' disabled' : '') + '>⬇</button>' +
                        '<button class="btn-del" data-index="' + i + '">🗑️</button>' +
                    '</div>' +
                    '</div>'
                );

                $block.find('.btn-cfg').on('click', function() {
                    var idx = parseInt($(this).data('index'));
                    self.showBlockConfigModal(idx);
                });
                $block.find('.btn-up').on('click', function() {
                    var idx = parseInt($(this).data('index'));
                    self.moveBlock(idx, idx - 1);
                });
                $block.find('.btn-down').on('click', function() {
                    var idx = parseInt($(this).data('index'));
                    self.moveBlock(idx, idx + 1);
                });
                $block.find('.btn-del').on('click', function() {
                    var idx = parseInt($(this).data('index'));
                    self.deleteBlock(idx);
                });

                $list.append($block);
            });
        },

        getBlockPreview: function(block) {
            var cfg = block.config || {};
            switch (block.type) {
                case 'hero':
                    return '🏞️ "' + (cfg.title || '') + '" | Фон: ' + (cfg.bg_color || '#1b4332') + (cfg.bg_image ? ' + изображение' : '');
                case 'text':
                    return '📝 ' + this.stripHtml(cfg.text || '').substring(0, 100) || (cfg.content || '').replace(/<[^>]*>/g, '').substring(0, 100);
                case 'image':
                    return cfg.image_url ? '🖼️ ' + cfg.image_url.substring(0, 60) : '🖼️ Изображение не выбрано';
                case 'gallery':
                    return '📸 ' + ((cfg.items||[]).length + (cfg.images||[]).length) + ' фото · ' + (cfg.cols || 3) + ' кол.';
                case 'video':
                    return '🎬 ' + (cfg.video_url || 'Ссылка не указана');
                case 'table':
                    return '📊 ' + (cfg.rows ? cfg.rows.length + ' строк' : '0 строк') + ' · заголовки: ' + (cfg.headers||[]).join(', ');
                case 'cards':
                    return cfg.auto_from_tree ? '🏗️ ' + this.getRoots().length + ' карточек · авто из меню' : '🏗️ ' + ((cfg.manual_items||cfg.items||[]).length) + ' карточек · ' + (cfg.cols||3) + ' кол.';
                case 'documents':
                    return '📄 ' + ((cfg.items||cfg.docs||[]).length) + ' документов';
                case 'form':
                    return '📋 ' + (cfg.form_type === 'suggest' ? 'Предложить новость' : 'Обратная связь');
                case 'divider':
                    return '➖➖➖➖➖➖➖➖➖➖';
                default:
                    return block.name || '';
            }
        },

        stripHtml: function(s) {
            if (!s) return '';
            return s.replace(/<[^>]*>/g, '');
        },

        addBlock: function() {
            var type = $('#zolo-block-type').val();
            if (!type) { this.toast('⚠️ Выберите тип блока'); return; }
            $('#zolo-block-type').val('');

            var names = {
                hero:'🧱 Hero / Баннер', text:'📝 Текст', image:'🖼️ Изображение',
                gallery:'📸 Галерея', video:'🎬 Видео (Rutube/VK)', table:'📊 Таблица',
                cards:'🏗️ Карточки / Плитки', documents:'📄 Документы', form:'📋 Форма',
                divider:'➖ Разделитель'
            };

            var defaults = {
                hero: { title:'', subtitle:'', bg_image:'', btn_text:'', btn_url:'', bg_color:'#1b4332' },
                text: { text:'', content:'<p>Введите текст</p>' },
                image: { image_url:'', caption:'', alt:'' },
                gallery: { cols:'3', items:[] },
                video: { video_url:'', embed:'' },
                table: { headers:['Колонка 1','Колонка 2'], rows:[['','']] },
                cards: { auto_from_tree:true, manual_items:[], all_link_text:'Все разделы →', all_link_url:'', cols:3 },
                documents: { items:[] },
                form: { form_type:'feedback', title:'Форма' },
                divider: { style:'solid' }
            };

            var block = {
                id: 'b' + Date.now(),
                type: type,
                name: names[type] || type,
                config: defaults[type] || {}
            };

            this.currentBlocks.push(block);
            this.isDirty = true;
            this.renderBlocks();
            this.updateDraftStatus();
            this.toast('✅ Блок «' + names[type] + '» добавлен');
        },

        moveBlock: function(from, to) {
            if (from < 0 || from >= this.currentBlocks.length) return;
            if (to < 0 || to >= this.currentBlocks.length) return;
            var item = this.currentBlocks.splice(from, 1)[0];
            this.currentBlocks.splice(to, 0, item);
            this.isDirty = true;
            this.renderBlocks();
            this.updateDraftStatus();
        },

        deleteBlock: function(idx) {
            if (!confirm('Удалить этот блок?')) return;
            this.currentBlocks.splice(idx, 1);
            this.isDirty = true;
            this.renderBlocks();
            this.updateDraftStatus();
            this.toast('🗑️ Блок удалён');
        },

        // ── BLOCK CONFIG MODAL ──

        showBlockConfigModal: function(idx) {
            var block = this.currentBlocks[idx];
            if (!block) return;
            this.editingBlockIdx = idx;

            var $overlay = $('#zolo-modal-block-overlay');
            var $body = $('#zolo-modal-block-body');
            $body.empty();

            $('#zolo-modal-block-title').text('⚙️ ' + this.esc(block.name));
            var cfg = $.extend(true, {}, block.config || {});
            var html = '';

            // Common: block name field
            html += this.field('Название блока', 'block-name', block.name);

            switch (block.type) {
                case 'hero':
                    html += this.field('Заголовок', 'hero-title', cfg.title);
                    html += this.fieldArea('Подзаголовок', 'hero-subtitle', cfg.subtitle);
                    html += this.field('Текст кнопки', 'hero-btn', cfg.btn_text);
                    html += this.field('Ссылка кнопки', 'hero-url', cfg.btn_url);
                    html += '<div class="zolo-field"><label>Цвет фона</label><input type="color" class="zolo-cfg" data-key="hero-bg" value="' + (cfg.bg_color || '#1b4332') + '" style="width:60px;height:36px;border:2px solid #dee2e6;border-radius:8px;padding:2px;cursor:pointer;"></div>';
                    html += this.field('Фоновое изображение (URL)', 'hero-image', cfg.bg_image, 'url');
                    break;
                case 'text':
                    html += this.fieldArea('Текст (HTML)', 'text-content', cfg.text || cfg.content);
                    break;
                case 'image':
                    html += this.field('URL изображения', 'image-src', cfg.image_url, 'url');
                    html += this.field('Alt-текст', 'image-alt', cfg.alt);
                    html += this.field('Подпись', 'image-caption', cfg.caption);
                    break;
                case 'gallery':
                    html += '<div class="zolo-field"><label>Колонок в сетке</label><input type="number" class="zolo-cfg" data-key="gallery-cols" value="' + (cfg.cols || 3) + '" min="1" max="6"></div>';
                    var items = cfg.items || cfg.images || [];
                    html += '<div class="zolo-field"><label>URL фото (каждый с новой строки)</label><textarea class="zolo-cfg" data-key="gallery-items" rows="5">' + this.esc(items.join('\n')) + '</textarea></div>';
                    break;
                case 'video':
                    html += this.field('Ссылка (Rutube / VK Video)', 'video-url', cfg.video_url, 'url');
                    html += this.field('Embed URL', 'video-embed', cfg.embed, 'url');
                    break;
                case 'table':
                    html += '<div class="zolo-field"><label>Заголовки колонок (через |)</label><input type="text" class="zolo-cfg" data-key="table-headers" value="' + this.esc((cfg.headers||[]).join(' | ')) + '"></div>';
                    html += '<div class="zolo-field"><label>Данные таблицы (каждая строка — значения через |)</label><textarea class="zolo-cfg" data-key="table-rows" rows="5">' + this.esc((cfg.rows||[]).map(function(r) { return (r||[]).join(' | '); }).join('\n')) + '</textarea></div>';
                    break;
                case 'cards':
                    html += '<div class="zolo-field"><label>Колонок</label><input type="number" class="zolo-cfg" data-key="cards-cols" value="' + (cfg.cols || 3) + '" min="1" max="6"></div>';
                    var isAuto = cfg.auto_from_tree !== false;
                    html += '<div class="zolo-field"><label><input type="checkbox" class="zolo-cfg" data-key="cards-auto" ' + (isAuto ? 'checked' : '') + ' onclick="zoloApp.toggleCardsMode(this)"> 🌳 Автоматически из разделов сайта</label></div>';
                    html += this.field('Подпись «Смотреть все»', 'cards-all-link', cfg.all_link_text || 'Все разделы →');

                    if (isAuto) {
                        var self = this;
                        var roots = this.getRoots().filter(function(p) { return p.id !== 'home'; });
                        var autoLines = roots.map(function(p) {
                            var override = (cfg.card_overrides && cfg.card_overrides[p.id]) || {};
                            return p.id + ' | ' + (override.image || '') + ' | ' + (override.text || '');
                        }).join('\n');
                        html += '<div class="zolo-field"><label>Карточки разделов (редактирование описаний):</label>';
                        html += '<textarea class="zolo-cfg" data-key="cards-auto-items" rows="' + Math.max(roots.length, 3) + '">' + this.esc(autoLines) + '</textarea></div>';
                        html += '<div style="font-size:11px;color:#888;margin-top:-8px;margin-bottom:12px;">Формат: <strong>id_раздела | URL_картинки | описание</strong><br>Оставь картинку пустой — будет иконка раздела.</div>';
                        html += '<div id="zolo-cards-manual-fields" style="display:none;"></div>';
                    } else {
                        html += '<div class="zolo-field" id="zolo-cards-manual-fields"><label>Карточки (каждая с новой строки: Название | Описание | Ссылка | Иконка/URL)</label>';
                        html += '<textarea class="zolo-cfg" data-key="cards-items" rows="5">' + this.esc((cfg.manual_items || cfg.items || []).map(function(i) { return i.title + ' | ' + (i.text||i.description||'') + ' | ' + (i.link||i.url||'#') + ' | ' + (i.image||i.icon||''); }).join('\n')) + '</textarea></div>';
                    }
                    break;
                case 'documents':
                    html += '<div class="zolo-field"><label>Документы (каждый с новой строки: Название | URL | Описание)</label>';
                    html += '<textarea class="zolo-cfg" data-key="docs-items" rows="5">' + this.esc((cfg.items || cfg.docs || []).map(function(d) { return d.title + ' | ' + (d.url || d.file_url || '#') + ' | ' + (d.description || ''); }).join('\n')) + '</textarea></div>';
                    break;
                case 'form':
                    html += '<div class="zolo-field"><label>Тип формы</label><select class="zolo-cfg" data-key="form-type">' +
                        '<option value="feedback"' + (cfg.form_type === 'feedback' ? ' selected' : '') + '>💬 Обратная связь</option>' +
                        '<option value="suggest"' + (cfg.form_type === 'suggest' || cfg.form_type === 'news_suggest' ? ' selected' : '') + '>📋 Предложить новость</option></select></div>';
                    html += this.field('Заголовок формы', 'form-title', cfg.title || cfg.placeholder);
                    break;
                case 'divider':
                    html += '<div class="zolo-field"><label>Стиль</label><select class="zolo-cfg" data-key="divider-style">' +
                        '<option value="solid"' + (cfg.style === 'solid' || !cfg.style ? ' selected' : '') + '>Сплошная</option>' +
                        '<option value="dashed"' + (cfg.style === 'dashed' ? ' selected' : '') + '>Пунктирная</option>' +
                        '<option value="dotted"' + (cfg.style === 'dotted' ? ' selected' : '') + '>Точечная</option></select></div>';
                    break;
            }

            $body.html(html + '<input type="hidden" class="zolo-cfg" data-key="_idx" value="' + idx + '">');
            $overlay.addClass('open');

            var self2 = this;
            $('#zolo-modal-block-save').off('click').on('click', function() {
                self2.saveBlockConfig();
            });
        },

        toggleCardsMode: function(checkbox) {
            // This is handled dynamically — on save we check the state
        },

        saveBlockConfig: function() {
            var idx = this.editingBlockIdx;
            if (idx < 0 || idx >= this.currentBlocks.length) return;
            var block = this.currentBlocks[idx];

            // Read all cfg fields
            var values = {};
            $('#zolo-modal-block-body .zolo-cfg').each(function() {
                var $el = $(this);
                var key = $el.data('key');
                if (key === '_idx') return;
                if ($el.is(':checkbox')) {
                    values[key] = $el.is(':checked');
                } else {
                    values[key] = $el.val();
                }
            });

            // Apply block name
            if (values['block-name']) block.name = values['block-name'];

            // Rebuild config based on type using mapping from prototype
            var config = {};
            switch (block.type) {
                case 'hero':
                    config.title = values['hero-title'] || '';
                    config.subtitle = values['hero-subtitle'] || '';
                    config.btn_text = values['hero-btn'] || '';
                    config.btn_url = values['hero-url'] || '';
                    config.bg_color = values['hero-bg'] || '#1b4332';
                    config.bg_image = values['hero-image'] || '';
                    break;
                case 'text':
                    config.content = values['text-content'] || '';
                    config.text = values['text-content'] || '';
                    break;
                case 'image':
                    config.image_url = values['image-src'] || '';
                    config.caption = values['image-caption'] || '';
                    config.alt = values['image-alt'] || '';
                    config.src = values['image-src'] || '';
                    break;
                case 'gallery':
                    config.cols = parseInt(values['gallery-cols']) || 3;
                    config.items = (values['gallery-items'] || '').split('\n').map(function(s) { return s.trim(); }).filter(Boolean);
                    config.images = config.items;
                    break;
                case 'video':
                    config.video_url = values['video-url'] || '';
                    config.embed = values['video-embed'] || '';
                    config.url = values['video-url'] || '';
                    break;
                case 'table':
                    config.headers = (values['table-headers'] || '').split('|').map(function(s) { return s.trim(); }).filter(Boolean);
                    config.rows = (values['table-rows'] || '').split('\n').filter(Boolean).map(function(line) {
                        return line.split('|').map(function(s) { return s.trim(); });
                    });
                    break;
                case 'cards':
                    config.cols = parseInt(values['cards-cols']) || 3;
                    config.all_link_text = values['cards-all-link'] || 'Все разделы →';
                    var isAuto = values['cards-auto'] === true || values['cards-auto'] === 'true';
                    if (isAuto) {
                        config.auto_from_tree = true;
                        config.card_overrides = {};
                        var autoLines = (values['cards-auto-items'] || '').split('\n').filter(Boolean);
                        autoLines.forEach(function(line) {
                            var parts = line.split('|').map(function(s) { return s.trim(); });
                            if (parts[0]) {
                                config.card_overrides[parts[0]] = {
                                    image: parts[1] || '',
                                    text: parts[2] || ''
                                };
                            }
                        });
                        config.manual_items = [];
                        config.items = [];
                    } else {
                        config.auto_from_tree = false;
                        config.card_overrides = {};
                        config.manual_items = (values['cards-items'] || '').split('\n').filter(Boolean).map(function(line) {
                            var parts = line.split('|').map(function(s) { return s.trim(); });
                            return { title: parts[0] || '', text: parts[1] || '', link: parts[2] || '#', image: parts[3] || '', icon: parts[3] || '' };
                        });
                        config.items = config.manual_items;
                    }
                    break;
                case 'documents':
                    config.items = (values['docs-items'] || '').split('\n').filter(Boolean).map(function(line) {
                        var parts = line.split('|').map(function(s) { return s.trim(); });
                        return { title: parts[0] || '', url: parts[1] || '#', description: parts[2] || '' };
                    });
                    config.docs = config.items;
                    break;
                case 'form':
                    config.form_type = values['form-type'] || 'feedback';
                    config.title = values['form-title'] || '';
                    config.placeholder = values['form-title'] || '';
                    break;
                case 'divider':
                    config.style = values['divider-style'] || 'solid';
                    break;
            }

            block.config = config;
            this.isDirty = true;
            this.closeModal();
            this.renderBlocks();
            this.updateDraftStatus();
            this.toast('💾 Блок настроен');
        },

        field: function(label, key, value, type) {
            type = type || 'text';
            return '<div class="zolo-field"><label>' + label + '</label><input type="' + type + '" class="zolo-cfg zolo-input" data-key="' + key + '" value="' + this.esc(value||'') + '"></div>';
        },
        fieldArea: function(label, key, value) {
            return '<div class="zolo-field"><label>' + label + '</label><textarea class="zolo-cfg zolo-input" data-key="' + key + '" rows="4">' + this.esc(value||'') + '</textarea></div>';
        },

        // ── SAVE / PUBLISH / PREVIEW ──

        saveDraft: function() {
            if (!this.currentPageId) return;
            var self = this;

            // Also save page status
            var page = this.getPage(this.currentPageId);
            if (page) page.status = 'draft';

            $.post(zoloData.ajaxUrl, {
                action: 'zolo_save_blocks',
                nonce: zoloData.nonce,
                page_id: this.currentPageId,
                blocks: JSON.stringify(this.currentBlocks)
            }).done(function(resp) {
                if (!resp.success) { self.toast('❌ Ошибка сохранения'); return; }
                self.isDirty = false;
                self.updateDraftStatus();
                self.renderTree();
                self.toast('💾 Черновик сохранён');
            });
        },

        publishPage: function() {
            if (!this.currentPageId) return;
            var self = this;

            // Save draft first, then publish
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_save_blocks',
                nonce: zoloData.nonce,
                page_id: this.currentPageId,
                blocks: JSON.stringify(this.currentBlocks)
            }).done(function() {
                $.post(zoloData.ajaxUrl, {
                    action: 'zolo_publish_page',
                    nonce: zoloData.nonce,
                    page_id: self.currentPageId
                }).done(function(resp) {
                    if (!resp.success) { self.toast('❌ Ошибка публикации'); return; }
                    self.isDirty = false;
                    // Update page status
                    var page = self.getPage(self.currentPageId);
                    if (page) page.status = 'published';
                    self.updateDraftStatus();
                    self.renderTree();
                    self.toast('📢 Страница опубликована');
                });
            });
        },

        publishAll: function() {
            if (!confirm('Опубликовать все страницы?')) return;
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_publish_all',
                nonce: zoloData.nonce
            }).done(function(resp) {
                self.toast(resp.data.message || '✅ Всё опубликовано');
                if (self.currentPageId) self.selectPage(self.currentPageId);
            });
        },

        previewPage: function() {
            if (!this.currentPageId) return;
            window.open(zoloData.adminUrl + 'admin-post.php?action=zolo_preview_page&page_id=' + this.currentPageId, '_blank');
        },

        deletePage: function(pageId) {
            if (pageId === 'home') { this.toast('⚠️ Главную страницу нельзя удалить'); return; }
            var page = this.getPage(pageId);
            if (!page) return;

            var children = this.getChildren(pageId);
            var msg = children.length > 0
                ? 'Удалить «' + page.name + '» и все её подразделы (' + children.length + ')?'
                : 'Удалить страницу «' + page.name + '»?';
            if (!confirm(msg)) return;

            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_delete_page',
                nonce: zoloData.nonce,
                page_id: pageId
            }).done(function(resp) {
                if (!resp.success) return;
                self.pages = self.pages.filter(function(p) { return p.id !== pageId && p.parent !== pageId; });
                self.renderTree();
                self.updatePageCount();
                if (self.currentPageId === pageId || !self.getPage(self.currentPageId)) {
                    self.currentPageId = null;
                    $('#zolo-editor').hide();
                    $('#zolo-empty').show();
                }
                self.toast('🗑️ «' + page.name + '» удалена');
            });
        },

        // ── PAGE MODAL (ADD / EDIT) ──

        showPageModal: function(mode) {
            var isSub = mode === 'sub';
            $('#zolo-modal-page-title').text(isSub ? '➕ Новый подраздел' : '➕ Новый раздел');
            $('#zolo-modal-page-parent-field').toggle(isSub);
            $('#zolo-modal-page-name').val('');
            $('#zolo-modal-page-icon').val('📄');
            $('#zolo-modal-page-slug').val('');
            $('#zolo-modal-page-order').val('99');

            var $parent = $('#zolo-modal-page-parent');
            $parent.find('option:not(:first)').remove();
            if (isSub) {
                var self = this;
                this.pages.forEach(function(p) {
                    if (!p.parent) {
                        $parent.append('<option value="' + p.id + '">' + p.icon + ' ' + p.name + '</option>');
                    }
                });
            }

            $('#zolo-modal-page-overlay').addClass('open');

            var self2 = this;
            $('#zolo-modal-page-save').off('click').on('click', function() {
                var name = $('#zolo-modal-page-name').val().trim();
                if (!name) { self2.toast('⚠️ Введите название страницы'); return; }
                var icon = $('#zolo-modal-page-icon').val().trim() || '📄';
                var parent = isSub ? $('#zolo-modal-page-parent').val() : '';
                var slug = $('#zolo-modal-page-slug').val().trim();
                var order = parseInt($('#zolo-modal-page-order').val()) || 99;
                self2.createPage(name, icon, parent, order, slug);
                self2.closeModal();
            });
        },

        showEditPageModal: function(pageId) {
            var page = this.getPage(pageId);
            if (!page) return;

            $('#zolo-edit-modal-page-title').text(page.name);
            $('#zolo-edit-page-name').val(page.name);
            $('#zolo-edit-page-icon').val(page.icon);
            $('#zolo-edit-page-slug').val(page.id);
            $('#zolo-edit-page-order').val(page.order);

            // Parent select
            var $parent = $('#zolo-edit-page-parent');
            $parent.find('option:not(:first)').remove();
            var self = this;
            this.pages.forEach(function(p) {
                if (!p.parent && p.id !== pageId) {
                    $parent.append('<option value="' + p.id + '">' + p.icon + ' ' + p.name + '</option>');
                }
            });
            $parent.val(page.parent || '');

            $('#zolo-edit-modal-page-overlay').addClass('open');

            var self2 = this;
            $('#zolo-edit-modal-page-save').off('click').on('click', function() {
                var name = $('#zolo-edit-page-name').val().trim();
                if (!name) { self2.toast('⚠️ Введите название'); return; }
                var icon = $('#zolo-edit-page-icon').val().trim() || '📄';
                var newParent = $('#zolo-edit-page-parent').val() || '';
                var newSlug = $('#zolo-edit-page-slug').val().trim() || page.id;
                var newOrder = parseInt($('#zolo-edit-page-order').val()) || page.order;

                page.name = name;
                page.icon = icon;
                page.parent = newParent;
                page.order = newOrder;
                page.status = page.status || 'draft';

                if (newSlug !== page.id) {
                    // Need to update id — for now just save
                    page.id = newSlug;
                }

                $.post(zoloData.ajaxUrl, {
                    action: 'zolo_save_page',
                    nonce: zoloData.nonce,
                    id: page.id,
                    name: page.name,
                    icon: page.icon,
                    parent: page.parent,
                    order: page.order,
                    status: page.status
                }).done(function(resp) {
                    if (!resp.success) return;
                    self2.pages = resp.data.pages;
                    self2.renderTree();
                    self2.updatePageCount();
                    self2.closeModal();
                    self2.toast('💾 Страница обновлена');
                    if (self2.currentPageId) self2.selectPage(self2.currentPageId);
                });
            });
        },

        createPage: function(name, icon, parent, order, customSlug) {
            var id = customSlug || this.transliterate(name.toLowerCase()
                .replace(/[^a-zа-яё0-9\s-]+/gi, '')
                .replace(/\s+/g, '-')
                .replace(/^-+|-+$/g, ''));
            if (!id) id = 'page-' + Date.now();

            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_save_page',
                nonce: zoloData.nonce,
                id: id,
                name: name,
                icon: icon,
                parent: parent,
                order: order,
                status: 'draft'
            }).done(function(resp) {
                if (!resp.success) return;
                self.pages = resp.data.pages;
                self.renderTree();
                self.updatePageCount();
                self.toast('➕ Страница «' + name + '» создана');
                self.selectPage(id);
            });
        },

        transliterate: function(text) {
            var map = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'};
            return text.split('').map(function(c) { return map[c] || (c.match(/[a-z0-9-]/) ? c : ''); }).join('');
        },

        // ── NAVIGATION ──

        switchTo: function(section) {
            this.currentSection = section;
            // Hide all editors
            $('#zolo-editor-pages, #zolo-editor-users, #zolo-editor-media, #zolo-editor-content, #zolo-editor-settings').hide();
            // Deactivate all nav buttons
            $('.zolo-nav-btn').removeClass('zolo-nav-active');
            $('.zolo-nav-btn[data-section="' + section + '"]').addClass('zolo-nav-active');
            // Show/hide sidebar pages tree
            $('#zolo-sidebar-pages').toggle(section === 'pages');

            if (section === 'users') {
                $('#zolo-editor-users').show();
                this.renderRoles();
                this.renderUsers();
                this.renderUsersStats();
            } else if (section === 'pages') {
                $('#zolo-editor-pages').show();
            } else if (section === 'media') {
                $('#zolo-editor-media').show();
                this.renderVideos();
                this.renderGalleryItems();
            } else if (section === 'content') {
                $('#zolo-editor-content').show();
                this.renderContentList();
            } else if (section === 'settings') {
                $('#zolo-editor-settings').show();
                this.renderSettings();
            }
        },

        // ── MEDIA: VIDEOS ──

        renderVideos: function() {
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_get_videos',
                nonce: zoloData.nonce
            }).done(function(resp) {
                if (!resp.success) return;
                var $list = $('#zolo-video-list');
                $list.empty();
                var videos = resp.data.videos || [];
                if (!videos.length) {
                    $list.html('<p style="color:#888;padding:12px;">Нет видео</p>');
                    return;
                }
                var html = '<div class="zolo-media-grid">';
                videos.forEach(function(v) {
                    html += '<div class="zolo-media-card">' +
                        '<div class="title">🎬 ' + self.esc(v.title) + '</div>' +
                        '<div class="meta">' + self.esc(v.url || '—').substring(0, 50) + '</div>' +
                        '<div class="actions">' +
                            '<button class="zolo-btn zolo-btn-red" style="font-size:11px;padding:3px 8px;" onclick="zoloApp.deleteVideo(' + v.id + ')">🗑️</button>' +
                        '</div></div>';
                });
                html += '</div>';
                $list.html(html);
            });
        },

        saveVideo: function() {
            var title = $('#zolo-video-title').val().trim();
            var url = $('#zolo-video-url').val().trim();
            var desc = $('#zolo-video-desc').val().trim();
            if (!title || !url) { this.toast('Введите название и URL видео'); return; }
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_save_video',
                nonce: zoloData.nonce,
                title: title,
                video_url: url,
                description: desc
            }).done(function(resp) {
                if (!resp.success) { self.toast('❌ Ошибка'); return; }
                $('#zolo-video-title').val('');
                $('#zolo-video-url').val('');
                $('#zolo-video-desc').val('');
                self.toast('🎬 Видео добавлено');
                self.renderVideos();
            });
        },

        deleteVideo: function(id) {
            if (!confirm('Удалить видео?')) return;
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_delete_video',
                nonce: zoloData.nonce,
                id: id
            }).done(function() {
                self.toast('🗑️ Видео удалено');
                self.renderVideos();
            });
        },

        // ── MEDIA: GALLERY ──

        renderGalleryItems: function() {
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_get_gallery_items',
                nonce: zoloData.nonce
            }).done(function(resp) {
                if (!resp.success) return;
                var $list = $('#zolo-gallery-list');
                $list.empty();
                var items = resp.data.items || [];
                if (!items.length) {
                    $list.html('<p style="color:#888;padding:12px;">Галерея пуста</p>');
                    return;
                }
                var html = '<div class="zolo-media-grid">';
                items.forEach(function(item) {
                    var thumb = item.thumb ? '<img src="' + self.esc(item.thumb) + '" style="width:100%;height:120px;object-fit:cover;border-radius:6px;margin-bottom:6px;">"<br>' : '';
                    html += '<div class="zolo-media-card">' +
                        thumb +
                        '<div class="title">📸 ' + self.esc(item.title) + '</div>' +
                        '<div class="meta">' + self.esc(item.date) + '</div>' +
                        '<div class="actions">' +
                            '<button class="zolo-btn zolo-btn-red" style="font-size:11px;padding:3px 8px;" onclick="zoloApp.deleteGalleryItem(' + item.id + ')">🗑️</button>' +
                        '</div></div>';
                });
                html += '</div>';
                $list.html(html);
            });
        },

        saveGalleryItem: function() {
            var title = $('#zolo-gallery-title').val().trim();
            if (!title) { this.toast('Введите название'); return; }
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_save_gallery_item',
                nonce: zoloData.nonce,
                title: title
            }).done(function(resp) {
                if (!resp.success) { self.toast('❌ Ошибка'); return; }
                $('#zolo-gallery-title').val('');
                self.toast('📸 Элемент добавлен');
                self.renderGalleryItems();
            });
        },

        deleteGalleryItem: function(id) {
            if (!confirm('Удалить элемент?')) return;
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_delete_gallery_item',
                nonce: zoloData.nonce,
                id: id
            }).done(function() {
                self.toast('🗑️ Удалено');
                self.renderGalleryItems();
            });
        },

        // ── CONTENT LIST ──

        renderContentList: function() {
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_get_recent_content',
                nonce: zoloData.nonce
            }).done(function(resp) {
                if (!resp.success) return;
                var $list = $('#zolo-content-list');
                $list.empty();
                var content = resp.data.content || {};
                var labels = {
                    school_news: '📚 Школьные новости',
                    kindergarten_news: '🧸 Новости детсада',
                    farm_production: '🌾 Продукция совхоза',
                    farm_vacancies: '💼 Вакансии совхоза',
                    sports_team: '⚽ Спортивные команды',
                    sports_match: '🏆 Матчи',
                    bulletin_board: '📋 Объявления'
                };
                var found = false;
                for (var cpt in content) {
                    if (!content.hasOwnProperty(cpt)) continue;
                    found = true;
                    var items = content[cpt];
                    var label = labels[cpt] || cpt;
                    var html = '<div class="zolo-content-section">';
                    html += '<div class="zolo-section-title">' + label + ' <span class="zolo-badge">' + items.length + '</span></div>';
                    html += '<div class="items">';
                    items.forEach(function(item) {
                        var statusBadge = item.status === 'publish'
                            ? '<span class="status-badge" style="background:#d3f9d8;color:#2d6a4f;">✅ Опубликовано</span>'
                            : '<span class="status-badge" style="background:#fff3bf;color:#856404;">⏳ На модерации</span>';
                        var editUrl = zoloData.adminUrl + 'post.php?post=' + item.id + '&action=edit';
                        html += '<div class="zolo-content-item">' +
                            '<span class="title">' + self.esc(item.title) + '</span>' +
                            statusBadge +
                            '<span style="font-size:11px;color:#888;">' + self.esc(item.date) + '</span>' +
                            '<span style="font-size:11px;color:#888;">' + self.esc(item.author) + '</span>' +
                            '<button class="zolo-btn" style="font-size:11px;padding:3px 8px;" onclick="window.open(\'' + editUrl + '\',\'_blank\')">✏️</button>' +
                        '</div>';
                    });
                    html += '</div></div>';
                    $list.append($(html));
                }
                if (!found) {
                    $list.html('<p style="color:#888;padding:12px;">Нет контента</p>');
                }
            });
        },

        // ── SETTINGS ──

        renderSettings: function() {
            var $form = $('#zolo-settings-form');
            var settings = this._settings || {};
            var html = '<table class="form-table">';

            html += '<tr><th colspan="2"><h2 style="margin:0;">🌐 Социальные сети</h2></th></tr>';
            html += this.settingField('VK', 'social_vk', settings.social_vk);
            html += this.settingField('Telegram', 'social_telegram', settings.social_telegram);
            html += this.settingField('OK', 'social_ok', settings.social_ok);
            html += this.settingField('RSS', 'social_rss', settings.social_rss);

            html += '<tr><th colspan="2"><h2 style="margin:0;">📞 Контакты</h2></th></tr>';
            html += this.settingField('Email', 'contact_email', settings.contact_email);
            html += this.settingField('Телефон', 'contact_phone', settings.contact_phone);
            html += this.settingField('Адрес', 'contact_address', settings.contact_address);

            html += '<tr><th colspan="2"><h2 style="margin:0;">🎨 Текст</h2></th></tr>';
            html += this.settingField('Теглайн', 'site_tagline', settings.site_tagline);
            html += this.settingField('Топ-бар', 'topbar_region', settings.topbar_region);
            html += this.settingField('Копирайт', 'footer_copyright', settings.footer_copyright);

            html += '</table>';
            $form.html(html);
        },

        settingField: function(label, key, value) {
            return '<tr><th>' + label + '</th><td><input type="text" class="zolo-setting-input zolo-input" data-key="' + key + '" value="' + this.esc(value||'') + '" style="max-width:400px;"></td></tr>';
        },

        saveSettings: function() {
            var settings = {};
            $('.zolo-setting-input').each(function() {
                settings[$(this).data('key')] = $(this).val();
            });
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_save_site_settings',
                nonce: zoloData.nonce,
                settings: JSON.stringify(settings)
            }).done(function(resp) {
                if (!resp.success) { self.toast('❌ Ошибка'); return; }
                self._settings = resp.data.settings;
                self.toast('⚙️ Настройки сохранены');
            });
        },

        // ── ROLES ──

        renderRoles: function() {
            var $tbody = $('#zolo-roles-tbody');
            $tbody.empty();
            var self = this;
            this.roles.forEach(function(r) {
                var sections = '';
                if (r.sections === '__all__') {
                    sections = '🔓 Все разделы';
                } else if ((r.sections||[]).length > 0) {
                    sections = r.sections.map(function(s) {
                        var p = self.getPage(s);
                        return p ? p.icon + ' ' + p.name : s;
                    }).join(', ');
                } else {
                    sections = '—';
                }

                $tbody.append('<tr>' +
                    '<td style="padding:10px 14px; font-weight:600;">' + r.icon + ' ' + self.esc(r.name) + '</td>' +
                    '<td style="padding:10px 14px;">' + (r.user_count||0) + '</td>' +
                    '<td style="padding:10px 14px; font-size:11px; color:#555;">' + self.esc(sections) + '</td>' +
                    '<td style="padding:10px 14px;">' +
                        '<button class="zolo-btn zolo-btn-blue zolo-role-edit" data-id="' + r.id + '" style="font-size:11px;padding:3px 8px;">✏️</button> ' +
                        (r.id !== 'admin' && !r.protected ? '<button class="zolo-btn zolo-btn-red zolo-role-delete" data-id="' + r.id + '" style="font-size:11px;padding:3px 8px;">🗑️</button>' : '') +
                    '</td>' +
                '</tr>');
            });

            $tbody.find('.zolo-role-edit').on('click', function() {
                var rid = $(this).data('id');
                self.showRoleSectionsModal(rid);
            });
            $tbody.find('.zolo-role-delete').on('click', function() {
                var rid = $(this).data('id');
                if (!confirm('Удалить роль?')) return;
                $.post(zoloData.ajaxUrl, {
                    action: 'zolo_delete_role',
                    nonce: zoloData.nonce,
                    role_id: rid
                }).done(function(resp) {
                    if (!resp.success) return;
                    self.roles = resp.data.roles;
                    self.renderRoles();
                    self.updateUsersSummary();
                    self.toast('🗑️ Роль удалена');
                });
            });
        },

        renderUsers: function() {
            var $tbody = $('#zolo-users-tbody');
            $tbody.empty();
            var self = this;
            this.users.forEach(function(u) {
                var roleText = u.role || '—';
                $tbody.append('<tr>' +
                    '<td style="padding:10px 14px; font-weight:600;">' + self.esc(u.name) + '</td>' +
                    '<td style="padding:10px 14px; color:#888;">' + self.esc(u.email) + '</td>' +
                    '<td style="padding:10px 14px;">' + self.esc(roleText) + '</td>' +
                    '<td style="padding:10px 14px;"><span class="status-badge" style="background:#d3f9d8;color:#2d6a4f;">Активен</span></td>' +
                    '<td style="padding:10px 14px;"><button class="zolo-btn" style="font-size:11px;padding:3px 8px;" onclick="window.open(\'' + zoloData.adminUrl + 'user-edit.php?user_id=' + u.id + '\',\'_blank\')">✏️</button></td>' +
                '</tr>');
            });
        },

        renderUsersStats: function() {
            var $stats = $('#zolo-users-stats');
            var roleCounts = {};
            var self = this;
            this.users.forEach(function(u) {
                (u.role || '').split(', ').forEach(function(r) {
                    roleCounts[r] = (roleCounts[r] || 0) + 1;
                });
            });
            var colors = ['#d3f9d8','#e3f2fd','#fff3bf','#f3e5f5','#fce4ec','#e0f7fa'];
            var html = '';
            var idx = 0;
            for (var role in roleCounts) {
                if (!roleCounts.hasOwnProperty(role)) continue;
                var color = colors[idx % colors.length];
                html += '<div class="zolo-stat-card" style="background:' + color + ';">' +
                    '<div class="num">' + roleCounts[role] + '</div>' +
                    '<div class="label">' + self.esc(role) + '</div></div>';
                idx++;
            }
            $stats.html(html);
        },

        updateUsersSummary: function() {
            $('#zolo-users-summary').text(this.roles.length + ' ролей · ' + this.users.length + ' пользователей');
        },

        showRoleSectionsModal: function(roleId) {
            var role = null;
            for (var i = 0; i < this.roles.length; i++) {
                if (this.roles[i].id === roleId) { role = this.roles[i]; break; }
            }
            if (!role) return;

            var $overlay = $('#zolo-modal-block-overlay');
            var $body = $('#zolo-modal-block-body');
            $body.empty();

            $('#zolo-modal-block-title').text('✏️ ' + role.icon + ' ' + this.esc(role.name) + ' — доступ к разделам');
            var html = '<p><strong>Выберите разделы для доступа:</strong></p><div style="max-height:400px;overflow-y:auto;border:1px solid #e9ecef;border-radius:8px;padding:12px;">';

            var self = this;

            // "Все разделы" option
            var allChecked = role.sections === '__all__' ? 'checked' : '';
            html += '<label style="font-weight:600;display:block;margin:4px 0 8px;padding-bottom:8px;border-bottom:1px solid #dee2e6;">' +
                '<input type="checkbox" class="zolo-role-section-cb" data-section="__all__" ' + allChecked + ' onchange="zoloApp.toggleRoleAllSections(this)"> 🔓 Все разделы (полный доступ)</label>';

            this.pages.forEach(function(p) {
                var checked2 = role.sections === '__all__' || (role.sections||[]).indexOf(p.id) !== -1 ? 'checked' : '';
                var indent = p.parent ? 'padding-left:24px;' : '';
                html += '<label style="display:block;margin:4px 0;' + indent + '">' +
                    '<input type="checkbox" class="zolo-role-section-cb" data-section="' + p.id + '" value="' + p.id + '" ' + checked2 + '> ' + p.icon + ' ' + self.esc(p.name) + '</label>';
            });

            html += '</div><input type="hidden" id="zolo-role-id-input" value="' + roleId + '">';
            $body.html(html);
            $overlay.addClass('open');

            $('#zolo-modal-block-save').off('click').on('click', function() {
                var sections = [];
                if ($('#zolo-modal-block-body .zolo-role-section-cb[data-section="__all__"]').is(':checked')) {
                    sections = '__all__';
                } else {
                    $('#zolo-modal-block-body .zolo-role-section-cb:checked').each(function() {
                        sections.push($(this).val());
                    });
                }
                var rid = $('#zolo-role-id-input').val();
                for (var j = 0; j < self.roles.length; j++) {
                    if (self.roles[j].id === rid) {
                        self.roles[j].sections = sections;
                        break;
                    }
                }
                // save all roles
                $.post(zoloData.ajaxUrl, {
                    action: 'zolo_save_roles',
                    nonce: zoloData.nonce,
                    roles: JSON.stringify(self.roles)
                }).done(function(resp) {
                    if (!resp.success) return;
                    self.roles = resp.data.roles;
                    self.renderRoles();
                    self.closeModal();
                    self.toast('✅ Роль обновлена');
                });
            });
        },

        toggleRoleAllSections: function(el) {
            var checked = el.checked;
            $('.zolo-role-section-cb').each(function() {
                if ($(this).data('section') !== '__all__') {
                    $(this).prop('checked', checked);
                }
            });
        },

        showAddRoleModal: function() {
            $('#zolo-modal-role-overlay').addClass('open');
            $('#zolo-modal-role-name').val('');
            $('#zolo-modal-role-id').val('');
            $('#zolo-modal-role-icon').val('👤');
            var self = this;
            $('#zolo-modal-role-save').off('click').on('click', function() {
                var name = $('#zolo-modal-role-name').val().trim();
                var id = $('#zolo-modal-role-id').val().trim();
                var icon = $('#zolo-modal-role-icon').val().trim() || '👤';
                if (!name) { self.toast('Введите название'); return; }
                if (!id) id = self.transliterate(name.toLowerCase().replace(/\s+/g, '_'));
                var newRole = {id: id, name: name, icon: icon, sections: [], caps: {moderate_comments: false, upload_files: false}, user_count: 0, protected: false};
                self.roles.push(newRole);
                $.post(zoloData.ajaxUrl, {
                    action: 'zolo_save_roles',
                    nonce: zoloData.nonce,
                    roles: JSON.stringify(self.roles)
                }).done(function(resp) {
                    if (!resp.success) return;
                    self.roles = resp.data.roles;
                    self.renderRoles();
                    self.updateUsersSummary();
                    self.closeModal();
                    self.toast('➕ Роль добавлена');
                });
            });
        },

        // ── TOAST / MODAL ──

        toast: function(msg) {
            var $toast = $('#zolo-toast');
            $toast.text(msg).addClass('show');
            clearTimeout(this.toastTimer);
            this.toastTimer = setTimeout(function() {
                $toast.removeClass('show');
            }, 3000);
        },

        closeModal: function() {
            $('.zolo-modal-overlay').removeClass('open');
            this.editingBlockIdx = -1;
        },

        esc: function(str) {
            if (!str) return '';
            return $('<span>').text(str).html();
        },

        // ── EVENTS ──

        bindEvents: function() {
            var self = this;

            // Modal close on overlay click
            $('.zolo-modal-overlay').on('click', function(e) {
                if ($(e.target).hasClass('zolo-modal-overlay')) {
                    $(e.target).removeClass('open');
                }
            });

            // User search
            $('#zolo-user-search').on('input', function() {
                var q = $(this).val().toLowerCase();
                $('#zolo-users-tbody tr').each(function() {
                    var text = $(this).text().toLowerCase();
                    $(this).toggle(text.indexOf(q) !== -1);
                });
            });

            // Ctrl+S save
            $(document).on('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                    e.preventDefault();
                    self.saveDraft();
                }
            });
        }
    };

    window.zoloApp = zoloApp;

    $(document).ready(function() {
        zoloApp.init();
    });

})(jQuery);
