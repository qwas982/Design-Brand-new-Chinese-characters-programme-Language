"""
集成调试器模块 - 源代码级调试支持
本模块实现集成调试器，支持断点设置、单步执行、变量查看等功能
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from 异常处理 import 异常处理中心, 错误节点, 错误级别
from 代数数据类型ADT import 指令
from 栈机核心 import 纯栈机虚拟机, 栈机状态


@dataclass
class 断点:
    """断点信息"""
    行号: int
    指令地址: int = 0
    条件: str = ""
    命中次数: int = 0
    已启用: bool = True
    
    def 应该触发(self, 上下文) -> bool:
        """检查断点是否应该触发"""
        if not self.已启用:
            return False
        
        if not self.条件:
            return True
        
        # 条件求值（简化版）
        try:
            结果 = eval(self.条件, {"__builtins__": {}}, 上下文)
            return bool(结果)
        except:
            return False


class 调试命令:
    """调试命令常量"""
    继续 = "continue"
    单步 = "step"
    步过 = "next"
    步出 = "finish"
    打印 = "print"
    列表 = "list"
    断点 = "break"
    删除断点 = "delete"
    监视 = "watch"
    信息 = "info"
    帮助 = "help"
    退出 = "quit"


class 拉尔夫集成调试器:
    """
    集成调试器 - 支持源代码级调试
    功能：
    1. 断点设置和管理
    2. 单步执行（步入、步过、步出）
    3. 变量查看和修改
    4. 调用栈查看
    5. 表达式求值
    """
    
    def __init__(
        self, 
        虚拟机: 纯栈机虚拟机 = None,
        调试符号表: Dict[int, Dict] = None
    ):
        self.虚拟机 = 虚拟机 or 创建栈机()
        self.调试符号表 = 调试符号表 or {}
        
        # 断点管理
        self.断点字典: Dict[int, 断点] = {}  # 行号 -> 断点
        self.断点地址映射: Dict[int, int] = {}  # 指令地址 -> 行号
        
        # 监视表达式
        self.监视表达式列表: List[Dict] = []
        
        # 调试状态
        self.调试模式 = False
        self.单步模式 = False
        self.步进类型 = ""
        self.当前函数深度 = 0
        self.目标函数深度 = 0
        
        # 调用栈跟踪
        self.调用栈深度历史: List[int] = []
        
        # 异常处理
        self.异常处理中心 = 异常处理中心()
        
        # 打印配置
        self.最大显示栈深度 = 10
        self.最大显示变量数 = 20
    
    def 设置断点(self, 行号: int, 条件: str = "", 地址: int = None) -> bool:
        """
        设置断点
        
        参数:
            行号: 源代码行号
            条件: 触发条件（可选）
            地址: 断点对应的指令地址（可选）
        
        返回:
            是否设置成功
        """
        if 行号 in self.断点字典:
            # 更新现有断点
            断点 = self.断点字典[行号]
            断点.条件 = 条件
            断点.已启用 = True
        else:
            # 创建新断点
            断点 = 断点(
                行号=行号,
                指令地址=地址 or 0,
                条件=条件
            )
            self.断点字典[行号] = 断点
        
        if 地址:
            self.断点地址映射[地址] = 行号
        
        print(f"✓ 断点设置在行 {行号}" + (f" (条件: {条件})" if 条件 else ""))
        return True
    
    def 删除断点(self, 行号: int) -> bool:
        """删除断点"""
        if 行号 in self.断点字典:
            del self.断点字典[行号]
            # 清理地址映射
            需要删除的地址 = []
            for 地址, 对应行号 in self.断点地址映射.items():
                if 对应行号 == 行号:
                    需要删除的地址.append(地址)
            for 地址 in 需要删除的地址:
                del self.断点地址映射[地址]
            
            print(f"✓ 断点已从行 {行号} 删除")
            return True
        return False
    
    def 列出断点(self):
        """列出所有断点"""
        if not self.断点字典:
            print("没有设置断点")
            return
        
        print("\n断点列表:")
        print("-" * 60)
        print(f"{'行号':<8} {'地址':<8} {'条件':<30} {'命中':<8}")
        print("-" * 60)
        
        for 行号, 断点 in sorted(self.断点字典.items()):
            状态 = "✓" if 断点.已启用 else "✗"
            条件 = 断点.条件 or "-"
            print(f"{行号:<8} {断点.指令地址:<8} {条件:<30} {断点.命中次数:<8} {状态}")
    
    def 启用断点(self, 行号: int, 启用: bool = True) -> bool:
        """启用或禁用断点"""
        if 行号 in self.断点字典:
            self.断点字典[行号].已启用 = 启用
            状态 = "启用" if 启用 else "禁用"
            print(f"✓ 断点行 {行号} 已{状态}")
            return True
        return False
    
    def 添加监视表达式(self, 表达式: str) -> bool:
        """添加监视表达式"""
        监视项 = {
            "表达式": 表达式,
            "旧值": None,
            "变化次数": 0
        }
        self.监视表达式列表.append(监视项)
        print(f"✓ 已添加监视: {表达式}")
        return True
    
    def 清除所有断点(self):
        """清除所有断点"""
        self.断点字典.clear()
        self.断点地址映射.clear()
        self.监视表达式列表.clear()
        print("✓ 已清除所有断点和监视")
    
    def 单步执行(self, 步进类型: str = "step") -> bool:
        """
        单步执行
        
        步进类型:
            - step: 步入（执行一条指令）
            - next: 步过（执行到函数返回或下一条指令）
            - finish: 步出（执行到当前函数返回）
        """
        self.调试模式 = True
        self.单步模式 = True
        self.步进类型 = 步进类型
        
        # 记录当前调用栈深度
        当前深度 = len(self.虚拟机.调用栈)
        
        if 步进类型 == "step":
            # 步入：执行一条指令
            return self._执行一步()
        
        elif 步进类型 == "next":
            # 步过：执行直到调用栈深度变化
            self.目标函数深度 = 当前深度
            return self._执行直到返回(当前深度)
        
        elif 步进类型 == "finish":
            # 步出：执行直到调用栈深度减少
            self.目标函数深度 = max(0, 当前深度 - 1)
            return self._执行直到返回(self.目标函数深度)
        
        return False
    
    def _执行一步(self) -> bool:
        """执行一步"""
        if not self.虚拟机.运行标志:
            return False
        
        # 执行一条指令
        self.虚拟机.执行单条指令()
        
        # 更新指令计数
        self.虚拟机.指令计数 += 1
        
        # 检查是否需要暂停
        return self.应该暂停()
    
    def _执行直到返回(self, 目标深度: int) -> bool:
        """执行直到达到目标调用栈深度"""
        while (self.虚拟机.运行标志 and 
               self.虚拟机.程序计数器 < len(self.虚拟机.指令存储器)):
            
            # 检查断点
            if self.检查断点():
                return True
            
            # 检查调用栈深度
            当前深度 = len(self.虚拟机.调用栈)
            if 当前深度 <= 目标深度:
                return True
            
            # 执行指令
            self.虚拟机.执行单条指令()
            self.虚拟机.指令计数 += 1
        
        return not self.虚拟机.运行标志
    
    def 运行到下一个断点(self) -> bool:
        """运行到下一个断点"""
        self.调试模式 = True
        self.单步模式 = False
        
        while self.虚拟机.运行标志:
            # 检查是否到达程序末尾
            if self.虚拟机.程序计数器 >= len(self.虚拟机.指令存储器):
                break
            
            # 检查断点
            if self.检查断点():
                return True
            
            # 执行指令
            self.虚拟机.执行单条指令()
            self.虚拟机.指令计数 += 1
        
        return not self.虚拟机.运行标志
    
    def 检查断点(self) -> bool:
        """检查是否到达断点"""
        当前地址 = self.虚拟机.程序计数器
        
        # 检查是否在断点地址
        if 当前地址 in self.断点地址映射:
            行号 = self.断点地址映射[当前地址]
            
            if 行号 in self.断点字典:
                断点 = self.断点字典[行号]
                
                if not 断点.已启用:
                    return False
                
                # 检查条件
                if 断点.条件:
                    上下文 = self._创建调试上下文()
                    if not 断点.应该触发(上下文):
                        return False
                
                # 命中断点
                断点.命中次数 += 1
                return True
        
        return False
    
    def 应该暂停(self) -> bool:
        """检查是否应该暂停执行"""
        # 检查断点
        if self.检查断点():
            return True
        
        # 检查单步模式
        if self.单步模式:
            return True
        
        return False
    
    def 暂停并等待命令(self) -> bool:
        """暂停执行并等待调试命令"""
        if not self.调试模式:
            return False
        
        # 输出当前状态
        self.输出当前状态()
        
        # 检查监视表达式
        self.检查监视表达式()
        
        # 打印提示
        print(f"\n(调试) ", end="")
        
        return True
    
    def _创建调试上下文(self) -> Dict[str, Any]:
        """创建调试上下文（用于条件求值）"""
        return {
            "栈": self.虚拟机.操作数栈,
            "栈深度": len(self.虚拟机.操作数栈),
            "调用栈": self.虚拟机.调用栈,
            "调用栈深度": len(self.虚拟机.调用栈),
            "程序计数器": self.虚拟机.程序计数器,
            "指令计数": self.虚拟机.指令计数,
            "变量": self._获取所有变量()
        }
    
    def _获取所有变量(self) -> Dict[str, Any]:
        """获取所有变量值"""
        变量字典 = {}
        
        # 从符号表获取
        for 变量名 in self.调试符号表:
            变量信息 = self.调试符号表[变量名]
            if "地址" in 变量信息:
                地址 = 变量信息["地址"]
                if 0 <= 地址 < len(self.虚拟机.堆内存):
                    值 = int.from_bytes(
                        self.虚拟机.堆内存[地址:地址+4], 
                        'little', 
                        signed=True
                    )
                    变量字典[变量名] = 值
        
        return 变量字典
    
    def 输出当前状态(self):
        """输出当前调试状态"""
        print("\n" + "=" * 60)
        print("当前状态")
        print("=" * 60)
        
        # 程序计数器
        当前指令 = self.虚拟机.指令存储器[self.虚拟机.程序计数器] if self.虚拟机.程序计数器 < len(self.虚拟机.指令存储器) else None
        print(f"程序计数器: {self.虚拟机.程序计数器}")
        if 当前指令:
            if 当前指令.操作码 == "标签":
                print(f"  标签: {当前指令.操作数}")
            else:
                操作数 = f" {当前指令.操作数}" if 当前指令.操作数 is not None else ""
                print(f"  指令: {当前指令.操作码}{操作数}")
        
        # 操作数栈
        print(f"\n操作数栈 (深度: {len(self.虚拟机.操作数栈)}):")
        显示的栈 = self.虚拟机.操作数栈[-self.最大显示栈深度:]
        for i, 值 in enumerate(显示的栈):
            实际索引 = len(self.虚拟机.操作数栈) - len(显示的栈) + i
            print(f"  [{实际索引}] {值}")
        if len(self.虚拟机.操作数栈) > self.最大显示栈深度:
            print(f"  ... (还有 {len(self.虚拟机.操作数栈) - self.最大显示栈深度} 个)")
        
        # 调用栈
        print(f"\n调用栈 (深度: {len(self.虚拟机.调用栈)}):")
        for i, 帧 in enumerate(reversed(self.虚拟机.调用栈[-5:])):
            实际索引 = len(self.虚拟机.调用栈) - 1 - i
            返回地址 = 帧.get("返回地址", -1)
            print(f"  [{实际索引}] 返回地址: {返回地址}")
        
        # 变量
        变量 = self._获取所有变量()
        if 变量:
            print(f"\n变量:")
            for 变量名, 值 in list(变量.items())[:self.最大显示变量数]:
                print(f"  {变量名} = {值}")
        
        print("=" * 60)
    
    def 检查监视表达式(self):
        """检查监视表达式"""
        if not self.监视表达式列表:
            return
        
        print("\n监视表达式:")
        上下文 = self._创建调试上下文()
        
        for 监视 in self.监视表达式列表:
            try:
                表达式 = 监视["表达式"]
                新值 = eval(表达式, {"__builtins__": {}}, 上下文)
                旧值 = 监视["旧值"]
                
                if 旧值 != 新值:
                    变化 = "↑" if (新值 or 0) > (旧值 or 0) else "↓" if (新值 or 0) < (旧值 or 0) else "="
                    print(f"  {表达式}: {旧值} -> {新值} {变化}")
                    监视["变化次数"] += 1
                
                监视["旧值"] = 新值
            except Exception as 求值异常:
                print(f"  {监视['表达式']}: 错误 - {求值异常}")
    
    def 求值表达式(self, 表达式: str) -> Any:
        """求值表达式"""
        try:
            上下文 = self._创建调试上下文()
            结果 = eval(表达式, {"__builtins__": {}}, 上下文)
            return 结果
        except Exception as 求值异常:
            raise ValueError(f"表达式求值失败: {求值异常}")
    
    def 修改变量(self, 变量名: str, 新值: Any) -> bool:
        """修改变量值"""
        if 变量名 in self.调试符号表:
            变量信息 = self.调试符号表[变量名]
            if "地址" in 变量信息:
                地址 = 变量信息["地址"]
                if 0 <= 地址 < len(self.虚拟机.堆内存):
                    字节值 = int(新值).to_bytes(4, 'little', signed=True)
                    self.虚拟机.堆内存[地址:地址+4] = 字节值
                    print(f"✓ {变量名} = {新值}")
                    return True
        return False
    
    def 生成调试报告(self) -> Dict[str, Any]:
        """生成当前调试状态的报告"""
        return {
            "程序计数器": self.虚拟机.程序计数器,
            "操作数栈深度": len(self.虚拟机.操作数栈),
            "操作数栈内容": self.虚拟机.操作数栈[-5:] if self.虚拟机.操作数栈 else [],
            "调用栈深度": len(self.虚拟机.调用栈),
            "指令计数": self.虚拟机.指令计数,
            "栈最大深度": self.虚拟机.栈最大深度,
            "断点数量": len(self.断点字典),
            "断点列表": [行号 for 行号 in self.断点字典.keys()],
            "监视表达式数量": len(self.监视表达式列表),
            "运行标志": self.虚拟机.运行标志,
            "异常标志": self.虚拟机.异常标志
        }
    
    def 启动交互式调试(self):
        """启动交互式调试会话"""
        self.调试模式 = True
        print("\n" + "=" * 60)
        print("调试器已启动")
        print("可用命令: run, step, next, finish, break, delete, list, watch, print, info, quit")
        print("=" * 60)
        
        while self.调试模式 and self.虚拟机.运行标志:
            try:
                命令 = input("(调试) ").strip().lower()
                
                if not 命令:
                    continue
                
                parts = 命令.split()
                主命令 = parts[0]
                参数 = parts[1:] if len(parts) > 1 else []
                
                self._处理调试命令(主命令, 参数)
                
            except KeyboardInterrupt:
                print("\n调试被中断")
                break
            except Exception as 命令异常:
                print(f"命令执行错误: {命令异常}")
    
    def _处理调试命令(self, 命令: str, 参数: List[str]) -> bool:
        """处理调试命令"""
        if 命令 in ["c", "continue", "run"]:
            self.调试模式 = False
            self.单步模式 = False
            print("继续执行...")
            return True
        
        elif 命令 in ["s", "step"]:
            self.单步执行("step")
            self.暂停并等待命令()
            return True
        
        elif 命令 in ["n", "next"]:
            self.单步执行("next")
            self.暂停并等待命令()
            return True
        
        elif 命令 in ["f", "finish"]:
            self.单步执行("finish")
            self.暂停并等待命令()
            return True
        
        elif 命令 in ["b", "break"]:
            if 参数:
                行号 = int(参数[0])
                条件 = " ".join(参数[1:]) if len(参数) > 1 else ""
                self.设置断点(行号, 条件)
            else:
                print("用法: break <行号> [条件]")
            return True
        
        elif 命令 in ["d", "delete"]:
            if 参数:
                行号 = int(参数[0])
                self.删除断点(行号)
            else:
                self.清除所有断点()
            return True
        
        elif 命令 in ["l", "list"]:
            self.列出断点()
            return True
        
        elif 命令 in ["w", "watch"]:
            if 参数:
                表达式 = " ".join(参数)
                self.添加监视表达式(表达式)
            else:
                print("用法: watch <表达式>")
            return True
        
        elif 命令 in ["p", "print"]:
            if 参数:
                表达式 = " ".join(参数)
                try:
                    结果 = self.求值表达式(表达式)
                    print(f"{表达式} = {结果}")
                except Exception as 求值异常:
                    print(f"求值错误: {求值异常}")
            else:
                self.输出当前状态()
            return True
        
        elif 命令 in ["i", "info"]:
            报告 = self.生成调试报告()
            for 键, 值 in 报告.items():
                print(f"  {键}: {值}")
            return True
        
        elif 命令 in ["h", "help", "?"]:
            self._打印帮助信息()
            return True
        
        elif 命令 in ["q", "quit"]:
            print("退出调试")
            self.调试模式 = False
            self.虚拟机.运行标志 = False
            return True
        
        else:
            print(f"未知命令: {命令}")
            print("输入 'help' 查看帮助")
            return False
    
    def _打印帮助信息(self):
        """打印帮助信息"""
        print("\n调试器命令:")
        print("-" * 40)
        print("运行控制:")
        print("  run/c/continue    - 继续执行到下一个断点")
        print("  step/s            - 单步步入（执行一条指令）")
        print("  next/n            - 单步步过（执行到函数返回）")
        print("  finish/f          - 单步步出（执行到当前函数返回）")
        print("断点控制:")
        print("  break/b <行号>    - 设置断点")
        print("  delete/d <行号>   - 删除断点")
        print("  list/l            - 列出所有断点")
        print("  watch/w <表达式>  - 添加监视表达式")
        print("信息查看:")
        print("  print/p [表达式]  - 求值表达式或显示当前状态")
        print("  info/i            - 显示调试信息")
        print("其他:")
        print("  help/h/?          - 显示此帮助")
        print("  quit/q            - 退出调试")
        print("-" * 40)


# ============ 便捷函数 ============

def 创建调试器(虚拟机: 纯栈机虚拟机 = None) -> 拉尔夫集成调试器:
    """创建调试器实例"""
    return 拉尔夫集成调试器(虚拟机)


def 创建栈机() -> 纯栈机虚拟机:
    """创建栈机实例"""
    from 栈机核心 import 纯栈机虚拟机
    return 纯栈机虚拟机()


# ============ 测试代码 ============

if __name__ == "__main__":
    print("测试集成调试器")
    print("=" * 60)
    
    # 创建测试程序
    from 栈机核心 import 纯栈机虚拟机
    from 代数数据类型ADT import 指令
    
    虚拟机 = 纯栈机虚拟机()
    测试指令序列 = [
        指令("推入", 10),
        指令("推入", 20),
        指令("加法"),
        指令("推入", 5),
        指令("除法"),
        指令("打印"),
        指令("停机"),
    ]
    
    虚拟机.加载程序(测试指令序列)
    
    # 创建调试器
    调试器 = 拉尔夫集成调试器(虚拟机)
    
    # 设置断点
    调试器.设置断点(2)  # 在加法指令处设置断点
    
    # 启动交互式调试（这里只演示，非真正交互）
    print("调试器已创建")
    print(f"断点: {list(调试器.断点字典.keys())}")
    
    # 报告
    报告 = 调试器.生成调试报告()
    print(f"\n调试报告:")
    for 键, 值 in 报告.items():
        print(f"  {键}: {值}")
