import tkinter as tk
from tkinter import font

MAIN_WINDOW_WIDTH = 700
MAIN_WINDOW_HEIGHT = 550


class Guide(tk.Button):
    def __init__(self, master):
        super().__init__(
            master=master,
            text="キーボード操作一覧",
            width=10,
            height=1,
            command=self.guide
        )
        self.master = master
        self.exist_window = False
        self.guide_window = None

    def guide(self):
        if self.exist_window:
            self.__del__()
        else:
            self.exist_window = True
            self.guide_window = tk.Toplevel(self.master)
            self.guide_window.title('キーボード操作一覧')
            self.guide_window.configure(borderwidth=10, relief=tk.RIDGE)
            self.guide_window.geometry('450x200' + '+' + str(MAIN_WINDOW_WIDTH-450) + '+' + str(0))
            self.guide_window.resizable(False, False)
            self.guide_window.protocol("WM_DELETE_WINDOW", self.__del__)
            bold_font = font.Font(self.guide_window, size=16, weight='bold')
            key_lab = tk.Label(self.guide_window, text='キー:', font=bold_font)
            process_lab = tk.Label(self.guide_window, text='動作', font=bold_font)
            cursol_key_right_lab = tk.Label(self.guide_window, text='カーソルキー右→:')
            cursol_key_right_process_lab = tk.Label(self.guide_window, text='次の動画を再生')
            cursol_key_left_lab = tk.Label(self.guide_window, text='カーソルキー左←:')
            cursol_key_left_process_lab = tk.Label(self.guide_window, text='前の動画を再生')
            cursol_key_up_lab = tk.Label(self.guide_window, text='カーソルキー上↑:')
            cursol_key_up_process_lab = tk.Label(self.guide_window, text='「カットする」にチェックする')
            cursol_key_down_lab = tk.Label(self.guide_window, text='カーソルキー下↓:')
            cursol_key_down_process_lab = tk.Label(self.guide_window, text='「カットする」のチェックを外す')
            space_key_lab = tk.Label(self.guide_window, text='スペースキー:')
            space_key_process_lab = tk.Label(self.guide_window, text='動画を再生(字幕変更)')
            shift_enter_key_lab = tk.Label(self.guide_window, text='(テキスト入力中に)シフト+エンター:')
            shift_enter_key_process_lab = tk.Label(self.guide_window, text='動画を再生(字幕を変更)')
            key_lab.grid(column=0, row=0, sticky=tk.E)
            process_lab.grid(column=1, row=0, sticky=tk.W)
            cursol_key_right_lab.grid(column=0, row=1, sticky=tk.E)
            cursol_key_right_process_lab.grid(column=1, row=1, sticky=tk.W)
            cursol_key_left_lab.grid(column=0, row=2, sticky=tk.E)
            cursol_key_left_process_lab.grid(column=1, row=2, sticky=tk.W)
            cursol_key_up_lab.grid(column=0, row=3, sticky=tk.E)
            cursol_key_up_process_lab.grid(column=1, row=3, sticky=tk.W)
            cursol_key_down_lab.grid(column=0, row=4, sticky=tk.E)
            cursol_key_down_process_lab.grid(column=1, row=4, sticky=tk.W)
            space_key_lab.grid(column=0, row=5, sticky=tk.E)
            space_key_process_lab.grid(column=1, row=5, sticky=tk.W)
            shift_enter_key_lab.grid(column=0, row=6, sticky=tk.E)
            shift_enter_key_process_lab.grid(column=1, row=6, sticky=tk.W)

        self.master.focus_set()
        return

    def __del__(self):
        self.guide_window.destroy()
        self.exist_window = False
        return

