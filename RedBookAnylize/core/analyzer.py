"""
数据分析与排序模块
Data Analysis and Sorting Module
"""

import logging
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from collections import Counter
import jieba
from datetime import datetime

# 导入可视化库（如果未安装，运行 install_all_deps.py 安装）
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
    logging.warning("未安装可视化库（matplotlib/seaborn）")
    logging.warning("请运行安装脚本: python3 install_all_deps.py")
    logging.warning("或手动安装: pip3 install matplotlib seaborn --user")

from config import (
    WEIGHTS,
    MIN_ENGAGEMENT,
    TOP_ARTICLES_TO_ANALYZE,
    RAW_DATA_FILE,
    PROCESSED_DATA_FILE,
    ANALYSIS_REPORT_FILE,
    OUTPUT_DIR
)


class RedNoteAnalyzer:
    """小红书数据分析器 / Xiaohongshu Data Analyzer"""
    
    def __init__(self):
        """初始化分析器 / Initialize analyzer"""
        self.logger = logging.getLogger(__name__)
        self.raw_data = None
        self.processed_data = None
        self.analysis_report = {}
        
        # 设置中文显示 / Set Chinese display (仅当安装了可视化库时)
        if HAS_VISUALIZATION:
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
            plt.rcParams['axes.unicode_minus'] = False
    
    def load_data(self, filename: str = None) -> pd.DataFrame:
        """
        加载原始数据 / Load raw data
        
        Args:
            filename: 数据文件名 / Data filename
            
        Returns:
            DataFrame对象 / DataFrame object
        """
        try:
            filename = filename or RAW_DATA_FILE
            
            self.raw_data = pd.read_csv(filename, encoding="utf-8-sig")
            
            self.logger.info(f"成功加载数据 / Successfully loaded data: {len(self.raw_data)} 条记录 / records")
            
            return self.raw_data
            
        except Exception as e:
            self.logger.error(f"加载数据失败 / Failed to load data: {e}")
            return pd.DataFrame()
    
    def calculate_engagement_index(self, row) -> float:
        """
        计算热度指数 / Calculate engagement index
        
        公式 / Formula:
        Index = (点赞数 * 1) + (收藏数 * 2) + (评论数 * 3) + (阅读数 * 0.1)
        
        Args:
            row: 数据行 / Data row
            
        Returns:
            热度指数 / Engagement index
        """
        try:
            index = (
                row.get('likes', 0) * WEIGHTS['likes'] +
                row.get('collects', 0) * WEIGHTS['collects'] +
                row.get('comments', 0) * WEIGHTS['comments'] +
                row.get('views', 0) * WEIGHTS['views']
            )
            return float(index)
        except:
            return 0.0
    
    def process_data(self) -> pd.DataFrame:
        """
        处理数据 / Process data
        
        包括: 计算热度指数、过滤低质量数据、排序
        Includes: Calculate engagement index, filter low-quality data, sort
        
        Returns:
            处理后的DataFrame / Processed DataFrame
        """
        try:
            if self.raw_data is None or len(self.raw_data) == 0:
                self.logger.error("没有原始数据可处理 / No raw data to process")
                return pd.DataFrame()
            
            self.logger.info("开始处理数据 / Start processing data")
            
            # 创建处理后的数据副本
            df = self.raw_data.copy()
            
            # 1. 数据清洗 / Data Cleaning
            
            # 填充缺失值 / Fill missing values
            df['likes'] = df['likes'].fillna(0).astype(int)
            df['collects'] = df['collects'].fillna(0).astype(int)
            df['comments'] = df['comments'].fillna(0).astype(int)
            df['views'] = df['views'].fillna(0).astype(int)
            
            # 填充文本字段 / Fill text fields
            df['title'] = df['title'].fillna('')
            df['content'] = df['content'].fillna('')
            df['author'] = df['author'].fillna('')
            
            # 2. 计算热度指数 / Calculate engagement index
            self.logger.info("计算热度指数 / Calculating engagement index")
            df['engagement_index'] = df.apply(self.calculate_engagement_index, axis=1)
            
            # 3. 计算其他指标 / Calculate other metrics
            
            # 收藏率 / Collect rate (收藏数/点赞数)
            df['collect_rate'] = np.where(
                df['likes'] > 0,
                df['collects'] / df['likes'],
                0
            )
            
            # 评论率 / Comment rate (评论数/点赞数)
            df['comment_rate'] = np.where(
                df['likes'] > 0,
                df['comments'] / df['likes'],
                0
            )
            
            # 综合质量分 / Comprehensive quality score
            df['quality_score'] = (
                df['engagement_index'] * 0.6 +
                df['collect_rate'] * 1000 * 0.2 +
                df['comment_rate'] * 1000 * 0.2
            )
            
            # 4. 过滤低质量数据 / Filter low-quality data
            initial_count = len(df)
            
            # 过滤热度指数低于阈值的内容
            df_filtered = df[df['engagement_index'] >= MIN_ENGAGEMENT].copy()
            
            # 过滤没有标题或内容为空的文章
            df_filtered = df_filtered[
                (df_filtered['title'].str.len() > 0) |
                (df_filtered['content'].str.len() > 0)
            ]
            
            filtered_count = len(df_filtered)
            self.logger.info(f"过滤前 / Before filter: {initial_count} 条 / records")
            self.logger.info(f"过滤后 / After filter: {filtered_count} 条 / records")
            self.logger.info(f"过滤掉 / Filtered out: {initial_count - filtered_count} 条 / records")
            
            # 5. 排序 / Sorting
            # 按热度指数降序排列
            df_sorted = df_filtered.sort_values(
                by='engagement_index',
                ascending=False
            ).reset_index(drop=True)
            
            # 6. 取TOP N / Take TOP N
            top_n = min(TOP_ARTICLES_TO_ANALYZE, len(df_sorted))
            df_top = df_sorted.head(top_n).copy()
            
            # 添加排名 / Add ranking
            df_top['rank'] = range(1, len(df_top) + 1)
            
            self.processed_data = df_top
            
            self.logger.info(f"数据处理完成 / Data processing completed")
            self.logger.info(f"最终保留 / Finally kept: {len(df_top)} 篇高质量文章 / high-quality articles")
            
            return self.processed_data
            
        except Exception as e:
            self.logger.error(f"处理数据失败 / Failed to process data: {e}")
            return pd.DataFrame()
    
    def save_processed_data(self, filename: str = None):
        """
        保存处理后的数据 / Save processed data
        
        Args:
            filename: 保存文件名 / Save filename
        """
        try:
            filename = filename or PROCESSED_DATA_FILE
            
            if self.processed_data is None or len(self.processed_data) == 0:
                self.logger.warning("没有处理后的数据可保存 / No processed data to save")
                return
            
            self.processed_data.to_csv(filename, index=False, encoding="utf-8-sig")
            
            self.logger.info(f"处理后的数据已保存到 / Processed data saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"保存处理后的数据失败 / Failed to save processed data: {e}")
    
    def analyze_content(self) -> Dict:
        """
        分析内容 / Analyze content
        
        分析内容包括:
        - 标题关键词
        - 内容长度分布
        - 互动数据统计
        - 作者分析
        
        返回: 分析报告 / Returns: Analysis report
        """
        try:
            if self.processed_data is None or len(self.processed_data) == 0:
                self.logger.error("没有数据可分析 / No data to analyze")
                return {}
            
            self.logger.info("开始内容分析 / Start content analysis")
            
            report = {
                "basic_stats": self._analyze_basic_stats(),
                "title_analysis": self._analyze_titles(),
                "content_analysis": self._analyze_contents(),
                "engagement_analysis": self._analyze_engagement(),
                "author_analysis": self._analyze_authors(),
                "keywords_analysis": self._analyze_keywords(),
                "insights": self._generate_insights()
            }
            
            self.analysis_report = report
            
            self.logger.info("内容分析完成 / Content analysis completed")
            
            return report
            
        except Exception as e:
            self.logger.error(f"内容分析失败 / Failed to analyze content: {e}")
            return {}
    
    def _analyze_basic_stats(self) -> Dict:
        """分析基本统计信息 / Analyze basic statistics"""
        df = self.processed_data
        
        stats = {
            "total_articles": len(df),
            "total_likes": int(df['likes'].sum()),
            "total_collects": int(df['collects'].sum()),
            "total_comments": int(df['comments'].sum()),
            "total_views": int(df['views'].sum()),
            "avg_likes": float(df['likes'].mean()),
            "avg_collects": float(df['collects'].mean()),
            "avg_comments": float(df['comments'].mean()),
            "avg_engagement_index": float(df['engagement_index'].mean()),
            "median_engagement_index": float(df['engagement_index'].median()),
            "max_engagement_index": float(df['engagement_index'].max()),
            "min_engagement_index": float(df['engagement_index'].min())
        }
        
        return stats
    
    def _analyze_titles(self) -> Dict:
        """分析标题 / Analyze titles"""
        df = self.processed_data
        
        # 标题长度统计 / Title length statistics
        df['title_length'] = df['title'].str.len()
        
        title_stats = {
            "avg_title_length": float(df['title_length'].mean()),
            "max_title_length": int(df['title_length'].max()),
            "min_title_length": int(df['title_length'].min()),
            "popular_titles": df.head(10)[['title', 'engagement_index']].to_dict('records')
        }
        
        return title_stats
    
    def _analyze_contents(self) -> Dict:
        """分析内容 / Analyze contents"""
        df = self.processed_data
        
        # 内容长度统计 / Content length statistics
        df['content_length'] = df['content'].str.len()
        
        content_stats = {
            "avg_content_length": float(df['content_length'].mean()),
            "max_content_length": int(df['content_length'].max()),
            "min_content_length": int(df['content_length'].min())
        }
        
        return content_stats
    
    def _analyze_engagement(self) -> Dict:
        """分析互动数据 / Analyze engagement data"""
        df = self.processed_data
        
        engagement_stats = {
            "collect_rate_avg": float(df['collect_rate'].mean()),
            "comment_rate_avg": float(df['comment_rate'].mean()),
            "top_engaged": df.head(5)[['title', 'likes', 'collects', 'comments', 'engagement_index']].to_dict('records')
        }
        
        return engagement_stats
    
    def _analyze_authors(self) -> Dict:
        """分析作者 / Analyze authors"""
        df = self.processed_data
        
        # 按作者分组统计 / Group by author and count
        author_stats = df.groupby('author').agg({
            'engagement_index': ['count', 'mean', 'sum'],
            'title': list
        }).round(2)
        
        # 重置索引并重命名列
        author_stats.columns = ['article_count', 'avg_engagement', 'total_engagement', 'titles']
        author_stats = author_stats.reset_index()
        
        # 按文章数量排序
        author_stats = author_stats.sort_values('article_count', ascending=False)
        
        # 取TOP 10作者
        top_authors = author_stats.head(10).to_dict('records')
        
        return {
            "total_authors": len(author_stats),
            "top_authors": top_authors
        }
    
    def _analyze_keywords(self) -> Dict:
        """分析关键词 / Analyze keywords"""
        df = self.processed_data
        
        # 提取标题中的关键词 / Extract keywords from titles
        all_titles = ' '.join(df['title'].tolist())
        
        # 使用jieba分词 / Use jieba for word segmentation
        words = jieba.lcut(all_titles)
        
        # 过滤停用词和短词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        filtered_words = [w for w in words if len(w) > 1 and w not in stopwords]
        
        # 统计词频
        word_freq = Counter(filtered_words)
        
        # 取TOP 20关键词
        top_keywords = word_freq.most_common(20)
        
        return {
            "top_keywords": [{"word": word, "count": count} for word, count in top_keywords]
        }
    
    def _generate_insights(self) -> List[str]:
        """生成洞察 / Generate insights"""
        insights = []
        
        if self.processed_data is None or len(self.processed_data) == 0:
            return insights
        
        df = self.processed_data
        
        # 洞察1: 高互动内容特征
        top_10 = df.head(10)
        avg_title_length_top = top_10['title'].str.len().mean()
        insights.append(f"TOP10爆款内容的平均标题长度为 {avg_title_length_top:.0f} 字")
        
        # 洞察2: 收藏率高的内容特点
        high_collect_rate = df[df['collect_rate'] > df['collect_rate'].quantile(0.75)]
        if len(high_collect_rate) > 0:
            insights.append(f"收藏率高的内容占比 {(len(high_collect_rate)/len(df)*100):.1f}%，通常包含更多实用信息")
        
        # 洞察3: 评论互动
        insights.append(f"平均每篇文章的评论数为 {df['comments'].mean():.0f}，用户互动较为活跃")
        
        # 洞察4: 热度分布
        if len(df) > 0:
            insights.append(f"热度指数范围从 {df['engagement_index'].min():.0f} 到 {df['engagement_index'].max():.0f}，头部内容优势明显")
        
        return insights
    
    def visualize_data(self):
        """
        数据可视化 / Data visualization
        
        生成图表:
        - 热度指数分布
        - 互动数据对比
        - 标题长度分布
        """
        if not HAS_VISUALIZATION:
            self.logger.warning("未安装可视化库，跳过数据可视化 / Visualization libraries not installed, skipping visualization")
            return
        
        try:
            if self.processed_data is None or len(self.processed_data) == 0:
                self.logger.warning("没有数据可可视化 / No data to visualize")
                return
            
            self.logger.info("生成数据可视化 / Generating data visualization")
            
            # 创建图表 / Create figures
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. 热度指数分布 / Engagement index distribution
            axes[0, 0].hist(self.processed_data['engagement_index'], bins=20, color='skyblue', edgecolor='black')
            axes[0, 0].set_xlabel('热度指数 / Engagement Index')
            axes[0, 0].set_ylabel('文章数量 / Article Count')
            axes[0, 0].set_title('热度指数分布 / Distribution of Engagement Index')
            
            # 2. 互动数据对比 / Engagement data comparison
            engagement_cols = ['likes', 'collects', 'comments']
            engagement_sum = self.processed_data[engagement_cols].sum()
            axes[0, 1].bar(engagement_cols, engagement_sum.values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
            axes[0, 1].set_ylabel('总数 / Total Count')
            axes[0, 1].set_title('互动数据总量 / Total Engagement Data')
            
            # 3. TOP 10 文章热度对比 / Top 10 articles engagement comparison
            top_10 = self.processed_data.head(10)
            top_10_sorted = top_10.sort_values('engagement_index', ascending=True)
            axes[1, 0].barh(range(len(top_10_sorted)), top_10_sorted['engagement_index'], color='lightcoral')
            axes[1, 0].set_yticks(range(len(top_10_sorted)))
            axes[1, 0].set_yticklabels([f"#{i+1}" for i in range(len(top_10_sorted))])
            axes[1, 0].set_xlabel('热度指数 / Engagement Index')
            axes[1, 0].set_title('TOP 10 文章热度 / Top 10 Articles by Engagement')
            
            # 4. 收藏率与评论率散点图 / Collect rate vs comment rate scatter plot
            axes[1, 1].scatter(
                self.processed_data['collect_rate'],
                self.processed_data['comment_rate'],
                alpha=0.6,
                s=self.processed_data['engagement_index']/100,
                c='purple'
            )
            axes[1, 1].set_xlabel('收藏率 / Collect Rate')
            axes[1, 1].set_ylabel('评论率 / Comment Rate')
            axes[1, 1].set_title('收藏率 vs 评论率 / Collect Rate vs Comment Rate')
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表
            chart_filename = os.path.join(OUTPUT_DIR, f"analysis_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
            
            self.logger.info(f"可视化图表已保存到 / Visualization chart saved to {chart_filename}")
            
            # 显示图表
            plt.show()
            
        except Exception as e:
            self.logger.error(f"数据可视化失败 / Failed to visualize data: {e}")
    
    def save_analysis_report(self, filename: str = None):
        """
        保存分析报告 / Save analysis report
        
        Args:
            filename: 保存文件名 / Save filename
        """
        try:
            import json
            filename = filename or ANALYSIS_REPORT_FILE
            
            if not self.analysis_report:
                self.logger.warning("没有分析报告可保存 / No analysis report to save")
                return
            
            # 转换numpy类型为Python原生类型
            report = self._convert_numpy_types(self.analysis_report)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"分析报告已保存到 / Analysis report saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"保存分析报告失败 / Failed to save analysis report: {e}")
    
    def _convert_numpy_types(self, obj):
        """递归转换numpy类型为Python原生类型"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        return obj


# 便捷函数 / Convenience functions
def analyze_articles(data_file: str = None) -> Tuple[pd.DataFrame, Dict]:
    """
    便捷的分析函数 / Convenient analysis function
    
    Args:
        data_file: 数据文件路径 / Data file path
        
    Returns:
        处理后的DataFrame和分析报告的元组 / Tuple of processed DataFrame and analysis report
    """
    analyzer = RedNoteAnalyzer()
    analyzer.load_data(data_file)
    analyzer.process_data()
    analyzer.save_processed_data()
    report = analyzer.analyze_content()
    analyzer.save_analysis_report()
    
    return analyzer.processed_data, report


if __name__ == "__main__":
    import os
    
    # 设置日志 / Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 示例使用 / Example usage
    analyzer = RedNoteAnalyzer()
    
    # 加载并处理数据
    analyzer.load_data()
    analyzer.process_data()
    analyzer.save_processed_data()
    
    # 分析内容
    report = analyzer.analyze_content()
    analyzer.save_analysis_report()
    
    # 打印基本信息
    print("\n" + "="*50)
    print("分析报告概览 / Analysis Report Overview")
    print("="*50)
    print(f"总文章数 / Total Articles: {report['basic_stats']['total_articles']}")
    print(f"总点赞数 / Total Likes: {report['basic_stats']['total_likes']}")
    print(f"总收藏数 / Total Collects: {report['basic_stats']['total_collects']}")
    print(f"平均热度指数 / Avg Engagement Index: {report['basic_stats']['avg_engagement_index']:.2f}")
    
    print("\nTOP 10 关键词 / Top 10 Keywords:")
    for i, kw in enumerate(report['keywords_analysis']['top_keywords'][:10], 1):
        print(f"  {i}. {kw['word']} ({kw['count']})")
    
    print("\n洞察 / Insights:")
    for insight in report['insights']:
        print(f"  - {insight}")
