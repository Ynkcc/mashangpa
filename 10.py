import time
import json
import os
import sys
from playwright.sync_api import sync_playwright, Page, expect

# 定义保存Cookies的文件名
COOKIES_FILE = "mashangpa_cookies.json"

def solve_problem(page: Page, problem_id: str):
    """
    解决问题的核心逻辑，已适配动态题目ID和多变的API请求方式。
    """
    total_sum = 0
    total_pages = 20

    # --- 1. 首先处理已经加载的第一页数据 ---
    print("正在处理第 1 页的初始数据...")
    page.wait_for_selector("#array-container .array-item", timeout=10000)
    
    number_locators = page.locator("#array-container .array-item").all()
    page_1_sum = sum([int(loc.text_content()) for loc in number_locators])
    total_sum += page_1_sum
    print(f"第 1 页数据之和为: {page_1_sum}，当前总和为: {total_sum}")

    # --- 2. 循环处理第 2 到 20 页 ---
    for page_num in range(2, total_pages + 1):
        print(f"\n准备获取第 {page_num} 页的数据...")
        
        if (page_num - 1) % 5 == 0:
            print(f"当前页码组处理完毕，点击 '下一页 »' 以加载新的页码组...")
            click_target = page.get_by_role("link", name="下一页 »")
        else:
            print(f"点击页码链接: '{page_num}'")
            click_target = page.get_by_role("link", name=str(page_num), exact=True)

        # 【最终修改】放宽请求的捕获条件，使其更具通用性。
        # 不再限制请求是GET还是POST，只要求URL包含数据接口的核心路径即可。
        with page.expect_response(
            f"**/api/problem-detail/{problem_id}/data/**",
            timeout=10000
        ) as response_info:
            click_target.click()
        
        response = response_info.value
        print(f"第 {page_num} 页数据加载请求完成 (HTTP Status: {response.status})")
        print(f"捕获到的请求方法: {response.request.method}, URL: {response.url}")

        page.locator("#array-container .array-item").first.wait_for(state="visible")
        
        number_locators = page.locator("#array-container .array-item").all()
        current_page_sum = sum([int(loc.text_content()) for loc in number_locators])
        
        total_sum += current_page_sum
        print(f"第 {page_num} 页数据之和为: {current_page_sum}，当前总和为: {total_sum}")

    # --- 3. 所有页面数据处理完毕，提交最终结果 ---
    print(f"\n所有页面数据抓取完成，计算出的总和为: {total_sum}")

    answer_input = page.locator("#user-answer")
    print(f"将答案 '{total_sum}' 填入输入框...")
    answer_input.fill(str(total_sum))
    
    submit_button = page.locator("button[type='submit']")
    print("点击提交按钮...")
    submit_button.click()

    result_message = page.locator("#result-message")
    expect(result_message).to_be_visible(timeout=5000)
    time.sleep(1)

    result_text = result_message.text_content()
    print(f"\n提交结果: {result_text}")


def main():
    """
    主函数，增加了自动加载/保存Cookies的登录管理逻辑，并能动态处理不同题目ID。
    """
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        problem_id = sys.argv[1]
        print(f"从命令行参数获取到题目ID: {problem_id}")
    else:
        problem_id = input("未提供命令行参数，请输入题目ID (例如 7, 8, 10): ")
        if not problem_id.isdigit():
            print("错误: 题目ID必须是数字。正在退出。")
            return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome", args=[
            "--disable-blink-features=AutomationControlled",
            '--log-level=3',
        ], ignore_default_args=["--enable-automation"])

        context_args = {}
        if os.path.exists(COOKIES_FILE):
            print(f"找到 Cookies 文件 '{COOKIES_FILE}'，将使用它进行登录。")
            context_args['storage_state'] = COOKIES_FILE
        else:
            print(f"未找到 Cookies 文件 '{COOKIES_FILE}'。")
        
        context = browser.new_context(**context_args)
        page = context.new_page()

        home_url = "https://www.mashangpa.com"
        page.goto(home_url, timeout=60000, wait_until="domcontentloaded")

        try:
            page.wait_for_selector('a[href="/profile/"]', timeout=5000)
            print("✓ 检测到已登录状态 (通过Cookies或已有会话)。")
        except Exception:
            print("! 未检测到登录状态，请在浏览器中手动登录。")
            print("  脚本将智能等待，登录成功后会自动继续 (最长等待2分钟)...")
            page.wait_for_selector('a[href="/profile/"]', timeout=120000)
            print("✓ 登录成功！已检测到'个人中心'链接。")
            
            print(f"正在保存当前会话到 '{COOKIES_FILE}' 以便下次自动登录...")
            storage = context.storage_state()
            with open(COOKIES_FILE, 'w') as f:
                json.dump(storage, f, indent=4)
            print("会话保存成功！")
        
        url = f"https://www.mashangpa.com/problem-detail/{problem_id}/"
        print(f"登录检查完毕，正在导航到题目页面: {url}")
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"页面加载失败: {e}")
            browser.close()
            return
            
        print("\n" + "="*20 + " 开始执行解题任务 " + "="*20)
        solve_problem(page, problem_id)

        print("\n脚本执行完毕，5秒后将自动关闭浏览器...")
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()