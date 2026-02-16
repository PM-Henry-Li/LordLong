#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书内容搜索器
使用浏览器自动化搜索小红书,提取高分笔记内容
"""

import os
import json
import time
from typing import List, Dict, Optional
import re


class XiaohongshuScraper:
    """小红书内容搜索器"""

    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化搜索器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.xhs_config = self.config.get("xiaohongshu", {})
        self.driver = None

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        default_xhs_config = {
            "search_mode": "browser",
            "browser_type": "chrome",
            "headless": False,  # 小红书在无头模式下可能不加载内容
            "max_search_results": 10,
            "min_likes_threshold": 1000,
            "login_required": False,
            "request_delay": 2,  # 请求间隔(秒)
        }

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf - 8") as f:
                config = json.load(f)
                if "xiaohongshu" not in config:
                    config["xiaohongshu"] = default_xhs_config
                else:
                    # 合并默认配置
                    for key, value in default_xhs_config.items():
                        if key not in config["xiaohongshu"]:
                            config["xiaohongshu"][key] = value
                return config
        else:
            return {"xiaohongshu": default_xhs_config}

    def _init_browser(self):
        """初始化浏览器驱动"""
        if self.driver:
            return

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options

            chrome_options = Options()

            # 设置无头模式
            if self.xhs_config.get("headless", True):
                chrome_options.add_argument("--headless=new")  # 使用新的headless模式
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")

            # 反爬虫设置
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)

            # 设置User-Agent
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )

            # 初始化驱动 - 优先使用系统chromedriver
            try:
                # 尝试直接使用系统的chromedriver
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✅ 浏览器驱动初始化成功 (系统驱动)")
            except Exception:
                # 如果系统没有chromedriver,尝试用webdriver-manager下载
                try:
                    from webdriver_manager.chrome import ChromeDriverManager

                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("✅ 浏览器驱动初始化成功 (自动下载)")
                except Exception as e:
                    raise RuntimeError(
                        f"无法初始化Chrome驱动。请确保: 1)已安装Chrome浏览器 2)网络连接正常 3)或手动安装chromedriver。错误: {e}"
                    )

            # 设置隐式等待
            self.driver.implicitly_wait(10)

        except Exception as e:
            raise RuntimeError(f"❌ 浏览器驱动初始化失败: {e}")

    def search_by_topic(self, topic: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        根据主题搜索小红书笔记

        Args:
            topic: 搜索主题关键词
            max_results: 最大结果数(None则使用配置文件中的值)

        Returns:
            笔记列表,每个笔记包含 title, author, likes, url, preview_text 等信息
        """
        if max_results is None:
            max_results = self.xhs_config.get("max_search_results", 10)

        print(f"\n🔍 开始搜索主题: {topic}")
        print(f"   目标获取: {max_results} 条笔记")

        try:
            pass

            # 初始化浏览器
            self._init_browser()

            # 构建搜索URL
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={topic}&source=web_search_result_notes"
            self.driver.get(search_url)

            # 等待页面加载
            time.sleep(3)

            # 滑动页面以加载更多内容
            self._scroll_page(scroll_times=3)

            # 提取笔记卡片
            notes = self._extract_note_cards(max_results)

            print(f"✅ 成功获取 {len(notes)} 条笔记")
            return notes

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            raise

    def _scroll_page(self, scroll_times: int = 3):
        """
        滑动页面以加载更多内容

        Args:
            scroll_times: 滑动次数
        """
        for i in range(scroll_times):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.xhs_config.get("request_delay", 2))
            print(f"   📄 滑动页面 ({i + 1}/{scroll_times})")

    def _extract_note_cards(self, max_results: int) -> List[Dict]:
        """
        提取笔记卡片信息

        Args:
            max_results: 最大提取数量

        Returns:
            笔记列表
        """
        from selenium.webdriver.common.by import By

        notes = []

        try:
            # 小红书的笔记卡片选择器 - 使用section元素
            note_elements = self.driver.find_elements(By.CSS_SELECTOR, "section")

            print(f"   找到 {len(note_elements)} 个笔记元素")

            for idx, element in enumerate(note_elements[: max_results * 2]):  # 多取一些以应对解析失败
                try:
                    note_data = self._parse_note_element(element)
                    if note_data:
                        notes.append(note_data)
                        print(
                            f"   ✓ [{len(notes)}] {note_data.get('title', '无标题')[:30]}... (👍 {note_data.get('likes', 0)})"
                        )

                        # 达到目标数量就停止
                        if len(notes) >= max_results:
                            break
                except Exception:
                    # 静默跳过解析失败的元素
                    continue

        except Exception as e:
            print(f"   ⚠️  提取笔记列表失败: {e}")

        return notes

    def _parse_note_element(self, element) -> Optional[Dict]:
        """
        解析单个笔记元素

        Args:
            element: Selenium WebElement

        Returns:
            笔记数据字典
        """
        from selenium.webdriver.common.by import By

        try:
            note_data = {}

            # 提取标题 - 使用a.title选择器
            try:
                title_elem = element.find_element(By.CSS_SELECTOR, "a.title")
                note_data["title"] = title_elem.text.strip()
            except Exception:
                # 如果没有title,可能不是有效的笔记卡片
                return None

            # 提取链接 - 可以从a.cover或a.title获取
            try:
                # 优先使用title链接
                link_elem = element.find_element(By.CSS_SELECTOR, "a.title, a.cover")
                link = link_elem.get_attribute("href")
                if link:
                    # 如果是相对路径,补全为绝对路径
                    if link.startswith("/"):
                        link = f"https://www.xiaohongshu.com{link}"
                    note_data["url"] = link
                else:
                    return None
            except Exception:
                return None

            # 提取点赞数 - 使用span.count选择器
            try:
                likes_elem = element.find_element(By.CSS_SELECTOR, "span.count")
                likes_text = likes_elem.text.strip()
                note_data["likes"] = self._parse_number(likes_text)
            except Exception:
                note_data["likes"] = 0

            # 提取作者 - 使用a.author选择器
            try:
                author_elem = element.find_element(By.CSS_SELECTOR, "a.author")
                # author可能在子元素中
                author_text = author_elem.text.strip()
                if not author_text:
                    # 尝试从子元素获取
                    author_div = author_elem.find_element(By.CSS_SELECTOR, "div, span")
                    author_text = author_div.text.strip()
                note_data["author"] = author_text if author_text else "未知作者"
            except Exception:
                note_data["author"] = "未知作者"

            # 提取预览文本(尝试从title获取,因为搜索页通常没有完整描述)
            note_data["preview_text"] = note_data["title"]

            return note_data if note_data.get("url") and note_data.get("title") else None

        except Exception:
            return None

    def _parse_number(self, text: str) -> int:
        """
        解析数字文本(支持1.2w, 3k等格式)

        Args:
            text: 数字文本

        Returns:
            整数值
        """
        if not text:
            return 0

        text = text.strip().lower()

        # 移除非数字和单位字符
        multiplier = 1
        if "w" in text or "万" in text:
            multiplier = 10000
            text = text.replace("w", "").replace("万", "")
        elif "k" in text or "千" in text:
            multiplier = 1000
            text = text.replace("k", "").replace("千", "")

        # 提取数字
        match = re.search(r"[\d.]+", text)
        if match:
            number = float(match.group())
            return int(number * multiplier)

        return 0

    def get_note_content(self, note_url: str) -> Optional[Dict]:
        """
        获取单条笔记的详细内容

        Args:
            note_url: 笔记URL

        Returns:
            笔记详细内容字典
        """
        if not note_url:
            return None

        try:
            from selenium.webdriver.common.by import By

            # 初始化浏览器
            self._init_browser()

            print(f"   📖 获取笔记详情: {note_url[:50]}...")

            # 访问笔记页面
            self.driver.get(note_url)
            time.sleep(self.xhs_config.get("request_delay", 2))

            content_data = {}

            # 提取标题
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, "#detail-title, .title")
                content_data["title"] = title_elem.text.strip()
            except Exception:
                content_data["title"] = ""

            # 提取正文
            try:
                content_elem = self.driver.find_element(By.CSS_SELECTOR, "#detail-desc, .desc, .content")
                content_data["content"] = content_elem.text.strip()
            except Exception:
                content_data["content"] = ""

            # 提取标签
            try:
                tag_elements = self.driver.find_elements(By.CSS_SELECTOR, ".tag, .topic")
                content_data["tags"] = [tag.text.strip() for tag in tag_elements]
            except Exception:
                content_data["tags"] = []

            # 提取互动数据
            try:
                likes_elem = self.driver.find_element(By.CSS_SELECTOR, ".like-count")
                content_data["likes"] = self._parse_number(likes_elem.text)
            except Exception:
                content_data["likes"] = 0

            try:
                collect_elem = self.driver.find_element(By.CSS_SELECTOR, ".collect-count")
                content_data["collects"] = self._parse_number(collect_elem.text)
            except Exception:
                content_data["collects"] = 0

            content_data["url"] = note_url

            print("   ✅ 获取成功")
            return content_data

        except Exception as e:
            print(f"   ❌ 获取笔记内容失败: {e}")
            return None

    def filter_high_quality_notes(self, notes: List[Dict], min_likes: Optional[int] = None) -> List[Dict]:
        """
        筛选高质量笔记

        Args:
            notes: 笔记列表
            min_likes: 最小点赞数(None则使用配置文件中的值)

        Returns:
            筛选后的笔记列表
        """
        if min_likes is None:
            min_likes = self.xhs_config.get("min_likes_threshold", 1000)

        print(f"\n🎯 筛选高质量笔记 (最小点赞数: {min_likes})")

        filtered = [note for note in notes if note.get("likes", 0) >= min_likes]

        # 按点赞数排序
        filtered.sort(key=lambda x: x.get("likes", 0), reverse=True)

        print(f"✅ 筛选出 {len(filtered)} 条高质量笔记")

        return filtered

    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("✅ 浏览器已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


def main():
    """测试函数"""
    import argparse

    parser = argparse.ArgumentParser(description="小红书内容搜索器")
    parser.add_argument("topic", help="搜索主题")
    parser.add_argument("-n", "--max-results", type=int, default=10, help="最大结果数")
    parser.add_argument("-m", "--min-likes", type=int, default=1000, help="最小点赞数")
    parser.add_argument("-c", "--config", default="config/config.json", help="配置文件路径")

    args = parser.parse_args()

    # 使用上下文管理器确保浏览器正确关闭
    with XiaohongshuScraper(config_path=args.config) as scraper:
        # 搜索笔记
        notes = scraper.search_by_topic(args.topic, max_results=args.max_results)

        # 筛选高质量笔记
        if notes:
            filtered_notes = scraper.filter_high_quality_notes(notes, min_likes=args.min_likes)

            # 打印结果
            print(f"\n{'=' * 60}")
            print(f"搜索主题: {args.topic}")
            print(f"找到笔记: {len(notes)} 条")
            print(f"高质量笔记: {len(filtered_notes)} 条")
            print(f"{'=' * 60}\n")

            for idx, note in enumerate(filtered_notes, 1):
                print(f"[{idx}] {note.get('title', '无标题')}")
                print(f"    作者: {note.get('author', '未知')}")
                print(f"    点赞: {note.get('likes', 0)}")
                print(f"    链接: {note.get('url', '')}")
                if note.get("preview_text"):
                    print(f"    预览: {note.get('preview_text', '')[:100]}...")
                print()


if __name__ == "__main__":
    main()
