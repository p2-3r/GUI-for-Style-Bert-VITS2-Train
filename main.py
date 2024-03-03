import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter.font import Font as TkFont
import sys
import json
from pathlib import Path
import glob
import subprocess
import shutil

from src.ColorPrint import Existing as clp

# プログラムはStyleBertVITS2の仮想環境で起動しているので
# settings.jsonを取得するためにこのプログラムがある場所を
# 受け取っておく
programdir = str(Path(sys.argv[0]).parent.absolute())

class HelpWindow():  # ?ボタンを押したときに表示するヘルプ用ウインドウのクラス
    def __init__(self, content="For help Window", width="300x200") -> None:
        self.content = content
        self.width = width
        self.window = None
        self.g_window = None

    def display(self):
        self.window = tk.Toplevel(root)
        self.window.title("Help")
        self.window.geometry(self.width)
        self.window.resizable(0, 0)
        self.window.attributes("-topmost", True)

        # Xや-をクリックで閉じれないように
        self.window.protocol("WM_DELETE_WINDOW", (lambda: 'pass')())

        self.guard_window()

        # 表示するテキスト
        message = tk.Message(self.window, text=self.content)
        message.pack()

        # 閉じる用のOKボタン
        button = tk.Button(self.window, text="OK", width=5, command=self.ok_button_clicked)
        button.place(x=130, y=160)

    # helpを表示している間メインウインドウを操作できないように半透明なウインドウを重ねておく
    def guard_window(self):
        self.g_window = tk.Toplevel(root)
        self.g_window.title("GUI for Style-Bert-VITS2 Train")
        self.g_window.attributes("-alpha",0.5)
        self.g_window.geometry(f"{str(root.winfo_width())}x{str(root.winfo_height())}")
        self.g_window.geometry('+%d+%d' % (root.winfo_x(), root.winfo_y()))
        self.g_window.resizable(0, 0)

        # Xをクリックで閉じれないように
        self.g_window.protocol("WM_DELETE_WINDOW", (lambda: 'pass')())

    # okボタンが押されたときの動作
    def ok_button_clicked(self):
        try:
            self.g_window.destroy()
            self.window.destroy()
        except AttributeError:
            pass

    @staticmethod
    def button_create(frame: tk.Frame, command):
        return tk.Button(frame, text="❓", width=2, command=command)

class Tabs():
    # ユーザーがファイル入力欄を直接操作できないようにReadonlyにしてこの関数を利用して書き込む
    @staticmethod
    def entry_write(content: str, entry: tk.Entry) -> None:
        entry.configure(state='normal')
        entry.delete(0, "end")
        entry.insert("end", content)
        entry.configure(state='readonly')

class SlicesTab():
    @classmethod
    def create(self, tab: tk.Frame) -> None:  # Slicesタブの内容作成

        # 初期値設定
        self.canvasitems = []
        self.tabledict = {}

        #
        # フォルダ選択とloadボタン部分
        #

        # ファイル関係のボタンや入力欄をまとめるフレーム
        self.dir_frame = tk.Frame(tab)
        self.dir_frame.place(x=100, y=0)

        # helpボタンの作成
        text = "Fileボタンを押してフォルダを選択してからLoadボタンを押してください。\nそのフォルダの中に音声ファイルや音声ファイルをまとめたフォルダがあった場合、\n音声のファイルは音声ごとにモデルが分けられ、フォルダに音声ファイルがまとめてあった場合はまとめて一つのモデルになります。"
        dir_help_window = HelpWindow(text)
        dir_help_button = HelpWindow.button_create(self.dir_frame, dir_help_window.display)

        # フォルダの参照用ボタンと表示用入力欄の作成
        self.dir_entry = tk.Entry(self.dir_frame, state="readonly", width=50)

        def f(*, text, command): return tk.Button(self.dir_frame, text=text, width=5, command=command)
        dir_button = f(text="File", command=lambda: self.dir_button_clicked(self))

        # ファイルロード用ボタンの作成
        load_button = f(text="Load", command=lambda: self.load_button_clicked(self))

        # それぞれが横に並ぶように配置
        [j.grid(row=0, column=i) for i, j in enumerate([dir_help_button, self.dir_entry, dir_button, load_button])]

        #
        # 読み込んだフォルダと音声ファイル一覧を表で表示する部分の作成
        #

        # 表用のFrameを配置
        self.table_frame = tk.Frame(tab)
        self.table_frame.place(x=65, y=30)

        #Frameに表を表示する用のキャンバスを配置
        self.canvas = tk.Canvas(self.table_frame, width=480,height=260,bg='white')
        self.canvas.grid(row=0, column=0)

        # スクロールバーの作成
        scrollbar = ttk.Scrollbar(self.table_frame,orient=tk.VERTICAL)
        scrollbar.grid(row=0,column=1,sticky='ns')
        scrollbar.config(command=self.canvas.yview)

        self.canvas.config(yscrollcommand=scrollbar.set)
        self.canvas.config(scrollregion=(0,0,0,0))

        #表の内容を配置する用のフレーム
        self.incanvas_frame = tk.Frame(self.canvas, bg='white')
        self.canvas.create_window((0,0),window=self.incanvas_frame,anchor=tk.NW,width=self.canvas.cget('width'))

        #列の見出しを配置
        def f(text, column, *, width):
            l = tk.Label(self.incanvas_frame,width=width,text=text,background='white', borderwidth=2, relief=tk.RIDGE)
            l.grid(row=0,column=column,padx=0,pady=0,ipadx=0,ipady=0)
            return l

        f("☐", 0, width=3)
        f("Type", 1, width=4)
        f("FileName", 2, width=60)

        # もし前回フォルダを開いていたらそのフォルダの存在確認をして読み込む
        open_path = Jsontools.read()["slice_settings"]["open_path"]
        if Path(open_path).exists():
            Tabs.entry_write(open_path, self.dir_entry)
            self.load_button_clicked(self)

        #
        # スライスオプションのスライダーの作成
        #

        # オプションを置くためのフレーム作成
        self.option_frame = tk.Frame(tab)
        self.option_frame.place(x=40, y=300)

        # オプションをスライダーで作成
        def f(column, label, *, to, resolusion, length):
            j = tk.Scale(self.option_frame, from_=0, to=to, orient=tk.HORIZONTAL, resolution=resolusion, label=label, tickinterval=to, length=length, bd=3, relief=tk.GROOVE)
            j.grid(row=0, column=column)
            return j

        self.min_sec = f(0, "この秒数未満は切り捨てる", to=10, resolusion=0.5, length=140)
        self.max_sec = f(1, "この秒数以上は切り捨てる", to=15, resolusion=0.5, length=140)
        self.min_silence_dur_ms = f(2, "無音とみなして区切る最小の無音の長さ（ms）", to=2000, resolusion=100, length=235)

        # スライダーの初期値をsettings.jsonから読み込んで設定する
        slice_settings = Jsontools.read()["slice_settings"]
        self.min_sec.set(slice_settings["min_sec"])
        self.max_sec.set(slice_settings["max_sec"])
        self.min_silence_dur_ms.set(slice_settings["min_silence_dur_ms"])

        #
        # 続けて文字起こしするかのオプションと開始ボタンの作成
        #

        # ボタンとオプションを置くためのフレームを配置
        self.startbuttons_frame = tk.Frame(tab)
        self.startbuttons_frame.place(x=307, y=400)

        # 続けて文字起こしを行うかのチェックボタン
        self.continue_check = tk.BooleanVar(value=True)
        continue_button = tk.Checkbutton(self.startbuttons_frame, text="続けて文字起こしを行う", variable=self.continue_check)

        # スライスの開始ボタン
        slicestart_button = tk.Button(self.startbuttons_frame, text="スライス開始", width=10, command=lambda: self.start_button_clicked(self))

        # helpボタン
        content = "左のチェックをONにして開始した場合は、\nTranscribeタブの設定どおりに続けて文字起こしを行います。\n設定は次回起動時に引き継がれます。"
        start_help_window = HelpWindow(content=content)
        start_help_button = HelpWindow.button_create(self.startbuttons_frame, start_help_window.display)

        # それぞれが横に並ぶように配置
        [j.grid(row=0, column=i) for i, j in enumerate([continue_button, slicestart_button, start_help_button])]

    # Fileボタンがクリックされたときの動作
    def dir_button_clicked(self) -> None:
        open_path = Jsontools.read()["slice_settings"]["open_path"]

        if open_path == "" or not Path(open_path).exists():
            open_path = Path.cwd().absolute()

        path = filedialog.askdirectory(initialdir=open_path)
        Tabs.entry_write(path, self.dir_entry)

        # 次回起動時に最初から読み込んで置けるようにsettings.jsonに保存しておく
        settings = Jsontools.read()
        settings["slice_settings"]["open_path"] = path
        Jsontools.write(settings)

    # Loadボタンがクリックされたときの動作
    def load_button_clicked(self) -> None:
        entry_val = self.dir_entry.get()

        if entry_val == "":  # もしフォルダが選ばれてないなら動作しない
            return

        self.input_path = Path(entry_val)

        wavfiles = [Path(i) for i in glob.glob(f"{self.input_path.as_posix()}/*.wav")]

        folders = [Path(i) for i in glob.glob(f"{self.input_path.as_posix()}/**/")]
        wavin_folders = [Path(i) for i in folders if glob.glob(i.as_posix() + "/*.wav")]

        # もしすでにチェックボックスなどがある場合消去する
        if self.canvasitems:
            for i in self.canvasitems:
                i.destroy()
            self.canvasitems = []
            self.tabledict = {}

        # 表の内容を設定
        table_wavnames = [i.name for i in wavin_folders] + [i.name for i in wavfiles]
        table_filetypes = ["📂" for i in wavin_folders] + ["♪" for i in wavfiles]

        file_count = int(150/6*(len(table_wavnames)+1))
        self.canvas.config(scrollregion=(0,0,500,file_count))

        for i, value in enumerate(table_wavnames):
            if i%2==0:  # 色ありとなしが交互に出るように
                color='#cdfff7'
            else:
                color='white'

            # チェックボックスの配置
            self.tabledict[value] = tk.BooleanVar()
            self.tabledict[value].set(False)

            c = tk.Checkbutton(self.incanvas_frame,variable = self.tabledict[value],width=0,text='',background='white')
            c.grid(row=i+1, column=0, padx=0, pady=0, ipadx=0, ipady=0, sticky=tk.E)
            self.canvasitems.append(c)

            # Typeとファイルの名前の配置
            def f(i, *, width, text, color, column):
                j = tk.Label(self.incanvas_frame, width=width, text=text, background=color, borderwidth=2, relief=tk.RIDGE)
                j.grid(row=i+1, column=column, padx=0, pady=0, ipadx=0, ipady=0, sticky=tk.W)
                self.canvasitems.append(j)

            f(i, width=4, text=table_filetypes[i], color=color, column=1)
            f(i, width=59, text=table_wavnames[i], color=color, column=2)

    # Startボタンがクリックされたときの動作
    def start_button_clicked(self) -> None:
        if any([i.get() for i in self.tabledict.values()]):  # 表のチェックリストに一つ以上チェックが入っていたら

            slicefile_list = [Path(f"{self.input_path}\\{key}") for key, value in self.tabledict.items() if value.get()]

            # 選択した値を次回起動時にも引き継ぐ
            settings = Jsontools.read()
            slice_settings = settings["slice_settings"]
            slice_settings["min_sec"] = self.min_sec.get()
            slice_settings["max_sec"] = self.max_sec.get()
            slice_settings["min_silence_dur_ms"] = self.min_silence_dur_ms.get()
            Jsontools.write(settings)

            for i in slicefile_list:
                if i.is_file():
                    to_move = i.joinpath("..", i.stem)

                    try:
                        to_move.mkdir()
                    except FileExistsError:
                        clp.error(f"すでに{i.name}の名前と同じフォルダがあったため、スライスを開始できませんでした。")
                        self.load_button_clicked(self)
                        return

                    shutil.move(i, to_move)

            for i in slicefile_list:

                clp.info(f"\"{i.name}\"のスライスを実行しています...")

                proc = subprocess.Popen([f"python", "slice.py",
                                         "--min_sec", str(self.min_sec.get()),
                                         "--max_sec", str(self.max_sec.get()),
                                         "--input_dir", i,
                                         "--model_name", i.name,
                                         "--min_silence_dur_ms", str(self.min_silence_dur_ms.get())
                                         ], shell=True)

                result = proc.communicate()

            clp.complete("スライスがすべて完了しました。")

            # 続けて書き起こしを行うにチェックが入っていた場合は
            if self.continue_check.get():
                settings = Jsontools.read()
                trans_settings = settings["transcribe_settings"]
                trans_settings["device"] = TranscribeTab.option_device.get()
                trans_settings["lang"] = TranscribeTab.option_lang.get()
                trans_settings["whisper"] = TranscribeTab.option_whispermodel.get()
                trans_settings["num"] = TranscribeTab.option_num.get()
                trans_settings["prompt"] = TranscribeTab.option_prompt.get()
                Jsontools.write(settings)

                #　書き起こしを実行
                for i in slicefile_list:
                    clp.info(f"\"{i}\"の書き起こしを実行しています...")

                    proc = subprocess.Popen([f"python", "transcribe.py",
                                            "--model_name", i.stem,
                                            "--initial_prompt", TranscribeTab.option_prompt.get(),
                                            "--device", TranscribeTab.option_device.get(),
                                            "--language", TranscribeTab.option_lang.get(),
                                            "--model", TranscribeTab.option_whispermodel.get(),
                                            "--compute_type", TranscribeTab.option_num.get()
                                            ], shell=True)

                    result = proc.communicate()

            clp.complete("書き起こしがすべて完了しました。")

            # 終わったら表を更新する
            TranscribeTab.reload_button_clicked(TranscribeTab)
            self.load_button_clicked(self)
        else:
            clp.warn("スライスするファイルを1つ以上指定してください。")
            return

class TranscribeTab():
    @classmethod
    def create(self, tab: tk.Frame) -> None:  # Transcribeタブの内容作成

        # 初期値設定
        self.canvasitems = []
        self.tabledict = {}

        #
        # フォルダ選択とReloadボタン部分
        #

        # ファイル関係のボタンや入力欄をまとめるフレーム
        self.dir_frame = tk.Frame(tab)
        self.dir_frame.place(x=100, y=0)

        # helpボタンの作成
        text = "書き起こしたいモデルにチェックを入れて startボタンを押してください。 \"✅書き起こし済みのモデルを表示する\"の切り替えでesd.listがすでにあるかどうかを判断して表示を切り替えます。"
        dir_help_window = HelpWindow(content=text)
        dir_help_button = HelpWindow.button_create(self.dir_frame, dir_help_window.display)

        # フォルダの参照用ボタンと表示用入力欄の作成
        self.dir_entry = tk.Entry(self.dir_frame, state="readonly", width=50)
        Tabs.entry_write(str(Path(Jsontools.read_stylepath()).absolute()) + "\\Data", self.dir_entry)

        # リロード用ボタンの作成
        reload_button = tk.Button(self.dir_frame, text="Reload", width=11, command=lambda: self.reload_button_clicked(self))

        # それぞれが横に並ぶように配置
        [j.grid(row=0, column=i) for i, j in enumerate([dir_help_button, self.dir_entry, reload_button])]

        #
        # 読み込んだフォルダと音声ファイル一覧を表で表示する部分の作成
        #

        # 表用のFrameを配置
        self.table_frame = tk.Frame(tab)
        self.table_frame.place(x=65, y=30)

        # Frameに表を表示する用のキャンバスを配置
        self.canvas = tk.Canvas(self.table_frame, width=480,height=230,bg='white')
        self.canvas.grid(row=0, column=0)

        # スクロールバーの作成
        scrollbar = ttk.Scrollbar(self.table_frame,orient=tk.VERTICAL)
        scrollbar.grid(row=0,column=1,sticky='ns')
        scrollbar.config(command=self.canvas.yview)

        self.canvas.config(yscrollcommand=scrollbar.set)
        self.canvas.config(scrollregion=(0,0,0,0))

        # 表の内容を配置する用のフレーム
        self.incanvas_frame = tk.Frame(self.canvas, bg='white')
        self.canvas.create_window((0,0),window=self.incanvas_frame,anchor=tk.NW,width=self.canvas.cget('width'))

        # 列の見出しを配置
        def f(text, column, *, width):
            l = tk.Label(self.incanvas_frame,width=width,text=text,background='white', borderwidth=2, relief=tk.RIDGE)
            l.grid(row=0,column=column,padx=0,pady=0,ipadx=0,ipady=0)
            return l

        f("☐", 0, width=3)
        f("済", 1, width=4)
        f("ModelName", 2, width=60)

        # オプションをまとめる用のFrame
        option_frame = tk.Frame(tab, borderwidth=3, relief=tk.GROOVE)
        option_frame.place(x=67, y=265)

        # すでにesd.listがあるモデルを表示するかのチェックボックス
        self.check_esd = tk.BooleanVar()
        self.check_esd.set(False)
        esd_checkbox = tk.Checkbutton(option_frame, variable=self.check_esd, text="すでに書き起こしが終わっているモデルを表示する", command=lambda: self.reload_button_clicked(self))
        esd_checkbox.grid(row=1, column=1,columnspan=3, sticky=tk.W)

        # 表にあらかじめ読み込んでおく
        self.reload_button_clicked(self)

        #
        # 書き起こしのオプション部分作成
        #

        def f_label(text): return tk.Label(option_frame, text=text, relief=tk.RAISED, bd=1)
        def f_combo(val): return ttk.Combobox(option_frame, values=val, state="readonly")

        # Whisperモデルの選択ドロップダウンリストとラベル
        val = ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']
        self.option_whispermodel_label = f_label("Whisperモデル:")
        self.option_whispermodel = f_combo(val)

        self.option_whispermodel_label.grid(row=2, column=4, sticky=tk.NSEW)
        self.option_whispermodel.grid(row=2, column=5, sticky=tk.NSEW)


        # 計算精度の選択ドロップダウンリストとラベル
        val = ['int8', 'int8_float32', 'int8_float16', 'int8_bfloat16', 'int16', 'float16', 'bfloat16', 'float32']
        self.option_num_label = f_label("計算精度:")
        self.option_num = f_combo(val)

        self.option_num_label.grid(row=3, column=4, sticky=tk.NSEW)
        self.option_num.grid(row=3, column=5, sticky=tk.NSEW)

        # デバイス選択のラジオボタンの作成
        radio_frame1 = tk.Frame(option_frame, relief=tk.RAISED, bd=1)

        self.option_device = tk.StringVar(option_frame)
        device_label = tk.Label(radio_frame1, text="使用するデバイス:")

        def f(text): return tk.Radiobutton(radio_frame1, text=text, variable=self.option_device, value=text)
        self.option_device_cpu = f("cpu")
        self.option_device_cuda = f("cuda")

        device_label.grid(row=1, column=1, sticky=tk.W)
        self.option_device_cpu.grid(row=1, column=2)
        self.option_device_cuda.grid(row=1, column=3, sticky=tk.E)

        radio_frame1.grid(row=2, column=1, columnspan=3, sticky=tk.W+tk.E)

        # 言語選択のラジオボタンの作成
        radio_frame2 = tk.Frame(option_frame, relief=tk.RAISED, bd=1)

        self.option_lang = tk.StringVar(option_frame)
        lang_label = tk.Label(radio_frame2, text="使用する言語:")

        def f(text): return tk.Radiobutton(radio_frame2, text=text, variable=self.option_lang, value=text)
        self.option_lang_ja = f("ja")
        self.option_lang_en = f("en")
        self.option_lang_zh = f("zh")

        lang_label.grid(row=1, column=1, sticky=tk.W)
        self.option_lang_ja.grid(row=1, column=2, sticky=tk.W)
        self.option_lang_en.grid(row=1, column=3)
        self.option_lang_zh.grid(row=1, column=4, sticky=tk.E)

        radio_frame2.grid(row=3, column=1, columnspan=3, sticky=tk.W+tk.E)

        # 初期プロンプト(どのように書き起こしてほしいかの設定)用インプットの作成
        prompt_label = tk.Label(option_frame, text="初期プロンプト(句読点の入れ方・笑い方・固有名詞等、どのように書き起こしてほしいかの設定)")
        self.option_prompt = tk.Entry(option_frame)

        prompt_label.grid(row=4, column=1, columnspan=5, sticky=tk.W)
        self.option_prompt.grid(row=5, column=1, columnspan=5, sticky=tk.W+tk.E)

        # オプションの初期値設定
        trans_settings = Jsontools.read()["transcribe_settings"]
        self.option_device.set(trans_settings["device"])
        self.option_lang.set(trans_settings["lang"])
        self.option_whispermodel.set(trans_settings["whisper"])
        self.option_num.set(trans_settings["num"])
        self.option_prompt.insert(tk.END, trans_settings["prompt"])

        #
        # 開始ボタンの作成
        #

        # 書き起こしの開始ボタン
        slicestart_button = tk.Button(tab, text="書き起こし開始", width=12, command=lambda: self.start_button_clicked(self))
        slicestart_button.place(x=453, y=400)

    # Reloadボタンがクリックされたときの動作
    def reload_button_clicked(self):
        entry_val = self.dir_entry.get()

        if entry_val == "":  # もしフォルダが選ばれてないなら動作しない
            return

        self.input_path = Path(entry_val)

        # Stylebertvits2のdataフォルダ内のフォルダ全取得
        models_folder = [Path(i) for i in glob.glob(str(self.input_path.absolute()) + "/**/")]

        # rawinは中にrawフォルダがあるものだけ、esdinは中にesd.listがあるものだけmodels_folderから取得
        rawin_folder = [i for i in models_folder if glob.glob(str(i) + "/raw/")]
        esdin_folder = [i for i in rawin_folder if glob.glob(str(i) + "/esd.list")]
        rawin_notesd_folder = list(set(rawin_folder) - set(esdin_folder))

        # もしすでにチェックボックスなどがある場合消去する
        if self.canvasitems:
            for i in self.canvasitems:
                i.destroy()
            self.canvasitems = []
            self.tabledict = {}

        # 表に表示する内容の準備
        if not self.check_esd.get():
            table_modelnames = [i.name for i in rawin_notesd_folder]
            table_filetypes = [" " for i in rawin_notesd_folder]
        else:
            table_modelnames = [i.name for i in rawin_notesd_folder] + [i.name for i in esdin_folder]
            table_filetypes = [" " for i in rawin_notesd_folder] + ["済" for i in esdin_folder]

        file_count = int(150/6*(len(table_modelnames)+1))
        self.canvas.config(scrollregion=(0,0,500,file_count))

        for i, value in enumerate(table_modelnames):
            if i%2==0:  # 色ありとなしが交互に出るように
                color='#cdfff7'
            else:
                color='white'

            # チェックボックスの配置
            self.tabledict[value] = tk.BooleanVar()
            self.tabledict[value].set(False)

            c = tk.Checkbutton(self.incanvas_frame, variable=self.tabledict[value], width=0, text='', background='white')
            c.grid(row=i+1, column=0, padx=0, pady=0, ipadx=0, ipady=0, sticky=tk.E)
            self.canvasitems.append(c)

            # Typeとファイルの名前の配置
            def f(i, *, width, text, color, column):
                j = tk.Label(self.incanvas_frame, width=width, text=text, background=color, borderwidth=2, relief=tk.RIDGE)
                j.grid(row=i+1, column=column, padx=0, pady=0, ipadx=0, ipady=0, sticky=tk.W)
                self.canvasitems.append(j)

            f(i, width=4, text=table_filetypes[i], color=color, column=1)
            f(i, width=59, text=table_modelnames[i], color=color, column=2)

    # Startボタンがクリックされたときの動作
    def start_button_clicked(self) -> None:
        if any([i.get() for i in self.tabledict.values()]):  # 表のチェックリストに一つ以上チェックが入っていたら

            transfile_list = [Path(f"{self.input_path}\\{key}").name for key, value in self.tabledict.items() if value.get()]

            # 選択した値を次回起動時にも引き継ぐ
            settings = Jsontools.read()
            trans_settings = settings["transcribe_settings"]
            trans_settings["device"] = self.option_device.get()
            trans_settings["lang"] = self.option_lang.get()
            trans_settings["whisper"] = self.option_whispermodel.get()
            trans_settings["num"] = self.option_num.get()
            trans_settings["prompt"] = self.option_prompt.get()
            Jsontools.write(settings)

            #　書き起こしを実行
            for i in transfile_list:
                 clp.info(f"\"{i}\"の書き起こしを実行しています...")

                 proc = subprocess.Popen([f"python", "transcribe.py",
                                           "--model_name", i,
                                           "--initial_prompt", self.option_prompt.get(),
                                           "--device", self.option_device.get(),
                                           "--language", self.option_lang.get(),
                                           "--model", self.option_whispermodel.get(),
                                           "--compute_type", self.option_num.get()
                                           ], shell=True)

                 result = proc.communicate()

            clp.complete("書き起こしがすべて完了しました。")
            self.reload_button_clicked(self)
            TrainTab.reload_button_clicked(TrainTab)
        else:
            clp.warn("書き起こしたいファイルを1つ以上指定してください。")
            return

class TrainTab():
    @classmethod
    def create(self, tab: tk.Frame):

        #詳細設定ウインドウの初期値設定
        def f(): return tk.IntVar()
        self.process = f()
        self.ver_data = f()
        self.tensorb = f()

        def f(): return tk.BooleanVar()
        self.freeze_en = f()
        self.freeze_ja = f()
        self.freeze_zh = f()
        self.freeze_style = f()
        self.freeze_decoder = f()

        # 初期値設定
        self.canvasitems = []
        self.tabledict = {}

        #
        # フォルダ選択とloadボタン部分
        #

        # ファイル関係のボタンや入力欄をまとめるフレーム
        self.dir_frame = tk.Frame(tab)
        self.dir_frame.place(x=100, y=0)

        # helpボタンの作成
        text = "学習したいモデルを選択して学習開始ボタンで学習を開始します"
        dir_help_window = HelpWindow(text)
        dir_help_button = HelpWindow.button_create(self.dir_frame, dir_help_window.display)

        # フォルダの参照用ボタンと表示用入力欄の作成
        self.dir_entry = tk.Entry(self.dir_frame, state="readonly", width=50)
        Tabs.entry_write(str(Path(Jsontools.read_stylepath()).absolute()) + "\\Data", self.dir_entry)

        # リロード用ボタンの作成
        reload_button = tk.Button(self.dir_frame, text="Reload", width=11, command=lambda: self.reload_button_clicked(self))

        # それぞれが横に並ぶように配置
        [j.grid(row=0, column=i) for i, j in enumerate([dir_help_button, self.dir_entry, reload_button])]

        #
        # 読み込んだフォルダと音声ファイル一覧を表で表示する部分の作成
        #

        # 表用のFrameを配置
        self.table_frame = tk.Frame(tab)
        self.table_frame.place(x=65, y=30)

        # Frameに表を表示する用のキャンバスを配置
        self.canvas = tk.Canvas(self.table_frame, width=480,height=230,bg='white')
        self.canvas.grid(row=0, column=0)

        # スクロールバーの作成
        scrollbar = ttk.Scrollbar(self.table_frame,orient=tk.VERTICAL)
        scrollbar.grid(row=0,column=1,sticky='ns')
        scrollbar.config(command=self.canvas.yview)

        self.canvas.config(yscrollcommand=scrollbar.set)
        self.canvas.config(scrollregion=(0,0,0,0))

        # 表の内容を配置する用のフレーム
        self.incanvas_frame = tk.Frame(self.canvas, bg='white')
        self.canvas.create_window((0,0),window=self.incanvas_frame,anchor=tk.NW,width=self.canvas.cget('width'))

        # 列の見出しを配置
        def f(text, column, *, width):
            l = tk.Label(self.incanvas_frame,width=width,text=text,background='white', borderwidth=2, relief=tk.RIDGE)
            l.grid(row=0,column=column,padx=0,pady=0,ipadx=0,ipady=0)
            return l

        f("☐", 0, width=3)
        f("済", 1, width=4)
        f("ModelName", 2, width=60)

        # オプションをまとめる用のFrame
        option_frame = tk.Frame(tab, borderwidth=3, relief=tk.GROOVE)
        option_frame.place(x=70, y=265)

        # すでにesd.listがあるモデルを表示するかのチェックボックス
        self.check_trained = tk.BooleanVar()
        self.check_trained.set(False)
        esd_checkbox = tk.Checkbutton(option_frame, variable=self.check_trained, text="すでに学習が終わっているモデルを表示する", command=lambda: self.reload_button_clicked(self))
        esd_checkbox.grid(row=1, column=1,columnspan=3, sticky=tk.W)

        # 表にあらかじめ読み込んでおく
        self.reload_button_clicked(self)

        #
        # 学習のオプション部分作成
        #

        # Spinbox作成関数
        def f(*, textvariable, from_, to, increment) -> tk.Spinbox:
            return tk.Spinbox(option_frame,
                              textvariable=textvariable,
                              from_=from_, to=to,
                              width=10,
                              increment=increment,
                              font=TkFont(size=13, weight="bold"),
                              wrap=True)


        # バッチサイズ選択部分作成
        self.option_batchsize = tk.IntVar(option_frame)
        label = tk.Label(option_frame, text="バッチサイズ:")
        batchsize = f(from_=1, to=64, increment=1, textvariable=self.option_batchsize)

        label.grid(row=1, column=4, sticky=tk.W)
        batchsize.grid(row=1, column=5, sticky=tk.E)

        # エポック数部分作成
        self.option_epoch = tk.IntVar(option_frame)
        label = tk.Label(option_frame, text="エポック数:")
        epoch = f(from_=10, to=1000, increment=10, textvariable=self.option_epoch)

        label.grid(row=2, column=4, sticky=tk.W)
        epoch.grid(row=2, column=5, sticky=tk.E)

        # 何ステップごとに結果を保存するかの部分作成
        self.option_step = tk.IntVar(option_frame)
        label = tk.Label(option_frame, text="何ステップごとに保存するか:")
        step = f(from_=100, to=10000, increment=100, textvariable=self.option_step)

        label.grid(row=3, column=4, sticky=tk.W)
        step.grid(row=3, column=5, sticky=tk.E)

        # 音声の音量正規化するのチェックボックス作成
        self.normalize = tk.BooleanVar(option_frame)
        normalize = tk.Checkbutton(option_frame, text="音声の音量を揃える", variable=self.normalize)

        normalize.grid(row=2, column=1, sticky=tk.W)

        # 音声の無音を取り除くのチェックボックス作成
        self.delete_silent = tk.BooleanVar(option_frame)
        delete_silent = tk.Checkbutton(option_frame, text="音声の最初と最後の無音を取り除く", variable=self.delete_silent)

        delete_silent.grid(row=3, column=1, sticky=tk.W)

        # JP-Extra版をつかうのチェックボックス作成
        self.jp_extra = tk.BooleanVar(option_frame)
        jp_extra = tk.Checkbutton(option_frame, text="JP-Extra版を使う", variable=self.jp_extra)

        jp_extra.grid(row=4, column=1, sticky=tk.W)

        # 書き起こしが読めない場合のプルダウンリスト
        label = tk.Label(option_frame, text="書き起こしが読めない場合:")
        val = ["エラー出たらテキスト前処理が終わった時点で中断", "読めないファイルは使わず続行", "読めないファイルも無理やり読んで学習に使う"]
        self.cant_read = ttk.Combobox(option_frame, state="readonly", values=val)

        label.grid(row=5, column=1, sticky=tk.W)
        self.cant_read.grid(row=5, column=2, columnspan=4, sticky=tk.W+tk.E)

        # それぞれのオプションの初期値をsettings.jsonから読み込んで設定
        train_settings = Jsontools.read()["Train_settings"]

        self.jp_extra.set(train_settings["jp_extra"])
        self.option_batchsize.set(train_settings["batch_size"])
        self.option_epoch.set(train_settings["epoch"])
        self.option_step.set(train_settings["step"])
        self.normalize.set(train_settings["normalize"])
        self.delete_silent.set(train_settings["delete_silent"])
        self.cant_read.set(train_settings["cant_read_file"])
        self.process.set(train_settings["process"])
        self.ver_data.set(train_settings["ver_data"])
        self.tensorb.set(train_settings["tensorb"])
        self.freeze_en.set(train_settings["freeze_en"])
        self.freeze_ja.set(train_settings["freeze_ja"])
        self.freeze_zh.set(train_settings["freeze_zh"])
        self.freeze_style.set(train_settings["freeze_style"])
        self.freeze_decoder.set(train_settings["freeze_decoder"])

        #
        # 詳細設定ボタンとそのウインドウ作成
        #

        advanced_button = tk.Button(tab, text="詳細設定", width=12, command=lambda: self.open_advanced_setting(self))
        advanced_button.place(x=350, y=400)

        #
        # 開始ボタンの作成
        #

        # 学習の開始ボタン
        slicestart_button = tk.Button(tab, text="学習開始", width=12, command=lambda: self.start_button_clicked(self))
        slicestart_button.place(x=453, y=400)

    # Reloadボタンがクリックされたときの動作
    def reload_button_clicked(self):
        entry_val = self.dir_entry.get()

        if entry_val == "":  # もしフォルダが選ばれてないなら動作しない
            return

        self.input_path = Path(entry_val)

        models_folder = [Path(i).name for i in glob.glob(str(self.input_path.absolute()) + "/**/")]
        inesd_models_folder = [i for i in models_folder if Path(f"{entry_val}/{i}/esd.list").exists()]
        trained_folder = [Path(i).name for i in glob.glob(Jsontools.read_stylepath() + "/model_assets/**/")]

        # まだ学習していないモデル名だけ取得
        not_trained_models = list(set(inesd_models_folder) - set(trained_folder))
        indata_trained_models = list(set(inesd_models_folder) & set(trained_folder))

        # もしすでにチェックボックスなどがある場合消去する
        if self.canvasitems:
            for i in self.canvasitems:
                i.destroy()
            self.canvasitems = []
            self.tabledict = {}

        # 表に表示する内容の準備
        if not self.check_trained.get():
            table_modelnames = [i for i in not_trained_models]
            table_filetypes = [" " for i in not_trained_models]
        else:
            table_modelnames = [i for i in not_trained_models] + [i for i in indata_trained_models]
            table_filetypes = [" " for i in not_trained_models] + ["済" for i in indata_trained_models]

        file_count = int(150/6*(len(table_modelnames)+1))
        self.canvas.config(scrollregion=(0,0,500,file_count))

        for i, value in enumerate(table_modelnames):
            if i%2==0:  # 色ありとなしが交互に出るように
                color='#cdfff7'
            else:
                color='white'

            # チェックボックスの配置
            self.tabledict[value] = tk.BooleanVar()
            self.tabledict[value].set(False)

            c = tk.Checkbutton(self.incanvas_frame, variable=self.tabledict[value], width=0, text='', background='white')
            c.grid(row=i+1, column=0, padx=0, pady=0, ipadx=0, ipady=0, sticky=tk.E)
            self.canvasitems.append(c)

            # Typeとファイルの名前の配置
            def f(i, *, width, text, color, column):
                j = tk.Label(self.incanvas_frame, width=width, text=text, background=color, borderwidth=2, relief=tk.RIDGE)
                j.grid(row=i+1, column=column, padx=0, pady=0, ipadx=0, ipady=0, sticky=tk.W)
                self.canvasitems.append(j)

            f(i, width=4, text=table_filetypes[i], color=color, column=1)
            f(i, width=59, text=table_modelnames[i], color=color, column=2)

    # 学習開始ボタンがクリックされたときの動作
    def start_button_clicked(self) -> None:
        if any([i.get() for i in self.tabledict.values()]):  # 表のチェックリストに一つ以上チェックが入っていたら
            train_modellist = [Path(f"{self.input_path}\\{key}").name for key, value in self.tabledict.items() if value.get()]

            # 選択した値を次回起動時にも引き継ぐ
            settings = Jsontools.read()
            train_settings = settings["Train_settings"]

            train_settings["jp_extra"] = self.jp_extra.get()
            train_settings["batch_size"] = self.option_batchsize.get()
            train_settings["epoch"] = self.option_epoch.get()
            train_settings["step"] = self.option_step.get()
            train_settings["normalize"] = self.normalize.get()
            train_settings["delete_silent"] = self.delete_silent.get()
            train_settings["cant_read_file"] = self.cant_read.get()
            train_settings["process"] = self.process.get()
            train_settings["ver_data"] = self.ver_data.get()
            train_settings["tensorb"] = self.tensorb.get()
            train_settings["freeze_en"] = self.freeze_en.get()
            train_settings["freeze_ja"] = self.freeze_ja.get()
            train_settings["freeze_zh"] = self.freeze_zh.get()
            train_settings["freeze_style"] = self.freeze_style.get()
            train_settings["freeze_decoder"] = self.freeze_decoder.get()

            Jsontools.write(settings)

            # 学習のオプション用変数を準備
            yomi_error_dict = {"エラー出たらテキスト前処理が終わった時点で中断": "raise",
                               "読めないファイルは使わず続行": "skip",
                               "読めないファイルも無理やり読んで学習に使う": "use"}

            yomi_error = yomi_error_dict[self.cant_read.get()]

            #　学習を実行
            for i in train_modellist:
                process_list = [f"python", "preprocess_all.py",
                                "-m", str(i),
                                "-b", str(self.option_batchsize.get()),
                                "-e", str(self.option_epoch.get()),
                                "-s", str(self.option_step.get()),
                                "--num_processes", str(self.process.get()),
                                "--log_interval", str(self.tensorb.get()),
                                "--yomi_error", yomi_error]

                process_dict = {self.normalize.get(): "--normalize",
                                self.delete_silent.get(): "--trim",
                                self.freeze_en.get(): "--freeze_EN_bert",
                                self.freeze_ja.get(): "--freeze_JP_bert",
                                self.freeze_zh.get(): "--freeze_ZH_bert",
                                self.freeze_style.get(): "--freeze_style",
                                self.freeze_decoder.get(): "--freeze_decoder",
                                self.jp_extra.get(): "--use_jp_extra"}

                [process_list.append(val) for key, val in list(process_dict.items()) if key]

                clp.info(f"\"{i}\"の前処理を実行しています...")
                proc = subprocess.Popen(process_list, shell=True)
                result = proc.communicate()
                clp.info(f"モデル: {i} を学習中...")

                if self.jp_extra.get():
                    proc = subprocess.Popen([f"python", "train_ms_jp_extra.py"], shell=True)
                    result = proc.communicate()
                else:
                    proc = subprocess.Popen([f"python", "train_ms.py"], shell=True)
                    result = proc.communicate()

            clp.complete("すべての学習が完了しました。")
            self.reload_button_clicked(self)

        else:
            clp.warn("学習するモデルを1つ以上指定してください。")
            return

    def open_advanced_setting(self):
        advanced_window = tk.Toplevel(root)
        advanced_window.title("Advanced Settings")
        advanced_window.geometry("275x220")
        advanced_window.resizable(0, 0)
        advanced_window.attributes("-topmost", True)

        # Xや-をクリックで閉じれないように
        advanced_window.protocol("WM_DELETE_WINDOW", (lambda: 'pass')())

        guard_window = HelpWindow()
        guard_window.guard_window()

        # オプションをまとめる用のフレーム作成
        advanced_frame = tk.Frame(advanced_window)
        advanced_frame.place(x=10, y=10)

        # spinboxを作るための関数
        def f_label(text): return tk.Label(advanced_frame, text=text)

        def f_spinbox(*, from_, to, increment, textvariable):
            return tk.Spinbox(advanced_frame,
                              textvariable=textvariable,
                              from_=from_, to=to,
                              width=10,
                              increment=increment,
                              font=TkFont(size=13, weight="bold"),
                              wrap=True)

        # プロセス数の部分作成
        label = f_label("プロセス数:")
        process = f_spinbox(from_=1, to=192, increment=1, textvariable=self.process)

        label.grid(row=1, column=1, sticky=tk.W)
        process.grid(row=1, column=2, sticky=tk.E)

        # 検証データ数の部分作成
        label = f_label("検証データ数:")
        ver_data = f_spinbox(from_=0, to=100, increment=1, textvariable=self.ver_data)

        label.grid(row=2, column=1, sticky=tk.W)
        ver_data.grid(row=2, column=2, sticky=tk.E)

        # Tensorboardのログ出力間隔部分作成
        label = f_label("Tensorboardのログ出力間隔:")
        tensorb = f_spinbox(from_=10, to=1000, increment=10, textvariable=self.tensorb)

        label.grid(row=3, column=1, sticky=tk.W)
        tensorb.grid(row=3, column=2, sticky=tk.E)

        # Checkbox作成用関数
        def f_check(text, *, variable): return tk.Checkbutton(advanced_frame, onvalue=True, offvalue=False, text=text, variable=variable)

        # それぞれのbert部分を凍結チェックボックスを作成
        freeze_en = f_check("英語bert部分を凍結", variable=self.freeze_en)
        freeze_ja = f_check("日本語bert部分を凍結", variable=self.freeze_ja)
        freeze_zh = f_check("中国語bert部分を凍結", variable=self.freeze_zh)
        freeze_style = f_check("スタイル部分を凍結", variable=self.freeze_style)
        freeze_decoder = f_check("デコーダ部分を凍結", variable=self.freeze_decoder)

        # それぞれを縦に並ぶように配置
        freezelist = [freeze_en, freeze_ja, freeze_zh, freeze_style, freeze_decoder]
        def f(i, j): j.grid(row=4+i, column=1, sticky=tk.W)
        [f(i, j) for i, j in enumerate(freezelist)]

        # 閉じる用のOKボタンを配置
        button = tk.Button(advanced_frame, text="閉じる", width=10, command=lambda: okbutton_clicked())
        button.grid(row=8, column=2, sticky=tk.W+tk.E)

        # OKボタンが押されたときに閉じる
        def okbutton_clicked():
            advanced_window.destroy()
            guard_window.ok_button_clicked()

class Jsontools():
    @classmethod
    def read(self) -> dict:
        with open(f'{programdir}/settings.json', "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def write(self, data: dict) -> None:
        with open(f'{programdir}/settings.json', 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # shellが空白が含まれているjsonファイルの値を取り出せないので
    # 入力されたStyleBertVITS2のパスに空白が含まれていた場合に対処するために
    # 空白をアンダーバー2つに置換してjsonに書き込んでいるので取り出すときは
    # アンダーバー2つを空白に置き換えて取り出す
    # read()["style_path"]でパスを取り出してはいけない

    # -> 取り出しにread_stylepath.pyからの戻り値を取得するようにしたのでこの必要はなくなりました

    @classmethod
    def read_stylepath(self) -> str:
        settings = self.read()
        r = settings["style_path"]
        return r

    @classmethod
    def write_stylepath(self, path: str) -> None:
        settings = self.read()
        settings["style_path"] = path
        self.write(settings)

if __name__ == "__main__":
    #メインウインドウの作成
    root = tk.Tk()
    root.title("GUI for Style-Bert-VITS2 Train")
    root.geometry("640x480")
    root.resizable(0, 0)

    # SlicesタブとTranscribeタブ、Trainsタブの作成
    notebook = ttk.Notebook(root)
    notebook.pack(expand=1, fill='both')

    def f(): return tk.Frame(notebook)
    slices_tab, transcribe_tab, trains_tab = f(), f(), f()

    tab_dict = {slices_tab: "Slice",
                transcribe_tab: "Transcribe",
                trains_tab: "Trains"}

    [notebook.add(key, text=value, padding=4) for key, value in tab_dict.items()]

    # それぞれのタブの内容作成
    SlicesTab.create(slices_tab)
    TranscribeTab.create(transcribe_tab)
    TrainTab.create(trains_tab)

    root.mainloop()