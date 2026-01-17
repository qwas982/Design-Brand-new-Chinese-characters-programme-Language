"""
拉尔夫·韦根环核心原语模块 - Python实现
提供循环执行、客观验证、状态感知等核心原语功能

用法: from 拉尔夫原语 import 环执行, 客观验证, 状态感知
"""

import subprocess
import json
import os
import time
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class 任务状态:
    """状态感知的数据载体"""
    迭代次数: int = 0
    项目路径: str = ""
    日志文件: str = "迭代日志.json"
    完成标志: str = "<promise>任务完成</promise>"
    额外数据: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.额外数据 is None:
            self.额外数据 = {}


class 环执行:
    """循环执行原语 - LOOP_EXEC"""
    
    def __init__(self, 最大迭代次数: int = 50):
        self.最大迭代次数 = 最大迭代次数
        self.安全计数器 = 0
    
    def 运行(self, 任务函数: Callable, 初始状态: 任务状态) -> 任务状态:
        """
        执行环直到任务完成或达到安全上限
        
        参数:
            任务函数: 每次迭代执行的函数，接受当前状态，返回新状态
            初始状态: 初始任务状态
        
        返回:
            最终任务状态
        """
        当前状态 = 初始状态
        
        while self.安全计数器 < self.最大迭代次数:
            self.安全计数器 += 1
            当前状态.迭代次数 = self.安全计数器
            
            print(f"\n{'='*40}")
            print(f"迭代第{当前状态.迭代次数}轮开始")
            print(f"{'='*40}")
            
            try:
                # 执行任务
                新状态 = 任务函数(当前状态)
                
                # 确保返回了新状态
                if 新状态 is None:
                    print("⚠️ 任务函数返回None，使用当前状态继续")
                    新状态 = 当前状态
                
                # 检查完成标志
                if self.检查完成(新状态):
                    print("✅ 任务达成客观标准，环终止")
                    return 新状态
                
                # 更新状态继续环
                当前状态 = 新状态
                
            except Exception as 执行异常:
                print(f"⚠️ 第{当前状态.迭代次数}轮执行异常: {执行异常}")
                当前状态.额外数据["最后异常"] = str(执行异常)
            
            # 安全暂停
            time.sleep(0.5)
        
        print(f"⚠️ 达到安全迭代上限({self.最大迭代次数})，强制终止")
        return 当前状态
    
    def 检查完成(self, 状态: 任务状态) -> bool:
        """检查任务是否完成"""
        if not 状态.项目路径:
            return False
            
        日志路径 = os.path.join(状态.项目路径, 状态.日志文件)
        
        if os.path.exists(日志路径):
            try:
                with open(日志路径, 'r', encoding='utf-8') as f:
                    日志 = json.load(f)
                    
                    # 支持多种完成标志格式
                    完成标志 = 日志.get("完成标志") or 日志.get("completion_flag")
                    
                    if 完成标志:
                        return 完成标志 == 状态.完成标志
                        
                    # 也检查事件日志中的完成标记
                    事件日志 = 日志.get("事件日志", [])
                    for 条目 in 事件日志:
                        if 条目.get("事件") == "任务完成":
                            return True
                            
            except json.JSONDecodeError as json异常:
                print(f"⚠️ 解析日志文件失败: {json异常}")
            except Exception as 读取异常:
                print(f"⚠️ 读取日志文件失败: {读取异常}")
        
        return False


class 客观验证:
    """客观验证原语 - VERIFY_OBJECTIVE"""
    
    @staticmethod
    def 执行测试(测试命令: str, 工作目录: str = ".") -> bool:
        """
        执行外部测试命令，返回是否通过
        
        参数:
            测试命令: 要执行的测试命令
            工作目录: 命令执行的工作目录
        
        返回:
            测试是否通过
        """
        try:
            print(f"执行测试命令: {测试命令}")
            print(f"工作目录: {工作目录}")
            
            结果 = subprocess.run(
                测试命令,
                shell=True,
                cwd=工作目录,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            标准输出 = 结果.stdout
            标准错误 = 结果.stderr
            
            if 标准输出:
                print(f"标准输出:\n{标准输出[:500]}")
            if 标准错误:
                print(f"标准错误:\n{标准错误[:200]}")
            
            if 结果.returncode == 0:
                print(f"✅ 验证通过")
                return True
            else:
                错误信息 = 标准错误[:200] if 标准错误 else "无错误信息"
                print(f"❌ 验证失败: {错误信息}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 测试执行超时(5分钟)")
            return False
        except Exception as 执行异常:
            print(f"⚠️ 验证异常: {执行异常}")
            return False
    
    @staticmethod
    def 检查条件(条件函数: Callable[[], bool], 描述: str = "") -> bool:
        """通过函数检查条件"""
        try:
            通过 = 条件函数()
            状态符号 = "✅" if 通过 else "❌"
            print(f"{状态符号} 条件检查: {描述}")
            return 通过
        except Exception as 检查异常:
            print(f"⚠️ 条件检查异常: {检查异常}")
            return False
    
    @staticmethod
    def 验证文件存在(文件路径: str) -> bool:
        """验证文件是否存在"""
        存在 = os.path.exists(文件路径)
        状态符号 = "✅" if 存在 else "❌"
        print(f"{状态符号} 文件存在检查: {文件路径}")
        return 存在
    
    @staticmethod
    def 验证目录存在(目录路径: str) -> bool:
        """验证目录是否存在"""
        存在 = os.path.isdir(目录路径)
        状态符号 = "✅" if 存在 else "❌"
        print(f"{状态符号} 目录存在检查: {目录路径}")
        return 存在


class 状态感知:
    """状态感知原语 - PERSIST_STATE"""
    
    def __init__(self, 项目根目录: str):
        self.项目路径 = Path(项目根目录)
        self.状态文件 = self.项目路径 / "项目状态.json"
        self.确保目录()
    
    def 确保目录(self):
        """确保项目目录存在"""
        self.项目路径.mkdir(parents=True, exist_ok=True)
        print(f"📁 确保目录存在: {self.项目路径}")
    
    def 保存状态(self, 状态数据: Dict[str, Any]):
        """持久化保存状态"""
        # 添加时间戳
        状态数据["_最后更新"] = self.当前时间戳()
        
        try:
            with open(self.状态文件, 'w', encoding='utf-8') as f:
                json.dump(状态数据, f, ensure_ascii=False, indent=2)
            print(f"💾 状态已保存到: {self.状态文件}")
        except Exception as 保存异常:
            print(f"⚠️ 保存状态失败: {保存异常}")
    
    def 加载状态(self) -> Dict[str, Any]:
        """加载持久化状态"""
        if self.状态文件.exists():
            try:
                with open(self.状态文件, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ 状态文件损坏，返回空状态")
                return {"迭代历史": [], "错误日志": []}
        return {"迭代历史": [], "错误日志": []}
    
    def 记录日志(self, 事件: str, 数据: Any = None):
        """记录迭代日志"""
        日志文件 = self.项目路径 / "迭代日志.json"
        
        # 加载现有日志数据
        if 日志文件.exists():
            try:
                with open(日志文件, 'r', encoding='utf-8') as f:
                    日志数据 = json.load(f)
            except json.JSONDecodeError:
                日志数据 = {}
        else:
            日志数据 = {}
        
        新条目 = {
            "时间戳": self.当前时间戳(),
            "事件": 事件,
            "数据": 数据
        }
        
        日志数据.setdefault("事件日志", []).append(新条目)
        
        try:
            with open(日志文件, 'w', encoding='utf-8') as f:
                json.dump(日志数据, f, ensure_ascii=False, indent=2)
            print(f"📝 日志已记录: {事件}")
        except Exception as 写入异常:
            print(f"⚠️ 记录日志失败: {写入异常}")
    
    def 添加迭代历史(self, 迭代数据: Dict[str, Any]):
        """添加迭代历史记录"""
        状态 = self.加载状态()
        
        迭代记录 = {
            "时间戳": self.当前时间戳(),
            **迭代数据
        }
        
        状态.setdefault("迭代历史", []).append(迭代记录)
        self.保存状态(状态)
    
    def 记录错误(self, 错误信息: str, 上下文: Dict[str, Any] = None):
        """记录错误日志"""
        状态 = self.加载状态()
        
        错误记录 = {
            "时间戳": self.当前时间戳(),
            "错误信息": 错误信息,
            "上下文": 上下文 or {}
        }
        
        状态.setdefault("错误日志", []).append(错误记录)
        self.保存状态(状态)
        print(f"❌ 错误已记录: {错误信息}")
    
    @staticmethod
    def 当前时间戳() -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# ============ AI调用接口 ============

class AI调用器接口:
    """AI调用接口，支持多种AI后端"""
    
    def __init__(self, 后端: str = "模拟"):
        self.后端 = 后端
        self.配置 = {}
        self.已调用次数 = 0
    
    def 配置API(self, api密钥: str, 模型: str = None, 基础URL: str = None):
        """配置API密钥和模型"""
        self.配置["api密钥"] = api密钥
        if 模型:
            self.配置["模型"] = 模型
        if 基础URL:
            self.配置["基础URL"] = 基础URL
        print(f"AI调用器已配置: 后端={self.后端}, 模型={模型}")
    
    def 调用(self, 提示词: str, 上下文: str = "") -> Dict[str, Any]:
        """
        调用AI处理任务
        
        返回字典格式:
            {
                "成功": bool,
                "响应": str,
                "用时": float,
                "错误": str (可选)
            }
        """
        self.已调用次数 += 1
        开始时间 = time.time()
        
        if self.后端 == "openai":
            return self.调用OpenAI(提示词, 上下文)
        elif self.后端 == "claude":
            return self.调用Claude(提示词, 上下文)
        elif self.后端 == "deepseek":
            return self.调用DeepSeek(提示词, 上下文)
        else:
            return self.调用模拟(提示词, 上下文)
    
    def 调用模拟(self, 提示词: str, 上下文: str) -> Dict[str, Any]:
        """模拟AI响应（用于测试）"""
        time.sleep(0.1)  # 模拟延迟
        return {
            "成功": True,
            "响应": f"[模拟AI响应] 已收到请求: {提示词[:50]}...",
            "用时": 0.1,
            "调用次数": self.已调用次数
        }
    
    def 调用OpenAI(self, 提示词: str, 上下文: str) -> Dict[str, Any]:
        """调用OpenAI API"""
        开始时间 = time.time()
        
        try:
            import openai
            模型 = self.配置.get("模型", "gpt-3.5-turbo")
            
            客户端 = openai.OpenAI(
                api_key=self.配置.get("api密钥"),
                base_url=self.配置.get("基础URL")
            )
            
            消息列表 = []
            if 上下文:
                消息列表.append({"role": "system", "content": 上下文})
            消息列表.append({"role": "user", "content": 提示词})
            
            响应 = 客户端.chat.completions.create(
                model=模型,
                messages=消息列表,
                temperature=0.7
            )
            
            用时 = time.time() - 开始时间
            
            return {
                "成功": True,
                "响应": 响应.choices[0].message.content,
                "用时": 用时,
                "token使用": 响应.usage.total_tokens if hasattr(响应, 'usage') else None
            }
            
        except ImportError:
            return {
                "成功": False,
                "响应": "",
                "用时": time.time() - 开始时间,
                "错误": "openai库未安装，请运行: pip install openai"
            }
        except Exception as api异常:
            return {
                "成功": False,
                "响应": "",
                "用时": time.time() - 开始时间,
                "错误": f"OpenAI API调用失败: {str(api异常)}"
            }
    
    def 调用Claude(self, 提示词: str, 上下文: str) -> Dict[str, Any]:
        """调用Claude API (Anthropic)"""
        开始时间 = time.time()
        
        try:
            import anthropic
            模型 = self.配置.get("模型", "claude-sonnet-4-20250514")
            
            客户端 = anthropic.Anthropic(
                api_key=self.配置.get("api密钥")
            )
            
            消息内容 = 提示词
            if 上下文:
                消息内容 = f"{上下文}\n\n{提示词}"
            
            响应 = 客户端.messages.create(
                model=模型,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": 消息内容}
                ]
            )
            
            用时 = time.time() - 开始时间
            
            return {
                "成功": True,
                "响应": 响应.content[0].text,
                "用时": 用时,
                "token使用": 响应.usage.input_tokens + response.usage.output_tokens if hasattr(响应, 'usage') else None
            }
            
        except ImportError:
            return {
                "成功": False,
                "响应": "",
                "用时": time.time() - 开始时间,
                "错误": "anthropic库未安装，请运行: pip install anthropic"
            }
        except Exception as api异常:
            return {
                "成功": False,
                "响应": "",
                "用时": time.time() - 开始时间,
                "错误": f"Claude API调用失败: {str(api异常)}"
            }
    
    def 调用DeepSeek(self, 提示词: str, 上下文: str) -> Dict[str, Any]:
        """调用DeepSeek API"""
        开始时间 = time.time()
        
        try:
            import openai  # DeepSeek兼容OpenAI API
            
            客户端 = openai.OpenAI(
                api_key=self.配置.get("api密钥"),
                base_url=self.配置.get("基础URL", "https://api.deepseek.com/v1")
            )
            
            消息列表 = []
            if 上下文:
                消息列表.append({"role": "system", "content": 上下文})
            消息列表.append({"role": "user", "content": 提示词})
            
            响应 = 客户端.chat.completions.create(
                model=self.配置.get("模型", "deepseek-chat"),
                messages=消息列表
            )
            
            用时 = time.time() - 开始时间
            
            return {
                "成功": True,
                "响应": 响应.choices[0].message.content,
                "用时": 用时
            }
            
        except ImportError:
            return {
                "成功": False,
                "响应": "",
                "用时": time.time() - 开始时间,
                "错误": "openai库未安装"
            }
        except Exception as api异常:
            return {
                "成功": False,
                "响应": "",
                "用时": time.time() - 开始时间,
                "错误": f"DeepSeek API调用失败: {str(api异常)}"
            }


# ============ 便捷工厂函数 ============

def 创建环(最大迭代次数: int = 50) -> 环执行:
    """创建循环执行器"""
    return 环执行(最大迭代次数)


def 创建验证器() -> 客观验证:
    """创建验证器"""
    return 客观验证()


def 创建状态管理器(项目路径: str) -> 状态感知:
    """创建状态管理器"""
    return 状态感知(项目路径)


def 创建AI调用器(后端: str = "模拟") -> AI调用器接口:
    """创建AI调用器"""
    return AI调用器接口(后端)


# ============ 测试代码 ============

if __name__ == "__main__":
    print("测试拉尔夫原语模块")
    print("=" * 50)
    
    # 测试1: 环执行
    print("\n测试1: 环执行")
    环 = 创建环(最大迭代次数=3)
    初始状态 = 任务状态(
        项目路径="./test_项目",
        日志文件="测试日志.json"
    )
    
    def 简单任务(状态):
        print(f"  执行任务，迭代次数: {状态.迭代次数}")
        状态.额外数据["当前时间"] = 状态感知.当前时间戳()
        return 状态
    
    结果 = 环.运行(简单任务, 初始状态)
    print(f"  最终迭代次数: {结果.迭代次数}")
    
    # 测试2: 验证器
    print("\n测试2: 验证器")
    验证结果 = 客观验证.验证文件存在("/tmp")
    print(f"  /tmp目录存在: {验证结果}")
    
    # 测试3: AI调用器
    print("\n测试3: AI调用器")
    AI调用器 = 创建AI调用器("模拟")
    响应 = AI调用器.调用("你好，请做一个自我介绍")
    print(f"  成功: {响应['成功']}")
    print(f"  响应: {响应['响应'][:100]}...")
    
    print("\n" + "=" * 50)
    print("所有测试完成")
