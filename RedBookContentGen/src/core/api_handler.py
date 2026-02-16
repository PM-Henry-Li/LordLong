#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 调用处理器模块

提供统一的 API 调用逻辑，包括速率限制、重试、错误处理
"""

from typing import List, Dict, Optional, Any, Callable
import openai
from src.core.logger import Logger
from src.core.retry_handler import retry
from src.core.exceptions import (
    APIError,
    APITimeoutError,
    APIRateLimitError,
    APIAuthenticationError,
    ContentGenerationError,
    wrap_exception,
)


class APIHandler:
    """API 调用处理器"""

    def __init__(
        self,
        rpm_limiter: Any = None,
        tpm_limiter: Any = None,
        rate_limit_enabled: bool = False,
        logger_name: str = "api_handler",
    ) -> None:
        """
        初始化 API 处理器

        Args:
            rpm_limiter: 每分钟请求数限制器
            tpm_limiter: 每分钟 token 数限制器
            rate_limit_enabled: 是否启用速率限制
            logger_name: 日志记录器名称
        """
        self.rpm_limiter = rpm_limiter
        self.tpm_limiter = tpm_limiter
        self.rate_limit_enabled = rate_limit_enabled
        self.logger_name = logger_name

    def _acquire_rate_limit_tokens(self, messages: List[Dict], timeout: int = 60) -> None:
        """
        获取速率限制令牌

        Args:
            messages: 消息列表（用于估算 token 数量）
            timeout: 超时时间（秒）

        Raises:
            APITimeoutError: 获取令牌超时
        """
        if not self.rate_limit_enabled:
            return

        # 1. 获取 RPM 令牌
        if self.rpm_limiter:
            Logger.debug(
                "正在获取 RPM 令牌",
                logger_name=self.logger_name,
                available_tokens=self.rpm_limiter.get_available_tokens(),
            )

            success = self.rpm_limiter.wait_for_token(tokens=1, timeout=timeout)
            if not success:
                raise APITimeoutError(api_name="OpenAI", timeout=timeout, details={"limiter_type": "RPM"})

            Logger.debug(
                "✅ 已获取 RPM 令牌",
                logger_name=self.logger_name,
                remaining_tokens=self.rpm_limiter.get_available_tokens(),
            )

        # 2. 估算并获取 TPM 令牌
        if self.tpm_limiter:
            estimated_tokens = self._estimate_tokens(messages)

            Logger.debug(
                "正在获取 TPM 令牌",
                logger_name=self.logger_name,
                estimated_tokens=estimated_tokens,
                available_tokens=self.tpm_limiter.get_available_tokens(),
            )

            success = self.tpm_limiter.wait_for_token(tokens=estimated_tokens, timeout=timeout)

            if not success:
                Logger.warning(
                    "获取 TPM 令牌超时，使用降级策略", logger_name=self.logger_name, estimated_tokens=estimated_tokens
                )
                # 降级策略：只获取部分令牌
                available = self.tpm_limiter.get_available_tokens()
                if available > 0:
                    self.tpm_limiter.wait_for_token(tokens=int(available), timeout=10)

            Logger.debug(
                "✅ 已获取 TPM 令牌",
                logger_name=self.logger_name,
                remaining_tokens=self.tpm_limiter.get_available_tokens(),
            )

    @staticmethod
    def _estimate_tokens(messages: List[Dict]) -> int:
        """
        估算消息的 token 数量

        Args:
            messages: 消息列表

        Returns:
            估算的 token 数量
        """
        # 简单估算：每个字符约 0.5 个 token（中文约 1.5 - 2 个字符/token）
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        estimated_tokens = total_chars // 2
        # 至少预留 100 tokens
        return max(estimated_tokens, 100)

    @retry(
        max_retries=3,
        retry_delay=2.0,
        backoff_factor=2.0,
        exceptions=(openai.APIError, openai.APITimeoutError, openai.RateLimitError),
        operation_name="OpenAI API 调用",
    )
    def call_openai(
        self,
        client: openai.OpenAI,
        model: str,
        messages: List[Dict],
        temperature: float = 0.8,
        response_format: Optional[Dict] = None,
        timeout: int = 60,
    ) -> Any:
        """
        调用 OpenAI API（带速率限制和重试）

        Args:
            client: OpenAI 客户端实例
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数
            response_format: 响应格式
            timeout: 速率限制超时时间

        Returns:
            API 响应对象

        Raises:
            APITimeoutError: API 调用超时
            APIRateLimitError: 超过速率限制
            APIAuthenticationError: 认证失败
            APIError: 其他 API 错误
        """
        try:
            # 获取速率限制令牌
            self._acquire_rate_limit_tokens(messages, timeout)

            # 调用 API
            Logger.debug("正在调用 OpenAI API", logger_name=self.logger_name, model=model, temperature=temperature)

            kwargs = {"model": model, "messages": messages, "temperature": temperature}
            if response_format:
                kwargs["response_format"] = response_format

            response = client.chat.completions.create(**kwargs)  # type: ignore[call-overload]

            Logger.debug("✅ OpenAI API 调用成功", logger_name=self.logger_name, model=model)

            return response

        except openai.AuthenticationError as e:
            raise APIAuthenticationError(
                api_name="OpenAI", suggestion="请检查 API Key 是否正确配置"
            )
        except openai.RateLimitError as e:
            raise APIRateLimitError(api_name="OpenAI")
        except openai.APITimeoutError as e:
            raise APITimeoutError(api_name="OpenAI", timeout=timeout)
        except openai.APIError as e:
            raise wrap_exception(
                e, message=f"OpenAI API 调用失败: {str(e)}", exception_class=APIError, api_name="OpenAI"
            )

    def call_openai_with_evaluation(
        self,
        client: openai.OpenAI,
        model: str,
        raw_content: str,
        prompt_builder: Callable[[str, int], str],
        max_iterations: int = 3,
        evaluator: Optional[Callable[[str], bool]] = None,
    ) -> Dict:
        """
        调用 OpenAI API 并进行迭代评估

        Args:
            client: OpenAI 客户端实例
            model: 模型名称
            raw_content: 原始输入内容
            prompt_builder: 提示词构建函数
            max_iterations: 最大迭代次数
            evaluator: 评估函数（可选）

        Returns:
            最佳生成结果

        Raises:
            ContentGenerationError: 内容生成失败
        """
        best_result = None
        current_content = raw_content
        last_error = None

        for attempt in range(1, max_iterations + 1):
            Logger.info(
                f"正在尝试生成内容 (第 {attempt}/{max_iterations} 次)",
                logger_name=self.logger_name,
                attempt=attempt,
                max_iterations=max_iterations,
            )

            try:
                # 生成内容
                prompt = prompt_builder(current_content, attempt)
                response = self.call_openai(
                    client=client,
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一位专业的小红书内容创作专家。请严格按照JSON格式输出。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.8,
                    response_format={"type": "json_object"},
                )

                import json

                result = json.loads(response.choices[0].message.content.strip())
                best_result = result

                # 如果提供了评估函数，进行评估
                if evaluator and attempt < max_iterations:
                    eval_result = evaluator(result)
                    should_continue = eval_result[0] if isinstance(eval_result, tuple) else eval_result
                    feedback = eval_result[1] if isinstance(eval_result, tuple) and len(eval_result) > 1 else ""

                    if not should_continue:
                        Logger.info("内容质量优秀，通过审核", logger_name=self.logger_name)
                        break

                    # 准备下一次生成的内容
                    current_content = f"{raw_content}\n\n[上一次生成的不足之处及改进意见]：{feedback}"
                else:
                    break

            except Exception as e:
                last_error = e
                Logger.error(f"第 {attempt} 次生成失败", logger_name=self.logger_name, attempt=attempt, error=str(e))
                if attempt == max_iterations and not best_result:
                    # 最后一次尝试失败且没有任何成功结果
                    raise ContentGenerationError(
                        message=f"内容生成失败，已达到最大尝试次数: {str(last_error)}",
                        generation_type="content",
                        attempt=attempt,
                        max_attempts=max_iterations,
                    )

        if not best_result:
            raise ContentGenerationError(
                message="无法生成有效内容",
                generation_type="content",
                attempt=max_iterations,
                max_attempts=max_iterations,
            )

        return best_result  # type: ignore[no-any-return]
