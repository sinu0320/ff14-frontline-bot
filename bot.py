import os
import discord

from dotenv import load_dotenv
from discord.ext import tasks
from datetime import datetime, timedelta


# .env 파일 불러오기
load_dotenv()


# 디스코드 봇 토큰
TOKEN = os.getenv("DISCORD_TOKEN")


# 디스코드 채널 / 카테고리 ID
CATEGORY_ID = int(
    os.getenv("CATEGORY_ID")
)

TODAY_CHANNEL_ID = int(
    os.getenv("TODAY_CHANNEL_ID")
)

TOMORROW_CHANNEL_ID = int(
    os.getenv("TOMORROW_CHANNEL_ID")
)


# 전장 로테이션 순서
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


# 로테이션 시작 기준 날짜
#
# 매우 중요
#
# 아래 날짜를 기준으로
# 첫 번째 전장인 "봉바"부터 시작함
#
# 만약 로테이션 순서가 바뀌면:
#
# 1. ROTATION 수정
# 2. 아래 날짜 수정
#
# 두 개만 변경하면 됨

ROTATION_START_DATE = datetime(
    2026, 5, 2
)


# 디스코드 권한 설정
intents = discord.Intents.default()


# 디스코드 클라이언트 생성
client = discord.Client(
    intents=intents
)


def get_frontline_data():

    # 현재 한국 시간 계산
    now = (
        datetime.utcnow()
        + timedelta(hours=9)
    )

    # 기준 날짜로부터 며칠 지났는지 계산
    passed_days = (
        now.date()
        - ROTATION_START_DATE.date()
    ).days

    # 오늘 전장 인덱스 계산
    current_index = (
        passed_days
        % len(ROTATION)
    )

    # 내일 전장 인덱스 계산
    tomorrow_index = (
        current_index + 1
    ) % len(ROTATION)

    # 오늘 전장 이름
    today_frontline = ROTATION[
        current_index
    ]

    # 내일 전장 이름
    tomorrow_frontline = ROTATION[
        tomorrow_index
    ]

    # 다음 자정 계산
    next_midnight = (
        now + timedelta(days=1)
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    # 자정까지 남은 시간 계산
    remain_time = (
        next_midnight - now
    )

    # 남은 시간 -> 시간 단위 계산
    hours, remainder = divmod(
        remain_time.seconds,
        3600
    )

    # 남은 시간 -> 분 단위 계산
    minutes, _ = divmod(
        remainder,
        60
    )

    # 디스코드 표시용 문자열 생성
    remain_text = (
        f"{hours}시간"
        f"{minutes}분 남음"
    )

    # 결과 반환
    return (
        today_frontline,
        tomorrow_frontline,
        remain_text
    )


# 10분마다 자동 실행
@tasks.loop(minutes=10)
async def update_channels():

    print("채널 업데이트 시작")

    # 전장 정보 가져오기
    today_map, tomorrow_map, remain = (
        get_frontline_data()
    )

    # 디스코드 카테고리 가져오기
    category = client.get_channel(
        CATEGORY_ID
    )

    # 오늘 전장 채널 가져오기
    today_channel = client.get_channel(
        TODAY_CHANNEL_ID
    )

    # 내일 전장 채널 가져오기
    tomorrow_channel = client.get_channel(
        TOMORROW_CHANNEL_ID
    )

    # 카테고리 이름 변경
    await category.edit(
        name="전장 타이머 (10분 주기 갱신)"
    )

    # 오늘 전장 채널 이름 변경
    await today_channel.edit(
        name=f"오늘：{today_map}"
    )

    # 내일 전장 채널 이름 변경
    await tomorrow_channel.edit(
        name=(
            f"내일："
            f"{tomorrow_map}"
            f" - {remain}"
        )
    )

    print("업데이트 완료")


# 봇 로그인 완료 시 실행
@client.event
async def on_ready():

    print(
        f"봇 로그인 완료: {client.user}"
    )

    # 봇 시작 즉시 1회 실행
    await update_channels()

    # 이후 10분마다 반복 실행
    update_channels.start()


# 디스코드 봇 실행
client.run(TOKEN)
