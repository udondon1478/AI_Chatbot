import openai
from speech_to_text import speech_to_text
from text_to_speech import text_to_speech

# OpenAIのAPIキーを設定
openai.api_key = ""

# テンプレートの準備
template = """あなたはどんな文章も指定された方言や敬語に正すAIです、入力された文章を関西弁、もしくは敬語に変換したものを返してください。
制約:
- 入出力は日本語を用います
- 入力された文章を適切な形に変換した状態でオウム返しをしてください
- 最初に関西弁に変換するか、敬語に変換するかの選択肢を提供してください
- 敬語に変換できない語句が入力された場合は、その語句をそのまま返してください
- 会話をするのではなく入力された文章を変換するのみが目的です"""

# メッセージの初期化
messages = [{"role": "system", "content": template}]

# ユーザーからのメッセージを受け取り、それに対する応答を生成
while True:
    # 音声をテキストに変換
    user_message = speech_to_text()

    # テキストが空の場合は処理をスキップ
    if user_message == "":
        continue

    print("あなたのメッセージ: \n{}".format(user_message))
    messages.append({"role": "user", "content": user_message})
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    bot_message = response["choices"][0]["message"]["content"]
    print("チャットボットの回答: \n{}".format(bot_message))

    # テキストを音声に変換して再生
    text_to_speech(bot_message)

    messages.append({"role": "assistant", "content": bot_message})
