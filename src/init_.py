import sys
import time
import json
from pathlib import Path

from ColorPrint import Existing as cl

class Jsontools():
    @classmethod
    def read(self) -> dict:
        with open('settings.json', "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def write(self, data: dict) -> None:
        with open('settings.json', 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

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

    @classmethod
    def create(self):
        with open('settings.json', "w", encoding="utf-8") as f:
            data = {
                        "style_path": "",
                        "slice_settings": {
                            "open_path": "",
                            "min_sec": 2.0,
                            "max_sec": 12.0,
                            "min_silence_dur_ms": 700
                        },
                        "transcribe_settings": {
                            "device": "cuda",
                            "lang": "ja",
                            "whisper": "large-v3",
                            "num": "bfloat16",
                            "prompt": "こんにちは。元気、ですかー？ふふっ、私は……ちゃんと元気だよ！"
                        },
                        "Train_settings": {
                            "jp_extra": True,
                            "batch_size": 2,
                            "epoch": 100,
                            "step": 1000,
                            "normalize": False,
                            "delete_silent": False,
                            "cant_read_file": "エラー出たらテキスト前処理が終わった時点で中断",
                            "process": 6,
                            "ver_data": 0,
                            "tensorb": 200,
                            "freeze_en": False,
                            "freeze_ja": False,
                            "freeze_zh": False,
                            "freeze_style": False,
                            "freeze_decoder": False
                        }
                    }

            json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":

    if not Path("settings.json").exists():
        Jsontools.create()

    settings = Jsontools.read()
    style_path = Jsontools.read_stylepath()
    checklist = ["\\venv\\Scripts\\activate", "\\slice.py", "\\transcribe.py", "\\preprocess_all.py", "\\train_ms.py", "\\train_ms_jp_extra.py"]

    if not all([Path(style_path + i).exists() for i in checklist]):

        while True:
            input_ = input(f"{'-'*50}\n初期設定を行います。\nStyle-Bert-VITS2があるパスを入力してください。\n例: C:/ExampleFolder/Style-Bert-VITS2\n{'-'*50}\nPath: ")
            input_path = str(Path(input_).absolute())

            if all([Path(input_path + i).exists() for i in checklist]):
                input_path = input_path.replace("\\", "/")
                Jsontools.write_stylepath(input_path)
                break
            else:
                cl.error("Style-bert-VITS2のパスを指定してください。")
                time.sleep(2)