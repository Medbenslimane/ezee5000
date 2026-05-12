"""
AdBlocker Shield - الواجهة الرسومية الرئيسية
واجهة حديثة باللغة العربية مع دعم RTL
"""

import customtkinter as ctk
import threading
import os
from tkinter import messagebox
from src.ad_blocker_engine import AdBlockerEngine, AD_BLOCKING_DNS


class AdBlockerGUI:
    """الواجهة الرسومية الرئيسية"""

    def __init__(self):
        self.engine = AdBlockerEngine()
        self._setup_window()
        self._create_sidebar()
        self._create_main_content()
        self._show_home_page()

    def _setup_window(self):
        """إعداد النافذة الرئيسية"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("AdBlocker Shield - حاجب الإعلانات")
        self.root.geometry("1000x650")
        self.root.minsize(900, 600)

        # تكوين الشبكة
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def _create_sidebar(self):
        """إنشاء الشريط الجانبي"""
        self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        # العنوان
        title = ctk.CTkLabel(
            self.sidebar, text="🛡️ AdBlocker",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 5))

        subtitle = ctk.CTkLabel(
            self.sidebar, text="حاجب الإعلانات الاحترافي",
            font=ctk.CTkFont(size=11)
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))

        # أزرار التنقل
        nav_buttons = [
            ("🏠  الرئيسية", self._show_home_page),
            ("📱  الجهاز", self._show_device_page),
            ("🚫  حجب الإعلانات", self._show_blocking_page),
            ("📋  القوائم", self._show_lists_page),
            ("📊  الإحصائيات", self._show_stats_page),
            ("⚙️  الإعدادات", self._show_settings_page),
        ]

        for i, (text, command) in enumerate(nav_buttons):
            btn = ctk.CTkButton(
                self.sidebar, text=text, command=command,
                font=ctk.CTkFont(size=13),
                anchor="w", height=40,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
            )
            btn.grid(row=i + 2, column=0, padx=10, pady=3, sticky="ew")

        # حالة الاتصال (أسفل الشريط)
        self.status_label = ctk.CTkLabel(
            self.sidebar, text="⚪ غير متصل",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.grid(row=9, column=0, padx=20, pady=(0, 10))

        version_label = ctk.CTkLabel(
            self.sidebar, text="الإصدار 1.0.0",
            font=ctk.CTkFont(size=10), text_color="gray"
        )
        version_label.grid(row=10, column=0, padx=20, pady=(0, 15))

    def _create_main_content(self):
        """إنشاء منطقة المحتوى الرئيسية"""
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

    def _clear_main(self):
        """مسح المحتوى الرئيسي"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _show_home_page(self):
        """عرض الصفحة الرئيسية"""
        self._clear_main()

        # العنوان
        header = ctk.CTkLabel(
            self.main_frame, text="مرحباً بك في AdBlocker Shield",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.grid(row=0, column=0, columnspan=2, pady=(30, 5), padx=20)

        desc = ctk.CTkLabel(
            self.main_frame,
            text="برنامج احترافي لإزالة الإعلانات المزعجة من هاتفك Android\nبدون فقدان البيانات أو المساس بملفات النظام",
            font=ctk.CTkFont(size=13), justify="center"
        )
        desc.grid(row=1, column=0, columnspan=2, pady=(0, 30), padx=20)

        # بطاقات سريعة
        cards_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        cards_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=20, sticky="ew")
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        stats = self.engine.get_stats()

        # بطاقة 1: حالة الحماية
        card1 = ctk.CTkFrame(cards_frame, corner_radius=10)
        card1.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        status_text = "🟢 نشطة" if stats["is_active"] else "🔴 غير نشطة"
        ctk.CTkLabel(card1, text="حالة الحماية", font=ctk.CTkFont(size=12)).pack(pady=(15, 5))
        ctk.CTkLabel(card1, text=status_text, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 15))

        # بطاقة 2: نطاقات محجوبة
        card2 = ctk.CTkFrame(cards_frame, corner_radius=10)
        card2.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(card2, text="نطاقات محجوبة", font=ctk.CTkFont(size=12)).pack(pady=(15, 5))
        ctk.CTkLabel(card2, text=f"{stats['total_blocked']:,}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 15))

        # بطاقة 3: آخر تحديث
        card3 = ctk.CTkFrame(cards_frame, corner_radius=10)
        card3.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(card3, text="آخر تحديث", font=ctk.CTkFont(size=12)).pack(pady=(15, 5))
        ctk.CTkLabel(card3, text=stats["last_update"], font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(0, 15))

        # زر التفعيل السريع
        action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        action_frame.grid(row=3, column=0, columnspan=2, pady=30, padx=20)

        if stats["is_active"]:
            btn_text = "🔴 إيقاف الحماية"
            btn_color = "#d32f2f"
            btn_command = self._deactivate_protection
        else:
            btn_text = "🟢 تفعيل الحماية"
            btn_color = "#2e7d32"
            btn_command = self._activate_protection

        activate_btn = ctk.CTkButton(
            action_frame, text=btn_text, command=btn_command,
            font=ctk.CTkFont(size=16, weight="bold"),
            width=250, height=50, corner_radius=25,
            fg_color=btn_color, hover_color="#1565c0"
        )
        activate_btn.pack()

        # تعليمات سريعة
        tips = ctk.CTkLabel(
            self.main_frame,
            text="💡 تأكد من توصيل هاتفك عبر USB مع تفعيل وضع المطور وتصحيح USB",
            font=ctk.CTkFont(size=11), text_color="gray"
        )
        tips.grid(row=4, column=0, columnspan=2, pady=(20, 10), padx=20)

    def _show_device_page(self):
        """صفحة الجهاز"""
        self._clear_main()

        header = ctk.CTkLabel(
            self.main_frame, text="📱 إدارة الجهاز",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.grid(row=0, column=0, pady=(20, 15), padx=20, sticky="w")

        # زر الاتصال
        connect_btn = ctk.CTkButton(
            self.main_frame, text="🔌 اتصال بالجهاز",
            command=self._connect_device,
            font=ctk.CTkFont(size=13), width=200, height=40
        )
        connect_btn.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        # معلومات الجهاز
        self.device_info_frame = ctk.CTkFrame(self.main_frame)
        self.device_info_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        info = self.engine.get_device_info()
        if info:
            self._display_device_info(info)
        else:
            ctk.CTkLabel(
                self.device_info_frame,
                text="لم يتم الاتصال بأي جهاز بعد",
                font=ctk.CTkFont(size=13)
            ).pack(pady=20, padx=20)

        # تعليمات
        instructions = ctk.CTkFrame(self.main_frame)
        instructions.grid(row=3, column=0, padx=20, pady=15, sticky="ew")

        ctk.CTkLabel(
            instructions, text="📝 خطوات الاتصال:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        steps = [
            "1. افتح إعدادات الهاتف > حول الهاتف",
            "2. انقر على 'رقم الإصدار' 7 مرات لتفعيل وضع المطور",
            "3. ارجع للإعدادات > خيارات المطور > فعّل 'تصحيح USB'",
            "4. وصّل الهاتف بالكمبيوتر عبر كابل USB",
            "5. اقبل رسالة الإذن على الهاتف",
        ]
        for step in steps:
            ctk.CTkLabel(
                instructions, text=step,
                font=ctk.CTkFont(size=12), anchor="w"
            ).pack(anchor="w", padx=25, pady=2)

        ctk.CTkLabel(instructions, text="").pack(pady=5)  # spacing

    def _show_blocking_page(self):
        """صفحة حجب الإعلانات"""
        self._clear_main()

        header = ctk.CTkLabel(
            self.main_frame, text="🚫 حجب الإعلانات",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.grid(row=0, column=0, pady=(20, 15), padx=20, sticky="w")

        # اختيار DNS
        dns_frame = ctk.CTkFrame(self.main_frame)
        dns_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            dns_frame, text="اختر خادم DNS لحجب الإعلانات:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.dns_var = ctk.StringVar(value=self.engine.selected_dns)

        for key, info in AD_BLOCKING_DNS.items():
            radio = ctk.CTkRadioButton(
                dns_frame, text=f"{info['name']} - {info['description']}",
                variable=self.dns_var, value=key,
                font=ctk.CTkFont(size=12),
                command=lambda k=key: self.engine.set_dns_provider(k)
            )
            radio.pack(anchor="w", padx=30, pady=5)

        ctk.CTkLabel(dns_frame, text="").pack(pady=5)

        # أزرار التحكم
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=20, pady=15, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="✅ تفعيل الحماية",
            command=self._activate_protection,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=180, height=45, fg_color="#2e7d32"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame, text="❌ إيقاف الحماية",
            command=self._deactivate_protection,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=180, height=45, fg_color="#d32f2f"
        ).pack(side="left", padx=10)

        # سجل العمليات
        self.log_text = ctk.CTkTextbox(self.main_frame, height=150)
        self.log_text.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.log_text.insert("end", "جاهز للعمل...\n")

    def _show_lists_page(self):
        """صفحة إدارة القوائم"""
        self._clear_main()

        header = ctk.CTkLabel(
            self.main_frame, text="📋 إدارة قوائم الحجب",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.grid(row=0, column=0, pady=(20, 15), padx=20, sticky="w")

        # زر التحديث
        update_btn = ctk.CTkButton(
            self.main_frame, text="🔄 تحديث القوائم من الإنترنت",
            command=self._update_blocklists,
            font=ctk.CTkFont(size=13), width=250, height=40
        )
        update_btn.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        # عرض المصادر
        sources_frame = ctk.CTkScrollableFrame(self.main_frame, height=250)
        sources_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            sources_frame, text="مصادر القوائم:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        for source in self.engine.blocklist.get_sources():
            frame = ctk.CTkFrame(sources_frame)
            frame.pack(fill="x", padx=10, pady=3)

            status = "✅" if source["enabled"] else "❌"
            ctk.CTkLabel(
                frame, text=f"{status} {source['name']}",
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(anchor="w", padx=10, pady=(5, 0))

            ctk.CTkLabel(
                frame, text=source.get("description", ""),
                font=ctk.CTkFont(size=10), text_color="gray"
            ).pack(anchor="w", padx=10, pady=(0, 5))

        # إضافة نطاق مخصص
        custom_frame = ctk.CTkFrame(self.main_frame)
        custom_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            custom_frame, text="إضافة نطاق مخصص للحجب:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        entry_frame = ctk.CTkFrame(custom_frame, fg_color="transparent")
        entry_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.custom_domain_entry = ctk.CTkEntry(
            entry_frame, placeholder_text="مثال: ads.example.com", width=300
        )
        self.custom_domain_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            entry_frame, text="➕ إضافة", width=80,
            command=self._add_custom_domain
        ).pack(side="left")

    def _show_stats_page(self):
        """صفحة الإحصائيات"""
        self._clear_main()

        header = ctk.CTkLabel(
            self.main_frame, text="📊 الإحصائيات",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.grid(row=0, column=0, pady=(20, 15), padx=20, sticky="w")

        stats = self.engine.get_stats()

        stats_frame = ctk.CTkFrame(self.main_frame)
        stats_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        stats_frame.grid_columnconfigure((0, 1), weight=1)

        stat_items = [
            ("🚫 نطاقات محجوبة", f"{stats['total_blocked']:,}"),
            ("🛡️ حالة الحماية", "نشطة" if stats["is_active"] else "غير نشطة"),
            ("🌐 خادم DNS", stats["selected_dns"]),
            ("📦 تطبيقات معطلة", str(stats["disabled_packages"])),
            ("📅 آخر تحديث", stats["last_update"]),
            ("🔄 عدد الجلسات", str(stats["sessions_count"])),
        ]

        for i, (label, value) in enumerate(stat_items):
            row = i // 2
            col = i % 2
            item_frame = ctk.CTkFrame(stats_frame)
            item_frame.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
            ctk.CTkLabel(item_frame, text=label, font=ctk.CTkFont(size=11)).pack(pady=(8, 2))
            ctk.CTkLabel(item_frame, text=value, font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(2, 8))

    def _show_settings_page(self):
        """صفحة الإعدادات"""
        self._clear_main()

        header = ctk.CTkLabel(
            self.main_frame, text="⚙️ الإعدادات",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.grid(row=0, column=0, pady=(20, 15), padx=20, sticky="w")

        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # مظهر التطبيق
        ctk.CTkLabel(
            settings_frame, text="المظهر:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        appearance_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["داكن", "فاتح", "تلقائي"],
            command=self._change_appearance
        )
        appearance_menu.pack(anchor="w", padx=25, pady=5)

        # تحديث تلقائي
        ctk.CTkLabel(
            settings_frame, text="التحديث التلقائي:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        auto_update_switch = ctk.CTkSwitch(
            settings_frame, text="تحديث قوائم الحجب تلقائياً",
            font=ctk.CTkFont(size=12)
        )
        auto_update_switch.pack(anchor="w", padx=25, pady=5)
        auto_update_switch.select()  # مفعل افتراضياً

        # معلومات البرنامج
        info_frame = ctk.CTkFrame(self.main_frame)
        info_frame.grid(row=2, column=0, padx=20, pady=15, sticky="ew")

        ctk.CTkLabel(
            info_frame, text="حول البرنامج",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 5))

        about_text = (
            "AdBlocker Shield v1.0.0\n"
            "برنامج احترافي لحجب الإعلانات من أجهزة Android\n"
            "يعمل عبر ADB بدون الحاجة لصلاحيات Root\n"
            "آمن تماماً - لا يحذف أو يعدل ملفات النظام"
        )
        ctk.CTkLabel(
            info_frame, text=about_text,
            font=ctk.CTkFont(size=11), justify="center"
        ).pack(pady=(0, 15))

    # === وظائف الأحداث ===

    def _connect_device(self):
        """الاتصال بالجهاز"""
        def task():
            success, msg = self.engine.connect_device()
            self.root.after(0, lambda: self._on_device_connected(success, msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_device_connected(self, success, msg):
        """بعد محاولة الاتصال"""
        if success:
            self.status_label.configure(text="🟢 متصل", text_color="#4caf50")
            info = self.engine.get_device_info()
            messagebox.showinfo("نجاح", msg)
            self._show_device_page()
        else:
            self.status_label.configure(text="🔴 غير متصل", text_color="#f44336")
            messagebox.showwarning("تنبيه", msg)

    def _display_device_info(self, info: dict):
        """عرض معلومات الجهاز"""
        for widget in self.device_info_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.device_info_frame, text="معلومات الجهاز المتصل:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        labels = {
            "brand": "العلامة التجارية",
            "model": "الموديل",
            "android_version": "إصدار Android",
            "sdk_version": "إصدار SDK",
        }

        for key, label in labels.items():
            if key in info:
                ctk.CTkLabel(
                    self.device_info_frame,
                    text=f"  {label}: {info[key]}",
                    font=ctk.CTkFont(size=12)
                ).pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(self.device_info_frame, text="").pack(pady=5)

    def _activate_protection(self):
        """تفعيل الحماية"""
        def task():
            success, msg = self.engine.activate_protection()
            self.root.after(0, lambda: self._on_protection_result(success, msg))

        threading.Thread(target=task, daemon=True).start()

    def _deactivate_protection(self):
        """إيقاف الحماية"""
        def task():
            success, msg = self.engine.deactivate_protection()
            self.root.after(0, lambda: self._on_protection_result(success, msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_protection_result(self, success, msg):
        """نتيجة تفعيل/إيقاف الحماية"""
        if success:
            messagebox.showinfo("نجاح", msg)
        else:
            messagebox.showwarning("تنبيه", msg)
        self._show_home_page()

    def _update_blocklists(self):
        """تحديث قوائم الحجب"""
        def task():
            success_count, total = self.engine.blocklist.update_all_blocklists()
            self.root.after(0, lambda: messagebox.showinfo(
                "تم التحديث",
                f"تم تحديث {success_count} قائمة بنجاح\nإجمالي النطاقات المحجوبة: {total:,}"
            ))
            self.root.after(0, self._show_lists_page)

        threading.Thread(target=task, daemon=True).start()

    def _add_custom_domain(self):
        """إضافة نطاق مخصص"""
        domain = self.custom_domain_entry.get().strip()
        if domain:
            self.engine.blocklist.add_custom_block(domain)
            self.custom_domain_entry.delete(0, "end")
            messagebox.showinfo("تم", f"تم إضافة {domain} لقائمة الحجب")
        else:
            messagebox.showwarning("تنبيه", "يرجى إدخال نطاق")

    def _change_appearance(self, choice):
        """تغيير المظهر"""
        modes = {"داكن": "dark", "فاتح": "light", "تلقائي": "system"}
        ctk.set_appearance_mode(modes.get(choice, "dark"))

    def run(self):
        """تشغيل التطبيق"""
        self.root.mainloop()
