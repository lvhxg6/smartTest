"""
ResultJudge - 结果仲裁器

负责:
- 分析测试结果
- 判断是否需要自愈
- 决定自愈类型 (语法/逻辑)
- 判断是否为真 Bug
"""

import logging
from typing import Optional

from ..models import (
    TestCaseResult, JudgeResult, TestStatus,
    ErrorType, HealingType, TestMode
)

logger = logging.getLogger(__name__)


class ResultJudge:
    """结果仲裁器

    根据测试结果判断:
    1. 是否通过
    2. 如果失败，是否可自愈
    3. 自愈类型是什么
    """

    def __init__(self, test_mode: TestMode, max_healing_attempts: int = 3):
        """
        Args:
            test_mode: 测试模式 (完整/轻量)
            max_healing_attempts: 最大自愈尝试次数
        """
        self.test_mode = test_mode
        self.max_healing_attempts = max_healing_attempts

    def judge(self, result: TestCaseResult) -> JudgeResult:
        """判定测试结果

        Args:
            result: 测试用例结果

        Returns:
            JudgeResult 包含判定和自愈建议
        """
        # 通过直接返回
        if result.status == TestStatus.PASS:
            return JudgeResult(
                verdict=TestStatus.PASS,
                need_healing=False
            )

        # 超时不自愈
        if result.status == TestStatus.TIMEOUT:
            return JudgeResult(
                verdict=TestStatus.TIMEOUT,
                need_healing=False,
                error_detail="测试执行超时，跳过自愈"
            )

        # 跳过不自愈
        if result.status == TestStatus.SKIP:
            return JudgeResult(
                verdict=TestStatus.SKIP,
                need_healing=False,
                error_detail="测试被跳过"
            )

        # 检查是否超过最大自愈次数
        if result.healing_attempts >= self.max_healing_attempts:
            return JudgeResult(
                verdict=TestStatus.FAIL,
                need_healing=False,
                error_detail=f"已达最大自愈次数 ({self.max_healing_attempts})"
            )

        # 分析错误类型
        if result.error_info is None:
            return JudgeResult(
                verdict=result.status,
                need_healing=False,
                error_detail="无错误信息"
            )

        error_type = result.error_info.error_type

        # 语法/运行错误 -> 语法自愈
        if error_type == ErrorType.SYNTAX:
            return JudgeResult(
                verdict=TestStatus.ERROR,
                need_healing=True,
                healing_type=HealingType.SYNTAX,
                error_detail=result.error_info.message
            )

        # 连接错误 -> 不自愈 (环境问题)
        if error_type == ErrorType.CONNECTION:
            return JudgeResult(
                verdict=TestStatus.ERROR,
                need_healing=False,
                error_detail="连接错误，可能是环境问题"
            )

        # 断言失败 -> 根据模式决定
        if error_type == ErrorType.ASSERTION:
            return self._judge_assertion_failure(result)

        # 未知错误 -> 尝试语法自愈
        return JudgeResult(
            verdict=TestStatus.ERROR,
            need_healing=True,
            healing_type=HealingType.SYNTAX,
            error_detail=f"未知错误: {result.error_info.message}"
        )

    def _judge_assertion_failure(self, result: TestCaseResult) -> JudgeResult:
        """判定断言失败

        完整模式: 可以进行逻辑自愈 (判断是脚本问题还是真Bug)
        轻量模式: 无业务规则，断言失败直接记为 FAIL
        """
        error_info = result.error_info

        if self.test_mode == TestMode.COMPLETE:
            # 完整模式: 触发逻辑自愈
            return JudgeResult(
                verdict=TestStatus.FAIL,
                need_healing=True,
                healing_type=HealingType.LOGIC,
                error_detail=f"断言失败: {error_info.assertion or error_info.message}"
            )
        else:
            # 轻量模式: 无法判断，直接记为失败
            return JudgeResult(
                verdict=TestStatus.FAIL,
                need_healing=False,
                is_bug=True,  # 轻量模式下断言失败视为 Bug
                error_detail=f"断言失败 (轻量模式无法判断是否为Bug): {error_info.message}"
            )

    def should_retry(self, result: TestCaseResult) -> bool:
        """判断是否应该重试

        Args:
            result: 测试用例结果

        Returns:
            是否应该重试
        """
        if result.status == TestStatus.PASS:
            return False

        if result.healing_attempts >= self.max_healing_attempts:
            return False

        if result.status == TestStatus.TIMEOUT:
            return False

        return True

    def update_result_after_healing(
        self,
        result: TestCaseResult,
        healing_success: bool,
        is_bug: bool = False
    ) -> TestCaseResult:
        """更新自愈后的结果

        Args:
            result: 原测试结果
            healing_success: 自愈是否成功
            is_bug: 是否判定为真 Bug

        Returns:
            更新后的 TestCaseResult
        """
        result.healing_attempts += 1

        if healing_success:
            result.healed = True
            # 自愈成功后需要重新运行测试

        return result


# 便捷函数
def create_judge(
    test_mode: TestMode,
    max_attempts: int = 3
) -> ResultJudge:
    """创建 ResultJudge 的便捷函数"""
    return ResultJudge(test_mode, max_attempts)
