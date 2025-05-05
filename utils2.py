import re
import unicodedata
import requests as req
import json
import datetime
import os
from dotenv import load_dotenv

from pprint import pprint

from utils import spreadSheetKey

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

try:
    import fcntl

    isFcntl = True
    logPath = "/home/klab/data/cl-chat/log/{}.tsv"
except:
    isFcntl = False
    logPath = "./log/{}.tsv"

# 環境変数の読み込み
load_dotenv()

# APIキーの設定
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

def connectSheet(id, name):
    res = req.get(f"https://sheets.googleapis.com/v4/spreadsheets/{id}/values/{name}?key={spreadSheetKey}")
    table = json.loads(res.text)["values"][1:]
    return table


def standardize_text(text, summary):
    """標準化する処理を行う関数"""
    text = re.sub(r"\s", "", text)  # 空白除去
    text = unicodedata.normalize('NFKC', text)  # 半角に変換
    text = text.lower()  # 小文字に変換
    for pattern, replacement in summary:
        text = re.sub(pattern, replacement, text)
    return text


def standardization(s, synonyms):
    # ファイルのパス
    pattern_file_path = 'database.txt'
    # ファイルから読み込む
    # 正規化のデータベース[（前,後）]
    summary = []
    with open(pattern_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            columns = line.strip().split('\t')
            replacement = columns[0]
            targets = columns[1:]
            for target in targets:
                summary.append((target, replacement))

    # 入力文字列を正規化
    s = standardize_text(s, summary)

    # synonymsの各要素を正規化
    normalized_synonyms = []
    for pair in synonyms:
        normalized_pair = [standardize_text(pair[0], summary)]
        for target in pair[1:]:
            normalized_pair.append(standardize_text(target, summary))
        normalized_synonyms.append(normalized_pair)

    # 同義語辞書とユーザー入力orキーワードをマッチング
    for pair in normalized_synonyms:
        replacement = pair[0]
        targets = pair[1:]
        for target in targets:
            s = s.replace(target, replacement)
    return s

def filtering(s, responseSheet, synonymDictSheet):
    # ボタンを押して質問した場合の処理
    # この処理が無いと無限に選択肢が出てくる

    # これまでの入力の最新だけ見る
    ss = s.split("。")
    ss = ss[-1] if ss[-1] != "" else ss[-2]
    for row in responseSheet:
        if len(row) != 6:
            row += ["", "F"]
        id, title, keyword, answer, additional, useAI = row

        if title == ss:
            # print("title matched")
            return [row]

    # ボタンが押されていない or 一番最初のボタンだったら絞り込み
    matchResult = {}
    print(s)
    s = standardization(s, synonymDictSheet)
    for row in responseSheet:
        if len(row) != 6:
            row += ["", "F"]
        id, title, keyword, answer, additional, useAI = row

        keyword = standardization(keyword, synonymDictSheet)
        keyword = set(keyword.split(","))
        c = sum([(key in s) for key in keyword])  # 含まれるキーワードをカウント
        p = c / len(keyword)
        #print(s)
        #print(p)
        #print(keyword)
        #print(len(keyword))

        if p not in matchResult:
            matchResult[p] = []
        matchResult[p].append(row)
    #print(matchResult)
    percent = sorted(list(map(float, matchResult.keys())), reverse=True)
    # pprint(matchResult)
    if len(percent) == 1:
        return []
    # print(percent)

    res = []
    c = 0
    for p in percent:
        if p == 0:
            break
        for row in matchResult[p]:
            if c >= 10:
                break
            res.append(row)
            c += 1
    return res

def useGemini(userInput):
    print(userInput)
    try:
        gemini_pro = genai.GenerativeModel("gemini-pro")
        prompt = "以下の【】の質問・不明点について100字以内で簡潔に回答してください。また、条件に合った回答をしてください。書き出す時に必ず「AIParrotが返答します」と記述し,改行してください" \
                 "条件1：箇条書きにしないでください。" \
                 "条件2：文章中にURLは含めないでください。" \
                 "条件3：PC操作の初心者でも分かることだけを書いてください。" \
                 "条件4：特に、以下のような要素については使わせない、触らせない内容にしてください。" \
                 "・コマンドプロンプトやBIOSなどの高度な内容" \
                 "\n【" + userInput + "】"
        response = gemini_pro.generate_content(prompt)
        ai_res = response.text
        return True, ai_res
    except ResourceExhausted:
        return False, "アクセスが集中しています。数分後にもう一度最初から質問してください"

def writeLog(userID, userInput, message, responseSheetID):
    # 日時を取得
    dt_now = datetime.datetime.now()
    time = dt_now.strftime('%Y/%m/%d %H:%M:%S')

    # ChatBotからの出力を整形する
    # 改行を消す
    message = message.replace("\r\n", "")
    message = message.replace("\n", "")
    message = message.replace("\r", "")
    version = "2.9"

    with open(logPath.format(responseSheetID), 'a', encoding="utf-8") as f:
        if (isFcntl):
            fcntl.flock(f, fcntl.LOCK_EX)  # ファイルのアクセス権を独占
            f.write(f"{time}\t{userID}\t{userInput}\t{message}\t{version}\n")
            fcntl.flock(f, fcntl.LOCK_UN)  # アクセス権を放棄
        else:
            f.write(f"{time}\t{userID}\t{userInput}\t{message}\t{version}\n")
