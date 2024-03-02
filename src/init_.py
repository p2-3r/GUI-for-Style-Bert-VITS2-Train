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

if __name__ == "__main__":

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