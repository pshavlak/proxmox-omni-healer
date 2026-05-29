<?php
/**
 * send-form.php — Обработчик заявок
 *
 * Принимает данные из формы, отправляет email и дублирует в Telegram.
 * Требует настройки переменных ниже.
 */

// ===== НАСТРОЙКИ =====
$to_email      = 'doctor@example.com';      // Email для получения заявок
$telegram_token = '';                        // Bot Token от @BotFather
$telegram_chat_id = '';                      // Telegram Chat ID
$site_name     = 'Гастроэнтеролог-диетолог';

// ===== Функция отправки в Telegram =====
function sendTelegram($message, $token, $chat_id) {
    if (empty($token) || empty($chat_id)) return false;
    $url = "https://api.telegram.org/bot{$token}/sendMessage";
    $data = [
        'chat_id' => $chat_id,
        'text'    => $message,
        'parse_mode' => 'HTML'
    ];
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    $result = curl_exec($ch);
    curl_close($ch);
    return $result;
}

// ===== Honeypot-проверка =====
if (!empty($_POST['_honey'])) {
    // Скрытое поле заполнено ботом — молча отбрасываем
    header('Content-Type: application/json');
    echo json_encode(['success' => true]);
    exit;
}

// ===== Валидация =====
$name    = trim($_POST['name'] ?? '');
$contact = trim($_POST['contact'] ?? '');
$service = trim($_POST['service'] ?? 'Не указана');
$comment = trim($_POST['comment'] ?? '');

if (empty($name) || empty($contact)) {
    header('Content-Type: application/json');
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Заполните обязательные поля']);
    exit;
}

// ===== Формируем письмо =====
$subject = "Заявка с сайта {$site_name}";
$email_message = "
<h2>Новая заявка с сайта</h2>
<p><strong>Имя:</strong> {$name}</p>
<p><strong>Контакты:</strong> {$contact}</p>
<p><strong>Услуга:</strong> {$service}</p>
<p><strong>Комментарий:</strong> {$comment}</p>
<hr>
<p><em>Отправлено с сайта {$site_name}</em></p>
";

$headers  = "MIME-Version: 1.0\r\n";
$headers .= "Content-Type: text/html; charset=UTF-8\r\n";
$headers .= "From: no-reply@{$_SERVER['HTTP_HOST']}\r\n";

// ===== Отправляем email =====
$email_sent = mail($to_email, $subject, $email_message, $headers);

// ===== Дублируем в Telegram =====
$telegram_message = "<b>Новая заявка с сайта</b>\n"
    . "\nИмя: {$name}"
    . "\nКонтакты: {$contact}"
    . "\nУслуга: {$service}"
    . "\nКомментарий: {$comment}";

sendTelegram($telegram_message, $telegram_token, $telegram_chat_id);

// ===== Ответ =====
header('Content-Type: application/json');
echo json_encode(['success' => true]);
