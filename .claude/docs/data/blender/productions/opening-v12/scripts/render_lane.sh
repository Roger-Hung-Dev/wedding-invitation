#!/usr/bin/env bash
# 用法：bash lane.sh <lane名> <幕:層> ...   例：bash lane.sh A 03:beauty 05:beauty 08:beauty,cast
export TEMP='D:\render-work\tmp' TMP='D:\render-work\tmp' PYTHONUNBUFFERED=1
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
S="D:/SideProject/wedding-invitation/.claude/docs/data/blender/productions/opening-v12/scripts"
B="D:/SideProject/wedding-invitation/.claude/docs/data/blender/productions/opening-v12/blend/couple.blend"
lane=$1; shift
for job in "$@"; do
  shot=${job%%:*}; layers=${job#*:}
  echo "[$lane] $(date +%T) START $shot $layers"
  "$BL" -b "$B" -P "$S/prod_cli.py" -- --run run_prod MODE=full SHOT=$shot LAYERS=$layers > "D:/render-work/opening-v12/logs/full_$shot.log" 2>&1
  echo "[$lane] $(date +%T) END $shot: $(grep -E 'FULL|BL_CLI_FAIL|QA_FEET' D:/render-work/opening-v12/logs/full_$shot.log | tr '\n' ' ')"
done
echo "[$lane] $(date +%T) LANE_DONE"
