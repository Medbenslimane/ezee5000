"""
ADB Manager - إدارة الاتصال بأجهزة Android عبر ADB
يتعامل مع الهاتف عبر USB أو WiFi بدون الحاجة لصلاحيات root
"""

import subprocess
import os
import platform
import shutil
from typing import Optional, List, Tuple


class ADBManager:
    """مدير اتصالات ADB مع أجهزة Android"""

    def __init__(self):
        self.adb_path = self._find_adb()
        self.connected_device: Optional[str] = None
        self.device_info: dict = {}

    def _find_adb(self) -> str:
        """البحث عن مسار ADB في النظام"""
        # البحث في PATH
        adb_in_path = shutil.which("adb")
        if adb_in_path:
            return adb_in_path

        # مسارات شائعة حسب نظام التشغيل
        system = platform.system()
        common_paths = []

        if system == "Windows":
            common_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
                os.path.expandvars(r"%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe"),
                r"C:\Android\platform-tools\adb.exe",
                r"C:\Program Files\Android\platform-tools\adb.exe",
            ]
        elif system == "Darwin":  # macOS
            common_paths = [
                os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
                "/usr/local/bin/adb",
            ]
        else:  # Linux
            common_paths = [
                os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
                "/usr/local/bin/adb",
                "/usr/bin/adb",
            ]

        for path in common_paths:
            if os.path.isfile(path):
                return path

        return "adb"  # fallback

    def _run_command(self, args: List[str], timeout: int = 30) -> Tuple[bool, str]:
        """تنفيذ أمر ADB وإرجاع النتيجة"""
        try:
            cmd = [self.adb_path] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )
            output = result.stdout.strip()
            if result.returncode != 0:
                error = result.stderr.strip()
                return False, error if error else output
            return True, output
        except subprocess.TimeoutExpired:
            return False, "انتهت المهلة الزمنية للاتصال"
        except FileNotFoundError:
            return False, "لم يتم العثور على ADB. يرجى تثبيت Android Platform Tools"
        except Exception as e:
            return False, f"خطأ: {str(e)}"

    def check_adb_installed(self) -> Tuple[bool, str]:
        """التحقق من تثبيت ADB"""
        success, output = self._run_command(["version"])
        if success:
            return True, output.split("\n")[0]
        return False, output

    def get_connected_devices(self) -> List[dict]:
        """الحصول على قائمة الأجهزة المتصلة"""
        success, output = self._run_command(["devices", "-l"])
        if not success:
            return []

        devices = []
        lines = output.split("\n")
        for line in lines[1:]:  # تخطي السطر الأول "List of devices attached"
            line = line.strip()
            if not line or "offline" in line:
                continue

            parts = line.split()
            if len(parts) >= 2 and parts[1] in ("device", "recovery", "unauthorized"):
                device = {
                    "serial": parts[0],
                    "status": parts[1],
                    "model": "",
                    "product": "",
                }
                # استخراج معلومات إضافية
                for part in parts[2:]:
                    if part.startswith("model:"):
                        device["model"] = part.split(":", 1)[1]
                    elif part.startswith("product:"):
                        device["product"] = part.split(":", 1)[1]
                devices.append(device)

        return devices

    def connect_device(self, serial: Optional[str] = None) -> Tuple[bool, str]:
        """الاتصال بجهاز محدد"""
        devices = self.get_connected_devices()

        if not devices:
            return False, "لا يوجد أجهزة متصلة. تأكد من:\n1. توصيل الهاتف عبر USB\n2. تفعيل وضع المطور\n3. تفعيل تصحيح USB"

        if serial:
            device = next((d for d in devices if d["serial"] == serial), None)
            if not device:
                return False, f"الجهاز {serial} غير موجود"
        else:
            device = devices[0]

        if device["status"] == "unauthorized":
            return False, "يرجى قبول إذن تصحيح USB على الهاتف"

        self.connected_device = device["serial"]
        self._load_device_info()
        return True, f"تم الاتصال بـ {device.get('model', device['serial'])}"

    def _load_device_info(self):
        """تحميل معلومات الجهاز المتصل"""
        if not self.connected_device:
            return

        props = {
            "model": "ro.product.model",
            "brand": "ro.product.brand",
            "android_version": "ro.build.version.release",
            "sdk_version": "ro.build.version.sdk",
            "device_name": "ro.product.device",
        }

        self.device_info = {}
        for key, prop in props.items():
            success, value = self._run_command(
                ["-s", self.connected_device, "shell", "getprop", prop]
            )
            if success:
                self.device_info[key] = value

    def get_device_info(self) -> dict:
        """الحصول على معلومات الجهاز المتصل"""
        return self.device_info

    def push_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """نقل ملف إلى الجهاز"""
        if not self.connected_device:
            return False, "لا يوجد جهاز متصل"
        return self._run_command(
            ["-s", self.connected_device, "push", local_path, remote_path]
        )

    def pull_file(self, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """سحب ملف من الجهاز"""
        if not self.connected_device:
            return False, "لا يوجد جهاز متصل"
        return self._run_command(
            ["-s", self.connected_device, "pull", remote_path, local_path]
        )

    def shell_command(self, command: str) -> Tuple[bool, str]:
        """تنفيذ أمر shell على الجهاز"""
        if not self.connected_device:
            return False, "لا يوجد جهاز متصل"
        return self._run_command(
            ["-s", self.connected_device, "shell", command]
        )

    def set_dns(self, dns_primary: str, dns_secondary: str = "") -> Tuple[bool, str]:
        """تغيير إعدادات DNS على الجهاز (لا يحتاج root)"""
        if not self.connected_device:
            return False, "لا يوجد جهاز متصل"

        # استخدام Private DNS (Android 9+)
        sdk = int(self.device_info.get("sdk_version", "0"))
        if sdk >= 28:  # Android 9+
            success, output = self.shell_command(
                f"settings put global private_dns_mode hostname"
            )
            if success:
                success, output = self.shell_command(
                    f"settings put global private_dns_specifier {dns_primary}"
                )
                if success:
                    return True, f"تم تعيين DNS الخاص إلى {dns_primary}"
            return False, f"فشل تعيين DNS: {output}"
        else:
            return False, "يتطلب Android 9 أو أحدث لتغيير DNS بدون root"

    def disable_private_dns(self) -> Tuple[bool, str]:
        """إعادة DNS إلى الوضع التلقائي"""
        if not self.connected_device:
            return False, "لا يوجد جهاز متصل"

        success, output = self.shell_command(
            "settings put global private_dns_mode opportunistic"
        )
        if success:
            return True, "تم إعادة DNS إلى الوضع التلقائي"
        return False, f"فشل: {output}"

    def get_installed_packages(self, third_party_only: bool = True) -> List[str]:
        """الحصول على قائمة التطبيقات المثبتة"""
        if not self.connected_device:
            return []

        flag = "-3" if third_party_only else ""
        success, output = self.shell_command(f"pm list packages {flag}")
        if not success:
            return []

        packages = []
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("package:"):
                packages.append(line.replace("package:", ""))
        return sorted(packages)

    def disable_package(self, package_name: str) -> Tuple[bool, str]:
        """تعطيل تطبيق (بدون حذفه) - آمن وقابل للتراجع"""
        if not self.connected_device:
            return False, "لا يوجد جهاز متصل"
        return self.shell_command(f"pm disable-user --user 0 {package_name}")

    def enable_package(self, package_name: str) -> Tuple[bool, str]:
        """إعادة تفعيل تطبيق معطل"""
        if not self.connected_device:
            return False, "لا يوجد جهاز متصل"
        return self.shell_command(f"pm enable {package_name}")

    def clear_app_cache(self, package_name: str) -> Tuple[bool, str]:
        """مسح كاش تطبيق معين"""
        if not self.connected_device:
            return False, "لا يوجد جهاز متصل"
        return self.shell_command(f"pm clear --cache-only {package_name}")

    def is_connected(self) -> bool:
        """التحقق إذا كان هناك جهاز متصل"""
        if not self.connected_device:
            return False
        devices = self.get_connected_devices()
        return any(d["serial"] == self.connected_device for d in devices)

    def disconnect(self):
        """قطع الاتصال"""
        self.connected_device = None
        self.device_info = {}
