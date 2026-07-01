/**
 * Zolotarevka Admin v2 — конструктор сайта
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

        init: function() {
            this.loadData();
            this.bindEvents();
        },

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
                zoloApp.renderTree();
                zoloApp.updatePageCount();
                zoloApp.renderRoles();
                zoloApp.renderUsers();
                zoloApp.renderUsersStats();
                zoloApp.updateUsersSummary();
            });
        },

        // ── Tree ──

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
            var $item = $('<div class="zolo-tree-node">' +
                '<div class="zolo-tree-item' + (this.currentPageId === page.id ? ' active' : '') + '" data-id="' + page.id + '" style="padding-left:' + (16 + depth * 20) + 'px;">' +
                    '<span class="zolo-tree-icon">' + (page.icon || '📄') + '</span>' +
                    '<span class="zolo-tree-name">' + this.esc(page.name) + '</span>' +
                    '<span class="zolo-page-count">' + this.getChildren(page.id).length + '</span>' +
                    '<span class="zolo-tree-actions">' +
                        '<button class="zolo-tree-edit" title="Редактировать">✏️</button>' +
                        '<button class="zolo-tree-delete" title="Удалить страницу">🗑️</button>' +
                    '</span>' +
                '</div></div>');
            var $itemDiv = $item.find('.zolo-tree-item');
            $itemDiv.on('click', function(e) {
                if ($(e.target).closest('.zolo-tree-actions').length) return;
                self.selectPage(page.id);
            });
            $itemDiv.find('.zolo-tree-edit').on('click', function(e) {
                e.stopPropagation();
                self.selectPage(page.id);
            });
            $itemDiv.find('.zolo-tree-delete').on('click', function(e) {
                e.stopPropagation();
                self.deletePage(page.id);
            });
            $container.append($item);

            var children = this.getChildren(page.id);
            if (children.length) {
                var $childContainer = $('<div class="zolo-tree-children"></div>');
                children.forEach(function(child) {
                    self.renderNode($childContainer, child, depth + 1);
                });
                $container.append($childContainer);
            }
        },

        updatePageCount: function() {
            $('#zolo-page-count').text(this.pages.length + ' страниц');
        },

        // ── Page selection ──

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

            // Load blocks
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_get_blocks',
                nonce: zoloData.nonce,
                page_id: pageId
            }).done(function(resp) {
                if (!resp.success) return;
                zoloApp.currentBlocks = resp.data.blocks || [];
                zoloApp.isDirty = resp.data.has_draft;
                zoloApp.renderBlocks();
                zoloApp.updateStatus();
            });
        },

        getPage: function(id) {
            for (var i = 0; i < this.pages.length; i++) {
                if (this.pages[i].id === id) return this.pages[i];
            }
            return null;
        },

        updateStatus: function() {
            var $status = $('#zolo-current-status');
            if (this.isDirty) {
                $status.text('✏️ Черновик').attr('class', 'zolo-status zolo-status-draft');
            } else {
                $status.text('✅ Опубликовано').attr('class', 'zolo-status zolo-status-published');
            }
        },

        // ── Blocks ──

        renderBlocks: function() {
            var $list = $('#zolo-blocks-list');
            $list.empty();
            var self = this;
            var icons = {
                hero:'🧱',text:'📝',image:'🖼️',gallery:'📸',video:'🎬',
                table:'📊',cards:'🏗️',documents:'📄',form:'📋',divider:'➖'
            };
            this.currentBlocks.forEach(function(b, i) {
                var icon = icons[b.type] || '📦';
                var preview = '';
                if (b.type === 'hero' && b.config) {
                    preview = '<strong>' + self.esc(b.config.title || '') + '</strong>';
                    if (b.config.subtitle) preview += '<br>' + self.esc(b.config.subtitle);
                } else if (b.type === 'text' && b.config) {
                    preview = self.esc((b.config.text || '').substring(0, 120));
                } else if (b.type === 'cards') {
                    preview = b.config && b.config.auto_from_tree ? '🌳 Авто из разделов' : '✏️ Ручной режим';
                } else if (b.type === 'divider') {
                    preview = '➖➖➖➖➖➖➖➖➖➖';
                } else {
                    preview = b.name;
                }

                var $block = $('<div class="zolo-block" data-index="' + i + '">' +
                    '<div class="zolo-block-header">' +
                        '<span class="zolo-drag">⠿</span>' +
                        '<span class="zolo-bicon">' + icon + '</span>' +
                        '<span class="zolo-bname">' + self.esc(b.name) + '</span>' +
                        '<span class="zolo-btype">' + b.type + '</span>' +
                    '</div>' +
                    '<div class="zolo-bpreview">' + preview + '</div>' +
                    '<div class="zolo-bactions">' +
                        '<button class="btn-cfg" data-index="' + i + '">⚙️ Настроить</button>' +
                        '<button class="btn-up" data-index="' + i + '"' + (i === 0 ? ' disabled' : '') + '>⬆</button>' +
                        '<button class="btn-down" data-index="' + i + '"' + (i === self.currentBlocks.length - 1 ? ' disabled' : '') + '>⬇</button>' +
                        '<button class="btn-del" data-index="' + i + '">🗑️</button>' +
                    '</div>' +
                '</div>');

                $block.find('.btn-cfg').on('click', function() {
                    var idx = parseInt($(this).data('index'));
                    self.showBlockConfigModal(idx);
                });
                $block.find('.btn-up').on('click', function() {
                    var idx = parseInt($(this).data('index'));
                    if (idx > 0) self.moveBlock(idx, idx - 1);
                });
                $block.find('.btn-down').on('click', function() {
                    var idx = parseInt($(this).data('index'));
                    if (idx < self.currentBlocks.length - 1) self.moveBlock(idx, idx + 1);
                });
                $block.find('.btn-del').on('click', function() {
                    var idx = parseInt($(this).data('index'));
                    self.deleteBlock(idx);
                });

                $list.append($block);
            });
        },

        addBlock: function() {
            var type = $('#zolo-block-type').val();
            if (!type) { this.toast('Выберите тип блока'); return; }
            $('#zolo-block-type').val('');

            var names = {
                hero:'🧱 Hero / Баннер',text:'📝 Текст',image:'🖼️ Изображение',
                gallery:'📸 Галерея',video:'🎬 Видео',table:'📊 Таблица',
                cards:'🏗️ Карточки',documents:'📄 Документы',form:'📋 Форма',divider:'➖ Разделитель'
            };
            var defaults = {
                hero: {title:'',subtitle:'',bg_image:'',btn_text:'',btn_url:''},
                text: {text:''},
                image: {image_url:'',caption:'',alt:''},
                gallery: {cols:'3',items:[]},
                video: {video_url:'',embed:''},
                table: {headers:['Колонка 1','Колонка 2'],rows:[['',''],['','']]},
                cards: {auto_from_tree:true,manual_items:[],all_link_text:'Все разделы →',all_link_url:''},
                documents: {items:[]},
                form: {form_type:'feedback',placeholder:''},
                divider: {}
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
            this.updateStatus();
        },

        moveBlock: function(from, to) {
            if (from < 0 || from >= this.currentBlocks.length) return;
            var item = this.currentBlocks.splice(from, 1)[0];
            this.currentBlocks.splice(to, 0, item);
            this.isDirty = true;
            this.renderBlocks();
            this.updateStatus();
        },

        deleteBlock: function(idx) {
            if (!confirm('Удалить блок?')) return;
            this.currentBlocks.splice(idx, 1);
            this.isDirty = true;
            this.renderBlocks();
            this.updateStatus();
        },

        // ── Block config modal ──

        showBlockConfigModal: function(idx) {
            var block = this.currentBlocks[idx];
            if (!block) return;
            var $overlay = $('#zolo-modal-block-overlay');
            var $body = $('#zolo-modal-block-body');
            $body.empty();

            $('#zolo-modal-block-title').text('⚙️ ' + this.esc(block.name));
            var cfg = block.config || {};
            var html = '';

            if (block.type === 'hero') {
                html += this.field('Заголовок','title',cfg.title);
                html += this.field('Подзаголовок','subtitle',cfg.subtitle);
                html += this.field('Фоновое изображение (URL)','bg_image',cfg.bg_image,'url');
                html += this.field('Текст кнопки','btn_text',cfg.btn_text);
                html += this.field('Ссылка кнопки','btn_url',cfg.btn_url);
            } else if (block.type === 'text') {
                html += this.fieldArea('Текст (HTML)','text',cfg.text);
            } else if (block.type === 'image') {
                html += this.field('URL изображения','image_url',cfg.image_url,'url');
                html += this.field('Подпись','caption',cfg.caption);
                html += this.field('Alt-текст','alt',cfg.alt);
            } else if (block.type === 'gallery') {
                html += this.field('Колонок','cols',cfg.cols||'3');
                html += '<p style="color:#888;font-size:12px;">Элементы галереи — встроенная галерея WP</p>';
            } else if (block.type === 'video') {
                html += this.field('URL видео (Rutube/VK)','video_url',cfg.video_url,'url');
                html += this.field('Embed URL','embed',cfg.embed,'url');
            } else if (block.type === 'cards') {
                html += this.fieldCheck('Автоматически из разделов','auto_from_tree',cfg.auto_from_tree);
                html += this.field('Текст "Все разделы →"','all_link_text',cfg.all_link_text);
                html += this.field('Ссылка "Все разделы"','all_link_url',cfg.all_link_url);
            } else if (block.type === 'documents') {
                html += '<p style="color:#888;font-size:12px;">Документы — через repeater (будет реализовано)</p>';
            } else if (block.type === 'form') {
                html += '<div class="zolo-field"><label>Тип формы</label><select class="zolo-cfg" data-key="form_type">' +
                    '<option value="feedback"'+(cfg.form_type==='feedback'?' selected':'')+'>Обратная связь</option>' +
                    '<option value="news_suggest"'+(cfg.form_type==='news_suggest'?' selected':'')+'>Предложить новость</option></select></div>';
                html += this.field('Placeholder','placeholder',cfg.placeholder);
            } else if (block.type === 'table') {
                html += '<div class="zolo-field"><label>Данные таблицы</label><textarea class="zolo-cfg" data-key="table_data" rows="4" placeholder="В разработке"></textarea></div>';
            } else if (block.type === 'divider') {
                html += '<p style="color:#888;">Разделитель — без настроек</p>';
            }

            $body.html(html + '<input type="hidden" class="zolo-cfg" data-key="_idx" value="' + idx + '">');
            $overlay.show();

            var self = this;
            $('#zolo-modal-block-save').off('click').on('click', function() {
                var config = {};
                $('#zolo-modal-block-body .zolo-cfg').each(function() {
                    var $el = $(this);
                    var key = $el.data('key');
                    if (key === '_idx') return;
                    if ($el.is(':checkbox')) {
                        config[key] = $el.is(':checked');
                    } else {
                        config[key] = $el.val();
                    }
                });
                self.currentBlocks[idx].config = config;
                self.isDirty = true;
                self.renderBlocks();
                self.updateStatus();
                self.closeModal();
                self.toast('✅ Блок настроен');
            });
        },

        field: function(label, key, value, type) {
            type = type || 'text';
            return '<div class="zolo-field"><label>' + label + '</label><input type="' + type + '" class="zolo-cfg zolo-input" data-key="' + key + '" value="' + this.esc(value||'') + '"></div>';
        },
        fieldArea: function(label, key, value) {
            return '<div class="zolo-field"><label>' + label + '</label><textarea class="zolo-cfg zolo-input" data-key="' + key + '" rows="4">' + this.esc(value||'') + '</textarea></div>';
        },
        fieldCheck: function(label, key, value) {
            return '<div class="zolo-field"><label><input type="checkbox" class="zolo-cfg" data-key="' + key + '" ' + (value?'checked':'') + '> ' + label + '</label></div>';
        },

        // ── Save / Publish ──

        saveDraft: function() {
            if (!this.currentPageId) return;
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_save_blocks',
                nonce: zoloData.nonce,
                page_id: this.currentPageId,
                blocks: JSON.stringify(this.currentBlocks)
            }).done(function(resp) {
                if (!resp.success) { self.toast('❌ Ошибка сохранения'); return; }
                self.isDirty = false;
                self.updateStatus();
                self.toast('💾 Черновик сохранён');
            });
        },

        publishPage: function() {
            if (!this.currentPageId) return;
            var self = this;
            // save first
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
                    self.updateStatus();
                    self.toast('📢 Страница опубликована');
                    self.renderTree();
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
            if (!confirm('Удалить страницу "' + (this.getPage(pageId)||{}).name + '"?')) return;
            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_delete_page',
                nonce: zoloData.nonce,
                page_id: pageId
            }).done(function(resp) {
                if (!resp.success) return;
                self.pages = self.pages.filter(function(p) { return p.id !== pageId; });
                self.renderTree();
                self.updatePageCount();
                if (self.currentPageId === pageId) {
                    self.currentPageId = null;
                    $('#zolo-editor').hide();
                    $('#zolo-empty').show();
                }
                self.toast('🗑️ Страница удалена');
            });
        },

        // ── Page modal ──

        showPageModal: function(mode) {
            var isSub = mode === 'sub';
            $('#zolo-modal-page-title').text(isSub ? '➕ Новый подраздел' : '➕ Новый раздел');
            $('#zolo-modal-page-parent-field').toggle(isSub);

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

            $('#zolo-modal-page-name').val('');
            $('#zolo-modal-page-icon').val('📄');
            $('#zolo-modal-page-overlay').show();

            var self2 = this;
            $('#zolo-modal-page-save').off('click').on('click', function() {
                var name = $('#zolo-modal-page-name').val().trim();
                if (!name) { self2.toast('Введите название'); return; }
                var icon = $('#zolo-modal-page-icon').val().trim() || '📄';
                var parent = isSub ? $('#zolo-modal-page-parent').val() : '';
                self2.createPage(name, icon, parent);
                self2.closeModal();
            });
        },

        createPage: function(name, icon, parent) {
            // generate id from name
            var id = this.transliterate(name.toLowerCase().replace(/[^a-zа-яё0-9\s-]+/gi, '').replace(/\s+/g, '-').replace(/^-+|-+$/g, ''));
            if (!id) id = 'page-' + Date.now();

            var self = this;
            $.post(zoloData.ajaxUrl, {
                action: 'zolo_save_page',
                nonce: zoloData.nonce,
                id: id,
                name: name,
                icon: icon,
                parent: parent,
                order: self.pages.length,
                status: 'draft'
            }).done(function(resp) {
                if (!resp.success) return;
                self.pages = resp.data.pages;
                self.renderTree();
                self.updatePageCount();
                self.toast('➕ Страница создана');
                self.selectPage(id);
            });
        },

        transliterate: function(text) {
            var map = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'};
            return text.split('').map(function(c) { return map[c] || (c.match(/[a-z0-9-]/)?c:''); }).join('');
        },

        // ── Navigation ──

        switchTo: function(section) {
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

        // ── Media: Videos ──

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
                var html = '<table class="zolo-table"><thead><tr><th>Название</th><th>URL</th><th>Порядок</th><th></th></tr></thead><tbody>';
                videos.forEach(function(v) {
                    html += '<tr>' +
                        '<td><b>' + self.esc(v.title) + '</b></td>' +
                        '<td style="font-size:11px;color:#888;">' + self.esc(v.url || '—') + '</td>' +
                        '<td>' + v.order + '</td>' +
                        '<td><button class="zolo-btn zolo-btn-red" style="font-size:11px;padding:3px 8px;" onclick="zoloApp.deleteVideo(' + v.id + ')">🗑️</button></td>' +
                    '</tr>';
                });
                html += '</tbody></table>';
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

        // ── Media: Gallery ──

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
                var html = '<table class="zolo-table"><thead><tr><th></th><th>Название</th><th>Дата</th><th></th></tr></thead><tbody>';
                items.forEach(function(item) {
                    var thumb = item.thumb ? '<img src="' + self.esc(item.thumb) + '" style="width:50px;height:40px;object-fit:cover;border-radius:4px;">' : '📷';
                    html += '<tr>' +
                        '<td>' + thumb + '</td>' +
                        '<td><b>' + self.esc(item.title) + '</b></td>' +
                        '<td>' + self.esc(item.date) + '</td>' +
                        '<td><button class="zolo-btn zolo-btn-red" style="font-size:11px;padding:3px 8px;" onclick="zoloApp.deleteGalleryItem(' + item.id + ')">🗑️</button></td>' +
                    '</tr>';
                });
                html += '</tbody></table>';
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

        // ── Content list ──

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
                    var html = '<div class="zolo-section-title">' + label + ' <span class="zolo-badge">' + items.length + '</span></div>';
                    html += '<table class="zolo-table"><thead><tr><th>Заголовок</th><th>Статус</th><th>Дата</th><th>Автор</th><th></th></tr></thead><tbody>';
                    items.forEach(function(item) {
                        var status = item.status === 'publish' ? '<span style="color:#2d6a4f;">✅ Опубликовано</span>' : '<span style="color:#856404;">⏳ На модерации</span>';
                        var editUrl = zoloData.adminUrl + 'post.php?post=' + item.id + '&action=edit';
                        html += '<tr>' +
                            '<td><b>' + self.esc(item.title) + '</b></td>' +
                            '<td>' + status + '</td>' +
                            '<td>' + self.esc(item.date) + '</td>' +
                            '<td>' + self.esc(item.author) + '</td>' +
                            '<td><button class="zolo-btn" style="font-size:11px;padding:3px 8px;" onclick="window.open(\'' + editUrl + '\',\'_blank\')">✏️</button></td>' +
                        '</tr>';
                    });
                    html += '</tbody></table>';
                    $list.append($(html));
                    $list.append('<div style="margin-bottom:16px;"></div>');
                }
                if (!found) {
                    $list.html('<p style="color:#888;padding:12px;">Нет контента</p>');
                }
            });
        },

        // ── Settings ──

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

        renderRoles: function() {
            var $tbody = $('#zolo-roles-tbody');
            $tbody.empty();
            var self = this;
            this.roles.forEach(function(r) {
                var sections = (r.sections||[]).map(function(s) {
                    var p = self.getPage(s);
                    return p ? p.icon + ' ' + p.name : s;
                }).join(', ') || '—';
                $tbody.append('<tr>' +
                    '<td><b>' + r.icon + ' ' + self.esc(r.name) + '</b></td>' +
                    '<td>' + (r.user_count||0) + '</td>' +
                    '<td>' + self.esc(sections) + '</td>' +
                    '<td><button class="zolo-btn zolo-btn-blue zolo-role-edit" data-id="' + r.id + '" style="font-size:11px;padding:3px 8px;">✏️</button> ' +
                        '<button class="zolo-btn zolo-btn-red zolo-role-delete" data-id="' + r.id + '" style="font-size:11px;padding:3px 8px;">🗑️</button></td>' +
                '</tr>');
            });

            // Role edit buttons open section selection in modal
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
                    self.toast('🗑️ Роль удалена');
                });
            });
        },

        renderUsers: function() {
            var $tbody = $('#zolo-users-tbody');
            $tbody.empty();
            var self = this;
            this.users.forEach(function(u) {
                $tbody.append('<tr>' +
                    '<td><b>' + self.esc(u.name) + '</b></td>' +
                    '<td>' + self.esc(u.email) + '</td>' +
                    '<td>' + self.esc(u.role) + '</td>' +
                    '<td><span style="background:#d3f9d8;color:#2d6a4f;padding:2px 8px;border-radius:4px;font-size:11px;">Активен</span></td>' +
                    '<td><button class="zolo-btn" style="font-size:11px;padding:3px 8px;" onclick="window.open(\'' + zoloData.adminUrl + 'user-edit.php?user_id=' + u.id + '\',\'_blank\')">✏️</button></td>' +
                '</tr>');
            });
        },

        renderUsersStats: function() {
            var $stats = $('#zolo-users-stats');
            var roleCounts = {};
            var self = this;
            this.users.forEach(function(u) {
                u.role.split(', ').forEach(function(r) {
                    roleCounts[r] = (roleCounts[r] || 0) + 1;
                });
            });
            var colors = ['#d3f9d8','#e3f2fd','#fff3bf','#f3e5f5','#fce4ec'];
            var html = '';
            var idx = 0;
            for (var role in roleCounts) {
                if (!roleCounts.hasOwnProperty(role)) continue;
                var color = colors[idx % colors.length];
                html += '<div style="background:'+color+';border-radius:10px;padding:14px;text-align:center;">' +
                    '<div style="font-size:24px;font-weight:700;color:#1b4332;">'+roleCounts[role]+'</div>' +
                    '<div style="font-size:12px;color:#555;">'+self.esc(role)+'</div></div>';
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
            var html = '<p><strong>Доступ к разделам:</strong></p>';
            var self = this;
            this.pages.forEach(function(p) {
                var checked = (role.sections||[]).indexOf(p.id) !== -1 ? 'checked' : '';
                html += '<label style="display:block;margin:4px 0;"><input type="checkbox" class="zolo-role-section-cb" value="'+p.id+'" '+checked+'> '+p.icon+' '+self.esc(p.name)+'</label>';
            });
            html += '<input type="hidden" id="zolo-role-id-input" value="'+roleId+'">';
            $body.html(html);
            $overlay.show();

            $('#zolo-modal-block-save').off('click').on('click', function() {
                var sections = [];
                $('#zolo-modal-block-body .zolo-role-section-cb:checked').each(function() {
                    sections.push($(this).val());
                });
                var rid = $('#zolo-role-id-input').val();
                for (var i = 0; i < self.roles.length; i++) {
                    if (self.roles[i].id === rid) {
                        self.roles[i].sections = sections;
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

        showAddRoleModal: function() {
            $('#zolo-modal-role-overlay').show();
            var self = this;
            $('#zolo-modal-role-save').off('click').on('click', function() {
                var name = $('#zolo-modal-role-name').val().trim();
                var id = $('#zolo-modal-role-id').val().trim();
                var icon = $('#zolo-modal-role-icon').val().trim() || '👤';
                if (!name) { self.toast('Введите название'); return; }
                if (!id) id = self.transliterate(name.toLowerCase().replace(/\s+/g,'_'));
                var newRole = {id:id, name:name, icon:icon, sections:[], caps:{moderate_comments:false,upload_files:false}, user_count:0};
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

        // ── Toast ──

        toast: function(msg) {
            var $toast = $('#zolo-toast');
            $toast.text(msg).addClass('show');
            clearTimeout(this.toastTimer);
            this.toastTimer = setTimeout(function() {
                $toast.removeClass('show');
            }, 3000);
        },

        closeModal: function() {
            $('.zolo-modal-overlay').hide();
        },

        esc: function(str) {
            if (!str) return '';
            return $('<span>').text(str).html();
        },

        // ── Events ──

        bindEvents: function() {
            var self = this;

            // Modal close on overlay click
            $('.zolo-modal-overlay').on('click', function(e) {
                if ($(e.target).hasClass('zolo-modal-overlay')) {
                    self.closeModal();
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

            // Publish all link (can add a button in header)
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
