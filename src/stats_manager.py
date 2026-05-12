"""
Stats Manager - نظام الإحصائيات والتقارير
تتبع عدد الإعلانات المحجوبة والجلسات
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict


class StatsManager:
    """مدير الإحصائيات"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        self.data_dir = data_dir
        self.stats_file = os.path.join(data_dir, "statistics.json")
        os.makedirs(data_dir, exist_ok=True)
        self._load()

    def _load(self):
        """تحميل الإحصائيات"""
        if os.path.exists(self.stats_file):
            with open(self.stats_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "total_ads_blocked": 0,
                "total_domains_in_list": 0,
                "protection_sessions": [],
                "daily_stats": {},
                "disabled_apps": [],
                "first_install": datetime.now().isoformat(),
            }
            self._save()

    def _save(self):
        """حفظ الإحصائيات"""
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def record_session_start(self, dns_provider: str, domains_count: int):
        """تسجيل بداية جلسة حماية"""
        session = {
            "start": datetime.now().isoformat(),
            "end": None,
            "dns_provider": dns_provider,
            "domains_blocked": domains_count,
        }
        self.data["protection_sessions"].append(session)
        self.data["total_domains_in_list"] = domains_count
        self._update_daily_stats(domains_count)
        self._save()

    def record_session_end(self):
        """تسجيل نهاية جلسة حماية"""
        if self.data["protection_sessions"]:
            last = self.data["protection_sessions"][-1]
            if last["end"] is None:
                last["end"] = datetime.now().isoformat()
                self._save()

    def _update_daily_stats(self, blocked: int):
        """تحديث الإحصائيات اليومية"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.data["daily_stats"]:
            self.data["daily_stats"][today] = {
                "ads_blocked": 0,
                "sessions": 0,
            }
        self.data["daily_stats"][today]["ads_blocked"] += blocked
        self.data["daily_stats"][today]["sessions"] += 1

    def record_app_disabled(self, package_name: str):
        """تسجيل تعطيل تطبيق"""
        if package_name not in self.data["disabled_apps"]:
            self.data["disabled_apps"].append(package_name)
            self._save()

    def record_app_enabled(self, package_name: str):
        """تسجيل إعادة تفعيل تطبيق"""
        if package_name in self.data["disabled_apps"]:
            self.data["disabled_apps"].remove(package_name)
            self._save()

    def get_summary(self) -> Dict:
        """الحصول على ملخص الإحصائيات"""
        total_sessions = len(self.data["protection_sessions"])
        active_session = False
        if total_sessions > 0:
            active_session = self.data["protection_sessions"][-1]["end"] is None

        return {
            "total_domains_blocked": self.data["total_domains_in_list"],
            "total_sessions": total_sessions,
            "active_session": active_session,
            "disabled_apps_count": len(self.data["disabled_apps"]),
            "days_active": len(self.data["daily_stats"]),
            "first_install": self.data.get("first_install", "غير معروف"),
        }

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """الحصول على إحصائيات آخر X أيام"""
        result = []
        for i in range(days - 1, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self.data["daily_stats"].get(date, {"ads_blocked": 0, "sessions": 0})
            result.append({"date": date, **stats})
        return result

    def get_total_blocked(self) -> int:
        """الحصول على إجمالي المحجوبات"""
        return self.data.get("total_domains_in_list", 0)

    def reset_stats(self):
        """إعادة تعيين الإحصائيات"""
        self.data = {
            "total_ads_blocked": 0,
            "total_domains_in_list": 0,
            "protection_sessions": [],
            "daily_stats": {},
            "disabled_apps": self.data.get("disabled_apps", []),
            "first_install": self.data.get("first_install", datetime.now().isoformat()),
        }
        self._save()
