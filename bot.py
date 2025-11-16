import os
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
    1423699794781536377
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
# 自動 翻訳 関数（日本語⇔韓国語）
# ==========================
async def translate_ja_ko_auto(text: str) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # 高精度で安定
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a translator for Japanese and Korean.\n"
                        "1. Detect whether the user text is Japanese or Korean.\n"
                        "2. If Japanese → translate to natural Korean.\n"
                        "3. If Korean → translate to natural Japanese.\n"
                        "4. If neither, return the text unchanged.\n"
                        "Respond with ONLY the translation text."
                    ),
                },
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

    translated = await translate_ja_ko_auto(text)

    # 判定で翻訳されなかった場合は送らない
    if translated == text:
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


