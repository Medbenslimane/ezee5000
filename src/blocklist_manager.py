"""
Blocklist Manager - إدارة قوائم حجب الإعلانات
تحميل وتحديث ودمج قوائم النطاقات المحجوبة
"""

import os
import json
import time
import requests
from typing import List, Set, Tuple
from datetime import datetime


# قوائم حجب معروفة ومجانية
DEFAULT_BLOCKLIST_SOURCES = [
    {
        "name": "Steven Black's Hosts",
        "url": "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
        "description": "قائمة شاملة لحجب الإعلانات والمواقع الضارة",
        "enabled": True,
    },
    {
        "name": "AdGuard DNS Filter",
        "url": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
        "description": "قائمة AdGuard لحجب الإعلانات عبر DNS",
        "enabled": True,
    },
    {
        "name": "Peter Lowe's Ad List",
        "url": "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0",
        "description": "قائمة مختصرة وفعالة لخوادم الإعلانات",
        "enabled": True,
    },
]

# نطاقات يجب عدم حجبها أبداً (لضمان عمل الجهاز)
WHITELIST_DEFAULTS = {
    "localhost",
    "localhost.localdomain",
    "local",
    "broadcasthost",
    "ip6-localhost",
    "ip6-loopback",
    "ip6-localnet",
    "ip6-mcastprefix",
    "ip6-allnodes",
    "ip6-allrouters",
    "ip6-allhosts",
    "dns.google",
    "dns.cloudflare.com",
    "one.one.one.one",
    "connectivity.check.android.com",
    "clients3.google.com",
    "connectivitycheck.gstatic.com",
    "play.googleapis.com",
    "time.android.com",
}


class BlocklistManager:
    """مدير قوائم الحجب"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "blocklists")
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "config.json")
        self.merged_file = os.path.join(data_dir, "merged_hosts.txt")
        self.custom_file = os.path.join(data_dir, "custom_rules.txt")

        os.makedirs(data_dir, exist_ok=True)
        self._load_config()

    def _load_config(self):
        """تحميل الإعدادات"""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "sources": DEFAULT_BLOCKLIST_SOURCES,
                "whitelist": list(WHITELIST_DEFAULTS),
                "custom_blocked": [],
                "last_update": None,
                "auto_update": True,
                "update_interval_hours": 24,
            }
            self._save_config()

    def _save_config(self):
        """حفظ الإعدادات"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get_sources(self) -> List[dict]:
        """الحصول على قائمة المصادر"""
        return self.config["sources"]

    def add_source(self, name: str, url: str, description: str = "") -> bool:
        """إضافة مصدر جديد"""
        # التحقق من عدم التكرار
        for source in self.config["sources"]:
            if source["url"] == url:
                return False

        self.config["sources"].append({
            "name": name,
            "url": url,
            "description": description,
            "enabled": True,
        })
        self._save_config()
        return True

    def remove_source(self, url: str):
        """حذف مصدر"""
        self.config["sources"] = [s for s in self.config["sources"] if s["url"] != url]
        self._save_config()

    def toggle_source(self, url: str, enabled: bool):
        """تفعيل/تعطيل مصدر"""
        for source in self.config["sources"]:
            if source["url"] == url:
                source["enabled"] = enabled
                break
        self._save_config()

    def download_blocklist(self, url: str) -> Tuple[bool, Set[str]]:
        """تحميل قائمة حجب من الإنترنت"""
        try:
            response = requests.get(url, timeout=30, headers={
                "User-Agent": "AdBlockerShield/1.0"
            })
            response.raise_for_status()
            domains = self._parse_hosts_content(response.text)
            return True, domains
        except requests.RequestException as e:
            return False, set()

    def _parse_hosts_content(self, content: str) -> Set[str]:
        """تحليل محتوى ملف hosts واستخراج النطاقات"""
        domains = set()
        for line in content.split("\n"):
            line = line.strip()
            # تخطي التعليقات والأسطر الفارغة
            if not line or line.startswith("#") or line.startswith("!"):
                continue

            # تنسيق hosts: 0.0.0.0 domain.com أو 127.0.0.1 domain.com
            parts = line.split()
            if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
                domain = parts[1].strip().lower()
                if domain and domain not in WHITELIST_DEFAULTS and "." in domain:
                    domains.add(domain)
            # تنسيق adblock: ||domain.com^
            elif line.startswith("||") and line.endswith("^"):
                domain = line[2:-1].strip().lower()
                if domain and domain not in WHITELIST_DEFAULTS and "." in domain:
                    domains.add(domain)

        return domains

    def update_all_blocklists(self, progress_callback=None) -> Tuple[int, int]:
        """تحديث جميع القوائم المفعلة"""
        all_domains: Set[str] = set()
        enabled_sources = [s for s in self.config["sources"] if s["enabled"]]
        total = len(enabled_sources)
        success_count = 0

        for i, source in enumerate(enabled_sources):
            if progress_callback:
                progress_callback(i + 1, total, source["name"])

            success, domains = self.download_blocklist(source["url"])
            if success:
                all_domains.update(domains)
                success_count += 1

        # إضافة القائمة المحلية الافتراضية
        default_file = os.path.join(self.data_dir, "default_hosts.txt")
        if os.path.exists(default_file):
            with open(default_file, "r", encoding="utf-8") as f:
                local_domains = self._parse_hosts_content(f.read())
                all_domains.update(local_domains)

        # إضافة النطاقات المخصصة
        all_domains.update(set(self.config.get("custom_blocked", [])))

        # إزالة القائمة البيضاء
        whitelist = set(self.config.get("whitelist", []))
        all_domains -= whitelist

        # حفظ القائمة المدمجة
        self._save_merged_list(all_domains)

        self.config["last_update"] = datetime.now().isoformat()
        self.config["total_domains"] = len(all_domains)
        self._save_config()

        return success_count, len(all_domains)

    def _save_merged_list(self, domains: Set[str]):
        """حفظ القائمة المدمجة"""
        with open(self.merged_file, "w", encoding="utf-8") as f:
            f.write(f"# AdBlocker Shield - Merged Blocklist\n")
            f.write(f"# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total domains: {len(domains)}\n\n")
            for domain in sorted(domains):
                f.write(f"0.0.0.0 {domain}\n")

    def get_merged_domains(self) -> Set[str]:
        """الحصول على القائمة المدمجة"""
        if not os.path.exists(self.merged_file):
            return set()

        with open(self.merged_file, "r", encoding="utf-8") as f:
            return self._parse_hosts_content(f.read())

    def get_total_blocked_domains(self) -> int:
        """الحصول على عدد النطاقات المحجوبة"""
        return self.config.get("total_domains", 0)

    def get_last_update(self) -> str:
        """الحصول على تاريخ آخر تحديث"""
        last = self.config.get("last_update")
        if last:
            try:
                dt = datetime.fromisoformat(last)
                return dt.strftime("%Y-%m-%d %H:%M")
            except:
                return "غير معروف"
        return "لم يتم التحديث بعد"

    def add_to_whitelist(self, domain: str):
        """إضافة نطاق للقائمة البيضاء"""
        domain = domain.strip().lower()
        if domain and domain not in self.config["whitelist"]:
            self.config["whitelist"].append(domain)
            self._save_config()

    def remove_from_whitelist(self, domain: str):
        """إزالة نطاق من القائمة البيضاء"""
        domain = domain.strip().lower()
        if domain in self.config["whitelist"]:
            self.config["whitelist"].remove(domain)
            self._save_config()

    def get_whitelist(self) -> List[str]:
        """الحصول على القائمة البيضاء"""
        return self.config.get("whitelist", [])

    def add_custom_block(self, domain: str):
        """إضافة نطاق مخصص للحجب"""
        domain = domain.strip().lower()
        if domain and domain not in self.config["custom_blocked"]:
            self.config["custom_blocked"].append(domain)
            self._save_config()

    def remove_custom_block(self, domain: str):
        """إزالة نطاق مخصص من الحجب"""
        domain = domain.strip().lower()
        if domain in self.config["custom_blocked"]:
            self.config["custom_blocked"].remove(domain)
            self._save_config()

    def get_custom_blocks(self) -> List[str]:
        """الحصول على النطاقات المخصصة المحجوبة"""
        return self.config.get("custom_blocked", [])

    def needs_update(self) -> bool:
        """التحقق إذا كان يجب تحديث القوائم"""
        if not self.config.get("auto_update"):
            return False

        last = self.config.get("last_update")
        if not last:
            return True

        try:
            last_dt = datetime.fromisoformat(last)
            hours_diff = (datetime.now() - last_dt).total_seconds() / 3600
            return hours_diff >= self.config.get("update_interval_hours", 24)
        except:
            return True
