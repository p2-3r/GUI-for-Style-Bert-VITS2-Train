# GUI-for-Style-Bert-VITS2-Train

Style-Bert-VITSのCLIを使ったプログラムです。

> [!NOTE]
>
> ※仮想環境内にtkinterがなく起動できない場合があるみたいです。
>
> Style-Bert-VITS2の "GitやPythonに馴染みが無い方" の方法で
>
> それがインストールされているとtkinterがなく起動できないかもしれません。

## アップデート情報

<img src="https://github.com/p2-3r/GUI-for-Style-Bert-VITS2-Train/assets/159620178/2bf2a2a1-95a7-4878-8769-e5499cf061da" width="500">

書き起こしテキスト(esd.list)の編集機能を付けました！

これで音源を用意すればこのツールで学習準備から学習まで完結します

## 機能紹介

### スライス、書き起こし、学習の連続実行

音声のスライス、書き起こし、モデルの学習を行いたいものをまとめて選択して連続で実行してくれます。

1つのモデルの学習が終わるたびにモデルの学習を開始させるためにクリックする手間を省けます。

スライス -> 書き起こしの自動実行も対応しています。

### 学習時に選んだオプションの記憶機能

スライスや書き起こしの秒数オプションや初期プロンプトなどを記憶して次回起動時に引き継いでくれます。

毎回オプションを選択する手間を省けます。

## 起動時の画面紹介

<img src="https://github.com/p2-3r/GUI-for-Style-Bert-VITS2-Train/assets/159620178/c1821fb7-ee58-49f5-aad7-df546b938a5a" width="330">
<img src="https://github.com/p2-3r/GUI-for-Style-Bert-VITS2-Train/assets/159620178/6f487146-f1f9-475c-8e79-c3a93b54dd84" width="330">
<img src="https://github.com/p2-3r/GUI-for-Style-Bert-VITS2-Train/assets/159620178/7d93a6c4-eca9-46b0-a38b-1d9c24bed1f3" width="330">

## 起動環境

Style-Bert-VITS2 (Version: 2.3)

Python (3.10.9で動作確認)

## 起動方法

```
git clone https://github.com/p2-3r/GUI-for-Style-Bert-VITS2-Train.git
```
このリポジトリをダウンロードします。

起動するには "run.bat" を起動します。

## 初期設定

起動するとまずStyle-Bert-VITS2のパスを聞いてくるのでパスを入力します。

※間違っていた場合もう一度聞いてくるので違うパスを入力してしまったりしても大丈夫です。

## 使用方法

Sliceの場合はFileボタンからパスを選択してLoadボタンを押します。

スライス、書き起こし、学習したいものにチェックを入れて開始のボタンを押します。

複数選んでいた場合は自動で連続で実行してくれます。

学習を実行した際にオプションをjsonファイルに記憶して次回起動時に引き継ぎます。

## 書き起こしテキスト(esd.list) 編集ツール

<img src="https://github.com/p2-3r/GUI-for-Style-Bert-VITS2-Train/assets/159620178/2bf2a2a1-95a7-4878-8769-e5499cf061da" width="330">

<img src="https://github.com/p2-3r/GUI-for-Style-Bert-VITS2-Train/assets/159620178/9e49f1ff-3fe7-4a9f-b9e7-b341881c1499" width="330">

いろいろな機能がついてます。

### 音声再生機能

表から選ぶと、音声が再生され下の入力欄を書き換えてEnterを押すだけで書き起こしテキストを編集できます

### 移動操作

Ctrl+U or I で左右に移動できます

### 10個のコピー置き場、置換機能、ショートカットキーで話者を書き換え

あらかじめ入力しておけばそこから呼び出して、

貼り付け、文章全体の置換、話者の選択

を行うことができます。

### ファイル選別機能

いらないと思ったファイルは Ctrl + Shift + D で消去できます。

対応する書き起こしテキストの部分も消えてくれます。

間違っても一回までなら Ctrl + Shift + S で戻せます。

## アップデート

update.batを起動するとアップデートすることができます。

## 参考

書き起こしテキスト編集ツールを作る際、

seichi042Iさんの "transcribe_tool" を参考にさせていただきました。

https://github.com/seichi042I/transcribe_tool

## 予定

このツールはStyle-Bert-VITS2の仮想環境を借りて起動してるので

そうじゃない方法で新しく仮想環境を作って起動できるようにしたい
