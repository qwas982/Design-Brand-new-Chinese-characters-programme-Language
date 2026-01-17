"""
完整工作流模块 - 端到端的编译执行流程
本模块整合编译器、虚拟机、调试器，提供完整的工作流程演示

工作流程：
1. 编写DSL程序
2. 编译为指令序列
3. 在虚拟机中执行
4. 监控和调试
"""

import json
import os
from typing import List, Dict, Any, Optional

from 异常处理 import 异常处理中心, 错误节点
from 代数数据类型ADT import 可选, 指令
from 编译管道 import 拉尔夫编译管道, 编译管道配置
from 栈机核心 import 纯栈机虚拟机, 创建栈机
from 集成调试器 import 拉尔夫集成调试器, 创建调试器
from 拉尔夫原语 import 创建验证器, 创建状态管理器, 创建AI调用器


class 完整工作流:
    """
    完整的拉尔夫·韦根系统工作流
    整合编译器、虚拟机、调试器和异常处理
    """
    
    def __init__(self, 配置: Dict[str, Any] = None):
        # 默认配置
        self.配置 = 配置 or {
            "优化级别": 1,
            "调试模式": False,
            "安全模式": True,
            "最大迭代次数": 1000,
            "内存大小": 65536
        }
        
        # 核心组件
        self.编译管道 = 拉尔夫编译管道(
            编译管道配置(
                是否启用优化=self.配置["优化级别"] > 0,
                优化级别=self.配置["优化级别"]
            )
        )
        self.虚拟机 = 创建栈机()
        self.调试器 = None
        
        # 运行时状态
        self.当前程序: Optional[List[指令]] = None
        self.编译结果: Optional[List[指令]] = None
        self.执行结果: Dict[str, Any] = {}
    
    def 编译程序(self, 源代码: str) -> bool:
        """
        编译源代码
        
        参数:
            源代码: DSL源代码字符串
        
        返回:
            编译是否成功
        """
        print("=" * 60)
        print("步骤1: 编译DSL程序")
        print("=" * 60)
        
        # 执行编译
        self.编译结果 = self.编译管道.编译(源代码)
        
        if self.编译结果.是空():
            print("\n编译失败:")
            for 错误 in self.编译管道.获取错误列表():
                print(f"  行{错误.行号}, 列{错误.列号}: {错误.错误信息}")
            return False
        
        # 成功
        self.当前程序 = self.编译结果.获取值()
        print(f"\n编译成功，生成 {len(self.当前程序)} 条指令")
        return True
    
    def 准备执行环境(self):
        """准备执行环境"""
        # 加载原语模块
        print("\n准备执行环境...")
        
        # 重置虚拟机
        self.虚拟机 = 创建栈机(内存大小=self.配置["内存大小"])
        
        # 如果需要调试模式，创建调试器
        if self.配置["调试模式"]:
            self.调试器 = 创建调试器(self.虚拟机)
            self.虚拟机.调试模式 = True
            print("✓ 调试器已启用")
    
    def 执行程序(self, 调试模式: bool = False) -> Dict[str, Any]:
        """
        执行编译好的程序
        
        参数:
            调试模式: 是否启用调试模式
        
        返回:
            执行结果字典
        """
        if not self.当前程序:
            return {"成功": False, "错误": "没有可执行的程序"}
        
        print("\n" + "=" * 60)
        print("步骤2: 在虚拟机中执行")
        print("=" * 60)
        
        # 准备执行环境
        self.准备执行环境()
        
        # 加载程序
        self.虚拟机.加载程序(self.当前程序)
        
        # 选择执行模式
        if 调试模式 or self.配置["调试模式"]:
            return self._调试执行()
        else:
            return self._普通执行()
    
    def _普通执行(self) -> Dict[str, Any]:
        """普通执行模式"""
        print("\n开始执行程序...")
        
        # 直接执行
        self.虚拟机.运行()
        
        # 获取结果
        return self._获取执行结果()
    
    def _调试执行(self) -> Dict[str, Any]:
        """调试执行模式"""
        if not self.调试器:
            self.调试器 = 创建调试器(self.虚拟机)
        
        print("\n进入调试模式")
        print("可用命令: run, step, next, finish, break, delete, list, watch, print, info, quit")
        
        # 启动交互式调试
        self.调试器.启动交互式调试()
        
        return self._获取执行结果()
    
    def _获取执行结果(self) -> Dict[str, Any]:
        """获取程序执行结果"""
        执行结果 = {
            "成功": self.虚拟机.运行标志 or self.虚拟机.指令计数 > 0,
            "执行状态": "正常结束" if not self.虚拟机.异常标志 else "异常结束",
            "执行指令数": self.虚拟机.指令计数,
            "最终栈状态": list(self.虚拟机.操作数栈),
            "最终栈深度": len(self.虚拟机.操作数栈),
            "内存使用": len(self.虚拟机.堆内存),
            "异常信息": self.虚拟机.当前异常信息,
            "性能统计": {
                "栈最大深度": self.虚拟机.栈最大深度,
                "调用栈最大深度": len(self.虚拟机.调用栈),
                "运行时长": self.虚拟机.运行时长
            }
        }
        
        self.执行结果 = 执行结果
        return 执行结果
    
    def 生成执行报告(self) -> Dict[str, Any]:
        """生成执行报告"""
        报告 = {
            "程序信息": {
                "生成指令数": len(self.当前程序) if self.当前程序 else 0,
                "优化级别": self.配置["优化级别"]
            },
            "执行结果": self.执行结果,
            "编译报告": self.编译管道.生成编译报告() if self.编译管道 else {}
        }
        return 报告
    
    def 保存报告(self, 文件路径: str = "执行报告.json"):
        """保存执行报告"""
        报告 = self.生成执行报告()
        
        with open(文件路径, 'w', encoding='utf-8') as f:
            json.dump(报告, f, ensure_ascii=False, indent=2)
        
        print(f"\n报告已保存到: {文件路径}")
        return 报告


def 完整工作流示例():
    """演示完整的工作流程"""
    
    print("=" * 60)
    print("拉尔夫·韦根编译器工作流演示")
    print("=" * 60)
    
    # 1. 编写DSL程序
    DSL程序 = """
循环 3 次:
    验证 "python -c 'print(\"测试通过\")'"
    
    如果 验证通过:
        持久化 "./测试结果.json"
        调用AI "测试成功，请分析日志"
    否则:
        调用AI "测试失败，需要调试"
    结束
    
    调用AI "执行下一个测试用例"
结束
"""
    
    print("源代码:")
    print(DSL程序)
    print("=" * 60)
    
    # 2. 创建工作流
    工作流 = 完整工作流(配置={
        "优化级别": 1,
        "调试模式": False,
        "内存大小": 65536
    })
    
    # 3. 编译程序
    if not 工作流.编译程序(DSL程序):
        return
    
    # 4. 执行程序
    执行结果 = 工作流.执行程序(调试模式=False)
    
    # 5. 输出结果
    print("\n" + "=" * 60)
    print("执行结果")
    print("=" * 60)
    print(f"执行状态: {执行结果['执行状态']}")
    print(f"执行指令数: {执行结果['执行指令数']}")
    print(f"最终栈深度: {执行结果['最终栈深度']}")
    print(f"栈最大深度: {执行结果['性能统计']['栈最大深度']}")
    print(f"运行时长: {执行结果['性能统计']['运行时长']:.4f}秒")
    
    if 执行结果.get("异常信息"):
        print(f"异常信息: {执行结果['异常信息']}")
    
    # 6. 保存报告
    工作流.保存报告()


class 拉尔夫韦根系统:
    """
    完整的拉尔夫·韦根系统集成
    整合编译器、虚拟机、调试器和异常处理
    """
    
    def __init__(self):
        self.编译管道 = 拉尔夫编译管道()
        self.虚拟机 = None
        self.调试器 = None
        
        # 系统配置
        self.配置 = {
            "优化级别": 1,
            "调试模式": True,
            "安全模式": True,
            "最大迭代次数": 1000,
            "内存大小": 65536
        }
        
        # 运行时状态
        self.当前程序 = None
        self.编译结果 = None
        self.执行结果 = None
    
    def 编译程序(self, 源代码: str) -> bool:
        """编译源代码"""
        print("开始编译程序...")
        
        # 配置编译管道
        self.编译管道 = 拉尔夫编译管道(
            编译管道配置(
                是否启用优化=self.配置["优化级别"] > 0,
                优化级别=self.配置["优化级别"]
            )
        )
        
        # 执行编译
        self.编译结果 = self.编译管道.编译(源代码)
        
        # 检查结果
        if self.编译结果.是空():
            print("编译失败")
            for 错误 in self.编译管道.获取错误列表():
                print(f"错误: {错误.错误信息} (行{错误.行号}, 列{错误.列号})")
            return False
        
        self.当前程序 = self.编译结果.获取值()
        print(f"编译成功，生成 {len(self.当前程序)} 条指令")
        return True
    
    def 执行程序(self, 调试模式: bool = False) -> Any:
        """执行编译好的程序"""
        if not self.当前程序:
            print("错误: 没有可执行的程序")
            return None
        
        print("开始执行程序...")
        
        # 创建虚拟机
        self.虚拟机 = 创建栈机(内存大小=self.配置["内存大小"])
        
        # 加载程序
        self.虚拟机.加载程序(self.当前程序)
        
        # 初始化调试器（如果需要）
        if 调试模式 or self.配置["调试模式"]:
            self.调试器 = 创建调试器(self.虚拟机)
            
            # 设置初始断点
            if self.配置["调试模式"]:
                self.调试器.设置断点(1)  # 在第一条指令处设置断点
            
            # 进入调试循环
            return self._调试执行()
        else:
            # 直接执行
            self.虚拟机.运行()
            return self._获取执行结果()
    
    def _调试执行(self):
        """调试模式执行"""
        print("进入调试模式")
        print("可用命令: run, step, next, break, watch, print, quit")
        
        while self.虚拟机 and self.虚拟机.运行标志:
            # 显示当前状态
            状态 = self.调试器.生成调试报告()
            print(f"PC={状态['程序计数器']}, 栈深度={状态['操作数栈深度']}")
            
            # 获取用户命令
            命令 = input("(调试) ").strip().lower()
            
            # 解析和执行命令
            if not 命令:
                continue
            
            parts = 命令.split()
            主命令 = parts[0]
            参数 = parts[1:]
            
            if 主命令 in ["run", "r"]:
                self.虚拟机.调试模式 = False
                self.虚拟机.运行()
                break
            elif 主命令 in ["step", "s"]:
                self.调试器.单步执行("step")
            elif 主命令 in ["next", "n"]:
                self.调试器.单步执行("next")
            elif 主命令 in ["break", "b"]:
                if 参数:
                    try:
                        行号 = int(参数[0])
                        self.调试器.设置断点(行号)
                        print(f"断点设置在行 {行号}")
                    except ValueError:
                        print("无效的行号")
            elif 主命令 in ["watch", "w"]:
                if 参数:
                    表达式 = " ".join(参数)
                    self.调试器.添加监视表达式(表达式)
            elif 主命令 in ["print", "p"]:
                if 参数:
                    表达式 = " ".join(参数)
                    try:
                        值 = self.调试器.求值表达式(表达式)
                        print(f"{表达式} = {值}")
                    except Exception as e:
                        print(f"求值失败: {e}")
            elif 主命令 in ["quit", "q"]:
                print("退出调试模式")
                break
            else:
                print("未知命令")
            
            # 检查程序是否结束
            if not self.虚拟机.运行标志:
                print("程序执行结束")
                break
        
        return self._获取执行结果()
    
    def _获取执行结果(self) -> Dict[str, Any]:
        """获取执行结果"""
        if self.虚拟机 is None:
            return {"错误": "虚拟机未初始化"}
        
        # 计算调用栈最大深度
        调用栈最大深度 = 0
        try:
            调用栈最大深度 = len(self.虚拟机.调用栈)
        except:
            pass
        
        return {
            "执行状态": "正常结束" if not self.虚拟机.异常标志 else "异常结束",
            "执行指令数": self.虚拟机.指令计数,
            "最终栈状态": list(self.虚拟机.操作数栈),
            "最终栈深度": len(self.虚拟机.操作数栈),
            "内存使用": len(self.虚拟机.堆内存),
            "异常信息": self.虚拟机.当前异常信息,
            "性能统计": {
                "栈最大深度": self.虚拟机.栈最大深度,
                "调用栈最大深度": 调用栈最大深度
            }
        }
    
    def 获取执行结果(self) -> Dict[str, Any]:
        """获取程序执行结果"""
        return self.执行结果 or {}


# ============ 独立测试 ============

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("完整工作流测试")
    print("=" * 60)
    
    # 运行示例
    完整工作流示例()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
