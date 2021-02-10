import tkinter as tk
import smtplib
import os.path
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import formatdate
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import csv
import shutil
import sys

import secret

WORK_DIR = './.tmp/'
try:
    WORK_DIR = sys._MEIPASS + '/.tmp/'
except:
    pass


class Questionnaire(tk.Button):
    def __init__(self, master):
        super().__init__(
        master = master,
        text = "アンケート",
        command = self.questionnaire,  # クリック時に実行
        )
        self.smtp_host = 'smtp.gmail.com'
        self.smtp_port = 465
        self.user_name = secret.GMAIL
        self.from_address = secret.GMAIL
        self.to_address = secret.SCHOOL_MAIL


    def questionnaire(self):
        self.questionnaire_window = tk.Toplevel()
        self.questionnaire_window.title('アンケート')
        self.questionnaire_window.configure(borderwidth=10, relief=tk.RIDGE)
        self.questionnaire_window.geometry('500x600')
        self.questionnaire_window.resizable(False, False)
        # 名前
        row = 0
        reporter_lab = tk.Label(self.questionnaire_window, text='お名前')
        reporter_lab.grid(column=0, row=row, sticky=tk.W)
        self.reporter_textbox = tk.Entry(self.questionnaire_window, width=20)
        self.reporter_textbox.grid(column=0, row=row, columnspan=2, sticky=tk.E)

        self.questionnaire_bln = []
        self.questionnaire_chk = []
        self.chk_texts = []
        self.chk_texts.append('動画を編集したことがある')
        self.chk_texts.append('動画編集をしている人が知り合いにいる')
        for i in range(len(self.chk_texts)):
            row += 1
            self.questionnaire_bln.append(tk.BooleanVar())
            self.questionnaire_chk.append(tk.Checkbutton(self.questionnaire_window, variable=self.questionnaire_bln[i], text=self.chk_texts[i]))
            self.questionnaire_chk[i].grid(column=0, row=row, sticky=tk.W)

        row += 1
        score_lab1 = tk.Label(self.questionnaire_window, text='当てはまらない〜当てはまる', font=("",15))
        score_lab1.grid(column=2, row=row, columnspan=3)
        row += 1
        score_lab2 = tk.Label(self.questionnaire_window, text='　 １ 〜 ５', font=("",18))
        score_lab2.grid(column=2, row=row, columnspan=3)

        self.questionnaire_scale_lab = []
        self.questionnaire_scale_var = []
        self.questionnaire_scale = []
        self.scale_texts = []
        self.scale_texts.append('ボタンなどの配置が良い')
        self.scale_texts.append('ログの表示がわかりやすい')
        self.scale_texts.append('修正画面は操作しやすい')
        self.scale_texts.append('操作でわからないところがあった')
        self.scale_texts.append('楽に編集できた')
        self.scale_texts.append('全体的に使いやすい')

        for i in range(len(self.scale_texts)):
            row += 1
            self.questionnaire_scale_lab.append(tk.Label(self.questionnaire_window, text=self.scale_texts[i]))
            self.questionnaire_scale_var.append(tk.DoubleVar())
            self.questionnaire_scale_var[i].set(3)
            self.questionnaire_scale.append(tk.Scale(self.questionnaire_window, variable=self.questionnaire_scale_var[i],
                                                     orient=tk.HORIZONTAL,from_=1.0, to=5.0, resolution=0.1,
                                                     activebackground='red'))
            self.questionnaire_scale_lab[i].grid(column=0, row=row, columnspan=2, sticky=tk.E)
            self.questionnaire_scale[i].grid(column=2, row=row, columnspan=3)

        # コメント
        self.questionnaire_comment_lab = tk.Label(self.questionnaire_window, text='コメント(要望や感想などをお願いします。)')
        self.questionnaire_comment_box = ScrolledText(self.questionnaire_window, font=("", 15), height=5, width=45)
        self.questionnaire_comment_lab.place(relx=0, rely=0.7)
        self.questionnaire_comment_box.place(relx=0, rely=0.75)

        # アンケート送信ボタン
        send_mail_button = tk.Button(self.questionnaire_window, text="アンケート送信", command=self.send_answer)
        send_mail_button.place(relx=0.35, rely=0.93, relwidth=0.3)

    def send_answer(self):
        if not messagebox.askyesno(title='アンケート送信', message='アンケートを送信しますか？'):
            return
        subject, body = self.create_subject_body()
        mime = {'type': 'text', 'subtype': 'comma-separated-values'}
        try:
            os.mkdir(WORK_DIR)
        except OSError:
            pass
        attach_file = self.create_csv_file(output_dir=WORK_DIR)
        msg = self.create_message(subject, body, mime, attach_file)
        self.send_mail(msg)
        shutil.rmtree(WORK_DIR)
        return

    def create_subject_body(self):
        reporter = self.reporter_textbox.get()
        reporter = reporter if reporter != '' else '名無し'
        subject = 'vidediアンケート(' + reporter + 'さん)'
        texts_max_len = max([len(max(self.chk_texts)), len(max(self.scale_texts))]) + 1
        body = ''
        body += 'お名前\n' + reporter + 'さん\n\n'
        for i in range(len(self.chk_texts)):
            body += self.chk_texts[i] + '　' * (texts_max_len-len(self.chk_texts[i]))
            body += '○\n' if self.questionnaire_bln[i].get() else '×\n'
        body += '\n'
        for i in range(len(self.scale_texts)):
            body += self.scale_texts[i] + '　' * (texts_max_len-len(self.scale_texts[i]))
            body += str(self.questionnaire_scale_var[i].get()) + '\n'
        body += '\n'
        body += 'コメント\n'
        comment = self.questionnaire_comment_box.get('1.0', 'end -1c')
        body += comment if comment != '' else '--------------'
        body += '\n\n\n'
        return subject, body

    def create_csv_file(self, output_dir):
        reporter = self.reporter_textbox.get()
        reporter = reporter if reporter != '' else '名無し'
        file_name = output_dir + 'vidediアンケート(' + reporter + 'さん).csv'
        with open(file_name, 'w', encoding='cp932')as csv_file:
            field_names = ['項目', '回答']
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writeheader()
            writer.writerow({'項目': '名前', '回答': reporter})
            for i in range(len(self.chk_texts)):
                writer.writerow({'項目': self.chk_texts[i], '回答': '○' if self.questionnaire_bln[i].get() else '×'})
            for i in range(len(self.scale_texts)):
                writer.writerow({'項目': self.scale_texts[i], '回答': str(self.questionnaire_scale_var[i].get())})
            comment = self.questionnaire_comment_box.get('1.0', 'end -1c')
            comment = comment if comment != '' else '--------------'
            writer.writerow({'項目': 'コメント', '回答': comment})
        return file_name


    def create_message(self, subject, body, mime, attach_file):
        """
        Mailのメッセージを構築する
        """
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = self.from_address
        msg["To"] = self.to_address
        msg["Date"] = formatdate()

        body = MIMEText(body, _charset=None)
        msg.attach(body)

        # 添付ファイルのMIMEタイプを指定する
        attachment = MIMEBase(mime['type'], mime['subtype'])
        # 添付ファイルのデータをセットする
        with open(attach_file, mode='r', encoding='cp932')as read_file:
            attachment.set_payload(read_file.read().encode('cp932', 'ignore'))

        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment", filename=os.path.split(attach_file)[1])
        msg.attach(attachment)
        return msg

    def send_mail(self, msg):
        """
        Mailを送信する
        """
        smtp = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
        smtp.login(self.user_name, secret.GMAIL_APP_PASS)
        smtp.sendmail(self.from_address, [self.to_address], msg.as_string())
        smtp.close()
        self.questionnaire_window.destroy()
        return

# main_window = tk.Tk()
# main_window.title('hello')
# question_button = Questionnaire(main_window)
# question_button.pack()
# main_window.mainloop()