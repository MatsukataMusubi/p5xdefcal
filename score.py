# scorer.py
from dataclasses import dataclass
from typing import Dict
from models import CharacterStats

@dataclass
class ScoringModel:
    """
    定义评分模型的权重。
    权重越高，代表该属性在总分中的占比越大。
    """
    w_dpr: float = 1.0          # 每点DPR的价值
    w_attack: float = 0.2       # 每点攻击力的价值
    w_crit_rate: float = 200.0  # 每1%暴击率的价值 (乘以200)
    w_crit_damage: float = 100.0 # 每1%暴击伤害的价值 (乘以100)

class Scorer:
    """根据给定的评分模型为角色配置打分。"""
    def __init__(self, model: ScoringModel):
        self.model = model
        print("评分器已初始化。")

    def calculate_score(self, dpr_results: Dict, final_stats: CharacterStats) -> float:
        """
        计算一个配置的综合得分。

        :param dpr_results: 来自 DprCalculator 的结果。
        :param final_stats: 用于评分的角色属性快照。
        :return: 综合得分。
        """
        dpr = dpr_results.get('dpr', 0)
        
        # 根据权重分别计算各部分得分
        dpr_score = dpr * self.model.w_dpr
        attack_score = final_stats.attack * self.model.w_attack
        crit_rate_score = final_stats.crit_rate * self.model.w_crit_rate
        crit_damage_score = final_stats.crit_damage * self.model.w_crit_damage

        # 加总得到最终分数
        total_score = dpr_score + attack_score + crit_rate_score + crit_damage_score
        
        print(f"  - 分数详情: DPR部分({dpr_score:.0f}) + 攻击力部分({attack_score:.0f}) + 暴击率部分({crit_rate_score:.0f}) + 暴伤部分({crit_damage_score:.0f})")

        return total_score
