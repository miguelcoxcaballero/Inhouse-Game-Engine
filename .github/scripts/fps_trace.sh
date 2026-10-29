#!/usr/bin/env bash
# fps-debug: runs the sandbox with --frame-trace in several configurations
# and keeps every log in smoke/. Usage: fps_trace.sh <set>
set -u
cd "$(dirname "$0")/../../engine"
mkdir -p smoke
EXE=./target/release/sandbox.exe
export FORJA_NO_FETCH=1 RUST_BACKTRACE=1
export RUST_LOG=${RUST_LOG:-info,wgpu_core=warn,wgpu_hal=warn,naga=warn}
TR=20
run() { # name timeout-seconds args...
  local name=$1 t=$2; shift 2
  echo "::group::$name: $*"
  local t0=$(date +%s)
  timeout "$t" "$EXE" "$@" --frame-trace $TR --screenshot "smoke/$name.png" 2>&1 | tee "smoke/$name.log" | grep -E "trace |SMOKE|surface:|frame trace|world built|uploaded|world ready|static set|graphics:|panicked|error" | cut -c1-3000
  echo "exit ${PIPESTATUS[0]} after $(( $(date +%s) - t0 )) s" | tee -a "smoke/$name.log"
  echo "::endgroup::"
}
case "$1" in
  headless)
    run h-track-64-low 900 --smoke 200 --map track --adapter warp --preset low --size 64x36
    run h-track-64-high 900 --smoke 200 --map track --adapter warp --preset high --size 64x36
    run h-track-320-low 900 --smoke 200 --map track --adapter warp --preset low --size 320x180
    run h-spain-64-low 1800 --smoke 200 --adapter warp --preset low --size 64x36
    run h-spain-64-high 1800 --smoke 200 --adapter warp --preset high --size 64x36
    run h-spain-320-low 1800 --smoke 120 --adapter warp --preset low --size 320x180
    FORJA_NO_STREAM=1 run h-spain-64-low-nostream 1800 --smoke 200 --adapter warp --preset low --size 64x36
    ;;
  window)
    run w-track-64-low 900 --smoke 200 --window --map track --adapter warp --preset low --size 64x36
    run w-track-64-high 900 --smoke 200 --window --map track --adapter warp --preset high --size 64x36
    run w-track-320-low 900 --smoke 200 --window --map track --adapter warp --preset low --size 320x180
    run w-spain-64-low 1800 --smoke 200 --window --adapter warp --preset low --size 64x36
    run w-spain-64-high 1800 --smoke 200 --window --adapter warp --preset high --size 64x36
    run w-spain-320-low 1800 --smoke 120 --window --adapter warp --preset low --size 320x180
    run w-spain-320-high 1800 --smoke 120 --window --adapter warp --preset high --size 320x180
    ;;
  variants)
    FORJA_NO_STREAM=1 run w-spain-64-low-nostream 1800 --smoke 200 --window --adapter warp --preset low --size 64x36
    FORJA_NO_TIME_REBUILD=1 run w-spain-64-low-norebuild 1800 --smoke 200 --window --adapter warp --preset low --size 64x36
    FORJA_NO_STREAM=1 FORJA_NO_TIME_REBUILD=1 RUST_LOG=warn run w-spain-64-low-quiet 1800 --smoke 200 --window --adapter warp --preset low --size 64x36
    # Log straight into a file (no pipe).
    echo "::group::w-spain-64-low-file"
    t0=$(date +%s)
    FORJA_TRACE_FILE=smoke/w-spain-64-low-file.trace timeout 1800 $EXE --smoke 200 --window --adapter warp --preset low --size 64x36 --frame-trace $TR --screenshot smoke/w-spain-64-low-file.png > smoke/w-spain-64-low-file.log 2>&1
    echo "exit $? after $(( $(date +%s) - t0 )) s"; cat smoke/w-spain-64-low-file.trace; grep -E "SMOKE|surface:" smoke/w-spain-64-low-file.log
    echo "::endgroup::"
    # Log into a real console window (conhost), as Jugar.bat does.
    echo "::group::w-spain-64-low-console"
    t0=$(date +%s)
    printf '@echo off\r\nstart "forja" /wait target\\release\\sandbox.exe %%*\r\nexit /b %%errorlevel%%\r\n' > console.bat
    cat console.bat
    MSYS_NO_PATHCONV=1 FORJA_TRACE_FILE=smoke/w-spain-64-low-console.trace timeout 1800 cmd /c console.bat --smoke 200 --window --adapter warp --preset low --size 64x36 --frame-trace $TR --screenshot smoke/w-spain-64-low-console.png
    echo "exit $? after $(( $(date +%s) - t0 )) s"; cat smoke/w-spain-64-low-console.trace
    echo "::endgroup::"
    # No v-sync (Mailbox/Immediate) and one frame of latency.
    cp data/graphics.toml data/graphics.toml.bak
    sed -i -e 's/^vsync = true/vsync = false/' -e 's/^frame_latency = 2/frame_latency = 1/' data/graphics.toml
    run w-spain-64-low-novsync 1800 --smoke 200 --window --adapter warp --preset low --size 64x36
    mv data/graphics.toml.bak data/graphics.toml
    ;;
  profile)
    # Sampling profiles (samply, ETW) of the main configurations, to split
    # CPU time between the game, wgpu-core/hal and the D3D12/WARP driver.
    mkdir -p ../samply
    if ! gh release download -R mstange/samply --pattern '*x86_64-pc-windows-msvc.zip' -D ../samply; then
      cargo install samply --locked --root ../samply
    fi
    (cd ../samply && ls && for z in *.zip; do [ -f "$z" ] && unzip -o -q "$z"; done; ls -R | head -20)
    SAMPLY=$(find ../samply -name samply.exe | head -1)
    echo "samply: $SAMPLY"; "$SAMPLY" --version
    prof() { # name frames args...
      local name=$1 fr=$2; shift 2
      echo "::group::$name: $*"
      local t0=$(date +%s)
      timeout 1800 "$SAMPLY" record --save-only --unstable-presymbolicate --symbol-dir "$(pwd)/target/release" --windows-symbol-server https://msdl.microsoft.com/download/symbols --windows-symbol-cache "$(pwd)/../symcache" -o "smoke/$name.json.gz" -- "$EXE" --smoke "$fr" "$@" --frame-trace $TR > "smoke/$name.log" 2>&1
      echo "exit $? after $(( $(date +%s) - t0 )) s"
      if [ ! -f "smoke/$name.json.gz" ]; then
        head -20 "smoke/$name.log"
        timeout 1800 "$SAMPLY" record --save-only --unstable-presymbolicate -o "smoke/$name.json.gz" -- "$EXE" --smoke "$fr" "$@" --frame-trace $TR > "smoke/$name.log" 2>&1
        echo "retry without symbol flags: exit $?"
      fi
      grep -E "trace .*f(80|160)-|SMOKE|surface:|samply|rror" "smoke/$name.log" | cut -c1-2500
      ls -la smoke/ | grep "$name"
      python ../.github/scripts/prof_summary.py "smoke/$name.json.gz" "$fr" 20 2>&1 | cut -c1-400
      echo "::endgroup::"
    }
    prof p-w-spain-64-low 200 --window --adapter warp --preset low --size 64x36
    prof p-h-spain-64-low 200 --adapter warp --preset low --size 64x36
    prof p-w-track-64-low 200 --window --map track --adapter warp --preset low --size 64x36
    ;;
esac
exit 0
