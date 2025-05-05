import os
import re
import openai
import datetime
from dotenv import load_dotenv

from pprint import pprint
from collections import defaultdict

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# ファイルのアクセス権を管理するライブラリを読み込む
# Linuxでしか使えないので、Windows環境用に制御
# ただし、アクセス権の管理が行えないのでテスト時限定とする
try:
    import fcntl

    isFcntl = True
    logPath = "/home/klab/data/cl-chat/log/log.tsv"
except:
    isFcntl = False
    logPath = "./log.tsv"


import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 環境変数の読み込み
load_dotenv()

# APIキーの設定
spreadSheetKey = os.getenv('SPREADSHEET_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
openai.api_key = os.getenv('OPENAI_API_KEY')

def connectSheet():
    # 認証処理
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(os.getcwd(), "gss_credential.json"),
                                                                   scope)
    authorize = gspread.authorize(credentials)

    # 対象のシートにアクセスする
    target_data = authorize.open("辞書定義")
    sheet = target_data.worksheet("シート1").get_all_values()

    return sheet


def filteringChoices(sheet, userInput):
    """
    ユーザーのことを考えれば、全てのキーワードがマッチしたものに限って返すべき
    それがない場合のみ、OR検索をする方が良い

    """

    # ユーザー入力と、シートのTitle列が一致したら、それを返す
    res = equalMatching(sheet, userInput)
    if res != []:
        # print("equal")
        return res

    userInput = userInput.lower()  # 大文字小文字の表記ゆれに対処する

    # 全てのキーワードがマッチしたら、それを返す
    res = andFiltering(sheet, userInput)
    if res != []:
        # print("and")
        return res

    # 完全マッチが無かったので、OR検索で絞り込みを促す
    res = orFiltering(sheet, userInput)
    # print("or")

    return res


def equalMatching(sheet, userInput):
    # userInputがシートのTitle列と一致したら、それを返す
    for i in range(len(sheet)):
        row = sheet[i]
        if userInput == row[1]:
            return [row]

    return []


def orFiltering(sheet, userInput):
    res = []

    for i in range(1, len(sheet)):
        row = sheet[i]

        keywords = row[2]
        if not isinstance(keywords, list):
            keywords = keywords.split(",")

        # 選択肢の絞り込み
        for keyword in keywords:
            if keyword.lower() in userInput:
                res.append(row)
                break
    return res


def andFiltering(sheet, userInput):
    print("t",sheet)
    print("q",userInput)
    res = []
    matchResult = defaultdict(list)

    # 一致しなかったら、キーワードのAND検索
    for row in sheet[1:]:
        keywords = row[2]

        # キーワード列をリストに変換する
        if not isinstance(keywords, list):
            keywords = keywords.split(",")

        regex = "^"
        for keyword in keywords:
            regex += f"(?=.*{keyword.lower()}.*)"
        regex += ".*$"

        if re.match(regex, userInput):
            matchResult[len(keywords)].append(row)

    if len(matchResult) == 0:
        return []

    maxCount = max(matchResult.keys())
    matches = matchResult[maxCount]
    if len(matches) == 0:
        return []
    elif len(matches) == 1:
        return matches
    else:
        for row in matches:
            res.append(row)
        return res


def useGemini(userInput):
    try:
        # API-KEYの設定
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_pro = genai.GenerativeModel("gemini-pro")
        prompt = userInput
        response = gemini_pro.generate_content(prompt)
        ai_res = response.text
        return True, ai_res
    except ResourceExhausted:
        return False, "アクセスが集中しています。数分後にもう一度最初から質問してください"


# openai
def useChatGPT(userInput):
    # prompt = "以下の【】の中の質問に答えてください。また、提示する条件を守って出力してください。" \
    #         "条件1：回答は100〜150文字以内とする。" \
    #         "条件2：機械的に提示してください" \
    #         "条件3：前の質問の内容は引き継がず、入力された質問だけを、答える対象としてください" \
    #         "\n【" + userInput + "】"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k-0613",
            messages=[
                {"role": "user", "content": userInput}
            ],
            temperature=0,
            request_timeout=30
        )
        return response['choices'][0]['message']['content']
    except openai.error.Timeout:
        return "1", "Timeout"
    except:
        return "0", "GPTへのリクエストでエラーが発生"


def writeLog(userID, userInput, message):
    # 日時を取得
    dt_now = datetime.datetime.now()
    time = dt_now.strftime('%Y/%m/%d %H:%M:%S')

    # ChatBotからの出力を整形する
    # 改行を消す
    message = message.replace("\r\n", "")
    message = message.replace("\n", "")
    message = message.replace("\r", "")

    with open(logPath, 'a', encoding="utf-8") as f:
        if (isFcntl):
            fcntl.flock(f, fcntl.LOCK_EX)  # ファイルのアクセス権を独占
            f.write(f"{time}\t{userID}\t{userInput}\t{message}\n")
            fcntl.flock(f, fcntl.LOCK_UN)  # アクセス権を放棄
        else:
            f.write(f"{time}\t{userID}\t{userInput}\t{message}\n")


if __name__ == "__main__":
    sheet = connectSheet()
    pprint(filteringChoices(sheet, "ログインできない"))
