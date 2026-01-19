"""
小红书数据采集模块
Xiaohongshu Data Crawler Module
使用 DrissionPage 进行动态网页爬取
"""

import time
import random
import logging
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from DrissionPage import ChromiumPage

from config import (
    TARGET_KEYWORD,
    MAX_ARTICLES_TO_SCRAPE,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    MAX_RETRIES,
    CRAWLER_TIMEOUT,
    RAW_DATA_FILE,
    USER_AGENTS,
    WINDOW_SIZE,
    BROWSER_HEADLESS
)


class RedNoteCrawler:
    """小红书爬虫类 / Xiaohongshu Crawler Class"""
    
    def __init__(self, keyword: str = None):
        """
        初始化爬虫 / Initialize crawler
        
        Args:
            keyword: 搜索关键词 / Search keyword
        """
        self.keyword = keyword or TARGET_KEYWORD
        self.logger = logging.getLogger(__name__)
        self.page = None
        self.articles_data = []
        
    def _init_browser(self):
        """
        初始化浏览器 / Initialize browser
        
        返回: 是否成功 / Whether successful
        """
        try:
            # 创建浏览器页面 / Create browser page
            self.page = ChromiumPage()
            
            # 设置窗口大小（模拟移动端） / Set window size (simulate mobile)
            self.page.set.window.size(*WINDOW_SIZE)
            
            # 设置随机 User-Agent / Set random User-Agent
            user_agent = random.choice(USER_AGENTS)
            self.page.set.user_agent(user_agent)
            
            self.logger.info(f"浏览器初始化成功 / Browser initialized successfully")
            self.logger.info(f"搜索关键词 / Search keyword: {self.keyword}")
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器初始化失败 / Browser initialization failed: {e}")
            return False
    
    def _random_delay(self):
        """
        随机延时 / Random delay
        用于模拟人类行为，避免被封 / To simulate human behavior and avoid blocking
        """
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        self.logger.debug(f"等待 {delay:.2f} 秒 / Waiting {delay:.2f} seconds")
        time.sleep(delay)
    
    def _extract_article_data(self, article_element) -> Optional[Dict]:
        """
        从文章元素中提取数据 / Extract data from article element
        
        Args:
            article_element: 文章元素对象 / Article element object
            
        Returns:
            文章数据字典 / Article data dictionary
        """
        try:
            # 这里需要根据小红书实际页面结构进行调整
            # This needs to be adjusted based on Xiaohongshu's actual page structure
            
            article_data = {
                "title": "",
                "author": "",
                "link": "",
                "likes": 0,
                "collects": 0,
                "comments": 0,
                "views": 0,
                "content": "",
                "publish_time": "",
                "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 示例：提取标题（需要根据实际页面调整）
            # Example: Extract title (needs adjustment based on actual page)
            try:
                title_elem = article_element.ele('css:.title-selector')
                if title_elem:
                    article_data["title"] = title_elem.text.strip()
            except:
                pass
            
            # 示例：提取链接
            # Example: Extract link
            try:
                link_elem = article_element.ele('css:.link-selector a')
                if link_elem:
                    article_data["link"] = link_elem.attr('href')
            except:
                pass
            
            # 示例：提取互动数据
            # Example: Extract engagement data
            try:
                # 点赞数 / Likes
                likes_elem = article_element.ele('css:.likes-selector')
                if likes_elem:
                    article_data["likes"] = self._parse_number(likes_elem.text)
                
                # 收藏数 / Collects
                collects_elem = article_element.ele('css:.collects-selector')
                if collects_elem:
                    article_data["collects"] = self._parse_number(collects_elem.text)
                
                # 评论数 / Comments
                comments_elem = article_element.ele('css:.comments-selector')
                if comments_elem:
                    article_data["comments"] = self._parse_number(comments_elem.text)
            except:
                pass
            
            # 验证是否有有效数据 / Validate if has valid data
            if article_data["title"] or article_data["link"]:
                return article_data
            
            return None
            
        except Exception as e:
            self.logger.warning(f"提取文章数据失败 / Failed to extract article data: {e}")
            return None
    
    def _parse_number(self, text: str) -> int:
        """
        解析数字文本（如"1.2万"转换为12000）
        Parse number text (e.g., "1.2万" converted to 12000)
        
        Args:
            text: 数字文本 / Number text
            
        Returns:
            整数 / Integer
        """
        if not text:
            return 0
        
        try:
            text = text.strip()
            
            # 处理万 / Handle "万"
            if "万" in text:
                num = float(text.replace("万", ""))
                return int(num * 10000)
            
            # 处理千 / Handle "千"
            if "k" in text.lower() or "K" in text:
                num = float(text.lower().replace("k", ""))
                return int(num * 1000)
            
            # 处理普通数字 / Handle normal number
            return int(text)
            
        except:
            return 0
    
    def _navigate_to_search_page(self) -> bool:
        """
        导航到搜索页面 / Navigate to search page
        
        返回: 是否成功 / Whether successful
        """
        try:
            # 小红书搜索页面URL（实际使用时需要调整）
            # Xiaohongshu search page URL (needs adjustment when using)
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={self.keyword}"
            
            self.logger.info(f"导航到搜索页面 / Navigating to search page: {search_url}")
            self.page.get(search_url)
            
            # 等待页面加载
            self._random_delay()
            
            # 检查是否需要登录 / Check if login is needed
            if self._check_login_required():
                self.logger.warning("可能需要登录 / May require login")
                # 可以在这里添加登录逻辑或提示用户
                # Can add login logic or prompt user here
                # self._login()
            
            return True
            
        except Exception as e:
            self.logger.error(f"导航到搜索页面失败 / Failed to navigate to search page: {e}")
            return False
    
    def _check_login_required(self) -> bool:
        """
        检查是否需要登录 / Check if login is required
        
        返回: 是否需要登录 / Whether login is required
        """
        try:
            # 检查页面是否有登录相关元素
            # Check if page has login-related elements
            login_elements = self.page.eles('css:selector')
            return len(login_elements) > 0
        except:
            return False
    
    def _scroll_and_load(self):
        """
        滚动页面加载更多内容 / Scroll page to load more content
        """
        try:
            # 滚动到底部 / Scroll to bottom
            self.page.scroll.to_bottom()
            
            # 等待内容加载
            self._random_delay()
            
        except Exception as e:
            self.logger.warning(f"滚动页面失败 / Failed to scroll page: {e}")
    
    def _check_connection(self) -> bool:
        """
        检查浏览器连接是否正常 / Check if browser connection is normal
        
        Returns:
            连接是否正常 / Whether connection is normal
        """
        try:
            if not self.page:
                return False
            
            # 尝试获取页面标题或URL来检查连接
            try:
                _ = self.page.url
                return True
            except:
                return False
        except:
            return False
    
    def _reconnect(self) -> bool:
        """
        重新连接浏览器 / Reconnect browser
        
        Returns:
            是否成功 / Whether successful
        """
        try:
            if self.page:
                try:
                    self.page.close()
                except:
                    pass
            
            return self._init_browser() and self._navigate_to_search_page()
        except Exception as e:
            self.logger.error(f"重新连接失败 / Reconnection failed: {e}")
            return False
    
    def scrape_articles(self, num_articles: int = None) -> List[Dict]:
        """
        爬取文章 / Scrape articles
        
        按照解决方案7优化：
        - 增加请求延时，降低请求频率
        - 添加5分钟超时机制
        - 超时后保存已爬取内容并返回
        
        Args:
            num_articles: 要爬取的文章数量 / Number of articles to scrape
            
        Returns:
            文章数据列表 / List of article data
        """
        num_articles = num_articles or MAX_ARTICLES_TO_SCRAPE
        self.articles_data = []
        
        # 记录开始时间
        start_time = time.time()
        timeout_seconds = CRAWLER_TIMEOUT
        
        # 错误统计
        consecutive_errors = 0
        max_consecutive_errors = 5
        reconnect_count = 0
        max_reconnects = 3
        
        try:
            # 初始化浏览器
            if not self._init_browser():
                return []
            
            # 导航到搜索页面
            if not self._navigate_to_search_page():
                return []
            
            self.logger.info(f"开始爬取文章，目标数量 / Start scraping articles, target count: {num_articles}")
            self.logger.info(f"超时时间 / Timeout: {timeout_seconds}秒 ({timeout_seconds/60:.1f}分钟)")
            self.logger.info(f"请求延时 / Request delay: {REQUEST_DELAY_MIN}-{REQUEST_DELAY_MAX}秒")
            
            # 爬取文章 / Scrape articles
            while len(self.articles_data) < num_articles:
                # 检查超时
                elapsed_time = time.time() - start_time
                if elapsed_time >= timeout_seconds:
                    self.logger.warning("="*60)
                    self.logger.warning(f"⏰ 爬虫超时 / Crawler timeout")
                    self.logger.warning("="*60)
                    self.logger.warning(f"已运行时间 / Elapsed time: {elapsed_time:.1f}秒 ({elapsed_time/60:.1f}分钟)")
                    self.logger.warning(f"超时限制 / Timeout limit: {timeout_seconds}秒 ({timeout_seconds/60:.1f}分钟)")
                    self.logger.warning(f"已采集文章数 / Articles collected: {len(self.articles_data)}")
                    self.logger.warning("")
                    self.logger.warning("将保存已爬取的内容并继续执行后续流程")
                    self.logger.warning("Will save collected content and continue with subsequent steps")
                    self.logger.warning("="*60)
                    
                    # 保存已爬取的数据
                    if self.articles_data:
                        self.save_to_csv()
                        self.logger.info(f"已保存 {len(self.articles_data)} 篇已爬取的文章 / Saved {len(self.articles_data)} collected articles")
                    
                    # 返回已爬取的数据
                    return self.articles_data
                
                try:
                    # 检查连接状态
                    if not self._check_connection():
                        consecutive_errors += 1
                        self.logger.warning(f"连接断开，尝试重新连接 ({consecutive_errors}/{max_consecutive_errors}) / Connection lost, attempting reconnect")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            self.logger.error("连接断开次数过多，停止爬取 / Too many connection failures, stopping")
                            break
                        
                        if reconnect_count < max_reconnects:
                            reconnect_count += 1
                            if self._reconnect():
                                consecutive_errors = 0
                                self.logger.info("重新连接成功 / Reconnection successful")
                                # 重新连接后增加延时
                                time.sleep(10)
                            else:
                                self.logger.warning("重新连接失败，等待后重试 / Reconnection failed, waiting before retry")
                                time.sleep(15)
                        else:
                            self.logger.error("重新连接次数已达上限，停止爬取 / Max reconnects reached, stopping")
                            break
                        continue
                    
                    # 重置连续错误计数（连接正常）
                    consecutive_errors = 0
                    
                    # 获取当前页面的文章元素 / Get article elements on current page
                    # 注意：CSS选择器需要根据实际页面调整
                    # Note: CSS selector needs adjustment based on actual page
                    article_elements = self.page.eles('css:.article-item-selector')
                    
                    # 如果找不到元素，可能是页面结构变化或需要等待
                    if not article_elements:
                        self.logger.debug("未找到文章元素，等待页面加载 / No article elements found, waiting for page load")
                        time.sleep(5)
                        continue
                    
                    # 提取文章数据
                    new_articles_count = 0
                    for article_elem in article_elements:
                        if len(self.articles_data) >= num_articles:
                            break
                        
                        article_data = self._extract_article_data(article_elem)
                        
                        if article_data:
                            # 检查是否重复（根据链接）
                            if not any(a.get('link') == article_data.get('link') for a in self.articles_data):
                                self.articles_data.append(article_data)
                                new_articles_count += 1
                                self.logger.info(f"已采集 {len(self.articles_data)}/{num_articles} 篇文章 / Scraped {len(self.articles_data)}/{num_articles} articles")
                    
                    # 如果本次没有采集到新文章，增加等待时间
                    if new_articles_count == 0:
                        self.logger.debug("本次未采集到新文章，增加等待时间 / No new articles collected, increasing wait time")
                        time.sleep(REQUEST_DELAY_MAX)
                    
                    # 如果还需要更多文章，滚动加载
                    if len(self.articles_data) < num_articles:
                        self._scroll_and_load()
                        # 按照解决方案7：增加延时，降低请求频率
                        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
                        self.logger.debug(f"等待 {delay:.1f} 秒后继续 / Waiting {delay:.1f}s before continuing")
                        time.sleep(delay)
                    else:
                        break
                        
                except Exception as e:
                    error_msg = str(e)
                    consecutive_errors += 1
                    
                    # 检查是否是连接断开错误
                    if "连接已断开" in error_msg or "disconnected" in error_msg.lower():
                        self.logger.warning(f"连接断开错误 ({consecutive_errors}/{max_consecutive_errors}) / Connection error: {error_msg[:100]}")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            self.logger.error("连接断开次数过多，停止爬取 / Too many connection failures, stopping")
                            break
                        
                        # 尝试重新连接
                        if reconnect_count < max_reconnects:
                            reconnect_count += 1
                            if self._reconnect():
                                consecutive_errors = 0
                                time.sleep(10)
                            else:
                                time.sleep(15)
                        else:
                            self.logger.error("重新连接次数已达上限，停止爬取 / Max reconnects reached, stopping")
                            break
                    else:
                        self.logger.warning(f"爬取过程中出错 ({consecutive_errors}/{max_consecutive_errors}) / Error during scraping: {error_msg[:200]}")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            self.logger.error("连续错误次数过多，停止爬取 / Too many consecutive errors, stopping")
                            break
                        
                        # 普通错误，等待后继续
                        time.sleep(REQUEST_DELAY_MAX)
            
            # 检查是否因为超时或错误而提前结束
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout_seconds:
                self.logger.warning(f"爬取因超时结束，已运行 {elapsed_time:.1f}秒 / Scraping ended due to timeout, ran for {elapsed_time:.1f}s")
            elif len(self.articles_data) < num_articles:
                self.logger.warning(f"爬取因错误提前结束，已采集 {len(self.articles_data)}/{num_articles} 篇 / Scraping ended early due to errors")
            
            # 保存数据
            if self.articles_data:
                self.save_to_csv()
            
            self.logger.info(f"文章爬取完成，共采集 {len(self.articles_data)} 篇 / Scraping completed, total {len(self.articles_data)} articles")
            self.logger.info(f"总耗时 / Total time: {elapsed_time:.1f}秒 ({elapsed_time/60:.1f}分钟)")
            
            return self.articles_data
            
        except Exception as e:
            self.logger.error(f"爬取文章失败 / Failed to scrape articles: {e}")
            # 即使失败，也保存已爬取的数据
            if self.articles_data:
                self.save_to_csv()
                self.logger.info(f"已保存 {len(self.articles_data)} 篇已爬取的文章 / Saved {len(self.articles_data)} collected articles")
            return self.articles_data
        
        finally:
            # 关闭浏览器 / Close browser
            if self.page:
                try:
                    self.page.close()
                    self.logger.info("浏览器已关闭 / Browser closed")
                except:
                    pass
    
    def save_to_csv(self, data: List[Dict] = None, filename: str = None):
        """
        保存数据到CSV文件 / Save data to CSV file
        
        Args:
            data: 要保存的数据 / Data to save
            filename: 文件名 / Filename
        """
        try:
            data = data or self.articles_data
            filename = filename or RAW_DATA_FILE
            
            if not data:
                self.logger.warning("没有数据可保存 / No data to save")
                return
            
            # 转换为DataFrame / Convert to DataFrame
            df = pd.DataFrame(data)
            
            # 保存到CSV / Save to CSV
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            
            self.logger.info(f"数据已保存到 / Data saved to {filename}")
            self.logger.info(f"共保存 {len(data)} 条记录 / Total {len(data)} records saved")
            
        except Exception as e:
            self.logger.error(f"保存CSV文件失败 / Failed to save CSV file: {e}")
    
    def load_from_csv(self, filename: str = None) -> List[Dict]:
        """
        从CSV文件加载数据 / Load data from CSV file
        
        Args:
            filename: 文件名 / Filename
            
        Returns:
            数据列表 / Data list
        """
        try:
            filename = filename or RAW_DATA_FILE
            
            # 读取CSV / Read CSV
            df = pd.read_csv(filename, encoding="utf-8-sig")
            
            # 转换为字典列表 / Convert to list of dictionaries
            data = df.to_dict('records')
            
            self.logger.info(f"从 {filename} 加载了 {len(data)} 条记录 / Loaded {len(data)} records from {filename}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"加载CSV文件失败 / Failed to load CSV file: {e}")
            return []


# 便捷函数 / Convenience functions
def scrape_rednote_articles(keyword: str, num_articles: int = 200) -> List[Dict]:
    """
    便捷的爬取函数 / Convenient scraping function
    
    Args:
        keyword: 搜索关键词 / Search keyword
        num_articles: 文章数量 / Number of articles
        
    Returns:
        文章数据列表 / List of article data
    """
    crawler = RedNoteCrawler(keyword=keyword)
    articles = crawler.scrape_articles(num_articles=num_articles)
    crawler.save_to_csv()
    return articles


if __name__ == "__main__":
    # 设置日志 / Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 示例使用 / Example usage
    crawler = RedNoteCrawler(keyword="极简装修")
    articles = crawler.scrape_articles(num_articles=50)
    crawler.save_to_csv()
    
    print(f"采集完成 / Scraping completed: {len(articles)} 篇文章 / articles")
