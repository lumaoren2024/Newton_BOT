import asyncio,json,random,sys,time
from os import path
from colorama import *
from playwright.async_api import async_playwright

# 版权
def show_copyright():
    """展示版权信息"""
    copyright_info = f"""{Fore.CYAN}
    *****************************************************
    *           X:https://x.com/ariel_sands_dan         *
    *           Tg:https://t.me/sands0x1                *
    *           NewTon Bot Version 2.0                  *
    *           Copyright (c) 2025                      *
    *           All Rights Reserved                     *
    *****************************************************
    """
    {Style.RESET_ALL}
    print(copyright_info)
    print('=' * 50)
    print(f"{Fore.GREEN}申请key: https://661100.xyz/ {Style.RESET_ALL}")
    print(f"{Fore.RED}联系Dandan: \n QQ:712987787 QQ群:1036105927 \n 电报:sands0x1 电报群:https://t.me/+fjDjBiKrzOw2NmJl \n 微信: dandan0x1{Style.RESET_ALL}")
    print('=' * 50)


MAGICNEWTON_URL = "https://www.magicnewton.com/portal/rewards"
DEFAULT_SLEEP_TIME = 24 * 60 * 60  # 24 小时以秒为单位
RANDOM_EXTRA_DELAY = lambda: random.randint(20, 60) * 60  # 20-60 分钟随机延迟（以秒为单位）

# 获取用户输入的账号配置，默认生成 cookies 文件路径
def get_user_accounts():
    ACCOUNTS = []
    used_ids = set()  # 用于检查重复的 ID
    print("请输入账号信息（直接按 Enter 结束输入）：")
    while True:
        account_id = input("请输入账号 ID（例如:输入1。那么你的配置cookies_1.json，直接按 Enter 结束）：").strip()
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
    print(f"\n[{account_id}] ✅ 时间已到！重试...")

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

async def random_click_minesweeper(page, account_id):
    # 定位游戏容器
    game_container = await page.query_selector(".game-container")
    if not game_container:
        print(f"[{account_id}] ❌ Game container not found")
        return False

    # 获取所有格子
    tiles = await game_container.query_selector_all(".tile.jetbrains")
    if not tiles:
        print(f"[{account_id}] ❌ No tiles found in the game container")
        return False

    # 筛选未打开的格子
    unopened_tiles = []
    for tile in tiles:
        tile_class = await tile.get_attribute("class") or ""
        tile_style = await tile.get_attribute("style") or ""
        
        is_changed = "tile-changed" in tile_class
        is_opened_empty = "background-color: transparent" in tile_style
        
        if not is_changed and not is_opened_empty:
            tile_box = await tile.bounding_box()
            if tile_box:
                unopened_tiles.append(tile_box)

    if not unopened_tiles:
        print(f"[{account_id}] ❌ No unopened tiles found")
        return False

    # 随机选择一个未打开的格子
    target_tile = random.choice(unopened_tiles)

    # 计算格子中心点进行点击
    center_x = target_tile["x"] + target_tile["width"] / 2
    center_y = target_tile["y"] + target_tile["height"] / 2

    # 点击格子
    await page.mouse.click(center_x, center_y)
    print(f"[{account_id}] ✅ Clicked at ({center_x:.2f}, {center_y:.2f})")
    return True

async def play_dice_game(page, account_id):
    print(f"[{account_id}] 🎲 尝试玩掷骰子游戏...")

    # 记录所有按钮以检查“立即滚动”
    buttons_debug = await page.evaluate("""
        () => {
            const buttons = document.querySelectorAll('button');
            return Array.from(buttons).map(btn => btn.innerText);
        }
    """)
    #print(f"[{account_id}] 📋 All buttons on the page: {buttons_debug}")

    # Click "Roll now" button
    try:
        roll_now_button = await page.wait_for_selector('button:has-text("Roll now")', timeout=10000)
        await roll_now_button.click()
        print(f"[{account_id}] ✅ 已点击‘Roll now’按钮！")
    except Exception as e:
        print(f"[{account_id}] ❌ 未找到 'Roll now' 按钮或无法点击: {e}")
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
            print(f"[{account_id}] ⏱ 距离下次掷骰子剩余时间: {timer_text}")
            return False, timer_text
        else:
            print(f"[{account_id}] ⚠️ 未找到定时器。")
            return False, None

    await delay(5)

    # 点击 "Let's roll" 按钮
    try:
        lets_roll_button = await page.wait_for_selector('button:has-text("Let\'s roll")', timeout=10000)
        await lets_roll_button.click()
        print(f"[{account_id}] ✅ 点击 'Let's roll' 按钮！")
    except Exception as e:
        print(f"[{account_id}] ❌ 未找到 'Let's roll' 按钮或无法点击: {e}")
        return False, None

    await delay(5)

    # 点击 "Throw Dice" 按钮
    try:
        throw_dice_button = await page.wait_for_selector('button:has-text("Throw Dice")', timeout=10000)
        await throw_dice_button.click()
        print(f"[{account_id}] ✅ 点击 'Throw Dice' 按钮！")
    except Exception as e:
        print(f"[{account_id}] ❌ 未找到 'Throw Dice' 按钮或无法点击: {e}")
        return False, None

    print(f"[{account_id}] ⏳ 等待 60 秒观看骰子动画...")
    await delay(60)

    user_credits = await page.evaluate(
        """() => document.querySelector('#creditBalance')?.innerText || 'Unknown'"""
    )
    print(f"[{account_id}] 💰 更新积分: {user_credits}")

    roll_count = 1
    while roll_count <= 1:
        score = await get_current_score(page)
        should_continue = await press_or_bank(page, roll_count, score, account_id)
        if not should_continue:
            break
        roll_count += 1
        await delay(60)

    return True, None

async def play_minesweeper_game(page, account_id):
    print(f"[{account_id}] 🎮 尝试玩扫雷游戏...")

    # 记录所有按钮以检查 "Play now" 按钮
    buttons_debug = await page.evaluate("""
        () => {
            const buttons = document.querySelectorAll('button');
            return Array.from(buttons).map(btn => btn.innerText);
        }
    """)
    #print(f"[{account_id}] 📋 All buttons on the page: {buttons_debug}")

    # 检查 "Play now" 按钮
    try:
        play_now_button = await page.wait_for_selector('button:has-text("Play now")', timeout=10000)
        await play_now_button.click()
        print(f"[{account_id}] ✅ 已点击‘Play now’按钮！")
    except Exception as e:
        print(f"[{account_id}] ❌ 未找到 'Play now' 按钮或无法点击: {e}")
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
            print(f"[{account_id}] ⏱ 距离下次扫雷剩余时间: {timer_text}")
            return False, timer_text
        else:
            print(f"[{account_id}] ⚠️ 未找到定时器。")
            return False, None

    await delay(5)

    # 点击 "Play now" 后等待网络空闲
    await page.wait_for_load_state("networkidle", timeout=30000)
    print(f"[{account_id}] 🌐 网络请求已完成！")

    # 点击 "Play now" 后调试页面内容
    page_content = await page.content()
    #print(f"[{account_id}] 📄 Page content after clicking 'Play now': {page_content[:500]}...")

    # Debug: Log all buttons to check for "Continue"
    buttons_debug = await page.evaluate("""
        () => {
            const buttons = document.querySelectorAll('button');
            return Array.from(buttons).map(btn => btn.innerText);
        }
    """)
    #print(f"[{account_id}] 📋 All buttons on the page: {buttons_debug}")

    # 点击 "Continue" 按钮
    try:
        continue_button = await page.wait_for_selector('button:has-text("Continue")', timeout=10000)
        await continue_button.click()
        print(f"[{account_id}] ✅ 点击 'Continue' 按钮！")
    except Exception as e:
        print(f"[{account_id}] ❌ 未找到 'Continue' 按钮或无法点击: {e}")
        return False, None

    await delay(5)

    # 点击 "Continue" 后等待网络空闲
    await page.wait_for_load_state("networkidle", timeout=30000)
    print(f"[{account_id}] 🌐 网络请求已完成！")

    # 点击 "Continue" 后调试页面内容
    page_content = await page.content()
    #print(f"[{account_id}] 📄 Page content after clicking 'Continue': {page_content[:500]}...")

    # 等待游戏容器并回退
    try:
        await page.wait_for_selector(".game-container", timeout=30000)
        print(f"[{account_id}] 🎮 扫雷游戏已加载！")
    except Exception as e:
        print(f"[{account_id}] ❌ 无法找到 .game-container 元素: {e}")
        try:
            await page.wait_for_selector(".ms-container", timeout=10000)
            print(f"[{account_id}] 🎮 找到 .ms-container 元素，游戏已加载！")
        except Exception as e2:
            print(f"[{account_id}] ❌ 无法找到 .ms-container 元素: {e2}")
            return False, None

    # 扫雷的随机点击逻辑
    max_attempts = 100
    for attempt in range(max_attempts):
        game_status = await page.query_selector(".ms-info")
        if game_status:
            status_text = await game_status.inner_text()
            if "Game Over" in status_text or "You Win" in status_text:
                print(f"[{account_id}] 🎉 游戏结束: {status_text}")
                break

        success = await random_click_minesweeper(page, account_id)
        if not success:
            print(f"[{account_id}] ⚠️ 没有可点击的格子，游戏可能已结束")
            break

        await delay(1)

    return True, None

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
                if user_email == 'Unknown':
                    print(f"[{account_id}] ❌ 登录失败，可能 cookies 无效！")
                    await page.screenshot(path=f"screenshots/{account_id}_login_error.png")
                    await browser.close()
                    return
                print(f"[{account_id}] 📧 登录账户: {user_email}")

                user_credits = await page.evaluate(
                    """() => document.querySelector('#creditBalance')?.innerText || 'Unknown'"""
                )
                print(f"[{account_id}] 💰 当前积分: {user_credits}")

                # 尝试玩这两种游戏
                max_dice_games = 1  # 骰子游戏每天只能玩一次
                max_minesweeper_games = 3  #扫雷每天可玩 3 次
                dice_games_played = 0
                minesweeper_games_played = 0
                dice_cooldown = None
                minesweeper_cooldown = None

                while (dice_games_played < max_dice_games or minesweeper_games_played < max_minesweeper_games):
                    # 尝试玩骰子游戏（仅一次）
                    if dice_games_played < max_dice_games and not dice_cooldown:
                        success, cooldown = await play_dice_game(page, account_id)
                        if success:
                            dice_games_played += 1
                            print(f"[{account_id}] ✅ 完成第 {dice_games_played} 次掷骰子游戏！")
                        else:
                            dice_cooldown = cooldown
                    else:
                        print(f"[{account_id}] ⚠️ 掷骰子游戏已达上限或冷却中，跳过...")

                    # 尝试玩扫雷游戏 (最多 3 次)
                    if minesweeper_games_played < max_minesweeper_games and not minesweeper_cooldown:
                        success, cooldown = await play_minesweeper_game(page, account_id)
                        if success:
                            minesweeper_games_played += 1
                            print(f"[{account_id}] ✅ 完成第 {minesweeper_games_played} 次扫雷游戏！")
                        else:
                            minesweeper_cooldown = cooldown
                    else:
                        print(f"[{account_id}] ⚠️ 扫雷游戏已达上限或冷却中，跳过...")

                    # 检查两个游戏是否都已完成或处于冷却状态
                    if (dice_games_played >= max_dice_games or dice_cooldown) and \
                       (minesweeper_games_played >= max_minesweeper_games or minesweeper_cooldown):
                        break

                    # 刷新页面检查可用性
                    await page.reload(wait_until='networkidle', timeout=60000)
                    print(f"[{account_id}] 🌐 页面已刷新，检查是否可以继续玩...")

                    # 下次尝试前请稍等片刻
                    await delay(5)

                await browser.close()

                print(f"[{account_id}] 🎲 总共玩了 {dice_games_played} 次掷骰子游戏！")
                print(f"[{account_id}] 🎮 总共玩了 {minesweeper_games_played} 次扫雷游戏！")

                # 根据冷却时间确定睡眠时间
                sleep_time_ms = DEFAULT_SLEEP_TIME * 1000  # 默认为 24​​ 小时（以毫秒为单位）
                if dice_cooldown:
                    dice_time_data = parse_time_string(dice_cooldown)
                    if dice_time_data:
                        sleep_time_ms = min(sleep_time_ms, dice_time_data['totalMs'] + 5000)
                if minesweeper_cooldown:
                    minesweeper_time_data = parse_time_string(minesweeper_cooldown)
                    if minesweeper_time_data:
                        sleep_time_ms = min(sleep_time_ms, minesweeper_time_data['totalMs'] + 5000)

                extra_delay = RANDOM_EXTRA_DELAY()
                total_sleep_time = sleep_time_ms / 1000 + extra_delay
                print(f"[{account_id}] 🔄 循环完成。休眠 {total_sleep_time // 3600} 小时 + 随机延迟 {extra_delay // 60} 分钟...")
                await delay(total_sleep_time)

        except Exception as error:
            print(f"[{account_id}] ❌ 错误: {error}")
            await delay(60)

async def main():
    show_copyright()
    await asyncio.sleep(10)
    ACCOUNTS = get_user_accounts()
    print(f"已配置 {len(ACCOUNTS)} 个账号：{[acc['id'] for acc in ACCOUNTS]}")
    tasks = [run_account(account) for account in ACCOUNTS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
