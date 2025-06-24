# main.py
import copy # 导入copy模块，用于深度复制状态对象

# 导入所有我们需要的自定义模块和类
from models import BattleState, Enemy, Action
from data_loader import DataLoader
from simulator import BattleSimulator
from dpr_calculator import DprCalculator

def main():
    """
    程序主入口。
    负责组织和协调所有模块，以执行一次完整的团队协同分析。
    """
    print("--- P5X 智能分析工具 v4.1 (最终版) ---")
    
    # --- 第1步: 初始化工具并加载团队成员 ---
    # 创建DataLoader实例，并指定数据文件的路径
    loader = DataLoader("character_data.json")
    
    # 从外部文件加载Joker和李瑶铃的角色面板
    joker = loader.load_character_panel("Joker")
    li_yaoling = loader.load_character_panel("Li Yaoling")
    
    # 健壮性检查：如果任一角色加载失败，则程序终止
    if not (joker and li_yaoling):
        print("角色数据加载失败，程序终止。")
        return

    # --- 第2步: 初始化模拟器和DPR计算器 ---
    # 将加载好的角色面板列表传递给模拟器
    sim = BattleSimulator([joker, li_yaoling])
    # 将模拟器实例注入到DPR计算器中
    dpr_calc = DprCalculator(sim)

    # --- 第3步: 定义战场环境 ---
    # 创建一个敌人实例
    dummy = Enemy(
        enemy_id="沙袋", 
        hp=100000, 
        defense=1200, 
        resistances={"诅咒": 0.1} # 假设敌人有10%的诅咒抗性
    )
    
    # 创建战斗的初始状态，包括初始资源和战场上的敌人
    initial_state = BattleState(
        turn_number=1,
        character_resources={"Joker": {"sp": 100}, "Li Yaoling": {"sp": 100}},
        enemies=[dummy]
    )
    
    # --- 第4步: 定义团队排轴 ---
    # 这是一个经典的“辅助先手增益，主C后手输出”的行动序列
    team_rotation = [
        # 第一个行动：李瑶铃使用她的第一个技能（激励之舞），目标是Joker
        Action(character_id="Li Yaoling", skill_used=li_yaoling.skills[0], target_id="Joker"),
        # 第二个行动：Joker在获得buff后，使用他的第一个技能（无畏压制），攻击沙袋
        Action(character_id="Joker", skill_used=joker.skills[0], target_id="沙袋"),
    ]

    # --- 第5步: 调用DPR计算器执行分析 ---
    results = dpr_calc.calculate_team_dpr(team_rotation, initial_state)

    # --- 第6步: 打印最终的分析报告 ---
    print("\n\n##################################")
    print("###      团队协同分析报告      ###")
    print("##################################")
    print(f"\n排轴: {[f'{a.character_id} 使用 {a.skill_used.name}' for a in team_rotation]}")
    print(f"\n团队总伤害: {results['total_damage']:.2f}")
    # 这里我们用“团队总伤害”除以“行动次数”来得到一个平均每次行动的伤害值
    print(f"**团队平均每次行动伤害 (DPA): {results['dpr']:.2f}**")
    print(f"结束时Joker的Buff: {results['final_state'].character_buffs.get('Joker', [])}")
    print("##################################")


# 确保这个脚本被直接运行时，才执行main()函数
if __name__ == "__main__":
    main()
