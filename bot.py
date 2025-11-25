import os
import re
import asyncio
import discord
from openai import OpenAI

# ==========================
#  環境変数からAPIキーを取得
# ==========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 翻訳を実行するチャンネルIDを入れる
TARGET_CHANNEL_IDS = [
    1439316912646389822,
    1423699794781536377,
]

# ==========================
# Discord クライアント設定
# ==========================
intents = discord.Intents.default()
intents.message_content = True  # これがないとメッセージ読めない
client = discord.Client(intents=intents)

# OpenAI クライアント設定
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# ==========================
# 日本語 / 韓国語の簡易判定
# ==========================
def detect_lang(text: str) -> str:
    """ざっくり日本語 / 韓国語 / その他 を判定する"""

    # ひらがな・カタカナ・漢字が含まれていたら日本語とみなす
    if re.search(r"[\u3040-\u30ff\u4e00-\u9faf]", text):
        return "ja"

    # ハングルが含まれていたら韓国語とみなす
    if re.search(r"[\uac00-\ud7af]", text):
        return "ko"

    # それ以外は対象外
    return "other"


# ==========================
# 自動 翻訳 関数（日本語⇔韓国語）
# ==========================
async def translate_ja_ko_auto(text: str, lang: str) -> str:
    """
    lang が 'ja' のとき: 日本語 → 韓国語
    lang が 'ko' のとき: 韓国語 → 日本語
    それ以外: そのまま返す
    """

    if lang == "ja":
        system_content = (
            "You are a professional translator from Japanese to Korean.\n"
            "The user input will be in Japanese.\n"
            "Translate it into natural, conversational Korean.\n"
            "Respond with ONLY the translated Korean text."
        )
    elif lang == "ko":
        system_content = (
            "You are a professional translator from Korean to Japanese.\n"
            "The user input will be in Korean.\n"
            "Translate it into natural, conversational Japanese.\n"
            "Respond with ONLY the translated Japanese text."
        )
    else:
        # 対象外言語
        return text

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("翻訳APIエラー:", e)
        return "(翻訳中にエラーが発生しました)"


# ==========================
# BOT 起動イベント
# ==========================
@client.event
async def on_ready():
    print(f"ログイン成功: {client.user} (ID: {client.user.id})")


# ==========================
# メッセージ受信時の処理
# ==========================
@client.event
async def on_message(message):
    # 自分や他のBOTの発言は無視
    if message.author.bot:
        return

    # 翻訳対象チャンネルだけ処理する
    if TARGET_CHANNEL_IDS and message.channel.id not in TARGET_CHANNEL_IDS:
        return

    text = message.content.strip()
    if not text:
        return

    # 日本語 / 韓国語 以外はそもそも翻訳しない
    lang = detect_lang(text)
    if lang == "other":
        return

    translated = await translate_ja_ko_auto(text, lang)

    # 念のため、翻訳結果が空なら送らない
    if not translated:
        return

    try:
        await message.reply(f"🐨 自動翻訳:\n{translated}", mention_author=False)
    except Exception as e:
        print("送信エラー:", e)


# ==========================
# メイン関数
# ==========================
def main():
    if not DISCORD_TOKEN:
        print("環境変数 DISCORD_TOKEN が設定されていません")
        return
    if not OPENAI_API_KEY:
        print("環境変数 OPENAI_API_KEY が設定されていません")
        return

    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
