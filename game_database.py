# game_database.py
from dataclasses import dataclass
from typing import Callable, Dict, Any
from models import Buff, CharacterStats, BattleState, Action

# --- 类型提示定义 ---
# 使用类型提示可以帮助IDE和静态分析工具理解代码，提高开发效率。
BonusApplicator = Callable[[CharacterStats], CharacterStats]
SkillEffectApplicator = Callable[[BattleState, Action], BattleState]
PassiveEffectApplicator = Callable[[CharacterStats, BattleState, str], CharacterStats]
DynamicBuffApplicator = Callable[[CharacterStats, Buff], CharacterStats]

# ===================================================================
# == 启示套装数据库 (REVELATION SET DATABASE)
# ===================================================================
@dataclass
class RevelationSet:
    """定义一个启示套装的效果。"""
    name: str
    two_piece_bonus: BonusApplicator | None = None
    four_piece_bonus: BonusApplicator | None = None

# --- 套装效果实现函数 ---
# 这些函数接收一个临时的bonuses对象，并修改它来添加套装效果。
def power_2p(stats_bonuses: CharacterStats) -> CharacterStats:
    """力量2件套: 攻击力提升12%"""
    print("[套装效果] '力量' 2件套生效: 攻击力提升 12%")
    stats_bonuses.attack_percent_bonus += 0.12
    return stats_bonuses

# --- "规则库" 本身 ---
# 这是一个字典，将套装名称映射到其效果定义。
REVELATION_SETS_DB: Dict[str, RevelationSet] = {
    "力量": RevelationSet(
        name="力量",
        two_piece_bonus=power_2p
    ),
    # 未来可以在此添加更多套装...
}

# ===================================================================
# == 技能效果数据库 (SKILL EFFECT DATABASE)
# ===================================================================
def generate_shaqi(state: BattleState, action: Action) -> BattleState:
    """实现为角色生成'煞气'的效果。"""
    actor_id = action.character_id
    print(f"[技能效果] '{actor_id}' 正在生成1个『煞气』...")
    # setdefault会确保字典和内部的字典存在
    resources = state.character_resources.setdefault(actor_id, {})
    resources["煞气"] = resources.get("煞气", 0) + 1
    return state

def apply_attack_up_to_joker(state: BattleState, action: Action) -> BattleState:
    """实现'激励之舞'的效果：为Joker施加'攻击力提升'Buff。"""
    target_char_id = "Joker"
    print(f"[技能效果] '{action.character_id}' 对 '{target_char_id}' 施加 '攻击力提升' Buff!")
    buffs = state.character_buffs.setdefault(target_char_id, [])
    # 为避免重复叠加，先移除已有的同名buff
    buffs[:] = [b for b in buffs if b.name != "攻击力提升"]
    buffs.append(Buff(name="攻击力提升", duration=3)) # 假设持续3回合
    return state

# --- "规则库" 本身 ---
SKILL_EFFECT_DB: Dict[str, SkillEffectApplicator] = {
    "GENERATE_SHAQI_1": generate_shaqi,
    "APPLY_ATTACK_UP_JOKER": apply_attack_up_to_joker,
}

# ===================================================================
# == 角色被动技能数据库 (CHARACTER PASSIVE DATABASE)
# ===================================================================
def apply_joker_shaqi_passive(stats: CharacterStats, state: BattleState, char_id: str) -> CharacterStats:
    """实现Joker的被动'复仇'：根据『煞气』层数提升攻击力。"""
    shaqi_count = state.character_resources.get(char_id, {}).get("煞气", 0)
    if shaqi_count > 0:
        bonus = shaqi_count * 0.18
        print(f"[被动技能] '复仇' 生效: 持有 {shaqi_count} 个『煞气』, 攻击力提升 {bonus:.0%}")
        stats.attack *= (1 + bonus)
    return stats

# --- "规则库" 本身 ---
CHARACTER_PASSIVE_DB: Dict[str, PassiveEffectApplicator] = {
    "Joker": apply_joker_shaqi_passive,
}

# ===================================================================
# == 动态Buff效果数据库 (DYNAMIC BUFF DATABASE)
# ===================================================================
def apply_attack_up_buff(stats: CharacterStats, buff: Buff) -> CharacterStats:
    """实现'攻击力提升'Buff的具体效果。"""
    bonus = 0.20  # 假设这是一个20%的攻击力加成
    print(f"[动态Buff] '{buff.name}'生效: 攻击力提升 {bonus:.0%}")
    stats.attack *= (1 + bonus)
    return stats

# --- "规则库" 本身 ---
DYNAMIC_BUFF_DB: Dict[str, DynamicBuffApplicator] = {
    "攻击力提升": apply_attack_up_buff,
}
