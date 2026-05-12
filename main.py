#!/usr/bin/env python3
"""
AdBlocker Shield - برنامج حجب الإعلانات لأجهزة Android
يعمل على سطح المكتب ويتصل بالهاتف عبر ADB
آمن تماماً - لا يحذف بيانات ولا يمس ملفات النظام
"""

import sys
import os

# إضافة المجلد الجذر للمشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui import AdBlockerGUI


def main():
    """نقطة الدخول الرئيسية"""
    print("=" * 50)
    print("   🛡️  AdBlocker Shield v1.0.0")
    print("   حاجب الإعلانات الاحترافي لأجهزة Android")
    print("=" * 50)
    print()

    app = AdBlockerGUI()
    app.run()


if __name__ == "__main__":
    main()
