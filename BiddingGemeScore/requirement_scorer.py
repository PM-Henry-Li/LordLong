#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求优先级打分与资源分配系统
根据《FY25系统功能使用考核-节奏拉齐》规则进行需求优先级计算和资源分配
"""

import json
import csv
from typing import List, Dict, Tuple
from datetime import datetime
from pathlib import Path


class RequirementScorer:
    """需求优先级打分器"""
    
    def __init__(self, total_score: float):
        """
        初始化打分器
        
        Args:
            total_score: 可用总分池
        """
        self.total_score = total_score
        self.requirements = []
        self.x_class_requirements = []  # X类需求（故障类）
        
    def load_from_json(self, file_path: str):
        """从JSON文件加载需求清单"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'requirements' in data:
                self.requirements = data['requirements']
                if 'total_score' in data:
                    self.total_score = data['total_score']
            elif isinstance(data, list):
                self.requirements = data
            else:
                raise ValueError("JSON格式错误：应为包含requirements数组的对象，或直接为数组")
        
        # 处理轻学需求标记和字段映射
        for req in self.requirements:
            # 支持新字段名：所属业务团队
            if '所属业务团队' in req and 'business_line' not in req:
                req['business_line'] = req['所属业务团队']
            
            # 支持新字段名：需求标题
            if '需求标题' in req and 'name' not in req:
                req['name'] = req['需求标题']
            
            business_line = req.get('business_line', '').strip()
            is_qingxue = req.get('is_qingxue', False)
            if isinstance(is_qingxue, str):
                is_qingxue = is_qingxue.lower() in ['是', 'yes', 'true', '1']
            # 如果业务线包含轻学，自动标记
            if '轻学' in business_line:
                req['is_qingxue'] = True
            else:
                req['is_qingxue'] = is_qingxue
            
            # 支持新字段名：业务需求优先级（映射到category）
            if '业务需求优先级' in req and 'category' not in req:
                req['category'] = req['业务需求优先级']
            
            # 确保有时间维度字段
            if 'time_dimension' not in req:
                req['time_dimension'] = req.get('时间维度', '季度')
            
            # 确保有季度计划字段（新模板可能没有）
            if 'quarter_plan' not in req:
                req['quarter_plan'] = req.get('季度计划', '未进入')
    
    def load_from_csv(self, file_path: str):
        """从CSV文件加载需求清单（支持新旧字段名，处理空行和部分字段为空）"""
        requirements = []
        last_business_line = ''  # 用于继承上一行的业务线
        last_category = ''  # 用于继承上一行的分类
        last_planning_status = ''  # 用于继承上一行的规划属性
        last_urgency = ''  # 用于继承上一行的紧迫度
        last_true_demand = ''  # 用于继承上一行的真需求判断
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 检查是否为空行（所有关键字段都为空）
                name = row.get('需求标题', row.get('需求名称', row.get('name', ''))).strip()
                business_line_raw = row.get('所属业务团队', row.get('业务线', row.get('business_line', ''))).strip()
                
                # 如果业务线为空，尝试继承上一行的值
                if business_line_raw:
                    last_business_line = business_line_raw
                elif last_business_line:
                    business_line_raw = last_business_line
                else:
                    # 如果业务线和需求标题都为空，跳过这一行
                    if not name:
                        continue
                    # 如果只有业务线为空但有需求标题，使用默认值
                    business_line_raw = ''
                
                business_line = business_line_raw
                
                # 识别轻学需求：业务线包含"轻学"或单独标记为轻学
                is_qingxue = '轻学' in business_line or row.get('是否轻学', row.get('is_qingxue', '否')).lower() in ['是', 'yes', 'true', '1']
                
                # 如果需求标题为空，跳过这一行（可能是空行或子项）
                if not name:
                    continue
                
                # 从关联目标及方向提取分类信息（优先，如"B类：【重点项目】"）
                related_targets = row.get('关联目标及方向', '')
                category = ''
                
                # 优先从关联目标及方向提取分类（因为实际数据中分类信息在这里）
                if related_targets:
                    related_targets_str = str(related_targets).strip()
                    # 优先检查明确的分类标识（X/A/B/C/D/E类），避免误判
                    if 'X类' in related_targets_str or '系统故障' in related_targets_str:
                        category = 'X类'
                    elif 'A类' in related_targets_str:
                        category = 'A类'
                    elif 'B类' in related_targets_str:
                        category = 'B类'
                    elif 'C类' in related_targets_str:
                        category = 'C类'
                    elif 'D类' in related_targets_str:
                        category = 'D类'
                    elif 'E类' in related_targets_str:
                        category = 'E类'
                    # 如果没有明确的分类标识，再检查关键词（向后兼容）
                    elif '季度重点' in related_targets_str:
                        category = 'E类'
                    elif '数据需求' in related_targets_str:
                        category = 'C类'
                    elif '重点项目' in related_targets_str:
                        category = 'B类'
                    elif '考核' in related_targets_str and '落地' in related_targets_str and '落地结束' not in related_targets_str:
                        category = 'A类'
                
                # 如果从关联目标及方向没有提取到，使用业务需求优先级字段
                if not category:
                    category = row.get('业务需求优先级', '').strip()
                    
                    # 处理P0/P1等优先级标记，映射到分类
                    if category.startswith('P'):
                        # P0/P1等优先级标记，根据关联目标及方向判断或使用默认
                        if 'B类' in related_targets or '重点项目' in related_targets:
                            category = 'B类'
                        else:
                            category = 'D类'  # 默认映射到D类
                
                # 如果分类仍为空，尝试使用需求分类字段
                if not category:
                    category = row.get('需求分类', row.get('category', ''))
                
                # 如果分类仍为空，尝试继承上一行的值
                if not category and last_category:
                    category = last_category
                
                # 更新last_category
                if category:
                    last_category = category
                
                # 支持新字段名：关联目标及方向（可能对应关联重点项目数）
                # 尝试从关联目标及方向提取数字
                related_projects = 0
                if related_targets:
                    # 尝试从文本中提取数字（如"关联2个重点项目"）
                    import re
                    numbers = re.findall(r'\d+', str(related_targets))
                    if numbers:
                        related_projects = int(numbers[0])
                # 如果没有从新字段提取到，使用旧字段
                if related_projects == 0:
                    related_projects = int(row.get('关联重点项目数', row.get('related_projects', 0)) or 0)
                
                # 季度计划（保持向后兼容，新模板可能没有此字段）
                quarter_plan = row.get('季度计划', row.get('quarter_plan', '未进入'))
                
                # 规划属性（新字段：规划内/规划外）
                planning_status = row.get('规划属性', row.get('规划状态', row.get('planning_status', ''))).strip()
                # 如果为空，尝试继承上一行的值
                if not planning_status and last_planning_status:
                    planning_status = last_planning_status
                # 如果没有明确指定，根据季度计划推断
                if not planning_status:
                    if '本季度' in quarter_plan or '当前季度' in quarter_plan or '下季度' in quarter_plan:
                        planning_status = '规划内'
                    else:
                        planning_status = '规划外'
                # 更新last_planning_status
                if planning_status:
                    last_planning_status = planning_status
                
                # 紧迫度（新字段：P0/P1/P2/P3）
                urgency = row.get('紧迫度', row.get('优先级', row.get('urgency', row.get('priority', '')))).strip().upper()
                # 如果为空，尝试继承上一行的值
                if not urgency and last_urgency:
                    urgency = last_urgency
                # 如果没有明确指定，尝试从业务需求优先级字段提取（如P0）
                if not urgency:
                    priority_field = row.get('业务需求优先级', '').strip().upper()
                    if priority_field.startswith('P'):
                        urgency = priority_field
                    else:
                        urgency = 'P2'  # 默认P2
                # 更新last_urgency
                if urgency:
                    last_urgency = urgency
                
                # 真需求判断（新字段：真/伪，可选，如果不填写则自动分析）
                true_demand = row.get('真需求判断', row.get('真需求', row.get('true_demand', ''))).strip()
                # 如果为空，尝试继承上一行的值
                if not true_demand and last_true_demand:
                    true_demand = last_true_demand
                # 如果没有明确指定，留空，后续通过内容分析自动判断
                # 更新last_true_demand
                if true_demand:
                    last_true_demand = true_demand
                
                # 启动状态
                status = row.get('启动状态', row.get('status', ''))
                
                # 是否故障（X类需求）
                is_fault = row.get('是否故障', row.get('is_fault', '否')).lower() in ['是', 'yes', 'true', '1']
                
                # 时间维度（轻学需求必填）
                time_dimension = row.get('时间维度', row.get('time_dimension', '季度')).strip()
                
                # FY26战略加分（新字段，可选，支持O1/O3/O4/O5指定）
                # 系统会自动分析需求内容匹配FY26战略目标，也可手动指定
                fy26_bonus_field = row.get('FY26战略加分', row.get('FY25战略加分', row.get('战略加分', row.get('fy26_bonus', '')))).strip()
                
                requirements.append({
                    'name': name,
                    'business_line': business_line,
                    'category': category,
                    'quarter_plan': quarter_plan,
                    'planning_status': planning_status,  # 规划属性：规划内/规划外
                    'urgency': urgency,  # 紧迫度：P0/P1/P2/P3
                    'true_demand': true_demand,  # 真需求判断：真/伪
                    'status': status,
                    'is_fault': is_fault,
                    'related_projects': related_projects,
                    'is_qingxue': is_qingxue,
                    'time_dimension': time_dimension,
                    'fy26_bonus_field': fy26_bonus_field,  # FY26战略加分字段（可选）
                    # 保存新字段（用于报告展示）
                    'related_targets': related_targets,
                    'core_delivery': row.get('核心交付功能说明', row.get('core_delivery', '')),
                    'current_data': row.get('当前数据及落地指标', row.get('current_data', '')),
                    'benefit': row.get('收益', row.get('benefit', ''))
                })
        self.requirements = requirements
    
    def add_requirement(self, requirement: Dict):
        """添加单个需求"""
        self.requirements.append(requirement)
    
    def _calculate_fy26_bonus(self, req: Dict) -> tuple:
        """
        计算FY26战略加分
        
        FY26战略加分规则（基于最新Prompt）：
        - O1：提升私域引流与资源转化能力（+20分）
          - KR1：（考研）未报名学员转工单率提升至15%
          - KR2：（考研）通过私域运营实现APP年度营收400万
          - KR3：（专升本）通过择校小程序及渠道专题升级收资能力
          - KR4：（考研）打造满足线下&在线多场景的AI择校能力
          - KR5：（轻学）将学科小程序从单一资料工具升级为用户全生命周期管理平台
        - O2：考研APP核心功能鸿蒙系统版本支持（已暂停，不计分）
        - O3：练测功能升级迭代（+15分）
          - KR1：（考研）完成题库能力更新，增加题库标准题目数量
          - KR2：（考研+四六级+专升本）练测与模考模块功能迭代
          - KR3：（考研+四六级+专升本）学习成绩回收和个性化报告能力迭代
        - O4：赋能教师与教研（+15分）
          - KR1：（考研）构建教师工作台，实现核心教学教务动作平台化
          - KR2：（考研）通过资料管理能力搭建，提升标化教研内容上传下达
          - KR3：（考研）通过AI答疑建设，降低教师在“非授课”环节的人均工作耗时
        - O5：实现学员差异化运营（+15分）
          - KR1：（考研）基于报名项目，完成学员分层运营策略
          - KR2：（考研）已报名学员学习进度提升至30~35%（当前24%）
          - KR3：（全品线）OMO融合能力建设
        
        Args:
            req: 需求字典
            
        Returns:
            (FY26战略加分值, 匹配的O和KR列表)
        """
        bonus = 0
        matched_oks = []
        
        # 获取业务线
        business_line = req.get('business_line', '').strip()
        is_qingxue = self._is_qingxue(req)
        
        # 收集需求文本内容
        name = req.get('name', '').strip()
        core_delivery = req.get('core_delivery', '').strip()
        benefit = req.get('benefit', '').strip()
        related_targets = req.get('related_targets', '').strip()
        current_data = req.get('current_data', '').strip()
        
        full_text = f"{name} {core_delivery} {benefit} {related_targets} {current_data}".strip()
        
        # O1：提升私域引流与资源转化能力（+20分）
        o1_keywords = [
            # KR1：（考研）未报名学员转工单率
            ('转工单', '工单率', '未报名学员', '工单转化'),
            # KR2：（考研）通过私域运营实现APP年度营收
            ('私域运营', '私域', 'APP营收', '年度营收', '营收'),
            # KR3：（专升本）通过择校小程序及渠道专题升级收资能力
            ('择校小程序', '渠道专题', '专升本择校', '收资能力'),
            # KR4：（考研）打造满足线下&在线多场景的AI择校能力
            ('AI择校', '择校能力', '智能择校', '多场景'),
            # KR5：（轻学）将学科小程序升级为用户全生命周期管理平台
            ('学科小程序', '全生命周期管理', '拉新', '留存', '转化', '私域闭环', '小程序', '二维码', '功能', '优化')
        ]
        
        o1_matched = False
        for i, kr_keywords in enumerate(o1_keywords):
            kr_index = i + 1
            if any(keyword in full_text for keyword in kr_keywords):
                # 检查业务线匹配
                if kr_index in [1, 2, 4] and ('考研' in business_line):  # KR1, KR2, KR4: 考研
                    o1_matched = True
                    matched_oks.append(f'O1-KR{kr_index}')
                    break
                elif kr_index == 3 and ('专升本' in business_line):  # KR3: 专升本
                    o1_matched = True
                    matched_oks.append(f'O1-KR{kr_index}')
                    break
                elif kr_index == 5 and is_qingxue:  # KR5: 轻学
                    o1_matched = True
                    matched_oks.append(f'O1-KR{kr_index}')
                    break
        
        if o1_matched:
            bonus += 20
        
        # O3：练测功能升级迭代（+15分）
        o3_keywords = [
            # KR1：（考研）完成题库能力更新
            ('题库', '题库更新', '题库能力', '题库升级', '知识点', '试题'),
            # KR2：（考研+四六级+专升本）练测与模考模块功能迭代
            ('练测', '模考', '练测模块', '模考模块', '阶段测', '标准化'),
            # KR3：（考研+四六级+专升本）学习成绩回收和个性化报告
            ('学习成绩回收', '个性化报告', '学习效果', '学习报告', '成绩回收')
        ]
        
        o3_matched = False
        for i, kr_keywords in enumerate(o3_keywords):
            kr_index = i + 1
            if any(keyword in full_text for keyword in kr_keywords):
                if kr_index == 1 and ('考研' in business_line): # KR1: 考研
                    o3_matched = True
                    matched_oks.append(f'O3-KR{kr_index}')
                    break
                elif kr_index in [2, 3]: # KR2, KR3: 考研+四六级+专升本
                     # check if business line is one of them
                     if any(bl in business_line for bl in ['考研', '四六级', '专升本', '集训营', '专业课']):
                        o3_matched = True
                        matched_oks.append(f'O3-KR{kr_index}')
                        break
        
        if o3_matched:
            bonus += 15
        
        # O4：赋能教师与教研（+15分）
        o4_keywords = [
            # KR1：（考研）构建教师工作台
            ('教师工作台', '工作台', '教师平台'),
            # KR2：（考研）通过资料管理能力搭建
            ('资料管理', '教研内容', '标化教研', '内容上传下达'),
            # KR3：（考研）通过AI答疑建设
            ('AI答疑', '答疑', '智能答疑', '自动答疑')
        ]
        
        o4_matched = False
        for i, kr_keywords in enumerate(o4_keywords):
            kr_index = i + 1
            if any(keyword in full_text for keyword in kr_keywords) and ('考研' in business_line):
                o4_matched = True
                matched_oks.append(f'O4-KR{kr_index}')
                break
        
        if o4_matched:
            bonus += 15
        
        # O5：实现学员差异化运营（+15分）
        o5_keywords = [
            # KR1：（考研）完成学员分层运营策略
            ('学员分层', '分层运营', '分层策略'),
            # KR2：（考研）已报名学员学习进度提升
            ('学习进度', '已报名学员', '进度提升'),
            # KR3：（全品线）OMO融合能力建设
            ('OMO', 'OMO融合', '融合能力', '线上线下融合')
        ]
        
        o5_matched = False
        for i, kr_keywords in enumerate(o5_keywords):
            kr_index = i + 1
            if any(keyword in full_text for keyword in kr_keywords):
                if kr_index in [1, 2] and ('考研' in business_line):
                     o5_matched = True
                     matched_oks.append(f'O5-KR{kr_index}')
                     break
                elif kr_index == 3:  # KR3：全品线
                    o5_matched = True
                    matched_oks.append(f'O5-KR{kr_index}')
                    break
        
        if o5_matched:
            bonus += 15
        
        return bonus, matched_oks
    
    def _calculate_score(self, req: Dict) -> float:
        """
        计算单个需求的最终价值分 S_final
        
        新公式（基于prompt.md更新）：
        S_final = [(战略基分 × 紧迫系数 × 规划系数) + 真需求修正 + FY26战略加分] × 业务加权
        
        1. 战略基分 (Strategic Base)：
           - A类（考核落地）：100分
           - B类（重点项目）：60分（含轻学、小程序等）
           - C类（常态/数据）：20分
           - D类（非考核类+考核类落地结束）：10分（向后兼容）
           - E类（季度重点）：映射到B类，60分
           - X类（故障）：∞（不参与打分）
        
        2. 规划系数 (Planning Discipline Factor)：
           - 规划内（In Plan）：1.5
           - 规划外（Ad-hoc）：0.8
        
        3. 紧迫度系数 (Urgency Coefficient)：
           - P0（致命）：2.0
           - P1（必须）：1.5（更新）
           - P2（改善）：1.0
           - P3（微调）：0.5（更新）
        
        4. 真需求修正 (True Demand Correction)：
           - 真需求：+50分
           - 伪需求：-50分
        
        5. FY26战略加分：
           - O1：提升私域引流与资源转化能力：+20分
           - O3：练测功能升级迭代：+15分
           - O4：赋能教师与教研：+15分
           - O5：实现学员差异化运营：+15分
           - O2：已暂停，不计分
        
        6. 业务加权 (Business Boost)：
           - 轻学需求：1.2
           - 其他需求：1.0
        
        Args:
            req: 需求字典
            
        Returns:
            最终价值分（已应用业务加权）
        """
        category = req.get('category', '').strip()
        
        # 1. 战略基分
        # A类（考核落地）：100分
        if category == 'A类' or 'A类' in category or ('考核' in category and '落地' in category and '落地结束' not in category):
            strategic_base = 100
        # B类（重点建设）：60分
        elif category == 'B类' or 'B类' in category or '重点项目' in category:
            strategic_base = 60
        # E类（季度重点）：映射到B类，60分
        elif category == 'E类' or 'E类' in category or '季度重点' in category:
            strategic_base = 60
        # C类（常态/其他）：20分
        elif category == 'C类' or 'C类' in category or '数据需求' in category:
            strategic_base = 20
        # D类（非考核类+考核类落地结束）：10分（向后兼容，原为1分）
        elif category == 'D类' or 'D类' in category:
            strategic_base = 10
        # 向后兼容旧分类
        elif '考核落地' in category:
            strategic_base = 100
        elif '重点项目' in category:
            strategic_base = 60
        else:  # 其他需求，默认为D类
            strategic_base = 10
        
        # 2. 规划系数
        planning_status = req.get('planning_status', '').strip()
        if not planning_status:
            # 如果没有规划属性字段，根据季度计划推断
            quarter_plan = req.get('quarter_plan', '').strip()
            if '本季度' in quarter_plan or '当前季度' in quarter_plan or '下季度' in quarter_plan:
                planning_status = '规划内'
            else:
                planning_status = '规划外'
        
        if '规划内' in planning_status or 'In Plan' in planning_status or planning_status.lower() == 'in plan':
            planning_factor = 1.5
        else:  # 规划外（Ad-hoc）
            planning_factor = 0.8
        
        # 3. 紧迫度系数
        urgency = req.get('urgency', '').strip().upper()
        if not urgency:
            # 如果没有紧迫度字段，尝试从其他字段推断
            priority_field = req.get('priority', '').strip().upper()
            if priority_field.startswith('P'):
                urgency = priority_field
            else:
                urgency = 'P2'  # 默认P2
        
        if urgency == 'P0':
            urgency_factor = 2.0
        elif urgency == 'P1':
            urgency_factor = 1.5  # 更新：从1.2改为1.5
        elif urgency == 'P2':
            urgency_factor = 1.0
        elif urgency == 'P3':
            urgency_factor = 0.5  # 更新：从0.8改为0.5
        else:
            # 向后兼容：根据启动状态推断
            status = req.get('status', '').strip()
            if '开发中' in status:
                urgency_factor = 1.5  # 开发中视为P1（更新为1.5）
            else:
                urgency_factor = 1.0  # 默认P2
        
        # 4. 真需求修正（基于梁宁《真需求》理论，通过分析需求标题和描述自动判断）
        # 4. 真需求修正（基于梁宁《真需求》理论）
        true_demand_field = req.get('true_demand', '').strip()
        
        # 梁宁四种类型判定
        if '核心真需求' in true_demand_field:
            true_demand_correction = 50
            true_demand_reason = "💎 核心真需求 (高价值+高频)"
        elif '魅力型需求' in true_demand_field:
             true_demand_correction = 30
             true_demand_reason = "✨ 魅力型需求 (高情绪价值)"
        elif '基础型需求' in true_demand_field:
             true_demand_correction = 40
             true_demand_reason = "🔧 基础型需求 (必备属性)"
        elif '伪需求' in true_demand_field or '弱需求' in true_demand_field:
             true_demand_correction = -50
             true_demand_reason = "❌ 伪需求 (无场景/无代价)"
        # 向后兼容逻辑
        elif true_demand_field and ('真' in true_demand_field or 'true' in true_demand_field.lower() or true_demand_field.lower() == 't'):
            true_demand_correction = 50
            true_demand_reason = "字段指定为真需求"
        elif true_demand_field and ('伪' in true_demand_field or 'false' in true_demand_field.lower() or true_demand_field.lower() == 'f'):
            true_demand_correction = -50
            true_demand_reason = "字段指定为伪需求"
        else:
            # 自动分析需求内容
            is_true, reason, correction = self._analyze_true_demand(req)
            true_demand_correction = correction
            true_demand_reason = reason
            # 保存判断结果和理由
            req['true_demand_analysis'] = {
                'is_true': is_true,
                'reason': reason,
                'correction': correction
            }
        
        # 5. FY26战略加分
        fy26_bonus, matched_oks = self._calculate_fy26_bonus(req)
        
        # 6. 业务加权
        business_boost = 1.2 if self._is_qingxue(req) else 1.0
        
        # 计算基础价值分（未应用业务加权）
        base_score = (strategic_base * planning_factor * urgency_factor) + true_demand_correction + fy26_bonus
        
        # 应用业务加权，得到最终价值分
        final_score = base_score * business_boost
        
        # 保存各组成部分用于报告展示
        req['strategic_base'] = strategic_base
        req['planning_factor'] = planning_factor
        req['urgency_factor'] = urgency_factor
        req['true_demand_correction'] = true_demand_correction
        req['fy26_bonus'] = fy26_bonus
        req['fy26_matched_oks'] = matched_oks  # 保存匹配的O和KR
        req['business_boost'] = business_boost
        req['base_score'] = base_score  # 基础分（未应用业务加权）
        
        return final_score
    
    def _is_x_class(self, req: Dict) -> bool:
        """
        判断是否为X类需求（系统故障或学员大面积无法使用）
        
        X类识别方式：
        1. 分类字段包含"X类"
        2. 是否故障字段为"是"
        3. 分类描述包含"系统故障"或"大面积无法使用"
        """
        category = req.get('category', '').strip()
        
        # 从分类字段识别
        if category == 'X类' or 'X类' in category:
            return True
        
        # 从是否故障字段识别
        is_fault = req.get('is_fault', False)
        if isinstance(is_fault, str):
            is_fault = is_fault.lower() in ['是', 'yes', 'true', '1']
        if is_fault:
            return True
        
        # 从分类描述识别
        if '系统故障' in category or '大面积无法使用' in category:
            return True
        
        return False
    
    def _is_qingxue(self, req: Dict) -> bool:
        """判断是否为轻学需求"""
        is_qingxue = req.get('is_qingxue', False)
        if isinstance(is_qingxue, str):
            is_qingxue = is_qingxue.lower() in ['是', 'yes', 'true', '1']
        # 也可以通过业务线名称判断
        if not is_qingxue:
            business_line = req.get('business_line', '').strip()
            is_qingxue = '轻学' in business_line
        return is_qingxue
    
    def _analyze_true_demand(self, req: Dict) -> tuple:
        """
        基于梁宁《真需求》理论，分析需求标题和描述，判断是否为真需求
        
        真需求的特征（基于梁宁理论）：
        1. 解决明确的用户痛点或问题（功能价值）
        2. 有具体的用户场景描述
        3. 有明确的业务价值或收益（价值闭环）
        4. 描述中包含解决问题的动词（提升、优化、解决、改善等）
        5. 有数据指标或可衡量的结果
        6. 描述逻辑清晰，有闭环
        
        伪需求的特征：
        1. 只是表面功能描述，没有说明为什么需要
        2. 描述模糊，缺乏具体场景
        3. 只是"要一匹更快的马"式的表面需求
        4. 缺乏业务价值说明
        5. 描述过于简单，没有说明解决的问题
        
        Args:
            req: 需求字典
            
        Returns:
            (是否为真需求(bool), 判断理由(str), 修正值(int))
        """
        # 收集需求文本内容
        name = req.get('name', '').strip()
        core_delivery = req.get('core_delivery', '').strip()
        benefit = req.get('benefit', '').strip()
        current_data = req.get('current_data', '').strip()
        related_targets = req.get('related_targets', '').strip()
        
        # 合并所有文本内容进行分析
        full_text = f"{name} {core_delivery} {benefit} {current_data} {related_targets}".strip()
        
        if not full_text:
            # 如果没有文本内容，默认真需求，不计修正
            return True, "无文本内容，默认真需求", 0
        
        # 真需求特征关键词（正向指标，基于梁宁《真需求》理论）
        true_demand_indicators = {
            '问题解决': ['解决', '修复', '处理', '消除', '避免', '防止', '减少', '降低', '修复', '修复问题'],
            '价值提升': ['提升', '提高', '优化', '改善', '增强', '完善', '升级', '改进', '加强', '优化'],
            '场景描述': ['用户', '学员', '教师', '场景', '情况', '场景', '使用', '操作', '体验'],
            '数据指标': ['数据', '指标', '率', '完成率', '正确率', '效率', '效果', '频次', '量'],
            '业务价值': ['收益', '价值', '目标', '考核', '达成', '实现', '完成', '服务', '带来'],
            '逻辑闭环': ['流程', '闭环', '打通', '连接', '关联', '整合', '统一', '协同', '适配']
        }
        
        # 伪需求特征关键词（负向指标）
        false_demand_indicators = {
            '表面需求': ['要', '需要', '希望', '想要', '建议'],
            '模糊描述': ['功能', '模块', '系统', '平台', '功能'],
            '缺乏场景': ['增加', '新增', '添加', '创建', '建立', '搭建']
        }
        
        # 计算真需求得分
        true_score = 0
        true_reasons = []
        
        for category, keywords in true_demand_indicators.items():
            # 去重关键词
            unique_keywords = list(set(keywords))
            count = sum(1 for keyword in unique_keywords if keyword in full_text)
            if count > 0:
                true_score += count
                true_reasons.append(f"{category}({count}个关键词)")
        
        # 计算伪需求得分
        false_score = 0
        false_reasons = []
        
        for category, keywords in false_demand_indicators.items():
            if keywords:
                # 去重关键词
                unique_keywords = list(set(keywords))
                count = sum(1 for keyword in unique_keywords if keyword in full_text)
                if count > 0:
                    false_score += count
                    false_reasons.append(f"{category}({count}个关键词)")
        
        # 特殊判断：基于梁宁理论的核心判断
        # 1. 是否有明确的问题或痛点描述
        has_problem_description = any(keyword in full_text for keyword in ['问题', '痛点', '困难', '阻碍', '障碍', '不足', '缺失', '无法', '不能'])
        
        # 2. 是否有价值或收益说明
        has_value_description = any(keyword in full_text for keyword in ['收益', '价值', '目标', '解决', '提升', '优化', '改善', '服务', '带来'])
        
        # 3. 是否有具体的用户场景
        has_scene_description = any(keyword in full_text for keyword in ['用户', '学员', '教师', '场景', '情况', '使用', '操作', '体验'])
        
        # 4. 是否有数据指标或可衡量结果
        has_metric_description = any(keyword in full_text for keyword in ['数据', '指标', '率', '完成率', '正确率', '效率', '效果', '频次'])
        
        # 基于梁宁理论：真需求需要同时具备问题/价值/场景中的至少两个
        value_scene_count = sum([has_problem_description, has_value_description, has_scene_description])
        
        # 如果只有功能描述，没有价值或问题说明，可能是伪需求
        if not has_value_description and not has_problem_description:
            false_score += 3
            false_reasons.append("缺乏价值或问题说明")
        
        # 如果同时具备问题、价值、场景，强烈倾向真需求
        if value_scene_count >= 2:
            true_score += 3
            true_reasons.append("具备问题/价值/场景描述")
        
        # 如果有数据指标，加分
        if has_metric_description:
            true_score += 1
            true_reasons.append("包含数据指标")
        
        # 判断逻辑
        # 如果真需求得分明显高于伪需求得分，且差值>=3，判断为真需求（+50分）
        # 如果伪需求得分明显高于真需求得分，且差值>=3，判断为伪需求（-50分）
        # 如果差值在-2到2之间，判断为真需求但不计修正（保守策略）
        # 否则，根据得分差值给予部分修正
        
        score_diff = true_score - false_score
        
        if score_diff >= 3:
            is_true = True
            reason = f"真需求特征明显（{', '.join(true_reasons)}），得分{true_score} vs {false_score}"
            correction = 50
        elif score_diff <= -3:
            is_true = False
            reason = f"伪需求特征明显（{', '.join(false_reasons)}），得分{true_score} vs {false_score}"
            correction = -50
        elif score_diff >= 1:
            is_true = True
            reason = f"真需求特征较明显（{', '.join(true_reasons)}），得分{true_score} vs {false_score}，保守判断为真需求，不计修正"
            correction = 0
        elif score_diff <= -1:
            is_true = True  # 保守策略：即使有伪需求特征，也判断为真需求，但给予负修正
            reason = f"存在伪需求特征（{', '.join(false_reasons)}），得分{true_score} vs {false_score}，保守判断为真需求，给予轻微负修正"
            correction = -20  # 轻微负修正
        else:
            # 得分接近，保守判断为真需求，但不计修正
            is_true = True
            reason = f"特征不明显（真需求得分{true_score}，伪需求得分{false_score}），保守判断为真需求，不计修正"
            correction = 0
        
        return is_true, reason, correction
    
    def process_requirements(self) -> Tuple[List[Dict], List[Dict]]:
        """
        处理需求清单，分离X类需求并计算得分
        将原始得分作为比例，按比例分配total_score
        
        Returns:
            (普通需求列表, X类需求列表)
        """
        normal_requirements = []
        x_class = []
        
        # 第一步：计算所有需求的原始得分（作为比例）
        for req in self.requirements:
            if self._is_x_class(req):
                x_class.append(req)
            else:
                raw_score = self._calculate_score(req)
                req['raw_score'] = raw_score  # 保存原始得分（绝对价值分）
                # 保存各组成部分用于报告展示
                req['strategic_base'] = req.get('strategic_base', 0)
                req['planning_factor'] = req.get('planning_factor', 1.0)
                req['urgency_factor'] = req.get('urgency_factor', 1.0)
                req['true_demand_correction'] = req.get('true_demand_correction', 0)
                # 保存真需求分析结果
                if 'true_demand_analysis' in req:
                    req['true_demand_reason'] = req['true_demand_analysis'].get('reason', '')
                else:
                    req['true_demand_reason'] = ''
                # 向后兼容字段
                req['A'] = req.get('strategic_base', 0)
                req['B'] = req.get('planning_factor', 1.0)
                req['C'] = req.get('urgency_factor', 1.0)
                
                # 标记是否为轻学需求
                req['is_qingxue'] = self._is_qingxue(req)
                
                normal_requirements.append(req)
        
        # 第二步：计算总最终价值分（raw_score已经是最终价值分，已应用业务加权）
        total_final_score = sum(req.get('raw_score', 0) for req in normal_requirements)
        
        # 第三步：按比例分配total_score
        if total_final_score > 0:
            for req in normal_requirements:
                final_score = req.get('raw_score', 0)  # 最终价值分（已应用业务加权）
                # 按比例分配：分配分数 = (最终价值分 / 总得分) × total_score
                allocated_score = (final_score / total_final_score) * self.total_score
                
                # 注意：业务加权已经在_calculate_score中应用，这里不再重复应用
                req['calculated_score'] = allocated_score
        else:
            # 如果总得分为0，所有需求分配0分
            for req in normal_requirements:
                req['calculated_score'] = 0
        
        # 按业务线分组并排序（轻学需求优先）
        normal_requirements.sort(key=lambda x: (
            x.get('business_line', ''),
            -x.get('is_qingxue', False),  # 轻学需求优先
            -x.get('calculated_score', 0)
        ))
        
        return normal_requirements, x_class
    
    def _get_category_score(self, req: Dict) -> int:
        """
        获取战略基分（用于报告展示）
        
        需求分类枚举值（新标准）：
        1. A类（考核落地）：100分
        2. B类（重点建设）：60分
        3. C类（常态/其他）：20分
        4. D类（非考核类+考核类落地结束）：10分
        5. E类（季度重点）：60分（映射到B类）
        """
        return req.get('strategic_base', 0)
    
    def _get_quarter_score(self, req: Dict) -> float:
        """获取规划系数（用于报告展示）"""
        return req.get('planning_factor', 1.0)
    
    def _get_status_score(self, req: Dict) -> float:
        """获取紧迫度系数（用于报告展示）"""
        return req.get('urgency_factor', 1.0)
    
    def calculate_quotas(self, normal_requirements: List[Dict]) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float]]:
        """
        计算各业务线的配额（实现动态回流机制）
        
        Args:
            normal_requirements: 普通需求列表（已包含 calculated_score）
            
        Returns:
            (各业务线的配额字典, 最终比例字典, 初始比例字典, 轻学配额字典（已废弃，返回空字典）)
        """
        # 初始比例（考研、四六级、专升本）
        initial_ratios = {
            '考研': 0.6,   # Kaoyan (including Qingxue)
            '四六级': 0.2, # CET-4/6 (previously Camp)
            '专升本': 0.2  # Zhanshengben (previously Professional Course)
        }
        
        # 业务线名称映射
        business_line_mapping = {
            '集训营': '四六级',
            '专业课': '专升本'
        }
        
        # 1. 计算各桶的初始配额
        initial_quotas = {k: self.total_score * v for k, v in initial_ratios.items()}
        
        # 2. 计算各桶的实际需求（总分）
        bucket_demands = {
            '考研': 0.0,
            '四六级': 0.0,
            '专升本': 0.0
        }
        
        for req in normal_requirements:
            bl = req.get('business_line', '').strip()
            score = req.get('calculated_score', 0)
            
            # 映射到三大桶
            if '考研' in bl or '轻学' in bl:
                bucket = '考研'
            else:
                bucket = business_line_mapping.get(bl, bl)
            
            if bucket in bucket_demands:
                bucket_demands[bucket] += score
            else:
                # 未知业务线，暂归入考研或者忽略（这里归入考研以防万一）
                bucket_demands['考研'] += score

        # 3. 计算回流（Flow Back）
        # 改进规则：
        # - 如果总需求 > 配额（即存在Backlog）：余下的零头不回流，保留为“启动积分”
        # - 如果总需求 <= 配额（即全部满足）：真正的剩余配额才回流给考研
        final_quotas = initial_quotas.copy()
        flow_back_amount = 0.0
        
        # 检查四六级
        if bucket_demands['四六级'] <= initial_quotas['四六级']:
            # 全部需求都能满足，剩余的钱回流
            surplus = initial_quotas['四六级'] - bucket_demands['四六级']
            final_quotas['四六级'] = bucket_demands['四六级']
            flow_back_amount += surplus
        else:
            # 需求爆了，全额保留配额，不回流（余下的钱留作下期启动）
            final_quotas['四六级'] = initial_quotas['四六级']
        
        # 检查专升本
        if bucket_demands['专升本'] <= initial_quotas['专升本']:
            surplus = initial_quotas['专升本'] - bucket_demands['专升本']
            final_quotas['专升本'] = bucket_demands['专升本']
            flow_back_amount += surplus
        else:
             # 需求爆了，全额保留配额
            final_quotas['专升本'] = initial_quotas['专升本']
            
        # 回流给考研
        final_quotas['考研'] += flow_back_amount
        
        # 4. 计算最终比例（仅用于报告展示）
        final_ratios = {k: v / self.total_score if self.total_score > 0 else 0 for k, v in final_quotas.items()}
        
        # 轻学不再单独预留配额
        qingxue_quotas = {}
        
        return final_quotas, final_ratios, initial_ratios, qingxue_quotas
    
    def allocate_resources(self, normal_requirements: List[Dict], quotas: Dict[str, float], qingxue_quotas: Dict[str, float] = None) -> List[Dict]:
        """
        分配资源，标记入选和待办
        轻学需求参与考研配额竞争，但得分已应用1.2倍权重
        
        Args:
            normal_requirements: 普通需求列表
            quotas: 各业务线配额
            qingxue_quotas: 轻学配额字典（已废弃，不再使用）
            
        Returns:
            标记了决策结果的需求列表
        """
        result = []
        
        # 按业务线分组（轻学归入考研，业务线名称映射）
        business_line_mapping = {
            '集训营': '四六级',
            '专业课': '专升本'
        }
        
        by_business_line = {}
        for req in normal_requirements:
            bl = req.get('business_line', '').strip()
            # 统一处理考研业务线（包括轻学）
            if '考研' in bl or '轻学' in bl:
                bl = '考研'
            else:
                # 映射旧业务线名称
                bl = business_line_mapping.get(bl, bl)
            if bl not in by_business_line:
                by_business_line[bl] = []
            by_business_line[bl].append(req)
        
        # 在各业务线内分配（按得分排序，轻学需求由于1.2倍权重会优先）
        for bl, reqs in by_business_line.items():
            quota = quotas.get(bl, 0)
            # 按得分降序排序
            reqs.sort(key=lambda x: -x.get('calculated_score', 0))
            cumulative_score = 0
            
            for req in reqs:
                score = req.get('calculated_score', 0)
                cumulative_score += score
                
                # 标记轻学需求
                if self._is_qingxue(req):
                    if cumulative_score <= quota:
                        req['decision'] = '✅ 入选（轻学）'
                    else:
                        req['decision'] = '仅启动'
                else:
                    if cumulative_score <= quota:
                        req['decision'] = '✅ 入选'
                    else:
                        req['decision'] = '仅启动'
                
                result.append(req)
        
        return result
    
    def generate_report(self, output_file: str = None) -> str:
        """
        生成Markdown格式的报告
        
        Args:
            output_file: 输出文件路径，如果为None则只返回字符串
            
        Returns:
            Markdown报告内容
        """
        normal_reqs, x_class_reqs = self.process_requirements()
        quotas, final_ratios, initial_ratios, qingxue_quotas = self.calculate_quotas(normal_reqs)
        allocated_reqs = self.allocate_resources(normal_reqs, quotas, qingxue_quotas)
        
        # 生成报告
        lines = []
        lines.append("# 需求优先级打分与资源分配报告")
        lines.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**可用总分池**: {self.total_score}分\n")
        
        # 1. 配额分配概览
        lines.append("## 1. 配额分配概览\n")
        lines.append("| **业务线** | **初始比例** | **是否触发回流** | **最终可用配额 (分)** |")
        lines.append("| ---------- | ------------ | ---------------- | --------------------- |")
        
        # 业务线名称映射（用于显示）
        business_line_display_mapping = {
            '集训营': '四六级',
            '专业课': '专升本'
        }
        
        for bl in ['考研', '四六级', '专升本']:
            initial_ratio = initial_ratios.get(bl, 0)
            final_ratio = final_ratios.get(bl, 0)
            quota = quotas.get(bl, 0)
            
            # 判断是否触发回流
            if initial_ratio > 0 and final_ratio == 0:
               回流说明 = "是（无需求，配额回流）"
            elif initial_ratio > final_ratio:
                回流说明 = "是（部分配额回流）"
            elif initial_ratio < final_ratio:
                回流说明 = "是（接收回流配额）"
            else:
                回流说明 = "否"
            
            lines.append(f"| {bl} | {initial_ratio*100:.0f}% | {回流说明} | {quota:.2f} |")
        
        # 轻学规则说明
        qingxue_reqs_count = len([r for r in normal_reqs if self._is_qingxue(r)])
        if qingxue_reqs_count > 0:
            lines.append("\n### 轻学规则说明：")
            lines.append("- **轻学需求**参与考研配额竞争，得分已应用**1.2倍权重**，优先排序")
            lines.append("")
        
        # 2. X类紧急通道
        lines.append("\n## 2. X类紧急通道 (不占分/优先处理)\n")
        if x_class_reqs:
            for req in x_class_reqs:
                name = req.get('name', '未知需求')
                business_line = req.get('business_line', '未知业务线')
                lines.append(f"- **{name}** - {business_line}业务线（系统故障/阻断性问题）")
        else:
            lines.append("- 无X类需求")
        
        # 3. 最终排期决策表
        lines.append("\n## 3. 最终排期决策表\n")
        lines.append("| **优先级** | **业务线** | **需求名称** | **战略基分** | **规划系数** | **紧迫度** | **真需求判断** | **FY26战略加分** | **业务加权** | **最终价值分** | **分配得分** | **决策结果** |")
        lines.append("| ---------- | ---------- | ------------ | ------------ | ------------ | ---------- | -------------- | --------------- | ------------ | -------------- | ------------ | --------------- |")
        
        # 按得分排序（全局排序）
        allocated_reqs.sort(key=lambda x: -x.get('calculated_score', 0))
        
        for idx, req in enumerate(allocated_reqs, 1):
            name = req.get('name', '未知需求')
            bl = req.get('business_line', '未知业务线')
            strategic_base = req.get('strategic_base', 0)
            planning_factor = req.get('planning_factor', 1.0)
            urgency = req.get('urgency', 'P2').upper()
            urgency_factor = req.get('urgency_factor', 1.0)
            true_demand_correction = req.get('true_demand_correction', 0)
            true_demand_reason = req.get('true_demand_reason', '')
            raw_score = req.get('raw_score', 0)
            allocated_score = req.get('calculated_score', 0)
            decision = req.get('decision', '')
            
            # 格式化真需求判断显示
            if true_demand_correction > 0:
                judgment_display = f"真(+{true_demand_correction})"
            elif true_demand_correction < 0:
                judgment_display = f"伪({true_demand_correction})"
            else:
                judgment_display = "真(0)"
            
            # 如果有关键词分析结果，添加提示
            if true_demand_reason and '特征' in true_demand_reason:
                judgment_display += " [自动分析]"
            
            # FY26战略加分和业务加权显示
            fy26_bonus = req.get('fy26_bonus', 0)
            fy26_matched_oks = req.get('fy26_matched_oks', [])
            business_boost = req.get('business_boost', 1.0)
            final_score = req.get('raw_score', 0)  # raw_score已经是最终价值分（已应用业务加权）
            
            if fy26_bonus > 0:
                fy26_display = f"+{fy26_bonus}"
                if fy26_matched_oks:
                    fy26_display += f" ({', '.join(fy26_matched_oks)})"
            else:
                fy26_display = "0"
            boost_display = f"{business_boost:.1f}x" if business_boost != 1.0 else "1.0x"
            
            lines.append(f"| {idx} | {bl} | {name} | {strategic_base} | {planning_factor:.1f} | {urgency}({urgency_factor:.1f}) | {judgment_display} | {fy26_display} | {boost_display} | **{final_score:.1f}** | {allocated_score:.2f} | {decision} |")
        
        # 添加真需求分析详情（如果有自动分析的需求）
        auto_analyzed_reqs = [r for r in allocated_reqs if r.get('true_demand_reason') and '特征' in r.get('true_demand_reason', '')]
        if auto_analyzed_reqs:
            lines.append("\n### 真需求自动分析详情：")
            for req in auto_analyzed_reqs[:10]:  # 只显示前10个
                name = req.get('name', '未知需求')
                reason = req.get('true_demand_reason', '')
                lines.append(f"- **{name}**: {reason}")
        
        # 4. 分析总结
        lines.append("\n## 4. 分析总结\n")
        
        # 统计入选和待办数量
        selected = [r for r in allocated_reqs if '✅' in r.get('decision', '')]
        backlog = [r for r in allocated_reqs if '⏸️' in r.get('decision', '')]
        
        lines.append(f"- **总需求数**: {len(self.requirements)}个（其中X类需求{len(x_class_reqs)}个）")
        lines.append(f"- **入选需求数**: {len(selected)}个")
        lines.append(f"- **待办需求数**: {len(backlog)}个")
        
        # 各业务线资源使用情况
        lines.append("\n### 各业务线资源使用情况：")
        
        # 业务线名称映射（用于统计）
        business_line_mapping = {
            '集训营': '四六级',
            '专业课': '专升本'
        }
        
        for bl in ['考研', '四六级', '专升本']:
            # 考研业务线包含轻学需求
            if bl == '考研':
                bl_reqs = [r for r in allocated_reqs if (r.get('business_line') == bl or r.get('business_line') == '轻学')]
            else:
                # 需要映射旧业务线名称
                bl_reqs = []
                for r in allocated_reqs:
                    req_bl = r.get('business_line', '').strip()
                    normalized_bl = business_line_mapping.get(req_bl, req_bl)
                    if normalized_bl == bl:
                        bl_reqs.append(r)
            
            bl_selected = [r for r in bl_reqs if '✅' in r.get('decision', '')]
            bl_used_score = sum(r.get('calculated_score', 0) for r in bl_selected)
            quota = quotas.get(bl, 0)
            
            # 统计轻学需求
            qingxue_in_bl = [r for r in bl_selected if self._is_qingxue(r)]
            qingxue_score = sum(r.get('calculated_score', 0) for r in qingxue_in_bl)
            
            if quota > 0:
                utilization = (bl_used_score / quota * 100) if quota > 0 else 0
                if qingxue_in_bl:
                    lines.append(f"- **{bl}**: 使用 {bl_used_score:.2f}/{quota:.2f}分 ({utilization:.1f}%)，入选{len(bl_selected)}个需求（其中轻学{len(qingxue_in_bl)}个，得分{qingxue_score:.2f}分）")
                else:
                    lines.append(f"- **{bl}**: 使用 {bl_used_score:.2f}/{quota:.2f}分 ({utilization:.1f}%)，入选{len(bl_selected)}个需求")
            else:
                lines.append(f"- **{bl}**: 无配额分配")
        
        # 高优待办需求建议
        if backlog:
            lines.append("\n### 高优待办需求建议：")
            high_priority_backlog = sorted(backlog, key=lambda x: -x.get('calculated_score', 0))[:3]
            for req in high_priority_backlog:
                name = req.get('name', '未知需求')
                score = req.get('calculated_score', 0)
                bl = req.get('business_line', '未知业务线')
                lines.append(f"- **{name}** ({bl}) - 得分{score}分，建议优先考虑")
        
        report_content = '\n'.join(lines)
        
        # 写入文件
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"报告已保存至: {output_path}")
        
        return report_content
    
    def generate_html_report(self, output_file: str = None) -> str:
        """
        生成HTML格式的报告（网页展示）
        
        Args:
            output_file: 输出文件路径，如果为None则只返回字符串
            
        Returns:
            HTML报告内容
        """
        normal_reqs, x_class_reqs = self.process_requirements()
        quotas, final_ratios, initial_ratios, qingxue_quotas = self.calculate_quotas(normal_reqs)
        allocated_reqs = self.allocate_resources(normal_reqs, quotas, qingxue_quotas)
        
        # 统计信息
        selected = [r for r in allocated_reqs if '✅' in r.get('decision', '')]
        backlog = [r for r in allocated_reqs if '⏸️' in r.get('decision', '')]
        
        # 按得分排序
        allocated_reqs.sort(key=lambda x: -x.get('calculated_score', 0))
        
        # 生成HTML
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>需求优先级打分与资源分配报告</title>
    <style>
        :root {{
            /* Ant Design Spec: Geek Blue #1890ff */
            --primary-color: #1890ff; 
            --success-color: #52c41a;
            --warning-color: #faad14;
            --error-color: #f5222d;
            --text-color: rgba(0, 0, 0, 0.85);
            --text-secondary: rgba(0, 0, 0, 0.45);
            --border-color: #f0f0f0;
            --bg-color: #f0f2f5;
            
            /* Design Spec: Certainty (4px-6px radius) */
            --card-radius: 6px; 
            --border-radius-base: 4px;
            
            /* Design Spec: Natural & Subtle Shadows */
            --box-shadow-base: 0 1px 2px -2px rgba(0, 0, 0, 0.16), 0 3px 6px 0 rgba(0, 0, 0, 0.12), 0 5px 12px 4px rgba(0, 0, 0, 0.09);
            --box-shadow-card: 0 1px 2px 0 rgba(0,0,0,0.03);
            
            /* Design Spec: 8px Grid System */
            --space-xs: 8px;
            --space-sm: 16px;
            --space-md: 24px;
            --space-lg: 32px;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.5715;
            padding: var(--space-md); /* 24px */
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            background: #fff;
            padding: var(--space-md); /* 24px */
            border-radius: var(--card-radius); /* 6px */
            margin-bottom: var(--space-md); /* 24px */
            box-shadow: var(--box-shadow-card);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .header h1 {{
            font-size: 20px;
            font-weight: 600;
            margin: 0;
            color: rgba(0,0,0,0.85);
        }}
        
        .header .meta {{
            font-size: 14px;
            color: var(--text-secondary);
        }}
        
        /* 卡片样式 */
        .ant-card {{
            background: #fff;
            border-radius: var(--card-radius); /* 6px */
            box-shadow: var(--box-shadow-card);
            margin-bottom: var(--space-md); /* 24px */
        }}
        
        .ant-card-head {{
            min-height: 48px;
            margin-bottom: -1px;
            padding: 0 var(--space-md); /* 24px */
            color: rgba(0, 0, 0, 0.85);
            font-weight: 500;
            font-size: 16px;
            background: transparent;
            border-bottom: 1px solid #f0f0f0;
            display: flex;
            align-items: center;
        }}
        
        .ant-card-body {{
            padding: var(--space-md); /* 24px */
        }}
        
        /* 统计卡片 */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: var(--space-md); /* 24px */
            margin-bottom: var(--space-md); /* 24px */
        }}
        
        .stat-card {{
            background: #fff;
            padding: var(--space-md); /* 24px */
            border-radius: var(--card-radius); /* 6px */
            box-shadow: var(--box-shadow-card);
            border: 1px solid #f0f0f0;
            display: flex;
            flex-direction: column;
            transition: all 0.3s;
        }}
        
        .stat-label {{
            font-size: 14px;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }}
        
        .stat-value {{
            font-size: 30px;
            color: rgba(0,0,0,0.85);
            font-weight: 500;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        
        /* 表格样式 */
        .ant-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .ant-table th {{
            background: #fafafa;
            color: rgba(0,0,0,0.85);
            font-weight: 500;
            text-align: left;
            padding: 16px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
            white-space: nowrap;
        }}
        
        .ant-table td {{
            padding: 16px;
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.3s;
            font-size: 14px;
        }}
        
        .ant-table tbody tr:hover td {{
            background: #fafafa;
        }}
        
        /* 标签样式 */
        .ant-tag {{
            display: inline-block;
            height: auto;
            margin-right: 8px;
            padding: 2px 7px;
            font-size: 12px;
            line-height: 20px;
            white-space: nowrap;
            background: #fafafa;
            border: 1px solid #d9d9d9;
            border-radius: 2px;
            cursor: default;
            opacity: 1;
            transition: all 0.3s;
            color: rgba(0,0,0,0.65);
        }}
        
        .help-icon {{
            position: relative;
            display: inline-flex;
            justify-content: center;
            align-items: center;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background-color: rgba(0,0,0,0.25);
            color: #fff;
            font-size: 10px;
            margin-left: 4px;
            cursor: pointer;
            vertical-align: middle;
        }}
        .help-icon:hover {{ background-color: rgba(0,0,0,0.45); }}
        .help-icon .tooltip-content {{
            visibility: hidden;
            width: 250px;
            background-color: rgba(0, 0, 0, 0.85);
            color: #fff;
            text-align: left;
            border-radius: 4px;
            padding: 8px 12px;
            position: absolute;
            z-index: 100;
            bottom: 125%; /* Position above */
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.2s;
            font-weight: normal;
            font-size: 12px;
            line-height: 1.5;
            white-space: pre-wrap; /* Interpret newlines */
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .help-icon .tooltip-content::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: rgba(0, 0, 0, 0.85) transparent transparent transparent;
        }}
        .help-icon:hover .tooltip-content {{
            visibility: visible;
            opacity: 1;
        }}
        
        .ant-tag-blue {{ color: #1890ff; background: #e6f7ff; border-color: #91d5ff; }}
        .ant-tag-green {{ color: #52c41a; background: #f6ffed; border-color: #b7eb8f; }}
        .ant-tag-gold {{ color: #faad14; background: #fffbe6; border-color: #ffe58f; }}
        .ant-tag-red {{ color: #f5222d; background: #fff1f0; border-color: #ffa39e; }}
        .ant-tag-purple {{ color: #722ed1; background: #f9f0ff; border-color: #d3adf7; }}
        .ant-tag-cyan {{ color: #13c2c2; background: #e6fffb; border-color: #87e8de; }}
        .ant-tag-orange {{ color: #fa8c16; background: #fff7e6; border-color: #ffd591; }}
        
        /* 进度条 */
        .ant-progress {{
            display: inline-block;
            width: 100%;
            font-size: 14px;
            line-height: 1;
        }}
        
        .ant-progress-outer {{
            display: inline-block;
            width: 100%;
            margin-right: 0;
            padding-right: 0;
            vertical-align: middle;
        }}
        
        .ant-progress-inner {{
            position: relative;
            display: inline-block;
            width: 100%;
            background-color: #f5f5f5;
            border-radius: 100px;
            vertical-align: middle;
            overflow: hidden;
        }}
        
        .ant-progress-bg {{
            position: relative;
            background-color: var(--primary-color);
            border-radius: 100px;
            transition: all 0.4s cubic-bezier(0.08, 0.82, 0.17, 1) 0s;
            height: 8px;
        }}
        
        /* 业务线颜色 */
        .business-line-text {{
            font-weight: 500;
            white-space: nowrap;
        }}
        
        .decision-check {{ color: var(--success-color); font-size: 16px; font-weight: bold; }}
        .decision-start {{ color: #1890ff; font-size: 15px; font-weight: normal; }}
        
        .score-val {{ font-family: 'Monaco', 'Menlo', 'Consolas', monospace; font-weight: 600; color: #000; }}
        
        .alert-info {{
            padding: 8px 15px;
            margin-bottom: 16px;
            border: 1px solid #91d5ff;
            background-color: #e6f7ff;
            border-radius: 2px;
            color: rgba(0,0,0,0.65);
            font-size: 13px;
            display: flex;
            align-items: center;
        }}
        
        .alert-error {{
            padding: 8px 15px;
            margin-bottom: 16px;
            border: 1px solid #ffccc7;
            background-color: #fff2f0;
            border-radius: 2px;
            color: rgba(0,0,0,0.65);
            font-size: 13px;
        }}

        .footer {{
            text-align: center;
            color: var(--text-secondary);
            font-size: 12px;
            margin-top: 40px;
            padding-bottom: 24px;
        }}

    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>需求优先级打分与资源分配报告</h1>
            <div class="meta">
                <span>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                <span style="margin: 0 8px; color: #d9d9d9;">|</span>
                <span>可用总分池: <span style="color:var(--primary-color);font-weight:600;">{self.total_score}</span> 分</span>
            </div>
        </div>
        
        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">总需求数</div>
                <div class="stat-value">{len(self.requirements)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">入选需求</div>
                <div class="stat-value" style="color: var(--success-color);">{len(selected)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">待办需求</div>
                <div class="stat-value" style="color: var(--warning-color);">{len(backlog)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">X类紧急需求</div>
                <div class="stat-value" style="color: var(--error-color);">{len(x_class_reqs)}</div>
            </div>
        </div>
        
        <div class="content">

            <!-- 1. 配额分配概览 -->
            <div class="ant-card">
                <div class="ant-card-head">
                    <span>1. 配额分配概览</span>
                </div>
                <div class="ant-card-body">
                    <table class="ant-table">
                        <thead>
                            <tr>
                                <th style="width: 200px;">业务线</th>
                                <th>初始比例</th>
                                <th>是否触发回流</th>
                                <th>最终可用配额 (分)</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for bl in ['考研', '四六级', '专升本']:
            initial_ratio = initial_ratios.get(bl, 0)
            final_ratio = final_ratios.get(bl, 0)
            quota = quotas.get(bl, 0)
            
            if initial_ratio > 0 and final_ratio == 0:
                tag = '<span class="ant-tag ant-tag-gold">是 (无需求回流)</span>'
            elif initial_ratio > final_ratio:
                tag = '<span class="ant-tag ant-tag-gold">是 (部分回流)</span>'
            elif initial_ratio < final_ratio:
                tag = '<span class="ant-tag ant-tag-blue">是 (接收回流)</span>'
            else:
                tag = '<span class="ant-tag">否</span>'
            
            html_content += f"""
                            <tr>
                                <td><span class="business-line-text">{bl}</span></td>
                                <td>{initial_ratio*100:.0f}%</td>
                                <td>{tag}</td>
                                <td><span style="font-weight:600; font-size:16px;">{quota:.2f}</span></td>
                            </tr>"""
        
        html_content += """
                        </tbody>
                    </table>
                    
                    """
        
        # 轻学规则说明
        qingxue_reqs_count = len([r for r in normal_reqs if self._is_qingxue(r)])
        if qingxue_reqs_count > 0:
            html_content += """
                    <div style="margin-top: 16px;"></div>
                    <div class="alert-info">
                        <span style="margin-right: 8px; font-size: 16px;">📘</span>
                        <span><strong>轻学规则：</strong> 轻学需求参与考研配额竞争，得分已应用 <strong>1.2倍权重</strong> 优先排序。</span>
                    </div>"""
            
        html_content += """
                </div>
            </div>
        
            <!-- 2. X类紧急通道 -->
            <div class="ant-card">
                <div class="ant-card-head">
                    <span>2. X类紧急通道 (不占分/优先处理)</span>
                </div>
                <div class="ant-card-body">"""
        
        if x_class_reqs:
            html_content += '<div class="alert-error" style="border-left: 4px solid #f5222d;">'
            for req in x_class_reqs:
                name = req.get('name', '未知需求')
                business_line = req.get('business_line', '未知业务线')
                html_content += f'<div style="margin-bottom:4px;">🚨 <strong>{name}</strong> <span class="ant-tag ant-tag-red" style="margin-left:8px;">{business_line}</span> - 系统故障/阻断性问题</div>'
            html_content += '</div>'
        else:
            html_content += '<div style="text-align:center; color:rgba(0,0,0,0.25); padding: 20px 0;">暂无 X 类紧急需求</div>'
        
        html_content += """
                </div>
            </div>
            
            <!-- 3. 最终排期决策表 -->
            <div class="ant-card">
                <div class="ant-card-head">
                    <span>3. 最终排期决策表</span>
                </div>
                <div class="ant-card-body" style="padding: 0;">
                    <table class="ant-table">
                        <thead>
                            <tr>
                                <th>排名</th>
                                <th>业务线</th>
                                <th>需求名称</th>
                                <th title="来源于需求分类：A类(100), B类(60), C类(20), D类(10)">需求分类得分</th>
                                <th>规划</th>
                                <th>紧迫度</th>
                                <th>梁宁判定结果</th>
                                <th>FY26战略</th>

                                <th>最终分</th>
                                <th>bidding分</th>
                                <th>决策</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for idx, req in enumerate(allocated_reqs, 1):
            name = req.get('name', '未知需求')
            bl = req.get('business_line', '未知业务线')
            category = req.get('category', '')
            strategic_base = req.get('strategic_base', 0)
            planning_factor = req.get('planning_factor', 1.0)
            urgency = req.get('urgency', 'P2').upper()
            urgency_factor = req.get('urgency_factor', 1.0)
            true_demand_correction = req.get('true_demand_correction', 0)
            true_demand_reason = req.get('true_demand_reason', '')
            fy26_bonus = req.get('fy26_bonus', 0)
            fy26_matched_oks = req.get('fy26_matched_oks', [])
            business_boost = req.get('business_boost', 1.0)
            final_score = req.get('raw_score', 0)
            allocated_score = req.get('calculated_score', 0)
            decision = req.get('decision', '')
            
            # 梁宁真伪判定标签
            if '核心真需求' in true_demand_reason:
                judgment_tag = f'<span class="ant-tag ant-tag-blue" style="border-color:#91d5ff;" title="{true_demand_reason}">💎 核心真(+50)</span>'
            elif '魅力型需求' in true_demand_reason:
                judgment_tag = f'<span class="ant-tag ant-tag-purple" title="{true_demand_reason}">✨ 魅力型(+30)</span>'
            elif '基础型需求' in true_demand_reason:
                judgment_tag = f'<span class="ant-tag ant-tag-cyan" title="{true_demand_reason}">🔧 基础型(+40)</span>'
            elif '伪需求' in true_demand_reason:
                judgment_tag = f'<span class="ant-tag ant-tag-red" title="{true_demand_reason}">❌ 伪需求(-50)</span>'
            elif true_demand_correction > 0:
                judgment_tag = f'<span class="ant-tag ant-tag-green" title="{true_demand_reason}">真(+{true_demand_correction})</span>'
            elif true_demand_correction < 0:
                judgment_tag = f'<span class="ant-tag ant-tag-red" title="{true_demand_reason}">伪({true_demand_correction})</span>'
            else:
                judgment_tag = '<span class="ant-tag">真(0)</span>'
            
            # FY26标签
            if fy26_bonus > 0:
                okr_tips = ', '.join(fy26_matched_oks) if fy26_matched_oks else ''
                fy26_cell = f'<span class="ant-tag ant-tag-purple" title="{okr_tips}">+{fy26_bonus}</span>'
            else:
                fy26_cell = '<span style="color:#d9d9d9;">-</span>'
                
            boost_display = f"{business_boost:.1f}x"
            if business_boost > 1.0:
                boost_display = f'<span style="color:var(--primary-color); font-weight:bold;">{boost_display}</span>'
            
            # 决策结果
            if '✅' in decision:
                decision_html = '<span class="decision-check">✓ 通过</span>'
                row_bg = ''
            elif decision == '仅启动':
                decision_html = '<span class="decision-start">仅启动</span>'
                row_bg = 'background-color: #fafafa;'
            else:
                decision_html = decision
                row_bg = ''
                
            # 业务线颜色映射
            bl_color = 'blue'
            if bl == '四六级': bl_color = 'cyan'
            if bl == '专升本': bl_color = 'green'
            if bl == '轻学': bl_color = 'purple'
            
            bl_tag = f'<span class="ant-tag ant-tag-{bl_color}">{bl}</span>'
            
            html_content += f"""
                            <tr style="{row_bg}">
                                <td style="color:#8c8c8c;">{idx}</td>
                                <td>{bl_tag}</td>
                                <td style="font-weight:500;">{name}</td>
                                <td title="{category}">{strategic_base}</td>
                                <td>{planning_factor:.1f}</td>
                                <td>{urgency} <span style="font-size:12px;color:#8c8c8c;">({urgency_factor:.1f})</span></td>
                                <td>{judgment_tag}</td>
                                <td>{fy26_cell}</td>

                                <td>{final_score:.1f}</td>
                                <td><span class="score-val" style="color:#1890ff; font-size:15px;">{allocated_score:.2f}</span></td>
                                <td>{decision_html}</td>
                            </tr>"""
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- 4. 分析总结 -->
             <div class="ant-card">
                <div class="ant-card-head">
                    <span>4. 分析总结</span>
                </div>
                <div class="ant-card-body">
                    <h4 style="margin-bottom: 16px; color: rgba(0,0,0,0.85);">各业务线资源使用情况</h4>"""
        
        # 各业务线资源使用情况（业务线名称映射）
        for bl in ['考研', '四六级', '专升本']:
            # 考研业务线包含轻学需求
            if bl == '考研':
                bl_reqs = [r for r in allocated_reqs if (r.get('business_line') == bl or r.get('business_line') == '轻学')]
            else:
                bl_reqs = [r for r in allocated_reqs if r.get('business_line') == bl]
            
            bl_selected = [r for r in bl_reqs if '✅' in r.get('decision', '')]
            bl_used_score = sum(r.get('calculated_score', 0) for r in bl_selected)
            quota = quotas.get(bl, 0)
            
            # 统计轻学需求
            qingxue_in_bl = [r for r in bl_selected if self._is_qingxue(r)]
            qingxue_score = sum(r.get('calculated_score', 0) for r in qingxue_in_bl)
            
            if quota > 0:
                utilization = (bl_used_score / quota * 100) if quota > 0 else 0
                
                # 进度条颜色
                progress_color = "var(--primary-color)"
                if utilization > 100: progress_color = "var(--error-color)"
                elif utilization > 90: progress_color = "var(--warning-color)"
                
                qingxue_text = f"（含轻学 {len(qingxue_in_bl)} 个，共 {qingxue_score:.2f} 分）" if qingxue_in_bl else ""
                
                html_content += f"""
                    <div style="margin-bottom: 24px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span><strong>{bl}</strong> {qingxue_text}</span>
                            <span>{bl_used_score:.2f} / {quota:.2f} ({utilization:.1f}%)</span>
                        </div>
                        <div class="ant-progress">
                            <div class="ant-progress-outer">
                                <div class="ant-progress-inner">
                                    <div class="ant-progress-bg" style="width: {min(utilization, 100)}%; background-color: {progress_color};"></div>
                                </div>
                            </div>
                        </div>
                    </div>"""
            else:
                html_content += f"""
                    <div style="margin-bottom: 24px; color: rgba(0,0,0,0.45);">
                        <strong>{bl}</strong>: 无配额分配
                    </div>"""
        
        # 高优待办需求建议
        if backlog:
            html_content += """
                <div style="margin-top: 32px; padding-top: 24px; border-top: 1px dashed #f0f0f0;">
                    <h4 style="margin-bottom: 16px; color: rgba(0,0,0,0.85);">✨ 高优待办需求建议</h4>
                    <ul style="padding-left: 20px; color: rgba(0,0,0,0.65);">"""
            high_priority_backlog = sorted(backlog, key=lambda x: -x.get('calculated_score', 0))[:3]
            for req in high_priority_backlog:
                name = req.get('name', '未知需求')
                score = req.get('calculated_score', 0)
                bl = req.get('business_line', '未知业务线')
                html_content += f'<li style="margin-bottom: 8px;"><strong>{name}</strong> <span class="ant-tag" style="margin: 0 4px;">{bl}</span> - 得分 <span style="color:#1890ff; font-weight:600;">{score:.2f}</span>，建议下个周期优先考虑</li>'
            html_content += '</ul></div>'
        
        html_content += """
                </div>
            </div>
            
        </div>
        
        <div class="footer">
            Generated by Requirement Scorer System v2.0 | Ant Design Edition
        </div>
    </div>
</body>
</html>"""
        

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML报告已保存至: {output_path}")
        
        return html_content


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='需求优先级打分与资源分配系统')
    parser.add_argument('--input', '-i', type=str, default='requirements_template_new_v2.csv', help='输入文件路径（CSV或JSON），默认: requirements_template_new_v2.csv')
    parser.add_argument('--total-score', '-t', type=float, required=True, help='可用总分池')
    parser.add_argument('--output', '-o', type=str, default='output/report.md', help='输出文件路径（默认: output/report.md）')
    parser.add_argument('--format', '-f', type=str, choices=['csv', 'json', 'auto'], default='auto', help='输入文件格式（默认: auto自动检测）')
    parser.add_argument('--html', action='store_true', help='生成HTML格式报告（网页展示）')
    
    args = parser.parse_args()
    
    # 创建打分器
    scorer = RequirementScorer(args.total_score)
    
    # 检测文件格式
    input_path = Path(args.input)
    if args.format == 'auto':
        if input_path.suffix.lower() == '.csv':
            file_format = 'csv'
        elif input_path.suffix.lower() == '.json':
            file_format = 'json'
        else:
            raise ValueError(f"无法自动检测文件格式，请使用 --format 参数指定")
    else:
        file_format = args.format
    
    # 加载数据
    print(f"正在从 {args.input} 加载数据（格式: {file_format}）...")
    if file_format == 'csv':
        scorer.load_from_csv(args.input)
    else:
        scorer.load_from_json(args.input)
    
    print(f"已加载 {len(scorer.requirements)} 个需求")
    
    # 生成报告
    print("正在生成报告...")
    if args.html:
        # 如果输出文件是.md，自动改为.html
        output_path = Path(args.output)
        if output_path.suffix == '.md':
            html_output = output_path.with_suffix('.html')
        else:
            html_output = args.output
        scorer.generate_html_report(html_output)
        print(f"HTML报告已生成: {html_output}")
        print(f"请在浏览器中打开查看: file://{Path(html_output).absolute()}")
    else:
        scorer.generate_report(args.output)
    print("完成！")


if __name__ == '__main__':
    main()
