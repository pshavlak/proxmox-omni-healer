<?php
/**
 * Plugin Name: Zolotarevka MVP Backend
 * Description: P0 backend for CPTs, roles, moderation and frontend data endpoints.
 * Version: 0.1.0
 */

if (!defined('ABSPATH')) {
    exit;
}

final class Zolotarevka_MVP_Backend {
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
        add_action('admin_post_zolo_submit_news', [__CLASS__, 'handle_news_submission']);
        add_action('rest_api_init', [__CLASS__, 'register_rest_routes']);
    }

    public static function register_content_model() {
        $types = [
            'school_news' => ['Школьные новости', 'Школьная новость', true],
            'kindergarten_news' => ['Новости детского сада', 'Новость детского сада', true],
            'farm_production' => ['Продукция совхоза', 'Позиция продукции', false],
            'farm_vacancies' => ['Вакансии совхоза', 'Вакансия', false],
            'sports_team' => ['Спортивные команды', 'Команда', false],
            'sports_match' => ['Матчи', 'Матч', false],
            'bulletin_board' => ['Объявления', 'Объявление', true],
            'gallery' => ['Галерея', 'Элемент галереи', true],
        ];

        foreach ($types as $type => $labels) {
            register_post_type($type, [
                'labels' => [
                    'name' => $labels[0],
                    'singular_name' => $labels[1],
                ],
                'public' => true,
                'show_in_rest' => true,
                'has_archive' => $labels[2],
                'menu_icon' => 'dashicons-media-document',
                'supports' => ['title', 'editor', 'author', 'thumbnail', 'excerpt', 'comments'],
                'capability_type' => 'post',
                'map_meta_cap' => true,
            ]);
        }

        register_taxonomy('content_section', ['school_news', 'kindergarten_news', 'farm_production', 'farm_vacancies', 'sports_team', 'sports_match', 'bulletin_board', 'gallery'], [
            'label' => 'Раздел контента',
            'public' => true,
            'show_in_rest' => true,
            'hierarchical' => true,
        ]);

        register_taxonomy('sports_kind', ['sports_team', 'sports_match'], [
            'label' => 'Вид спорта',
            'public' => true,
            'show_in_rest' => true,
            'hierarchical' => true,
        ]);
    }

    public static function register_roles() {
        add_role('school_editor', 'Редактор школы', self::editor_caps(['school_news']));
        add_role('sports_editor', 'Редактор спорта', self::editor_caps(['sports_team', 'sports_match']));
        add_role('farm_editor', 'Редактор совхоза', self::editor_caps(['farm_production', 'farm_vacancies']));
        add_role('content_moderator', 'Модератор', self::moderator_caps());
        add_role('community_author', 'Автор пользовательских материалов', self::author_caps());
    }

    private static function editor_caps($post_types) {
        $caps = [
            'read' => true,
            'edit_posts' => true,
            'edit_published_posts' => true,
            'publish_posts' => true,
            'upload_files' => true,
            'moderate_comments' => true,
        ];

        foreach ($post_types as $post_type) {
            $caps['edit_' . $post_type] = true;
            $caps['publish_' . $post_type] = true;
        }

        return $caps;
    }

    private static function moderator_caps() {
        return [
            'read' => true,
            'edit_posts' => true,
            'edit_others_posts' => true,
            'publish_posts' => true,
            'moderate_comments' => true,
            'edit_comment' => true,
            'delete_comment' => true,
        ];
    }

    private static function author_caps() {
        return [
            'read' => true,
            'edit_posts' => true,
            'delete_posts' => true,
            'upload_files' => false,
        ];
    }

    public static function apply_comment_moderation_defaults() {
        update_option('comment_moderation', '1');
        update_option('comment_previously_approved', '0');
        update_option('comment_registration', '0');
    }

    public static function handle_news_submission() {
        if (!isset($_POST['_wpnonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['_wpnonce'])), 'zolo_submit_news')) {
            wp_die('Неверный nonce', 403);
        }

        // Honeypot field must stay empty in legitimate browser submissions.
        $honeypot = isset($_POST['website']) ? trim((string) wp_unslash($_POST['website'])) : '';
        if ($honeypot !== '') {
            wp_die('Подозрительная активность', 400);
        }

        if (!self::check_rate_limit()) {
            wp_die('Слишком много попыток. Повторите позже.', 429);
        }

        $title = isset($_POST['news_title']) ? sanitize_text_field(wp_unslash($_POST['news_title'])) : '';
        $content = isset($_POST['news_text']) ? wp_kses_post(wp_unslash($_POST['news_text'])) : '';

        if ($title === '' || $content === '') {
            wp_die('Заполните заголовок и текст новости', 400);
        }

        if (mb_strlen($title) > self::MAX_TITLE_LENGTH || mb_strlen(wp_strip_all_tags($content)) > self::MAX_CONTENT_LENGTH) {
            wp_die('Слишком длинный заголовок или текст новости', 400);
        }

        $post_id = wp_insert_post([
            'post_type' => self::USER_SUBMISSION_POST_TYPE,
            'post_title' => $title,
            'post_content' => $content,
            'post_status' => 'pending',
            'meta_input' => [
                self::USER_SUBMISSION_META_KEY => 'form_submit_news',
                '_zolo_submission_ip' => self::get_request_ip(),
                '_zolo_submission_user_agent' => self::get_request_user_agent(),
            ],
        ], true);

        if (is_wp_error($post_id)) {
            wp_die('Ошибка сохранения новости: ' . $post_id->get_error_message(), 500);
        }

        $redirect_target = wp_get_referer();
        if (!$redirect_target || !wp_validate_redirect($redirect_target, false)) {
            $redirect_target = home_url('/');
        }

        wp_safe_redirect(add_query_arg('submitted', '1', $redirect_target));
        exit;
    }

    private static function check_rate_limit() {
        $fingerprint = self::get_rate_limit_fingerprint();
        $key = self::RATE_LIMIT_TRANSIENT_PREFIX . md5($fingerprint);
        $attempts = (int) get_transient($key);

        if ($attempts >= self::RATE_LIMIT_MAX_ATTEMPTS) {
            return false;
        }

        set_transient($key, $attempts + 1, self::RATE_LIMIT_WINDOW_SECONDS);
        return true;
    }

    private static function get_rate_limit_fingerprint() {
        return self::get_request_ip() . '|' . self::get_request_user_agent();
    }

    private static function get_request_ip() {
        $ip = isset($_SERVER['REMOTE_ADDR']) ? sanitize_text_field(wp_unslash($_SERVER['REMOTE_ADDR'])) : '0.0.0.0';
        return substr($ip, 0, 64);
    }

    private static function get_request_user_agent() {
        $agent = isset($_SERVER['HTTP_USER_AGENT']) ? sanitize_text_field(wp_unslash($_SERVER['HTTP_USER_AGENT'])) : 'unknown';
        return substr($agent, 0, 255);
    }

    public static function register_rest_routes() {
        register_rest_route('zolo/v1', '/content/(?P<type>[a-z_]+)', [
            'methods' => 'GET',
            'callback' => [__CLASS__, 'rest_get_content'],
            'permission_callback' => '__return_true',
            'args' => [
                'type' => [
                    'required' => true,
                    'sanitize_callback' => 'sanitize_key',
                ],
                'per_page' => [
                    'default' => 10,
                    'sanitize_callback' => 'absint',
                ],
            ],
        ]);
    }

    public static function rest_get_content(WP_REST_Request $request) {
        $type = $request->get_param('type');
        $allowed = ['school_news', 'kindergarten_news', 'farm_production', 'farm_vacancies', 'sports_team', 'sports_match', 'bulletin_board', 'gallery'];

        if (!in_array($type, $allowed, true)) {
            return new WP_Error('invalid_type', 'Unsupported content type', ['status' => 400]);
        }

        $q = new WP_Query([
            'post_type' => $type,
            'post_status' => 'publish',
            'posts_per_page' => max(1, min(50, (int) $request->get_param('per_page'))),
            'orderby' => 'date',
            'order' => 'DESC',
        ]);

        $items = [];
        foreach ($q->posts as $post) {
            $items[] = [
                'id' => $post->ID,
                'title' => get_the_title($post),
                'excerpt' => get_the_excerpt($post),
                'date' => get_the_date('c', $post),
                'link' => get_permalink($post),
            ];
        }

        return rest_ensure_response([
            'type' => $type,
            'count' => count($items),
            'items' => $items,
        ]);
    }
}

Zolotarevka_MVP_Backend::init();
