<?php
/*********************************************************
 * EZEE 5000 - Activation Request (SMTP + LOG)
 * Receiver: simply.awes@gmail.com
 *********************************************************/

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

// ===== تحميل PHPMailer =====
require __DIR__ . '/PHPMailer/Exception.php';
require __DIR__ . '/PHPMailer/PHPMailer.php';
require __DIR__ . '/PHPMailer/SMTP.php';

// ===== إعدادات =====
define('ADMIN_EMAIL', 'simply.awes@gmail.com');
define('SMTP_USER',  'simply.awes@gmail.com'); // <-- بريد Gmail
define('SMTP_PASS',  'hgol hbpu onvy sgqe');         // <-- App Password
define('LOG_FILE',   __DIR__ . '/activation.log');

// ===== منع الوصول المباشر =====
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(403);
    exit('Access denied');
}

// ===== دوال LOG =====
function write_log($type, $message, $data = []) {
    $time = date('Y-m-d H:i:s');
    $ip   = $_SERVER['REMOTE_ADDR'] ?? 'UNKNOWN';

    $extra = '';
    foreach ($data as $k => $v) {
        $extra .= " | $k=$v";
    }

    $line = "[$time] [$type] IP=$ip$extra | $message" . PHP_EOL;
    file_put_contents(LOG_FILE, $line, FILE_APPEND | LOCK_EX);
}

function is_duplicate_request($email, $hardware) {
    if (!file_exists(LOG_FILE)) {
        return false;
    }
    $log = file(LOG_FILE, FILE_IGNORE_NEW_LINES);
    foreach ($log as $line) {
        if (stripos($line, "email=$email") !== false ||
            stripos($line, "HDD=$hardware") !== false) {
            return true;
        }
    }
    return false;
}

// ===== قراءة وتنظيف البيانات =====
$institute = trim($_POST['institute_name'] ?? '');
$email     = trim($_POST['email'] ?? '');
$hardware  = trim($_POST['hardware_id'] ?? '');
$phone     = trim($_POST['phone'] ?? '');

if ($institute === '' || $email === '' || $hardware === '') {
    write_log('ERROR', 'بيانات ناقصة');
    exit('بيانات ناقصة');
}

// ===== تسجيل الطلب =====
write_log('REQUEST', 'طلب تفعيل جديد', [
    'institute' => $institute,
    'email'     => $email,
    'HDD'       => $hardware
]);

// ===== كشف التكرار =====
if (is_duplicate_request($email, $hardware)) {
    write_log('WARNING', 'طلب مكرر', [
        'email' => $email,
        'HDD'   => $hardware
    ]);
}

// ===== إرسال البريد عبر SMTP =====
$mail = new PHPMailer(true);

try {
    $mail->isSMTP();
    $mail->Host       = 'smtp.gmail.com';
    $mail->SMTPAuth   = true;
    $mail->Username   = SMTP_USER;
    $mail->Password   = SMTP_PASS;
    $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
    $mail->Port       = 587;
    $mail->CharSet    = 'UTF-8';

    // المرسل
    $mail->setFrom(SMTP_USER, 'EZEE 5000 Activation');
    $mail->addAddress(ADMIN_EMAIL);
    $mail->addReplyTo($email, $institute);

    // محتوى الرسالة
    $mail->isHTML(false);
    $mail->Subject = 'طلب تفعيل جديد - EZEE 5000';

    $mail->Body = "
طلب تفعيل جديد لبرنامج EZEE 5000

اسم المؤسسة:
$institute

البريد الإلكتروني:
$email

رقم القرص الصلب (HDD Serial):
$hardware

رقم الهاتف:
$phone

--------------------------------
تم الإرسال من صفحة التفعيل
";

    $mail->send();

    // ===== نجاح =====
    write_log('SUCCESS', 'تم إرسال الطلب بنجاح', [
        'email' => $email,
        'HDD'   => $hardware
    ]);

    echo "
    <h3 style='font-family:Cairo;color:green;text-align:center'>
        ✅ تم إرسال طلبك بنجاح<br>
        سيتم الرد عليك عبر البريد خلال 24 ساعة
    </h3>
    ";

} catch (Exception $e) {

    // ===== فشل =====
    write_log('ERROR', 'فشل الإرسال', [
        'email' => $email,
        'HDD'   => $hardware,
        'error' => $mail->ErrorInfo
    ]);

    echo "
    <h3 style='font-family:Cairo;color:red;text-align:center'>
        ❌ حدث خطأ أثناء الإرسال<br>
        يرجى المحاولة لاحقًا
    </h3>
    ";
}
/***********************
 * إرسال نسخة للمستخدم
 ***********************/
$userMail = new PHPMailer(true);

try {
    $userMail->isSMTP();
    $userMail->Host       = 'smtp.gmail.com';
    $userMail->SMTPAuth   = true;
    $userMail->Username   = SMTP_USER;
    $userMail->Password   = SMTP_PASS;
    $userMail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
    $userMail->Port       = 587;
    $userMail->CharSet    = 'UTF-8';

    // المرسل
    $userMail->setFrom(SMTP_USER, 'EZEE 5000');
    $userMail->addAddress($email, $institute);

    // محتوى الرسالة
    $userMail->isHTML(true);
    $userMail->Subject = 'تم استلام طلب تفعيل EZEE 5000';

    $userMail->Body = "
    <div style='font-family:Cairo,Arial;direction:rtl;text-align:right'>
        <h2 style='color:#00C897'>✅ تم استلام طلبك بنجاح</h2>

        <p>نشكركم على طلب تفعيل برنامج <strong>EZEE 5000</strong>.</p>

        <p><strong>تفاصيل الطلب:</strong></p>
        <ul>
            <li><strong>المؤسسة:</strong> $institute</li>
            <li><strong>Hardware ID:</strong> $hardware</li>
        </ul>

        <p>
            سيتم إرسال <strong>مفتاح التفعيل</strong> إلى هذا البريد
            خلال مدة أقصاها <strong>24 ساعة</strong>.
        </p>

        <p style='color:#555'>
            يرجى عدم تغيير القرص الصلب أو إعادة تثبيت النظام
            إلى حين استلام رمز التفعيل.
        </p>

        <hr>
        <p style='font-size:13px;color:#888'>
            فريق الدعم – EZEE 5000<br>
            هذه رسالة تلقائية، يرجى عدم الرد عليها
        </p>
    </div>
    ";

    $userMail->send();

    write_log('SUCCESS', 'تم إرسال نسخة تلقائية للمستخدم', [
        'email' => $email
    ]);

} catch (Exception $e) {
    write_log('WARNING', 'فشل إرسال النسخة للمستخدم', [
        'email' => $email,
        'error' => $userMail->ErrorInfo
    ]);
}

