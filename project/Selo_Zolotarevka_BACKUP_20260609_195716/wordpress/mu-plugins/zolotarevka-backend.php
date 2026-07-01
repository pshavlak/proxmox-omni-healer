<?php
/**
 * Plugin Name: Zolotarevka Backend
 * Description: Админ-панель «Золотаревка» — конструктор сайта v2. Дерево страниц, блочный редактор, роли.
 * Version: 2.0.0
 *
 * Полная обратная совместимость: zolo_get_page_content(), zolo_get_site_settings() и др. сохранены.
 * Новая админ-панель — точная копия HTML-прототипа site-builder-v2.html.
 */

if (!defined('ABSPATH')) exit;

// ────────────────────────────────────────────────────────────
// 1. CPT, РОЛИ, REST, ВИДЕО, ФОРМА НОВОСТИ
// ────────────────────────────────────────────────────────────

final class Zolotarevka_Backend {
    const USER_SUBMISSION_POST_TYPE = 'bulletin_board';
    const USER_SUBMISSION_META_KEY = '_zolo_submission_source';
    const RATE_LIMIT_TRANSIENT_PREFIX = 'zolo_submit_rl_';
    const RATE_LIMIT_WINDOW_SECONDS = 600;
    const RATE_LIMIT_MAX_ATTEMPTS = 5;
    const MAX_TITLE_LENGTH = 140;
    const MAX_CONTENT_LENGTH = 5000;

    public static function init() {
        add_action('init', [__CLASS__, 'register_content_model']);
        add_action('init', [__CLASS__, 'register_roles']);
        add_action('init', [__CLASS__, 'apply_comment_moderation_defaults']);
        add_action('admin_post_nopriv_zolo_submit_news', [__CLASS__, 'handle_news_submission']);
        add_action('rest_api_init', [__CLASS__, 'register_rest_routes']);
        add_action('add_meta_boxes_zolo_video', [__CLASS__, 'add_video_meta_box']);
        add_action('save_post_zolo_video', [__CLASS__, 'save_video_meta'], 10, 2);
        // AJAX
        add_action('wp_ajax_zolo_get_data',         [__CLASS__, 'ajax_get_data']);
        add_action('wp_ajax_zolo_save_pages',        [__CLASS__, 'ajax_save_pages']);
        add_action('wp_ajax_zolo_save_page',         [__CLASS__, 'ajax_save_page']);
        add_action('wp_ajax_zolo_get_blocks',        [__CLASS__, 'ajax_get_blocks']);
        add_action('wp_ajax_zolo_save_blocks',       [__CLASS__, 'ajax_save_blocks']);
        add_action('wp_ajax_zolo_publish_page',      [__CLASS__, 'ajax_publish_page']);
        add_action('wp_ajax_zolo_publish_all',       [__CLASS__, 'ajax_publish_all']);
        add_action('wp_ajax_zolo_delete_page',       [__CLASS__, 'ajax_delete_page']);
        add_action('wp_ajax_zolo_save_roles',        [__CLASS__, 'ajax_save_roles']);
        add_action('wp_ajax_zolo_delete_role',       [__CLASS__, 'ajax_delete_role']);
        // Media & content AJAX
        add_action('wp_ajax_zolo_get_videos',        [__CLASS__, 'ajax_get_videos']);
        add_action('wp_ajax_zolo_save_video',        [__CLASS__, 'ajax_save_video']);
        add_action('wp_ajax_zolo_delete_video',      [__CLASS__, 'ajax_delete_video']);
        add_action('wp_ajax_zolo_get_gallery_items', [__CLASS__, 'ajax_get_gallery_items']);
        add_action('wp_ajax_zolo_save_gallery_item', [__CLASS__, 'ajax_save_gallery_item']);
        add_action('wp_ajax_zolo_delete_gallery_item',[__CLASS__, 'ajax_delete_gallery_item']);
        add_action('wp_ajax_zolo_save_site_settings',[__CLASS__, 'ajax_save_site_settings']);
        add_action('wp_ajax_zolo_get_recent_content',[__CLASS__, 'ajax_get_recent_content']);
    }

    // ── CPT ──

    public static function register_content_model() {
        $types = [
            'school_news'       => ['Школьные новости', 'Школьная новость', true],
            'kindergarten_news' => ['Новости детского сада', 'Новость детского сада', true],
            'farm_production'   => ['Продукция совхоза', 'Позиция продукции', false],
            'farm_vacancies'    => ['Вакансии совхоза', 'Вакансия', false],
            'sports_team'       => ['Спортивные команды', 'Команда', false],
            'sports_match'      => ['Матчи', 'Матч', false],
            'bulletin_board'    => ['Объявления', 'Объявление', true],
            'gallery'           => ['Галерея', 'Элемент галереи', true],
        ];
        foreach ($types as $type => $labels) {
            register_post_type($type, [
                'labels'          => ['name' => $labels[0], 'singular_name' => $labels[1]],
                'public'          => true, 'show_in_rest' => true, 'has_archive' => $labels[2],
                'menu_icon'       => 'dashicons-media-document',
                'supports'        => ['title','editor','author','thumbnail','excerpt','comments'],
                'capability_type' => 'post', 'map_meta_cap' => true, 'show_in_menu' => false,
            ]);
        }
        register_taxonomy('content_section',
            ['school_news','kindergarten_news','farm_production','farm_vacancies','sports_team','sports_match','bulletin_board','gallery'],
            ['label' => 'Раздел контента', 'public' => true, 'show_in_rest' => true, 'hierarchical' => true]);
        register_taxonomy('sports_kind', ['sports_team','sports_match'],
            ['label' => 'Вид спорта', 'public' => true, 'show_in_rest' => true, 'hierarchical' => true]);
        register_post_type('zolo_video', [
            'labels' => ['name'=>'Видеогалерея','singular_name'=>'Видео','add_new_item'=>'Добавить видео','edit_item'=>'Редактировать видео','new_item'=>'Новое видео','view_item'=>'Просмотреть видео','search_items'=>'Искать видео','not_found'=>'Видео не найдены','menu_name'=>'Видео'],
            'public' => true, 'show_in_rest' => true, 'rest_base' => 'videos', 'has_archive' => false,
            'menu_icon' => 'dashicons-video-alt3',
            'supports' => ['title','excerpt','thumbnail','page-attributes'],
            'capability_type' => 'post', 'map_meta_cap' => true, 'show_in_menu' => false,
        ]);
    }

    public static function add_video_meta_box() {
        add_meta_box('zolo_video_source', 'Ссылка на видео', [__CLASS__, 'render_video_meta_box'], 'zolo_video', 'normal', 'high');
    }
    public static function render_video_meta_box($post) {
        wp_nonce_field('zolo_video_save', 'zolo_video_nonce');
        $url = get_post_meta($post->ID, '_zolo_video_url', true);
        echo '<p><label for="zolo_video_url"><strong>URL Rutube или VK Video</strong></label><br>';
        echo '<input type="url" id="zolo_video_url" name="zolo_video_url" value="'.esc_attr($url).'" style="width:100%;max-width:800px;" placeholder="https://rutube.ru/video/..."></p>';
    }
    public static function save_video_meta($post_id, $post) {
        if (defined('DOING_AUTOSAVE')&&DOING_AUTOSAVE) return;
        if ($post->post_type!=='zolo_video') return;
        if (!isset($_POST['zolo_video_nonce'])||!wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['zolo_video_nonce'])),'zolo_video_save')) return;
        if (!current_user_can('edit_post',$post_id)) return;
        update_post_meta($post_id,'_zolo_video_url',isset($_POST['zolo_video_url'])?esc_url_raw(trim(wp_unslash($_POST['zolo_video_url']))):'');
    }

    // ── Roles ──

    public static function register_roles() {
        add_role('school_editor','Редактор школы',self::editor_caps(['school_news']));
        add_role('sports_editor','Редактор спорта',self::editor_caps(['sports_team','sports_match']));
        add_role('farm_editor','Редактор совхоза',self::editor_caps(['farm_production','farm_vacancies']));
        add_role('content_moderator','Модератор',self::moderator_caps());
        add_role('community_author','Автор материалов',['read'=>true,'edit_posts'=>true,'delete_posts'=>true,'upload_files'=>false]);
        foreach(['administrator','school_editor','sports_editor','farm_editor','content_moderator'] as $rn){
            $r=get_role($rn);if($r&&!$r->has_cap('zolo_edit_site_content'))$r->add_cap('zolo_edit_site_content');
        }
    }
    private static function editor_caps($pts){
        $c=['read'=>true,'edit_posts'=>true,'edit_published_posts'=>true,'publish_posts'=>true,'upload_files'=>true,'moderate_comments'=>true];
        foreach($pts as $pt){$c["edit_$pt"]=true;$c["publish_$pt"]=true;}return$c;
    }
    private static function moderator_caps(){
        return['read'=>true,'edit_posts'=>true,'edit_others_posts'=>true,'publish_posts'=>true,'moderate_comments'=>true,'edit_comment'=>true,'delete_comment'=>true];
    }
    public static function apply_comment_moderation_defaults(){
        update_option('comment_moderation','1');update_option('comment_previously_approved','0');update_option('comment_registration','0');
    }

    // ── News submit ──

    public static function handle_news_submission() {
        if(!isset($_POST['_wpnonce'])||!wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['_wpnonce'])),'zolo_submit_news'))wp_die('Неверный nonce',403);
        if(trim((string)wp_unslash($_POST['website']??''))!=='')wp_die('Подозрительная активность',400);
        $k=self::RATE_LIMIT_TRANSIENT_PREFIX.md5(self::get_ip().'|'.self::get_ua());
        if((int)get_transient($k)>=self::RATE_LIMIT_MAX_ATTEMPTS)wp_die('Слишком много попыток',429);
        set_transient($k,(int)get_transient($k)+1,self::RATE_LIMIT_WINDOW_SECONDS);
        $title=sanitize_text_field(wp_unslash($_POST['news_title']??''));
        $content=wp_kses_post(wp_unslash($_POST['news_text']??''));
        if($title===''||$content==='')wp_die('Заполните поля',400);
        if(mb_strlen($title)>self::MAX_TITLE_LENGTH||mb_strlen(wp_strip_all_tags($content))>self::MAX_CONTENT_LENGTH)wp_die('Слишком длинный текст',400);
        $id=wp_insert_post(['post_type'=>'bulletin_board','post_title'=>$title,'post_content'=>$content,'post_status'=>'pending','meta_input'=>[self::USER_SUBMISSION_META_KEY=>'form_submit_news','_zolo_submission_ip'=>self::get_ip(),'_zolo_submission_user_agent'=>self::get_ua()]],true);
        if(is_wp_error($id))wp_die('Ошибка: '.$id->get_error_message(),500);
        $ref=wp_get_referer();if(!$ref||!wp_validate_redirect($ref,false))$ref=home_url('/');
        wp_safe_redirect(add_query_arg('submitted','1',$ref));exit;
    }
    private static function get_ip(){return substr(sanitize_text_field(wp_unslash($_SERVER['REMOTE_ADDR']??'0.0.0.0')),0,64);}
    private static function get_ua(){return substr(sanitize_text_field(wp_unslash($_SERVER['HTTP_USER_AGENT']??'unknown')),0,255);}

    // ── Video helpers ──

    public static function get_video_embed_url($url){
        $url=trim((string)$url);if($url==='')return'';
        $h=strtolower((string)wp_parse_url($url,PHP_URL_HOST));
        $p=(string)wp_parse_url($url,PHP_URL_PATH);
        if(strpos($h,'rutube.ru')!==false){if(preg_match('~/(?:video|shorts)/([a-f0-9]+)/?~i',$p,$m))return'https://rutube.ru/play/embed/'.$m[1];if(strpos($url,'rutube.ru/play/embed/')!==false)return$url;}
        if(strpos($h,'vk.com')!==false||strpos($h,'vkvideo.ru')!==false){if(strpos($url,'video_ext.php')!==false)return$url;}
        return'';
    }
    public static function get_video_cards($limit=0){
        $q=new WP_Query(['post_type'=>'zolo_video','post_status'=>'publish','posts_per_page'=>$limit>0?$limit:-1,'orderby'=>['menu_order'=>'ASC','date'=>'DESC'],'no_found_rows'=>true]);
        $r=[];foreach($q->posts as$p){$u=(string)get_post_meta($p->ID,'_zolo_video_url',true);$r[]=['id'=>$p->ID,'title'=>get_the_title($p),'description'=>get_the_excerpt($p),'url'=>$u,'embed_url'=>self::get_video_embed_url($u),'order'=>(int)$p->menu_order,'thumb'=>get_the_post_thumbnail_url($p,'large')?:''];}
        return $r;
    }

    // ────────────────────────────────────────────────────────────
    // 2. НОВЫЕ ДАННЫЕ
    // ────────────────────────────────────────────────────────────

    public static function get_pages() {
        $data = get_option('zolo_site_pages');
        if ($data) return $data;
        // auto-migrate from legacy
        $legacy = ['home','school','kindergarten','farm','sports','village-life','media','news'];
        $icons  = ['home'=>'🏠','school'=>'📚','kindergarten'=>'🧸','farm'=>'🌾','sports'=>'⚽','village-life'=>'🏘️','media'=>'📸','news'=>'📰'];
        $names  = ['home'=>'Главная','school'=>'Школа','kindergarten'=>'Детский сад','farm'=>'Совхоз','sports'=>'Спорт','village-life'=>'Жизнь села','media'=>'Медиа','news'=>'Новости'];
        $pages  = [];
        foreach ($legacy as $slug) {
            $pages[] = [
                'id' => $slug, 'name' => $names[$slug], 'icon' => $icons[$slug], 'parent' => '',
                'order' => array_search($slug, $legacy), 'status' => 'published'
            ];
        }
        update_option('zolo_site_pages', $pages, false);
        return $pages;
    }

    public static function get_blocks_draft($page_id) {
        $opt = get_option("zolo_blocks_{$page_id}_draft");
        if ($opt) return $opt;
        return self::migrate_legacy_blocks($page_id, 'draft');
    }

    public static function get_blocks_live($page_id) {
        $opt = get_option("zolo_blocks_{$page_id}_live");
        if ($opt) return $opt;
        return self::migrate_legacy_blocks($page_id, 'live');
    }

    private static function migrate_legacy_blocks($page_id, $mode) {
        $legacy = get_option("zolo_page_{$page_id}_{$mode}", []);
        if (empty($legacy)) return self::default_blocks($page_id);
        $blocks = [];
        $title  = $legacy['hero_title'] ?? $legacy['page_title'] ?? '';
        if ($title) {
            $blocks[] = [
                'id' => "hero-{$page_id}", 'type' => 'hero', 'name' => '🧱 Hero / Баннер',
                'config' => [
                    'title'    => $title,
                    'subtitle' => $legacy['hero_subtitle'] ?? '',
                    'bg_image' => $legacy['hero_image'] ?? $legacy['page_image'] ?? '',
                    'btn_text' => $legacy['hero_btn_text'] ?? '',
                    'btn_url'  => $legacy['hero_btn_url'] ?? '',
                ],
            ];
        }
        if (!empty($legacy['documents']) && is_array($legacy['documents'])) {
            $blocks[] = [
                'id' => "docs-{$page_id}", 'type' => 'documents', 'name' => '📄 Документы',
                'config' => ['items' => $legacy['documents']],
            ];
        }
        update_option("zolo_blocks_{$page_id}_{$mode}", $blocks, false);
        return $blocks ?: self::default_blocks($page_id);
    }

    public static function default_blocks($page_id) {
        return [
            ['id'=>"hero-{$page_id}", 'type'=>'hero', 'name'=>'🧱 Hero / Баннер',
             'config'=>['title'=>'','subtitle'=>'','bg_image'=>'','btn_text'=>'','btn_url'=>'']],
        ];
    }

    public static function get_roles_data() {
        $data = get_option('zolo_roles_v2');
        if ($data) return $data;
        $default = [
            ['id'=>'school_editor','name'=>'Редактор школы','icon'=>'📚','sections'=>['school'],'caps'=>['moderate_comments'=>true,'upload_files'=>true],'user_count'=>0],
            ['id'=>'sports_editor','name'=>'Редактор спорта','icon'=>'⚽','sections'=>['sports'],'caps'=>['moderate_comments'=>true,'upload_files'=>true],'user_count'=>0],
            ['id'=>'farm_editor','name'=>'Редактор совхоза','icon'=>'🌾','sections'=>['farm'],'caps'=>['moderate_comments'=>true,'upload_files'=>true],'user_count'=>0],
            ['id'=>'content_moderator','name'=>'Модератор','icon'=>'🛡️','sections'=>[],'caps'=>['moderate_comments'=>true,'upload_files'=>true],'user_count'=>0],
            ['id'=>'community_author','name'=>'Автор','icon'=>'✏️','sections'=>[],'caps'=>['moderate_comments'=>false,'upload_files'=>false],'user_count'=>0],
        ];
        // count users per role
        foreach ($default as &$r) {
            $role = get_role($r['id']);
            if ($role) {
                $users = get_users(['role' => $r['id'], 'number' => 1, 'fields' => 'ID']);
                $r['user_count'] = count($users); // approximate with count_users
                $counts = count_users();
                foreach ($counts['avail_roles'] as $k => $c) {
                    if ($k === $r['id']) { $r['user_count'] = $c; break; }
                }
            }
        }
        update_option('zolo_roles_v2', $default, false);
        return $default;
    }

    // ────────────────────────────────────────────────────────────
    // 3. AJAX
    // ────────────────────────────────────────────────────────────

    public static function ajax_get_data() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $pages = self::get_pages();
        $roles = self::get_roles_data();
        $users = get_users(['number' => 50]);
        $users_data = [];
        foreach ($users as $u) {
            $users_data[] = [
                'id' => $u->ID, 'name' => $u->display_name, 'email' => $u->user_email,
                'role' => implode(', ', $u->roles), 'registered' => $u->user_registered,
            ];
        }
        $videos = self::get_video_cards();
        // gallery items
        $gq = new WP_Query(['post_type' => 'gallery', 'post_status' => 'publish', 'posts_per_page' => -1, 'no_found_rows' => true]);
        $gallery_items = [];
        foreach ($gq->posts as $p) {
            $gallery_items[] = [
                'id' => $p->ID, 'title' => get_the_title($p),
                'thumb' => get_the_post_thumbnail_url($p, 'medium') ?: '',
                'date' => get_the_date('d.m.Y', $p), 'link' => get_permalink($p),
            ];
        }
        $settings = zolo_get_site_settings();
        // recent content stats
        $cpts = ['school_news', 'kindergarten_news', 'farm_production', 'farm_vacancies', 'sports_team', 'sports_match', 'bulletin_board'];
        $recent_content = [];
        foreach ($cpts as $cpt) {
            $q = new WP_Query(['post_type' => $cpt, 'post_status' => ['publish', 'pending'], 'posts_per_page' => 5, 'no_found_rows' => true]);
            $items = [];
            foreach ($q->posts as $p) {
                $items[] = [
                    'id' => $p->ID, 'title' => get_the_title($p), 'status' => $p->post_status,
                    'date' => get_the_date('d.m.Y', $p), 'author' => get_the_author_meta('display_name', $p->post_author),
                ];
            }
            if (!empty($items)) $recent_content[$cpt] = $items;
        }
        wp_send_json_success(compact('pages', 'roles', 'users_data', 'videos', 'gallery_items', 'settings', 'recent_content'));
    }

    // ── Video AJAX ──

    public static function ajax_get_videos() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        wp_send_json_success(['videos' => self::get_video_cards()]);
    }

    public static function ajax_save_video() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $id = intval($_POST['id'] ?? 0);
        $title = sanitize_text_field(wp_unslash($_POST['title'] ?? ''));
        $url = esc_url_raw(trim(wp_unslash($_POST['video_url'] ?? '')));
        $excerpt = sanitize_textarea_field(wp_unslash($_POST['description'] ?? ''));

        if ($id > 0) {
            wp_update_post(['ID' => $id, 'post_title' => $title, 'post_excerpt' => $excerpt]);
            update_post_meta($id, '_zolo_video_url', $url);
        } else {
            $id = wp_insert_post([
                'post_type' => 'zolo_video', 'post_title' => $title,
                'post_excerpt' => $excerpt, 'post_status' => 'publish',
                'meta_input' => ['_zolo_video_url' => $url],
            ]);
        }
        if (is_wp_error($id)) wp_send_json_error($id->get_error_message());
        wp_send_json_success(['id' => $id]);
    }

    public static function ajax_delete_video() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $id = intval($_POST['id'] ?? 0);
        if ($id) wp_delete_post($id, true);
        wp_send_json_success();
    }

    // ── Gallery AJAX ──

    public static function ajax_get_gallery_items() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $q = new WP_Query(['post_type' => 'gallery', 'post_status' => 'publish', 'posts_per_page' => -1, 'orderby' => 'date', 'order' => 'DESC']);
        $items = [];
        foreach ($q->posts as $p) {
            $items[] = [
                'id' => $p->ID, 'title' => get_the_title($p),
                'thumb' => get_the_post_thumbnail_url($p, 'medium') ?: '',
                'date' => get_the_date('d.m.Y', $p),
                'link' => get_permalink($p),
            ];
        }
        wp_send_json_success(['items' => $items]);
    }

    public static function ajax_save_gallery_item() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $title = sanitize_text_field(wp_unslash($_POST['title'] ?? ''));
        $id = intval($_POST['id'] ?? 0);
        if ($id > 0) {
            wp_update_post(['ID' => $id, 'post_title' => $title]);
        } else {
            $id = wp_insert_post(['post_type' => 'gallery', 'post_title' => $title, 'post_status' => 'publish']);
        }
        if (is_wp_error($id)) wp_send_json_error($id->get_error_message());
        wp_send_json_success(['id' => $id]);
    }

    public static function ajax_delete_gallery_item() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $id = intval($_POST['id'] ?? 0);
        if ($id) wp_delete_post($id, true);
        wp_send_json_success();
    }

    // ── Settings AJAX ──

    public static function ajax_save_site_settings() {
        if (!current_user_can('manage_options')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $data = json_decode(wp_unslash($_POST['settings'] ?? '{}'), true);
        if (!is_array($data)) wp_send_json_error('Invalid');
        $clean = [];
        foreach ($data as $k => $v) $clean[sanitize_key($k)] = sanitize_text_field($v);
        update_option('zolo_site_settings', $clean, false);
        wp_send_json_success(['settings' => $clean]);
    }

    // ── Recent content AJAX ──

    public static function ajax_get_recent_content() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $cpts = ['school_news', 'kindergarten_news', 'farm_production', 'farm_vacancies', 'sports_team', 'sports_match', 'bulletin_board'];
        $result = [];
        foreach ($cpts as $cpt) {
            $q = new WP_Query(['post_type' => $cpt, 'post_status' => ['publish', 'pending'], 'posts_per_page' => 5, 'no_found_rows' => true]);
            $items = [];
            foreach ($q->posts as $p) {
                $items[] = [
                    'id' => $p->ID, 'title' => get_the_title($p), 'status' => $p->post_status,
                    'date' => get_the_date('d.m.Y', $p), 'author' => get_the_author_meta('display_name', $p->post_author),
                ];
            }
            if (!empty($items)) $result[$cpt] = $items;
        }
        wp_send_json_success(['content' => $result]);
    }

    public static function ajax_save_pages() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $pages = json_decode(wp_unslash($_POST['pages'] ?? '[]'), true);
        if (!is_array($pages)) wp_send_json_error('Invalid');
        $clean = [];
        foreach ($pages as $p) {
            $clean[] = [
                'id'     => sanitize_key($p['id'] ?? ''),
                'name'   => sanitize_text_field($p['name'] ?? ''),
                'icon'   => sanitize_text_field($p['icon'] ?? '📄'),
                'parent' => sanitize_key($p['parent'] ?? ''),
                'order'  => intval($p['order'] ?? 0),
                'status' => in_array($p['status'] ?? '', ['published','draft']) ? $p['status'] : 'draft',
            ];
        }
        update_option('zolo_site_pages', $clean, false);
        wp_send_json_success(['pages' => $clean]);
    }

    public static function ajax_save_page() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $pages = self::get_pages();
        $new = [
            'id'     => sanitize_key($_POST['id'] ?? ''),
            'name'   => sanitize_text_field($_POST['name'] ?? ''),
            'icon'   => sanitize_text_field($_POST['icon'] ?? '📄'),
            'parent' => sanitize_key($_POST['parent'] ?? ''),
            'order'  => intval($_POST['order'] ?? count($pages)),
            'status' => sanitize_key($_POST['status'] ?? 'draft'),
        ];
        if (!$new['id']) wp_send_json_error('No id');
        $found = false;
        foreach ($pages as &$p) {
            if ($p['id'] === $new['id']) { $p = $new; $found = true; break; }
        }
        if (!$found) $pages[] = $new;
        update_option('zolo_site_pages', $pages, false);
        wp_send_json_success(['pages' => $pages]);
    }

    public static function ajax_get_blocks() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $pid = sanitize_key($_POST['page_id'] ?? '');
        if (!$pid) wp_send_json_error('No page_id');
        $draft = self::get_blocks_draft($pid);
        $live  = self::get_blocks_live($pid);
        $has_draft = md5(serialize($draft)) !== md5(serialize($live));
        wp_send_json_success(['blocks' => $draft, 'has_draft' => $has_draft]);
    }

    public static function ajax_save_blocks() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $pid = sanitize_key($_POST['page_id'] ?? '');
        $blocks = json_decode(wp_unslash($_POST['blocks'] ?? '[]'), true);
        if (!$pid || !is_array($blocks)) wp_send_json_error('Invalid');
        $clean = [];
        foreach ($blocks as $b) {
            $clean[] = [
                'id'     => sanitize_key($b['id'] ?? uniqid('b')),
                'type'   => sanitize_key($b['type'] ?? 'text'),
                'name'   => sanitize_text_field($b['name'] ?? 'Блок'),
                'config' => self::sanitize_cfg($b['config'] ?? []),
            ];
        }
        update_option("zolo_blocks_{$pid}_draft", $clean, false);
        wp_send_json_success(['blocks' => $clean]);
    }

    public static function ajax_publish_page() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $pid = sanitize_key($_POST['page_id'] ?? '');
        if (!$pid) wp_send_json_error('No page_id');
        $draft = get_option("zolo_blocks_{$pid}_draft", []);
        update_option("zolo_blocks_{$pid}_live", $draft, false);
        // sync legacy for template compat
        $legacy = [];
        foreach ($draft as $b) {
            if (($b['type']??'') === 'hero' && !empty($b['config'])) {
                $c = $b['config'];
                if (!empty($c['title']))    $legacy['hero_title'] = $c['title'];
                if (!empty($c['subtitle'])) $legacy['hero_subtitle'] = $c['subtitle'];
                if (!empty($c['bg_image'])) $legacy['hero_image'] = $c['bg_image'];
                if (!empty($c['btn_text'])) $legacy['hero_btn_text'] = $c['btn_text'];
                if (!empty($c['btn_url']))  $legacy['hero_btn_url'] = $c['btn_url'];
            }
            if (($b['type']??'') === 'documents' && !empty($b['config']['items'])) {
                $legacy['documents'] = $b['config']['items'];
            }
        }
        $old = get_option("zolo_page_{$pid}_live", []);
        update_option("zolo_page_{$pid}_live", wp_parse_args($legacy, $old), false);
        wp_send_json_success(['status' => 'published']);
    }

    public static function ajax_publish_all() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $pages = self::get_pages();
        $count = 0;
        foreach ($pages as $p) {
            $d = get_option("zolo_blocks_{$p['id']}_draft", []);
            if (!empty($d)) { update_option("zolo_blocks_{$p['id']}_live", $d, false); $count++; }
        }
        wp_send_json_success(['message' => "Опубликовано: {$count}"]);
    }

    public static function ajax_delete_page() {
        if (!current_user_can('zolo_edit_site_content')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $pid = sanitize_key($_POST['page_id'] ?? '');
        if (!$pid) wp_send_json_error('No page_id');
        $pages = self::get_pages();
        $pages = array_values(array_filter($pages, fn($p) => $p['id'] !== $pid));
        update_option('zolo_site_pages', $pages, false);
        delete_option("zolo_blocks_{$pid}_draft");
        delete_option("zolo_blocks_{$pid}_live");
        wp_send_json_success(['message' => "{$pid} удалена"]);
    }

    public static function ajax_save_roles() {
        if (!current_user_can('manage_options')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $roles = json_decode(wp_unslash($_POST['roles'] ?? '[]'), true);
        if (!is_array($roles)) wp_send_json_error('Invalid');
        $clean = [];
        foreach ($roles as $r) {
            $sections = [];
            if (isset($r['sections']) && is_array($r['sections'])) {
                foreach ($r['sections'] as $s) $sections[] = sanitize_key($s);
            }
            $clean[] = [
                'id'       => sanitize_key($r['id'] ?? ''),
                'name'     => sanitize_text_field($r['name'] ?? ''),
                'icon'     => sanitize_text_field($r['icon'] ?? '👤'),
                'sections' => $sections,
                'caps'     => ['moderate_comments'=>!empty($r['caps']['moderate_comments']),'upload_files'=>!empty($r['caps']['upload_files'])],
                'user_count'=> intval($r['user_count'] ?? 0),
            ];
        }
        update_option('zolo_roles_v2', $clean, false);
        wp_send_json_success(['roles' => $clean]);
    }

    public static function ajax_delete_role() {
        if (!current_user_can('manage_options')) wp_send_json_error('Нет прав');
        check_ajax_referer('zolo_nonce', 'nonce');
        $rid = sanitize_key($_POST['role_id'] ?? '');
        if (!$rid) wp_send_json_error('No role_id');
        $roles = self::get_roles_data();
        $roles = array_values(array_filter($roles, fn($r) => $r['id'] !== $rid));
        update_option('zolo_roles_v2', $roles, false);
        wp_send_json_success(['roles' => $roles]);
    }

    private static function sanitize_cfg($cfg) {
        if (!is_array($cfg)) return [];
        $clean = [];
        foreach (['title','subtitle','bg_image','btn_text','btn_url','text','caption','alt','image_url','video_url','all_link_text','all_link_url','embed','placeholder','form_type'] as $k) {
            if (isset($cfg[$k])) $clean[$k] = $k === 'text' ? wp_kses_post($cfg[$k]) : sanitize_text_field($cfg[$k]);
        }
        $clean['auto_from_tree'] = !empty($cfg['auto_from_tree']);
        $clean['cols'] = isset($cfg['cols']) ? absint($cfg['cols']) : 0;
        foreach (['items','manual_items'] as $nk) {
            if (isset($cfg[$nk]) && is_array($cfg[$nk])) {
                $clean[$nk] = [];
                foreach ($cfg[$nk] as $item) {
                    if (is_array($item)) {
                        $ci = [];
                        foreach (['title','description','url','image_url','icon'] as $sk) $ci[$sk] = sanitize_text_field($item[$sk]??'');
                        $clean[$nk][] = $ci;
                    }
                }
            }
        }
        if (isset($cfg['headers']) && is_array($cfg['headers'])) $clean['headers'] = array_map('sanitize_text_field', $cfg['headers']);
        if (isset($cfg['rows']) && is_array($cfg['rows'])) {
            $clean['rows'] = [];
            foreach ($cfg['rows'] as $row) if (is_array($row)) $clean['rows'][] = array_map('sanitize_text_field', $row);
        }
        return $clean;
    }

    // ── REST ──

    public static function register_rest_routes() {
        register_rest_route('zolo/v1', '/content/(?P<type>[a-z_]+)', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'rest_content'],
            'permission_callback' => '__return_true',
            'args' => ['type'=>['required'=>true,'sanitize_callback'=>'sanitize_key'],'per_page'=>['default'=>10,'sanitize_callback'=>'absint']],
        ]);
        register_rest_route('zolo/v2', '/page/(?P<pid>[a-z_\-]+)/blocks', [
            'methods' => 'GET', 'callback' => function($r){return rest_ensure_response(['blocks'=>self::get_blocks_live($r->get_param('pid'))]);},
            'permission_callback' => '__return_true',
        ]);
    }

    public static function rest_content(WP_REST_Request $req) {
        $type = $req->get_param('type');
        $allowed = ['school_news','kindergarten_news','farm_production','farm_vacancies','sports_team','sports_match','bulletin_board','gallery'];
        if (!in_array($type,$allowed,true)) return new WP_Error('invalid','Unsupported',['status'=>400]);
        $q = new WP_Query(['post_type'=>$type,'post_status'=>'publish','posts_per_page'=>max(1,min(50,(int)$req->get_param('per_page'))),'orderby'=>'date','order'=>'DESC']);
        $items = [];
        foreach ($q->posts as $p) $items[] = ['id'=>$p->ID,'title'=>get_the_title($p),'excerpt'=>get_the_excerpt($p),'date'=>get_the_date('c',$p),'link'=>get_permalink($p)];
        return rest_ensure_response(['type'=>$type,'count'=>count($items),'items'=>$items]);
    }
}

// ────────────────────────────────────────────────────────────
// 4. СТАРЫЕ ФУНКЦИИ СОВМЕСТИМОСТИ
// ────────────────────────────────────────────────────────────

function zolo_site_settings_defaults() {
    return ['social_vk'=>'#','social_telegram'=>'#','social_ok'=>'#','social_rss'=>home_url('/feed'),'contact_email'=>'info@zolotarevka.ru','contact_phone'=>'','contact_address'=>'','site_tagline'=>'Неофициальный портал села','topbar_region'=>'Золотаревка, Россия','footer_copyright'=>'© 2026 Неофициальный портал села Золотаревка.'];
}
function zolo_get_site_settings() {
    return wp_parse_args((array)get_option('zolo_site_settings',[]), zolo_site_settings_defaults());
}
function zolo_page_content_defaults($slug) {
    $d = ['home'=>['hero_image'=>'','hero_title'=>'Добро пожаловать в Золотаревку!','hero_subtitle'=>'Неофициальный портал нашего села.','hero_btn_text'=>'Исследовать разделы →','hero_btn_url'=>'#bento','news_section_title'=>'📰 Последние новости','news_all_link_text'=>'Все новости →','suggest_title'=>'💡 Хотите предложить новость?','suggest_text'=>'','suggest_btn_text'=>'Предложить новость'],'school'=>['page_image'=>'','documents'=>[],'page_title'=>'📚 Школа','news_section_title'=>'📰 Новости школы','news_count'=>3,'comments_title'=>'💬 Комментарии'],'kindergarten'=>['page_image'=>'','documents'=>[],'page_title'=>'🧸 Детский сад','news_section_title'=>'📰 Жизнь групп','news_count'=>3,'gallery_title'=>'📸 Фотоотчеты'],'farm'=>['page_image'=>'','documents'=>[],'page_title'=>'🌾 Совхоз','products_title'=>'📦 Продукция','products_count'=>3,'vacancies_title'=>'💼 Вакансии','vacancies_count'=>4],'sports'=>['page_image'=>'','documents'=>[],'page_title'=>'⚽ Спорт','team_section_title'=>'⚽ Команда','team_subtitle'=>'Состав','team_count'=>6,'other_sections_title'=>'🏐 Другие секции','gallery_title'=>'📸 Фото'],'village-life'=>['page_image'=>'','documents'=>[],'page_title'=>'🏘️ Жизнь села','history_title'=>'📜 История','culture_title'=>'🎭 ДК','culture_events_title'=>'📅 Афиша','culture_circles_title'=>'🎨 Кружки','bulletin_title'=>'📋 Объявления'],'media'=>['page_image'=>'','documents'=>[],'page_title'=>'📸 Медиа','gallery_title'=>'Фотогалерея','gallery_description'=>'','video_title'=>'🎬 Видеогалерея','video_description'=>''],'news'=>['page_image'=>'','documents'=>[],'page_title'=>'📰 Новости','news_per_page'=>9,'suggest_title'=>'💡 Предложить новость','suggest_text'=>'','suggest_btn_text'=>'Предложить']];
    return $d[$slug] ?? [];
}
function zolo_get_page_content($slug){
    return wp_parse_args((array)get_option("zolo_page_{$slug}_live",[]), zolo_page_content_defaults($slug));
}
function zolo_get_page_content_draft($slug){
    return wp_parse_args((array)get_option("zolo_page_{$slug}_draft",[]), zolo_page_content_defaults($slug));
}
function zolo_has_draft_changes($slug){
    return md5(serialize(get_option("zolo_page_{$slug}_draft",[])))!==md5(serialize(get_option("zolo_page_{$slug}_live",[])));
}
function zolo_seed_default_content(){
    if(!get_option('zolo_site_settings'))update_option('zolo_site_settings',zolo_site_settings_defaults(),false);
    foreach(['home','school','kindergarten','farm','sports','village-life','media','news'] as $s){
        if(!get_option("zolo_page_{$s}_draft"))update_option("zolo_page_{$s}_draft",zolo_page_content_defaults($s),false);
        if(!get_option("zolo_page_{$s}_live"))update_option("zolo_page_{$s}_live",zolo_page_content_defaults($s),false);
    }
}

// ────────────────────────────────────────────────────────────
// 5. АДМИН-ПАНЕЛЬ — точная копия HTML-прототипа
// ────────────────────────────────────────────────────────────

final class Zolotarevka_Admin_Panel {
    public static function init() {
        add_action('admin_menu', [__CLASS__, 'add_menu'], 20);
        add_action('admin_enqueue_scripts', [__CLASS__, 'enqueue']);
        add_action('admin_init', 'zolo_seed_default_content');
        add_action('admin_init', [__CLASS__, 'handle_settings_save']);
        add_action('admin_post_zolo_preview_page', [__CLASS__, 'handle_preview']);
    }

    public static function add_menu() {
        remove_menu_page('zolotarevka');
        remove_menu_page('zolotarevka-v2');
        add_menu_page('Золотаревка', 'Золотаревка ⚙️', 'zolo_edit_site_content', 'zolotarevka-v2',
            [__CLASS__, 'render'], 'dashicons-admin-generic', 3);
        // скрываем подменю — всё в одном SPA
        add_submenu_page('zolotarevka-v2', 'Конструктор', 'Конструктор', 'zolo_edit_site_content', 'zolotarevka-v2', [__CLASS__, 'render']);
    }

    public static function enqueue($hook) {
        if (strpos($hook, 'zolotarevka-v2') === false) return;

        wp_enqueue_style('zolo-admin', false, [], '2.0.0');
        wp_add_inline_style('zolo-admin', file_get_contents(__DIR__ . '/zolotarevka-admin.css'));

        wp_enqueue_script('zolo-admin', false, ['jquery'], '2.0.0', true);
        wp_add_inline_script('zolo-admin', file_get_contents(__DIR__ . '/zolotarevka-admin.js'));

        wp_localize_script('zolo-admin', 'zoloData', [
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce'   => wp_create_nonce('zolo_nonce'),
            'adminUrl'=> admin_url(),
        ]);
    }

    public static function render() {
        ?>
        <div class="zolo-wrap">
            <div class="zolo-header">
                <h1>🗂️ Золотаревка ⚙️ — Конструктор сайта v2</h1>
                <p>Слева — структура сайта (дерево страниц). Справа — редактор выбранной страницы</p>
            </div>

            <div class="zolo-layout">
                <!-- LEFT -->
                <div class="zolo-left">
                    <div class="zolo-panel-header" style="cursor:default;">🗂️ Золотаревка <span class="zolo-badge">управление</span></div>
                    <div class="zolo-nav">
                        <button class="zolo-nav-btn zolo-nav-active" data-section="pages" onclick="zoloApp.switchTo('pages')">🗺️ Страницы сайта</button>
                        <button class="zolo-nav-btn" data-section="media" onclick="zoloApp.switchTo('media')">🖼️ Медиа-центр</button>
                        <button class="zolo-nav-btn" data-section="content" onclick="zoloApp.switchTo('content')">📰 Контент</button>
                        <button class="zolo-nav-btn" data-section="settings" onclick="zoloApp.switchTo('settings')">⚙️ Настройки</button>
                    </div>
                    <div id="zolo-sidebar-pages">
                        <div class="zolo-panel-actions">
                            <button class="zolo-btn zolo-btn-green" onclick="zoloApp.showPageModal('section')">➕ Раздел</button>
                            <button class="zolo-btn zolo-btn-blue" onclick="zoloApp.showPageModal('sub')">➕ Подраздел</button>
                        </div>
                        <div class="zolo-tree" id="zolo-tree"></div>
                    </div>
                    <div class="zolo-bottom-btn">
                        <button onclick="zoloApp.switchTo('users')" class="zolo-btn zolo-btn-purple" style="width:100%;">👥 Пользователи и роли</button>
                    </div>
                </div>

                <!-- RIGHT -->
                <div class="zolo-right">
                    <!-- Pages editor -->
                    <div id="zolo-editor-pages">
                        <div class="zolo-right-header">
                            <div class="zolo-page-indicator">
                                <span id="zolo-current-icon">🏠</span>
                                <span id="zolo-current-name">Главная</span>
                                <span class="zolo-status" id="zolo-current-status">✅ Опубликовано</span>
                            </div>
                            <div class="zolo-header-actions">
                                <button class="zolo-btn" onclick="zoloApp.previewPage()">👁️ Предпросмотр</button>
                                <button class="zolo-btn zolo-btn-green" onclick="zoloApp.saveDraft()">💾 Сохранить</button>
                                <button class="zolo-btn zolo-btn-dark" onclick="zoloApp.publishPage()">📢 Опубликовать</button>
                            </div>
                        </div>
                        <div class="zolo-empty" id="zolo-empty">
                            <div class="zolo-empty-icon">👈</div>
                            <p>Выберите страницу из дерева слева</p>
                        </div>
                        <div id="zolo-editor" style="display:none;">
                            <div class="zolo-blocks" id="zolo-blocks-list"></div>
                            <div class="zolo-add-block-bar">
                                <select id="zolo-block-type">
                                    <option value="">— Добавить блок —</option>
                                    <option value="hero">🧱 Hero / Баннер</option>
                                    <option value="text">📝 Текст</option>
                                    <option value="image">🖼️ Изображение</option>
                                    <option value="gallery">📸 Галерея</option>
                                    <option value="video">🎬 Видео (Rutube/VK)</option>
                                    <option value="table">📊 Таблица</option>
                                    <option value="cards">🏗️ Карточки / Плитки</option>
                                    <option value="documents">📄 Документы</option>
                                    <option value="form">📋 Форма</option>
                                    <option value="divider">➖ Разделитель</option>
                                </select>
                                <button class="zolo-btn zolo-btn-green" onclick="zoloApp.addBlock()">➕ Добавить</button>
                            </div>
                        </div>
                    </div>

                    <!-- Users editor -->
                    <div id="zolo-editor-users" style="display:none;">
                        <div class="zolo-right-header">
                            <div class="zolo-page-indicator">👥 Пользователи и роли <span class="zolo-status zolo-status-green" id="zolo-users-summary">загрузка...</span></div>
                            <div class="zolo-header-actions">
                                <button class="zolo-btn zolo-btn-green" onclick="zoloApp.showAddRoleModal()">➕ Добавить роль</button>
                            </div>
                        </div>
                        <div style="padding:16px;">
                            <div class="zolo-users-stats" id="zolo-users-stats"></div>
                            <div class="zolo-roles-section">
                                <div class="zolo-section-title">🎭 Роли</div>
                                <table class="zolo-table" id="zolo-roles-table">
                                    <thead><tr><th>Роль</th><th>Пользователей</th><th>Доступ к разделам</th><th></th></tr></thead>
                                    <tbody id="zolo-roles-tbody"></tbody>
                                </table>
                            </div>
                            <div class="zolo-users-section">
                                <div class="zolo-section-title">👤 Пользователи <input type="text" placeholder="Поиск..." id="zolo-user-search" class="zolo-search"></div>
                                <table class="zolo-table" id="zolo-users-table">
                                    <thead><tr><th>Имя</th><th>Email</th><th>Роль</th><th>Статус</th><th></th></tr></thead>
                                    <tbody id="zolo-users-tbody"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <!-- Media center -->
                    <div id="zolo-editor-media" style="display:none;">
                        <div class="zolo-right-header">
                            <div class="zolo-page-indicator">🖼️ Медиа-центр</div>
                            <div class="zolo-header-actions">
                                <button class="zolo-btn" onclick="window.open('<?php echo admin_url('upload.php'); ?>','_blank')">🗂️ Медиатека WP</button>
                            </div>
                        </div>
                        <div style="padding:16px;">
                            <div class="zolo-section-title">🎬 Видео (Rutube/VK)</div>
                            <div id="zolo-video-list" style="margin-bottom:20px;"></div>
                            <div style="background:#f8f9fa;padding:16px;border-radius:10px;margin-bottom:20px;">
                                <h3 style="margin:0 0 12px;font-size:14px;">➕ Добавить видео</h3>
                                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                                    <input type="text" id="zolo-video-title" class="zolo-input" placeholder="Название видео">
                                    <input type="url" id="zolo-video-url" class="zolo-input" placeholder="URL Rutube или VK Video">
                                </div>
                                <textarea id="zolo-video-desc" class="zolo-input" style="margin-top:10px;" placeholder="Описание (необязательно)"></textarea>
                                <button class="zolo-btn zolo-btn-green" style="margin-top:10px;" onclick="zoloApp.saveVideo()">💾 Добавить видео</button>
                            </div>
                            <div class="zolo-section-title">📸 Галерея</div>
                            <div id="zolo-gallery-list" style="margin-bottom:20px;"></div>
                            <div style="background:#f8f9fa;padding:16px;border-radius:10px;">
                                <h3 style="margin:0 0 12px;font-size:14px;">➕ Добавить в галерею</h3>
                                <input type="text" id="zolo-gallery-title" class="zolo-input" placeholder="Название элемента">
                                <button class="zolo-btn zolo-btn-green" style="margin-top:10px;" onclick="zoloApp.saveGalleryItem()">💾 Добавить</button>
                                <p style="font-size:12px;color:#888;margin-top:8px;">Изображение можно загрузить через медиатеку WP (<a href="<?php echo admin_url('upload.php'); ?>" target="_blank">открыть</a>), затем указать его в блоке страницы.</p>
                            </div>
                        </div>
                    </div>

                    <!-- Content -->
                    <div id="zolo-editor-content" style="display:none;">
                        <div class="zolo-right-header">
                            <div class="zolo-page-indicator">📰 Контент сайта</div>
                        </div>
                        <div style="padding:16px;">
                            <p>Управление записями и контентом сайта. Нажмите на заголовок для редактирования в WP.</p>
                            <div id="zolo-content-list"></div>
                        </div>
                    </div>

                    <!-- Settings -->
                    <div id="zolo-editor-settings" style="display:none;">
                        <div class="zolo-right-header">
                            <div class="zolo-page-indicator">⚙️ Настройки сайта</div>
                            <div class="zolo-header-actions">
                                <button class="zolo-btn zolo-btn-green" onclick="zoloApp.saveSettings()">💾 Сохранить</button>
                            </div>
                        </div>
                        <div style="padding:16px;">
                            <div id="zolo-settings-form"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal: page/section -->
        <div class="zolo-modal-overlay" id="zolo-modal-page-overlay">
            <div class="zolo-modal">
                <h2 id="zolo-modal-page-title">➕ Новый раздел</h2>
                <div class="zolo-field"><label>Название</label><input id="zolo-modal-page-name" class="zolo-input"></div>
                <div class="zolo-field"><label>Иконка (emoji)</label><input id="zolo-modal-page-icon" class="zolo-input" value="📄"></div>
                <div class="zolo-field" id="zolo-modal-page-parent-field">
                    <label>Родительский раздел</label>
                    <select id="zolo-modal-page-parent" class="zolo-input"></select>
                </div>
                <div class="zolo-modal-actions">
                    <button class="zolo-btn zolo-btn-green" id="zolo-modal-page-save">💾 Создать</button>
                    <button class="zolo-btn" onclick="zoloApp.closeModal()">Отмена</button>
                </div>
            </div>
        </div>

        <!-- Modal: block config -->
        <div class="zolo-modal-overlay" id="zolo-modal-block-overlay">
            <div class="zolo-modal zolo-modal-wide">
                <h2 id="zolo-modal-block-title">⚙️ Настройки блока</h2>
                <div id="zolo-modal-block-body"></div>
                <div class="zolo-modal-actions">
                    <button class="zolo-btn zolo-btn-green" id="zolo-modal-block-save">💾 Сохранить</button>
                    <button class="zolo-btn" onclick="zoloApp.closeModal()">Отмена</button>
                </div>
            </div>
        </div>

        <!-- Modal: add role -->
        <div class="zolo-modal-overlay" id="zolo-modal-role-overlay">
            <div class="zolo-modal">
                <h2>➕ Добавить роль</h2>
                <div class="zolo-field"><label>Название роли</label><input id="zolo-modal-role-name" class="zolo-input"></div>
                <div class="zolo-field"><label>ID (eng)</label><input id="zolo-modal-role-id" class="zolo-input"></div>
                <div class="zolo-field"><label>Иконка</label><input id="zolo-modal-role-icon" class="zolo-input" value="👤"></div>
                <div class="zolo-modal-actions">
                    <button class="zolo-btn zolo-btn-green" id="zolo-modal-role-save">➕ Добавить</button>
                    <button class="zolo-btn" onclick="zoloApp.closeModal()">Отмена</button>
                </div>
            </div>
        </div>

        <!-- Toast -->
        <div class="zolo-toast" id="zolo-toast"></div>

        <style><?php echo file_get_contents(__DIR__ . '/zolotarevka-admin.css'); ?></style>
        <script><?php echo file_get_contents(__DIR__ . '/zolotarevka-admin.js'); ?></script>
        <?php
    }

    public static function handle_settings_save() {
        if (empty($_POST['zolo_settings_save'])) return;
        if (!current_user_can('manage_options')) wp_die('Нет прав');
        check_admin_referer('zolo_settings_v2');
        $data = isset($_POST['zolo_s']) ? (array) $_POST['zolo_s'] : [];
        $clean = [];
        foreach ($data as $k => $v) $clean[sanitize_key($k)] = sanitize_text_field($v);
        update_option('zolo_site_settings', $clean, false);
        wp_redirect(add_query_arg(['page' => 'zolotarevka-settings', 'msg' => urlencode('✅ Настройки сохранены'), 'type' => 'success'], admin_url('admin.php')));
        exit;
    }

    public static function handle_preview() {
        if (!current_user_can('zolo_edit_site_content') || empty($_GET['page_id'])) wp_die('Нет прав');
        $pid = sanitize_key($_GET['page_id']);
        wp_redirect(home_url('/' . ($pid === 'home' ? '' : $pid . '/')));
        exit;
    }
}

add_action('plugins_loaded', function () {
    Zolotarevka_Backend::init();
    Zolotarevka_Admin_Panel::init();
});
