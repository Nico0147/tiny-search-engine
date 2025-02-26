import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import os
import threading
import webbrowser
import sys

try:
    from search_engines import config
except ImportError as e:
    msg = '"{}"\nPlease install `search_engines` to resolve this error.'
    raise ImportError(msg.format(str(e)))


class ModernSearchGUI:
    def __init__(self, root):
        if sys.platform == "linux":
            root.state('normal')
            root.attributes('-zoomed', 0)
        else:
            # 修改全屏属性为最大化窗口
            root.state('zoomed')  # 替代原来的全屏模式
            root.attributes('-toolwindow', 0)  # 显示标准窗口按钮

        self.root = root
        self.root.title("Tiny Search")
        self.root.configure(bg="#ffffff")

        # 整体容器，使用grid布局管理
        self.main_container = tk.Frame(self.root, bg="#ffffff")
        self.main_container.pack(expand=True, fill=tk.BOTH)

        # 现代LOGO展示
        self.logo_frame = tk.Frame(self.main_container, bg="#ffffff")
        self.logo_frame.grid(row=0, column=0, columnspan=2, pady=(120, 30))
        self.logo_label = tk.Label(self.logo_frame,
                                   text="TINY",
                                   font=("Roboto", 48, "bold"),
                                   fg="#4285f4",
                                   bg="#ffffff")
        self.logo_label.pack(side=tk.LEFT)
        tk.Label(self.logo_frame,
                 text="SEARCH",
                 font=("Roboto", 48),
                 fg="#5f6368",
                 bg="#ffffff").pack(side=tk.LEFT)

        # 智能搜索框
        self.search_frame = tk.Frame(self.main_container, bg="#ffffff")
        self.search_frame.grid(row=1, column=0, columnspan=2, pady=20)

        # 搜索输入框
        self.query_entry = tk.Entry(self.search_frame,
                                    width=80,
                                    font=("Arial", 16),
                                    relief="flat",
                                    highlightthickness=1,
                                    highlightcolor="#4285f4",
                                    highlightbackground="#dfe1e5",
                                    bd=0,
                                    bg="#f1f3f4",
                                    fg="#202124",
                                    insertbackground="#202124")
        self.query_entry.pack(side=tk.LEFT, pady=10, padx=10, ipady=8)
        self.query_entry.bind("<Return>", lambda e: self.run_search())
        self.query_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.query_entry.bind("<FocusOut>", self._on_entry_focus_out)

        # 添加搜索图标作为按钮
        self.search_icon = tk.Label(self.search_frame, text="🔍", font=("Arial", 32), bg="#f1f3f4", fg="#5f6368",
                                    cursor="hand2")
        self.search_icon.pack(side=tk.LEFT, padx=(0, 10))
        self.search_icon.bind("<Button-1>", lambda e: self.run_search())
        self.search_icon.bind("<Enter>", self._on_icon_enter)
        self.search_icon.bind("<Leave>", self._on_icon_leave)

        # 进度条
        self.progress = ttk.Progressbar(
            self.search_frame,
            mode="indeterminate",
            length=100,
            orient="horizontal"
        )
        self.progress.pack(side=tk.LEFT, padx=10)

        # 创建居中容器
        self.center_container = tk.Frame(self.main_container, bg="#ffffff")
        self.center_container.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)

        # 智能结果容器
        self.result_container = tk.Canvas(self.center_container, bg="#ffffff", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.center_container, orient="vertical", command=self.result_container.yview)
        self.result_frame = tk.Frame(self.result_container, bg="#ffffff")

        # 居中包装框架
        self.center_wrapper = tk.Frame(self.result_container, bg="#ffffff")
        self.result_container.create_window((self.result_container.winfo_width() / 2, 0),
                                            window=self.center_wrapper,
                                            anchor="n")

        # 布局
        self.result_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定滚动事件
        self.result_container.bind_all("<MouseWheel>", self._on_mousewheel)
        self.result_frame.bind("<Configure>", self.on_frame_configure)

        # 初始化数据
        self.results_data = []

        # 添加状态标签
        self.status_label = tk.Label(self.root, text="", fg="#5f6368", bg="#ffffff")
        self.status_label.pack(side=tk.BOTTOM, pady=10)

        # 让结果显示区域铺满屏幕
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.center_container.grid_rowconfigure(0, weight=1)
        self.center_container.grid_columnconfigure(0, weight=1)

    def _on_entry_focus_in(self, event):
        self.query_entry.config(highlightbackground="#4285f4")

    def _on_entry_focus_out(self, event):
        self.query_entry.config(highlightbackground="#dfe1e5")

    def _on_icon_enter(self, event):
        self.search_icon.config(fg="#4285f4")

    def _on_icon_leave(self, event):
        self.search_icon.config(fg="#5f6368")

    def _on_mousewheel(self, event):
        self.result_container.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def run_search(self):
        query = self.query_entry.get()
        if not query:
            messagebox.showerror("Error", "Query is required!")
            return
        self._toggle_ui_state(False)
        self.progress.start()
        self.status_label.config(text="Searching the web...")
        search_engine = "bing"
        output_format = "json"
        filename = "output"
        pages = 5
        filter_type = "title"
        ignore_duplicates = False
        proxy = config.PROXY
        command = [
            "python", "search_engines_cli.py",
            "-q", query,
            "-e", search_engine,
            "-o", output_format,
            "-n", filename,
            "-p", str(pages),
            "-f", filter_type,
            "-i" if ignore_duplicates else ""
        ]
        if proxy:
            command.append("-proxy")
            command.append(proxy)
        command = [arg for arg in command if arg]
        search_thread = threading.Thread(target=self.run_command, args=(command, filename + ".json"))
        search_thread.start()

    def _toggle_ui_state(self, enabled=True):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.query_entry.config(state=state)

    def run_command(self, command, filename):
        try:
            subprocess.run(command, check=True)
            self.display_results(filename)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")
        self._toggle_ui_state(True)
        self.progress.stop()
        self.status_label.config(text="Search Completed!")

    def display_results(self, filename):
        for widget in self.center_wrapper.winfo_children():
            widget.destroy()
        if not os.path.exists(filename):
            messagebox.showerror("Error", "Output file does not exist.")
            return
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)  # 解析 JSON 数据
            query = data.get("query", "No query")
            results = data.get("results", {})  # 获取搜索结果部分
            self.results_data = []

            # 检查 Bing 的结果是否为空
            if "Bing" in results and not results["Bing"]:
                messagebox.showwarning("Warning",
                                       "您所在国家和地区不支持搜索这个关键词！\nYour region does not support searching for this keyword!")
                return

            for engine, engine_results in results.items():
                for result in engine_results:
                    self.results_data.append({
                        "engine": engine,
                        "title": result.get("title", "No Title"),
                        "link": result.get("link", "No Link"),
                        "host": result.get("host", "No Host"),
                        "text": result.get("text", "No description")  # 提取 text 字段
                    })

            if not self.results_data:
                messagebox.showinfo("Info", "No search results found.")
                return

            # 清空结果区域
            for widget in self.result_frame.winfo_children():
                widget.destroy()

            # 显示所有结果
            for result in self.results_data:
                result_frame = tk.Frame(self.result_frame, bg="#ffffff", padx=20, pady=10)
                result_frame.pack(fill=tk.X, expand=True, pady=10)  # 水平填充并扩展

                # 标题
                title = tk.Label(result_frame,
                                 text=result["title"],
                                 fg="#1a0dab",
                                 font=("Arial", 16),
                                 cursor="hand2",
                                 bg="#ffffff")
                title.pack(anchor="w", pady=5)  # 标题靠左对齐
                title.bind("<Button-1>", lambda e, url=result["link"]: self.open_url(url))

                # URL
                tk.Label(result_frame,
                         text=result["link"],
                         fg="#006621",
                         font=("Arial", 14),
                         bg="#ffffff").pack(anchor="w", pady=5)

                # 描述（text 字段）
                text_content = result["text"][:150] + "..." if len(result["text"]) > 150 else result["text"]
                tk.Label(result_frame,
                         text=text_content,
                         fg="#545454",
                         font=("Arial", 12),
                         wraplength=600,
                         justify="left",
                         bg="#ffffff").pack(anchor="w", pady=5)

                # 主机信息（host 字段）
                tk.Label(result_frame,
                         text=f"{result['host']}",
                         fg="#545454",
                         font=("Arial", 14),
                         wraplength=600,
                         justify="left",
                         bg="#ffffff").pack(anchor="w", pady=5)

                # 分割线
                ttk.Separator(result_frame, orient="horizontal").pack(fill=tk.X, pady=5)

            # 更新滚动区域
            self.result_container.update_idletasks()
            self.result_container.config(scrollregion=self.result_container.bbox("all"))

            # 将结果区域居中显示
            self.result_container.create_window((self.result_container.winfo_width() / 2, 0),
                                                window=self.result_frame,
                                                anchor="center")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse JSON: {e}")

    def open_url(self, url):
        webbrowser.open(url)

    def on_frame_configure(self, event):
        width = self.result_container.winfo_width()
        self.result_container.coords(self.center_wrapper, (width / 2, 0))
        self.result_container.configure(scrollregion=self.result_container.bbox("all"))


if __name__ == "__main__":
    root = tk.Tk()
    root.minsize(1024, 768)  # 设置最小窗口尺寸
    app = ModernSearchGUI(root)
    root.mainloop()