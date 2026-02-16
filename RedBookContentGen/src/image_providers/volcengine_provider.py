#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
火山引擎即梦 AI 图片生成服务提供商

实现火山引擎即梦 AI 的图片生成功能，支持文本生成图片。
使用 CVSync2AsyncSubmitTask / CVSync2AsyncGetResult 异步 API。

参考文档: https://www.volcengine.com/docs/85621/1817045
"""

from typing import Optional
from .base import BaseImageProvider
from src.volcengine.signature import VolcengineSignatureV4


class VolcengineImageProvider(BaseImageProvider):
    """火山引擎即梦 AI 图片生成服务提供商"""

    # 即梦模型 req_key 映射
    MODEL_REQ_KEYS = {
        "jimeng_t2i_v40": "jimeng_t2i_v40",        # 即梦 4.0 文生图
        "jimeng-3.0-t2i": "high_aes_general_v30l_zt2i",  # 即梦 3.0 文生图（兼容旧配置）
    }

    def __init__(self, config_manager, logger, rate_limiter=None, cache=None):
        """
        初始化火山引擎图片生成服务提供商

        Args:
            config_manager: ConfigManager 实例，用于读取配置
            logger: Logger 实例，用于记录日志
            rate_limiter: RateLimiter 实例（可选），用于速率限制
            cache: CacheManager 实例（可选），用于缓存结果
        """
        super().__init__(config_manager, logger, rate_limiter, cache)

        # 从配置中读取火山引擎相关配置
        self.access_key_id = self.config_manager.get("volcengine.access_key_id")
        self.secret_access_key = self.config_manager.get("volcengine.secret_access_key")
        self.endpoint = self.config_manager.get("volcengine.endpoint", "https://visual.volcengineapi.com")
        self.service = self.config_manager.get("volcengine.service", "cv")
        self.region = self.config_manager.get("volcengine.region", "cn-north-1")
        self.timeout = self.config_manager.get("volcengine.timeout", 180)
        self.max_retries = self.config_manager.get("volcengine.max_retries", 3)

        # 默认 req_key（即梦4.0文生图）
        self.req_key = "jimeng_t2i_v40"

        # 初始化签名器
        if self.access_key_id and self.secret_access_key:
            self.signer = VolcengineSignatureV4(
                self.access_key_id,
                self.secret_access_key,
                self.service,
                self.region
            )
        else:
            self.signer = None
            self.logger.warning(
                "火山引擎 API 密钥未配置，无法使用火山引擎图片生成服务",
                logger_name="volcengine_provider"
            )

    def generate(self, prompt: str, size: str = "1024*1365", **kwargs) -> Optional[str]:
        """
        生成图片

        流程:
        1. 检查缓存
        2. 检查速率限制
        3. 创建图片生成任务 (CVSync2AsyncSubmitTask)
        4. 轮询任务状态 (CVSync2AsyncGetResult)
        5. 缓存结果

        Args:
            prompt: 图片提示词，描述要生成的图片内容
            size: 图片尺寸，格式为 "宽*高"，默认 "1024*1365"
            **kwargs: 其他参数，如 is_cover（是否为封面图）等

        Returns:
            生成的图片 URL，失败返回 None
        """
        if not self.signer:
            self.logger.error(
                "火山引擎 API 密钥未配置，无法生成图片",
                logger_name="volcengine_provider"
            )
            return None

        # 1. 检查缓存
        cache_key = None
        if self.cache:
            import hashlib
            cache_key = hashlib.md5(f"{prompt}_{size}".encode('utf-8')).hexdigest()
            cached_url = self.cache.get(cache_key)
            if cached_url:
                self.logger.info(
                    "从缓存返回图片 URL",
                    logger_name="volcengine_provider",
                    cache_key=cache_key
                )
                return cached_url

        # 2. 检查速率限制
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()

        try:
            # 3. 创建图片生成任务
            self.logger.info(
                "创建即梦图片生成任务",
                logger_name="volcengine_provider",
                prompt=prompt[:50] + "..." if len(prompt) > 50 else prompt,
                size=size
            )
            task_id = self._create_task(prompt, size)

            if not task_id:
                self.logger.error(
                    "创建图片生成任务失败",
                    logger_name="volcengine_provider"
                )
                return None

            # 4. 轮询任务状态
            self.logger.info(
                "轮询任务状态",
                logger_name="volcengine_provider",
                task_id=task_id
            )
            image_url = self._poll_status(task_id, max_wait=self.timeout)

            if not image_url:
                self.logger.error(
                    "获取图片 URL 失败",
                    logger_name="volcengine_provider",
                    task_id=task_id
                )
                return None

            # 5. 缓存结果
            if self.cache and cache_key:
                self.cache.set(cache_key, image_url)
                self.logger.info(
                    "缓存图片 URL",
                    logger_name="volcengine_provider",
                    cache_key=cache_key
                )

            self.logger.info(
                "图片生成成功",
                logger_name="volcengine_provider",
                image_url=image_url
            )
            return image_url

        except Exception as e:
            self.logger.error(
                f"图片生成失败: {str(e)}",
                logger_name="volcengine_provider",
                error=str(e)
            )
            return None

    def _handle_api_error(self, error: Exception, retry_count: int) -> tuple:
        """
        处理 API 错误，判断是否应该重试

        Args:
            error: 异常对象
            retry_count: 当前重试次数

        Returns:
            (是否应该重试, 错误消息)
        """
        import requests

        # 记录错误
        self.logger.error(
            f"API 调用失败（重试次数: {retry_count}/{self.max_retries}）",
            logger_name="volcengine_provider",
            error=str(error),
            retry_count=retry_count
        )

        # 分类错误并决定是否重试
        if isinstance(error, requests.exceptions.Timeout):
            return (retry_count < self.max_retries, "网络超时")

        elif isinstance(error, requests.exceptions.ConnectionError):
            return (retry_count < self.max_retries, "连接失败")

        elif isinstance(error, requests.exceptions.HTTPError):
            status_code = error.response.status_code if error.response else 0
            resp_text = ""
            try:
                resp_text = error.response.text[:300] if error.response else ""
            except Exception:
                pass

            if status_code == 429:
                return (retry_count < self.max_retries, f"速率限制: {resp_text}")

            elif status_code == 401:
                return (False, f"认证失败(401): {resp_text}")

            elif 400 <= status_code < 500:
                return (False, f"客户端错误({status_code}): {resp_text}")

            elif 500 <= status_code < 600:
                return (retry_count < self.max_retries, f"服务器错误({status_code}): {resp_text}")

        return (False, f"未知错误: {str(error)}")

    def _create_task(self, prompt: str, size: str) -> Optional[str]:
        """
        创建图片生成任务（使用 CVSync2AsyncSubmitTask API）

        即梦4.0 API 请求参数:
        - req_key: jimeng_t2i_v40 (必填)
        - prompt: 提示词 (必填，最大800字)
        - width/height: 分辨率 (可选)
        - scale: prompt 权重 (可选, 0-1, 默认0.5)
        - force_single: 强制单图 (可选)
        - req_json: 扩展参数JSON串 (可选)

        Args:
            prompt: 图片提示词
            size: 图片尺寸，格式为 "宽*高"

        Returns:
            任务 ID，失败返回 None
        """
        import requests
        import json
        import time

        # 解析尺寸
        try:
            width, height = map(int, size.split('*'))
        except ValueError:
            self.logger.error(
                f"无效的图片尺寸格式: {size}",
                logger_name="volcengine_provider"
            )
            return None

        # 构建请求体 - 即梦4.0 CVSync2AsyncSubmitTask 格式
        request_body = {
            "req_key": self.req_key,
            "prompt": prompt,
            "width": width,
            "height": height,
            "force_single": True,       # 强制单图输出
            "req_json": json.dumps({    # 扩展参数（JSON字符串）
                "return_url": True,
                "logo_info": {
                    "add_logo": False
                }
            })
        }

        # 构建请求 URL（使用 Query 参数指定 Action 和 Version）
        url = f"{self.endpoint}?Action=CVSync2AsyncSubmitTask&Version=2022-08-31"

        # 构建请求头
        host = self.endpoint.replace("https://", "").replace("http://", "")
        headers = {
            "Content-Type": "application/json",
            "Host": host
        }

        # 签名请求
        body_str = json.dumps(request_body)
        signed_headers = self.signer.sign("POST", url, headers, body_str)

        # 重试逻辑
        retry_count = 0
        last_error_msg = None

        while retry_count <= self.max_retries:
            try:
                self.logger.info(
                    f"发送 CVSync2AsyncSubmitTask 请求（尝试 {retry_count + 1}/{self.max_retries + 1}）",
                    logger_name="volcengine_provider"
                )

                response = requests.post(
                    url,
                    headers=signed_headers,
                    data=body_str,
                    timeout=30
                )

                # 记录响应内容（便于调试）
                try:
                    resp_text = response.text[:500]
                    self.logger.info(
                        f"API 响应: status={response.status_code}, body={resp_text}",
                        logger_name="volcengine_provider"
                    )
                except Exception:
                    pass

                response.raise_for_status()

                result = response.json()

                self.logger.info(
                    f"CVSync2AsyncSubmitTask 响应: code={result.get('code')}, message={result.get('message', '')}",
                    logger_name="volcengine_provider"
                )

                # 检查响应码
                if result.get("code") != 10000:
                    error_msg = result.get('message', '未知错误')
                    self.logger.error(
                        f"创建任务失败: code={result.get('code')}, message={error_msg}",
                        logger_name="volcengine_provider",
                        code=result.get("code"),
                        message=error_msg
                    )
                    return None

                # 获取任务 ID
                task_id = result.get("data", {}).get("task_id")
                if not task_id:
                    self.logger.error(
                        "响应中未包含任务 ID",
                        logger_name="volcengine_provider",
                        response=str(result)[:200]
                    )
                    return None

                self.logger.info(
                    "即梦任务创建成功",
                    logger_name="volcengine_provider",
                    task_id=task_id
                )
                return task_id

            except requests.exceptions.RequestException as e:
                should_retry, error_msg = self._handle_api_error(e, retry_count)
                last_error_msg = error_msg

                if not should_retry:
                    self.logger.error(
                        f"创建任务失败（不可重试）: {error_msg}",
                        logger_name="volcengine_provider",
                        error=str(e)
                    )
                    return None

                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = 2 ** (retry_count - 1)
                    self.logger.warning(
                        f"创建任务失败，{wait_time}秒后重试（{retry_count}/{self.max_retries}）",
                        logger_name="volcengine_provider",
                        error=error_msg,
                        wait_time=wait_time
                    )
                    time.sleep(wait_time)

        self.logger.error(
            f"创建任务失败，重试次数已耗尽: {last_error_msg}",
            logger_name="volcengine_provider",
            retry_count=retry_count
        )
        return None

    def _poll_status(self, task_id: str, max_wait: int = 180) -> Optional[str]:
        """
        轮询任务状态（使用 CVSync2AsyncGetResult API）

        即梦4.0 查询 API:
        - 方法: POST
        - req_key: jimeng_t2i_v40 (必填)
        - task_id: 提交任务返回的ID (必填)
        - 返回 Status: 0=处理中, 1=成功, 2=失败

        Args:
            task_id: 任务 ID
            max_wait: 最大等待时间（秒），默认 180 秒

        Returns:
            图片 URL，失败返回 None
        """
        import requests
        import json
        import time

        start_time = time.time()
        poll_interval = 2  # 轮询间隔（秒）
        consecutive_errors = 0
        max_consecutive_errors = 3

        while True:
            # 检查是否超时
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                self.logger.error(
                    f"轮询超时（{max_wait}秒）",
                    logger_name="volcengine_provider",
                    task_id=task_id
                )
                return None

            # 构建请求 URL（POST 方法，task_id 放在请求体中）
            url = f"{self.endpoint}?Action=CVSync2AsyncGetResult&Version=2022-08-31"

            # 构建请求体
            request_body = {
                "req_key": self.req_key,
                "task_id": task_id
            }
            body_str = json.dumps(request_body)

            # 构建请求头
            host = self.endpoint.replace("https://", "").replace("http://", "")
            headers = {
                "Content-Type": "application/json",
                "Host": host
            }

            # 签名请求
            signed_headers = self.signer.sign("POST", url, headers, body_str)

            try:
                response = requests.post(
                    url,
                    headers=signed_headers,
                    data=body_str,
                    timeout=30
                )

                # 记录响应
                try:
                    resp_text = response.text[:500]
                    self.logger.info(
                        f"查询响应: status={response.status_code}, body={resp_text}",
                        logger_name="volcengine_provider"
                    )
                except Exception:
                    pass

                response.raise_for_status()

                result = response.json()

                # 请求成功，重置连续错误计数
                consecutive_errors = 0

                # 检查响应码
                resp_code = result.get("code")
                if resp_code != 10000:
                    error_msg = result.get('message', '未知错误')
                    # code=20000 表示任务还在处理中
                    if resp_code == 20000:
                        self.logger.info(
                            f"任务处理中（code: {resp_code}）",
                            logger_name="volcengine_provider",
                            task_id=task_id
                        )
                        time.sleep(poll_interval)
                        continue

                    self.logger.error(
                        f"查询任务状态失败: code={resp_code}, message={error_msg}",
                        logger_name="volcengine_provider",
                        code=resp_code,
                        message=error_msg
                    )
                    return None

                # 获取任务数据
                data = result.get("data", {})
                
                # DEBUG: 打印完整响应数据以调试 URL 提取
                self.logger.info(
                    f"查询任务响应数据: {json.dumps(data, ensure_ascii=False)}",
                    logger_name="volcengine_provider",
                    task_id=task_id
                )

                # 即梦4.0 用 Status 字段（int）: 0=处理中, 1=成功, 2=失败
                status = data.get("status") or data.get("Status")
                
                # 检查是否有 base64 数据 (有些情况返回 base64 但 status 仍为 in_queue)
                binary_data = data.get("binary_data_base64")
                has_binary_data = binary_data and isinstance(binary_data, list) and len(binary_data) > 0

                if status == 1 or status == "done" or has_binary_data:
                    # 任务完成，获取图片 URL
                    image_urls = data.get("image_urls", [])
                    if image_urls:
                        image_url = image_urls[0]
                        self.logger.info(
                            "即梦任务完成",
                            logger_name="volcengine_provider",
                            task_id=task_id,
                            image_url=image_url[:80]
                        )
                        return image_url

                    # 尝试从 resp_data 中获取
                    resp_data = data.get("resp_data", {})
                    if isinstance(resp_data, str):
                        try:
                            resp_data = json.loads(resp_data)
                        except Exception:
                            pass

                    if isinstance(resp_data, dict):
                        image_urls = resp_data.get("image_urls", [])
                        if image_urls:
                            image_url = image_urls[0]
                            self.logger.info(
                                "即梦任务完成（从 resp_data 获取）",
                                logger_name="volcengine_provider",
                                task_id=task_id,
                                image_url=image_url[:80]
                            )
                            return image_url

                    # 尝试从 binary_data_base64 获取并保存为文件
                    if has_binary_data:
                        try:
                            import base64
                            import uuid
                            import os
                            
                            # 确保保存目录存在
                            save_dir = os.path.join(os.getcwd(), "static", "images", "generated")
                            os.makedirs(save_dir, exist_ok=True)
                            
                            # 解码并保存图片
                            image_data = base64.b64decode(binary_data[0])
                            filename = f"jimeng_{int(time.time())}_{str(uuid.uuid4())[:8]}.png"
                            filepath = os.path.join(save_dir, filename)
                            
                            with open(filepath, "wb") as f:
                                f.write(image_data)
                                
                            # 返回本地 URL (相对于 static 目录)
                            local_url = f"/static/images/generated/{filename}"
                            
                            self.logger.info(
                                f"即梦任务完成（保存 base64 为文件: {filepath}）",
                                logger_name="volcengine_provider",
                                task_id=task_id
                            )
                            return local_url
                        except Exception as e:
                            self.logger.error(
                                f"保存 Base64 图片失败: {e}",
                                logger_name="volcengine_provider",
                                task_id=task_id
                            )

                    self.logger.error(
                        "任务成功但未返回图片 URL",
                        logger_name="volcengine_provider",
                        task_id=task_id,
                        data=str(data)[:300]
                    )
                    return None

                elif status == 2 or status == "failed":
                    self.logger.error(
                        "即梦任务失败",
                        logger_name="volcengine_provider",
                        task_id=task_id,
                        data=str(data)[:200]
                    )
                    return None

                elif status in (0, "running", "pending", "submitted", "in_queue", "generating", None):
                    # 任务处理中，继续轮询
                    self.logger.info(
                        f"任务处理中（status: {status}）",
                        logger_name="volcengine_provider",
                        task_id=task_id
                    )
                    time.sleep(poll_interval)
                    continue

                else:
                    # 未知状态
                    self.logger.warning(
                        f"未知的任务状态: {status}",
                        logger_name="volcengine_provider",
                        task_id=task_id,
                        status=status
                    )
                    time.sleep(poll_interval)
                    continue

            except requests.exceptions.RequestException as e:
                should_retry, error_msg = self._handle_api_error(e, consecutive_errors)
                consecutive_errors += 1

                if not should_retry or consecutive_errors > max_consecutive_errors:
                    self.logger.error(
                        f"查询任务状态失败（不可重试或连续错误过多）: {error_msg}",
                        logger_name="volcengine_provider",
                        error=str(e),
                        consecutive_errors=consecutive_errors
                    )
                    return None

                wait_time = min(2 ** (consecutive_errors - 1), poll_interval)
                self.logger.warning(
                    f"查询任务状态失败，{wait_time}秒后重试（连续错误: {consecutive_errors}/{max_consecutive_errors}）",
                    logger_name="volcengine_provider",
                    error=error_msg,
                    wait_time=wait_time
                )
                time.sleep(wait_time)
                continue

    def get_provider_name(self) -> str:
        """
        获取服务提供商名称

        Returns:
            服务提供商名称 "volcengine"
        """
        return "volcengine"
