import os
import discord

# .env 파일 읽기용
from dotenv import load_dotenv

# 반복 작업(loop)과 명령어 시스템
from discord.ext import tasks, commands

# 슬래시 명령어 관련
from discord import app_commands

# 날짜 계산용
from datetime import datetime, timedelta


# .env 파일 불러오기
load_dotenv()

# 디스코드 봇 토큰
TOKEN = os.getenv("DISCORD_TOKEN")

# 오늘 전장 채널 ID
TODAY_CHANNEL_ID = int(
    os.getenv("TODAY_CHANNEL_ID")
)

# 내일 전장 채널 ID
TOMORROW_CHANNEL_ID = int(
    os.getenv("TOMORROW_CHANNEL_ID")
)


# 전장 순환표
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


# 전장 시작 기준 날짜
ROTATION_START = datetime(
    2026, 1, 1
)


# 디스코드 권한(Intents)
intents = discord.Intents.default()


# 봇 생성
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# 특정 날짜의 전장을 계산하는 함수
def get_frontline_by_date(target_date):

    # 기준 날짜부터 지난 날짜 계산
    passed_days = (
        target_date.date()
        - ROTATION_START.date()
    ).days

    # 순환표 반복 계산
    index = (
        passed_days
        % len(ROTATION)
    )

    # 해당 전장 반환
    return ROTATION[index]


# 현재 / 내일 전장 계산 함수
def get_frontline():

    # 한국 시간
    now = (
        datetime.utcnow()
        + timedelta(hours=9)
    )

    # 오늘 전장
    current_map = (
        get_frontline_by_date(now)
    )

    # 내일 전장
    next_map = (
        get_frontline_by_date(
            now + timedelta(days=1)
        )
    )

    # 다음 자정 계산
    tomorrow = (
        now + timedelta(days=1)
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    # 남은 시간 계산
    remain = tomorrow - now

    hours, remainder = divmod(
        remain.seconds,
        3600
    )

    minutes, _ = divmod(
        remainder,
        60
    )

    # 표시용 문자열
    remain_text = (
        f"{hours}시간"
        f"{minutes}분 남음"
    )

    return (
        current_map,
        next_map,
        remain_text
    )


# 채널 이름 자동 업데이트
# 10분마다 반복 실행
@tasks.loop(minutes=10)
async def update_channels():

    # 현재 전장 정보 가져오기
    current_map, next_map, remain = (
        get_frontline()
    )

    # 채널 가져오기
    today_channel = bot.get_channel(
        TODAY_CHANNEL_ID
    )

    tomorrow_channel = bot.get_channel(
        TOMORROW_CHANNEL_ID
    )

    # 오늘 전장 채널 이름 수정
    if today_channel:

        await today_channel.edit(
            name=f"오늘 전장：{current_map}"
        )

    # 내일 전장 채널 이름 수정
    if tomorrow_channel:

        await tomorrow_channel.edit(
            name=f"내일 전장：{next_map} - {remain}"
        )

    print("채널 업데이트 완료")


# 슬래시 명령어
#
# 사용 예시:
# /전장 날짜:5/29
# /전장 날짜:2026/5/29
@bot.tree.command(
    name="전장",
    description="날짜의 전장을 확인합니다."
)

# 슬래시 명령어 입력칸 설명
@app_commands.describe(
    날짜="예: 5/29 또는 2026/5/29"
)

async def frontline(
    interaction: discord.Interaction,
    날짜: str
):

    try:

        # 현재 한국 시간
        now = (
            datetime.utcnow()
            + timedelta(hours=9)
        )

        # 날짜 형식 통일
        split_data = (
            날짜.replace("-", "/")
            .split("/")
        )

        # 연도를 입력하지 않은 경우
        if len(split_data) == 2:

            month = int(split_data[0])
            day = int(split_data[1])

            current_year = now.year

            # 가장 가까운 연도 찾기
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

            # 현재 날짜와 가장 가까운 날짜 선택
            target_date = min(
                candidate_dates,
                key=lambda d: abs(d - now)
            )

        # 연도를 입력한 경우
        elif len(split_data) == 3:

            year = int(split_data[0])
            month = int(split_data[1])
            day = int(split_data[2])

            target_date = datetime(
                year,
                month,
                day
            )

        # 날짜 형식 오류
        else:
            raise ValueError

        # 해당 날짜 전장 계산
        frontline_name = (
            get_frontline_by_date(
                target_date
            )
        )

        # 비밀 메시지로 응답
        await interaction.response.send_message(
            f"{target_date.strftime('%Y-%m-%d')} 전장 : {frontline_name}",
            ephemeral=True
        )

    # 날짜 입력 오류 처리
    except:

        await interaction.response.send_message(
            "날짜 형식이 올바르지 않습니다.\n\n"
            "사용 예시:\n"
            "`/전장 날짜:5/29`\n"
            "`/전장 날짜:2026/5/29`",
            ephemeral=True
        )


# 봇 시작 시 실행
@bot.event
async def on_ready():

    print(
        f"로그인 완료: {bot.user}"
    )

    try:

        # 슬래시 명령어 등록
        synced = await bot.tree.sync()

        print(
            f"슬래시 명령어 동기화 완료: {len(synced)}개"
        )

    except Exception as e:

        print(e)

    # 채널 자동 업데이트 시작
    update_channels.start()


# 봇 실행
bot.run(TOKEN)