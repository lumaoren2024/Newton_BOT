import asyncio,json,random,sys,time
from os import path
from playwright.async_api import async_playwright


MAGICNEWTON_URL = "https://www.magicnewton.com/portal/rewards"
DEFAULT_SLEEP_TIME = 24 * 60 * 60  # 24 hours in seconds
RANDOM_EXTRA_DELAY = lambda: random.randint(20, 60) * 60  # 20-60 mins random delay in seconds

# 获取用户输入的账号配置，默认生成 cookies 文件路径
def get_user_accounts():
    ACCOUNTS = []
    used_ids = set()  # 用于检查重复的 ID
    print("请输入账号信息（直接按 Enter 结束输入）：")
    while True:
        account_id = input("请输入账号 ID（例如 user1，直接按 Enter 结束）：").strip()
        if not account_id:  # 如果输入空行，则结束
            if ACCOUNTS:  # 如果已经输入了至少一个账号，则退出
                break
            else:
                print("⚠️ 请至少输入一个账号！")
                continue
        if account_id in used_ids:
            print(f"⚠️ 账号 ID '{account_id}' 已存在，请输入不同的 ID！")
            continue
        used_ids.add(account_id)
        # 自动生成默认的 cookies 文件路径
        cookies_file = f"config/cookies_{account_id}.json"
        print(f"[{account_id}] 将使用默认 cookies 文件：{cookies_file}")
        ACCOUNTS.append({"id": account_id, "cookies_file": cookies_file})
    if not ACCOUNTS:
        print("⚠️ 未输入任何账号，默认使用单一账号 cookies.json")
        ACCOUNTS.append({"id": "default", "cookies_file": "cookies.json"})
    return ACCOUNTS

async def delay(seconds):
    await asyncio.sleep(seconds)

def parse_time_string(time_str):
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) != 3:
            return None
        return {
            'hours': parts[0],
            'minutes': parts[1],
            'seconds': parts[2],
            'totalMs': (parts[0] * 3600 + parts[1] * 60 + parts[2]) * 1000
        }
    except:
        return None

async def show_live_countdown(total_ms, account_id):
    total_seconds = total_ms // 1000
    while total_seconds > 0:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        sys.stdout.write(f"\r[{account_id}] ⏳ 下一次运行时间: {hours:02d}:{minutes:02d}:{seconds:02d} ")
        sys.stdout.flush()
        await delay(1)
        total_seconds -= 1
    print(f"\n[{account_id}] ✅ 时间已到！重试掷骰...")

async def get_current_score(page):
    try:
        score = await page.evaluate(
            """() => {
                const el = document.querySelector('div.jsx-f1b6ce0373f41d79 h2');
                return parseInt(el?.innerText) || 0;
            }"""
        )
        return score
    except:
        return 0

async def press_or_bank(page, roll_count, score, account_id):
    if (roll_count <= 2 and score < 35) or (2 < roll_count < 5 and score < 30):
        print(f"[{account_id}] 🎲 Roll {roll_count}: Score = {score}. Pressing again...")
        await page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                const pressButton = Array.from(buttons).find(btn => btn.innerText.includes("Press"));
                if (pressButton) pressButton.click();
            }
        """)
        await delay(5)
        return True
    else:
        print(f"[{account_id}] 🏦 Roll {roll_count}: Score = {score}. Banking score...")
        await page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                const bankButton = Array.from(buttons).find(btn => btn.innerText.includes("Bank"));
                if (bankButton) bankButton.click();
            }
        """)
        return False

async def run_account(account):
    account_id = account["id"]
    cookies_file = account["cookies_file"]
    print(f"[{account_id}] 🚀 启动账户...")

    proxy = None
    try:
        with open(cookies_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and "proxy" in data:
                proxy = {"server": data["proxy"]}
            elif isinstance(data, list) and len(data) > 0 and "proxy" in data[0]:
                proxy = {"server": data[0]["proxy"]}
            cookies = data if isinstance(data, list) else data.get("cookies", [])
    except Exception as e:
        print(f"[{account_id}] ❌ 无法加载 cookies 文件 {cookies_file}: {e}")
        return

    if proxy:
        print(f"[{account_id}] 🌐 使用代理: {proxy['server']}")
    else:
        print(f"[{account_id}] ⚠️ 未指定代理，无需代理即可运行.")

    while True:
        try:
            print(f"\033c[{account_id}] 🔄 新的循环开始了...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox'],
                    proxy=proxy
                )
                page = await browser.new_page()

                if path.exists(cookies_file):
                    await page.context.add_cookies(cookies)
                    print(f"[{account_id}] ✅ Cookie 加载成功.")
                else:
                    print(f"[{account_id}] ❌ 未找到 Cookie 文件：{cookies_file}。跳过帐户.")
                    await browser.close()
                    return

                await page.goto(MAGICNEWTON_URL, wait_until='networkidle', timeout=60000)
                print(f"[{account_id}] 🌐 页面已加载.")

                user_email = await page.evaluate(
                    """() => document.querySelector('p.gGRRlH.WrOCw.AEdnq.hGQgmY.jdmPpC')?.innerText || 'Unknown'"""
                )
                print(f"[{account_id}] 📧 登录账户: {user_email}")

                user_credits = await page.evaluate(
                    """() => document.querySelector('#creditBalance')?.innerText || 'Unknown'"""
                )
                print(f"[{account_id}] 💰 当前积分: {user_credits}")

                await page.wait_for_selector('button', timeout=30000)
                roll_now_clicked = await page.evaluate("""
                    () => {
                        const buttons = document.querySelectorAll('button');
                        const target = Array.from(buttons).find(btn => btn.innerText.includes("Roll now"));
                        if (target) {
                            target.click();
                            return true;
                        }
                        return false;
                    }
                """)

                if roll_now_clicked:
                    print(f"[{account_id}] ✅ 已点击‘摇骰子’按钮！")
                    await delay(5)

                    lets_roll_clicked = await page.evaluate("""
                        () => {
                            const buttons = document.querySelectorAll('button');
                            const target = Array.from(buttons).find(btn => btn.innerText.includes("Let's roll"));
                            if (target) {
                                target.click();
                                return true;
                            }
                            return false;
                        }
                    """)

                    if lets_roll_clicked:
                        print(f"[{account_id}] ✅ 点击 'Let's roll' 按钮！")
                        await delay(5)
                        throw_dice_clicked = await page.evaluate("""
                            () => {
                                const buttons = document.querySelectorAll('button');
                                const target = Array.from(buttons).find(btn => btn.innerText.includes("Throw Dice"));
                                if (target) {
                                    target.click();
                                    return true;
                                }
                                return false;
                            }
                        """)

                        if throw_dice_clicked:
                            print(f"[{account_id}] ✅ 点击  'Throw Dice' 按钮！")
                            print(f"[{account_id}] ⏳ 等待 60 秒观看骰子动画...")
                            await delay(60)
                            user_credits = await page.evaluate(
                                """() => document.querySelector('#creditBalance')?.innerText || 'Unknown'"""
                            )
                            print(f"[{account_id}] 💰 更新积分: {user_credits}")

                            roll_count = 1
                            while roll_count <= 5:
                                score = await get_current_score(page)
                                should_continue = await press_or_bank(page, roll_count, score, account_id)
                                if not should_continue:
                                    break
                                roll_count += 1
                                await delay(60)
                        else:
                            print(f"[{account_id}] ⚠️ 没找到'Throw Dice'按钮.")
                    else:
                        print(f"[{account_id}] 👇 稍等！摇骰子 尚未可用.")
                        timer_text = await page.evaluate(r"""
                            () => {
                                const h2Elements = document.querySelectorAll('h2');
                                for (let h2 of h2Elements) {
                                    const text = h2.innerText.trim();
                                    if (/^\d{2}:\d{2}:\d{2}$/.test(text)) {
                                        return text;
                                    }
                                }
                                return null;
                            }
                        """)

                        if timer_text:
                            print(f"[{account_id}] ⏱ 距离下次 摇骰子 剩余时间: {timer_text}")
                            time_data = parse_time_string(timer_text)
                            if time_data:
                                await show_live_countdown(time_data['totalMs'] + 5000, account_id)
                            else:
                                print(f"[{account_id}] ⚠️ 无法解析计时器。使用默认睡眠时间.")
                        else:
                            print(f"[{account_id}] ⚠️ 未找到定时器。使用默认睡眠时间.")
                await browser.close()

                extra_delay = RANDOM_EXTRA_DELAY()
                print(f"[{account_id}] 🔄 循环完成。休眠 24 小时 + 随机延迟 {extra_delay // 60} 分钟...")
                await delay(DEFAULT_SLEEP_TIME + extra_delay)
        except Exception as error:
            print(f"[{account_id}] ❌ 错误: {error}")
            await delay(60)

async def main():
    ACCOUNTS = get_user_accounts()
    print(f"已配置 {len(ACCOUNTS)} 个账号：{[acc['id'] for acc in ACCOUNTS]}")
    tasks = [run_account(account) for account in ACCOUNTS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())