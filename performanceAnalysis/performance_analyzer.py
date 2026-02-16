#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绩效分析脚本 v2.0
功能：
1. 输入员工姓名或车厢名称，输出详细的绩效分析结论
2. 支持按月份（12月/1月）查询数据
3. 提供深度分析和具体改进建议
"""

import pandas as pd
import sys
import os
import argparse
import math
from datetime import datetime
from typing import Dict, Optional, Tuple, List


class OHTRulesAnalyzer:
    """OHT考核细则分析器
    
    基于OHT考核细则提供深度分析：
    - 需求价值分 = 调权工时(Hw) × 需求价值系数
    - 需求价值系数 = log₁₀(Bidding分数) + 1
    - 调权工时(Hw) = √(总工时)
    """
    
    @staticmethod
    def calculate_weighted_hours(hours: float) -> float:
        """计算调权工时"""
        if hours <= 0:
            return 0
        return math.sqrt(hours)
    
    @staticmethod
    def calculate_value_coefficient(bidding: float) -> float:
        """计算需求价值系数"""
        if bidding <= 0:
            return 0
        return math.log10(bidding) + 1
    
    @staticmethod
    def calculate_value_score(hours: float, bidding: float) -> float:
        """计算需求价值分"""
        hw = OHTRulesAnalyzer.calculate_weighted_hours(hours)
        coef = OHTRulesAnalyzer.calculate_value_coefficient(bidding)
        return hw * coef
    
    @staticmethod
    def analyze_work_efficiency(actual_hours: float, oht_score: float) -> List[str]:
        """分析工作效率（基于调权机制）"""
        insights = []
        
        if actual_hours <= 0:
            return insights
        
        # 理论调权工时
        weighted_hours = OHTRulesAnalyzer.calculate_weighted_hours(actual_hours)
        weighted_ratio = (weighted_hours / actual_hours * 100) if actual_hours > 0 else 0
        
        # 如果工时充足但得分低
        if actual_hours >= 10 and oht_score < 8:
            insights.append(f"      🔍 工作效率分析（基于OHT考核细则）：")
            insights.append(f"         实际工时：{actual_hours:.1f}h")
            insights.append(f"         调权工时：{weighted_hours:.1f}h（调权比例：{weighted_ratio:.1f}%）")
            insights.append(f"         💡 考核公式：价值分 = √工时 × (log₁₀(Bidding)+1)")
            insights.append(f"         ")
            insights.append(f"         ⚠️  工时边际递减规律：")
            insights.append(f"         - 16h → 4.0h (25%)  |  64h → 8.0h (13%)")
            insights.append(f"         - 100h → 10.0h (10%)")
            insights.append(f"         ")
            insights.append(f"         📈 优化建议：")
            insights.append(f"         1. 聚焦高Bidding需求（≥100分，价值系数≥3）")
            insights.append(f"         2. 检查TAPD工时填写规范性（每日按时写Log）")
            insights.append(f"         3. 提升单位时间产出质量，而非堆砌工时")
        
        return insights
    
    @staticmethod
    def suggest_bidding_optimization(current_score: float) -> List[str]:
        """Bidding优化建议"""
        insights = []
        
        insights.append(f"      💼 Bidding价值导向建议：")
        insights.append(f"         ")
        insights.append(f"         📊 不同Bidding的价值系数：")
        
        bidding_examples = [
            (10, "低价值需求"),
            (50, "中等需求"),
            (100, "高价值需求 ⭐"),
            (500, "核心需求 ⭐⭐"),
            (1000, "战略需求 ⭐⭐⭐")
        ]
        
        for bidding, desc in bidding_examples:
            coef = OHTRulesAnalyzer.calculate_value_coefficient(bidding)
            # 计算相同工时下的价值分差异
            value_score = OHTRulesAnalyzer.calculate_value_score(36, bidding)  # 假设36工时
            insights.append(f"         - Bidding {bidding:>4}分 → 系数{coef:.2f} → 价值分{value_score:.1f} ({desc})")
        
        insights.append(f"         ")
        insights.append(f"         ✨ 最优策略：")
        insights.append(f"         1. 优先参与Bidding≥100的需求")
        insights.append(f"         2. 产品评审时主动了解Bidding定价")
        insights.append(f"         3. 同等工时投入，高Bidding需求得分可提升50%+")
        
        return insights
    
    @staticmethod
    def check_tapd_compliance() -> List[str]:
        """TAPD规范性检查建议"""
        insights = []
        
        insights.append(f"      📋 TAPD规范性自查（考核基础）：")
        insights.append(f"         ")
        insights.append(f"         ✅ 每日填写Log检查清单：")
        insights.append(f"         □ 是否每日按时填写工时Log")
        insights.append(f"         □ 工时记录是否真实反映实际投入")
        insights.append(f"         □ 任务归属是否正确（主车厢/站台）")
        insights.append(f"         □ 业务价值字段是否填写Bidding点数")
        insights.append(f"         ")
        insights.append(f"         ⚠️  考核规则：")
        insights.append(f"         - 只统计周期内的**终态需求**（未完结=0分）")
        insights.append(f"         - 工时数据不准确 → 调权工时偏低 → 价值分降低")
        insights.append(f"         ")
        insights.append(f"         💡 月底冲刺建议：")
        insights.append(f"         - 优先完结进行中的需求")
        insights.append(f"         - 大需求合理拆分，确保阶段性交付")
        insights.append(f"         - 避免跨月需求积压")
        
        return insights


class BiddingDataLoader:
    """Bidding数据加载器 - 整合多个时间段的Bidding数据"""
    
    def __init__(self, bidding_files: List[str]):
        """
        初始化Bidding数据加载器
        
        Args:
            bidding_files: Bidding Excel文件路径列表
        """
        self.bidding_files = bidding_files
        self.bidding_data = None
        self._load_all_bidding_data()
    
    def _load_all_bidding_data(self):
        """加载所有Bidding数据文件"""
        all_data = []
        
        for file_path in self.bidding_files:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path, sheet_name=0)
                    # 添加时间段标识
                    df['数据来源'] = os.path.basename(file_path)
                    all_data.append(df)
                except Exception as e:
                    print(f"  ⚠️  加载Bidding文件失败: {file_path} - {e}")
        
        if all_data:
            self.bidding_data = pd.concat(all_data, ignore_index=True)
            print(f"  ✓ Bidding数据加载完成：共{len(self.bidding_data)}条需求记录")
        else:
            print(f"  ⚠️  未加载到任何Bidding数据")
            self.bidding_data = pd.DataFrame()
    
    def get_team_bidding_stats(self, team_name: str) -> Dict:
        """
        获取车厢的Bidding统计数据
        
        Args:
            team_name: 车厢名称
            
        Returns:
            统计字典
        """
        if self.bidding_data.empty:
            return {}
        
        # 车厢名称映射（员工数据 -> Bidding数据）
        team_mapping = {
            '站内营销': '站内营销-FC',
            '督导学': '督导学服务-FC',
            '学员旅程': '学员全旅程服务-FC',
            '三教服务': '教学教研教务-FC',
            '三方能力': '三方能力对接-FC',
            '学科工具': '学科工具-FC',
            '站台': '站台'
        }
        
        # 获取Bidding数据中的车厢名称
        bidding_team_name = team_mapping.get(team_name, team_name)
        
        # 根据FCM-主车厢筛选
        team_data = self.bidding_data[self.bidding_data['FCM-主车厢'] == bidding_team_name]
        
        if team_data.empty:
            return {}
        
        # 统计Bidding分布
        bidding_values = team_data['BG点数合计'].dropna()
        
        stats = {
            '需求总数': len(team_data),
            'Bidding总分': bidding_values.sum(),
            'Bidding平均': bidding_values.mean(),
            'Bidding中位数': bidding_values.median(),
            'Bidding最大': bidding_values.max(),
            'Bidding最小': bidding_values.min(),
            '高价值需求数': len(bidding_values[bidding_values >= 100]),
            '中等需求数': len(bidding_values[(bidding_values >= 50) & (bidding_values < 100)]),
            '低价值需求数': len(bidding_values[bidding_values < 50])
        }
        
        return stats
    
    def get_bidding_distribution_insight(self, team_name: str) -> List[str]:
        """获取Bidding分布洞察"""
        stats = self.get_team_bidding_stats(team_name)
        
        if not stats:
            return []
        
        insights = []
        insights.append(f"      📊 Bidding数据分析（基于历史需求）：")
        insights.append(f"         需求总数：{stats['需求总数']}个")
        insights.append(f"         平均Bidding：{stats['Bidding平均']:.1f}分")
        insights.append(f"         ")
        insights.append(f"         需求价值分布：")
        insights.append(f"         - 高价值（≥100分）：{stats['高价值需求数']}个 ({stats['高价值需求数']/stats['需求总数']*100:.0f}%)")
        insights.append(f"         - 中等（50-100分）：{stats['中等需求数']}个 ({stats['中等需求数']/stats['需求总数']*100:.0f}%)")
        insights.append(f"         - 低价值（<50分）：{stats['低价值需求数']}个 ({stats['低价值需求数']/stats['需求总数']*100:.0f}%)")
        
        # 分析建议
        high_ratio = stats['高价值需求数'] / stats['需求总数'] if stats['需求总数'] > 0 else 0
        
        if high_ratio < 0.3:
            insights.append(f"         ")
            insights.append(f"         💡 优化建议：")
            insights.append(f"         高价值需求占比较低（{high_ratio*100:.0f}%），建议：")
            insights.append(f"         1. 产品评审时争取更多高Bidding需求")
            insights.append(f"         2. 关注需求业务价值，避免只接低价值需求")
        elif high_ratio >= 0.5:
            insights.append(f"         ")
            insights.append(f"         ✨ 车厢表现优秀：")
            insights.append(f"         高价值需求占比{high_ratio*100:.0f}%，价值导向明确")
        
        return insights


class RoleBasedAnalyzer:
    """基于岗位的差异化分析器"""
    
    # 岗位分类
    ROLE_PM = 'PM'
    ROLE_FE = 'FE'
    ROLE_RD = 'RD'
    ROLE_QA = 'QA'
    
    @staticmethod
    def get_role_specific_suggestions(role: str, dimension: str, score: float) -> List[str]:
        """
        根据岗位和维度提供差异化建议
        
        Args:
            role: 岗位（PM/FE/RD/QA）
            dimension: 维度名称
            score: 得分
            
        Returns:
            建议列表
        """
        insights = []
        
        # OHT执行维度 - 岗位差异化建议
        if dimension == 'OHT执行' and score < 8:
            if role == RoleBasedAnalyzer.ROLE_PM:
                insights.append(f"      💼 产品经理专项建议：")
                insights.append(f"         1. 需求评审质量：确保需求描述清晰、验收标准明确")
                insights.append(f"         2. Bidding定价合理性：主动参与Bidding评审，争取合理定价")
                insights.append(f"         3. 需求跟进与协调：加强与研发的沟通，及时解决阻塞")
                insights.append(f"         4. 业务价值阐述：在TAPD中清晰填写业务价值和预期收益")
            
            elif role in [RoleBasedAnalyzer.ROLE_FE, RoleBasedAnalyzer.ROLE_RD]:
                tech_role = "前端" if role == RoleBasedAnalyzer.ROLE_FE else "后端"
                insights.append(f"      💻 {tech_role}研发专项建议：")
                insights.append(f"         1. 代码质量：提升Code Review参与度，保证代码规范")
                insights.append(f"         2. 技术方案设计：重视技术方案评审，避免返工")
                insights.append(f"         3. 交付效率：合理评估工时，按时交付需求")
                insights.append(f"         4. 技术债务：及时处理技术债，避免影响后续开发")
            
            elif role == RoleBasedAnalyzer.ROLE_QA:
                insights.append(f"      🔍 测试专项建议：")
                insights.append(f"         1. 测试覆盖率：提高自动化测试覆盖率")
                insights.append(f"         2. 质量卡点：在需求评审阶段识别质量风险")
                insights.append(f"         3. Bug管理：及时发现和跟进Bug，保证线上质量")
                insights.append(f"         4. 测试左移：参与需求评审和技术方案设计")
        
        # 影响力维度 - 岗位差异化
        if dimension == '影响力' and score < 10:
            if role == RoleBasedAnalyzer.ROLE_PM:
                insights.append(f"      🌟 产品影响力提升：")
                insights.append(f"         1. 业务洞察分享：定期分享行业趋势和竞品分析")
                insights.append(f"         2. 需求评审组织：主持需求评审会，提升评审质量")
                insights.append(f"         3. 跨部门协作：加强与业务、运营部门的沟通")
            
            elif role in [RoleBasedAnalyzer.ROLE_FE, RoleBasedAnalyzer.ROLE_RD]:
                insights.append(f"      🌟 技术影响力提升：")
                insights.append(f"         1. 技术分享：每月至少1次技术分享（新技术、最佳实践）")
                insights.append(f"         2. Code Review：主动Review他人代码，输出高质量反馈")
                insights.append(f"         3. 技术文档：沉淀关键技术方案和troubleshooting文档")
                insights.append(f"         4. Mentor机制：帮助新人成长，传递经验")
        
        # 保障维度 - 通用建议（避免PM收到技术工单建议）
        if dimension == '保障' and score < 8:
            if role == RoleBasedAnalyzer.ROLE_PM:
                insights.append(f"      📋 产品保障建议：")
                insights.append(f"         1. 需求质量：避免需求不清导致的返工和Bug")
                insights.append(f"         2. 上线跟进：关注线上数据，及时发现和响应问题")
                insights.append(f"         3. 用户反馈：建立用户反馈机制，快速响应")
            
            elif role in [RoleBasedAnalyzer.ROLE_FE, RoleBasedAnalyzer.ROLE_RD]:
                # 保留原有技术工单建议
                pass  # 在原有的analyze_oht_safeguard中已有
        
        return insights
    
    @staticmethod
    def filter_suggestions_by_role(role: str, insights: List[str]) -> List[str]:
        """
        过滤不适合该岗位的建议
        
        Args:
            role: 岗位
            insights: 原始建议列表
            
        Returns:
            过滤后的建议列表
        """
        # PM岗位过滤掉纯技术建议
        if role == RoleBasedAnalyzer.ROLE_PM:
            filtered = []
            skip_keywords = ['Code Review', '技术分享', '代码', '架构', '技术债']
            
            for insight in insights:
                should_skip = False
                for keyword in skip_keywords:
                    if keyword in insight and '产品' not in insight:
                        should_skip = True
                        break
                
                if not should_skip:
                    filtered.append(insight)
            
            return filtered
        
        return insights


class DeepAnalysisEngine:
    """深度分析引擎 - 提供具体的分析和建议"""
    
    @staticmethod
    def analyze_oht_execution(score: float, detail: pd.Series, team_members: pd.DataFrame = None, 
                             work_hours: float = 0) -> List[str]:
        """深度分析OHT执行维度"""
        insights = []
        
        if pd.notna(detail.get('车厢-分位')) and pd.notna(detail.get('站台-分位')):
            che_pct = detail['车厢-分位']
            zhan_pct = detail['站台-分位']
            
            if che_pct < 0.5:
                insights.append(f"      🔍 车厢分位{che_pct:.1%}，低于团队中位数")
                insights.append(f"         建议：重点关注项目质量和交付效率，加强代码review")
                if team_members is not None:
                    top_member = team_members.nsmallest(1, 'RANK').iloc[0]
                    insights.append(f"         对标：参考优秀成员{top_member['姓名']}的工作方法")
            
            if zhan_pct < 0.5:
                insights.append(f"      🔍 站台分位{zhan_pct:.1%}，技术影响力需提升")
                insights.append(f"         建议：增加技术分享、文档沉淀和知识库建设")
                insights.append(f"         行动：每周至少1次技术分享或Code Review")
            
            # 分析平衡性
            if abs(che_pct - zhan_pct) > 0.3:
                if che_pct > zhan_pct:
                    insights.append(f"      ⚖️  车厢表现强于站台，建议平衡发展")
                else:
                    insights.append(f"      ⚖️  站台表现强于车厢，需加强项目执行")
        
        # 【新增】基于OHT考核细则的深度分析
        if work_hours > 0 and score < 8.5:
            # 工作效率分析
            efficiency_insights = OHTRulesAnalyzer.analyze_work_efficiency(work_hours, score)
            if efficiency_insights:
                insights.append(f"         ")
                insights.extend(efficiency_insights)
            
            # Bidding优化建议（OHT执行较低时提供）
            if score < 8:
                insights.append(f"         ")
                bidding_insights = OHTRulesAnalyzer.suggest_bidding_optimization(score)
                insights.extend(bidding_insights)
                
                # TAPD规范性检查
                insights.append(f"         ")
                tapd_insights = OHTRulesAnalyzer.check_tapd_compliance()
                insights.extend(tapd_insights)
        
        return insights
    
    @staticmethod
    def analyze_oht_safeguard(score: float, detail: pd.Series) -> List[str]:
        """深度分析OHT保障维度"""
        insights = []
        
        tech_order = detail.get('技术工单(20%)', 10)
        sys_dual = detail.get('系统两用分(10%)', 0)
        
        if tech_order < 7:
            insights.append(f"      ⚠️  技术工单得分{tech_order:.1f}，需改进响应质量")
            insights.append(f"         建议：设置工单日报提醒，确保及时响应")
            insights.append(f"         目标：工单处理时效<24小时，质量评分>8分")
        
        if sys_dual == 0:
            insights.append(f"      💡 系统两用分为0，缺少跨系统经验")
            insights.append(f"         建议：主动承担1-2个跨系统需求或技术支持")
            insights.append(f"         价值：提升综合能力，增加职业发展空间")
        
        return insights
    
    @staticmethod
    def analyze_effort(score: float, detail: pd.Series, avg_hours: float = 11.0) -> List[str]:
        """深度分析努力度维度"""
        insights = []
        
        work_hours = detail.get('平均工时', 0)
        
        if work_hours < avg_hours - 1:
            insights.append(f"      📊 平均工时{work_hours:.1f}h，低于团队平均{avg_hours:.1f}h")
            insights.append(f"         建议：合理安排工作时间，保证充足投入")
        elif score < 8.5 and work_hours >= avg_hours:
            insights.append(f"      🤔 工时充足但得分{score:.1f}，需优化工作效率")
            insights.append(f"         建议：检查时间分配，减少无效会议和干扰")
            insights.append(f"         工具：使用番茄工作法，提高专注度")
        
        return insights
    
    @staticmethod
    def analyze_influence(score: float, detail: pd.Series) -> List[str]:
        """深度分析影响力维度"""
        insights = []
        
        if score < 10:
            insights.append(f"      🌟 影响力得分{score:.1f}，有提升空间")
            insights.append(f"         建议：")
            insights.append(f"         1. 每月至少1次技术分享或培训")
            insights.append(f"         2. 主动参与Code Review，输出高质量反馈")
            insights.append(f"         3. 承担Mentor角色，帮助1-2名新人成长")
            insights.append(f"         4. 在团队知识库贡献高质量文档")
        
        return insights
    
    @staticmethod
    def analyze_system_value(score: float, detail: pd.Series) -> List[str]:
        """深度分析系统价值分维度"""
        insights = []
        
        if score < 9:
            system = detail.get('车厢', 'N/A')
            insights.append(f"      💼 系统价值分{score:.1f}（{system}）")
            if score < 8:
                insights.append(f"         建议：关注所在系统的核心指标和业务价值")
                insights.append(f"         行动：与产品和运营对齐，理解业务目标")
        
        return insights
    
    @staticmethod
    def generate_action_plan(person: pd.Series, dimensions: list) -> List[str]:
        """生成分级行动计划"""
        urgent = []
        important = []
        optimize = []
        maintain = []
        
        for dim_name, weight, _ in dimensions:
            score = person[dim_name]
            
            if score < 7:
                urgent.append(f"{dim_name}（{score:.1f}分）")
            elif score < 8:
                important.append(f"{dim_name}（{score:.1f}分）")
            elif score < 9:
                optimize.append(f"{dim_name}（{score:.1f}分）")
            else:
                maintain.append(f"{dim_name}（{score:.1f}分）")
        
        plan = []
        
        if urgent:
            plan.append("  🚨 紧急改进（1周内启动）：")
            for item in urgent:
                plan.append(f"     - {item} - 制定专项提升计划")
        
        if important:
            plan.append("  📈 重点提升（本月内）：")
            for item in important:
                plan.append(f"     - {item} - 设定具体提升目标")
        
        if optimize:
            plan.append("  💎 持续优化：")
            for item in optimize:
                plan.append(f"     - {item} - 保持并逐步提升")
        
        if maintain:
            plan.append("  ✨ 保持优势：")
            for item in maintain:
                plan.append(f"     - {item} - 继续发挥，帮助他人")
        
        return plan


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self, excel_path: str, month: str = 'all'):
        """
        初始化分析器
        
        Args:
            excel_path: Excel文件路径
            month: 月份筛选 ('12', '1', 'all')
        """
        self.excel_path = excel_path
        self.month = month
        self.data = {}
        self.analysis_engine = DeepAnalysisEngine()
        self.role_analyzer = RoleBasedAnalyzer()
        
        # Bidding数据文件列表
        bidding_files = [
            'baseInfo/8R+OHT 里程碑节点 0119.xlsx',
            'baseInfo/8R+OHT 里程碑节点 1222.xlsx',
            'baseInfo/8R+OHT 里程碑节点0105.xlsx',
            'baseInfo/8R+OHT 里程碑节点1208.xlsx'
        ]
        self.bidding_loader = BiddingDataLoader(bidding_files)
        
        self._load_data()
    
    def _load_data(self):
        """加载Excel数据"""
        try:
            print(f"📊 正在加载数据文件: {self.excel_path}")
            if self.month != 'all':
                print(f"📅 月份筛选: {self.month}月")
            
            xl = pd.ExcelFile(self.excel_path)
            
            # 加载所有相关Sheet页
            sheets = ['汇总', '数据透视表', 'OHT执行（30%）', '保障-(10%)', 
                     '影响力-(10%)', '努力度(10%)', '系统价值分（5%）']
            
            for sheet in sheets:
                if sheet in xl.sheet_names:
                    self.data[sheet] = pd.read_excel(xl, sheet_name=sheet)
                    print(f"  ✓ 已加载 {sheet}")
                else:
                    print(f"  ⚠ 未找到 {sheet}")
            
            print("✅ 数据加载完成\n")
            
        except FileNotFoundError:
            print(f"❌ 错误：找不到文件 {self.excel_path}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 错误：加载数据失败 - {str(e)}")
            sys.exit(1)
    
    def find_person(self, name: str) -> Optional[pd.Series]:
        """
        查找员工数据
        
        Args:
            name: 员工姓名
            
        Returns:
            员工数据Series，如果未找到返回None
        """
        if '汇总' not in self.data:
            return None
        
        df = self.data['汇总']
        person_data = df[df['姓名'] == name]
        
        if person_data.empty:
            # 尝试模糊匹配
            similar = df[df['姓名'].str.contains(name, na=False)]
            if not similar.empty:
                print(f"未找到 '{name}'，您是否指：")
                for idx, row in similar.iterrows():
                    print(f"  - {row['姓名']}")
            return None
        
        return person_data.iloc[0]
    
    def find_team(self, team_name: str) -> Optional[pd.DataFrame]:
        """
        查找车厢数据
        
        Args:
            team_name: 车厢名称
            
        Returns:
            车厢成员数据DataFrame，如果未找到返回None
        """
        if '汇总' not in self.data:
            return None
        
        df = self.data['汇总']
        team_data = df[df['车厢'] == team_name]
        
        if team_data.empty:
            # 尝试模糊匹配并显示可用车厢
            print(f"未找到车厢 '{team_name}'")
            teams = df['车厢'].dropna().unique()
            print(f"\n可用的车厢列表：")
            for team in sorted(teams):
                count = len(df[df['车厢'] == team])
                print(f"  - {team} ({count}人)")
            return None
        
        return team_data
    
    def _get_detail_data(self, sheet_name: str, person_name: str) -> Optional[pd.Series]:
        """获取某个Sheet中的人员详细数据"""
        if sheet_name not in self.data:
            return None
        
        df = self.data[sheet_name]
        if '姓名' not in df.columns:
            return None
        
        person_data = df[df['姓名'] == person_name]
        if person_data.empty:
            return None
        
        return person_data.iloc[0]
    
    def _format_score(self, score: float, max_score: float = 10) -> str:
        """格式化分数显示，带百分比"""
        if pd.isna(score):
            return "N/A"
        percentage = (score / max_score) * 100
        return f"{score:.2f} ({percentage:.1f}%)"
    
    def _get_rank_description(self, rank: int, total: int) -> str:
        """获取排名描述"""
        percentile = (1 - (rank - 1) / total) * 100
        
        if percentile >= 90:
            return f"🏆 优秀（前10%）"
        elif percentile >= 70:
            return f"🌟 良好（前30%）"
        elif percentile >= 50:
            return f"👍 中等偏上（前50%）"
        else:
            return f"📈 有提升空间（后{100-percentile:.0f}%）"
    
    def _get_trend_data(self, sheet_name: str, person_name: str) -> Tuple[Optional[float], Optional[float]]:
        """获取12月和1月的趋势数据"""
        if sheet_name not in self.data:
            return None, None
        
        df = self.data[sheet_name]
        
        # 努力度表的月度数据
        if sheet_name == '努力度(10%)' and '12月数据' in df.columns:
            # 查找12月数据
            dec_col_idx = df.columns.get_loc('12月数据')
            jan_col_idx = df.columns.get_loc('截止1月数据') if '截止1月数据' in df.columns else None
            
            # 12月数据
            dec_row = df[df['12月数据'] == person_name]
            dec_score = None
            if not dec_row.empty and dec_col_idx + 2 < len(df.columns):
                dec_score = dec_row.iloc[0, dec_col_idx + 2]
            
            # 1月数据（默认使用汇总表的数据）
            jan_score = None
            if jan_col_idx and not dec_row.empty:
                jan_row_idx = dec_row.index[0]
                if jan_row_idx < len(df) and jan_col_idx + 1 < len(df.columns):
                    jan_score = df.iloc[jan_row_idx, jan_col_idx + 1]
            
            # 转换为float
            try:
                dec_score = float(dec_score) if pd.notna(dec_score) else None
                jan_score = float(jan_score) if pd.notna(jan_score) else None
            except:
                pass
            
            return dec_score, jan_score
        
        return None, None
    
    def analyze_person(self, name: str) -> str:
        """
        分析员工绩效
        
        Args:
            name: 员工姓名
            
        Returns:
            分析结论文本
        """
        # 查找员工
        person = self.find_person(name)
        if person is None:
            return f"❌ 未找到员工 '{name}' 的数据"
        
        # 获取车厢成员（用于对比）
        team_members = self.find_team(person['车厢'])
        
        # 开始分析
        result = []
        result.append("=" * 70)
        result.append(f"📋 绩效分析报告 - {name}")
        if self.month != 'all':
            result.append(f"   （{self.month}月数据）")
        result.append("=" * 70)
        result.append("")
        
        # 基本信息
        result.append("【基本信息】")
        result.append(f"  姓名：{person['姓名']}")
        result.append(f"  车厢：{person['车厢']}")
        result.append(f"  是否车厢长：{person['是否车厢长']}")
        result.append(f"  归属实体：{person['归属实体']}")
        result.append("")
        
        # 总体绩效
        total_score = person['总分']
        rank = person['RANK']
        total_people = len(self.data['汇总'])
        
        result.append("【总体绩效】")
        result.append(f"  总分：{total_score:.2f} 分")
        result.append(f"  排名：第 {rank} 名 / 共 {total_people} 人")
        result.append(f"  评价：{self._get_rank_description(rank, total_people)}")
        result.append("")
        
        # 各维度得分和深度分析
        result.append("【各维度详细分析】")
        
        dimensions = [
            ('OHT执行30%', 30, 'OHT执行（30%）'),
            ('OHT保障10%', 10, '保障-(10%)'),
            ('影响力10%', 10, '影响力-(10%)'),
            ('努力度10%', 10, '努力度(10%)'),
            ('价值分5%', 5, '系统价值分（5%）')
        ]
        
        for dim_name, weight, sheet_name in dimensions:
            score = person[dim_name]
            result.append(f"\n  【{dim_name}】")
            result.append(f"    得分：{self._format_score(score, 10)}")
            result.append(f"    权重：{weight}%")
            result.append(f"    贡献：{score * weight / 10:.2f} 分")
            
            # 获取详细数据
            detail = self._get_detail_data(sheet_name, name)
            if detail is not None:
                self._add_dimension_details(result, sheet_name, detail)
                
                # 深度分析
                insights = []
                
                # 获取员工岗位
                role = person['归属实体']
                
                if sheet_name == 'OHT执行（30%）':
                    # 获取努力度数据中的工时信息
                    effort_detail = self._get_detail_data('努力度(10%)', name)
                    work_hours = effort_detail.get('平均工时', 0) if effort_detail is not None else 0
                    insights = self.analysis_engine.analyze_oht_execution(score, detail, team_members, work_hours)
                    
                    # 添加Bidding数据洞察
                    team_name = person['车厢']
                    bidding_insights = self.bidding_loader.get_bidding_distribution_insight(team_name)
                    if bidding_insights:
                        insights.append(f"         ")
                        insights.extend(bidding_insights)
                    
                    # 添加岗位差异化建议
                    role_insights = self.role_analyzer.get_role_specific_suggestions(role, 'OHT执行', score)
                    if role_insights:
                        insights.append(f"         ")
                        insights.extend(role_insights)
                    
                elif sheet_name == '保障-(10%)':
                    insights = self.analysis_engine.analyze_oht_safeguard(score, detail)
                    # 添加岗位差异化建议
                    role_insights = self.role_analyzer.get_role_specific_suggestions(role, '保障', score)
                    if role_insights:
                        insights.append(f"         ")
                        insights.extend(role_insights)
                    
                elif sheet_name == '努力度(10%)':
                    team_avg_hours = team_members['努力度10%'].mean() * 1.2 if team_members is not None else 11.0
                    insights = self.analysis_engine.analyze_effort(score, detail, team_avg_hours)
                    
                elif sheet_name == '影响力-(10%)':
                    insights = self.analysis_engine.analyze_influence(score, detail)
                    # 添加岗位差异化建议
                    role_insights = self.role_analyzer.get_role_specific_suggestions(role, '影响力', score)
                    if role_insights:
                        insights.append(f"         ")
                        insights.extend(role_insights)
                    
                elif sheet_name == '系统价值分（5%）':
                    insights = self.analysis_engine.analyze_system_value(score, detail)
                
                # PM岗位过滤不适合的建议
                if role == 'PM':
                    insights = self.role_analyzer.filter_suggestions_by_role(role, insights)
                
                if insights:
                    result.append(f"    💡 深度洞察：")
                    result.extend(insights)
        
        result.append("")
        
        # 车厢对比
        self._add_team_comparison(result, person)
        
        # 趋势分析
        self._add_trend_analysis(result, name)
        
        # 行动计划
        result.append("")
        result.append("【行动计划】")
        action_plan = self.analysis_engine.generate_action_plan(person, dimensions)
        result.extend(action_plan)
        
        result.append("")
        result.append("=" * 70)
        result.append(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append("=" * 70)
        
        return "\n".join(result)
    
    def _add_dimension_details(self, result: list, sheet_name: str, detail: pd.Series):
        """添加维度详细信息"""
        if sheet_name == 'OHT执行（30%）':
            result.append(f"    详细：")
            result.append(f"      - 车厢得分：{detail.get('车厢得分', 'N/A')}")
            result.append(f"      - 站台得分：{detail.get('站台得分', 'N/A')}")
            if pd.notna(detail.get('车厢-分位')):
                result.append(f"      - 车厢分位：{detail['车厢-分位']:.2%}")
            if pd.notna(detail.get('站台-分位')):
                result.append(f"      - 站台分位：{detail['站台-分位']:.2%}")
        
        elif sheet_name == '保障-(10%)':
            result.append(f"    详细：")
            result.append(f"      - 线上故障(40%)：{detail.get('线上故障(40%)', 'N/A')}")
            result.append(f"      - 线上BUG(20%)：{detail.get('线上BUG(20%)', 'N/A')}")
            result.append(f"      - 技术工单(20%)：{detail.get('技术工单(20%)', 'N/A'):.2f}")
            result.append(f"      - 漏洞超期(10%)：{detail.get('漏洞超期(10%)', 'N/A')}")
            result.append(f"      - 系统两用分(10%)：{detail.get('系统两用分(10%)', 'N/A')}")
        
        elif sheet_name == '影响力-(10%)':
            result.append(f"    详细：")
            result.append(f"      - 自评：{detail.get('自评', 'N/A')}")
            result.append(f"      - 同事评价：{detail.get('同事', 'N/A')}")
            result.append(f"      - 他评：{detail.get('他评', 'N/A')}")
        
        elif sheet_name == '努力度(10%)':
            result.append(f"    详细：")
            result.append(f"      - 平均工时：{detail.get('平均工时', 'N/A')}")
            result.append(f"      - 连续得分：{detail.get('连续得分', 'N/A'):.2f}")
        
        elif sheet_name == '系统价值分（5%）':
            result.append(f"    详细：")
            result.append(f"      - 所属车厢：{detail.get('车厢', 'N/A')}")
            result.append(f"      - 换算分数：{detail.get('换算', 'N/A')}")
            if pd.notna(detail.get('备注（多个系统则平均）')):
                result.append(f"      - 备注：{detail.get('备注（多个系统则平均）')}")
    
    def _add_team_comparison(self, result: list, person: pd.Series):
        """添加车厢对比"""
        if '数据透视表' not in self.data:
            return
        
        pivot = self.data['数据透视表']
        team = person['车厢']
        
        team_data = pivot[pivot['车厢'] == team]
        if team_data.empty:
            return
        
        team_avg = team_data.iloc[0]
        
        result.append("【与车厢平均对比】")
        result.append(f"  车厢：{team}")
        
        comparisons = [
            ('平均值:OHT执行30%', person['OHT执行30%']),
            ('平均值:OHT保障10%', person['OHT保障10%']),
            ('平均值:努力度10%', person['努力度10%']),
            ('平均值:价值分5%', person['价值分5%']),
            ('平均值:总分', person['总分'])
        ]
        
        for avg_col, personal_score in comparisons:
            if avg_col in team_avg.index:
                team_score = team_avg[avg_col]
                if pd.notna(team_score) and pd.notna(personal_score):
                    diff = personal_score - team_score
                    symbol = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                    result.append(f"  {avg_col.replace('平均值:', '')}：个人 {personal_score:.2f} vs 车厢 {team_score:.2f} {symbol} {diff:+.2f}")
    
    def _add_trend_analysis(self, result: list, name: str):
        """添加趋势分析"""
        result.append("")
        result.append("【趋势分析】")
        
        has_trend = False
        
        # 努力度趋势
        dec_effort, jan_effort = self._get_trend_data('努力度(10%)', name)
        if dec_effort is not None and jan_effort is not None:
            has_trend = True
            change = jan_effort - dec_effort
            percent_change = (change / dec_effort * 100) if dec_effort != 0 else 0
            symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            
            result.append(f"  • 努力度：12月 {dec_effort:.2f} → 1月 {jan_effort:.2f} {symbol} {change:+.2f} ({percent_change:+.1f}%)")
            
            if change < -0.5:
                result.append(f"    ⚠️  努力度下降明显，需关注工作投入度")
            elif change > 0.5:
                result.append(f"    ✨ 努力度提升明显，继续保持！")
        
        if not has_trend:
            result.append(f"  暂无月度趋势数据")
    
    def analyze_team(self, team_name: str) -> str:
        """
        分析车厢绩效
        
        Args:
            team_name: 车厢名称
            
        Returns:
            分析结论文本
        """
        # 查找车厢
        team_data = self.find_team(team_name)
        if team_data is None:
            return f"❌ 未找到车厢 '{team_name}' 的数据"
        
        # 开始分析
        result = []
        result.append("=" * 70)
        result.append(f"🚂 车厢绩效分析报告 - {team_name}")
        result.append("=" * 70)
        result.append("")
        
        # 车厢基本信息
        member_count = len(team_data)
        has_leader = (team_data['是否车厢长'] == '是').any()
        leader_name = team_data[team_data['是否车厢长'] == '是']['姓名'].values
        
        result.append("【车厢基本信息】")
        result.append(f"  车厢名称：{team_name}")
        result.append(f"  成员人数：{member_count} 人")
        if has_leader and len(leader_name) > 0:
            result.append(f"  车厢长：{', '.join(leader_name)}")
        else:
            result.append(f"  车厢长：无")
        result.append("")
        
        # 车厢总体表现
        avg_score = team_data['总分'].mean()
        avg_rank = team_data['RANK'].mean()
        
        # 获取数据透视表中的车厢数据
        pivot_data = None
        if '数据透视表' in self.data:
            pivot = self.data['数据透视表']
            pivot_team = pivot[pivot['车厢'] == team_name]
            if not pivot_team.empty:
                pivot_data = pivot_team.iloc[0]
        
        result.append("【车厢总体表现】")
        result.append(f"  平均总分：{avg_score:.2f} 分")
        result.append(f"  平均排名：第 {avg_rank:.1f} 名")
        
        # 与全公司对比
        if pivot_data is not None and '数据透视表' in self.data:
            pivot = self.data['数据透视表']
            company_avg = pivot[pivot['车厢'] == '总计']
            if not company_avg.empty:
                company_score = company_avg.iloc[0]['平均值:总分']
                diff = avg_score - company_score
                symbol = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                result.append(f"  vs 全公司：{symbol} {diff:+.2f} 分")
                
                # 计算车厢排名（过滤掉空白和标题行）
                team_scores = pivot[
                    (pivot['车厢'] != '总计') & 
                    (pivot['车厢'] != '(空白)') & 
                    (pivot['车厢'] != '归属实体') &
                    (pivot['车厢'].notna())
                ][['车厢', '平均值:总分']].copy()
                
                # 转换为float类型
                team_scores['平均值:总分'] = pd.to_numeric(team_scores['平均值:总分'], errors='coerce')
                team_scores = team_scores.dropna()
                
                if not team_scores.empty:
                    team_scores_sorted = team_scores.sort_values('平均值:总分', ascending=False, ignore_index=True)
                    team_rank_idx = team_scores_sorted[team_scores_sorted['车厢'] == team_name].index
                    if len(team_rank_idx) > 0:
                        team_rank = team_rank_idx[0] + 1
                        total_teams = len(team_scores_sorted)
                        result.append(f"  车厢排名：第 {team_rank} 名 / 共 {total_teams} 个车厢")
        
        result.append("")
        
        # 各维度平均得分
        result.append("【各维度平均得分】")
        
        dimensions = [
            ('OHT执行30%', 30),
            ('OHT保障10%', 10),
            ('影响力10%', 10),
            ('努力度10%', 10),
            ('价值分5%', 5)
        ]
        
        for dim_name, weight in dimensions:
            avg_dim_score = team_data[dim_name].mean()
            result.append(f"\n  【{dim_name}】")
            result.append(f"    平均得分：{self._format_score(avg_dim_score, 10)}")
            result.append(f"    权重：{weight}%")
            
            # 与全公司对比
            if pivot_data is not None:
                pivot_col = f'平均值:{dim_name}'
                if pivot_col in pivot_data.index:
                    pivot_score = pivot_data[pivot_col]
                    if '数据透视表' in self.data:
                        company_avg = self.data['数据透视表'][self.data['数据透视表']['车厢'] == '总计']
                        if not company_avg.empty and pivot_col in company_avg.iloc[0].index:
                            company_score = company_avg.iloc[0][pivot_col]
                            if pd.notna(company_score):
                                diff = avg_dim_score - company_score
                                symbol = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                                result.append(f"    vs 全公司：{symbol} {diff:+.2f}")
        
        result.append("")
        
        # 成员排名分布
        result.append("【成员排名分布】")
        top10_count = len(team_data[team_data['RANK'] <= 6])  # 前10%约6人
        top30_count = len(team_data[team_data['RANK'] <= 17])  # 前30%约17人
        top50_count = len(team_data[team_data['RANK'] <= 28])  # 前50%约28人
        
        result.append(f"  🏆 前10%：{top10_count} 人 ({top10_count/member_count*100:.1f}%)")
        result.append(f"  🌟 前30%：{top30_count} 人 ({top30_count/member_count*100:.1f}%)")
        result.append(f"  👍 前50%：{top50_count} 人 ({top50_count/member_count*100:.1f}%)")
        result.append("")
        
        # Top 3成员
        result.append("【车厢Top 3成员】")
        top3 = team_data.nsmallest(3, 'RANK')[['姓名', 'RANK', '总分', '是否车厢长']]
        for idx, row in top3.iterrows():
            leader_tag = "👑" if row['是否车厢长'] == '是' else ""
            result.append(f"  {leader_tag} {row['姓名']}：第 {row['RANK']} 名，总分 {row['总分']:.2f}")
        
        result.append("")
        
        # 需要关注的成员（排名后30%）
        bottom_threshold = 40  # 第40名之后
        bottom_members = team_data[team_data['RANK'] > bottom_threshold].nsmallest(5, 'RANK')[['姓名', 'RANK', '总分']]
        if not bottom_members.empty:
            result.append("【需要关注的成员】（排名后30%）")
            for idx, row in bottom_members.iterrows():
                result.append(f"  📈 {row['姓名']}：第 {row['RANK']} 名，总分 {row['总分']:.2f}")
            result.append("")
        
        # 车厢深度分析和管理建议
        self._add_team_deep_insights(result, team_name, team_data, dimensions, avg_score)
        
        result.append("")
        result.append("=" * 70)
        result.append(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append("=" * 70)
        
        return "\n".join(result)
    
    def _add_team_deep_insights(self, result: list, team_name: str, team_data: pd.DataFrame, 
                                 dimensions: list, avg_score: float):
        """添加车厢深度洞察和管理建议"""
        result.append("【深度洞察与管理建议】")
        
        # 找出最强和最弱的维度
        dim_scores = [(dim[0], team_data[dim[0]].mean()) for dim in dimensions]
        dim_scores.sort(key=lambda x: x[1], reverse=True)
        
        result.append(f"\n  💪 优势维度：")
        for dim_name, score in dim_scores[:2]:
            result.append(f"    - {dim_name}：平均 {score:.2f} 分")
        
        result.append(f"\n  📈 改进维度：")
        weak_dims = []
        for dim_name, score in dim_scores[-2:]:
            if score < 8:
                result.append(f"    - {dim_name}：平均 {score:.2f} 分")
                weak_dims.append((dim_name, score))
        
        # 成员分布分析
        result.append(f"\n  🔍 成员分布分析：")
        top_count = len(team_data[team_data['RANK'] <= 17])
        bottom_count = len(team_data[team_data['RANK'] > 40])
        
        if top_count / len(team_data) < 0.3:
            result.append(f"    ⚠️  优秀成员占比较低（{top_count/len(team_data)*100:.0f}%），缺少领头羊")
            result.append(f"       建议：识别潜力成员，制定重点培养计划")
        
        if bottom_count > 0:
            result.append(f"    ⚠️  有{bottom_count}名成员排名后30%，需重点帮扶")
            result.append(f"       建议：建立mentor机制，让Top成员带动后进成员")
        
        # 具体管理建议
        result.append(f"\n  💡 车厢长管理建议：")
        
        if avg_score >= 8.5:
            result.append(f"    ✅ 车厢整体表现优秀！")
            result.append(f"       1. 总结成功经验，形成最佳实践文档")
            result.append(f"       2. 帮助排名靠后成员，缩小组内差距")
            result.append(f"       3. 保持优势维度，争取全公司第一")
        elif avg_score >= 8.0:
            result.append(f"    👍 车厢表现良好，需持续优化")
            for dim_name, score in weak_dims:
                result.append(f"       - 针对{dim_name}：组织专项提升活动")
            result.append(f"       - 定期1on1，了解成员困难并提供支持")
        else:
            result.append(f"    ⚠️  车厢需要整体提升")
            result.append(f"       1. 分析薄弱维度原因，制定改进计划")
            result.append(f"       2. 每周团队分享会，促进经验传递")
            result.append(f"       3. 设立月度改进目标，跟踪进展")
        
        # 对标建议
        if '数据透视表' in self.data:
            pivot = self.data['数据透视表']
            team_scores = pivot[
                (pivot['车厢'] != '总计') & 
                (pivot['车厢'] != '(空白)') & 
                (pivot['车厢'] != '归属实体') &
                (pivot['车厢'].notna())
            ][['车厢', '平均值:总分']].copy()
            team_scores['平均值:总分'] = pd.to_numeric(team_scores['平均值:总分'], errors='coerce')
            team_scores = team_scores.dropna().sort_values('平均值:总分', ascending=False)
            
            if not team_scores.empty and len(team_scores) > 1:
                top_team = team_scores.iloc[0]
                if top_team['车厢'] != team_name:
                    result.append(f"\n  🎯 对标优秀车厢：")
                    result.append(f"    标杆车厢：{top_team['车厢']}（平均分{top_team['平均值:总分']:.2f}）")
                    gap = top_team['平均值:总分'] - avg_score
                    result.append(f"    差距：{gap:.2f}分")
                    result.append(f"    建议：与{top_team['车厢']}车厢长交流，学习管理经验")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='绩效分析脚本 v2.0 - 深度分析和月份支持',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 个人分析
  python performance_analyzer.py 丁星杰
  python performance_analyzer.py --month 12 丁星杰  # 查看12月数据
  python performance_analyzer.py --month 1 丁星杰   # 查看1月数据
  
  # 车厢分析
  python performance_analyzer.py --team 站内营销
  python performance_analyzer.py -t 三教服务
  
  # 交互式模式
  python performance_analyzer.py
  python performance_analyzer.py --team
        """
    )
    
    parser.add_argument('name', nargs='?', help='员工姓名或车厢名称（配合--team使用）')
    parser.add_argument('--file', '-f', default='baseInfo/FY26Q3-汇总版-v1.xlsx',
                       help='Excel文件路径 (默认: baseInfo/FY26Q3-汇总版-v1.xlsx)')
    parser.add_argument('--team', '-t', action='store_true',
                       help='分析车厢绩效（而非个人绩效）')
    parser.add_argument('--month', '-m', choices=['12', '1', 'all'], default='all',
                       help='指定月份：12(12月), 1(1月), all(全部/汇总，默认)')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.file):
        print(f"❌ 错误：找不到文件 {args.file}")
        sys.exit(1)
    
    # 创建分析器
    analyzer = PerformanceAnalyzer(args.file, args.month)
    
    # 判断是车厢分析还是个人分析
    if args.team:
        # 车厢分析模式
        team_name = args.name
        if not team_name:
            team_name = input("请输入车厢名称：").strip()
            if not team_name:
                print("❌ 错误：车厢名称不能为空")
                sys.exit(1)
        
        # 分析并输出
        result = analyzer.analyze_team(team_name)
        print(result)
    else:
        # 个人分析模式
        name = args.name
        if not name:
            name = input("请输入员工姓名：").strip()
            if not name:
                print("❌ 错误：姓名不能为空")
                sys.exit(1)
        
        # 分析并输出
        result = analyzer.analyze_person(name)
        print(result)


if __name__ == '__main__':
    main()
