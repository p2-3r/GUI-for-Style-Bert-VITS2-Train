import tkinter as tk
import tkinter.ttk as ttk
from tkinter.font import Font as tkfont
from pathlib import Path
import glob
from pprint import pprint
import subprocess
import threading
import sys
import os
import wave

from pydub import AudioSegment
from pydub.playback import play as playsound

try:
    import simpleaudio
except ModuleNotFoundError:
    pass

from main import Jsontools

class Main_Window():
    @classmethod
    def create(self, root: tk.Tk):
        # 初期値設定
        self.root = root
        self.last_choiced = None
        self.audio_play = True

        # ウインドウの作成
        self.window = tk.Toplevel(root)
        self.window.title("Transcribe Editing tool")
        self.window.geometry("960x620")
        self.window.resizable(0, 0)
        self.window.protocol("WM_DELETE_WINDOW", destroy)

        #
        # モデル選択画面の作成
        #

        esd_frame = tk.Frame(self.window)
        esd_frame.grid(row=0, column=0)

        # モデル選択用の表を作成

        column = ("Model")
        self.esd_tree = ttk.Treeview(esd_frame, columns=column, show="headings", selectmode="browse", height=22)
        self.esd_tree.grid(row=0, column=0, sticky=tk.N+tk.W+tk.E, padx=10)

        self.esd_tree.column("Model", width=200, stretch='no')
        self.esd_tree.heading("Model", text="\"esd.list\"を編集したいモデルを選択", anchor="center")

        # 表の内容を作成

        self.style_path = Path(Jsontools.read_stylepath())

        # SBV2のDataフォルダ内のesd.listがあるフォルダ名だけ取得
        indata_folder = [Path(i) for i in glob.glob(str(self.style_path) + "/Data/**/esd.list")]
        inesd_folder_name = [i.parent.name for i in indata_folder]

        for i in inesd_folder_name:
            self.esd_tree.insert("", index="end", values=(i,))

        # ロード用のボタンを作成
        esd_load_button = tk.Button(esd_frame, text="Load", height=3, command=lambda: self.esd_load())
        esd_load_button.grid(row=1, column=0, sticky=tk.NSEW, padx=10)

        # esd.listの内容を表示する表を作成
        column = ("id", "Speaker", "Content")
        self.content_tree = ttk.Treeview(esd_frame, columns=column, show="headings", selectmode="browse", height=25)
        self.content_tree.bind("<<TreeviewSelect>>", self.table_choiced)

        self.content_tree.grid(row=0, column=2, rowspan=2, sticky=tk.N+tk.W+tk.E, pady=0)

        self.content_tree.column("id", width=35, stretch='no')
        self.content_tree.column("Speaker", width=140, stretch='no', anchor="center")
        self.content_tree.column("Content", width=540, stretch='no')

        self.content_tree.heading("id", text="id", anchor="center")
        self.content_tree.heading("Speaker", text="Speaker", anchor="center")
        self.content_tree.heading("Content", text="Content", anchor="center")

        self.scrollbar = ttk.Scrollbar(esd_frame, orient=tk.VERTICAL, command=self.content_tree.yview)
        self.content_tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=3, sticky=tk.N+tk.S+tk.E)

        # 選択されている表の内容を表示するための入力欄
        self.entry_content = tk.StringVar(esd_frame)
        self.entry = tk.Entry(esd_frame, textvariable=self.entry_content, font=tkfont(size=15, font="メイリオ"))

        #
        # イベント設定
        #

        # 列移動
        self.entry.bind(sequence="<Return>", func=self.entry_button_clicked)
        self.entry.bind(sequence="<Control-Return>", func=Key_Shortcuts.playsound_again)
        self.entry.bind(sequence="<Shift-Return>", func=Key_Shortcuts.return_1up)

        # 表とそのファイルの削除、復元機能
        self.entry.bind(sequence="<Control-Shift-D>", func=Key_Shortcuts.item_delete_restore)
        self.entry.bind(sequence="<Control-Shift-S>", func=Key_Shortcuts.item_delete_restore)

        # カーソル移動
        def f(x): self.entry.bind(sequence=f"<Control-KeyPress-{x}>", func=Key_Shortcuts.cursor_moves)
        [f(x) for x in ["u", "i", "o", "p", "l", ";"]]

        # コピーボードからの貼り付け
        def f(x): self.entry.bind(sequence=f"<Control-Shift-{x}>", func=Key_Shortcuts.paste_copyboard)
        [f(x) for x in ["H", "J", "K", "L", "+", "Y", "U", "I", "O", "P"]]

        # スピーカーのチェンジ
        def f(x): self.entry.bind(sequence=f"<Control-Alt-{x}>", func=Key_Shortcuts.change_speaker)
        [f(x) for x in ["h", "j", "l", ";", ":", "y", "u", "i", "o", "p"]]

        # 置換機能
        def f(x): self.entry.bind(sequence=f"<Shift-Alt-{x}>", func=Key_Shortcuts.replace)
        [f(x) for x in ["H", "J", "K", "L", "+", "Y", "U", "I", "O", "P"]]

        self.entry.grid(row=2, column=1, columnspan=2 ,sticky=tk.W+tk.E, pady=30)

        # 入力欄からesd.listの内容を書き換えるボタン
        entry_button = tk.Button(esd_frame, text="Enter", command=self.entry_button_clicked)
        entry_button.grid(row=2, column=0, sticky=tk.W+tk.E, pady=30, padx=10)

    @classmethod
    def esd_load(self):  # loadボタンが押されたら、あとほかにloadしなおしたいときにも使う

        # ロード時リセット
        self.last_choiced = None

        record_id = self.esd_tree.focus()

        # なにも選択されていなかったら何もしない
        if not record_id:
            return

        # すでに読み込まれていた場合、削除する
        for i in self.content_tree.get_children():
            self.content_tree.delete(i)

        choiced_item = self.esd_tree.item(record_id, "values")[0]
        self.esd_path = Path(f"{self.style_path}/Data/{choiced_item}/esd.list")

        with open(self.esd_path, "r", encoding="utf-8") as f:
            self.content_list = f.readlines()

        for i, j in enumerate(self.content_list):
            self.content_list[i] = j.replace("\n", "").split("|")

        for i, j in enumerate(self.content_list):
            self.content_tree.insert("", index="end", iid=i, values=(i,j[1],j[3],))

    @classmethod
    def table_choiced(self, event):  # 表が選択されたら
        record_id = self.content_tree.focus()

        # Enterを押したとき二重で反応しないように
        if record_id == self.last_choiced:
            return

        # なにも選択されていなかったら何もしない
        if not record_id:
            return

        self.last_choiced = record_id

        choiced_item = self.content_tree.item(record_id, "values")
        model_name = self.esd_path.parent.name

        audio_name = Path(self.content_list[int(record_id)][0]).name
        self.audio_path = f"{str(self.style_path)}\\Data\\{model_name}\\raw\\{audio_name}"

        AudioPlayer.play(self.audio_path)

        # 表の選択された内容を入力欄に入れる
        self.entry_content.set(choiced_item[2])

        # 入力欄に自動的にカーソルを合わせる
        self.entry.focus()
        self.entry.icursor("end")

    @classmethod
    def entry_button_clicked(self, *event):

        # なにも選択されていなかったら何もしない
        record_id = self.content_tree.focus()
        if not record_id:
            return

        # 何も入力していなかったら何もしない
        if self.entry_content.get() == "":
            return

        with open(self.esd_path, "r", encoding="utf-8") as f:
            self.content_list = f.readlines()

        for i, j in enumerate(self.content_list):
            self.content_list[i] = j.replace("\n", "").split("|")

        choiced_item = self.content_tree.item(record_id, "values")

        input_num = int(choiced_item[0])
        input_speaker = choiced_item[1]
        input_text = self.entry_content.get()

        self.content_list[input_num][1] = input_speaker
        self.content_list[input_num][3] = input_text

        joined_list = ["|".join(i) for i in self.content_list]
        lined_list = [i + "\n" for i in joined_list]

        with open(self.esd_path, "w", encoding="utf-8") as f:
            f.writelines(lined_list)

        self.esd_load()

        #次の場所を選んでおく
        try:
            self.content_tree.focus(input_num + 1)
            self.content_tree.selection_set(input_num + 1)
            self.content_tree.yview_scroll(1, "units")
        except tk.TclError:
            self.content_tree.focus(0)
            self.content_tree.selection_set(0)
            self.content_tree.yview_scroll( - (len(self.content_list)), "units")

class Option_Window():
    @classmethod
    def cheatsheat(self):
        cheatsheat_frame = tk.Frame(Option_Window.option_window, relief=tk.RIDGE, bd=5)
        cheatsheat_frame.grid(row=0, column=0, padx=0, pady=0, sticky=tk.NSEW)

        def f(text, *, row, column, columnspan=1):
            l = tk.Label(cheatsheat_frame, text=text)
            l.grid(row=row, column=column, columnspan=columnspan, sticky=tk.W, pady=2)
            return l

        f("※ショートカットは入力欄にカーソルを合わせた状態でないと使用できません。", row=0, column=0, columnspan=2)

        f("Enter: ", row=1, column=0); f("esd.listを保存、次の行に移動", row=1, column=1)
        f("Ctrl + Enter: ", row=2, column=0); f("現在の文章をもう一度再生", row=2, column=1)
        f("Shift + Enter: ", row=3, column=0); f("一つ上の行に戻る", row=3, column=1)

        f("Ctrl + U or I", row=4, column=0); f("カーソルを左右に1つ移動", row=4, column=1)
        f("Ctrl + L or ;", row=5, column=0); f("カーソルを左右に3つ移動", row=5, column=1)
        f("Ctrl + O or P", row=6, column=0); f("カーソルを最初、最後に移動", row=6, column=1)

        f("Ctrl+Shift + D", row=7, column=0); f("その書き起こしデータの行と音声ファイルを削除", row=7, column=1)
        f("Ctrl+Shift + S", row=8, column=0); f("間違って削除した場合、これで1回分復元できます", row=8, column=1)

    @classmethod
    def copy_board(self):
        copybin_frame = tk.Frame(Option_Window.option_window, relief=tk.RIDGE, bd=5)
        copybin_frame.grid(row=1, column=0, padx=0, pady=0, sticky=tk.NSEW)

        def f(text, *, row, columnspan=1, ):
            l = tk.Label(copybin_frame, text=text)
            l.grid(row=row, column=0, columnspan=columnspan, sticky=tk.W, pady=3)
            return l

        f("Shift+Ctrl + 入力欄の左のアルファベットで入力欄の文字を貼り付けられます", row=0, columnspan=10)

        [f(text, row=i+1) for i, text in enumerate(["H:", "J:", "K:", "L:", ";", "Y:", "U:", "I:", "O:", "P:"])]

        def f(row):
            l = tk.Entry(copybin_frame, width=45)
            l.grid(row=row, column=1, columnspan=10, sticky=tk.W, pady=3)
            return l

        self.copy_dict = {}

        self.copy_dict["H"] = f(1);  self.copy_dict["Y"] = f(6)
        self.copy_dict["J"] = f(2);  self.copy_dict["U"] = f(7)
        self.copy_dict["K"] = f(3);  self.copy_dict["I"] = f(8)
        self.copy_dict["L"] = f(4);  self.copy_dict["O"] = f(9)
        self.copy_dict["plus"] = f(5);  self.copy_dict["P"] = f(10)

    @classmethod
    def speaker_board(self):
        speaker_frame = tk.Frame(Option_Window.option_window, relief=tk.RIDGE, bd=5)
        speaker_frame.grid(row=0, column=1, padx=0, pady=0, sticky=tk.NSEW)

        def f(text, *, row, column=0, columnspan=1):
            l = tk.Label(speaker_frame, text=text)
            l.grid(row=row, column=column, columnspan=columnspan, sticky=tk.NSEW, pady=3)
            return l

        f("Ctrl+Alt + 入力欄の左のアルファベットでSpeakerを切り替えます。", row=0, columnspan=4)

        [f(text, row=i+1) if i <= 4 else f(text, column=2, row=i-4, columnspan=1) \
            for i, text in enumerate(["H:", "J:", "L:", ";", ":", "Y:", "U:", "I:", "O:", "P:"])]

        def f(row, column=1):
            l = tk.Entry(speaker_frame, width=20)
            l.grid(row=row, column=column, columnspan=1, sticky=tk.W, pady=3)
            return l

        self.speaker_dict = {}

        self.speaker_dict["h"] = f(1);  self.speaker_dict["y"] = f(1, 3)
        self.speaker_dict["j"] = f(2);  self.speaker_dict["u"] = f(2, 3)
        self.speaker_dict["l"] = f(3);  self.speaker_dict["i"] = f(3, 3)
        self.speaker_dict["semicolon"] = f(4);  self.speaker_dict["o"] = f(4, 3)
        self.speaker_dict["colon"] = f(5);  self.speaker_dict["p"] = f(5, 3)

    @classmethod
    def replace_board(self):
        replace_frame = tk.Frame(Option_Window.option_window, relief=tk.RIDGE, bd=5)
        replace_frame.grid(row=1, column=1, padx=0, pady=0, sticky=tk.NSEW)

        def f(text, *, row, column=1,  columnspan=1):
            l = tk.Label(replace_frame, text=text)
            l.grid(row=row, column=column, columnspan=columnspan, sticky=tk.W, pady=3)
            return l

        f("Shift+Alt + 入力欄の左のアルファベットで入力欄の文字を置換できます", row=0, columnspan=10)

        [f(text, row=i+1) for i, text in enumerate(["H:", "J:", "K:", "L:", ";", "Y:", "U:", "I:", "O:", "P:"])]
        [f("-->", row=i+1, column=3) for i, text in enumerate(["H:", "J:", "K:", "L:", ";", "Y:", "U:", "I:", "O:", "P:"])]

        def f(row, column):
            l = tk.Entry(replace_frame, width=23)
            l.grid(row=row, column=column, columnspan=1, sticky=tk.W, pady=3)
            return l

        self.replace_dict = {}

        self.replace_dict["H"] = [f(1,2), f(1,4)]
        self.replace_dict["J"] = [f(2,2), f(2,4)]
        self.replace_dict["K"] = [f(3,2), f(3,4)]
        self.replace_dict["L"] = [f(4,2), f(4,4)]
        self.replace_dict["plus"] = [f(5,2), f(5,4)]

        self.replace_dict["Y"] = [f(6,2), f(6,4)]
        self.replace_dict["U"] = [f(7,2), f(7,4)]
        self.replace_dict["I"] = [f(8,2), f(8,4)]
        self.replace_dict["O"] = [f(9,2), f(9,4)]
        self.replace_dict["P"] = [f(10,2), f(10,4)]

    @classmethod
    def create(self, root: tk.Tk):
        # オプション用ウインドウの作成
        self.option_window = tk.Toplevel(root)
        self.option_window.title("Editing tool Options")
        self.option_window.geometry("733x543")
        self.option_window.resizable(0, 0)

        #チートシート部分作成
        self.cheatsheat()
        self.copy_board()
        self.speaker_board()
        self.replace_board()

class Key_Shortcuts():
    @classmethod
    def playsound_again(self, event):
        AudioPlayer.play(Main_Window.audio_path)

    @classmethod
    def return_1up(self, event):

        # なにも選択されていなかったら何もしない
        record_id = Main_Window.content_tree.focus()
        if not record_id:
            return

        # 何も入力していなかったら何もしない
        if Main_Window.entry_content.get() == "":
            return

        with open(Main_Window.esd_path, "r", encoding="utf-8") as f:
            Main_Window.content_list = f.readlines()

        for i, j in enumerate(Main_Window.content_list):
            Main_Window.content_list[i] = j.replace("\n", "").split("|")

        choiced_item = Main_Window.content_tree.item(record_id, "values")

        input_num = int(choiced_item[0])

        try:
            Main_Window.content_tree.focus(input_num - 1)
            Main_Window.content_tree.selection_set(input_num - 1)
            Main_Window.content_tree.yview_scroll(- 1, "units")
        except tk.TclError:
            Main_Window.content_tree.focus(len(Main_Window.content_list) -1 )
            Main_Window.content_tree.selection_set(len(Main_Window.content_list) -1 )
            Main_Window.content_tree.yview_scroll(len(Main_Window.content_list), "units")

    @classmethod
    def cursor_moves(self, event):
        key = event.keysym
        main_entry = Main_Window.entry

        key_dict = {"u": 1,
                    "i": -1,
                    "l": 3,
                    "semicolon": -3,
                    "o": "start",
                    "p": "end"}

        if type(key_dict[key]) == int:
            Main_Window.entry.icursor(main_entry.index(tk.INSERT) - key_dict[key])
            Main_Window.entry.xview_scroll( - (key_dict[key]), "units")

        else:
            if key == "o":
                Main_Window.entry.icursor(0)
                Main_Window.entry.xview_scroll( - (len(main_entry.get())), "units")
            elif key == "p":
                Main_Window.entry.icursor("end")
                Main_Window.entry.xview_scroll(len(main_entry.get()), "units")

    @classmethod
    def paste_copyboard(self, event):
        key = event.keysym
        paste = Option_Window.copy_dict[key].get()

        if paste != "":
            Main_Window.entry.insert(Main_Window.entry.index(tk.INSERT), paste)

    @classmethod
    def change_speaker(self, event):
        Main_Window.audio_play = False  # 音声を再生しない
        key = event.keysym
        speaker = Option_Window.speaker_dict[key].get()

        # 何も入力されてなかったら動作しない
        if speaker == "":
            return

        # なにも選択されていなかったら何もしない
        record_id = Main_Window.content_tree.focus()
        if not record_id:
            return

        with open(Main_Window.esd_path, "r", encoding="utf-8") as f:
            Main_Window.content_list = f.readlines()

        for i, j in enumerate(Main_Window.content_list):
            Main_Window.content_list[i] = j.replace("\n", "").split("|")

        choiced_item = Main_Window.content_tree.item(record_id, "values")

        input_num = int(choiced_item[0])

        Main_Window.content_list[input_num][1] = speaker

        joined_list = ["|".join(i) for i in Main_Window.content_list]
        lined_list = [i + "\n" for i in joined_list]

        with open(Main_Window.esd_path, "w", encoding="utf-8") as f:
            f.writelines(lined_list)


        Main_Window.esd_load()

        # 選択が外れるので同じところを選んでおく

        try:
            Main_Window.content_tree.focus(input_num)
            Main_Window.content_tree.selection_set(input_num)
        except tk.TclError:
            Main_Window.content_tree.focus(0)
            Main_Window.content_tree.selection_set(0)

    @classmethod
    def replace(self, event):
        key = event.keysym
        replaces = Option_Window.replace_dict[key]
        before = replaces[0].get()
        after = replaces[1].get()

        entry = Main_Window.entry

        if before != "":  # 変換前が空白なら置換しない
            t = entry.get().replace(before, after)
            entry.delete(0, "end")
            entry.insert(0, t)

    @classmethod
    def item_delete_restore(self, event):
        key = event.keysym

        if key == "D":
            self.choiced_num = Main_Window.content_tree.focus()
            if self.choiced_num == "": return # 何も選ばれてなかったら何もしない

            stylepath = Main_Window.style_path

            self.choiced_num = int(self.choiced_num)

            # 指定された要素を取り出しておいて削除して戻す
            with open(Main_Window.esd_path, "r", encoding="utf-8") as f:
                content_list = f.readlines()

            self.restore_element = content_list[self.choiced_num]

            del content_list[self.choiced_num]

            with open(Main_Window.esd_path, "w", encoding="utf-8") as f:
                f.writelines(content_list)

            # wav、モデルの名前を取り出し
            temp_path = self.restore_element.split("|")[0]
            wavname = Path(temp_path).name
            modelname = Path(temp_path).parent.parent.name

            # wavを取り出してファイルを変数においておく
            self.wavpath = f"{stylepath}\\Data\\{modelname}\\raw\\{wavname}"

            with open(self.wavpath, 'rb') as f:
                self.restore_wave = f.read()

            os.remove(self.wavpath)

            Main_Window.esd_load()

            # 選択が外れるので次を選んでおく

            try:
                Main_Window.content_tree.focus(self.choiced_num)
                Main_Window.content_tree.selection_set(self.choiced_num)
            except tk.TclError:
                Main_Window.content_tree.focus(0)
                Main_Window.content_tree.selection_set(0)

        elif key == "S":
            try:  # すでに復元を実行したなら何もしない
                if self.restore_element is None:
                    return
            except AttributeError:
                return

            # 取り出しておいたものを戻して更新する
            with open(Main_Window.esd_path, "r", encoding="utf-8") as f:
                content_list = f.readlines()

            content_list.insert(self.choiced_num, self.restore_element)

            with open(Main_Window.esd_path, "w", encoding="utf-8") as f:
                f.writelines(content_list)

            # 音声ファイルも戻す
            with open(self.wavpath, "wb") as f:
                f.write(self.restore_wave)

            self.restore_element = None

            Main_Window.esd_load()

            # 選択が外れるので次を選んでおく

            try:
                Main_Window.content_tree.focus(self.choiced_num)
                Main_Window.content_tree.selection_set(self.choiced_num)
            except tk.TclError:
                Main_Window.content_tree.focus(0)
                Main_Window.content_tree.selection_set(0)


class AudioPlayer():
    def play(path: Path):
        if not Main_Window.audio_play:
            Main_Window.audio_play = True
            return

        def f():
            simpleaudio.stop_all()
            audio = AudioSegment.from_wav(path)
            playsound(audio)

        thread = threading.Thread(target=f)
        thread.start()

def create_all(root: tk.Tk, programdir):
    # メインウインドウを隠す
    root.withdraw()

    try:
        import simpleaudio
    except ModuleNotFoundError:
        input("-"*80 + "\n"
              "Transcribe Editing toolでは、音声の再生を行うため \n"
              "'simpleaudio' をStyle-Bert-VITS2の仮想環境にインストールします。\n"
              "もしよければEnterを押してください...\n" + "-"*80)
        proc = subprocess.Popen(["pip", "install", "simpleaudio"], shell=True)
        result = proc.communicate()

        input("-"*80 + "\n"
              "インストールが完了しました。run.batを再起動してください。"
              "Enterを押して終了します...\n" + "-"*80)

        sys.exit()

    Main_Window.create(root)
    Option_Window.create(root)

def destroy():
    Main_Window.root.deiconify()
    Main_Window.window.destroy()
    Option_Window.option_window.destroy()