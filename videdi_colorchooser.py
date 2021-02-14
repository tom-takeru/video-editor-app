import tkmacosx as tk
from tkinter import colorchooser


# 色選択ボタンのクラス
class ColorSelectButton(tk.Button):
    def __init__(self, master, bg_color='#ffffff', command=(lambda: None)):
        super().__init__(
            master=master,
            text="",
            width=30,
            height=30,
            bg=bg_color,
            relief='ridge',
            command=self.change_color,
            )
        self.config(fg='black')
        self.bg_color = bg_color
        self.command2 = command

    def set_color(self, bg_color):
        self.bg_color = bg_color
        self.config(bg=self.bg_color)

    def change_color(self):
        # color chooser を呼び出す
        c = colorchooser.askcolor()
        # 選択した色に設定
        if c[1]:
            self.bg_color = c[1]
            self.config(bg=self.bg_color)
            self.command2()
