# ===================================================================
# data_loader.py
# ===================================================================
import json
from typing import Dict, Any, List
# 导入所有需要的数据模型，用于将字典转换为对象
from models import (
    CharacterPanel, CharacterStats, Weapon, Skill, 
    Revelation, RevelationPosition
)

class DataLoader:
    """
    负责从外部JSON文件加载数据，并将其转换成程序可以理解的dataclass对象。
    这是连接数据和程序的“桥梁”。
    """
    def __init__(self, data_filepath: str):
        """
        在初始化时，读取并解析JSON文件。
        """
        try:
            with open(data_filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"成功从 '{data_filepath}' 加载数据。")
        except FileNotFoundError:
            print(f"[错误] 数据文件未找到: {data_filepath}")
            self.data = {}
        except json.JSONDecodeError:
            print(f"[错误] 解析JSON文件失败: {data_filepath}")
            self.data = {}

    def load_character_panel(self, character_id: str) -> CharacterPanel | None:
        """
        根据给定的character_id，加载并构建一个完整的CharacterPanel。
        """
        char_data = self.data.get(character_id)
        if not char_data:
            print(f"[错误] 在数据文件中找不到角色: '{character_id}'")
            return None

        try:
            # 使用Python的**kwargs语法，将字典直接解包作为dataclass的构造函数参数
            base_stats = CharacterStats(**char_data.get('base_stats', {}))
            weapon = Weapon(**char_data.get('weapon', {}))
            skills = [Skill(**skill_data) for skill_data in char_data.get('skills', [])]
            
            # 加载启示列表
            revelations_data = char_data.get('revelations', [])
            revelations_list: List[Revelation] = []
            for rev_data in revelations_data:
                # 将JSON中的字符串位置 (e.g., "SUN") 转换为枚举成员 (RevelationPosition.SUN)
                position_enum = RevelationPosition[rev_data['position']]
                revelations_list.append(
                    Revelation(
                        name=rev_data['name'],
                        set_name=rev_data['set_name'],
                        position=position_enum
                    )
                )

            # 构建并返回最终的角色面板对象
            panel = CharacterPanel(
                character_id=character_id,
                base_stats=base_stats,
                equipped_weapon=weapon,
                skills=skills,
                revelations=revelations_list
            )
            return panel
        except (KeyError, TypeError) as e:
            print(f"[错误] 加载 '{character_id}' 时数据格式错误: {e}")
            return None