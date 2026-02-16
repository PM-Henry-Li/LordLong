#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索 API 使用示例

演示如何使用搜索 API 接口进行各种查询操作
"""

import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class SearchAPIClient:
    """搜索 API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        初始化客户端
        
        Args:
            base_url: API 基础 URL
        """
        self.base_url = base_url
        self.search_url = f"{base_url}/api/search"
    
    def search(
        self,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """
        执行搜索
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            start_time: 开始时间（ISO 8601 格式）
            end_time: 结束时间（ISO 8601 格式）
            sort_by: 排序字段
            sort_order: 排序顺序（asc/desc）
            
        Returns:
            搜索结果字典
        """
        params = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        
        if keyword:
            params["keyword"] = keyword
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        
        try:
            response = requests.get(self.search_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": {"message": f"请求失败: {str(e)}"}
            }
    
    def search_by_keyword(self, keyword: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        按关键词搜索
        
        Args:
            keyword: 搜索关键词
            page: 页码
            
        Returns:
            搜索结果列表
        """
        result = self.search(keyword=keyword, page=page)
        if result.get("success"):
            return result["data"]["items"]
        else:
            print(f"搜索失败: {result.get('error', {}).get('message')}")
            return []
    
    def search_by_time_range(
        self,
        start_time: str,
        end_time: str,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        按时间范围搜索
        
        Args:
            start_time: 开始时间（ISO 8601 格式）
            end_time: 结束时间（ISO 8601 格式）
            page: 页码
            
        Returns:
            搜索结果列表
        """
        result = self.search(start_time=start_time, end_time=end_time, page=page)
        if result.get("success"):
            return result["data"]["items"]
        else:
            print(f"搜索失败: {result.get('error', {}).get('message')}")
            return []
    
    def search_recent(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        搜索最近几天的内容
        
        Args:
            days: 天数
            
        Returns:
            搜索结果列表
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        return self.search_by_time_range(
            start_time.isoformat(timespec='seconds'),
            end_time.isoformat(timespec='seconds')
        )
    
    def get_all_pages(
        self,
        keyword: Optional[str] = None,
        page_size: int = 50,
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取所有页面的结果
        
        Args:
            keyword: 搜索关键词
            page_size: 每页数量
            max_pages: 最大页数
            
        Returns:
            所有结果列表
        """
        all_items = []
        page = 1
        
        while page <= max_pages:
            result = self.search(keyword=keyword, page=page, page_size=page_size)
            
            if not result.get("success"):
                print(f"搜索失败: {result.get('error', {}).get('message')}")
                break
            
            items = result["data"]["items"]
            if not items:
                break
            
            all_items.extend(items)
            
            # 检查是否还有更多页
            total = result["data"]["total"]
            if len(all_items) >= total:
                break
            
            page += 1
        
        return all_items


def example_basic_search():
    """示例：基本搜索"""
    print("=" * 60)
    print("示例 1: 基本搜索")
    print("=" * 60)
    
    client = SearchAPIClient()
    result = client.search(keyword="老北京")
    
    if result.get("success"):
        print(f"✅ 搜索成功")
        print(f"总结果数: {result['data']['total']}")
        print(f"当前页: {result['data']['page']}")
        print(f"每页数量: {result['data']['page_size']}")
        print(f"查询参数: {result['query']}")
    else:
        print(f"❌ 搜索失败: {result.get('error', {}).get('message')}")
    
    print()


def example_pagination():
    """示例：分页搜索"""
    print("=" * 60)
    print("示例 2: 分页搜索")
    print("=" * 60)
    
    client = SearchAPIClient()
    
    # 第一页
    result = client.search(keyword="老北京", page=1, page_size=20)
    if result.get("success"):
        print(f"✅ 第 1 页: {len(result['data']['items'])} 条结果")
    
    # 第二页
    result = client.search(keyword="老北京", page=2, page_size=20)
    if result.get("success"):
        print(f"✅ 第 2 页: {len(result['data']['items'])} 条结果")
    
    print()


def example_time_range():
    """示例：时间范围搜索"""
    print("=" * 60)
    print("示例 3: 时间范围搜索")
    print("=" * 60)
    
    client = SearchAPIClient()
    
    # 搜索最近 7 天的内容
    items = client.search_recent(days=7)
    print(f"✅ 最近 7 天: {len(items)} 条结果")
    
    # 搜索指定时间范围
    items = client.search_by_time_range(
        start_time="2026-02-01T00:00:00",
        end_time="2026-02-13T23:59:59"
    )
    print(f"✅ 2月1日-2月13日: {len(items)} 条结果")
    
    print()


def example_sorting():
    """示例：排序搜索"""
    print("=" * 60)
    print("示例 4: 排序搜索")
    print("=" * 60)
    
    client = SearchAPIClient()
    
    # 按创建时间降序
    result = client.search(sort_by="created_at", sort_order="desc")
    if result.get("success"):
        print(f"✅ 按创建时间降序: {result['query']['sort_order']}")
    
    # 按标题升序
    result = client.search(sort_by="title", sort_order="asc")
    if result.get("success"):
        print(f"✅ 按标题升序: {result['query']['sort_order']}")
    
    print()


def example_error_handling():
    """示例：错误处理"""
    print("=" * 60)
    print("示例 5: 错误处理")
    print("=" * 60)
    
    client = SearchAPIClient()
    
    # 无效的页码
    result = client.search(page=0)
    if not result.get("success"):
        error = result.get("error", {})
        print(f"❌ 无效页码错误:")
        print(f"   错误码: {error.get('code')}")
        print(f"   错误消息: {error.get('message')}")
        if error.get('errors'):
            for err in error['errors']:
                print(f"   字段: {err.get('field')}")
                print(f"   详情: {err.get('message')}")
    
    # 无效的页面大小
    result = client.search(page_size=500)
    if not result.get("success"):
        error = result.get("error", {})
        print(f"\n❌ 无效页面大小错误:")
        print(f"   错误码: {error.get('code')}")
        print(f"   错误消息: {error.get('message')}")
    
    # SQL 注入尝试
    result = client.search(keyword="'; DROP TABLE users; --")
    if not result.get("success"):
        error = result.get("error", {})
        print(f"\n❌ SQL 注入防护:")
        print(f"   错误码: {error.get('code')}")
        print(f"   错误消息: {error.get('message')}")
    
    print()


def example_advanced_search():
    """示例：高级搜索"""
    print("=" * 60)
    print("示例 6: 高级搜索（组合查询）")
    print("=" * 60)
    
    client = SearchAPIClient()
    
    # 组合多个条件
    result = client.search(
        keyword="老北京",
        page=1,
        page_size=20,
        start_time="2026-02-01T00:00:00",
        end_time="2026-02-13T23:59:59",
        sort_by="created_at",
        sort_order="desc"
    )
    
    if result.get("success"):
        print(f"✅ 高级搜索成功")
        print(f"查询参数:")
        for key, value in result['query'].items():
            if value is not None:
                print(f"  - {key}: {value}")
        print(f"结果: {result['data']['total']} 条")
    
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("搜索 API 使用示例")
    print("=" * 60 + "\n")
    
    # 运行所有示例
    example_basic_search()
    example_pagination()
    example_time_range()
    example_sorting()
    example_error_handling()
    example_advanced_search()
    
    print("=" * 60)
    print("所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
