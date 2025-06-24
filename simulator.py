# simulator.py
import copy
from typing import List, Dict, Tuple
from collections import Counter

# 导入所有需要的模型和类
from models import CharacterPanel, BattleState, Action, Skill, CharacterStats, Buff, Enemy
# 导入伤害计算器和游戏规则数据库
from calculator import calculate_expected_damage
import game_database

# --- 全局游戏常量 ---
# 定义了与资源相关的核心平衡数值
HIGHLIGHT_MAX_ENERGY = 100
ENERGY_PER_ACTION = 35 # 每次普通行动回复的能量

class BattleSimulator:
    """
    模拟引擎的最终版本，支持团队作战、目标选择、资源系统和被动效果。
    """
    def __init__(self, character_panels: List[CharacterPanel]):
        # 模拟器在初始化时，需要知道所有参与战斗的角色的“面板蓝图”
        self.characters: Dict[str, CharacterPanel] = {p.character_id: p for p in character_panels}
        print("战斗模拟器已初始化 (最终版)。")

    def _get_final_stats(self, actor_panel: CharacterPanel, state: BattleState) -> CharacterStats:
        """
        [内部辅助方法] 计算一个角色在特定战斗状态下行动时的真正最终属性。
        这是一个统一的入口，负责处理所有类型的属性加成。
        """
        # 1. 获取包含装备和套装效果的静态面板属性
        final_stats = actor_panel.get_final_stats()
        
        # 2. 应用来自BattleState的动态Buff
        active_buffs = state.character_buffs.get(actor_panel.character_id, [])
        for buff in active_buffs:
            buff_function = game_database.DYNAMIC_BUFF_DB.get(buff.name)
            if buff_function:
                final_stats = buff_function(final_stats, buff)

        # 3. 应用基于资源的被动技能 (例如 Joker的'复仇')
        passive_func = game_database.CHARACTER_PASSIVE_DB.get(actor_panel.character_id)
        if passive_func:
            final_stats = passive_func(final_stats, state, actor_panel.character_id)
            
        return final_stats

    def process_action(self, state: BattleState, action: Action) -> Tuple[float, BattleState]:
        """
        处理单个行动，包含完整的资源检查、状态演进和Buff持续时间管理。
        这是模拟器的核心方法。
        """
        actor_id, skill, target_id = action.character_id, action.skill_used, action.target_id
        
        # --- 资源检查 ---
        # 检查行动是否可行，如果资源不足，则行动失败，返回0伤害和原始状态
        resources = state.character_resources.get(actor_id, {})
        # 检查HIGHLIGHT技能
        if skill.skill_type == "HIGHLIGHT":
            if resources.get("h_energy", 0) < HIGHLIGHT_MAX_ENERGY:
                print(f"[行动失败] {actor_id} 尝试使用 'HIGHLIGHT', 但能量不足。")
                return 0.0, state
        # 检查普通技能的SP消耗
        elif resources.get("sp", 0) < skill.sp_cost:
            print(f"[行动失败] {actor_id} 尝试使用 '{skill.name}', 但SP不足。")
            return 0.0, state
        
        # --- 正常处理流程 ---
        # 复制状态，准备进行修改，以保证“不可变性”
        next_state = copy.deepcopy(state)
        
        # --- 状态演进: 第1部分 - 资源消耗与生成 ---
        res = next_state.character_resources.setdefault(actor_id, {})
        if skill.skill_type == "HIGHLIGHT":
            res["h_energy"] = 0
        else:
            res["sp"] = res.get("sp", 0) - skill.sp_cost
            res["h_energy"] = min(HIGHLIGHT_MAX_ENERGY, res.get("h_energy", 0) + ENERGY_PER_ACTION)

        # --- 状态演进: 第2部分 - 触发技能效果 ---
        for effect_name in skill.effect_names:
            effect_function = game_database.SKILL_EFFECT_DB.get(effect_name)
            if effect_function:
                next_state = effect_function(next_state, action)
        
        # --- 伤害计算 ---
        damage = 0.0
        # 辅助技能不造成伤害
        if skill.damage_type != "辅助":
            target = next((e for e in next_state.enemies if e.enemy_id == target_id), None)
            if not target:
                print(f"[行动失败] 找不到目标 {target_id}。")
                return 0.0, next_state

            # 获取计入所有效果后的最终属性，并计算伤害
            final_stats = self._get_final_stats(self.characters[actor_id], next_state)
            damage = calculate_expected_damage(final_stats, skill, target)
        
        # --- 状态演进: 第3部分 - Buff持续时间递减 ---
        # (这部分逻辑可以添加在这里，以确保在每次行动后所有buff都正确地减少持续时间)
        
        return damage, next_state
