
import unittest
from requirement_scorer import RequirementScorer

class TestRequirementScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = RequirementScorer(total_score=1000)

    def test_fy26_bonus_o1(self):
        # O1 KR1: 考研 转工单
        req = {
            'name': 'Test O1 KR1',
            'business_line': '考研',
            'core_delivery': '未报名学员转工单率提升',
            'benefit': '',
            'related_targets': '',
            'current_data': ''
        }
        bonus, matched = self.scorer._calculate_fy26_bonus(req)
        self.assertEqual(bonus, 20)
        self.assertIn('O1-KR1', matched)

        # O1 KR3: 专升本 择校小程序
        req = {
            'name': 'Test O1 KR3',
            'business_line': '专升本',
            'core_delivery': '择校小程序升级收资能力',
            'benefit': '',
            'related_targets': '',
            'current_data': ''
        }
        bonus, matched = self.scorer._calculate_fy26_bonus(req)
        self.assertEqual(bonus, 20)
        self.assertIn('O1-KR3', matched)

    def test_fy26_bonus_o3(self):
        # O3 KR2: 四六级 练测模块
        req = {
            'name': 'Test O3 KR2',
            'business_line': '四六级',
            'core_delivery': '练测与模考模块功能迭代',
            'benefit': '',
            'related_targets': '',
            'current_data': ''
        }
        bonus, matched = self.scorer._calculate_fy26_bonus(req)
        self.assertEqual(bonus, 15)
        self.assertIn('O3-KR2', matched)

    def test_fy26_bonus_qingxue_real_case(self):
        # Real case from CSV which failed to match
        req = {
            'name': '图片任务生成二维码功能',
            'business_line': '轻学',
            'core_delivery': '用户在使用【图片任务】功能时，可在小程序前台随时选择是否为图片任务的图片添加个人微信或企微二维码',
            'benefit': '',
            'related_targets': '',
            'current_data': ''
        }
        bonus, matched = self.scorer._calculate_fy26_bonus(req)
        # We expect this to match O1-KR5 (+20 points) potentially, but currently it fails.
        # Let's see if it matches.
        self.assertIn('O1-KR5', matched)
        self.assertEqual(bonus, 20)

    def test_flow_back_logic(self):
        # Setup specific requirements to test flow back: 
        # Camp (四六级) has low demand, Kaoyan has high demand.
        # Initial Quotas: Kaoyan 600, CET 200, ZSB 200
        
        reqs = [
            {'name': 'K1', 'business_line': '考研', 'calculated_score': 800},
            {'name': 'C1', 'business_line': '四六级', 'calculated_score': 50}, # Low demand
            {'name': 'Z1', 'business_line': '专升本', 'calculated_score': 200} # Full demand
        ]
        
        quotas, _, _, _ = self.scorer.calculate_quotas(reqs)
        
        # Expected:
        # CET quota reduces to 50. Surplus 150 goes to Kaoyan.
        # ZSB quota stays 200.
        # Kaoyan quota = 600 + 150 = 750.
        
        self.assertEqual(quotas['四六级'], 50.0)
        self.assertEqual(quotas['专升本'], 200.0)
        self.assertEqual(quotas['考研'], 750.0)

if __name__ == '__main__':
    unittest.main()
