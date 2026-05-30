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
        add_action('add_meta_boxes', [__CLASS__, 'add_standings_meta_box']);
        add_action('add_meta_boxes', [__CLASS__, 'add_calendar_meta_box']);
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
}

Zolotarevka_MVP_Backend::init();
