# calculator.py
from models import CharacterStats, Skill, Enemy

# --- 全局游戏常量 ---
# 这些常量定义了伤害公式中的核心平衡数值。
# 来自文章1.2节《基础伤害公式的构建》
DEFENSE_CONSTANT = 1400
# 防御系数 (来自文章1.2节, 暂定为1.0, 未来可调整)
DEFENSE_COEFFICIENT = 1.0

def calculate_expected_damage(
    stats: CharacterStats, 
    skill: Skill, 
    enemy: Enemy
) -> float:
    """
    根据文章重构的、分步的期望伤害计算函数。
    完整实现了文章第四章《完整公式的整合》中描述的计算序列。
    
    :param stats: 包含了所有加成后的最终角色属性。
    :param skill: 使用的技能。
    :param enemy: 攻击的目标敌人。
    :return: 期望伤害值。
    """
    
    # === 第1步: 计算技能面板伤害 (文章4.1节) ===
    # 这是最基础的伤害值，由角色的最终攻击力和技能倍率决定。
    panel_damage = stats.attack * skill.multiplier

    # === 第2步: 计算防御减免 (文章4.1节, 步骤2a-2d) ===
    # 2a. 计算基础有效防御力 (计入来自debuff的减防效果)
    effective_def_after_debuffs = enemy.defense * (1 - enemy.defense_reduction)
    
    # 应用全局防御系数
    effective_def_with_coeff = effective_def_after_debuffs * DEFENSE_COEFFICIENT
    
    # 2b. 应用来自攻击方的穿透效果
    penetrated_def = effective_def_with_coeff * (1 - stats.penetration)
    
    # 2c & 2d. 计算最终防御承伤系数并应用
    # 为避免除以零的错误，增加一个保护性检查。
    if (penetrated_def + DEFENSE_CONSTANT) <= 0:
        return float('inf') # 如果防御被降为负无穷，伤害理论上也是无穷大
        
    defense_multiplier = 1 - (penetrated_def / (penetrated_def + DEFENSE_CONSTANT))
    damage_after_def = panel_damage * defense_multiplier

    # === 第3步: 应用“增伤区”乘数 (文章4.1节, 步骤3) ===
    # 此处为所有加法类增伤（如属性伤害、全伤害等）的总和。
    bonus_multiplier = 1 + stats.additive_damage_bonus
    damage_after_bonus = damage_after_def * bonus_multiplier

    # === 第4步: 应用暴击乘数 (基于期望值) (文章4.1节, 步骤4) ===
    # 期望伤害 = 非暴击伤害 * (1 - 暴击率) + 暴击伤害 * 暴击率
    #           = 基础伤害 * (1 + 额外暴伤 * 暴击率)
    # 注意: 我们的 stats.crit_damage 存储的是【额外】暴伤
    crit_multiplier = 1 + stats.crit_rate * stats.crit_damage
    damage_after_crit = damage_after_bonus * crit_multiplier

    # === 第5步: 应用“易伤区”乘数 (文章4.1节, 步骤5) ===
    # 5a. 应用基础的属性抗性
    resistance_value = enemy.resistances.get(skill.damage_type, 0)
    resistance_multiplier = 1 - resistance_value
    damage_after_resistance = damage_after_crit * resistance_multiplier
    
    # 5b. 应用独立的弱点倍率
    damage_after_weakness = damage_after_resistance * enemy.weakness_multiplier
    
    # 5c. 应用通用的易伤效果
    vulnerability_multiplier = 1 + enemy.vulnerability
    damage_after_vulnerability = damage_after_weakness * vulnerability_multiplier

    # === 第6步: 应用“最终伤害”乘数 (文章4.1节, 步骤6) ===
    # 这是一个独立的、位于计算链末端的强大乘区。
    final_damage_multiplier = 1 + stats.final_damage_bonus
    final_damage = damage_after_vulnerability * final_damage_multiplier

    # 确保最终伤害不会是负数
    return max(0, final_damage)
