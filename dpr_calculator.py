# dpr_calculator.py
import copy
from typing import List, Dict

# 导入所有需要的数据模型和类
from models import BattleState, Action, Skill
from simulator import BattleSimulator

class DprCalculator:
    """
    使用战斗模拟器来运行一个完整的技能循环(排轴)，并计算DPR。
    这是一个高层级的分析工具，负责协调模拟流程并汇总结果。
    """
    def __init__(self, simulator: BattleSimulator):
        """
        在初始化时，接收一个已经创建好的战斗模拟器实例。
        这是一种依赖注入的体现，使得DPR计算器不关心模拟器如何被创建。
        """
        self.simulator = simulator
        print("DPR 计算器已初始化。")

    def calculate_team_dpr(self, team_rotation: List[Action], initial_state: BattleState) -> Dict:
        """
        计算一个完整的团队排轴的表现。
        这是DPR计算器的核心方法。

        :param team_rotation: 一个包含多个Action对象的列表，定义了团队的行动顺序。
        :param initial_state: 模拟开始时的战斗状态。
        :return: 一个包含详细分析结果的字典。
        """
        print(f"\n>>>>>> 开始计算团队排轴DPR... <<<<<<")
        total_damage = 0.0
        turn_count = len(team_rotation)
        # 使用深度复制来保证每次计算都从一个纯净的初始状态开始
        current_state = copy.deepcopy(initial_state)

        # 如果排轴为空，直接返回零值结果，避免除以零的错误
        if not team_rotation:
            print("[警告] 团队排轴为空，无法计算DPR。")
            return {"total_damage": 0, "dpr": 0, "final_state": current_state}

        # 遍历排轴中的每一个行动
        for i, action in enumerate(team_rotation):
            print(f"\n[团队排轴 - 第 {i+1} 动]")
            # 调用模拟器处理单个行动，并接收造成的伤害和行动后的新状态
            damage, next_state = self.simulator.process_action(current_state, action)
            total_damage += damage
            # 更新当前状态，用于下一次循环
            current_state = next_state
        
        # 计算平均每轮伤害 (Damage Per Round)
        dpr = total_damage / turn_count if turn_count else 0
        
        # 将所有分析结果打包成一个字典并返回
        return {
            "total_damage": total_damage, 
            "dpr": dpr, 
            "final_state": current_state
        }
