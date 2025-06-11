# pyright: reportInvalidTypeForm=false
bl_info = {
    "name": "MikuMikuRig",  # 插件名字
    "author": "William",  # 作者名字
    "version": (0, 5, 7, 0),  # 插件版本
    "blender": (4, 0, 0),  # 建议更新到较新的Blender版本，例如4.0
    "location": "3DView > Tools",  # 插件所在位置
    "description": "快速为各种人形模型生成rigify控制器,一键套mixamo动作",  # 描述
    "support": 'COMMUNITY',  # 支持等级（社区支持）
    "category": "Rigging",  # 分类
}

from . import animation, extra, cloth, settings, translation

# 需要调用其 register/unregister 方法的模块列表
modules_to_register = (
    settings,
    animation,
    cloth,
    extra,
    translation,
)

def register():  # 启用插件时候执行
    # 调用其他模块的 register 函数
    for module in modules_to_register:
        module.register()

    print(f"Registered: {bl_info['name']} version {bl_info['version']}")

def unregister():  # 关闭插件时候执行
    # 以相反的顺序调用其他模块的 unregister 函数
    for module in reversed(modules_to_register):
        module.unregister()

    print(f"Unregistered: {bl_info['name']}")
