#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
火山引擎 HMAC-SHA256 签名算法实现

该模块实现了火山引擎 API 的 HMAC-SHA256 签名认证。
参考文档: https://www.volcengine.com/docs/6791/116837
"""

import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs, quote
from typing import Dict


class VolcengineSignatureV4:
    """火山引擎 HMAC-SHA256 签名算法实现"""
    
    def __init__(self, access_key_id: str, secret_access_key: str, service: str, region: str):
        """
        初始化签名器
        
        Args:
            access_key_id: 访问密钥 ID (AK)
            secret_access_key: 访问密钥 (SK)，直接使用原始值，不做任何编码/解码处理
            service: 服务名（如 "cv"）
            region: 区域（如 "cn-north-1"）
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key  # 直接使用，不做 Base64 解码
        self.service = service
        self.region = region
    
    def sign(self, method: str, url: str, headers: Dict[str, str], body: str = "") -> Dict[str, str]:
        """
        签名 HTTP 请求
        
        参考火山引擎签名规范:
        - 算法: HMAC-SHA256
        - Credential Scope: {date}/{region}/{service}/request
        - 签名密钥: 直接用 SK（不加 "AWS4" 前缀）
        
        Args:
            method: HTTP 方法（GET, POST 等）
            url: 完整的请求 URL
            headers: 请求头字典
            body: 请求体（可选）
            
        Returns:
            包含 Authorization 头的完整请求头字典
        """
        # 解析 URL
        parsed_url = urlparse(url)
        path = parsed_url.path or '/'
        query = parsed_url.query
        host = parsed_url.netloc
        
        # 获取当前 UTC 时间戳
        now = datetime.now(timezone.utc)
        x_date = now.strftime('%Y%m%dT%H%M%SZ')
        date_short = now.strftime('%Y%m%d')
        
        # 计算 payload 的 SHA256 哈希
        payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
        
        # 构建要签名的请求头（火山引擎要求 content-type, host, x-content-sha256, x-date）
        headers = headers.copy()
        headers['X-Date'] = x_date
        headers['X-Content-Sha256'] = payload_hash
        if 'Host' not in headers:
            headers['Host'] = host
        
        # 规范化请求头（key 小写、排序）
        canonical_headers_map = {}
        for key, value in headers.items():
            canonical_headers_map[key.lower()] = value.strip()
        
        sorted_header_keys = sorted(canonical_headers_map.keys())
        canonical_headers_str = ""
        for key in sorted_header_keys:
            canonical_headers_str += f"{key}:{canonical_headers_map[key]}\n"
        signed_headers_str = ";".join(sorted_header_keys)
        
        # 规范化查询字符串
        canonical_querystring = self._get_canonical_query_string(query)
        
        # 构建规范请求 (Canonical Request)
        canonical_request = (
            f"{method}\n"
            f"{path}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers_str}\n"
            f"{signed_headers_str}\n"
            f"{payload_hash}"
        )
        
        # 构建待签名字符串 (String to Sign)
        credential_scope = f"{date_short}/{self.region}/{self.service}/request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        string_to_sign = (
            f"HMAC-SHA256\n"
            f"{x_date}\n"
            f"{credential_scope}\n"
            f"{hashed_canonical_request}"
        )
        
        # 计算签名密钥（火山引擎：直接用 SK，不加 "AWS4" 前缀）
        k_date = self._hmac_sha256(self.secret_access_key.encode('utf-8'), date_short)
        k_region = self._hmac_sha256(k_date, self.region)
        k_service = self._hmac_sha256(k_region, self.service)
        k_signing = self._hmac_sha256(k_service, "request")
        
        # 计算最终签名
        signature = self._hmac_sha256(k_signing, string_to_sign).hex()
        
        # 构建 Authorization 头
        authorization = (
            f"HMAC-SHA256 "
            f"Credential={self.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers_str}, "
            f"Signature={signature}"
        )
        
        # 返回包含签名的请求头
        result_headers = headers.copy()
        result_headers['Authorization'] = authorization
        
        return result_headers
    
    def _get_canonical_query_string(self, query: str) -> str:
        """
        规范化查询字符串
        
        按参数名 ASCII 排序，使用 URI 编码。
        
        Args:
            query: 原始查询字符串
            
        Returns:
            规范化的查询字符串
        """
        if not query:
            return ''
        
        # 解析查询参数
        params = parse_qs(query, keep_blank_values=True)
        
        # 对参数进行排序和编码
        canonical_params = []
        for key in sorted(params.keys()):
            for value in sorted(params[key]):
                encoded_key = quote(key, safe='')
                encoded_value = quote(value, safe='')
                canonical_params.append(f"{encoded_key}={encoded_value}")
        
        return '&'.join(canonical_params)
    
    @staticmethod
    def _hmac_sha256(key: bytes, message: str) -> bytes:
        """
        计算 HMAC-SHA256
        
        Args:
            key: 密钥（字节）
            message: 消息（字符串）
            
        Returns:
            HMAC-SHA256 结果（字节）
        """
        return hmac.new(key, message.encode('utf-8'), hashlib.sha256).digest()
