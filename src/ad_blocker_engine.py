"""
Ad Blocker Engine - محرك حجب الإعلانات
يعمل عبر ADB لتكوين DNS وتعطيل تطبيقات الإعلانات
بدون الحاجة لصلاحيات root - آمن تماماً
"""

import os
import json
import time
from datetime import datetime
from typing import Tuple, List, Optional, Callable
from src.adb_manager import ADBManager
from src.blocklist_manager import BlocklistManager


# تطبيقات الإعلانات المعروفة التي يمكن تعطيلها بأمان
KNOWN_AD_PACKAGES = [
    {"package": "com.google.android.gms.ads", "name": "Google Ads Module", "safe": True},
    {"package": "com.facebook.orca.ads", "name": "Facebook Ads", "safe": True},
    {"package": "com.startapp.android.publish", "name": "StartApp Ads", "safe": True},
    {"package": "com.applovin.sdk", "name": "AppLovin Ads SDK", "safe": True},
    {"package": "com.unity3d.ads", "name": "Unity Ads", "safe": True},
    {"package": "com.vungle.publisher", "name": "Vungle Ads", "safe": True},
    {"package": "com.mopub.mobileads", "name": "MoPub Ads", "safe": True},
    {"package": "com.inmobi.ads", "name": "InMobi Ads", "safe": True},
]

# خوادم DNS لحجب الإعلانات
AD_BLOCKING_DNS = {
    "adguard": {
        "name": "AdGuard DNS",
        "hostname": "dns.adguard-dns.com",
        "description": "خادم AdGuard لحجب الإعلانات والتتبع",
    },
    "nextdns": {
        "name": "NextDNS",
        "hostname": "dns.nextdns.io",
        "description": "خادم NextDNS مع حماية متقدمة",
    },
    "cloudflare_family": {
        "name": "Cloudflare Family",
        "hostname": "family.cloudflare-dns.com",
        "description": "Cloudflare مع حجب محتوى ضار",
    },
    "quad9": {
        "name": "Quad9",
        "hostname": "dns.quad9.net",
        "description": "Quad9 مع حماية من المواقع الضارة",
    },
}


class AdBlockerEngine:
    """محرك حجب الإعلانات الرئيسي"""

    def __init__(self):
        self.adb = ADBManager()
        self.blocklist = BlocklistManager()
        self.is_active = False
        self.selected_dns = "adguard"
        self.stats_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "logs", "stats.json"
        )
        self._load_stats()

    def _load_stats(self):
        """تحميل الإحصائيات"""
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        if os.path.exists(self.stats_file):
            with open(self.stats_file, "r", encoding="utf-8") as f:
                self.stats = json.load(f)
        else:
            self.stats = {
                "total_blocked": 0,
                "sessions": [],
                "disabled_packages": [],
                "dns_configured": False,
                "first_run": datetime.now().isoformat(),
            }

    def _save_stats(self):
        """حفظ الإحصائيات"""
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

    def check_requirements(self) -> Tuple[bool, str]:
        """التحقق من المتطلبات (ADB مثبت وجهاز متصل)"""
        adb_ok, adb_msg = self.adb.check_adb_installed()
        if not adb_ok:
            return False, f"❌ ADB غير مثبت: {adb_msg}"
        return True, f"✅ {adb_msg}"

    def connect_device(self, serial: Optional[str] = None) -> Tuple[bool, str]:
        """الاتصال بالجهاز"""
        return self.adb.connect_device(serial)

    def get_device_info(self) -> dict:
        """الحصول على معلومات الجهاز"""
        return self.adb.get_device_info()

    def get_available_dns(self) -> dict:
        """الحصول على قائمة خوادم DNS المتاحة"""
        return AD_BLOCKING_DNS

    def set_dns_provider(self, provider_key: str):
        """اختيار مزود DNS"""
        if provider_key in AD_BLOCKING_DNS:
            self.selected_dns = provider_key

    def activate_protection(self, progress_callback: Optional[Callable] = None) -> Tuple[bool, str]:
        """تفعيل الحماية من الإعلانات"""
        results = []

        # الخطوة 1: التحقق من الاتصال
        if progress_callback:
            progress_callback(1, 3, "التحقق من الاتصال...")

        if not self.adb.is_connected():
            return False, "❌ لا يوجد جهاز متصل"

        # الخطوة 2: تكوين DNS
        if progress_callback:
            progress_callback(2, 3, "تكوين DNS لحجب الإعلانات...")

        dns_info = AD_BLOCKING_DNS[self.selected_dns]
        success, msg = self.adb.set_dns(dns_info["hostname"])
        if success:
            results.append(f"✅ تم تكوين DNS: {dns_info['name']}")
            self.stats["dns_configured"] = True
        else:
            results.append(f"⚠️ DNS: {msg}")

        # الخطوة 3: تسجيل الجلسة
        if progress_callback:
            progress_callback(3, 3, "حفظ الإعدادات...")

        self.is_active = True
        blocked_count = self.blocklist.get_total_blocked_domains()
        self.stats["total_blocked"] = blocked_count
        self.stats["sessions"].append({
            "start": datetime.now().isoformat(),
            "dns": self.selected_dns,
            "domains_blocked": blocked_count,
        })
        self._save_stats()

        results.append(f"✅ تم حجب {blocked_count:,} نطاق إعلاني")
        return True, "\n".join(results)

    def deactivate_protection(self) -> Tuple[bool, str]:
        """إلغاء تفعيل الحماية"""
        if not self.adb.is_connected():
            self.is_active = False
            return True, "تم إلغاء الحماية (الجهاز غير متصل)"

        success, msg = self.adb.disable_private_dns()
        self.is_active = False
        self.stats["dns_configured"] = False
        self._save_stats()

        if success:
            return True, "✅ تم إعادة DNS إلى الوضع الافتراضي"
        return False, f"⚠️ {msg}"

    def scan_ad_packages(self) -> List[dict]:
        """فحص التطبيقات المثبتة للبحث عن تطبيقات إعلانية"""
        if not self.adb.is_connected():
            return []

        installed = self.adb.get_installed_packages(third_party_only=False)
        found_packages = []

        for pkg_info in KNOWN_AD_PACKAGES:
            if pkg_info["package"] in installed:
                found_packages.append(pkg_info)

        return found_packages

    def disable_ad_package(self, package_name: str) -> Tuple[bool, str]:
        """تعطيل تطبيق إعلاني (قابل للتراجع)"""
        success, msg = self.adb.disable_package(package_name)
        if success:
            if package_name not in self.stats["disabled_packages"]:
                self.stats["disabled_packages"].append(package_name)
                self._save_stats()
            return True, f"✅ تم تعطيل {package_name}"
        return False, f"❌ فشل: {msg}"

    def enable_ad_package(self, package_name: str) -> Tuple[bool, str]:
        """إعادة تفعيل تطبيق معطل"""
        success, msg = self.adb.enable_package(package_name)
        if success:
            if package_name in self.stats["disabled_packages"]:
                self.stats["disabled_packages"].remove(package_name)
                self._save_stats()
            return True, f"✅ تم إعادة تفعيل {package_name}"
        return False, f"❌ فشل: {msg}"

    def get_stats(self) -> dict:
        """الحصول على الإحصائيات"""
        return {
            "total_blocked": self.stats.get("total_blocked", 0),
            "dns_configured": self.stats.get("dns_configured", False),
            "disabled_packages": len(self.stats.get("disabled_packages", [])),
            "sessions_count": len(self.stats.get("sessions", [])),
            "is_active": self.is_active,
            "selected_dns": AD_BLOCKING_DNS.get(self.selected_dns, {}).get("name", ""),
            "last_update": self.blocklist.get_last_update(),
        }

    def is_protection_active(self) -> bool:
        """التحقق من حالة الحماية"""
        return self.is_active
