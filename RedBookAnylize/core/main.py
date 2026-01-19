"""
小红书竞品分析与爆款内容生成系统 - 主程序入口
Xiaohongshu Competitor Analysis and Viral Content Generation System - Main Entry Point

完整流程：
1. 数据采集（爬虫）
2. 数据分析与排序
3. 内容生成（AI）
4. 视觉提示词生成（AI）
"""

import logging
import argparse
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    TARGET_KEYWORD,
    MAX_ARTICLES_TO_SCRAPE,
    setup_logging,
    validate_config
)

# 尝试导入爬虫模块（如果未安装依赖则跳过）
try:
    from crawler import RedNoteCrawler
    HAS_CRAWLER = True
except ImportError as e:
    HAS_CRAWLER = False
    RedNoteCrawler = None
    logging.warning(f"爬虫模块导入失败，将跳过爬虫功能 / Crawler module import failed: {e}")

from analyzer import RedNoteAnalyzer
from content_generator import ContentGenerator
from visual_generator import VisualPromptGenerator


class RedNoteWorkflow:
    """小红书工作流管理器 / Xiaohongshu Workflow Manager"""
    
    def __init__(self, keyword: str = None):
        """
        初始化工作流 / Initialize workflow
        
        Args:
            keyword: 目标关键词 / Target keyword
        """
        self.keyword = keyword or TARGET_KEYWORD
        self.logger = setup_logging()
        
        self.logger.info("="*60)
        self.logger.info("小红书竞品分析与爆款内容生成系统")
        self.logger.info("Xiaohongshu Competitor Analysis & Content Generation System")
        self.logger.info("="*60)
        self.logger.info(f"目标关键词 / Target Keyword: {self.keyword}")
        self.logger.info(f"启动时间 / Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("="*60 + "\n")
    
    def run_crawler(self, num_articles: int = None) -> bool:
        """
        运行爬虫 / Run crawler
        
        Args:
            num_articles: 爬取文章数量 / Number of articles to scrape
            
        Returns:
            是否成功 / Whether successful
            
        Raises:
            SystemExit: 如果爬虫失败，终止程序
        """
        # 检查爬虫模块是否可用
        if not HAS_CRAWLER or RedNoteCrawler is None:
            self.logger.error("="*60)
            self.logger.error("❌ 爬虫模块未安装或导入失败 / Crawler module not available")
            self.logger.error("="*60)
            self.logger.error("")
            self.logger.error("【失败原因 / Failure Reason】")
            self.logger.error("  爬虫依赖模块未正确安装或导入失败")
            self.logger.error("  Crawler dependency module not installed or import failed")
            self.logger.error("")
            self.logger.error("【解决方案 / Solution】")
            self.logger.error("  1. 安装依赖包 / Install dependencies:")
            self.logger.error("     pip3 install DrissionPage pandas --user")
            self.logger.error("")
            self.logger.error("  2. 或使用 --skip-crawler 参数跳过爬虫功能:")
            self.logger.error("     python3 main.py --skip-crawler -k '关键词'")
            self.logger.error("")
            self.logger.error("="*60)
            self.logger.error("程序已终止 / Program terminated")
            self.logger.error("="*60)
            return False
        
        try:
            self.logger.info("第一步 / Step 1: 开始数据采集 / Starting data collection")
            self.logger.info("-" * 60)
            
            num_articles = num_articles or MAX_ARTICLES_TO_SCRAPE
            
            crawler = RedNoteCrawler(keyword=self.keyword)
            articles = crawler.scrape_articles(num_articles=num_articles)
            
            # 检查是否有已爬取的数据（即使数量不足）
            if not articles:
                # 检查是否有已保存的数据文件
                from config import RAW_DATA_FILE
                if os.path.exists(RAW_DATA_FILE):
                    import pandas as pd
                    try:
                        df = pd.read_csv(RAW_DATA_FILE, encoding="utf-8-sig")
                        if len(df) > 0:
                            self.logger.warning("="*60)
                            self.logger.warning("⚠️  爬虫未采集到新数据，但发现已有数据文件 / No new data collected, but found existing data file")
                            self.logger.warning("="*60)
                            self.logger.warning(f"将使用已有数据文件继续执行: {RAW_DATA_FILE}")
                            self.logger.warning(f"已有数据量 / Existing data: {len(df)} 条记录")
                            self.logger.warning("="*60 + "\n")
                            return True
                    except:
                        pass
                
                # 没有任何数据，终止
                self.logger.error("="*60)
                self.logger.error("❌ 爬虫执行失败 / Crawler execution failed")
                self.logger.error("="*60)
                self.logger.error("")
                self.logger.error("【失败原因 / Failure Reason】")
                self.logger.error("  爬虫未采集到任何数据")
                self.logger.error("  Crawler did not collect any data")
                self.logger.error("")
                self.logger.error("【可能的原因 / Possible Causes】")
                self.logger.error("  1. 网站结构发生变化，需要更新爬虫代码")
                self.logger.error("  2. 需要登录才能访问内容")
                self.logger.error("  3. 网络连接问题")
                self.logger.error("  4. 反爬虫机制拦截")
                self.logger.error("  5. 关键词搜索结果为空")
                self.logger.error("")
                self.logger.error("【解决方案 / Solution】")
                self.logger.error("  1. 检查网络连接")
                self.logger.error("  2. 尝试手动访问网站确认是否可访问")
                self.logger.error("  3. 检查关键词是否正确")
                self.logger.error("  4. 使用 --skip-crawler 参数跳过爬虫:")
                self.logger.error("     python3 main.py --skip-crawler -k '关键词'")
                self.logger.error("")
                self.logger.error("="*60)
                self.logger.error("程序已终止 / Program terminated")
                self.logger.error("="*60)
                return False
            
            # 数据已由crawler.save_to_csv()保存
            # 检查是否达到目标数量
            if len(articles) < num_articles:
                self.logger.warning("="*60)
                self.logger.warning("⚠️  爬虫未达到目标数量 / Crawler did not reach target count")
                self.logger.warning("="*60)
                self.logger.warning(f"目标数量 / Target: {num_articles} 篇")
                self.logger.warning(f"实际采集 / Collected: {len(articles)} 篇")
                self.logger.warning(f"完成度 / Completion: {len(articles)/num_articles*100:.1f}%")
                self.logger.warning("")
                self.logger.warning("可能原因 / Possible reasons:")
                self.logger.warning("  - 超时限制（5分钟）")
                self.logger.warning("  - 连接断开次数过多")
                self.logger.warning("  - 反爬虫机制拦截")
                self.logger.warning("")
                self.logger.warning("将使用已采集的数据继续执行后续流程")
                self.logger.warning("Will continue with collected data")
                self.logger.warning("="*60 + "\n")
            
            self.logger.info(f"✓ 数据采集完成，共采集 {len(articles)} 篇文章 / Data collection completed, scraped {len(articles)} articles")
            self.logger.info("-" * 60 + "\n")
            
            return True
            
        except ImportError as e:
            self.logger.error("="*60)
            self.logger.error("❌ 爬虫模块导入失败 / Crawler module import failed")
            self.logger.error("="*60)
            self.logger.error("")
            self.logger.error("【失败原因 / Failure Reason】")
            self.logger.error(f"  {str(e)}")
            self.logger.error("")
            self.logger.error("【解决方案 / Solution】")
            self.logger.error("  1. 安装缺失的依赖包:")
            self.logger.error("     pip3 install DrissionPage pandas --user")
            self.logger.error("")
            self.logger.error("  2. 或使用 --skip-crawler 参数跳过爬虫:")
            self.logger.error("     python3 main.py --skip-crawler -k '关键词'")
            self.logger.error("")
            self.logger.error("="*60)
            self.logger.error("程序已终止 / Program terminated")
            self.logger.error("="*60)
            return False
        except Exception as e:
            import traceback
            self.logger.error("="*60)
            self.logger.error("❌ 爬虫执行失败 / Crawler execution failed")
            self.logger.error("="*60)
            self.logger.error("")
            self.logger.error("【失败原因 / Failure Reason】")
            self.logger.error(f"  {type(e).__name__}: {str(e)}")
            self.logger.error("")
            self.logger.error("【详细错误信息 / Detailed Error】")
            self.logger.error(traceback.format_exc())
            self.logger.error("")
            self.logger.error("【可能的原因 / Possible Causes】")
            self.logger.error("  1. 网站结构发生变化，需要更新爬虫代码")
            self.logger.error("  2. 需要登录才能访问内容")
            self.logger.error("  3. 网络连接问题")
            self.logger.error("  4. 反爬虫机制拦截")
            self.logger.error("  5. 浏览器驱动问题")
            self.logger.error("")
            self.logger.error("【解决方案 / Solution】")
            self.logger.error("  1. 检查网络连接")
            self.logger.error("  2. 查看日志文件获取更多信息: logs/rednote_analysis.log")
            self.logger.error("  3. 尝试手动访问网站确认是否可访问")
            self.logger.error("  4. 使用 --skip-crawler 参数跳过爬虫:")
            self.logger.error("     python3 main.py --skip-crawler -k '关键词'")
            self.logger.error("")
            self.logger.error("="*60)
            self.logger.error("程序已终止 / Program terminated")
            self.logger.error("="*60)
            return False
    
    def run_analyzer(self) -> bool:
        """
        运行数据分析器 / Run data analyzer
        
        Returns:
            是否成功 / Whether successful
        """
        try:
            self.logger.info("第二步 / Step 2: 开始数据分析 / Starting data analysis")
            self.logger.info("-" * 60)
            
            # 检查数据文件是否存在
            from config import RAW_DATA_FILE
            if not os.path.exists(RAW_DATA_FILE):
                self.logger.error("="*60)
                self.logger.error("❌ 数据文件不存在 / Data file not found")
                self.logger.error("="*60)
                self.logger.error("")
                self.logger.error("【失败原因 / Failure Reason】")
                self.logger.error(f"  找不到数据文件: {RAW_DATA_FILE}")
                self.logger.error(f"  Data file not found: {RAW_DATA_FILE}")
                self.logger.error("")
                self.logger.error("【解决方案 / Solution】")
                self.logger.error("  1. 先运行爬虫获取数据:")
                self.logger.error("     python3 main.py --crawler-only -k '关键词'")
                self.logger.error("")
                self.logger.error("  2. 或使用示例数据文件（如果存在）")
                self.logger.error("")
                self.logger.error("="*60)
                self.logger.error("程序已终止 / Program terminated")
                self.logger.error("="*60)
                return False
            
            analyzer = RedNoteAnalyzer()
            analyzer.load_data()
            analyzer.process_data()
            analyzer.save_processed_data()
            
            # 分析内容
            report = analyzer.analyze_content()
            analyzer.save_analysis_report()
            
            # 可选：生成可视化图表
            # analyzer.visualize_data()
            
            # 打印基本统计
            basic_stats = report.get('basic_stats', {})
            self.logger.info(f"✓ 数据分析完成")
            self.logger.info(f"  - 原始文章数 / Original articles: {basic_stats.get('total_articles', 0)}")
            self.logger.info(f"  - 平均热度指数 / Avg engagement index: {basic_stats.get('avg_engagement_index', 0):.2f}")
            self.logger.info(f"  - 总点赞数 / Total likes: {basic_stats.get('total_likes', 0)}")
            self.logger.info(f"  - 总收藏数 / Total collects: {basic_stats.get('total_collects', 0)}")
            
            self.logger.info("-" * 60 + "\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"数据分析执行失败 / Data analysis execution failed: {e}")
            return False
    
    def run_content_generator(self) -> bool:
        """
        运行内容生成器 / Run content generator
        
        Returns:
            是否成功 / Whether successful
        """
        try:
            self.logger.info("第三步 / Step 3: 开始内容生成 / Starting content generation")
            self.logger.info("-" * 60)
            
            generator = ContentGenerator()
            generator.load_analysis_data()
            content_list = generator.generate_all_content(keyword=self.keyword)
            
            if not content_list:
                self.logger.error("内容生成器未生成内容 / Content generator did not generate any content")
                return False
            
            generator.save_content()
            
            self.logger.info(f"✓ 内容生成完成，共生成 {len(content_list)} 篇文章 / Content generation completed, generated {len(content_list)} articles")
            
            # 打印生成的文章标题
            for content in content_list:
                self.logger.info(f"  - {content.get('generated_title', '')}")
            
            self.logger.info("-" * 60 + "\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"内容生成执行失败 / Content generation execution failed: {e}")
            return False
    
    def run_visual_generator(self) -> bool:
        """
        运行视觉提示词生成器 / Run visual prompt generator
        
        Returns:
            是否成功 / Whether successful
        """
        try:
            self.logger.info("第四步 / Step 4: 开始视觉提示词生成 / Starting visual prompt generation")
            self.logger.info("-" * 60)
            
            generator = VisualPromptGenerator()
            generator.load_content_data()
            prompts = generator.generate_all_visual_prompts()
            
            if not prompts:
                self.logger.error("视觉提示词生成器未生成提示词 / Visual prompt generator did not generate any prompts")
                return False
            
            generator.save_visual_prompts()
            
            self.logger.info(f"✓ 视觉提示词生成完成，共生成 {len(prompts)} 个提示词 / Visual prompts generated, total {len(prompts)} prompts")
            
            # 统计提示词类型
            cover_count = sum(1 for p in prompts if p.get('type') == 'cover')
            inner_count = sum(1 for p in prompts if p.get('type') == 'inner_page')
            
            self.logger.info(f"  - 封面图提示词 / Cover prompts: {cover_count}")
            self.logger.info(f"  - 内页图提示词 / Inner page prompts: {inner_count}")
            
            self.logger.info("-" * 60 + "\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"视觉提示词生成执行失败 / Visual prompt generation execution failed: {e}")
            return False
    
    def run_full_workflow(self, skip_crawler: bool = False) -> bool:
        """
        运行完整工作流 / Run full workflow
        
        Args:
            skip_crawler: 是否跳过爬虫（使用已有数据）/ Whether to skip crawler (use existing data)
            
        Returns:
            是否成功 / Whether successful
        """
        try:
            success = True
            
            # 步骤1: 数据采集（可选跳过）
            # 注意：如果爬虫超时（5分钟）但已采集到部分数据，会保存数据并继续执行
            # Note: If crawler times out (5 minutes) but has collected some data, it will save and continue
            if not skip_crawler:
                crawler_result = self.run_crawler()
                if not crawler_result:
                    # 检查是否有已保存的数据文件（可能是超时后保存的）
                    from config import RAW_DATA_FILE
                    if os.path.exists(RAW_DATA_FILE):
                        import pandas as pd
                        try:
                            df = pd.read_csv(RAW_DATA_FILE, encoding="utf-8-sig")
                            if len(df) > 0:
                                self.logger.info("="*60)
                                self.logger.info("ℹ️  发现已有数据文件，将继续执行后续步骤")
                                self.logger.info("Found existing data file, will continue with subsequent steps")
                                self.logger.info(f"数据量 / Data count: {len(df)} 条记录")
                                self.logger.info("="*60 + "\n")
                                # 继续执行后续步骤
                            else:
                                # 没有任何数据，终止流程
                                self.logger.error("")
                                self.logger.error("="*60)
                                self.logger.error("工作流已终止 / Workflow terminated")
                                self.logger.error("="*60)
                                self.logger.error("")
                                self.logger.error("由于数据采集失败且无可用数据，无法继续执行后续步骤")
                                self.logger.error("Because data collection failed and no data available, cannot continue")
                                self.logger.error("")
                                self.logger.error("如需跳过爬虫功能，请使用 --skip-crawler 参数:")
                                self.logger.error("To skip crawler, use --skip-crawler parameter:")
                                self.logger.error("  python3 main.py --skip-crawler -k '关键词'")
                                self.logger.error("")
                                return False
                        except:
                            # 文件读取失败，终止流程
                            self.logger.error("")
                            self.logger.error("="*60)
                            self.logger.error("工作流已终止 / Workflow terminated")
                            self.logger.error("="*60)
                            self.logger.error("")
                            self.logger.error("由于数据采集失败，无法继续执行后续步骤")
                            self.logger.error("Because data collection failed, cannot continue with subsequent steps")
                            self.logger.error("")
                            self.logger.error("如需跳过爬虫功能，请使用 --skip-crawler 参数:")
                            self.logger.error("To skip crawler, use --skip-crawler parameter:")
                            self.logger.error("  python3 main.py --skip-crawler -k '关键词'")
                            self.logger.error("")
                            return False
                    else:
                        # 没有任何数据，终止流程
                        self.logger.error("")
                        self.logger.error("="*60)
                        self.logger.error("工作流已终止 / Workflow terminated")
                        self.logger.error("="*60)
                        self.logger.error("")
                        self.logger.error("由于数据采集失败且无可用数据，无法继续执行后续步骤")
                        self.logger.error("Because data collection failed and no data available, cannot continue")
                        self.logger.error("")
                        self.logger.error("如需跳过爬虫功能，请使用 --skip-crawler 参数:")
                        self.logger.error("To skip crawler, use --skip-crawler parameter:")
                        self.logger.error("  python3 main.py --skip-crawler -k '关键词'")
                        self.logger.error("")
                        return False
            
            # 步骤2: 数据分析
            if not self.run_analyzer():
                self.logger.error("数据分析失败，工作流终止 / Data analysis failed, workflow terminated")
                return False
            
            # 步骤3: 内容生成
            if not self.run_content_generator():
                self.logger.error("内容生成失败，工作流终止 / Content generation failed, workflow terminated")
                return False
            
            # 步骤4: 视觉提示词生成
            if not self.run_visual_generator():
                self.logger.error("视觉提示词生成失败 / Visual prompt generation failed")
                success = False
            
            # 打印总结
            self.logger.info("\n" + "="*60)
            self.logger.info("工作流执行完成 / Workflow execution completed")
            self.logger.info(f"结束时间 / End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("="*60)
            
            # 输出文件位置提示
            self.logger.info("\n输出文件 / Output Files:")
            self.logger.info(f"  - 数据文件 / Data Files: ./data/")
            self.logger.info(f"  - 分析报告 / Analysis Report: ./output/analysis_report.json")
            self.logger.info(f"  - 生成内容 / Generated Content: ./output/generated_content.json")
            self.logger.info(f"  - 视觉提示词 / Visual Prompts: ./output/visual_prompts.json")
            self.logger.info(f"  - 日志文件 / Log File: ./logs/rednote_analysis.log")
            
            return success
            
        except Exception as e:
            self.logger.error(f"工作流执行失败 / Workflow execution failed: {e}")
            return False


def main():
    """主函数 / Main function"""
    parser = argparse.ArgumentParser(
        description="小红书竞品分析与爆款内容生成系统 / Xiaohongshu Competitor Analysis & Content Generation System"
    )
    
    parser.add_argument(
        '-k', '--keyword',
        type=str,
        default=TARGET_KEYWORD,
        help=f'搜索关键词 / Search keyword (default: {TARGET_KEYWORD})'
    )
    
    parser.add_argument(
        '-n', '--num-articles',
        type=int,
        default=MAX_ARTICLES_TO_SCRAPE,
        help=f'爬取文章数量 / Number of articles to scrape (default: {MAX_ARTICLES_TO_SCRAPE})'
    )
    
    parser.add_argument(
        '--skip-crawler',
        action='store_true',
        help='跳过爬虫，使用已有数据 / Skip crawler, use existing data'
    )
    
    parser.add_argument(
        '--crawler-only',
        action='store_true',
        help='仅运行爬虫 / Run crawler only'
    )
    
    parser.add_argument(
        '--analyzer-only',
        action='store_true',
        help='仅运行数据分析器 / Run analyzer only'
    )
    
    parser.add_argument(
        '--content-only',
        action='store_true',
        help='仅运行内容生成器 / Run content generator only'
    )
    
    parser.add_argument(
        '--visual-only',
        action='store_true',
        help='仅运行视觉提示词生成器 / Run visual prompt generator only'
    )
    
    args = parser.parse_args()
    
    # 验证配置
    logger = setup_logging()
    if not validate_config():
        logger.error("配置验证失败，请检查配置文件 / Configuration validation failed, please check config file")
        sys.exit(1)
    
    # 创建工作流实例
    workflow = RedNoteWorkflow(keyword=args.keyword)
    
    # 根据参数执行相应步骤
    if args.crawler_only:
        workflow.run_crawler(num_articles=args.num_articles)
    elif args.analyzer_only:
        workflow.run_analyzer()
    elif args.content_only:
        workflow.run_content_generator()
    elif args.visual_only:
        workflow.run_visual_generator()
    else:
        # 运行完整工作流
        workflow.run_full_workflow(skip_crawler=args.skip_crawler)


if __name__ == "__main__":
    main()
