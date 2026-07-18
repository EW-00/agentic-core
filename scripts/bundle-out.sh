#!/usr/bin/env bash
# bundle-out.sh — 客户机端：把 workspace 的项目状态打包成单个可上传 SharePoint 的文件夹
#
# 用法： ./bundle-out.sh [--workspace DIR] [--out DIR]
# 产物： <out>/transfer_out_<YYYYMMDD_HHMM>/
#          repos/<study>__<repo>.bundle     每个 git repo 的全量 bundle（含所有分支）
#          repos/MANIFEST.txt               repo 路径 ↔ bundle 文件名 ↔ 当前分支
#          docs/                            projects/*/docs + handoffs（非 git 文件）
#          workspace/                       STUDY.md、.windsurf/rules/study-*.md
#        以及同名 .zip（直接拖进 SharePoint）
#
# ⚠️ 使用前提：该传输管道已获 EM 书面许可（见 Day-1 checklist §D）。
set -euo pipefail

WORKSPACE="$HOME/workspace"
OUT="$HOME"
while [ $# -gt 0 ]; do
  case "$1" in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
done

STAMP="$(date +%Y%m%d_%H%M)"
DEST="$OUT/transfer_out_$STAMP"
mkdir -p "$DEST/repos" "$DEST/docs" "$DEST/workspace"

echo "打包 workspace: $WORKSPACE"

# ---- git repos → bundles -------------------------------------------------
found=0
for repo in "$WORKSPACE"/projects/*/repos/*/; do
  [ -d "$repo/.git" ] || continue
  found=$((found+1))
  study="$(basename "$(dirname "$(dirname "$repo")")")"
  name="$(basename "$repo")"
  bundle="$DEST/repos/${study}__${name}.bundle"
  branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"
  dirty="$(git -C "$repo" status --porcelain | wc -l | tr -d ' ')"
  if [ "$dirty" != 0 ]; then
    echo "  ! $study/$name 有 $dirty 个未提交改动 —— bundle 只含已 commit 内容，先 commit 或自行取舍"
  fi
  git -C "$repo" bundle create "$bundle" --all >/dev/null 2>&1
  printf '%s\t%s\t%s\n' "projects/$study/repos/$name" "$(basename "$bundle")" "$branch" \
    >> "$DEST/repos/MANIFEST.txt"
  echo "  ✓ $study/$name → $(basename "$bundle")（当前分支 $branch）"
done
[ "$found" = 0 ] && echo "  ! projects/*/repos/ 下没有找到 git repo"

# ---- 非 git 的项目文档 -----------------------------------------------------
for d in docs notes handoffs; do
  for p in "$WORKSPACE"/projects/*/"$d"/; do
    [ -d "$p" ] || continue
    study="$(basename "$(dirname "$p")")"
    mkdir -p "$DEST/docs/$study"
    cp -R "$p" "$DEST/docs/$study/$d"
  done
done
echo "  ✓ 项目 docs/notes/handoffs"

# ---- workspace 层 ----------------------------------------------------------
[ -f "$WORKSPACE/STUDY.md" ] && cp "$WORKSPACE/STUDY.md" "$DEST/workspace/"
if ls "$WORKSPACE"/.windsurf/rules/study-*.md >/dev/null 2>&1; then
  mkdir -p "$DEST/workspace/windsurf-rules"
  cp "$WORKSPACE"/.windsurf/rules/study-*.md "$DEST/workspace/windsurf-rules/"
fi
echo "  ✓ STUDY.md + study rules"

# ---- zip -------------------------------------------------------------------
( cd "$OUT" && zip -rq "transfer_out_$STAMP.zip" "transfer_out_$STAMP" )
echo
echo "完成：$OUT/transfer_out_$STAMP.zip → 上传 SharePoint，在对端跑 apply-in.sh"
