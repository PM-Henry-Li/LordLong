#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时调试脚本 - 使用非无头模式查看实际页面
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Chrome选项
chrome_options = Options()
# 不使用无头模式,可以看到浏览器
# chrome_options.add_argument("--headless=new")

# 反爬虫设置
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# User-Agent
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

print("启动浏览器...")
driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(10)

try:
    # 访问搜索页面
    url = "https://www.xiaohongshu.com/search_result?keyword=故宫太和殿"
    print(f"访问: {url}")
    driver.get(url)
    
    # 等待页面加载
    print("等待页面加载...")
    time.sleep(5)
    
    # 尝试不同的选择器
    selectors_to_try = [
        "section",
        "section.note-item",
        "a.cover",
        "div.note-item",
        ".note-item",
        "article",
    ]
    
    print("\n测试不同选择器:")
    print("=" * 60)
    
    for selector in selectors_to_try:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"✓ {selector:30s} -> 找到 {len(elements)} 个元素")
            
            # 如果找到元素,打印第一个元素的HTML(前200个字符)
            if elements:
                html = elements[0].get_attribute('outerHTML')[:200]
                print(f"  第一个元素HTML: {html}...")
                print()
        except Exception as e:
            print(f"✗ {selector:30s} -> 错误: {e}")
    
    print("=" * 60)
    print("\n页面标题:", driver.title)
    print("当前URL:", driver.current_url)
    
    # 保存页面源代码用于分析
    with open("debug_page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("\n页面源代码已保存到: debug_page_source.html")
    
    print("\n浏览器将在30秒后关闭...")
    time.sleep(30)
    
finally:
    driver.quit()
    print("浏览器已关闭")
