<?php
// log-download.php - تسجيل التحميلات بشكل آمن

// منع الوصول المباشر غير المصرح به (اختياري)
// if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(403); exit; }

$file = 'downloads-log.txt';
$timestamp = date('Y-m-d H:i:s');
$ip = filter_var($_SERVER['REMOTE_ADDR'] ?? 'unknown', FILTER_VALIDATE_IP) ? $_SERVER['REMOTE_ADDR'] : 'unknown';
$user_agent = substr($_SERVER['HTTP_USER_AGENT'] ?? 'unknown', 0, 200); // منع الحقن الطويل

// تنسيق السجل
$log_entry = sprintf("[%s] IP: %s | UA: %s\n", $timestamp, $ip, $user_agent);

// الكتابة في الملف مع قفل لمنع التضارب
@file_put_contents($file, $log_entry, FILE_APPEND | LOCK_EX);

// إرجاع استجابة سريعة
http_response_code(204); // No Content - أسرع من 200
header('Content-Type: text/plain');
echo 'OK';
?>