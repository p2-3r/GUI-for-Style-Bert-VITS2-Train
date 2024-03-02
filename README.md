# GUI-for-Style-Bert-VITS2-Train

Style-Bert-VITSのCLIを使ったプログラムです。

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

## 予定

アップデートで書き起こしテキスト(esd.list)の編集機能を付ける予定です。

(音源を用意したらこのツール上で学習準備から学習が完結するようにしたい)
