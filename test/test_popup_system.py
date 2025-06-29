#!/usr/bin/env python3
"""
弹窗系统测试脚本
展示不同类型的弹窗和按钮配置
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.presentation_manager import PresentationManager

def test_popup_system():
    """测试弹窗系统的各种功能"""

    # 初始化显示管理器（测试模式）
    pm = PresentationManager(test_mode=False)

    print("=== 弹窗系统测试 ===\n")

    # 1. 基础单按钮弹窗
    print("1. 测试单按钮弹窗")
    result = pm.show_popup("操作已完成！", "提示")
    print(f"返回结果: {result}\n")

    # 2. 确认对话框
    print("2. 测试确认对话框")
    result = pm.show_confirm_dialog("确定要删除这个文件吗？", "确认删除")
    print(f"用户确认: {result}\n")

    # 3. 是否对话框
    print("3. 测试是否对话框")
    result = pm.show_yes_no_dialog("是否保存当前设置？", "保存设置")
    print(f"用户选择: {'是' if result else '否'}\n")

    # 4. 多选择对话框
    print("4. 测试多选择对话框")
    choices = ["新手模式", "普通模式", "专家模式", "自定义模式"]
    selected = pm.show_choice_dialog("请选择游戏难度", choices, "难度选择")
    print(f"用户选择: {choices[selected]}\n")

    # 5. 自定义三按钮弹窗
    print("5. 测试自定义三按钮弹窗")
    buttons = [
        {"text": "取消", "value": "cancel", "color": (150, 150, 150)},
        {"text": "保存", "value": "save", "color": (70, 180, 70)},
        {"text": "删除", "value": "delete", "color": (180, 70, 70)}
    ]
    result = pm.show_popup("文件已修改，请选择操作", "文件管理", buttons)
    print(f"用户操作: {result}\n")

    # 6. 多按钮选项弹窗
    print("6. 测试多按钮选项弹窗")
    buttons = [
        {"text": "故事1", "value": "story1", "color": (70, 130, 180)},
        {"text": "故事2", "value": "story2", "color": (70, 180, 70)},
        {"text": "故事3", "value": "story3", "color": (180, 140, 70)},
        {"text": "故事4", "value": "story4", "color": (180, 70, 180)},
        {"text": "随机", "value": "random", "color": (70, 180, 180)},
        {"text": "取消", "value": "cancel", "color": (150, 150, 150)}
    ]
    result = pm.show_popup("选择要阅读的故事", "故事选择", buttons, 500, 250)
    print(f"用户选择: {result}\n")

    print("=== 弹窗系统测试完成 ===")

if __name__ == "__main__":
    test_popup_system()
