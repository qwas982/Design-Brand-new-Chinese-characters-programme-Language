"""
异常处理模块 - 提供统一的错误处理和异常恢复机制
本模块定义编译器相关的所有异常类型和错误处理基础设施
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Union
from enum import Enum, auto


class 错误级别(Enum):
    """错误严重级别枚举"""
    信息 = auto()
    警告 = auto()
    错误 = auto()
    严重 = auto()


class 错误类型(Enum):
    """错误类型枚举"""
    词法错误 = auto()
    语法错误 = auto()
    语义错误 = auto()
    类型错误 = auto()
    运行时错误 = auto()
    内存错误 = auto()
    除零错误 = auto()
    未知错误 = auto()


@dataclass
class 错误节点:
    """错误信息节点 - 记录编译或运行时的错误信息"""
    错误信息: str
    行号: int
    列号: int
    错误类型: 错误类型 = 错误类型.未知错误
    严重程度: 错误级别 = 错误级别.错误
    源文件: str = ""
    详细信息: str = ""
    
    def 转字典(self) -> Dict[str, Any]:
        """将错误节点转换为字典格式"""
        return {
            "错误信息": self.错误信息,
            "行号": self.行号,
            "列号": self.列号,
            "错误类型": self.错误类型.name,
            "严重程度": self.严重程度.name,
            "源文件": self.源文件,
            "详细信息": self.详细信息
        }


class 编译异常基类(Exception):
    """所有编译相关异常的基类"""
    
    def __init__(self, 消息: str, 行号: int = 0, 列号: int = 0):
        super().__init__(消息)
        self.消息 = 消息
        self.行号 = 行号
        self.列号 = 列号
    
    def __str__(self):
        位置信息 = f" (行{self.行号}, 列{self.列号})" if self.行号 > 0 else ""
        return f"{self.__class__.__name__}: {self.消息}{位置信息}"


class 词法分析异常(编译异常基类):
    """词法分析阶段异常"""
    pass


class 语法分析异常(编译异常基类):
    """语法分析阶段异常"""
    pass


class 语义分析异常(编译异常基类):
    """语义分析阶段异常"""
    pass


class 类型检查异常(编译异常基类):
    """类型检查阶段异常"""
    pass


class 运行时异常(编译异常基类):
    """运行时异常"""
    pass


class 除零异常(运行时异常):
    """除零错误异常"""
    pass


class 内存访问异常(运行时异常):
    """内存访问越界异常"""
    pass


class 栈操作异常(运行时异常):
    """栈操作异常（如栈空时弹出）"""
    pass


class 未知指令异常(运行时异常):
    """执行未知指令时异常"""
    pass


@dataclass
class 恢复树节点:
    """异常恢复树节点 - 用于记录和查找恢复策略"""
    节点名称: str
    恢复策略列表: List[str] = field(default_factory=list)
    子节点字典: Dict[str, '恢复树节点'] = field(default_factory=dict)
    父节点: Optional['恢复树节点'] = None
    
    def 添加子节点(self, 名称: str, 策略列表: List[str] = None) -> '恢复树节点':
        """添加子节点"""
        子节点 = 恢复树节点(名称, 策略列表 or [], 父节点=self)
        self.子节点字典[名称] = 子节点
        return 子节点
    
    def 获取恢复策略(self, 错误类型: str) -> str:
        """根据错误类型获取恢复策略"""
        策略映射 = {
            "词法错误": "跳过字符",
            "语法错误": "恐慌模式",
            "类型错误": "类型强制转换",
            "除零错误": "返回默认值",
            "内存错误": "中止执行",
            "运行时错误": "默认恢复"
        }
        return 策略映射.get(错误类型, "默认恢复")


class 异常处理中心:
    """异常处理中心 - 统一的异常管理和恢复机制"""
    
    def __init__(self):
        self.异常恢复树 = self._创建默认恢复树()
        self.异常处理程序映射: Dict[str, Callable] = {}
        self.异常记录列表: List[错误节点] = []
    
    def _创建默认恢复树(self) -> 恢复树节点:
        """创建默认的异常恢复树"""
        根节点 = 恢复树节点("根节点")
        
        # 词法分析恢复节点
        词法节点 = 根节点.添加子节点("词法分析", ["跳过字符", "跳转到下一行", "插入缺失字符"])
        
        # 语法分析恢复节点
        语法节点 = 根节点.添加子节点("语法分析", ["恐慌模式", "错误产生式", "短语层恢复"])
        
        # 运行时恢复节点
        运行时节点 = 根节点.添加子节点("运行时", ["类型强制转换", "返回默认值", "重试操作"])
        
        # 类型检查恢复节点
        类型节点 = 根节点.添加子节点("类型检查", ["类型强制转换", "报告错误"])
        
        return 根节点
    
    def 注册异常处理程序(self, 异常类型: str, 处理程序: Callable):
        """注册异常处理程序"""
        self.异常处理程序映射[异常类型] = 处理程序
    
    def 查找异常处理程序(self, 异常信息: str) -> Optional[Callable]:
        """根据异常信息查找处理程序"""
        # 直接匹配
        for 类型名, 处理程序 in self.异常处理程序映射.items():
            if 类型名 in 异常信息:
                return 处理程序
        
        # 默认处理程序
        return self.异常处理程序映射.get("默认")
    
    def 记录错误(self, 错误节点对象: 错误节点):
        """记录错误信息"""
        self.异常记录列表.append(错误节点对象)
    
    def 清除错误记录(self):
        """清除所有错误记录"""
        self.异常记录列表.clear()
    
    def 有错误(self) -> bool:
        """检查是否有错误记录"""
        return len(self.异常记录列表) > 0
    
    def 获取错误数量(self) -> int:
        """获取错误数量"""
        return len(self.异常记录列表)
    
    def 获取所有错误(self) -> List[错误节点]:
        """获取所有错误记录"""
        return self.异常记录列表.copy()
    
    def 创建错误节点(
        self,
        错误信息: str,
        行号: int,
        列号: int,
        错误类型: 错误类型 = 错误类型.未知错误,
        严重程度: 错误级别 = 错误级别.错误,
        源文件: str = "",
        详细信息: str = ""
    ) -> 错误节点:
        """创建错误节点并记录"""
        节点 = 错误节点(
            错误信息=错误信息,
            行号=行号,
            列号=列号,
            错误类型=错误类型,
            严重程度=严重程度,
            源文件=源文件,
            详细信息=详细信息
        )
        self.记录错误(节点)
        return 节点
    
    def 获取恢复策略(self, 错误类型: str) -> str:
        """获取恢复策略"""
        return self.异常恢复树.获取恢复策略(错误类型)


class 安全执行器:
    """安全执行器 - 提供安全的操作执行包装"""
    
    def __init__(self, 异常处理中心: 异常处理中心):
        self.异常处理中心 = 异常处理中心
        self.最大重试次数 = 3
    
    def 安全执行(
        self,
        操作函数: Callable,
        操作名称: str,
        错误类型名: str = "运行时错误"
    ) -> Any:
        """安全执行操作 - 带有异常处理包装"""
        最后异常 = None
        
        for 重试次数 in range(self.最大重试次数):
            try:
                return 操作函数()
            except Exception as 执行异常:
                最后异常 = 执行异常
                恢复策略 = self.异常处理中心.获取恢复策略(错误类型名)
                
                if 恢复策略 == "重试操作":
                    if 重试次数 < self.最大重试次数 - 1:
                        continue
                    else:
                        self.异常处理中心.创建错误节点(
                            f"{操作名称}重试{self.最大重试次数}次失败: {执行异常}",
                            0, 0, 错误类型=错误类型.运行时错误
                        )
                        break
                elif 恢复策略 == "返回默认值":
                    return self._获取默认值(执行异常)
                else:
                    self.异常处理中心.创建错误节点(
                        f"{操作名称}失败: {执行异常}",
                        0, 0, 错误类型=错误类型.运行时错误
                    )
                    break
        
        # 如果有异常且没有特殊处理，抛出异常
        if 最后异常:
            raise 最后异常
        return None
    
    def _获取默认值(self, 异常: Exception) -> Any:
        """根据异常类型获取默认值"""
        if isinstance异常(异常, (ZeroDivisionError, ArithmeticError)):
            return 0
        elif isinstance异常(异常, (ValueError, TypeError)):
            return 0 if "int" in str(异常) else 0.0 if "float" in str(异常) else ""
        elif isinstance异常(异常, IndexError):
            return None
        elif isinstance异常(异常, KeyError):
            return None
        else:
            return None


def isinstance异常(obj: Any, 类型元组) -> bool:
    """检查对象是否属于指定类型（元组支持）"""
    if not isinstance(类型元组, tuple):
        类型元组 = (类型元组,)
    return any(isinstance(obj, t) for t in 类型元组)
