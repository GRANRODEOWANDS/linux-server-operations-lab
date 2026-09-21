# Linux Server Operations Lab

Excel × Python × Ansible × Linux を組み合わせて、
Linuxサーバ3台の管理・点検・操作・障害復旧を自動化する検証プロジェクトです。

単純にAnsibleのPlaybookを実行するだけではなく、

- Excelをサーバ管理台帳として使用
- PythonでExcelを読み込む
- Ansible Inventoryを自動生成
- Linuxサーバを一括点検
- Ansibleの実行結果をPythonで解析
- 点検結果をExcelへ自動書き戻し
- ExcelからLinuxへの操作指示
- 障害検知と復旧
- Excelダッシュボードで状態を可視化

までを一連の流れとして構築しました。

---

## プロジェクト構成

```text
Excel
  ↓
Python
  ↓
Ansible
  ↓
Linux Servers
  ↓
Pythonで結果解析
  ↓
Excelへ書き戻し
