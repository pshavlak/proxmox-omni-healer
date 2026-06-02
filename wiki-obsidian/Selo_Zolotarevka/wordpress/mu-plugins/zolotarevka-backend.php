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
        add_action('add_meta_boxes', [__CLASS__, 'add_squad_meta_box']);
        add_action('add_meta_boxes', [__CLASS__, 'add_standings_meta_box']);
        add_action('add_meta_boxes', [__CLASS__, 'add_calendar_meta_box']);
        add_action('save_post_sports_team', [__CLASS__, 'save_squad_meta'], 10, 2);
        add_action('save_post_sports_season', [__CLASS__, 'save_standings_meta'], 10, 2);
        add_action('save_post_sports_season', [__CLASS__, 'save_calendar_meta'], 10, 2);
        add_action('admin_enqueue_scripts', [__CLASS__, 'enqueue_admin_assets']);

        // Ajax handler for standings auto-calculate
        add_action('wp_ajax_zolo_calc_standings', [__CLASS__, 'ajax_calc_standings']);
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

        register_post_type('sports_season', [
            'labels' => [
                'name' => 'Сезоны',
                'singular_name' => 'Сезон',
            ],
            'public' => true,
            'show_in_rest' => true,
            'has_archive' => false,
            'menu_icon' => 'dashicons-calendar-alt',
            'supports' => ['title'],
            'capability_type' => 'post',
            'map_meta_cap' => true,
        ]);

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
        add_role('sports_editor', 'Редактор спорта', self::editor_caps(['sports_team', 'sports_match', 'sports_season']));
        add_role('farm_editor', 'Редактор совхоза', self::editor_caps(['farm_production', 'farm_vacancies']));
        add_role('content_moderator', 'Модератор', self::moderator_caps());
        add_role('community_author', 'Автор пользовательских материалов', self::author_caps());

        // Grant page editor capability to roles that need it
        $editor_roles = ['administrator', 'school_editor', 'sports_editor', 'farm_editor'];
        foreach ($editor_roles as $role_name) {
            $role = get_role($role_name);
            if ($role && !$role->has_cap('zolo_edit_site_content')) {
                $role->add_cap('zolo_edit_site_content');
            }
        }
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

    public static function add_standings_meta_box() {
        add_meta_box(
            'zolo_standings',
            'Турнирная таблица',
            [__CLASS__, 'render_standings_meta_box'],
            'sports_season',
            'normal',
            'high'
        );
    }

    public static function rest_get_seasons() {
        $q = new WP_Query([
            'post_type' => 'sports_season',
            'post_status' => 'publish',
            'posts_per_page' => 50,
            'orderby' => 'date',
            'order' => 'DESC',
        ]);

        $items = [];
        foreach ($q->posts as $post) {
            $items[] = [
                'id' => $post->ID,
                'title' => get_the_title($post),
            ];
        }

        return rest_ensure_response([
            'count' => count($items),
            'items' => $items,
        ]);
    }

    public static function rest_get_season(WP_REST_Request $request) {
        $post_id = (int) $request->get_param('id');
        $post = get_post($post_id);

        if (!$post || $post->post_type !== 'sports_season' || $post->post_status !== 'publish') {
            return new WP_Error('not_found', 'Season not found', ['status' => 404]);
        }

        return rest_ensure_response([
            'id' => $post->ID,
            'title' => get_the_title($post),
            'standings' => get_post_meta($post->ID, 'standings_data', true) ?: [],
        ]);
    }

    /* =========================================================
     * Calendar meta box for sports_season
     * ========================================================= */

    public static function add_calendar_meta_box() {
        add_meta_box(
            'zolo_calendar',
            'Календарь и результаты',
            [__CLASS__, 'render_calendar_meta_box'],
            'sports_season',
            'normal',
            'high'
        );
    }

    public static function render_calendar_meta_box($post) {
        wp_nonce_field('zolo_calendar_save', 'zolo_calendar_nonce');

        $data = get_post_meta($post->ID, 'calendar_data', true);
        if (!is_array($data)) {
            $data = [
                '1' => [
                    ['round' => 1, 'date' => '', 'm' => [['num' => 1, 'home' => '', 'away' => '', 'score_h' => '', 'score_a' => '', 'status' => 'scheduled']]],
                ],
                '2' => [
                    ['round' => 1, 'date' => '', 'm' => [['num' => 1, 'home' => '', 'away' => '', 'score_h' => '', 'score_a' => '', 'status' => 'scheduled']]],
                ],
            ];
        }

        $circles = [
            '1' => '1 круг',
            '2' => '2 круг',
        ];
        ?>
        <div class="zolo-calendar-wrap">
            <div class="zolo-circle-tabs">
                <?php foreach ($circles as $c_id => $c_label): ?>
                <div class="zolo-circle-tab <?php echo $c_id === '1' ? 'active' : ''; ?>" data-circle="<?php echo $c_id; ?>"><?php echo esc_html($c_label); ?></div>
                <?php endforeach; ?>
            </div>

            <?php foreach ($circles as $c_id => $c_label):
                $rounds = isset($data[$c_id]) ? (array) $data[$c_id] : [];
            ?>
            <div id="zolo-circle-panel-<?php echo $c_id; ?>" class="zolo-circle-panel <?php echo $c_id === '1' ? 'active' : ''; ?>" data-circle="<?php echo $c_id; ?>">
                <?php foreach ($rounds as $r_idx => $round):
                    $round_num = $round['round'] ?? ($r_idx + 1);
                    $date = $round['date'] ?? '';
                    $matches = isset($round['m']) ? (array) $round['m'] : [];
                ?>
                <div class="zolo-round-block" data-circle="<?php echo $c_id; ?>" data-round-idx="<?php echo $r_idx; ?>">
                    <div class="zolo-round-header">
                        <span class="zolo-round-title">Тур <span class="zolo-round-display"><?php echo (int) $round_num; ?></span></span>
                        <input type="hidden" name="zolo_calendar[<?php echo $c_id; ?>][<?php echo $r_idx; ?>][round]" value="<?php echo (int) $round_num; ?>">
                        <span class="zolo-date-label">Дата:</span>
                        <input type="text" name="zolo_calendar[<?php echo $c_id; ?>][<?php echo $r_idx; ?>][date]" value="<?php echo esc_attr($date); ?>" placeholder="напр. 18 апреля">
                        <button type="button" class="button zolo-remove-round-btn" style="margin-left:auto;">✕ Удалить тур</button>
                    </div>
                    <table class="zolo-matches-table">
                        <thead>
                            <tr>
                                <th class="zolo-col-num">#</th>
                                <th class="zolo-col-team">Хозяева</th>
                                <th class="zolo-col-vs"></th>
                                <th class="zolo-col-team">Гости</th>
                                <th class="zolo-col-score" colspan="2">Счёт</th>
                                <th class="zolo-col-status">Статус</th>
                                <th class="zolo-col-action"></th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($matches as $m_idx => $m):
                                $home = $m['home'] ?? '';
                                $away = $m['away'] ?? '';
                                $score_h = $m['score_h'] ?? '';
                                $score_a = $m['score_a'] ?? '';
                                $status = $m['status'] ?? 'scheduled';
                            ?>
                            <tr>
                                <td class="zolo-col-num"><?php echo $m_idx + 1; ?></td>
                                <td class="zolo-col-team"><input type="text" name="zolo_calendar[<?php echo $c_id; ?>][<?php echo $r_idx; ?>][m][<?php echo $m_idx; ?>][home]" value="<?php echo esc_attr($home); ?>" placeholder="Хозяева"></td>
                                <td class="zolo-col-vs">—</td>
                                <td class="zolo-col-team"><input type="text" name="zolo_calendar[<?php echo $c_id; ?>][<?php echo $r_idx; ?>][m][<?php echo $m_idx; ?>][away]" value="<?php echo esc_attr($away); ?>" placeholder="Гости"></td>
                                <td class="zolo-col-score"><input type="text" name="zolo_calendar[<?php echo $c_id; ?>][<?php echo $r_idx; ?>][m][<?php echo $m_idx; ?>][score_h]" value="<?php echo esc_attr($score_h); ?>" placeholder="–" size="3"></td>
                                <td class="zolo-col-score"><input type="text" name="zolo_calendar[<?php echo $c_id; ?>][<?php echo $r_idx; ?>][m][<?php echo $m_idx; ?>][score_a]" value="<?php echo esc_attr($score_a); ?>" placeholder="–" size="3"></td>
                                <td class="zolo-col-status">
                                    <select name="zolo_calendar[<?php echo $c_id; ?>][<?php echo $r_idx; ?>][m][<?php echo $m_idx; ?>][status]">
                                        <option value="scheduled" <?php selected($status, 'scheduled'); ?>>Запланирован</option>
                                        <option value="played" <?php selected($status, 'played'); ?>>Сыгран</option>
                                        <option value="postponed" <?php selected($status, 'postponed'); ?>>Перенесён</option>
                                    </select>
                                </td>
                                <td class="zolo-col-action"><button type="button" class="zolo-remove-match" title="Удалить матч">✕</button></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                    <div class="zolo-round-actions">
                        <button type="button" class="button zolo-add-match-btn">+ Добавить матч</button>
                    </div>
                </div>
                <?php endforeach; ?>
                <div class="zolo-calendar-actions">
                    <button type="button" class="button zolo-add-round-btn" data-circle="<?php echo $c_id; ?>">+ Добавить тур</button>
                </div>
            </div>
            <?php endforeach; ?>

            <div class="zolo-calendar-actions" style="margin-top:24px;">
                <button type="button" class="button button-primary" id="zolo-calc-standings">🧮 Авторассчитать турнирную таблицу из результатов</button>
                <div id="zolo-calc-result" class="zolo-calc-result"></div>
            </div>
        </div>
        <?php
    }

    public static function save_calendar_meta($post_id, $post) {
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
            return;
        }

        if (!isset($_POST['zolo_calendar_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['zolo_calendar_nonce'])), 'zolo_calendar_save')) {
            return;
        }

        if (!current_user_can('edit_post', $post_id)) {
            return;
        }

        if ($post->post_type !== 'sports_season') {
            return;
        }

        $raw = isset($_POST['zolo_calendar']) ? (array) $_POST['zolo_calendar'] : [];
        $clean = [];

        foreach ($raw as $circle => $rounds) {
            $clean[$circle] = [];
            $r_idx = 0;
            foreach ((array) $rounds as $round) {
                if (!is_array($round)) continue;
                $matches = isset($round['m']) ? (array) $round['m'] : [];
                $clean_m = [];
                foreach ($matches as $m) {
                    if (!is_array($m)) continue;
                    $clean_m[] = [
                        'home'    => sanitize_text_field($m['home'] ?? ''),
                        'away'    => sanitize_text_field($m['away'] ?? ''),
                        'score_h' => sanitize_text_field($m['score_h'] ?? ''),
                        'score_a' => sanitize_text_field($m['score_a'] ?? ''),
                        'status'  => in_array($m['status'] ?? '', ['scheduled', 'played', 'postponed'], true) ? $m['status'] : 'scheduled',
                    ];
                }
                $clean[$circle][] = [
                    'round' => (int) ($round['round'] ?? ($r_idx + 1)),
                    'date'  => sanitize_text_field($round['date'] ?? ''),
                    'm'     => $clean_m,
                ];
                $r_idx++;
                if ($r_idx > 50) break; // safety limit
            }
        }

        update_post_meta($post_id, 'calendar_data', $clean);
    }

    /* =========================================================
     * Extend standings meta box with GF/GA/GD columns
     * ========================================================= */

    public static function render_standings_meta_box($post) {
        wp_nonce_field('zolo_standings_save', 'zolo_standings_nonce');

        $data = get_post_meta($post->ID, 'standings_data', true);
        if (!is_array($data)) {
            $data = [];
        }
        ?>
        <style>
            #zolo-standings-table th, #zolo-standings-table td { vertical-align: middle; }
            #zolo-standings-table input[type="text"],
            #zolo-standings-table input[type="number"] { width: 100%; }
        </style>
        <table class="widefat striped" id="zolo-standings-table">
            <thead>
                <tr>
                    <th style="width:30px;">#</th>
                    <th>Команда</th>
                    <th style="width:50px;">И</th>
                    <th style="width:50px;">В</th>
                    <th style="width:50px;">Н</th>
                    <th style="width:50px;">П</th>
                    <th style="width:50px;">ЗМ</th>
                    <th style="width:50px;">ПМ</th>
                    <th style="width:40px;">±</th>
                    <th style="width:50px;">О</th>
                    <th style="width:40px;"></th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($data as $i => $row): ?>
                <tr>
                    <td><?php echo $i + 1; ?></td>
                    <td><input type="text" name="standings[<?php echo $i; ?>][team]" value="<?php echo esc_attr($row['team'] ?? ''); ?>"></td>
                    <td><input type="number" name="standings[<?php echo $i; ?>][gp]" value="<?php echo esc_attr($row['gp'] ?? '0'); ?>" min="0"></td>
                    <td><input type="number" name="standings[<?php echo $i; ?>][w]" value="<?php echo esc_attr($row['w'] ?? '0'); ?>" min="0"></td>
                    <td><input type="number" name="standings[<?php echo $i; ?>][d]" value="<?php echo esc_attr($row['d'] ?? '0'); ?>" min="0"></td>
                    <td><input type="number" name="standings[<?php echo $i; ?>][l]" value="<?php echo esc_attr($row['l'] ?? '0'); ?>" min="0"></td>
                    <td><input type="number" name="standings[<?php echo $i; ?>][gf]" value="<?php echo esc_attr($row['gf'] ?? '0'); ?>" min="0"></td>
                    <td><input type="number" name="standings[<?php echo $i; ?>][ga]" value="<?php echo esc_attr($row['ga'] ?? '0'); ?>" min="0"></td>
                    <td class="zolo-standings-gd <?php $gd_val = ($row['gf'] ?? 0) - ($row['ga'] ?? 0); echo $gd_val > 0 ? 'positive' : ($gd_val < 0 ? 'negative' : ''); ?>">
                        <?php $gd = ($row['gf'] ?? 0) - ($row['ga'] ?? 0); echo $gd > 0 ? '+' : ''; echo $gd; ?>
                    </td>
                    <td><input type="number" name="standings[<?php echo $i; ?>][pts]" value="<?php echo esc_attr($row['pts'] ?? '0'); ?>" min="0"></td>
                    <td><button type="button" class="button zolo-remove-row" style="background:#dc3545;color:#fff;border:none;cursor:pointer;">✕</button></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        <p>
            <button type="button" class="button button-primary" id="zolo-add-row">+ Добавить строку</button>
        </p>
        <p class="description">Турнирная таблица. Очки: победа — 3, ничья — 1, поражение — 0. ЗМ — забито, ПМ — пропущено, ± — разница. Первая строка подсвечивается на сайте как лидер.</p>
        <script>
        (function() {
            var tbody = document.querySelector('#zolo-standings-table tbody');
            var addBtn = document.getElementById('zolo-add-row');
            var idx = <?php echo count($data); ?>;

            addBtn.addEventListener('click', function() {
                var tr = document.createElement('tr');
                tr.innerHTML = [
                    '<td>' + (idx + 1) + '</td>',
                    '<td><input type="text" name="standings[' + idx + '][team]" value="" style="width:100%;"></td>',
                    '<td><input type="number" name="standings[' + idx + '][gp]" value="0" min="0" style="width:100%;"></td>',
                    '<td><input type="number" name="standings[' + idx + '][w]" value="0" min="0" style="width:100%;"></td>',
                    '<td><input type="number" name="standings[' + idx + '][d]" value="0" min="0" style="width:100%;"></td>',
                    '<td><input type="number" name="standings[' + idx + '][l]" value="0" min="0" style="width:100%;"></td>',
                    '<td><input type="number" name="standings[' + idx + '][gf]" value="0" min="0" style="width:100%;"></td>',
                    '<td><input type="number" name="standings[' + idx + '][ga]" value="0" min="0" style="width:100%;"></td>',
                    '<td class="zolo-standings-gd">0</td>',
                    '<td><input type="number" name="standings[' + idx + '][pts]" value="0" min="0" style="width:100%;"></td>',
                    '<td><button type="button" class="button zolo-remove-row" style="background:#dc3545;color:#fff;border:none;cursor:pointer;">✕</button></td>'
                ].join('');
                tbody.appendChild(tr);
                idx++;
                bindRemove();
            });

            function bindRemove() {
                tbody.querySelectorAll('.zolo-remove-row').forEach(function(btn) {
                    btn.removeEventListener('click', removeRow);
                    btn.addEventListener('click', removeRow);
                });
            }

            function removeRow(e) {
                var tr = e.target.closest('tr');
                if (tbody.querySelectorAll('tr').length > 1) {
                    tr.parentNode.removeChild(tr);
                    renumber();
                }
            }

            function renumber() {
                tbody.querySelectorAll('tr').forEach(function(tr, i) {
                    tr.cells[0].textContent = i + 1;
                });
            }

            bindRemove();
        })();
        </script>
        <?php
    }

    public static function save_standings_meta($post_id, $post) {
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
            return;
        }

        if (!isset($_POST['zolo_standings_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['zolo_standings_nonce'])), 'zolo_standings_save')) {
            return;
        }

        if (!current_user_can('edit_post', $post_id)) {
            return;
        }

        if ($post->post_type !== 'sports_season') {
            return;
        }

        $raw = isset($_POST['standings']) ? (array) $_POST['standings'] : [];
        $clean = [];
        foreach ($raw as $row) {
            $clean[] = [
                'team' => sanitize_text_field($row['team'] ?? ''),
                'gp'   => absint($row['gp'] ?? 0),
                'w'    => absint($row['w'] ?? 0),
                'd'    => absint($row['d'] ?? 0),
                'l'    => absint($row['l'] ?? 0),
                'gf'   => absint($row['gf'] ?? 0),
                'ga'   => absint($row['ga'] ?? 0),
                'pts'  => absint($row['pts'] ?? 0),
            ];
        }

        // Sort by pts desc, then GD desc, then GF desc
        usort($clean, function($a, $b) {
            if ($b['pts'] !== $a['pts']) return $b['pts'] - $a['pts'];
            $gd_a = $a['gf'] - $a['ga'];
            $gd_b = $b['gf'] - $b['ga'];
            if ($gd_b !== $gd_a) return $gd_b - $gd_a;
            return $b['gf'] - $a['gf'];
        });

        update_post_meta($post_id, 'standings_data', $clean);
    }

    /* =========================================================
     * Admin assets enqueue
     * ========================================================= */

    public static function enqueue_admin_assets($hook) {
        global $post;
        if ($hook !== 'post.php' && $hook !== 'post-new.php') return;
        if (!$post || $post->post_type !== 'sports_season') return;

        $theme_url = get_template_directory_uri();

        wp_enqueue_style(
            'zolo-admin-calendar',
            $theme_url . '/css/admin-calendar.css',
            [],
            '0.1.0'
        );

        wp_enqueue_script(
            'zolo-admin-calendar',
            $theme_url . '/js/admin-calendar.js',
            [],
            '0.1.0',
            true
        );
    }

    /* =========================================================
     * REST routes for calendar
     * ========================================================= */

    public static function register_rest_routes() {
        // Already registered routes stay; add calendar routes
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

        register_rest_route('zolo/v1', '/standings', [
            'methods' => 'GET',
            'callback' => [__CLASS__, 'rest_get_seasons'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route('zolo/v1', '/standings/(?P<id>\d+)', [
            'methods' => 'GET',
            'callback' => [__CLASS__, 'rest_get_season'],
            'permission_callback' => '__return_true',
            'args' => [
                'id' => [
                    'required' => true,
                    'sanitize_callback' => 'absint',
                ],
            ],
        ]);

        register_rest_route('zolo/v1', '/calendar/(?P<id>\d+)', [
            'methods' => 'GET',
            'callback' => [__CLASS__, 'rest_get_calendar'],
            'permission_callback' => '__return_true',
            'args' => [
                'id' => [
                    'required' => true,
                    'sanitize_callback' => 'absint',
                ],
            ],
        ]);
    }

    public static function rest_get_calendar(WP_REST_Request $request) {
        $post_id = (int) $request->get_param('id');
        $post = get_post($post_id);

        if (!$post || $post->post_type !== 'sports_season' || $post->post_status !== 'publish') {
            return new WP_Error('not_found', 'Calendar not found', ['status' => 404]);
        }

        return rest_ensure_response([
            'id' => $post->ID,
            'title' => get_the_title($post),
            'calendar' => get_post_meta($post->ID, 'calendar_data', true) ?: [],
        ]);
    }

    /* =========================================================
     * AJAX handler: auto-calculate standings from calendar results
     * ========================================================= */

    public static function ajax_calc_standings() {
        if (!current_user_can('edit_posts')) {
            wp_die('Доступ запрещён', 403);
        }

        $post_id = isset($_POST['post_id']) ? absint($_POST['post_id']) : 0;
        if (!$post_id) {
            wp_send_json_error(['message' => 'ID поста не указан']);
        }

        $calendar = get_post_meta($post_id, 'calendar_data', true);
        if (!is_array($calendar)) {
            wp_send_json_error(['message' => 'Календарь пуст. Сначала сохраните расписание.']);
        }

        $teams = [];

        foreach ($calendar as $circle => $rounds) {
            foreach ((array) $rounds as $round) {
                $matches = isset($round['m']) ? (array) $round['m'] : [];
                foreach ($matches as $m) {
                    $home = trim($m['home'] ?? '');
                    $away = trim($m['away'] ?? '');
                    $score_h = trim($m['score_h'] ?? '');
                    $score_a = trim($m['score_a'] ?? '');
                    $status = $m['status'] ?? 'scheduled';

                    if (!$home || !$away) continue;
                    if ($status !== 'played') continue;
                    if ($score_h === '' || $score_a === '') continue;
                    if (!is_numeric($score_h) || !is_numeric($score_a)) continue;

                    $sh = (int) $score_h;
                    $sa = (int) $score_a;

                    if (!isset($teams[$home])) {
                        $teams[$home] = ['team' => $home, 'gp' => 0, 'w' => 0, 'd' => 0, 'l' => 0, 'gf' => 0, 'ga' => 0, 'pts' => 0];
                    }
                    if (!isset($teams[$away])) {
                        $teams[$away] = ['team' => $away, 'gp' => 0, 'w' => 0, 'd' => 0, 'l' => 0, 'gf' => 0, 'ga' => 0, 'pts' => 0];
                    }

                    $teams[$home]['gp']++;
                    $teams[$home]['gf'] += $sh;
                    $teams[$home]['ga'] += $sa;

                    $teams[$away]['gp']++;
                    $teams[$away]['gf'] += $sa;
                    $teams[$away]['ga'] += $sh;

                    if ($sh > $sa) {
                        $teams[$home]['w']++;
                        $teams[$home]['pts'] += 3;
                        $teams[$away]['l']++;
                    } elseif ($sa > $sh) {
                        $teams[$away]['w']++;
                        $teams[$away]['pts'] += 3;
                        $teams[$home]['l']++;
                    } else {
                        $teams[$home]['d']++;
                        $teams[$home]['pts'] += 1;
                        $teams[$away]['d']++;
                        $teams[$away]['pts'] += 1;
                    }
                }
            }
        }

        if (empty($teams)) {
            wp_send_json_error(['message' => 'Нет сыгранных матчей с заполненными счётами.']);
        }

        $standings = array_values($teams);

        usort($standings, function($a, $b) {
            if ($b['pts'] !== $a['pts']) return $b['pts'] - $a['pts'];
            $gd_a = $a['gf'] - $a['ga'];
            $gd_b = $b['gf'] - $b['ga'];
            if ($gd_b !== $gd_a) return $gd_b - $gd_a;
            return $b['gf'] - $a['gf'];
        });

        update_post_meta($post_id, 'standings_data', $standings);

        wp_send_json_success([
            'message' => 'Турнирная таблица рассчитана: ' . count($standings) . ' команд',
            'standings' => $standings,
        ]);
    }

    /* =========================================================
     * Get calendar for frontend display (helper)
     * ========================================================= */

    public static function get_calendar_for_display($season_id) {
        $data = get_post_meta($season_id, 'calendar_data', true);
        if (!is_array($data)) return [];

        $output = [];
        foreach ($data as $circle => $rounds) {
            $output[$circle] = [];
            foreach ((array) $rounds as $r_idx => $round) {
                $matches = isset($round['m']) ? (array) $round['m'] : [];
                $output[$circle][] = [
                    'round'   => (int) ($round['round'] ?? ($r_idx + 1)),
                    'date'    => $round['date'] ?? '',
                    'matches' => $matches,
                ];
            }
        }

        return $output;
    }

    /* =========================================================
     * Get standings for frontend display (helper)
     * ========================================================= */

    public static function get_standings_for_display($season_id) {
        return get_post_meta($season_id, 'standings_data', true) ?: [];
    }

    /* =========================================================
     * Squad meta box for sports_team (номер, возраст, амплуа)
     * ========================================================= */

    public static function add_squad_meta_box() {
        add_meta_box(
            'zolo_squad',
            'Состав команды',
            [__CLASS__, 'render_squad_meta_box'],
            'sports_team',
            'normal',
            'high'
        );
    }

    public static function render_squad_meta_box($post) {
        wp_nonce_field('zolo_squad_save', 'zolo_squad_nonce');

        $number   = get_post_meta($post->ID, 'number', true);
        $age      = get_post_meta($post->ID, 'age', true);
        $position = get_the_excerpt($post);
        ?>
        <table class="form-table">
            <tbody>
                <tr>
                    <th scope="row"><label for="zolo_player_number">Номер</label></th>
                    <td>
                        <input type="text" id="zolo_player_number" name="zolo_player_number"
                               value="<?php echo esc_attr($number); ?>" class="regular-text" placeholder="напр. 10">
                        <p class="description">Игровой номер футболиста.</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="zolo_player_age">Возраст</label></th>
                    <td>
                        <input type="number" id="zolo_player_age" name="zolo_player_age"
                               value="<?php echo esc_attr($age); ?>" class="small-text" min="0" placeholder="25">
                        <p class="description">Возраст игрока (полных лет).</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="zolo_player_position">Амплуа</label></th>
                    <td>
                        <input type="text" id="zolo_player_position" name="zolo_player_position"
                               value="<?php echo esc_attr($position); ?>" class="regular-text" placeholder="напр. Нападающий">
                        <p class="description">Позиция / амплуа на поле. Сохраняется в отрывок (excerpt).</p>
                    </td>
                </tr>
            </tbody>
        </table>
        <?php
    }

    public static function save_squad_meta($post_id, $post) {
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
            return;
        }

        if (!isset($_POST['zolo_squad_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['zolo_squad_nonce'])), 'zolo_squad_save')) {
            return;
        }

        if (!current_user_can('edit_post', $post_id)) {
            return;
        }

        if ($post->post_type !== 'sports_team') {
            return;
        }

        // Save number
        if (isset($_POST['zolo_player_number'])) {
            update_post_meta($post_id, 'number', sanitize_text_field(wp_unslash($_POST['zolo_player_number'])));
        }

        // Save age
        if (isset($_POST['zolo_player_age'])) {
            update_post_meta($post_id, 'age', absint($_POST['zolo_player_age']));
        }

        // Save position as excerpt
        if (isset($_POST['zolo_player_position'])) {
            $position = sanitize_text_field(wp_unslash($_POST['zolo_player_position']));

            // Unhook to avoid infinite loop
            remove_action('save_post_sports_team', [__CLASS__, 'save_squad_meta'], 10);

            wp_update_post([
                'ID'           => $post_id,
                'post_excerpt' => $position,
            ]);

            add_action('save_post_sports_team', [__CLASS__, 'save_squad_meta'], 10, 2);
        }
    }
}

/* =========================================================
 * Settings helpers – page content defaults and accessors
 * ========================================================= */

function zolo_page_content_defaults($slug) {
    $defaults = [
        'home' => [
            'hero_title'    => 'Добро пожаловать в Золотаревку!',
            'hero_subtitle' => 'Неофициальный портал нашего села. Новости, события, спорт, история и многое другое.',
            'hero_btn_text' => 'Исследовать разделы →',
            'hero_btn_url'  => '#bento',
            'bento_section_title'    => 'Наши разделы',
            'bento_section_subtitle' => 'Быстрый доступ к ключевым разделам портала',
            'bento_cards' => [
                ['icon' => '📚', 'title' => 'Школа', 'text' => 'Новости классов, расписание автобуса, достижения учеников', 'url' => '/school/', 'gradient' => 'linear-gradient(135deg, #4a90d9, #357abd)'],
                ['icon' => '🧸', 'title' => 'Детский сад', 'text' => 'Жизнь групп, полезные советы, фотоотчеты с утренников', 'url' => '/kindergarten/', 'gradient' => 'linear-gradient(135deg, #f093fb, #f5576c)'],
                ['icon' => '🌾', 'title' => 'Совхоз', 'text' => 'История предприятия, вакансии, производимая продукция', 'url' => '/farm/', 'gradient' => 'linear-gradient(135deg, #43e97b, #38f9d7)'],
                ['icon' => '⚽', 'title' => 'Футбольная команда', 'text' => 'Состав, расписание матчей, турнирная таблица, фото с игр', 'url' => '/sports/', 'gradient' => 'linear-gradient(135deg, #fa709a, #fee140)'],
                ['icon' => '🏘️', 'title' => 'Жизнь села', 'text' => 'История, Дом Культуры, доска объявлений, выдающиеся земляки', 'url' => '/village-life/', 'gradient' => 'linear-gradient(135deg, #a18cd1, #fbc2eb)'],
                ['icon' => '📸', 'title' => 'Медиа', 'text' => 'Фото- и видеогалерея села, яркие моменты из жизни', 'url' => '/media/', 'gradient' => 'linear-gradient(135deg, #ffecd2, #fcb69f)'],
            ],
            'match_team_home' => 'ФК «Золотаревка»',
            'match_team_away' => 'ФК «Соседи»',
            'match_date'      => 'Суббота, 15:00',
            'match_location'  => 'Стадион «Центральный»',
            'match_active'    => true,
            'news_section_title' => '📰 Последние новости',
            'news_all_link_text' => 'Все новости →',
            'news_cpt_types'     => ['school_news', 'kindergarten_news', 'farm_production', 'sports_match', 'bulletin_board'],
            'news_count'         => 3,
            'suggest_title'   => '💡 Хотите предложить новость?',
            'suggest_text'    => 'Жители села могут присылать свои фото и истории. Лучшие публикации попадут на главную!',
            'suggest_btn_text' => 'Предложить новость',
        ],
        'school' => [
            'page_title'           => '📚 Школа села Золотаревка',
            'news_section_title'   => '📰 Новости школы',
            'news_count'           => 3,
            'bus_schedule_title'   => '🚌 Расписание школьного автобуса',
            'bus_schedule' => [
                ['route' => 'Золотаревка — Школа (ул. Центральная)', 'morning' => '07:30', 'afternoon' => '13:00'],
                ['route' => 'Золотаревка — Школа (ул. Садовая)', 'morning' => '07:45', 'afternoon' => '13:15'],
                ['route' => 'Золотаревка — Школа (ул. Полевая)', 'morning' => '07:50', 'afternoon' => '13:10'],
                ['route' => 'Золотаревка — Школа (д. Сосновка)', 'morning' => '07:15', 'afternoon' => '13:30'],
            ],
            'achievements_title' => '🏆 Достижения учеников',
            'achievements' => [
                ['icon' => '🥇', 'title' => 'Районная олимпиада по математике', 'text' => 'Иванов Петр, 9 класс — 1 место. Апрель 2026.'],
                ['icon' => '🥇', 'title' => 'Соревнования по легкой атлетике', 'text' => 'Команда школы — 2 место в эстафете. Март 2026.'],
                ['icon' => '🥇', 'title' => 'Конкурс чтецов «Родное слово»', 'text' => 'Сидорова Анна, 7 класс — 1 место. Февраль 2026.'],
            ],
            'comments_enabled' => true,
            'comments_title'   => '💬 Комментарии',
        ],
        'kindergarten' => [
            'page_title'         => '🧸 Детский сад «Колосок»',
            'news_section_title' => '📰 Жизнь групп',
            'news_count'         => 3,
            'parenting_tips_title' => '👪 Полезные советы родителям',
            'parenting_tips' => [
                ['icon' => '📖', 'title' => 'Как привить любовь к чтению', 'text' => 'Читайте вместе с ребенком каждый день по 15-20 минут, обсуждайте прочитанное, задавайте вопросы.'],
                ['icon' => '🥗', 'title' => 'Здоровое питание', 'text' => 'Включайте в рацион больше овощей и фруктов. Ограничьте сладости и газированные напитки.'],
                ['icon' => '🎨', 'title' => 'Развитие творчества', 'text' => 'Рисование, лепка, аппликация — отличные способы развить мелкую моторику и воображение.'],
            ],
            'gallery_title' => '📸 Фотоотчеты',
            'gallery_count' => 6,
        ],
        'farm' => [
            'page_title'    => '🌾 Совхоз «Золотаревский»',
            'history_title' => '📜 История предприятия',
            'history_text'  => "Совхоз «Золотаревский» был основан в 1960 году. За более чем 60 лет своей истории предприятие прошло славный путь от небольшого хозяйства до одного из ведущих сельскохозяйственных производителей района.\n\nСегодня совхоз специализируется на выращивании зерновых культур, производстве молока и мяса. На предприятии трудятся более 200 человек, многие из которых — династиями.",
            'pride_title' => '⭐ Гордость села',
            'pride_people' => [
                ['icon' => '👨‍🌾', 'name' => 'Иван Петрович Смирнов', 'role' => 'Комбайнер, ветеран труда', 'desc' => 'Более 40 лет работает в совхозе. Неоднократный победитель районных соревнований по уборке урожая.'],
                ['icon' => '👩‍🌾', 'name' => 'Анна Васильевна Кузнецова', 'role' => 'Доярка, передовик производства', 'desc' => 'Лучшая доярка района 2024 года. Достигла рекордных надоев молока.'],
                ['icon' => '🚜', 'name' => 'Николай Сергеевич Орлов', 'role' => 'Тракторист, заслуженный работник', 'desc' => 'Награжден почетной грамотой Министерства сельского хозяйства за многолетний добросовестный труд.'],
            ],
            'products_title'  => '📦 Производимая продукция',
            'products_count'  => 10,
            'vacancies_title' => '💼 Вакансии',
            'vacancies_count' => 10,
            'contacts_title'  => '📞 Контакты',
            'contacts' => [
                ['title' => 'Адрес', 'text' => 'с. Золотаревка, ул. Совхозная, 1', 'icon' => '📍'],
                ['title' => 'Телефон', 'text' => '8 (999) 123-45-67', 'icon' => '📞'],
                ['title' => 'Email', 'text' => 'sovhoz@zolotarevka.ru', 'icon' => '✉️'],
            ],
        ],
        'sports' => [
            'page_title'           => '⚽ Спорт в Золотаревке',
            'team_section_title'   => 'Футбольная команда «Золотаревка»',
            'team_subtitle'        => 'Состав команды',
            'team_count'           => 20,
            'other_sections_title' => '🏅 Другие секции',
            'other_sections' => [
                ['icon' => '🏐', 'title' => 'Волейбол', 'text' => 'Тренировки по вторникам и четвергам в 18:00 в спортзале школы. Тренер: Сергей Иванович.'],
                ['icon' => '♟️', 'title' => 'Шахматы', 'text' => 'Кружок работает в Доме Культуры по средам и пятницам в 17:00. Все возрасты приветствуются.'],
                ['icon' => '🏃', 'title' => 'Легкая атлетика', 'text' => 'Тренировки на стадионе «Центральный» ежедневно в 07:00 утра. Присоединяйтесь!'],
            ],
            'gallery_title' => '📸 Фото с игр',
            'gallery_count' => 6,
        ],
        'village-life' => [
            'page_title'  => '🏘️ Жизнь села Золотаревка',
            'history_title' => '📜 История села',
            'history_text'  => "Село Золотаревка было основано в середине XIX века переселенцами из центральных губерний России. Название село получило благодаря живописным золотистым полям пшеницы, которые окружают его со всех сторон.\n\nВ разные годы Золотаревка была центром сельсовета, здесь располагалась усадьба помещика, а после революции — коллективное хозяйство. Сегодня село продолжает развиваться, сохраняя свои традиции и самобытность.",
            'residents_title' => '⭐ Выдающиеся земляки',
            'notable_residents' => [
                ['icon' => '🎖️', 'name' => 'Иван Алексеевич Новиков', 'role' => 'Герой Социалистического Труда', 'desc' => 'Уроженец села, награжден за выдающиеся достижения в сельском хозяйстве.'],
                ['icon' => '📖', 'name' => 'Мария Петровна Соколова', 'role' => 'Заслуженный учитель РФ', 'desc' => 'Более 50 лет проработала в школе села, воспитала не одно поколение золотаревцев.'],
                ['icon' => '🎭', 'name' => 'Николай Дмитриевич Белов', 'role' => 'Художественный руководитель ДК', 'desc' => 'Основал народный хор, который выступал на областных сценах.'],
            ],
            'culture_title'       => '🎭 Дом Культуры',
            'culture_description' => 'Дом Культуры села Золотаревка — центр культурной жизни. Здесь проходят праздники, концерты, работают кружки и секции для детей и взрослых.',
            'culture_events_title' => '📅 Афиша мероприятий',
            'culture_events' => [
                ['date' => '1 июня 2026', 'event' => 'День защиты детей — праздничный концерт', 'time' => '11:00'],
                ['date' => '12 июня 2026', 'event' => 'День России — гуляния на площади', 'time' => '14:00'],
                ['date' => '20 июня 2026', 'event' => 'Выставка местных художников и мастеров', 'time' => '16:00'],
            ],
            'culture_circles_title' => '🎨 Кружки и секции',
            'culture_circles' => [
                ['icon' => '🎤', 'title' => 'Вокальный кружок', 'text' => 'Занятия по вторникам и четвергам в 17:00. Руководитель: Белов Н.Д.'],
                ['icon' => '💃', 'title' => 'Танцевальный кружок', 'text' => 'Занятия по понедельникам, средам и пятницам в 18:00.'],
                ['icon' => '🎨', 'title' => 'Изостудия', 'text' => 'Рисование для детей и взрослых. Суббота в 14:00.'],
                ['icon' => '🧶', 'title' => 'Рукоделие', 'text' => 'Вязание, вышивка, лоскутное шитье. Среда и пятница в 15:00.'],
            ],
            'bulletin_title'       => '📋 Доска объявлений',
            'bulletin_description' => 'Куплю, продам, услуги местных мастеров.',
            'bulletin_count'       => 10,
        ],
        'media' => [
            'page_title'        => '📸 Медиа',
            'gallery_title'     => 'Фотогалерея села',
            'gallery_description' => 'Яркие моменты из жизни Золотаревки. Нажмите на фото для просмотра.',
            'gallery_count'     => 12,
            'video_title'       => '🎬 Видеогалерея',
            'video_description' => 'Видеозаписи мероприятий и событий села.',
            'video_offset'      => 12,
            'video_count'       => 3,
        ],
        'news' => [
            'page_title'      => '📰 Новости села',
            'news_per_page'   => 9,
            'suggest_title'   => '💡 Хотите предложить новость?',
            'suggest_text'    => 'Жители села могут присылать свои фото и истории. Лучшие публикации попадут на главную!',
            'suggest_btn_text' => 'Предложить новость',
        ],
    ];

    return isset($defaults[$slug]) ? $defaults[$slug] : [];
}

function zolo_site_settings_defaults() {
    return [
        'social_vk'       => '#',
        'social_telegram' => '#',
        'social_ok'       => '#',
        'social_rss'      => home_url('/feed'),
        'contact_email'   => 'info@zolotarevka.ru',
        'contact_phone'   => '',
        'contact_address' => '',
        'site_tagline'    => 'Неофициальный портал села',
        'topbar_region'   => 'Золотаревка, Россия',
        'footer_copyright' => '© 2026 Неофициальный портал села Золотаревка. Сделано с ❤️ для земляков.',
        'footer_columns' => [
            ['title' => '🌾 Золотаревка', 'links' => [
                ['label' => 'Главная', 'url' => '/'],
                ['label' => 'Новости', 'url' => '/news/'],
                ['label' => 'Медиа', 'url' => '/media/'],
            ]],
            ['title' => 'Организации', 'links' => [
                ['label' => 'Школа', 'url' => '/school/'],
                ['label' => 'Детский сад', 'url' => '/kindergarten/'],
                ['label' => 'Совхоз', 'url' => '/farm/'],
            ]],
            ['title' => 'Активности', 'links' => [
                ['label' => 'Спорт', 'url' => '/sports/'],
                ['label' => 'Жизнь села', 'url' => '/village-life/'],
                ['label' => 'Доска объявлений', 'url' => '/village-life/#bulletin'],
            ]],
            ['title' => 'Контакты', 'links' => [
                ['label' => 'Предложить новость', 'url' => '#', 'modal' => 'suggestModal'],
                ['label' => 'info@zolotarevka.ru', 'url' => 'mailto:info@zolotarevka.ru'],
            ]],
        ],
    ];
}

function zolo_get_site_settings() {
    $defaults = zolo_site_settings_defaults();
    $saved = get_option('zolo_site_settings', []);
    return wp_parse_args($saved, $defaults);
}

function zolo_get_page_content($slug) {
    $defaults = zolo_page_content_defaults($slug);
    $saved = get_option("zolo_page_{$slug}_live", []);
    return wp_parse_args($saved, $defaults);
}

function zolo_get_page_content_draft($slug) {
    $defaults = zolo_page_content_defaults($slug);
    $saved = get_option("zolo_page_{$slug}_draft", []);
    return wp_parse_args($saved, $defaults);
}

function zolo_save_page_content_draft($slug, $data) {
    $clean = zolo_sanitize_page_content($slug, $data);
    update_option("zolo_page_{$slug}_draft", $clean, false);
}

function zolo_publish_page_content($slug) {
    $draft = get_option("zolo_page_{$slug}_draft", []);
    update_option("zolo_page_{$slug}_live", $draft, false);
}

function zolo_publish_all() {
    $pages = ['home', 'school', 'kindergarten', 'farm', 'sports', 'village-life', 'media', 'news'];
    foreach ($pages as $slug) {
        zolo_publish_page_content($slug);
    }
}

function zolo_has_draft_changes($slug) {
    $draft = get_option("zolo_page_{$slug}_draft", []);
    $live  = get_option("zolo_page_{$slug}_live", []);
    return md5(serialize($draft)) !== md5(serialize($live));
}

function zolo_sanitize_page_content($slug, $data) {
    if (!is_array($data)) return [];
    $clean = [];

    // Fields that should preserve newlines (textarea fields)
    $textarea_fields = ['history_text', 'culture_description', 'bulletin_description'];

    foreach ($data as $key => $value) {
        if (is_array($value)) {
            $clean[$key] = zolo_sanitize_page_content($slug . '_' . $key, $value);
        } elseif (is_string($value)) {
            if (in_array($key, $textarea_fields, true)) {
                $clean[$key] = sanitize_textarea_field($value);
            } else {
                $clean[$key] = sanitize_text_field($value);
            }
        } elseif (is_bool($value)) {
            $clean[$key] = (bool) $value;
        } elseif (is_int($value)) {
            $clean[$key] = absint($value);
        } else {
            $clean[$key] = sanitize_text_field((string) $value);
        }
    }
    return $clean;
}

function zolo_seed_default_content() {
    $version = get_option('zolo_settings_version', '');
    if ($version === '1.0.0') return;

    $pages = ['home', 'school', 'kindergarten', 'farm', 'sports', 'village-life', 'media', 'news'];
    foreach ($pages as $slug) {
        $defaults = zolo_page_content_defaults($slug);
        if (!get_option("zolo_page_{$slug}_live")) {
            update_option("zolo_page_{$slug}_live", $defaults, false);
        }
        if (!get_option("zolo_page_{$slug}_draft")) {
            update_option("zolo_page_{$slug}_draft", $defaults, false);
        }
    }
    if (!get_option('zolo_site_settings')) {
        update_option('zolo_site_settings', zolo_site_settings_defaults(), true);
    }
    update_option('zolo_settings_version', '1.0.0', false);
}

/* =========================================================
 * Settings admin pages
 * ========================================================= */

final class Zolotarevka_MVP_Settings {
    const CAP = 'zolo_edit_site_content';

    public static function init() {
        add_action('admin_menu', [__CLASS__, 'register_admin_menu']);
        add_action('admin_init', [__CLASS__, 'register_settings']);
        add_action('admin_init', [__CLASS__, 'handle_save_page_content']);
        add_action('admin_init', [__CLASS__, 'handle_publish_all']);
        add_action('admin_init', [__CLASS__, 'handle_reset_page']);
        add_action('admin_init', 'zolo_seed_default_content');
    }

    public static function register_admin_menu() {
        add_menu_page(
            'Управление сайтом',
            'Золотаревка ⚙️',
            self::CAP,
            'zolotarevka',
            [__CLASS__, 'render_dashboard'],
            'dashicons-location',
            3
        );

        $pages = [
            'zolotarevka'              => 'Панель управления',
            'zolotarevka-settings'     => 'Настройки сайта',
            'zolotarevka-page-home'    => 'Главная страница',
            'zolotarevka-page-school'  => 'Школа',
            'zolotarevka-page-kindergarten' => 'Детский сад',
            'zolotarevka-page-farm'    => 'Совхоз',
            'zolotarevka-page-sports'  => 'Спорт',
            'zolotarevka-page-village-life' => 'Жизнь села',
            'zolotarevka-page-media'   => 'Медиа',
            'zolotarevka-page-news'    => 'Новости',
        ];

        foreach ($pages as $slug => $title) {
            $method = 'render_' . str_replace(['zolotarevka-', 'zolotarevka'], ['page_', 'dashboard'], $slug);
            $method = str_replace('-', '_', $method);
            $page_slug = ($slug === 'zolotarevka') ? 'zolotarevka' : $slug;

            add_submenu_page(
                'zolotarevka',
                $title,
                $title,
                self::CAP,
                $page_slug,
                [__CLASS__, $method]
            );
        }
    }

    public static function register_settings() {
        register_setting('zolo_site_settings', 'zolo_site_settings', [__CLASS__, 'sanitize_site_settings']);
    }

    public static function sanitize_site_settings($input) {
        if (!is_array($input)) return zolo_site_settings_defaults();
        $defaults = zolo_site_settings_defaults();
        $clean = [];

        foreach ($defaults as $key => $default_val) {
            if ($key === 'footer_columns') {
                $clean[$key] = $default_val; // Keep defaults for now, handle via custom form
            } elseif (isset($input[$key])) {
                if (is_string($input[$key])) {
                    $clean[$key] = sanitize_text_field($input[$key]);
                } elseif (is_array($input[$key])) {
                    $clean[$key] = $input[$key]; // Let custom handler process arrays
                } else {
                    $clean[$key] = sanitize_text_field((string) $input[$key]);
                }
            } else {
                $clean[$key] = $default_val;
            }
        }

        return $clean;
    }

    /* =========================================================
     * Handle form submissions
     * ========================================================= */

    public static function handle_save_page_content() {
        if (empty($_POST['zolo_page_save']) || empty($_POST['zolo_page_slug'])) {
            return;
        }
        if (!current_user_can(self::CAP)) {
            wp_die('Доступ запрещён', 403);
        }
        check_admin_referer('zolo_save_page_' . $_POST['zolo_page_slug']);

        $slug = sanitize_key($_POST['zolo_page_slug']);
        $raw  = isset($_POST['zolo_content']) ? (array) $_POST['zolo_content'] : [];
        zolo_save_page_content_draft($slug, $raw);

        $action = sanitize_key($_POST['zolo_page_save'] ?? 'draft');

        if ($action === 'publish') {
            zolo_publish_page_content($slug);
            $msg = 'Опубликовано!';
            $type = 'success';
        } elseif ($action === 'preview') {
            $preview_url = add_query_arg(['zolo_preview' => $slug], home_url('/' . ($slug === 'home' ? '' : $slug . '/')));
            wp_safe_redirect($preview_url);
            exit;
        } else {
            $msg = 'Черновик сохранён';
            $type = 'info';
        }

        $redirect = add_query_arg([
            'page' => 'zolotarevka-page-' . $slug,
            'zolo_msg' => urlencode($msg),
            'zolo_type' => $type,
        ], admin_url('admin.php'));
        wp_safe_redirect($redirect);
        exit;
    }

    public static function handle_publish_all() {
        if (empty($_POST['zolo_publish_all'])) return;
        if (!current_user_can(self::CAP)) wp_die('Доступ запрещён', 403);
        check_admin_referer('zolo_publish_all');

        zolo_publish_all();

        $redirect = add_query_arg([
            'page' => 'zolotarevka',
            'zolo_msg' => urlencode('Все изменения опубликованы!'),
            'zolo_type' => 'success',
        ], admin_url('admin.php'));
        wp_safe_redirect($redirect);
        exit;
    }

    public static function handle_reset_page() {
        if (empty($_POST['zolo_reset_page']) || empty($_POST['zolo_page_slug'])) return;
        if (!current_user_can(self::CAP)) wp_die('Доступ запрещён', 403);
        check_admin_referer('zolo_reset_' . $_POST['zolo_page_slug']);

        $slug     = sanitize_key($_POST['zolo_page_slug']);
        $defaults = zolo_page_content_defaults($slug);
        update_option("zolo_page_{$slug}_draft", $defaults, false);
        update_option("zolo_page_{$slug}_live", $defaults, false);

        $redirect = add_query_arg([
            'page' => 'zolotarevka-page-' . $slug,
            'zolo_msg' => urlencode('Сброшено на умолчания'),
            'zolo_type' => 'info',
        ], admin_url('admin.php'));
        wp_safe_redirect($redirect);
        exit;
    }

    /* =========================================================
     * Helper: form field renderers
     * ========================================================= */

    private static function msg() {
        if (!empty($_GET['zolo_msg'])) {
            $type = $_GET['zolo_type'] ?? 'info';
            $class = $type === 'success' ? 'notice-success' : ($type === 'error' ? 'notice-error' : 'notice-info');
            printf('<div class="notice %s"><p>%s</p></div>', $class, esc_html($_GET['zolo_msg']));
        }
    }

    private static function render_text($name, $label, $value, $placeholder = '') {
        ?>
        <p>
            <label><strong><?php echo esc_html($label); ?></strong></label><br>
            <input type="text" name="zolo_content[<?php echo esc_attr($name); ?>]"
                   value="<?php echo esc_attr($value); ?>"
                   placeholder="<?php echo esc_attr($placeholder); ?>" style="width:100%;max-width:600px;">
        </p>
        <?php
    }

    private static function render_textarea($name, $label, $value, $placeholder = '', $rows = 4) {
        ?>
        <p>
            <label><strong><?php echo esc_html($label); ?></strong></label><br>
            <textarea name="zolo_content[<?php echo esc_attr($name); ?>]"
                      placeholder="<?php echo esc_attr($placeholder); ?>"
                      style="width:100%;max-width:600px;" rows="<?php echo (int) $rows; ?>"><?php echo esc_textarea($value); ?></textarea>
        </p>
        <?php
    }

    private static function render_checkbox($name, $label, $value) {
        ?>
        <p>
            <label>
                <input type="hidden" name="zolo_content[<?php echo esc_attr($name); ?>]" value="0">
                <input type="checkbox" name="zolo_content[<?php echo esc_attr($name); ?>]" value="1" <?php checked($value, true); ?>>
                <?php echo esc_html($label); ?>
            </label>
        </p>
        <?php
    }

    private static function render_number($name, $label, $value) {
        ?>
        <p>
            <label><strong><?php echo esc_html($label); ?></strong></label><br>
            <input type="number" name="zolo_content[<?php echo esc_attr($name); ?>]"
                   value="<?php echo (int) $value; ?>" style="width:100px;">
        </p>
        <?php
    }

    private static function render_repeater_start($name, $label, $items, $fields) {
        $idx = 0;
        ?>
        <div class="zolo-repeater" data-name="<?php echo esc_attr($name); ?>">
            <p><strong><?php echo esc_html($label); ?></strong></p>
            <div class="zolo-repeater-items">
                <?php foreach ($items as $item): ?>
                    <div class="zolo-repeater-item" style="background:#f0f0f1;padding:12px;margin-bottom:8px;border-radius:4px;position:relative;">
                        <?php foreach ($fields as $fkey => $flabel): ?>
                            <?php if ($fkey === $fields[array_key_first($fields)]): ?>
                                <input type="hidden" name="zolo_content[<?php echo esc_attr($name); ?>][<?php echo $idx; ?>][<?php echo esc_attr($fkey); ?>]"
                                       value="<?php echo esc_attr($item[$fkey] ?? ''); ?>">
                            <?php else: ?>
                                <div style="margin-bottom:4px;">
                                    <label style="font-size:12px;color:#666;"><?php echo esc_html($flabel); ?></label>
                                    <input type="text" name="zolo_content[<?php echo esc_attr($name); ?>][<?php echo $idx; ?>][<?php echo esc_attr($fkey); ?>]"
                                           value="<?php echo esc_attr($item[$fkey] ?? ''); ?>" style="width:100%;">
                                </div>
                            <?php endif; ?>
                        <?php endforeach; ?>
                        <button type="button" class="button zolo-remove-item"
                                style="position:absolute;top:8px;right:8px;background:#dc3545;color:#fff;border:none;cursor:pointer;line-height:1;padding:4px 8px;">✕</button>
                    </div>
                <?php $idx++; endforeach; ?>
            </div>
            <button type="button" class="button zolo-add-item" data-name="<?php echo esc_attr($name); ?>"
                    data-fields='<?php echo json_encode($fields); ?>'>+ Добавить</button>
        </div>
        <?php
    }

    private static function render_page_form($slug, $title, $fields, $content = null) {
        if ($content === null) {
            $content = zolo_get_page_content_draft($slug);
        }
        $has_changes = zolo_has_draft_changes($slug);
        ?>
        <div class="wrap">
            <h1><?php echo esc_html($title); ?></h1>
            <?php self::msg(); ?>
            <?php if ($has_changes): ?>
                <div class="notice notice-warning"><p>⚡ Есть неопубликованные изменения</p></div>
            <?php endif; ?>
            <form method="post" action="">
                <input type="hidden" name="zolo_page_slug" value="<?php echo esc_attr($slug); ?>">
                <?php wp_nonce_field('zolo_save_page_' . $slug); ?>

                <div id="zolo-page-editor" style="background:#fff;padding:20px;border:1px solid #ccc;border-radius:4px;max-width:800px;">
                    <?php
                    foreach ($fields as $field) {
                        $type  = $field['type'] ?? 'text';
                        $name  = $field['name'] ?? '';
                        $label = $field['label'] ?? '';
                        $value = $name ? ($content[$name] ?? '') : '';

                        if ($type === 'text') {
                            self::render_text($name, $label, $value, $field['placeholder'] ?? '');
                        } elseif ($type === 'textarea') {
                            self::render_textarea($name, $label, $value, $field['placeholder'] ?? '', $field['rows'] ?? 4);
                        } elseif ($type === 'checkbox') {
                            self::render_checkbox($name, $label, $value);
                        } elseif ($type === 'number') {
                            self::render_number($name, $label, $value);
                        } elseif ($type === 'repeater') {
                            self::render_repeater_start($name, $label, $content[$name] ?? [], $field['subfields']);
                        } elseif ($type === 'section') {
                            echo '<hr><h2 style="margin-top:24px;">' . esc_html($label) . '</h2>';
                        }
                    }
                    ?>
                </div>

                <p style="margin-top:16px;">
                    <button type="submit" name="zolo_page_save" value="draft" class="button button-primary">💾 Сохранить черновик</button>
                    <button type="submit" name="zolo_page_save" value="preview" class="button">👁 Сохранить и предпросмотреть</button>
                    <button type="submit" name="zolo_page_save" value="publish" class="button button-primary"
                            style="background:#2d6a4f;border-color:#1b4332;">📢 Опубликовать</button>
                </p>
            </form>

            <form method="post" action="" style="margin-top:8px;">
                <input type="hidden" name="zolo_page_slug" value="<?php echo esc_attr($slug); ?>">
                <?php wp_nonce_field('zolo_reset_' . $slug); ?>
                <button type="submit" name="zolo_reset_page" value="1" class="button"
                        style="color:#dc3545;" onclick="return confirm('Сбросить все поля на умолчания? Это действие необратимо.');">
                    ↺ Сбросить на умолчания
                </button>
            </form>
        </div>

        <style>
        .zolo-repeater-item { position:relative; padding-right:40px; }
        .zolo-add-item, .zolo-remove-item { font-size:13px; }
        #zolo-page-editor p { margin-bottom:12px; }
        </style>
        <script>
        (function() {
            document.querySelectorAll('.zolo-add-item').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    var name = this.getAttribute('data-name');
                    var fields = JSON.parse(this.getAttribute('data-fields'));
                    var container = this.closest('.zolo-repeater').querySelector('.zolo-repeater-items');
                    var items = container.querySelectorAll('.zolo-repeater-item');
                    var idx = items.length;

                    var div = document.createElement('div');
                    div.className = 'zolo-repeater-item';
                    div.style.cssText = 'background:#f0f0f1;padding:12px;margin-bottom:8px;border-radius:4px;position:relative;';

                    var first = true;
                    for (var fkey in fields) {
                        if (!fields.hasOwnProperty(fkey)) continue;
                        var flabel = fields[fkey];
                        if (first) {
                            div.innerHTML += '<input type="hidden" name="zolo_content[' + name + '][' + idx + '][' + fkey + ']" value="">';
                            first = false;
                        } else {
                            div.innerHTML += '<div style="margin-bottom:4px;">' +
                                '<label style="font-size:12px;color:#666;">' + flabel + '</label>' +
                                '<input type="text" name="zolo_content[' + name + '][' + idx + '][' + fkey + ']" value="" style="width:100%;">' +
                                '</div>';
                        }
                    }
                    div.innerHTML += '<button type="button" class="button zolo-remove-item" style="position:absolute;top:8px;right:8px;background:#dc3545;color:#fff;border:none;cursor:pointer;line-height:1;padding:4px 8px;">✕</button>';
                    container.appendChild(div);
                    bindRemove();
                });
            });

            function bindRemove() {
                document.querySelectorAll('.zolo-remove-item').forEach(function(btn) {
                    btn.removeEventListener('click', function() {});
                    btn.addEventListener('click', function() {
                        var item = this.closest('.zolo-repeater-item');
                        if (item) item.parentNode.removeChild(item);
                    });
                });
            }
            bindRemove();
        })();
        </script>
        <?php
    }

    /* =========================================================
     * Dashboard page
     * ========================================================= */

    public static function render_dashboard() {
        $pages = [
            'home'    => 'Главная',
            'school'  => 'Школа',
            'kindergarten' => 'Детский сад',
            'farm'    => 'Совхоз',
            'sports'  => 'Спорт',
            'village-life' => 'Жизнь села',
            'media'   => 'Медиа',
            'news'    => 'Новости',
        ];
        ?>
        <div class="wrap">
            <h1>📊 Панель управления сайтом</h1>
            <?php self::msg(); ?>

            <p>Управление контентом страниц сайта Золотаревка.</p>

            <h2>Статус страниц</h2>
            <table class="widefat striped" style="max-width:600px;">
                <thead>
                    <tr>
                        <th>Страница</th>
                        <th>Редактор</th>
                        <th>Черновик</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($pages as $slug => $label): ?>
                        <tr>
                            <td><?php echo esc_html($label); ?></td>
                            <td><a href="<?php echo admin_url('admin.php?page=zolotarevka-page-' . $slug); ?>" class="button button-small">Редактировать</a></td>
                            <td>
                                <?php if (zolo_has_draft_changes($slug)): ?>
                                    <span style="color:#d63638;">⚡ Есть изменения</span>
                                <?php else: ?>
                                    <span style="color:#46b450;">✓ Опубликовано</span>
                                <?php endif; ?>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>

            <form method="post" action="" style="margin-top:20px;">
                <?php wp_nonce_field('zolo_publish_all'); ?>
                <button type="submit" name="zolo_publish_all" value="1" class="button button-primary"
                        style="background:#2d6a4f;border-color:#1b4332;padding:8px 24px;font-size:1.1em;">
                    📢 Опубликовать все изменения
                </button>
            </form>

            <hr style="margin-top:24px;">
            <h2>Быстрые ссылки</h2>
            <p>
                <a href="<?php echo admin_url('nav-menus.php'); ?>" class="button">🎯 Управление меню</a>
                <a href="<?php echo admin_url('edit.php?post_type=sports_season'); ?>" class="button">📅 Сезоны (спорт)</a>
                <a href="<?php echo admin_url('edit.php?post_type=bulletin_board'); ?>" class="button">📋 Доска объявлений</a>
                <a href="<?php echo admin_url('edit.php?post_type=gallery'); ?>" class="button">📸 Галерея</a>
            </p>
        </div>
        <?php
    }

    /* =========================================================
     * Site Settings page
     * ========================================================= */

    public static function render_page_settings() {
        $settings = zolo_get_site_settings();
        ?>
        <div class="wrap">
            <h1>⚙️ Настройки сайта</h1>
            <?php self::msg(); ?>
            <form method="post" action="options.php" style="max-width:800px;">
                <?php settings_fields('zolo_site_settings'); ?>

                <div style="background:#fff;padding:20px;border:1px solid #ccc;border-radius:4px;">

                    <h2>🌐 Социальные сети</h2>
                    <p>
                        <label><strong>VK</strong></label><br>
                        <input type="url" name="zolo_site_settings[social_vk]" value="<?php echo esc_attr($settings['social_vk']); ?>" style="width:100%;max-width:600px;">
                    </p>
                    <p>
                        <label><strong>Telegram</strong></label><br>
                        <input type="url" name="zolo_site_settings[social_telegram]" value="<?php echo esc_attr($settings['social_telegram']); ?>" style="width:100%;max-width:600px;">
                    </p>
                    <p>
                        <label><strong>Одноклассники</strong></label><br>
                        <input type="url" name="zolo_site_settings[social_ok]" value="<?php echo esc_attr($settings['social_ok']); ?>" style="width:100%;max-width:600px;">
                    </p>
                    <p>
                        <label><strong>RSS</strong></label><br>
                        <input type="url" name="zolo_site_settings[social_rss]" value="<?php echo esc_attr($settings['social_rss']); ?>" style="width:100%;max-width:600px;">
                    </p>

                    <hr>
                    <h2>📞 Контакты</h2>
                    <p>
                        <label><strong>Email</strong></label><br>
                        <input type="email" name="zolo_site_settings[contact_email]" value="<?php echo esc_attr($settings['contact_email']); ?>" style="width:100%;max-width:600px;">
                    </p>
                    <p>
                        <label><strong>Телефон</strong></label><br>
                        <input type="text" name="zolo_site_settings[contact_phone]" value="<?php echo esc_attr($settings['contact_phone']); ?>" style="width:100%;max-width:600px;" placeholder="+7 (999) 123-45-67">
                    </p>
                    <p>
                        <label><strong>Адрес</strong></label><br>
                        <input type="text" name="zolo_site_settings[contact_address]" value="<?php echo esc_attr($settings['contact_address']); ?>" style="width:100%;max-width:600px;" placeholder="с. Золотаревка, ул. Центральная, 1">
                    </p>

                    <hr>
                    <h2>🆔 Идентичность</h2>
                    <p>
                        <label><strong>Теглайн портала</strong></label><br>
                        <input type="text" name="zolo_site_settings[site_tagline]" value="<?php echo esc_attr($settings['site_tagline']); ?>" style="width:100%;max-width:600px;" placeholder="Неофициальный портал села">
                    </p>
                    <p>
                        <label><strong>Текст в топ-баре (регион)</strong></label><br>
                        <input type="text" name="zolo_site_settings[topbar_region]" value="<?php echo esc_attr($settings['topbar_region']); ?>" style="width:100%;max-width:600px;" placeholder="Золотаревка, Россия">
                    </p>

                    <hr>
                    <h2>📝 Подвал</h2>
                    <p>
                        <label><strong>Текст копирайта</strong></label><br>
                        <input type="text" name="zolo_site_settings[footer_copyright]" value="<?php echo esc_attr($settings['footer_copyright']); ?>" style="width:100%;max-width:600px;">
                    </p>
                    <p class="description">Колонки футера пока редактируются через базу данных. В следующем обновлении добавим редактор колонок.</p>
                </div>

                <?php submit_button('Сохранить настройки'); ?>
            </form>
        </div>
        <?php
    }

    /* =========================================================
     * Page editor: Home
     * ========================================================= */

    public static function render_home() {
        $fields = [
            ['type' => 'section', 'label' => '🔷 Hero-блок'],
            ['type' => 'text', 'name' => 'hero_title', 'label' => 'Заголовок hero', 'placeholder' => 'Добро пожаловать в Золотаревку!'],
            ['type' => 'text', 'name' => 'hero_subtitle', 'label' => 'Подзаголовок hero', 'placeholder' => 'Неофициальный портал...'],
            ['type' => 'text', 'name' => 'hero_btn_text', 'label' => 'Текст кнопки', 'placeholder' => 'Исследовать разделы'],
            ['type' => 'text', 'name' => 'hero_btn_url', 'label' => 'Ссылка кнопки', 'placeholder' => '#bento'],

            ['type' => 'section', 'label' => '🔷 Bento-плитки'],
            ['type' => 'text', 'name' => 'bento_section_title', 'label' => 'Заголовок раздела', 'placeholder' => 'Наши разделы'],
            ['type' => 'text', 'name' => 'bento_section_subtitle', 'label' => 'Подзаголовок раздела', 'placeholder' => 'Быстрый доступ...'],
            ['type' => 'repeater', 'name' => 'bento_cards', 'label' => 'Карточки разделов',
                'subfields' => ['icon' => 'Иконка', 'title' => 'Заголовок', 'text' => 'Текст', 'url' => 'Ссылка', 'gradient' => 'Gradient CSS']],

            ['type' => 'section', 'label' => '⚽ Ближайший матч'],
            ['type' => 'checkbox', 'name' => 'match_active', 'label' => 'Показывать виджет матча'],
            ['type' => 'text', 'name' => 'match_team_home', 'label' => 'Команда хозяев', 'placeholder' => 'ФК «Золотаревка»'],
            ['type' => 'text', 'name' => 'match_team_away', 'label' => 'Команда гостей', 'placeholder' => 'ФК «Соседи»'],
            ['type' => 'text', 'name' => 'match_date', 'label' => 'Дата/время', 'placeholder' => 'Суббота, 15:00'],
            ['type' => 'text', 'name' => 'match_location', 'label' => 'Место', 'placeholder' => 'Стадион «Центральный»'],

            ['type' => 'section', 'label' => '📰 Блок новостей'],
            ['type' => 'text', 'name' => 'news_section_title', 'label' => 'Заголовок', 'placeholder' => 'Последние новости'],
            ['type' => 'text', 'name' => 'news_all_link_text', 'label' => 'Текст ссылки "Все новости"', 'placeholder' => 'Все новости →'],
            ['type' => 'number', 'name' => 'news_count', 'label' => 'Количество новостей'],

            ['type' => 'section', 'label' => '💡 Блок "Предложить новость"'],
            ['type' => 'text', 'name' => 'suggest_title', 'label' => 'Заголовок', 'placeholder' => 'Хотите предложить новость?'],
            ['type' => 'text', 'name' => 'suggest_text', 'label' => 'Текст', 'placeholder' => 'Жители села могут...'],
            ['type' => 'text', 'name' => 'suggest_btn_text', 'label' => 'Текст кнопки', 'placeholder' => 'Предложить новость'],
        ];

        self::render_page_form('home', '🏠 Редактор главной страницы', $fields);
    }

    /* =========================================================
     * Page editor: School
     * ========================================================= */

    public static function render_page_school() {
        $fields = [
            ['type' => 'text', 'name' => 'page_title', 'label' => 'Заголовок страницы', 'placeholder' => 'Школа села Золотаревка'],
            ['type' => 'text', 'name' => 'news_section_title', 'label' => 'Заголовок Новости школы', 'placeholder' => 'Новости школы'],
            ['type' => 'number', 'name' => 'news_count', 'label' => 'Количество новостей'],
            ['type' => 'section', 'label' => '🚌 Расписание автобуса'],
            ['type' => 'text', 'name' => 'bus_schedule_title', 'label' => 'Заголовок расписания', 'placeholder' => 'Расписание школьного автобуса'],
            ['type' => 'repeater', 'name' => 'bus_schedule', 'label' => 'Маршруты',
                'subfields' => ['route' => 'Маршрут', 'morning' => 'Утренний', 'afternoon' => 'Обратный']],
            ['type' => 'section', 'label' => '🏆 Достижения'],
            ['type' => 'text', 'name' => 'achievements_title', 'label' => 'Заголовок достижений', 'placeholder' => 'Достижения учеников'],
            ['type' => 'repeater', 'name' => 'achievements', 'label' => 'Достижения',
                'subfields' => ['icon' => 'Иконка', 'title' => 'Заголовок', 'text' => 'Текст']],
            ['type' => 'section', 'label' => '💬 Комментарии'],
            ['type' => 'checkbox', 'name' => 'comments_enabled', 'label' => 'Показывать комментарии'],
            ['type' => 'text', 'name' => 'comments_title', 'label' => 'Заголовок комментариев', 'placeholder' => 'Комментарии'],
        ];
        self::render_page_form('school', '📚 Редактор страницы Школа', $fields);
    }

    /* =========================================================
     * Page editor: Kindergarten
     * ========================================================= */

    public static function render_page_kindergarten() {
        $fields = [
            ['type' => 'text', 'name' => 'page_title', 'label' => 'Заголовок страницы', 'placeholder' => 'Детский сад «Колосок»'],
            ['type' => 'text', 'name' => 'news_section_title', 'label' => 'Заголовок новостей', 'placeholder' => 'Жизнь групп'],
            ['type' => 'number', 'name' => 'news_count', 'label' => 'Количество новостей'],
            ['type' => 'section', 'label' => '👪 Советы родителям'],
            ['type' => 'text', 'name' => 'parenting_tips_title', 'label' => 'Заголовок советов', 'placeholder' => 'Полезные советы родителям'],
            ['type' => 'repeater', 'name' => 'parenting_tips', 'label' => 'Советы',
                'subfields' => ['icon' => 'Иконка', 'title' => 'Заголовок', 'text' => 'Текст']],
            ['type' => 'section', 'label' => '📸 Галерея'],
            ['type' => 'text', 'name' => 'gallery_title', 'label' => 'Заголовок галереи', 'placeholder' => 'Фотоотчеты'],
            ['type' => 'number', 'name' => 'gallery_count', 'label' => 'Количество фото'],
        ];
        self::render_page_form('kindergarten', '🧸 Редактор страницы Детский сад', $fields);
    }

    /* =========================================================
     * Page editor: Farm
     * ========================================================= */

    public static function render_page_farm() {
        $fields = [
            ['type' => 'text', 'name' => 'page_title', 'label' => 'Заголовок страницы', 'placeholder' => 'Совхоз «Золотаревский»'],
            ['type' => 'section', 'label' => '📜 История'],
            ['type' => 'text', 'name' => 'history_title', 'label' => 'Заголовок истории', 'placeholder' => 'История предприятия'],
            ['type' => 'textarea', 'name' => 'history_text', 'label' => 'Текст истории', 'rows' => 6],
            ['type' => 'section', 'label' => '⭐ Гордость села'],
            ['type' => 'text', 'name' => 'pride_title', 'label' => 'Заголовок', 'placeholder' => 'Гордость села'],
            ['type' => 'repeater', 'name' => 'pride_people', 'label' => 'Люди',
                'subfields' => ['icon' => 'Иконка', 'name' => 'Имя', 'role' => 'Роль', 'desc' => 'Описание']],
            ['type' => 'section', 'label' => '📦 Продукция'],
            ['type' => 'text', 'name' => 'products_title', 'label' => 'Заголовок продукции', 'placeholder' => 'Производимая продукция'],
            ['type' => 'number', 'name' => 'products_count', 'label' => 'Количество'],
            ['type' => 'section', 'label' => '💼 Вакансии'],
            ['type' => 'text', 'name' => 'vacancies_title', 'label' => 'Заголовок вакансий', 'placeholder' => 'Вакансии'],
            ['type' => 'number', 'name' => 'vacancies_count', 'label' => 'Количество'],
            ['type' => 'section', 'label' => '📞 Контакты'],
            ['type' => 'text', 'name' => 'contacts_title', 'label' => 'Заголовок контактов', 'placeholder' => 'Контакты'],
            ['type' => 'repeater', 'name' => 'contacts', 'label' => 'Контакты',
                'subfields' => ['icon' => 'Иконка', 'title' => 'Заголовок', 'text' => 'Текст']],
        ];
        self::render_page_form('farm', '🌾 Редактор страницы Совхоз', $fields);
    }

    /* =========================================================
     * Page editor: Sports
     * ========================================================= */

    public static function render_page_sports() {
        $fields = [
            ['type' => 'text', 'name' => 'page_title', 'label' => 'Заголовок страницы', 'placeholder' => 'Спорт в Золотаревке'],
            ['type' => 'text', 'name' => 'team_section_title', 'label' => 'Заголовок команды', 'placeholder' => 'Футбольная команда «Золотаревка»'],
            ['type' => 'text', 'name' => 'team_subtitle', 'label' => 'Подзаголовок', 'placeholder' => 'Состав команды'],
            ['type' => 'number', 'name' => 'team_count', 'label' => 'Количество игроков'],
            ['type' => 'section', 'label' => '🏅 Другие секции'],
            ['type' => 'text', 'name' => 'other_sections_title', 'label' => 'Заголовок', 'placeholder' => 'Другие секции'],
            ['type' => 'repeater', 'name' => 'other_sections', 'label' => 'Секции',
                'subfields' => ['icon' => 'Иконка', 'title' => 'Название', 'text' => 'Описание']],
            ['type' => 'section', 'label' => '📸 Галерея'],
            ['type' => 'text', 'name' => 'gallery_title', 'label' => 'Заголовок', 'placeholder' => 'Фото с игр'],
            ['type' => 'number', 'name' => 'gallery_count', 'label' => 'Количество фото'],
        ];
        self::render_page_form('sports', '⚽ Редактор страницы Спорт', $fields);
    }

    /* =========================================================
     * Page editor: Village Life
     * ========================================================= */

    public static function render_page_village_life() {
        $fields = [
            ['type' => 'text', 'name' => 'page_title', 'label' => 'Заголовок страницы', 'placeholder' => 'Жизнь села Золотаревка'],
            ['type' => 'section', 'label' => '📜 История'],
            ['type' => 'text', 'name' => 'history_title', 'label' => 'Заголовок', 'placeholder' => 'История села'],
            ['type' => 'textarea', 'name' => 'history_text', 'label' => 'Текст истории', 'rows' => 6],
            ['type' => 'section', 'label' => '⭐ Выдающиеся земляки'],
            ['type' => 'text', 'name' => 'residents_title', 'label' => 'Заголовок', 'placeholder' => 'Выдающиеся земляки'],
            ['type' => 'repeater', 'name' => 'notable_residents', 'label' => 'Земляки',
                'subfields' => ['icon' => 'Иконка', 'name' => 'Имя', 'role' => 'Роль', 'desc' => 'Описание']],
            ['type' => 'section', 'label' => '🎭 Дом Культуры'],
            ['type' => 'text', 'name' => 'culture_title', 'label' => 'Заголовок', 'placeholder' => 'Дом Культуры'],
            ['type' => 'text', 'name' => 'culture_description', 'label' => 'Описание', 'placeholder' => 'Дом Культуры села Золотаревка...'],
            ['type' => 'text', 'name' => 'culture_events_title', 'label' => 'Заголовок афиши', 'placeholder' => 'Афиша мероприятий'],
            ['type' => 'repeater', 'name' => 'culture_events', 'label' => 'Мероприятия',
                'subfields' => ['date' => 'Дата', 'event' => 'Мероприятие', 'time' => 'Время']],
            ['type' => 'text', 'name' => 'culture_circles_title', 'label' => 'Заголовок кружков', 'placeholder' => 'Кружки и секции'],
            ['type' => 'repeater', 'name' => 'culture_circles', 'label' => 'Кружки',
                'subfields' => ['icon' => 'Иконка', 'title' => 'Название', 'text' => 'Описание']],
            ['type' => 'section', 'label' => '📋 Доска объявлений'],
            ['type' => 'text', 'name' => 'bulletin_title', 'label' => 'Заголовок', 'placeholder' => 'Доска объявлений'],
            ['type' => 'text', 'name' => 'bulletin_description', 'label' => 'Описание', 'placeholder' => 'Куплю, продам, услуги...'],
            ['type' => 'number', 'name' => 'bulletin_count', 'label' => 'Количество объявлений'],
        ];
        self::render_page_form('village-life', '🏘️ Редактор страницы Жизнь села', $fields);
    }

    /* =========================================================
     * Page editor: Media
     * ========================================================= */

    public static function render_page_media() {
        $fields = [
            ['type' => 'text', 'name' => 'page_title', 'label' => 'Заголовок страницы', 'placeholder' => 'Медиа'],
            ['type' => 'section', 'label' => '📸 Фотогалерея'],
            ['type' => 'text', 'name' => 'gallery_title', 'label' => 'Заголовок', 'placeholder' => 'Фотогалерея села'],
            ['type' => 'text', 'name' => 'gallery_description', 'label' => 'Описание', 'placeholder' => 'Яркие моменты...'],
            ['type' => 'number', 'name' => 'gallery_count', 'label' => 'Количество фото'],
            ['type' => 'section', 'label' => '🎬 Видеогалерея'],
            ['type' => 'text', 'name' => 'video_title', 'label' => 'Заголовок', 'placeholder' => 'Видеогалерея'],
            ['type' => 'text', 'name' => 'video_description', 'label' => 'Описание', 'placeholder' => 'Видеозаписи мероприятий...'],
            ['type' => 'number', 'name' => 'video_offset', 'label' => 'Offset (сдвиг)'],
            ['type' => 'number', 'name' => 'video_count', 'label' => 'Количество видео'],
        ];
        self::render_page_form('media', '📸 Редактор страницы Медиа', $fields);
    }

    /* =========================================================
     * Page editor: News
     * ========================================================= */

    public static function render_page_news() {
        $fields = [
            ['type' => 'text', 'name' => 'page_title', 'label' => 'Заголовок страницы', 'placeholder' => 'Новости села'],
            ['type' => 'number', 'name' => 'news_per_page', 'label' => 'Новостей на странице'],
            ['type' => 'section', 'label' => '💡 Блок "Предложить новость"'],
            ['type' => 'text', 'name' => 'suggest_title', 'label' => 'Заголовок', 'placeholder' => 'Хотите предложить новость?'],
            ['type' => 'text', 'name' => 'suggest_text', 'label' => 'Текст', 'placeholder' => 'Жители села могут...'],
            ['type' => 'text', 'name' => 'suggest_btn_text', 'label' => 'Текст кнопки', 'placeholder' => 'Предложить новость'],
        ];
        self::render_page_form('news', '📰 Редактор страницы Новости', $fields);
    }
}

// Initialize both the backend and settings
add_action('plugins_loaded', function () {
    Zolotarevka_MVP_Backend::init();
    Zolotarevka_MVP_Settings::init();
});
