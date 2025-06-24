# app.py
from flask import Flask, render_template, request, jsonify
import os
import traceback

# 导入我们所有需要的后台模块
from data_loader import DataLoader
from simulator import BattleSimulator
from dpr_calculator import DprCalculator
from rotation_finder import RotationFinder # 导入智能排轴查找器
from models import BattleState, Enemy, Action

# --- 应用初始化 ---
app = Flask(__name__)

# --- 全局实例 (仅限轻量级) ---
# 在应用启动时，只初始化最轻量级的数据加载器
try:
    DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), 'character_data.json')
    loader = DataLoader(DATA_FILE_PATH)
    AVAILABLE_CHARACTERS = list(loader.data.keys())
except Exception as e:
    print(f"应用启动时加载数据失败: {e}")
    loader = None
    AVAILABLE_CHARACTERS = []

# --- 路由和视图函数定义 ---

@app.route('/')
def index():
    """渲染主页"""
    if not AVAILABLE_CHARACTERS:
        return render_template('index.html', characters=[], error="无法加载角色数据。")
    return render_template('index.html', characters=AVAILABLE_CHARACTERS)

@app.route('/analyze', methods=['POST'])
def analyze():
    """处理【手动】分析请求的API接口。"""
    print("收到手动分析请求...")
    if not loader:
        return jsonify({'error': '服务器数据加载器未初始化。'}), 500

    try:
        data = request.get_json()
        character_id = data.get('character_id')
        turns = int(data.get('turns', 3))

        panel = loader.load_character_panel(character_id)
        if not panel:
            return jsonify({'error': f"无法加载角色 '{character_id}'"}), 404

        # 每次请求都创建新的实例，以保证线程安全和状态隔离
        simulator = BattleSimulator([panel])
        dpr_calculator = DprCalculator(simulator)
        
        dummy_enemy = Enemy("沙袋", 100000, 1200, {"诅咒": 0.1})
        initial_state = BattleState(
            turn_number=1,
            enemies=[dummy_enemy],
            character_resources={character_id: {"sp": 1000}}
        )
        
        if not panel.skills:
             return jsonify({'error': f"角色 '{character_id}' 没有技能"}), 400
        
        # 使用一个简单的默认排轴进行分析
        rotation = [Action(character_id, panel.skills[0], dummy_enemy.enemy_id)] * turns
        results = dpr_calculator.calculate_team_dpr(rotation, initial_state)

        response_data = {
            'character_id': character_id,
            'dpr': results['dpr'],
            'total_damage': results['total_damage'],
            'rotation': [a.skill_used.name for a in rotation],
            'final_resources': results['final_state'].character_resources.get(character_id, {})
        }
        return jsonify(response_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': '服务器内部错误。'}), 500

@app.route('/find_best_rotation', methods=['POST'])
def find_best_rotation():
    """
    处理【智能查找最优排轴】请求的全新API接口。
    """
    print("收到智能排轴请求...")
    if not loader:
        return jsonify({'error': '服务器数据加载器未初始化。'}), 500
    
    try:
        data = request.get_json()
        character_id = data.get('character_id')
        turns = int(data.get('turns', 3))

        panel = loader.load_character_panel(character_id)
        if not panel:
            return jsonify({'error': f"无法加载角色 '{character_id}'"}), 404

        # 每次请求都创建全新的实例
        simulator = BattleSimulator([panel])
        dpr_calculator = DprCalculator(simulator)
        rotation_finder = RotationFinder(simulator, dpr_calculator)

        # 定义一个更真实的初始状态用于智能查找
        initial_state = BattleState(
            turn_number=1,
            enemies=[Enemy("沙袋", 100000, 1200, {"诅咒": 0.1})],
            character_resources={character_id: {"sp": 100, "h_energy": 0}}
        )

        # 调用我们的“大脑”来寻找最优解
        best_rotation_info = rotation_finder.find_best_rotation(
            character_panel=panel,
            turns=turns,
            initial_state=initial_state
        )

        if not best_rotation_info:
            return jsonify({'error': f'在 {turns} 回合内未能为 {character_id} 找到任何可行的排轴。'}), 404

        # 将找到的结果打包成与前端期望一致的格式
        results = best_rotation_info['dpr_results']
        response_data = {
            'character_id': character_id,
            'dpr': results['dpr'],
            'total_damage': results['total_damage'],
            'rotation': best_rotation_info['rotation'], # 使用找到的最优排轴
            'final_resources': results['final_state'].character_resources.get(character_id, {})
        }
        return jsonify(response_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': '服务器在智能分析过程中遇到内部错误。'}), 500

# --- 应用启动 ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)
