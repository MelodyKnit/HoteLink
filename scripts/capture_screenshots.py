"""
capture_screenshots.py — 使用 Playwright 从运行中的 HoteLink 系统截取论文所需界面截图。

用法:
    python scripts/capture_screenshots.py [--base-url http://localhost:8088] [--output dist/BYSJ-V2/v1/img]

前提:
    1. HoteLink 开发容器已启动 (docker compose -f docker-compose.dev.yml up)
    2. 已安装 playwright: pip install playwright && playwright install chromium
    3. 数据库中有 zhangsan (用户) / admin (管理员) 账户, 密码 Password123
"""

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, BrowserContext

BASE_URL = "http://localhost:8088"
API_BASE = "/api/v1"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "dist" / "BYSJ-V2" / "v1" / "img"

USER_CRED = {"username": "zhangsan", "password": "Password123"}
ADMIN_CRED = {"username": "admin", "password": "Password123"}

# 视口尺寸
USER_VIEWPORT = {"width": 390, "height": 844}       # iPhone 14 Pro 尺寸
ADMIN_VIEWPORT = {"width": 1440, "height": 900}     # 标准桌面


def login_via_api(context: BrowserContext, endpoint: str, cred: dict, namespace: str, base_url: str):
    """通过 API 登录并将 token 注入 localStorage。"""
    import requests
    resp = requests.post(f"{base_url}{API_BASE}{endpoint}", json=cred, timeout=10)
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Login failed for {cred['username']}: {data}")
    tokens = data["data"]
    access = tokens["access_token"]
    refresh = tokens.get("refresh_token", "")
    # 注入到浏览器 localStorage
    page = context.new_page()
    page.goto(base_url)
    page.evaluate(f"""() => {{
        localStorage.setItem('hotelink_access_token_{namespace}', '{access}');
        localStorage.setItem('hotelink_refresh_token_{namespace}', '{refresh}');
    }}""")
    page.close()
    return access


def wait_for_content(page: Page, timeout: int = 8000):
    """等待页面网络空闲 + 主要内容加载。"""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    # 额外等待动画/渲染完成
    page.wait_for_timeout(800)


def screenshot(page: Page, name: str, output_dir: Path, full_page: bool = False):
    """截图并保存。"""
    filepath = output_dir / name
    page.screenshot(path=str(filepath), full_page=full_page, type="png")
    size_kb = filepath.stat().st_size / 1024
    print(f"  ✅ {name}  ({size_kb:.0f} KB)")


def capture_user_screenshots(context: BrowserContext, output_dir: Path, base_url: str):
    """截取用户端页面。"""
    print("\n📱 用户端截图")
    page = context.new_page()
    page.set_viewport_size(USER_VIEWPORT)

    # 01 - 首页
    page.goto(f"{base_url}/")
    wait_for_content(page)
    screenshot(page, "01-user-home.png", output_dir, full_page=True)

    # 02 - 酒店列表
    page.goto(f"{base_url}/hotels")
    wait_for_content(page)
    screenshot(page, "02-user-hotels.png", output_dir, full_page=True)

    # 03 - 酒店详情 (进入有房型的酒店)
    page.goto(f"{base_url}/hotels")
    wait_for_content(page)
    # 点击酒店卡片（选择包含价格的卡片链接）
    hotel_cards = page.locator("a[href^='/hotels/']").all()
    clicked = False
    for card in hotel_cards[:5]:
        href = card.get_attribute("href") or ""
        # 过滤出 /hotels/数字 格式的链接
        if href and href.replace("/hotels/", "").isdigit():
            card.click()
            wait_for_content(page)
            clicked = True
            break
    if not clicked:
        page.goto(f"{base_url}/hotels/4254")
        wait_for_content(page)
    screenshot(page, "03-user-hotel-detail.png", output_dir, full_page=True)

    # 04 - 预订页 (尝试点击预订按钮)
    book_btn = page.locator("button:has-text('预订'), button:has-text('立即预订'), a:has-text('预订')").first
    if book_btn.count():
        book_btn.click()
        wait_for_content(page)
        screenshot(page, "04-user-booking.png", output_dir)
    else:
        print("  ⚠️ 04-user-booking.png 跳过 (未找到预订入口)")

    # 07 - AI 智能客服
    page.goto(f"{base_url}/ai-chat")
    wait_for_content(page)
    screenshot(page, "07-user-ai-chat.png", output_dir)

    # 08 - 酒店对比
    page.goto(f"{base_url}/hotel-compare")
    wait_for_content(page)
    screenshot(page, "08-user-compare.png", output_dir)

    # 14 - AI 订房助手 (使用 ai-booking 路由)
    page.goto(f"{base_url}/ai-booking")
    wait_for_content(page)
    screenshot(page, "14-user-ai-booking.png", output_dir)

    # 21 - 账号安全
    page.goto(f"{base_url}/my/security")
    wait_for_content(page)
    screenshot(page, "21-user-security-current.png", output_dir)

    # 订单相关截图 - 先获取订单列表
    page.goto(f"{base_url}/my/orders")
    wait_for_content(page)

    # 找到第一个订单
    order_link = page.locator("a[href*='/my/orders/'], [class*='order'] a, tr a").first
    if order_link.count():
        order_link.click()
        wait_for_content(page)
        screenshot(page, "06-user-order-detail.png", output_dir)
    else:
        print("  ⚠️ 06-user-order-detail.png 跳过 (未找到订单)")

    # 05 - 支付页 (需要从未支付订单进入)
    page.goto(f"{base_url}/my/orders")
    wait_for_content(page)
    pay_btn = page.locator("button:has-text('支付'), button:has-text('去支付'), a:has-text('支付')").first
    if pay_btn.count():
        pay_btn.click()
        wait_for_content(page)
        screenshot(page, "05-user-payment.png", output_dir)
    else:
        print("  ⚠️ 05-user-payment.png 跳过 (无待支付订单)")

    page.close()


def capture_admin_screenshots(context: BrowserContext, output_dir: Path, base_url: str):
    """截取管理端页面。"""
    print("\n🖥️  管理端截图")
    page = context.new_page()
    page.set_viewport_size(ADMIN_VIEWPORT)

    def go(path: str, name: str, full_page: bool = False, wait_extra: int = 0):
        try:
            page.goto(f"{base_url}{path}", timeout=15000)
            wait_for_content(page)
            if wait_extra:
                page.wait_for_timeout(wait_extra)
            screenshot(page, name, output_dir, full_page=full_page)
        except Exception as e:
            print(f"  ⚠️ {name} 失败: {e}")

    # 09 - Dashboard
    go("/admin/", "09-admin-dashboard.png")

    # 10 - 库存管理
    go("/admin/inventory", "10-admin-inventory.png")

    # 11 - 订单管理
    go("/admin/orders", "11-admin-orders.png")

    # 12 - AI 经营报告 (通过报表页)
    go("/admin/reports", "12-admin-ai-business-report.png", wait_extra=1000)

    # 13 - AI 配置
    go("/admin/ai-settings", "13-admin-ai-settings.png")

    # 15 - AI 定价 (AI 助手页面的某功能)
    go("/admin/ai", "15-admin-ai-pricing.png", wait_extra=500)

    # 17 - AI 调用日志
    go("/admin/ai-logs", "17-admin-ai-logs.png")

    # 22 - 系统状态
    go("/admin/system-status", "22-admin-system-status-current.png")

    # 23 - AI 配置 (同 13，当前状态)
    go("/admin/ai-settings", "23-admin-ai-settings-current.png")

    # 24 - 系统设置
    go("/admin/settings", "24-admin-settings-current.png")

    # 25 - 前台入住
    go("/admin/frontdesk/check-in", "25-admin-frontdesk-check-in.png")

    # 26 - 前台退房
    go("/admin/frontdesk/check-out", "26-admin-frontdesk-check-out.png")

    # 27 - 续住换房
    go("/admin/frontdesk/extend-switch", "27-admin-frontdesk-extend-switch.png")

    # 评论管理
    go("/admin/reviews", "16-admin-ai-sentiment.png")

    page.close()


def main():
    parser = argparse.ArgumentParser(description="HoteLink 论文截图工具")
    parser.add_argument("--base-url", default=BASE_URL, help="系统访问地址")
    parser.add_argument("--output", default=str(OUTPUT_DIR), help="截图输出目录")
    parser.add_argument("--skip-user", action="store_true", help="跳过用户端截图")
    parser.add_argument("--skip-admin", action="store_true", help="跳过管理端截图")
    parser.add_argument("--headless", action="store_true", default=True, help="无头模式运行")
    parser.add_argument("--headed", action="store_true", help="有头模式运行 (调试)")
    args = parser.parse_args()

    base_url = args.base_url
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    headless = not args.headed

    print(f"📸 HoteLink 截图工具")
    print(f"   系统地址: {base_url}")
    print(f"   输出目录: {output_dir}")
    print(f"   模式: {'无头' if headless else '有头'}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        if not args.skip_user:
            print("\n🔐 登录用户端 (zhangsan)...")
            user_ctx = browser.new_context(
                viewport=USER_VIEWPORT,
                device_scale_factor=2,
                locale="zh-CN",
            )
            login_via_api(user_ctx, "/public/auth/login", USER_CRED, "user", base_url)
            capture_user_screenshots(user_ctx, output_dir, base_url)
            user_ctx.close()

        if not args.skip_admin:
            print("\n🔐 登录管理端 (admin)...")
            admin_ctx = browser.new_context(
                viewport=ADMIN_VIEWPORT,
                device_scale_factor=2,
                locale="zh-CN",
            )
            login_via_api(admin_ctx, "/public/auth/admin-login", ADMIN_CRED, "admin", base_url)
            capture_admin_screenshots(admin_ctx, output_dir, base_url)
            admin_ctx.close()

        browser.close()

    print(f"\n✅ 截图完成! 输出目录: {output_dir}")


if __name__ == "__main__":
    main()
