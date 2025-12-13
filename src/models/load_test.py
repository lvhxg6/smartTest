"""
LoadTest Models - 压力测试相关数据模型
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class LoadTestStatus(Enum):
    """压测状态"""
    PENDING = "pending"           # 待执行
    GENERATING = "generating"     # 正在生成压测脚本
    RUNNING = "running"           # 正在执行压测
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 执行失败
    STOPPED = "stopped"           # 用户停止


@dataclass
class LoadTestConfig:
    """压测配置"""
    concurrent_users: int = 50      # 并发用户数
    spawn_rate: int = 10            # 每秒启动用户数
    duration: int = 60              # 持续时间(秒)
    target_endpoints: Optional[List[str]] = None  # 目标接口(空=全部)
    only_passed: bool = False       # 仅测试通过的接口

    # 预设配置
    PRESETS = {
        "light": {"concurrent_users": 10, "spawn_rate": 5, "duration": 30},
        "standard": {"concurrent_users": 50, "spawn_rate": 10, "duration": 60},
        "heavy": {"concurrent_users": 100, "spawn_rate": 20, "duration": 180},
    }

    @classmethod
    def from_preset(cls, preset: str) -> "LoadTestConfig":
        """从预设创建配置"""
        if preset not in cls.PRESETS:
            raise ValueError(f"Unknown preset: {preset}")
        return cls(**cls.PRESETS[preset])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concurrent_users": self.concurrent_users,
            "spawn_rate": self.spawn_rate,
            "duration": self.duration,
            "target_endpoints": self.target_endpoints,
            "only_passed": self.only_passed,
        }


@dataclass
class LoadTestProgress:
    """压测实时进度"""
    elapsed_time: float = 0.0       # 已运行时间(秒)
    total_requests: int = 0         # 总请求数
    failed_requests: int = 0        # 失败请求数
    current_users: int = 0          # 当前用户数
    requests_per_second: float = 0.0  # 当前 RPS
    avg_response_time: float = 0.0  # 平均响应时间(ms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "elapsed_time": round(self.elapsed_time, 1),
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "current_users": self.current_users,
            "requests_per_second": round(self.requests_per_second, 2),
            "avg_response_time": round(self.avg_response_time, 2),
            "error_rate": round(self.failed_requests / max(self.total_requests, 1) * 100, 2),
        }


@dataclass
class LoadTestResult:
    """压测结果"""
    status: LoadTestStatus = LoadTestStatus.PENDING

    # 统计数据
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0   # 平均响应时间(ms)
    min_response_time: float = 0.0   # 最小响应时间(ms)
    max_response_time: float = 0.0   # 最大响应时间(ms)
    p50_response_time: float = 0.0   # P50 响应时间(ms)
    p95_response_time: float = 0.0   # P95 响应时间(ms)
    p99_response_time: float = 0.0   # P99 响应时间(ms)
    requests_per_second: float = 0.0  # 平均 QPS

    # 时间信息
    duration: float = 0.0            # 实际运行时间(秒)
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    # 报告路径
    report_path: Optional[str] = None
    csv_path: Optional[str] = None
    locustfile_path: Optional[str] = None

    # 错误信息
    error_message: Optional[str] = None

    # 按接口统计
    endpoint_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def error_rate(self) -> float:
        """错误率(%)"""
        if self.total_requests == 0:
            return 0.0
        return round(self.failed_requests / self.total_requests * 100, 2)

    @property
    def success_rate(self) -> float:
        """成功率(%)"""
        return round(100 - self.error_rate, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "avg_response_time": round(self.avg_response_time, 2),
            "min_response_time": round(self.min_response_time, 2),
            "max_response_time": round(self.max_response_time, 2),
            "p50_response_time": round(self.p50_response_time, 2),
            "p95_response_time": round(self.p95_response_time, 2),
            "p99_response_time": round(self.p99_response_time, 2),
            "requests_per_second": round(self.requests_per_second, 2),
            "duration": round(self.duration, 1),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "report_path": self.report_path,
            "error_message": self.error_message,
            "endpoint_stats": self.endpoint_stats,
        }
