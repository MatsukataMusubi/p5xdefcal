# models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum, auto
from collections import Counter

# --- 枚举定义 ---
# 使用枚举可以提高代码的可读性和健壮性，避免使用魔法字符串。

class RevelationPosition(Enum):
    """定义启示的位置（宙, 日, 月, 星, 辰）。"""
    COSMOS = auto()
    SUN = auto()
    MOON = auto()
    STAR = auto()
    CHEN = auto()

# --- 核心数据结构 ---
# 使用@dataclass装饰器可以自动生成__init__, __repr__等方法，让代码更简洁。

@dataclass
class CharacterStats:
    """
    角色的属性模型。
    这个类作为所有属性的容器，无论是角色的基础属性、装备加成，还是最终面板。
    """
    # 基础属性
    attack: float = 0.0
    hp: float = 0.0
    crit_rate: float = 0.0
    crit_damage: float = 0.0  # 注意: 这是【额外】的暴击伤害, 例如, 50%暴伤在这里是0.5

    # 高级伤害公式所需属性
    penetration: float = 0.0              # 穿透, e.g., 20%穿透是0.2
    additive_damage_bonus: float = 0.0    # 加法类增伤区总和 (属性/全伤等)
    final_damage_bonus: float = 0.0       # 最终伤害加成, e.g., 40%最终增伤是0.4

    # 用于中间计算的临时字段
    attack_percent_bonus: float = 0.0
    hp_percent_bonus: float = 0.0
    crit_rate_bonus: float = 0.0

@dataclass
class Enemy:
    """
    敌人的数据模型，包含了计算伤害所需的所有防御属性。
    """
    enemy_id: str
    hp: float
    defense: float
    resistances: Dict[str, float] = field(default_factory=dict) # 属性抗性, e.g., {"诅咒": 0.1}
    defense_reduction: float = 0.0    # 减防总和, e.g., 30%减防是0.3
    vulnerability: float = 0.0        # 易伤总和, e.g., 10%易伤是0.1
    weakness_multiplier: float = 1.0  # 独立的弱点倍率, e.g., 1.5

@dataclass
class Weapon:
    """武器的数据模型。"""
    name: str
    base_attack: int
    crit_rate_bonus: float = 0.0
    crit_damage_bonus: float = 0.0
    penetration: float = 0.0

@dataclass
class Revelation:
    """单个启示的数据模型。"""
    name: str
    set_name: str  # 所属套装名称, e.g., "力量"
    position: RevelationPosition
    main_stat: CharacterStats = field(default_factory=CharacterStats) # 主词条属性

@dataclass
class Skill:
    """技能的数据模型，现在包含了类型和消耗。"""
    name: str
    multiplier: float
    sp_cost: int = 0
    skill_type: str = "NORMAL"  # 技能类型, 'NORMAL' 或 'HIGHLIGHT'
    damage_type: str = "物理"   # 伤害属性, e.g., "物理", "诅咒", "火焰"
    effect_names: List[str] = field(default_factory=list) # 技能附带的效果名称列表

@dataclass
class CharacterPanel:
    """
    角色面板，负责将角色的基础属性、武器和启示组合起来。
    这是一个“组装器”，本身不存储状态，只负责计算。
    """
    character_id: str
    base_stats: CharacterStats
    equipped_weapon: Weapon
    revelations: List[Revelation] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)

    def get_final_stats(self) -> CharacterStats:
        """
        计算并返回应用了武器和启示套装加成后的最终【静态】属性。
        注意：此方法不计算战斗中的动态buff或被动。
        """
        import game_database  # 局部导入以避免循环依赖

        final_stats = CharacterStats(**self.base_stats.__dict__)
        final_stats.attack += self.equipped_weapon.base_attack

        # 创建一个临时对象来累积所有加成
        all_bonuses = CharacterStats()
        all_bonuses.penetration += self.equipped_weapon.penetration
        all_bonuses.crit_rate_bonus += self.equipped_weapon.crit_rate_bonus
        final_stats.crit_damage += self.equipped_weapon.crit_damage_bonus

        # 处理启示套装效果
        set_counts = Counter(r.set_name for r in self.revelations)
        for name, count in set_counts.items():
            set_definition = game_database.REVELATION_SETS_DB.get(name)
            if not set_definition: continue
            if count >= 2 and set_definition.two_piece_bonus:
                all_bonuses = set_definition.two_piece_bonus(all_bonuses)
            # [FIX] 将 s_def 修正为正确的变量名 set_definition
            if count >= 4 and set_definition.four_piece_bonus:
                all_bonuses = set_definition.four_piece_bonus(all_bonuses)

        # 将累积的加成应用到最终属性上
        final_stats.attack *= (1 + all_bonuses.attack_percent_bonus)
        final_stats.crit_rate += all_bonuses.crit_rate_bonus
        final_stats.penetration += all_bonuses.penetration
        return final_stats

# --- 战斗模拟相关的数据结构 ---

@dataclass
class Buff:
    """代表一个临时的增益或减益效果，现在支持叠加。"""
    name: str
    duration: int
    stacks: int = 1       # 当前层数
    max_stacks: int = 1   # 最大可叠加层数

@dataclass
class Action:
    """代表一个单一的行动，包含了行动者、技能和目标。"""
    character_id: str
    skill_used: Skill
    target_id: str

@dataclass
class BattleState:
    """
    代表战斗在某一时刻的完整快照，是所有动态数据的“单一数据源”。
    """
    turn_number: int
    character_buffs: Dict[str, List[Buff]] = field(default_factory=dict)
    enemy_debuffs: Dict[str, List[Buff]] = field(default_factory=dict)
    character_resources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    enemies: List[Enemy] = field(default_factory=list)
