# keymap

快捷键编辑器，网页版。给一套动作分配快捷键，冲突要当场发现。

纯静态、无构建、无依赖。

## 目录

```
samples/actions.json   可绑定快捷键的动作清单
samples/current.json   当前绑定（故意留了冲突）
```

## 动作格式

```json
{
  "actions": [
    { "id": "save", "name": "保存", "default": "Ctrl+S", "scope": "global" },
    { "id": "find", "name": "查找", "default": "Ctrl+F", "scope": "editor" }
  ]
}
```

## 键的写法

`Ctrl+Shift+S`、`Cmd+K`、`Alt+Enter`、`F5`、`Ctrl+ArrowUp`、`Ctrl+1`。
要有"按一下键盘自动识别"的录入方式，不用手打字符串。

## 重点

- 同一个作用域里两个动作绑到同一个组合键要报冲突，
  并且区分"完全一样"和"被更长组合键前缀吃掉"（绑了 `Ctrl+K` 又绑 `Ctrl+K S`）两种情况
- Mac 上 `Cmd` 和 Windows 上 `Ctrl` 要能分别配置，展示时按平台显示（⌘ / Ctrl）
- 单键绑定要拦住（比如只绑一个 `S`），要能自定义"允许单键"的白名单
- 重置单个动作、重置全部、导出/导入配置
- 绑定改了之后要有一块"试一试"的区域，按下去显示触发了哪个动作
