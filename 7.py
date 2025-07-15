import time
from playwright.sync_api import sync_playwright, Page, expect

def solve_problem(page: Page):
    """
    解决 "题七：千山鸟飞绝" 问题的核心逻辑。
    最终版：处理5页一组的静态分页栏。

    Args:
        page: Playwright 的 Page 对象。
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
        
        # 【核心分页逻辑】
        # 判断是点击 "下一页" 还是直接点击页码
        # 当 page_num 是 6, 11, 16 时，(page_num - 1) % 5 == 0，此时需要点击 "下一页"
        if (page_num - 1) % 5 == 0:
            print(f"当前页码组处理完毕，点击 '下一页 »' 以加载新的页码组...")
            click_target = page.get_by_role("link", name="下一页 »")
        else:
            # 否则，直接点击对应的页码链接
            print(f"点击页码链接: '{page_num}'")
            click_target = page.get_by_role("link", name=str(page_num), exact=True)

        # 在点击前，设置监听器等待后台数据响应
        with page.expect_response(f"**/api/problem-detail/7/data/?page={page_num}*") as response_info:
            click_target.click()
        
        response = response_info.value
        print(f"第 {page_num} 页数据加载请求完成 (HTTP Status: {response.status})")
        print(f"捕获到的URL: {response.url}")

        # 解析新加载的数据
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
    主函数，初始化 Playwright 并执行解题脚本。
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False,channel="chrome",args=[
                    "--disable-blink-features=AutomationControlled",
                    '--log-level=3',
                ],
                ignore_default_args=["--enable-automation"],)
        page = browser.new_page()
        
        url = "https://www.mashangpa.com/problem-detail/7/"
        print(f"正在访问页面: {url}")
        page.goto(url, timeout=60000)

        print("请在15秒内完成登录（如果需要）...")
        time.sleep(30)
        print("等待结束，开始执行自动化任务。")

        solve_problem(page)

        print("\n脚本执行完毕，5秒后将自动关闭浏览器...")
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()