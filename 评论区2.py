from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import pyperclip

# 配置部分
MESSAGE = "‍‍‍‍‍‍‍‍‍‍‍‍‍‍‍‍啊啊啊啊"  # 要发送的私信内容
COOKIES_PATH = "bilibili_cookies.json"  # 登录后保存的cookie路径
SENT_USERS_PATH = "sent_users.json"  # 已发送用户记录文件

# 初始化浏览器
def init_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")  # 最大化窗口
    driver = webdriver.Chrome(options=options)
    return driver

# 登录B站（手动登录一次保存cookies）
def login_bilibili(driver):
    driver.get("https://www.bilibili.com")
    print("请手动登录B站...")
    time.sleep(20)  # 等待用户手动登录
    print("登录完成，保存Cookies")
    cookies = driver.get_cookies()
    with open(COOKIES_PATH, "w", encoding="utf-8") as f:
        json.dump(cookies, f)

# 加载Cookies
def load_cookies(driver):
    if not os.path.exists(COOKIES_PATH):
        raise Exception("Cookies文件不存在，请先手动登录保存Cookies")
    driver.get("https://www.bilibili.com")
    with open(COOKIES_PATH, "r", encoding="utf-8") as f:
        cookies = json.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(20)

# 加载已发送用户记录
def load_sent_usernames():
    if os.path.exists(SENT_USERS_PATH):
        with open(SENT_USERS_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

# 保存已发送用户记录
def save_sent_usernames(sent_usernames):
    with open(SENT_USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(list(sent_usernames), f)

# 递归进入 Shadow DOM 定位元素
def find_shadow_element(driver, root_element, css_selector):
    try:
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", root_element)
        if shadow_root:
            return shadow_root.find_element(By.CSS_SELECTOR, css_selector)
        return None
    except Exception as e:
        print(f"Shadow DOM 定位失败：{e}")
        return None

# 切换评论区为“最新”排序
def click_sort_actions(driver, video_url):
    try:
        # 打开指定页面
        driver.get(video_url)
        print("正在访问指定的视频页面...")

        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "commentapp"))
        )
        print("页面加载完成，定位到评论区 commentapp")

        # 滚动到评论区确保其加载
        comment_app = driver.find_element(By.ID, "commentapp")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_app)
        print("滚动到评论区")

        # 增加等待时间，确保动态评论区内容加载完成
        time.sleep(3)  # 如果内容加载较慢，可以适当增加这个时间

        # 等待 bili-comments 元素加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "bili-comments"))
        )
        bili_comments = driver.find_element(By.TAG_NAME, "bili-comments")
        print("成功定位到 <bili-comments> 组件")

        # Step 1: 进入 bili-comments 的 Shadow DOM
        bili_shadow_root = driver.execute_script("return arguments[0].shadowRoot", bili_comments)
        if not bili_shadow_root:
            print("未能进入 bili-comments 的 Shadow DOM")
            return False
        print("成功进入 bili-comments 的 Shadow DOM")

        # Step 2: 等待并定位到 div#header
        WebDriverWait(driver, 10).until(
            lambda d: bili_shadow_root.find_element(By.CSS_SELECTOR, "#header")
        )
        header_element = bili_shadow_root.find_element(By.CSS_SELECTOR, "#header")
        print("成功定位到 id='header'")

        # Step 3: 定位到 bili-comments-header-renderer
        bili_header_renderer = header_element.find_element(By.TAG_NAME, "bili-comments-header-renderer")
        print("成功定位到 bili-comments-header-renderer")

        # Step 4: 进入 bili-comments-header-renderer 的 Shadow DOM
        bili_header_shadow = driver.execute_script("return arguments[0].shadowRoot", bili_header_renderer)
        if not bili_header_shadow:
            print("未能进入 bili-comments-header-renderer 的 Shadow DOM")
            return False
        print("成功进入 bili-comments-header-renderer 的 Shadow DOM")

        # Step 5: 等待并定位到 div#navbar
        WebDriverWait(driver, 10).until(
            lambda d: bili_header_shadow.find_element(By.CSS_SELECTOR, "#navbar")
        )
        navbar_element = bili_header_shadow.find_element(By.CSS_SELECTOR, "#navbar")
        print("成功定位到 div#navbar")

        # Step 6: 定位到 id="sort-actions"
        sort_actions = navbar_element.find_element(By.CSS_SELECTOR, "#sort-actions")
        print("成功定位到 id='sort-actions'")

        # Step 7: 定位到 sort-actions 中的 bili-text-button
        bili_text_buttons = sort_actions.find_elements(By.TAG_NAME, "bili-text-button")
        print(f"找到 {len(bili_text_buttons)} 个 bili-text-button 元素")

        # 检查是否有足够的 bili-text-button 元素
        if len(bili_text_buttons) < 2:
            print("未找到足够的 bili-text-button 元素")
            return False

        # 定位第二个 bili-text-button 的 Shadow DOM
        second_bili_button = bili_text_buttons[1]
        second_button_shadow = driver.execute_script("return arguments[0].shadowRoot", second_bili_button)
        if not second_button_shadow:
            print("未能进入第二个 bili-text-button 的 Shadow DOM")
            return False
        print("成功进入第二个 bili-text-button 的 Shadow DOM")

        # Step 8: 定位 class="button   " 的元素
        button_element = second_button_shadow.find_element(By.CSS_SELECTOR, ".button")
        if not button_element:
            print("未找到 class='button ' 的元素")
            return False

        # 点击该元素
        button_element.click()
        print("成功点击第二个 bili-text-button 的 class='button ' 的元素")
        return True

    except Exception as e:
        print(f"切换评论区为最新排序失败：{e}")
        return False

def get_recent_comment_users(driver, video_url):
    if not click_sort_actions(driver, video_url):
        print("无法切换到最新排序，获取评论失败")
        return []
    
    # 等待评论区加载完成
    time.sleep(3)
    print("开始获取评论用户信息...")

    users = []

    try:
        # Step 1: 定位到 ID 为 'commentapp' 的主容器
        print("尝试定位 ID 为 'commentapp' 的主容器...")
        comment_app_div = driver.find_element(By.ID, "commentapp")
        print("成功定位 'commentapp' 容器")
        
        # Step 2: 定位到 'bili-comments' 组件
        print("尝试定位 'bili-comments' 组件...")
        bili_comments_component = comment_app_div.find_element(By.TAG_NAME, "bili-comments")
        print("成功定位 'bili-comments' 组件")

        # Step 3: 获取 'bili-comments' 的 Shadow DOM
        print("尝试获取 'bili-comments' 的 Shadow DOM...")
        bili_comments_shadow_root = driver.execute_script("return arguments[0].shadowRoot", bili_comments_component)
        if not bili_comments_shadow_root:
            print("'bili-comments' 的 Shadow DOM 为空")
            return []
        print("成功获取 'bili-comments' 的 Shadow DOM")

        # Step 4: 定位到 Shadow DOM 中的 div ID 为 'contents'
        print("尝试在 'bili-comments' 的 Shadow DOM 中定位 ID 为 'contents' 的 div...")
        contents_div = bili_comments_shadow_root.find_element(By.ID, "contents")
        print("成功定位 'contents' 容器")

        # Step 5: 定位到 'contents' 下的 div ID 为 'feed'
        print("尝试在 'contents' 中定位 ID 为 'feed' 的 div...")
        feed_div = contents_div.find_element(By.ID, "feed")
        print("成功定位 'feed' 容器")

        # Step 6: 定位到 'feed' 下的 'bili-comment-thread-renderer' 组件
        print("尝试查找所有 'bili-comment-thread-renderer' 元素...")
        thread_renderers = feed_div.find_elements(By.TAG_NAME, "bili-comment-thread-renderer")
        print(f"找到 {len(thread_renderers)} 个 'bili-comment-thread-renderer' 元素")

        for idx, thread_renderer in enumerate(thread_renderers):
            if idx == 0:
                # 跳过第一个（UP主）
                print(f"第 {idx + 1} 个评论为 UP 主，跳过")
                continue
            
            # 只获取前 10 个用户（跳过第一个后只获取 10 个）
            if len(users) >= 20:
                break

            print(f"处理第 {idx + 1} 个评论线程组件...")

            try:
                # Step 7: 获取 'bili-comment-thread-renderer' 的 Shadow DOM
                print(f"尝试获取第 {idx + 1} 个评论线程的 Shadow DOM...")
                thread_shadow_root = driver.execute_script("return arguments[0].shadowRoot", thread_renderer)
                if not thread_shadow_root:
                    print(f"第 {idx + 1} 个评论线程的 Shadow DOM 为空，跳过")
                    continue
                print(f"成功获取第 {idx + 1} 个评论线程的 Shadow DOM")

                # Step 8: 定位到 Shadow DOM 中的 'bili-comment-renderer' 组件，ID 为 'comment'
                print(f"尝试查找第 {idx + 1} 个评论中的 'bili-comment-renderer' 元素（ID 为 'comment'）...")
                comment_renderer = thread_shadow_root.find_element(By.CSS_SELECTOR, "bili-comment-renderer#comment")
                print(f"成功找到第 {idx + 1} 个评论的 'bili-comment-renderer' 元素")

                # Step 9: 获取 'bili-comment-renderer' 的 Shadow DOM
                print(f"尝试获取第 {idx + 1} 个评论的 'bili-comment-renderer' 的 Shadow DOM...")
                comment_shadow_root = driver.execute_script("return arguments[0].shadowRoot", comment_renderer)
                if not comment_shadow_root:
                    print(f"第 {idx + 1} 个评论的 'bili-comment-renderer' 的 Shadow DOM 为空，跳过")
                    continue
                print(f"成功获取第 {idx + 1} 个评论的 'bili-comment-renderer' 的 Shadow DOM")

                # Step 10: 定位到 Shadow DOM 中的 div ID 为 'body'
                print(f"尝试定位第 {idx + 1} 个评论的 div ID 为 'body'...")
                body_div = comment_shadow_root.find_element(By.ID, "body")
                print(f"成功定位 div ID 为 'body'")

                # Step 11: 定位到 'body' 下的 div ID 为 'main'
                print(f"尝试定位 div ID 为 'main'...")
                main_div = body_div.find_element(By.ID, "main")
                print(f"成功定位 div ID 为 'main'")

                # Step 12: 定位到 'main' 下的 div ID 为 'header'
                print(f"尝试定位 div ID 为 'header'...")
                header_div = main_div.find_element(By.ID, "header")
                print(f"成功定位 div ID 为 'header'")

                # Step 13: 定位到 'header' 下的 'bili-comment-user-info' 组件
                print(f"尝试定位 'bili-comment-user-info' 组件...")
                user_info_component = header_div.find_element(By.CSS_SELECTOR, "bili-comment-user-info")
                print(f"成功找到 'bili-comment-user-info' 组件")

                # Step 14: 获取 'bili-comment-user-info' 的 Shadow DOM
                print(f"尝试获取 'bili-comment-user-info' 的 Shadow DOM...")
                user_shadow_root = driver.execute_script("return arguments[0].shadowRoot", user_info_component)
                if not user_shadow_root:
                    print(f"第 {idx + 1} 个评论的 'bili-comment-user-info' 的 Shadow DOM 为空，跳过")
                    continue
                print(f"成功获取 'bili-comment-user-info' 的 Shadow DOM")

                # Step 15: 定位到 Shadow DOM 中的 div ID 为 'info'，然后定位到 'user-name'
                print(f"尝试查找用户名...")
                user_info_div = user_shadow_root.find_element(By.ID, "info")
                user_name_div = user_info_div.find_element(By.ID, "user-name")
                user_link_element = user_name_div.find_element(By.TAG_NAME, "a")
                username = user_link_element.text.strip()
                profile_url = user_link_element.get_attribute("href")
                print(f"成功获取用户名：{username}，用户链接：{profile_url}")

                if username:
                    users.append({
                        "name": username,
                        "profile_url": profile_url
                    })
                else:
                    print(f"第 {idx + 1} 个评论的用户名为空，跳过")

            except Exception as e:
                print(f"处理第 {idx + 1} 个评论时出错：{e}")
                continue

    except Exception as e:
        print(f"获取评论线程时出错：{e}")

    print(f"成功获取 {len(users)} 个用户")
    return users

# 私信逻辑
def send_message_to_user(driver, user):
    try:
        print(f"正在尝试发送私信给：{user['name']}")

        # 点击用户名，进入用户主页（会打开新页面）
        driver.execute_script(f"window.open('{user['profile_url']}', '_blank');")
        time.sleep(2)  # 等待新页面打开

        # 获取当前窗口句柄
        current_window = driver.current_window_handle  

        # 获取所有窗口句柄并切换到新打开的粉丝主页窗口
        all_windows = driver.window_handles
        new_window = [window for window in all_windows if window != current_window][0]
        driver.switch_to.window(new_window)

        # 点击粉丝主页中的“发消息”按钮 - 修改后的选择器
        try:
            print("尝试点击粉丝主页的发消息按钮...")
            message_button = driver.find_element(By.CSS_SELECTOR, ".message-btn")
            message_button.click()
            print("成功点击发消息按钮！")
        except Exception as e:
            print(f"未找到粉丝主页的发消息按钮，错误信息：{e}")
            driver.close()  # 关闭新窗口
            driver.switch_to.window(current_window)
            return False

        # 此时私信页面应打开新窗口，再次获取窗口句柄并切换
        all_windows = driver.window_handles
        private_message_window = [window for window in all_windows if window != current_window and window != new_window][0]
        driver.switch_to.window(private_message_window)  # 切换到私信窗口
        time.sleep(1)  # 等待私信页面加载完成
        # 定位到文本框
        print("定位到文本框...")
        try:
            editor = driver.find_element(By.CLASS_NAME, "brt-editor")  # 根据 ID 定位输入框
        except Exception as e:
            print(f"定位文本框失败，尝试等待页面完全加载，错误信息：{e}")
            time.sleep(3)  # 增加等待时间，确保页面完全加载
            editor = driver.find_element(By.CLASS_NAME, "brt-editor") 

    
        # 使用粘贴的方式插入内容
        print(f"准备以粘贴方式插入内容，内容为：\n{MESSAGE}")
        try:
            pyperclip.copy(MESSAGE)
            editor.click()
            if os.name == 'nt':  # Windows
                editor.send_keys(Keys.CONTROL, 'v')
            else:  # MacOS/Linux
                editor.send_keys(Keys.COMMAND, 'v')

            print("内容已成功粘贴到文本框！")
        except Exception as e:
            print(f"粘贴内容失败，错误信息：{e}")
            driver.close()
            driver.switch_to.window(current_window)
            return False

        # 点击发送按钮
        print("尝试点击发送按钮...")
        try:
            send_button = driver.find_element(By.CLASS_NAME, "_MessageSendBox__SendBtn_125bg_58")
            send_button.click()
            time.sleep(1)
        except Exception as e:
            print(f"发送按钮点击失败，错误信息：{e}")
            driver.close()
            driver.switch_to.window(current_window)
            return False

        # 关闭所有相关窗口并切回主窗口
        print("等待3秒后关闭粉丝主页和私信页面窗口...")
        driver.close()  # 关闭私信页面窗口
        driver.switch_to.window(new_window)  # 切回粉丝主页窗口
        driver.close()  # 关闭粉丝主页窗口
        driver.switch_to.window(current_window)  # 切回主窗口
        print("切回主窗口成功！")
        time.sleep(1)
        return True

    except Exception as e:
        print(f"发送私信失败，错误信息：{e}")
        try:
            driver.close()  # 尝试关闭新窗口（如果打开了）
        except:
            pass
        driver.switch_to.window(current_window)  # 切回主窗口
        time.sleep(1)
        return False



def main():
    driver = init_browser()
    sent_usernames = load_sent_usernames()

    # 视频任务队列
    VIDEO_URLS = [
               "https://www.bilibili.com/video/BV1dzVJzeEi4/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
       "https://www.bilibili.com/video/BV1iuVxzJECp/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
       "https://www.bilibili.com/video/BV1UMVbz2EUK/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
       "https://www.bilibili.com/video/BV1bZVgzhE7Z/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
       "https://www.bilibili.com/video/BV1xPV1zsEZm/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV16bQtYEECx?spm_id_from=333.788.recommend_more_video.1&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1HwZ8YTEcu?spm_id_from=333.788.recommend_more_video.-1&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1g7dwYvENg?spm_id_from=333.788.recommend_more_video.0&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1n5QHYeERN?spm_id_from=333.788.recommend_more_video.-1&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1RBdTYxEpX?spm_id_from=333.788.recommend_more_video.-1&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1c1Lkz2EX9/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1JaG1zGEvd/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1bFVwzME49/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1dMVAzDEgD/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1FvoMY3EEd?spm_id_from=333.788.recommend_more_video.8&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1bqC1YtEXA?spm_id_from=333.788.recommend_more_video.-1&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV19x4y1E7gZ?spm_id_from=333.788.recommend_more_video.0&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1v1L3zLEYJ/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1VsVuzNEti/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV18yZ9YREQc?spm_id_from=333.788.recommend_more_video.0&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1TcV3zbEbq/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1c1Lkz2EX9/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV18yZ9YREQc?spm_id_from=333.788.recommend_more_video.-1&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1UuGeztERq/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1nKKKeREMb?spm_id_from=333.788.recommend_more_video.0&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1bqC1YtEXA?spm_id_from=333.788.recommend_more_video.0&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1JcLBzcEk9/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1v4dqYLEfz/?spm_id_from=333.1387.homepage.video_card.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1RijwzWEk8/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1aBGXznEgY/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1VeGrzsEsq?spm_id_from=333.788.recommend_more_video.0&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1YLRRYXEnH/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1RBdTYxEpX/?spm_id_from=333.1387.homepage.video_card.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1WMZ4YvEia/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV15oVjzxEgA/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1VyG1zPEY9/?spm_id_from=333.337.search-card.all.click&vd_source=e66614dc8905ed77322d9de68f16d030",
        "https://www.bilibili.com/video/BV1nKKKeREMb?spm_id_from=333.788.recommend_more_video.-1&vd_source=e66614dc8905ed77322d9de68f16d030",

    ]

    try:
        # 加载Cookies或登录
        if not os.path.exists(COOKIES_PATH):
            print("未检测到 Cookies 文件，将进入手动扫码登录流程...")
            driver.get("https://www.bilibili.com")
            print("请扫码登录 B站（10秒后自动继续）...")
            time.sleep(20)
            print("登录完成，保存 Cookies...")
            cookies = driver.get_cookies()
            with open(COOKIES_PATH, "w", encoding="utf-8") as f:
                json.dump(cookies, f)
        else:
            load_cookies(driver)

        # 无限循环处理视频任务队列
        while True:
            for video_url in VIDEO_URLS:
                print(f"开始处理视频：{video_url}")

                while True:
                    # 获取最新评论的用户列表
                    users = get_recent_comment_users(driver, video_url)

                    # 过滤出未发送私信的新用户
                    new_users = [user for user in users if user['name'] not in sent_usernames]

                    if not new_users:
                        print(f"视频 {video_url} 没有新的用户需要私信，切换到下一个视频...")
                        break  # 当前视频任务完成，切换到下一个视频

                    # 给每个新用户发送私信
                    for user in new_users:
                        if send_message_to_user(driver, user):
                            sent_usernames.add(user['name'])  # 添加到已发送用户名列表
                            save_sent_usernames(sent_usernames)  # 保存记录
                        else:
                            print(f"发送私信失败，跳过用户 {user['name']}")
                            sent_usernames.add(user['name'])
                            save_sent_usernames(sent_usernames)

                print(f"视频 {video_url} 的所有任务已完成，切换到下一个视频...")

            # 当所有视频任务都完成后，等待一段时间后再从头开始
            print("所有视频任务完成，等待 10 秒后重新开始...")
            time.sleep(10)

    except Exception as e:
        print(f"运行出错：{e}")
    finally:
        driver.quit()
if __name__ == "__main__":
    main()

