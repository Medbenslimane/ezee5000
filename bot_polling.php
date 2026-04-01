<?php
// ================== الإعدادات ==================
define('BOT_TOKEN', '8267802292:AAGK4sTC2IQ6Uj5x2p75zpkbrqRX_QaS49A');
define('OWNER_ID', '1555265017'); // ID حسابك الشخصي
define('SECRET', 'EZEE5000_SECRET_2025');
define('OFFSET_FILE', __DIR__ . '/offset.txt');

// ================== دوال مساعدة ==================
function apiRequest($method, $params = [])
{
    $url = "https://api.telegram.org/bot" . BOT_TOKEN . "/" . $method;
    $options = [
        'http' => [
            'method'  => 'POST',
            'header'  => "Content-Type: application/json",
            'content' => json_encode($params),
            'timeout' => 10
        ]
    ];
    return json_decode(file_get_contents($url, false, stream_context_create($options)), true);
}

function sendMessage($chat_id, $text)
{
    apiRequest('sendMessage', [
        'chat_id' => $chat_id,
        'text'    => $text
    ]);
}

function generateKey($hardware)
{
    $hash = hash('sha256', SECRET . $hardware);
    $short = strtoupper(substr($hash, 0, 20));
    return 'EZEE-5000-' . implode('-', str_split($short, 4));
}

// ================== قراءة OFFSET ==================
$offset = file_exists(OFFSET_FILE) ? (int)file_get_contents(OFFSET_FILE) : 0;

// ================== جلب الرسائل ==================
$response = apiRequest('getUpdates', [
    'offset'  => $offset + 1,
    'timeout' => 5
]);

if (empty($response['result'])) {
    echo "لا توجد رسائل جديدة";
    exit;
}

// ================== معالجة الرسائل ==================
foreach ($response['result'] as $update) {

    $update_id = $update['update_id'];
    file_put_contents(OFFSET_FILE, $update_id);

    if (!isset($update['message']['text'])) continue;

    $chat_id = $update['message']['chat']['id'];
    $text    = trim($update['message']['text']);

    // حماية: أنت فقط
    if ($chat_id != OWNER_ID) {
        sendMessage($chat_id, "⛔ هذا البوت خاص.");
        continue;
    }

    // أمر start
    if ($text === '/start') {
        sendMessage($chat_id,
            "🔐 *EZEE 5000 KeyGen Bot*\n\n".
            "📌 أرسل Hardware ID فقط\n".
            "وسيتم توليد مفتاح التفعيل فورًا."
        );
        continue;
    }

    // تنظيف Hardware ID
    $hardware = preg_replace('/[^A-Za-z0-9\-]/', '', $text);

    if (strlen($hardware) < 6) {
        sendMessage($chat_id, "❌ Hardware ID غير صالح");
        continue;
    }

    // توليد المفتاح
    $key = generateKey($hardware);

    sendMessage($chat_id,
        "✅ *مفتاح التفعيل*\n\n".
        "$key\n\n".
        "💽 Hardware ID:\n$hardware"
    );
}

echo "تمت المعالجة بنجاح";
