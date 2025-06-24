# rotation_finder.py
import copy
from typing import List, Dict, Tuple

from models import CharacterPanel, BattleState, Skill, Action # 确保导入Action
from dpr_calculator import DprCalculator
from simulator import BattleSimulator, HIGHLIGHT_MAX_ENERGY

class RotationFinder:
    """
    通过智能搜索来寻找最优排轴，会考虑资源约束和攻击目标。
    """
    def __init__(self, simulator: BattleSimulator, dpr_calculator: DprCalculator):
        self.simulator = simulator
        self.dpr_calculator = dpr_calculator
        self.best_dpr = -1.0
        self.best_rotation_info = None
        self.target_id = None # 新增一个实例变量来存储本次搜索的目标ID
        print("智能排轴查找器已初始化 (带目标感知)。")

    def _find_rotations_recursive(
        self,
        character_panel: CharacterPanel,
        turns_left: int,
        current_path: List[Skill],
        current_state: BattleState
    ):
        """
        [核心] 使用递归深度优先搜索来查找所有可行的排轴。
        """
        # 基本情况: 如果没有剩余回合，说明我们找到了一个完整的、可行的排轴
        if turns_left == 0:
            # 使用DPR计算器评估这个排轴的性能
            result = self.dpr_calculator.calculate_team_dpr(
                team_rotation=[Action(character_panel.character_id, skill, self.target_id) for skill in current_path],
                initial_state=self.initial_state
            )
            
            # 如果找到了一个更高DPR的排轴，就更新记录
            if result and result.get('dpr', -1) > self.best_dpr:
                self.best_dpr = result['dpr']
                self.best_rotation_info = {
                    "rotation": [skill.name for skill in current_path],
                    "dpr_results": result
                }
                print(f"*** 新的最优DPR被发现: {self.best_dpr:.2f} ***")
            return

        # 递归步骤: 尝试在当前状态下使用每一个可用技能
        for skill in character_panel.skills:
            resources = current_state.character_resources.get(character_panel.character_id, {})
            is_possible = False
            
            # 智能检查资源是否足够
            if skill.skill_type == "HIGHLIGHT":
                if resources.get("h_energy", 0) >= HIGHLIGHT_MAX_ENERGY:
                    is_possible = True
            elif resources.get("sp", 0) >= skill.sp_cost:
                is_possible = True
            
            if is_possible:
                # --- FIX: 此处是关键修正 ---
                # 1. 创建一个包含正确目标ID的Action对象
                action_to_process = Action(
                    character_id=character_panel.character_id, 
                    skill_used=skill, 
                    target_id=self.target_id # 使用我们已锁定的目标ID
                )
                
                # 2. 将这个Action对象传递给模拟器，以推演下一步的状态
                damage, next_state = self.simulator.process_action(current_state, action_to_process)
                
                # 只有在行动有效时才继续
                if damage >= 0:
                    self._find_rotations_recursive(
                        character_panel=character_panel,
                        turns_left=turns_left - 1,
                        current_path=current_path + [skill],
                        current_state=next_state
                    )

    def find_best_rotation(
        self, 
        character_panel: CharacterPanel, 
        turns: int, 
        initial_state: BattleState
    ) -> Dict | None:
        """
        在给定的回合数内，为角色寻找DPR最高的【可行】技能排轴。
        """
        print(f"\n>>>>>> 开始为 '{character_panel.character_id}' 在 {turns} 回合内【高度智能】寻找最优排轴... <<<<<<")
        
        # --- NEW: 在搜索开始前，锁定目标 ---
        if not initial_state.enemies:
            print("[错误] 无法开始排轴查找：战场上没有敌人。")
            return None
        # 假设总是攻击战场上的第一个敌人
        self.target_id = initial_state.enemies[0].enemy_id
        print(f"智能搜索目标已锁定: {self.target_id}")

        self.best_dpr = -1.0
        self.best_rotation_info = None
        self.initial_state = copy.deepcopy(initial_state)

        # 启动递归搜索
        self._find_rotations_recursive(
            character_panel=character_panel,
            turns_left=turns,
            current_path=[],
            current_state=self.initial_state
        )

        print("\n==========================================")
        print("智能排轴搜索完成。")
        return self.best_rotation_info
