#!/usr/bin/env bash
# apply-in.sh — 接收端：把 bundle-out.sh 的产物应用到本机 workspace
#
# 用法： ./apply-in.sh <transfer_out_目录或zip> [--workspace DIR]
# 行为：
#   - repo 已存在 → git fetch <bundle> 全部分支到 transfer/* 引用，并提示如何合并
#     （不自动 merge —— 本机可能有本地改动，合并动作留给你/agent 决策）
#   - repo 不存在 → 直接从 bundle clone，checkout MANIFEST 记录的分支
#   - docs/workspace 文件 → 拷贝覆盖前先把旧版备份为 *.pre_transfer
#
# 反向（McKinsey 机改完 → 客户机）：同样用 bundle-out.sh / apply-in.sh，方向对称。
set -euo pipefail

SRC="${1:?用法: apply-in.sh <transfer_out_目录或zip> [--workspace DIR]}"; shift || true
WORKSPACE="$HOME/workspace"
while [ $# -gt 0 ]; do
  case "$1" in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
done

case "$SRC" in
  *.zip) tmp="$(mktemp -d)"; unzip -q "$SRC" -d "$tmp"; SRC="$(find "$tmp" -maxdepth 1 -type d -name 'transfer_out_*' | head -1)" ;;
esac
[ -f "$SRC/repos/MANIFEST.txt" ] || { echo "MANIFEST.txt 缺失：$SRC 不是有效的 transfer 目录" >&2; exit 1; }

echo "应用 transfer: $SRC → $WORKSPACE"

# ---- repos -------------------------------------------------------------
while IFS=$'\t' read -r relpath bundlefile branch; do
  bundle="$SRC/repos/$bundlefile"
  target="$WORKSPACE/$relpath"
  if [ -d "$target/.git" ]; then
    git -C "$target" fetch -q "$bundle" '+refs/heads/*:refs/transfer/*'
    echo "  ✓ $relpath：bundle 已 fetch 到 refs/transfer/*"
    echo "      合并示例：git -C $target merge refs/transfer/$branch   （或先 diff 审阅）"
  else
    mkdir -p "$(dirname "$target")"
    git clone -q "$bundle" "$target"
    git -C "$target" checkout -q "$branch"
    echo "  ✓ $relpath：从 bundle 新建（分支 $branch）"
  fi
done < "$SRC/repos/MANIFEST.txt"

# ---- docs（覆盖前备份） ----------------------------------------------------
if [ -d "$SRC/docs" ]; then
  ( cd "$SRC/docs" && find . -type f ) | while read -r f; do
    rel="${f#./}"
    dest="$WORKSPACE/projects/$rel"
    mkdir -p "$(dirname "$dest")"
    [ -f "$dest" ] && cp "$dest" "$dest.pre_transfer"
    cp "$SRC/docs/$rel" "$dest"
  done
  echo "  ✓ 项目 docs 已应用（被覆盖的旧文件保留为 *.pre_transfer）"
fi

# ---- workspace 层 -----------------------------------------------------------
if [ -f "$SRC/workspace/STUDY.md" ]; then
  [ -f "$WORKSPACE/STUDY.md" ] && cp "$WORKSPACE/STUDY.md" "$WORKSPACE/STUDY.md.pre_transfer"
  cp "$SRC/workspace/STUDY.md" "$WORKSPACE/STUDY.md"
  echo "  ✓ STUDY.md 已应用（旧版 → STUDY.md.pre_transfer）"
fi
if [ -d "$SRC/workspace/windsurf-rules" ]; then
  mkdir -p "$WORKSPACE/.windsurf/rules"
  cp "$SRC/workspace/windsurf-rules/"*.md "$WORKSPACE/.windsurf/rules/"
  echo "  ✓ study-*.md rules 已应用"
fi

echo
echo "完成。repo 的合并动作是留给你的：先审 refs/transfer/* 再 merge。"
