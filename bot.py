import os
import discord

from dotenv import load_dotenv
from discord.ext import tasks, commands
from discord import app_commands
from datetime import datetime, timedelta


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

TODAY_CHANNEL_ID = int(
    os.getenv("TODAY_CHANNEL_ID")
)

TOMORROW_CHANNEL_ID = int(
    os.getenv("TOMORROW_CHANNEL_ID")
)


ROTATION = [
    "봉바",
    "쇄빙",
    "온살",
    "워치",
    "봉바",
    "제압",
    "온살",
    "워치"
]


ROTATION_START = datetime(
    2026, 5, 2
)


intents = discord.Intents.default()


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


def get_frontline_by_date(target_date):

    passed_days = (
        target_date.date()
        - ROTATION_START.date()
    ).days

    index = (
        passed_days
        % len(ROTATION)
    )

    return ROTATION[index]


def get_frontline():

    now = (
        datetime.utcnow()
        + timedelta(hours=9)
    )

    current_map = (
        get_frontline_by_date(now)
    )

    next_map = (
        get_frontline_by_date(
            now + timedelta(days=1)
        )
    )

    tomorrow = (
        now + timedelta(days=1)
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    remain = tomorrow - now

    hours, remainder = divmod(
        remain.seconds,
        3600
    )

    minutes, _ = divmod(
        remainder,
        60
    )

    remain_text = (
        f"{hours}시간 "
        f"{minutes}분 남음"
    )

    return (
        current_map,
        next_map,
        remain_text
    )


@tasks.loop(minutes=10)
async def update_channels():

    current_map, next_map, remain = (
        get_frontline()
    )

    today_channel = bot.get_channel(
        TODAY_CHANNEL_ID
    )

    tomorrow_channel = bot.get_channel(
        TOMORROW_CHANNEL_ID
    )

    if today_channel:

        await today_channel.edit(
            name=f"오늘 전장：{current_map}"
        )

    if tomorrow_channel:

        await tomorrow_channel.edit(
            name=f"내일 전장：{next_map} - {remain}"
        )

    print("채널 업데이트 완료")


# 실제 전장 계산 처리 함수
async def frontline_command(
    interaction: discord.Interaction,
    날짜: str
):

    try:

        now = (
            datetime.utcnow()
            + timedelta(hours=9)
        )

        split_data = (
            날짜.replace("-", "/")
            .split("/")
        )

        # 5/29 형식
        if len(split_data) == 2:

            month = int(split_data[0])
            day = int(split_data[1])

            current_year = now.year

            candidate_dates = [

                datetime(
                    current_year - 1,
                    month,
                    day
                ),

                datetime(
                    current_year,
                    month,
                    day
                ),

                datetime(
                    current_year + 1,
                    month,
                    day
                )
            ]

            target_date = min(
                candidate_dates,
                key=lambda d: abs(d - now)
            )

        # 2026/5/29 형식
        elif len(split_data) == 3:

            year = int(split_data[0])
            month = int(split_data[1])
            day = int(split_data[2])

            target_date = datetime(
                year,
                month,
                day
            )

        else:
            raise ValueError

        frontline_name = (
            get_frontline_by_date(
                target_date
            )
        )

        await interaction.response.send_message(
            f"{target_date.strftime('%Y-%m-%d')} 전장 : {frontline_name}",
            ephemeral=True
        )

    except:

        await interaction.response.send_message(
            "날짜 형식이 올바르지 않습니다.\n\n"
            "사용 예시:\n"
            "`/전장 날짜:5/29`\n"
            "`/전장 날짜:2026/5/29`",
            ephemeral=True
        )


# /전장
@bot.tree.command(
    name="전장",
    description="날짜의 전장을 확인합니다."
)
@app_commands.describe(
    날짜="예: 5/29 또는 2026/5/29"
)
async def frontline_long(
    interaction: discord.Interaction,
    날짜: str
):

    await frontline_command(
        interaction,
        날짜
    )


# /ㅈㅈ
@bot.tree.command(
    name="ㅈㅈ",
    description="날짜의 전장을 확인합니다."
)
@app_commands.describe(
    날짜="예: 5/29 또는 2026/5/29"
)
async def frontline_short(
    interaction: discord.Interaction,
    날짜: str
):

    await frontline_command(
        interaction,
        날짜
    )


@bot.event
async def on_ready():

    print(
        f"로그인 완료: {bot.user}"
    )

    try:

        synced = await bot.tree.sync()

        print(
            f"슬래시 명령어 동기화 완료: {len(synced)}개"
        )

    except Exception as e:

        print(e)

    update_channels.start()


bot.run(TOKEN)