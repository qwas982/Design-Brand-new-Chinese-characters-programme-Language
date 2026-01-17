"""
栈机核心模块 - 纯栈式虚拟机实现
本模块实现基于栈操作的虚拟机，执行编译生成的指令序列

设计原则：
1. 所有操作都通过栈进行
2. 指令集简单、正交
3. 异常处理通过栈管理
4. 状态完全由栈内容决定
"""

from typing import List, Any, Optional, Dict, Callable
from dataclasses import dataclass, field

from 异常处理 import (
    异常处理中心, 错误节点, 错误类型, 错误级别,
    运行时异常, 除零异常, 内存访问异常, 栈操作异常, 未知指令异常
)
from 代数数据类型ADT import 指令


@dataclass
class 栈机状态:
    """栈机运行状态快照"""
    程序计数器: int = 0
    操作数栈深度: int = 0
    调用栈深度: int = 0
    运行标志: bool = True
    异常标志: bool = False
    当前异常信息: str = ""


class 纯栈机虚拟机:
    """
    纯栈机虚拟机 - 无寄存器，完全基于栈操作
    
    架构：
    1. 操作数栈：存储计算中间结果
    2. 调用栈：存储函数调用信息（返回地址、局部变量）
    3. 异常处理栈：存储异常处理上下文
    4. 指令存储器：存储程序指令
    5. 堆内存：存储变量和对象
    """
    
    def __init__(self, 内存大小: int = 65536):
        # 核心栈结构
        self.操作数栈: List[Any] = []          # 存储操作数和中间结果
        self.调用栈: List[Dict] = []            # 存储返回地址和局部变量
        self.异常处理栈: List[Dict] = []        # 存储异常处理上下文
        
        # 内存和状态
        self.指令存储器: List[指令] = []        # 程序指令
        self.堆内存: bytearray = bytearray(内存大小)  # 堆内存
        self.程序计数器: int = 0                 # 当前指令位置
        self.栈帧指针: int = 0                   # 当前栈帧在调用栈中的位置
        self.堆指针: int = 0                     # 堆分配指针
        
        # 运行状态
        self.运行标志: bool = True
        self.异常标志: bool = False
        self.当前异常信息: str = ""
        
        # 性能统计
        self.指令计数: int = 0
        self.栈最大深度: int = 0
        self.运行时长: float = 0.0
        
        # 异常处理
        self.异常处理中心 = 异常处理中心()
        
        # 调试支持
        self.调试模式: bool = False
        self.断点集合: set = set()
        self.单步模式: bool = False
    
    def 加载程序(self, 指令序列: List[指令]):
        """加载程序到指令存储器"""
        self.指令存储器 = list(指令序列)  # 复制一份
        self.程序计数器 = 0
        self.运行标志 = True
        self.异常标志 = False
        self.当前异常信息 = ""
        self.指令计数 = 0
        print(f"程序已加载，共 {len(指令序列)} 条指令")
    
    def 运行(self):
        """运行程序 - 主执行循环"""
        import time
        开始时间 = time.time()
        
        print(f"开始执行程序，指令数: {len(self.指令存储器)}")
        
        while self.运行标志 and self.程序计数器 < len(self.指令存储器):
            # 检查是否需要暂停（如断点、单步）
            if self.需要暂停():
                self.处理暂停()
            
            if not self.运行标志:
                break
            
            # 执行单条指令
            self.执行单条指令()
            
            # 更新性能统计
            self.指令计数 += 1
            self.栈最大深度 = max(self.栈最大深度, len(self.操作数栈))
        
        self.运行时长 = time.time() - 开始时间
        
        # 输出运行统计
        self.输出运行统计()
    
    def 需要暂停(self) -> bool:
        """检查是否需要暂停执行"""
        # 断点检查
        if self.调试模式 and self.程序计数器 in self.断点集合:
            return True
        # 单步模式检查
        if self.单步模式:
            return True
        return False
    
    def 处理暂停(self):
        """处理暂停（断点或单步）"""
        print(f"\n暂停在指令 {self.程序计数器}: {self.指令存储器[self.程序计数器]}")
        print(f"  操作数栈: {self.操作数栈[-5:] if len(self.操作数栈) > 5 else self.操作数栈}")
        print(f"  调用栈深度: {len(self.调用栈)}")
        
        # 进入调试循环
        while True:
            命令 = input("(调试) ").strip().lower()
            
            if 命令 in ['c', 'continue', 'run']:
                self.调试模式 = False
                self.单步模式 = False
                break
            elif 命令 in ['s', 'step']:
                self.单步模式 = True
                break
            elif 命令 in ['p', 'print']:
                print(f"  操作数栈: {self.操作数栈}")
            elif 命令 in ['q', 'quit']:
                self.运行标志 = False
                break
            else:
                print("可用命令: c(continue), s(step), p(print), q(quit)")
    
    def 执行单条指令(self):
        """执行单条指令"""
        if self.程序计数器 >= len(self.指令存储器):
            return
        
        指令 = self.指令存储器[self.程序计数器]
        
        try:
            # 使用模式匹配处理不同指令
            self._执行指令(指令)
        except Exception as 执行异常:
            self.触发异常(f"指令执行异常: {执行异常}")
        
        # 如果没有异常，继续执行
        if not self.异常标志:
            self.程序计数器 += 1
    
    def _执行指令(self, 指令: 指令):
        """根据指令类型执行对应操作"""
        操作码 = 指令.操作码
        
        # 算术指令
        if 操作码 == "推入":
            self.执行推入指令(指令)
        elif 操作码 == "弹出":
            self.执行弹出指令(指令)
        elif 操作码 == "加法":
            self.执行二元算术指令(lambda a, b: a + b, "加法")
        elif 操作码 == "减法":
            self.执行二元算术指令(lambda a, b: a - b, "减法")
        elif 操作码 == "乘法":
            self.执行二元算术指令(lambda a, b: a * b, "乘法")
        elif 操作码 == "除法":
            self.执行除法指令()
        elif 操作码 == "取模":
            self.执行二元算术指令(lambda a, b: a % b if b != 0 else self.触发异常("除零错误"), "取模")
        
        # 比较指令
        elif 操作码 == "等于":
            self.执行比较指令(lambda a, b: a == b)
        elif 操作码 == "不等于":
            self.执行比较指令(lambda a, b: a != b)
        elif 操作码 == "大于":
            self.执行比较指令(lambda a, b: a > b)
        elif 操作码 == "小于":
            self.执行比较指令(lambda a, b: a < b)
        elif 操作码 == "大于等于":
            self.执行比较指令(lambda a, b: a >= b)
        elif 操作码 == "小于等于":
            self.执行比较指令(lambda a, b: a <= b)
        
        # 跳转指令
        elif 操作码 == "跳转":
            self.执行跳转指令(指令)
        elif 操作码 == "条件跳转":
            self.执行条件跳转指令(指令)
        
        # 函数调用指令
        elif 操作码 == "调用":
            self.执行调用指令(指令)
        elif 操作码 == "返回":
            self.执行返回指令()
        
        # 内存指令
        elif 操作码 == "加载":
            self.执行加载指令(指令)
        elif 操作码 == "存储":
            self.执行存储指令(指令)
        
        # 标签指令
        elif 操作码 == "标签":
            pass  # 标签不执行
        
        # 外部调用指令
        elif 操作码 == "调用外部":
            self.执行外部调用指令(指令)
        
        # 栈操作指令
        elif 操作码 == "复制栈顶":
            if self.操作数栈:
                self.操作数栈.append(self.操作数栈[-1])
        elif 操作码 == "交换":
            if len(self.操作数栈) >= 2:
                self.操作数栈[-1], self.操作数栈[-2] = self.操作数栈[-2], self.操作数栈[-1]
        
        # 特殊指令
        elif 操作码 == "停机":
            self.运行标志 = False
        elif 操作码 == "打印":
            if self.操作数栈:
                print(self.操作数栈.pop())
        elif 操作码 == "调试信息":
            self.输出调试信息()
        
        else:
            self.触发异常(f"未知指令: {操作码}")
    
    def 执行推入指令(self, 指令: 指令):
        """执行推入指令：将值推入操作数栈"""
        self.操作数栈.append(指令.操作数)
    
    def 执行弹出指令(self, 指令: 指令 = None) -> Any:
        """执行弹出指令：从操作数栈弹出值"""
        if self.操作数栈:
            return self.操作数栈.pop()
        else:
            self.触发异常("操作数栈下溢")
            return None
    
    def 执行二元算术指令(self, 操作函数: Callable, 指令名称: str):
        """执行二元算术指令：弹出两个操作数，计算结果并推回"""
        if len(self.操作数栈) < 2:
            self.触发异常(f"{指令名称}操作数不足")
            return
        
        右操作数 = self.操作数栈.pop()
        左操作数 = self.操作数栈.pop()
        
        try:
            结果 = 操作函数(左操作数, 右操作数)
            self.操作数栈.append(结果)
        except Exception as 算术异常:
            self.触发异常(f"{指令名称}运算错误: {算术异常}")
    
    def 执行除法指令(self):
        """执行除法指令 - 特殊处理除零情况"""
        if len(self.操作数栈) < 2:
            self.触发异常("除法操作数不足")
            return
        
        右操作数 = self.操作数栈.pop()
        左操作数 = self.操作数栈.pop()
        
        if 右操作数 == 0:
            self.触发异常("除零错误")
            # 推入默认值（根据恢复策略）
            恢复策略 = self.异常处理中心.获取恢复策略("除零错误")
            if 恢复策略 == "返回默认值":
                self.操作数栈.append(0)
            return
        
        try:
            结果 = 左操作数 / 右操作数
            self.操作数栈.append(结果)
        except Exception as 除法异常:
            self.触发异常(f"除法运算错误: {除法异常}")
    
    def 执行比较指令(self, 比较函数: Callable[[Any, Any], bool]):
        """执行比较指令：弹出两个操作数，比较结果推回"""
        if len(self.操作数栈) < 2:
            self.触发异常("比较操作数不足")
            return
        
        右操作数 = self.操作数栈.pop()
        左操作数 = self.操作数栈.pop()
        
        结果 = 比较函数(左操作数, 右操作数)
        self.操作数栈.append(1 if 结果 else 0)
    
    def 执行跳转指令(self, 指令: 指令):
        """执行无条件跳转"""
        目标标签 = 指令.操作数
        目标地址 = self.查找标签地址(目标标签)
        
        if 目标地址 is not None:
            self.程序计数器 = 目标地址
        else:
            self.触发异常(f"未找到标签: {目标标签}")
    
    def 执行条件跳转指令(self, 指令: 指令):
        """执行条件跳转：检查栈顶值决定是否跳转"""
        if not self.操作数栈:
            self.触发异常("条件跳转操作数栈为空")
            return
        
        条件 = self.操作数栈.pop()
        目标标签 = 指令.操作数
        
        if 条件:
            目标地址 = self.查找标签地址(目标标签)
            if 目标地址 is not None:
                self.程序计数器 = 目标地址
    
    def 执行调用指令(self, 指令: 指令):
        """执行函数调用：保存返回地址，跳转到目标"""
        # 保存返回地址到调用栈
        调用帧 = {
            "返回地址": self.程序计数器 + 1,
            "栈帧指针": self.栈帧指针,
            "局部变量": {}
        }
        self.调用栈.append(调用帧)
        
        # 设置新的栈帧指针
        self.栈帧指针 = len(self.调用栈) - 1
        
        # 跳转到函数入口
        目标地址 = self.查找标签地址(指令.操作数)
        if 目标地址 is not None:
            self.程序计数器 = 目标地址
        else:
            self.触发异常(f"未找到函数入口: {指令.操作数}")
    
    def 执行返回指令(self):
        """从函数返回：恢复调用者上下文"""
        if not self.调用栈:
            self.触发异常("调用栈为空")
            return
        
        # 获取返回信息
        调用帧 = self.调用栈.pop()
        返回地址 = 调用帧["返回地址"]
        之前栈帧指针 = 调用帧["栈帧指针"]
        
        # 恢复程序计数器和栈帧指针
        self.程序计数器 = 返回地址
        self.栈帧指针 = 之前栈帧指针
    
    def 执行加载指令(self, 指令: 指令):
        """从内存加载值到操作数栈"""
        地址 = 指令.操作数
        
        if not isinstance(地址, int):
            self.触发异常(f"无效的内存地址: {地址}")
            return
        
        if 0 <= 地址 < len(self.堆内存):
            # 从堆内存加载值（假设存储4字节整数）
            if 地址 + 4 <= len(self.堆内存):
                值 = int.from_bytes(self.堆内存[地址:地址+4], 'little', signed=True)
                self.操作数栈.append(值)
            else:
                self.触发异常(f"内存读取越界: {地址}")
        else:
            self.触发异常(f"内存地址越界: {地址}")
    
    def 执行存储指令(self, 指令: 指令):
        """将操作数栈顶值存储到内存"""
        if not self.操作数栈:
            self.触发异常("存储操作数栈为空")
            return
        
        值 = self.操作数栈.pop()
        地址 = 指令.操作数
        
        if not isinstance(地址, int):
            self.触发异常(f"无效的内存地址: {地址}")
            self.操作数栈.append(值)  # 恢复栈
            return
        
        if 0 <= 地址 < len(self.堆内存):
            # 存储值到堆内存（假设存储4字节整数）
            if 地址 + 4 <= len(self.堆内存):
                字节值 = int(值).to_bytes(4, 'little', signed=True)
                self.堆内存[地址:地址+4] = 字节值
            else:
                self.触发异常(f"内存写入越界: {地址}")
        else:
            self.触发异常(f"内存地址越界: {地址}")
    
    def 执行外部调用指令(self, 指令: 指令):
        """执行外部函数调用"""
        函数名 = 指令.操作数
        
        if 函数名 == "验证器":
            self._执行验证器调用()
        elif 函数名 == "持久化器":
            self._执行持久化器调用()
        elif 函数名 == "AI调用器":
            self._执行AI调用器调用()
        else:
            self.触发异常(f"未知外部函数: {函数名}")
    
    def _执行验证器调用(self):
        """执行验证器外部调用"""
        if len(self.操作数栈) < 1:
            self.触发异常("验证命令参数不足")
            return
        
        验证命令 = self.操作数栈.pop()
        
        try:
            import subprocess
            结果 = subprocess.run(
                验证命令, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=60
            )
            
            # 将验证结果推入栈
            成功 = 结果.returncode == 0
            self.操作数栈.append(1 if 成功 else 0)
            if 结果.stdout:
                print(f"验证输出: {结果.stdout[:100]}")
        except Exception as 执行异常:
            self.触发异常(f"验证执行失败: {执行异常}")
            self.操作数栈.append(0)
    
    def _执行持久化器调用(self):
        """执行持久化器调用"""
        if len(self.操作数栈) < 2:
            self.触发异常("持久化参数不足")
            return
        
        路径 = self.操作数栈.pop()
        数据 = self.操作数栈.pop()
        
        try:
            import json
            with open(str(路径), 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            self.操作数栈.append(1)  # 成功
        except Exception as 持久化异常:
            self.触发异常(f"持久化失败: {持久化异常}")
            self.操作数栈.append(0)
    
    def _执行AI调用器调用(self):
        """执行AI调用器调用"""
        if len(self.操作数栈) < 1:
            self.触发异常("AI调用参数不足")
            return
        
        提示词 = self.操作数栈.pop()
        
        try:
            from 拉尔夫原语 import 创建AI调用器
            AI调用器 = 创建AI调用器("模拟")
            结果 = AI调用器.调用(提示词)
            
            if 结果["成功"]:
                self.操作数栈.append(1)
                # 可选：将响应也推入栈
            else:
                self.操作数栈.append(0)
        except ImportError:
            self.操作数栈.append(0)
        except Exception as AI异常:
            self.触发异常(f"AI调用失败: {AI异常}")
            self.操作数栈.append(0)
    
    def 查找标签地址(self, 标签名: str) -> Optional[int]:
        """查找标签对应的指令地址"""
        for 地址, 指令 in enumerate(self.指令存储器):
            if 指令.操作码 == "标签" and 指令.操作数 == 标签名:
                return 地址
        return None
    
    def 触发异常(self, 异常信息: str):
        """触发异常：设置异常标志和异常信息"""
        self.异常标志 = True
        self.当前异常信息 = 异常信息
        
        # 记录异常
        self.异常处理中心.创建错误节点(
            错误信息=异常信息,
            行号=self.程序计数器,
            列号=0,
            错误类型=错误类型.运行时错误,
            严重程度=错误级别.错误
        )
        
        # 保存异常上下文到异常处理栈
        异常上下文 = {
            "异常信息": 异常信息,
            "程序计数器": self.程序计数器,
            "操作数栈快照": list(self.操作数栈),
            "调用栈深度": len(self.调用栈)
        }
        self.异常处理栈.append(异常上下文)
        
        # 尝试查找异常处理程序
        self.处理异常()
    
    def 处理异常(self):
        """异常处理：查找异常处理程序并跳转"""
        if not self.异常处理栈:
            # 没有异常处理程序，终止执行
            self.运行标志 = False
            print(f"未处理的异常: {self.当前异常信息}")
            return
        
        # 获取最近的异常上下文
        异常上下文 = self.异常处理栈[-1]
        
        # 查找异常处理程序
        处理程序地址 = self.异常处理中心.查找异常处理程序(异常上下文["异常信息"])
        
        if 处理程序地址 is not None and 处理程序地址 > 0:
            # 跳转到异常处理程序
            self.程序计数器 = 处理程序地址
            self.异常标志 = False
            self.当前异常信息 = ""
        else:
            # 没有找到处理程序，弹出异常上下文
            self.异常处理栈.pop()
            
            # 如果没有更多异常处理上下文，终止
            if not self.异常处理栈:
                self.运行标志 = False
                print(f"未处理的异常: {异常上下文['异常信息']}")
    
    def 输出运行统计(self):
        """输出运行统计信息"""
        print(f"\n程序执行完成")
        print(f"  执行指令数: {self.指令计数}")
        print(f"  最大栈深度: {self.栈最大深度}")
        print(f"  运行时长: {self.运行时长:.4f}秒")
        
        if self.异常标志:
            print(f"  异常: {self.当前异常信息}")
    
    def 输出调试信息(self):
        """输出调试信息"""
        print(f"\n调试信息:")
        print(f"  程序计数器: {self.程序计数器}")
        print(f"  指令计数: {self.指令计数}")
        print(f"  操作数栈: {self.操作数栈}")
        print(f"  调用栈帧数: {len(self.调用栈)}")
        print(f"  异常栈深度: {len(self.异常处理栈)}")
    
    def 获取状态(self) -> 栈机状态:
        """获取当前状态快照"""
        return 栈机状态(
            程序计数器=self.程序计数器,
            操作数栈深度=len(self.操作数栈),
            调用栈深度=len(self.调用栈),
            运行标志=self.运行标志,
            异常标志=self.异常标志,
            当前异常信息=self.当前异常信息
        )


# ============ 便捷函数 ============

def 创建栈机(内存大小: int = 65536) -> 纯栈机虚拟机:
    """创建栈机实例"""
    return 纯栈机虚拟机(内存大小)


# ============ 测试代码 ============

if __name__ == "__main__":
    print("测试栈机核心")
    print("=" * 60)
    
    栈机 = 创建栈机()
    
    # 创建测试程序
    测试指令序列 = [
        指令("推入", 10),
        指令("推入", 20),
        指令("加法"),
        指令("推入", 5),
        指令("除法"),
        指令("打印"),
    ]
    
    print("测试程序:")
    for i, 指令 in enumerate(测试指令序列):
        print(f"  {i}: {指令}")
    
    print("\n执行:")
    栈机.加载程序(测试指令序列)
    栈机.运行()
