import tkinter as tk
from tkinter import Frame

class ClassFrame(Frame):
    def __init__(self, master, bg=None, width=None, height=None):
        super().__init__(master, bg=bg, width=width, height=height)

class LogFrame(ClassFrame):
    def __init__(self, master, log_max, bg=None, width=None, height=None):
        super(LogFrame, self).__init__(master, bg=bg, width=width, height=height)

        self.height = height
        self.width = width
        self.bg = bg

        # スクロールバーの作成
        self.scroll_bar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.scroll_bar.pack(fill=tk.Y, side=tk.RIGHT, expand=False)
        self.canvas = tk.Canvas(self, bg=self.bg, yscrollcommand=self.scroll_bar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_bar.config(command=self.canvas.yview)

        # ビューをリセット
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        self.interior = Frame(self.canvas, bg=self.bg, borderwidth=10)
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor=tk.NW)

        self.interior.bind('<Configure>', self.configure_interior)
        self.canvas.bind('<Configure>', self.configure_canvas)

        # ログを初期化
        self.log_max = log_max
        self.log_vars = []
        self.log_labels = []
        self.log_color = 0
        self.reset_all_logs()

    def configure_interior(self, event=None):
        size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
        self.canvas.config(scrollregion='0 0 %s %s' % size)
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.config(width=self.interior.winfo_reqwidth())

    def configure_canvas(self, event=None):
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())

    def mouse_y_scroll(self, event):
        if event.delta > 0:
            self.canvas.yview_scroll(-1, 'units')
        elif event.delta < 0:
            self.canvas.yview_scroll(1, 'units')

    # ログのセット
    def set_log(self, s):
        if len(self.log_vars) < self.log_max:
            self.log_vars.append(tk.StringVar())
            for i in range(len(self.log_vars)-1, 0, -1):
                self.log_vars[i].set(self.log_vars[i-1].get())
            self.log_labels.append(tk.Label(self.interior, textvariable=self.log_vars[len(self.log_vars) - 1],
                                            foreground='#' + format(self.log_color, '02x')*3, bg=self.bg))
            self.log_color += int(255 / self.log_max - 1)
            self.log_labels[len(self.log_vars)-1].pack(anchor=tk.S, fill=tk.X, padx=0, pady=0, ipadx=0, ipady=0)
            self.log_labels[len(self.log_vars)-1].bind('<MouseWheel>', self.mouse_y_scroll)
            self.log_vars[0].set(s)
        else:
            for i in range(len(self.log_vars)-1, 0, -1):
                self.log_vars[i].set(self.log_vars[i-1].get())
            self.log_vars[0].set(s)
        return

    # 大きいログのセット
    def set_big_log(self, s):
        self.set_log('')
        self.set_log('----------------------------------------------------------')
        self.set_log(s)
        self.set_log('----------------------------------------------------------')
        return

    # ログのリセット
    def reset_all_logs(self):
        for i in range(len(self.log_labels)):
            self.log_labels[i].destroy()
        self.log_vars = []
        self.log_labels = []
        self.log_color = 0
        # --       --     ----     ----      -----    ----     ----
        #  \\     //     -  -    ||   \\    ||---    ||   \\   _  _
        #   \\   //      | |     ||   ||    ||__|    ||   ||   ||
        #    \\ //      -  -     ||  //     ||___    ||  //   _  _
        #     \_/      ----     ----       -----    ----     ----
        for i in range(2):
            self.set_log('')
        self.set_log(r'       \_/          ----      ----        -----      ----          ----')
        self.set_log(r'     \ \ / /         _  _     | |___/ /     | |___     | |___/ /       _  _')
        self.set_log(r'   \ \     / /        | |      | |      | |   | |___|     | |      | |      | |')
        self.set_log(r' \ \        / /      -  -     | |---\ \    | |---     | |--- \ \     -  -')
        self.set_log(r'--          --     ----     ----        -----     ----          ----')
        self.set_log('')
        return
