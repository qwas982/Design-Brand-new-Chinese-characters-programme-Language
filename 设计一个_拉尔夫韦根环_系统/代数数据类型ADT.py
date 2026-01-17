"""
代数数据类型模块 - 提供ADT、模式匹配和访问者模式基础设施
本模块定义编译器所需的类型系统和数据结构
"""

from dataclasses import dataclass, field
from typing import (
    Union, List, Dict, Any, Callable, TypeVar, Generic, 
    Optional, Protocol, runtime_checkable, ForwardRef
)
from enum import Enum, auto
import sys


# 类型变量用于泛型
_T = TypeVar('_T')
_U = TypeVar('_U')
_V = TypeVar('_V')


class 匹配结果(Enum):
    """匹配结果枚举"""
    成功 = auto()
    失败 = auto()
    无匹配 = auto()


class 可选(Generic[_T]):
    """可选类型 - Maybe Monad模式：表示可能存在的值"""
    
    def __init__(self, 值: Optional[_T] = None):
        self.值 = 值
    
    def 是空(self) -> bool:
        """检查是否为空"""
        return self.值 is None
    
    def 不是空(self) -> bool:
        """检查是否非空"""
        return self.值 is not None
    
    def 获取值(self, 默认值: _T = None) -> _T:
        """获取值，如果为空则返回默认值"""
        return self.值 if self.值 is not None else 默认值
    
    def 映射(self, 函数: Callable[[_T], _U]) -> '可选[_U]':
        """Functor映射：如果存在值则应用函数"""
        if self.值 is not None:
            return 可选(函数(self.值))
        return 可选()
    
    def 绑定(self, 函数: Callable[[_T], '可选[_U]']) -> '可选[_U]':
        """Monad绑定：链式处理可选值"""
        if self.值 is not None:
            return 函数(self.值)
        return 可选()
    
    def 过滤(self, 谓词: Callable[[_T], bool]) -> '可选[_T]':
        """过滤：保留满足条件的值"""
        if self.值 is not None and 谓词(self.值):
            return self
        return 可选()
    
    def 模式匹配(
        self, 
        有值分支: Callable[[_T], _U], 
        无值分支: Callable[[], _U]
    ) -> _U:
        """模式匹配：根据值存在与否执行不同分支"""
        if self.值 is not None:
            return 有值分支(self.值)
        return 无值分支()
    
    def __bool__(self) -> bool:
        """布尔值转换"""
        return self.值 is not None
    
    def __repr__(self) -> str:
        return f"可选({self.值!r})" if self.值 is not None else "可选()"


class 要么(Generic[_T, _U]):
    """Either类型 - Either Monad模式：表示两种可能结果"""
    
    def __init__(self, 左值: _T = None, 右值: _U = None):
        self.左值 = 左值
        self.右值 = 右值
    
    def 是左值(self) -> bool:
        """检查是否是左值"""
        return self.左值 is not None
    
    def 是右值(self) -> bool:
        """检查是否是右值"""
        return self.右值 is not None
    
    def 获取左值(self, 默认值: _T = None) -> _T:
        """获取左值"""
        return self.左值 if self.左值 is not None else 默认值
    
    def 获取右值(self, 默认值: _U = None) -> _U:
        """获取右值"""
        return self.右值 if self.右值 is not None else 默认值
    
    def 映射左(self, 函数: Callable[[_T], _V]) -> 'Either[_V, _U]':
        """映射左值"""
        if self.左值 is not None:
            return 要么(函数(self.左值), None)
        return 要么(None, self.右值)
    
    def 映射右(self, 函数: Callable[[_U], _V]) -> 'Either[_T, _V]':
        """映射右值"""
        if self.右值 is not None:
            return 要么(None, 函数(self.右值))
        return 要么(self.左值, None)
    
    def 绑定(self, 函数: Callable[[_T], 'Either[_V, _U]']) -> 'Either[_V, _U]':
        """绑定"""
        if self.左值 is not None:
            return 函数(self.左值)
        return 要么(None, self.右值)
    
    def 模式匹配(
        self, 
        左分支: Callable[[_T], _V], 
        右分支: Callable[[_U], _V]
    ) -> _V:
        """模式匹配：根据左右值执行不同分支"""
        if self.左值 is not None:
            return 左分支(self.左值)
        return 右分支(self.右值)
    
    def __repr__(self) -> str:
        if self.左值 is not None:
            return f"左值({self.左值!r})"
        return f"右值({self.右值!r})"


class 匹配器:
    """模式匹配器 - 用于实现模式匹配功能"""
    
    def __init__(self, 目标):
        self.目标 = 目标
        self.匹配结果 = None
    
    def 匹配(self, 模式) -> bool:
        """检查目标是否匹配模式"""
        # 通配符匹配
        if 模式 == '_' or 模式 is None:
            self.匹配结果 = self.目标
            return True
        
        # 类型匹配
        if isinstance(模式, type) and isinstance(self.目标, 模式):
            self.匹配结果 = self.目标
            return True
        
        # 值匹配
        if self.目标 == 模式:
            self.匹配结果 = self.目标
            return True
        
        # 元组模式匹配
        if isinstance(模式, tuple) and isinstance(self.目标, tuple):
            if len(模式) == len(self.目标):
                return all(匹配器(子目标).匹配(子模式) 
                          for 子目标, 子模式 in zip(self.目标, 模式))
        
        # 列表模式匹配
        if isinstance(模式, list) and isinstance(self.目标, list):
            if len(模式) == len(self.目标):
                return all(匹配器(子目标).匹配(子模式) 
                          for 子目标, 子模式 in zip(self.目标, 模式))
        
        # 数据类模式匹配
        if dataclasses.is_dataclass(模式):
            if dataclasses.is_dataclass(self.目标):
                for 字段名 in dataclasses.fields(模式):
                    if not hasattr(self.目标, 字段名.name):
                        return False
                    目标字段值 = getattr(self.目标, 字段名.name)
                    模式字段值 = getattr(模式, 字段名.name)
                    if 模式字段值 != '_' and not 匹配器(目标字段值).匹配(模式字段值):
                        return False
                self.匹配结果 = self.目标
                return True
        
        return False
    
    def 获取匹配结果(self):
        """获取匹配结果"""
        return self.匹配结果


def 模式匹配函数(匹配函数: Callable):
    """模式匹配装饰器 - 使函数支持模式匹配语法"""
    def 包装器(*参数, **关键字参数):
        结果 = 匹配函数(*参数, **关键字参数)
        
        # 如果结果是模式匹配表达式，求值它
        if isinstance(结果, _模式匹配表达式):
            return 结果.求值()
        
        return 结果
    
    return 包装器


class _模式匹配表达式:
    """模式匹配表达式 - 内部使用的表达式类"""
    
    def __init__(self, 目标, 分支列表: List[tuple]):
        self.目标 = 目标
        self.分支列表 = 分支列表
    
    def 求值(self):
        """求值模式匹配表达式"""
        for 模式, 处理函数 in self.分支列表:
            if 匹配器(self.目标).匹配(模式):
                匹配结果 = 匹配器(self.目标).获取匹配结果()
                if callable(处理函数):
                    return 处理函数(匹配结果)
                return 处理函数
        raise ValueError(f"没有模式匹配成功: {self.目标}")


def 匹配(目标) -> '_模式匹配表达式':
    """创建模式匹配表达式"""
    return _模式匹配表达式(目标, [])


def _(模式):
    """创建模式匹配分支"""
    匹配表达式 = _模式匹配表达式(None, [(模式, None)])
    return 匹配表达式


class 访问者协议(Protocol):
    """访问者协议 - 定义访问者必须实现的方法"""
    
    def 访问程序节点(self, 节点: '程序节点') -> Any:
        ...
    
    def 访问循环节点(self, 节点: '循环节点') -> Any:
        ...
    
    def 访问验证节点(self, 节点: '验证节点') -> Any:
        ...
    
    def 访问持久化节点(self, 节点: '持久化节点') -> Any:
        ...
    
    def 访问AI调用节点(self, 节点: 'AI调用节点') -> Any:
        ...
    
    def 访问条件节点(self, 节点: '条件节点') -> Any:
        ...
    
    def 访问块节点(self, 节点: '块节点') -> Any:
        ...
    
    def 访问关键字词法单元(self, 节点: '关键字词法单元') -> Any:
        ...
    
    def 访问字面量节点(self, 节点: '字面量节点') -> Any:
        ...
    
    def 访问标识符节点(self, 节点: '标识符节点') -> Any:
        ...
    
    def 访问二元表达式节点(self, 节点: '二元表达式节点') -> Any:
        ...
    
    def 访问一元表达式节点(self, 节点: '一元表达式节点') -> Any:
        ...
    
    def 访问函数调用节点(self, 节点: '函数调用节点') -> Any:
        ...


import dataclasses


class 递归数据类型基类:
    """所有递归数据类型的基类 - 支持访问者模式"""
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        """访问者模式：允许外部遍历数据结构"""
        raise NotImplementedError(f"{self.__class__.__name__} 未实现接受访问者方法")
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        """遍历数据结构的所有节点"""
        raise NotImplementedError(f"{self.__class__.__name__} 未实现遍历方法")


# ============ 词法单元代数数据类型 ============

@dataclass(frozen=True)
class 词法单元基类(递归数据类型基类):
    """词法单元ADT基类 - 不可变"""
    行号: int
    列号: int
    位置: int
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        raise NotImplementedError()
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)


@dataclass(frozen=True)
class 关键字词法单元(词法单元基类):
    """关键字词法单元"""
    值: str  # "循环", "验证", "持久化", "调用AI", "如果", "否则", "结束"
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问关键字词法单元(self)


@dataclass(frozen=True)
class 标识符词法单元(词法单元基类):
    """标识符词法单元"""
    值: str  # 变量名、函数名等


@dataclass(frozen=True)
class 数字词法单元(词法单元基类):
    """数字词法单元"""
    值: int


@dataclass(frozen=True)
class 浮点数词法单元(词法单元基类):
    """浮点数词法单元"""
    值: float


@dataclass(frozen=True)
class 字符串词法单元(词法单元基类):
    """字符串词法单元"""
    值: str


@dataclass(frozen=True)
class 运算符词法单元(词法单元基类):
    """运算符词法单元"""
    值: str  # "+", "-", "==", "!=", ">", "<", "<=", ">=", "&&", "||"


@dataclass(frozen=True)
class 分隔符词法单元(词法单元基类):
    """分隔符词法单元"""
    值: str  # ":", ";", "(", ")", "{", "}", "[", "]"


@dataclass(frozen=True)
class 文件结束词法单元(词法单元基类):
    """文件结束词法单元"""
    pass


@dataclass(frozen=True)
class 注释词法单元(词法单元基类):
    """注释词法单元"""
    内容: str


# 词法单元联合类型
词法单元 = Union[
    关键字词法单元,
    标识符词法单元,
    数字词法单元,
    浮点数词法单元,
    字符串词法单元,
    运算符词法单元,
    分隔符词法单元,
    文件结束词法单元,
    注释词法单元
]


# ============ 抽象语法树代数数据类型 ============

@dataclass
class AST节点基类(递归数据类型基类):
    """AST节点ADT基类"""
    位置信息: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.位置信息 is None:
            self.位置信息 = {"行号": 0, "列号": 0}
        if not hasattr(self, '假分支'):
            self.假分支 = None
        if not hasattr(self, '条件表达式'):
            self.条件表达式 = None
    
    def 获取行号(self) -> int:
        """获取行号"""
        return self.位置信息.get("行号", 0)
    
    def 获取列号(self) -> int:
        """获取列号"""
        return self.位置信息.get("列号", 0)
    
    def 设置位置(self, 行号: int, 列号: int):
        """设置位置信息"""
        self.位置信息 = {"行号": 行号, "列号": 列号}


@dataclass
class 程序节点(AST节点基类):
    """程序根节点"""
    语句列表: List[AST节点基类] = field(default_factory=list)
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问程序节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        for 语句 in self.语句列表:
            语句.遍历(处理函数)


@dataclass
class 循环节点(AST节点基类):
    """循环语句节点"""
    循环次数: AST节点基类 = None
    循环体: '块节点' = None
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问循环节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        if self.循环次数:
            self.循环次数.遍历(处理函数)
        if self.循环体:
            self.循环体.遍历(处理函数)


@dataclass
class 验证节点(AST节点基类):
    """验证语句节点"""
    验证命令: AST节点基类 = None
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问验证节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        self.验证命令.遍历(处理函数)


@dataclass
class 持久化节点(AST节点基类):
    """持久化语句节点"""
    路径表达式: AST节点基类 = None
    数据表达式: AST节点基类 = None
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问持久化节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        if self.路径表达式:
            self.路径表达式.遍历(处理函数)
        if self.数据表达式:
            self.数据表达式.遍历(处理函数)


@dataclass
class AI调用节点(AST节点基类):
    """AI调用语句节点"""
    参数表达式: AST节点基类 = None
    任务描述: AST节点基类 = None
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问AI调用节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        self.任务描述.遍历(处理函数)
        if self.参数表达式:
            self.参数表达式.遍历(处理函数)


@dataclass
class 条件节点(AST节点基类):
    """条件语句节点"""
    真分支: '块节点' = None
    假分支: '块节点' = None
    条件表达式: AST节点基类 = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.条件表达式 is None and self.假分支 is None:
            # 兼容旧用法
            pass
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问条件节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        self.条件表达式.遍历(处理函数)
        self.真分支.遍历(处理函数)
        if self.假分支:
            self.假分支.遍历(处理函数)


@dataclass
class 块节点(AST节点基类):
    """块语句节点 - 包含多个语句"""
    语句列表: List[AST节点基类] = field(default_factory=list)
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问块节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        for 语句 in self.语句列表:
            语句.遍历(处理函数)


@dataclass
class 表达式节点基类(AST节点基类):
    """表达式节点ADT基类"""
    期望类型: str = ""
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        raise NotImplementedError()


@dataclass
class 字面量节点(表达式节点基类):
    """字面量表达式节点"""
    值: Any = None
    类型: str = ""  # "整数", "浮点数", "字符串", "布尔值"
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问字面量节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)


@dataclass
class 标识符节点(表达式节点基类):
    """标识符表达式节点"""
    名称: str = ""
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问标识符节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)


@dataclass
class 二元表达式节点(表达式节点基类):
    """二元表达式节点"""
    左表达式: 表达式节点基类 = None
    运算符: str = ""
    右表达式: 表达式节点基类 = None
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问二元表达式节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        if self.左表达式:
            self.左表达式.遍历(处理函数)
        if self.右表达式:
            self.右表达式.遍历(处理函数)


@dataclass
class 一元表达式节点(表达式节点基类):
    """一元表达式节点"""
    运算符: str = ""
    表达式: 表达式节点基类 = None
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问一元表达式节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        if self.表达式:
            self.表达式.遍历(处理函数)


@dataclass
class 函数调用节点(表达式节点基类):
    """函数调用表达式节点"""
    函数名: str = ""
    参数列表: List[表达式节点基类] = field(default_factory=list)
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问函数调用节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        for 参数 in self.参数列表:
            参数.遍历(处理函数)


@dataclass
class 赋值节点(AST节点基类):
    """赋值语句节点"""
    变量名: str = ""
    值表达式: 表达式节点基类 = None
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问赋值节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        self.值表达式.遍历(处理函数)


@dataclass
class 变量声明节点(AST节点基类):
    """变量声明节点"""
    变量名: str = ""
    类型: str = ""
    初始值: 表达式节点基类 = None
    
    def 接受访问者(self, 访问者: 访问者协议) -> Any:
        return 访问者.访问变量声明节点(self)
    
    def 遍历(self, 处理函数: Callable[[Any], None]):
        处理函数(self)
        if self.初始值:
            self.初始值.遍历(处理函数)


# 表达式节点类型
表达式节点 = Union[
    字面量节点,
    标识符节点,
    二元表达式节点,
    一元表达式节点,
    函数调用节点
]

# 语句节点类型
语句节点 = Union[
    变量声明节点,
    赋值节点,
    循环节点,
    验证节点,
    持久化节点,
    AI调用节点,
    条件节点,
    块节点,
    函数调用节点
]


# ============ 栈机指令类型 ============

@dataclass
class 指令:
    """栈机指令"""
    操作码: str
    操作数: Any = None
    
    def __repr__(self):
        if self.操作数 is not None:
            return f"指令({self.操作码}, {self.操作数!r})"
        return f"指令({self.操作码})"


# 指令联合类型
指令类型 = Union[
    指令
]
