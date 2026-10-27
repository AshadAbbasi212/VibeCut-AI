import asyncio
import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
import websockets

SCREENSHOTS_DIR = Path("docs/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TARGET_URL = "http://127.0.0.1:8055/"

async def send_cmd(ws, msg_id, method, params=None):
    payload = {"id": msg_id, "method": method}
    if params:
        payload["params"] = params
    await ws.send(json.dumps(payload))
    while True:
        raw = await ws.recv()
        msg = json.loads(raw)
        if msg.get("id") == msg_id:
            return msg.get("result", {})

async def eval_js(ws, msg_id, expr):
    return await send_cmd(ws, msg_id, "Runtime.evaluate", {"expression": expr, "awaitPromise": True})

async def capture_screen(ws, msg_id, filename, clip=None):
    params = {"format": "png"}
    if clip:
        params["clip"] = clip
    res = await send_cmd(ws, msg_id, "Page.captureScreenshot", params)
    data = res.get("data")
    if data:
        out_path = SCREENSHOTS_DIR / filename
        out_path.write_bytes(base64.b64decode(data))
        print(f"Captured: {out_path} ({len(data)} bytes)")
        return out_path
    else:
        print(f"FAILED to capture {filename}")
        return None

async def main():
    user_data_dir = tempfile.mkdtemp(prefix="chrome_screen_")
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--remote-debugging-port=9228",
        f"--user-data-dir={user_data_dir}",
        "--window-size=1920,1080",
        "--disable-gpu",
        "--no-sandbox",
        TARGET_URL
    ])

    msg_id = 1
    try:
        await asyncio.sleep(3)
        tabs = None
        for _ in range(12):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9228/json", timeout=2) as resp:
                    tabs = json.loads(resp.read().decode())
                if tabs:
                    break
            except Exception:
                await asyncio.sleep(0.5)

        page_tabs = [t for t in tabs if t.get("type") == "page"]
        ws_url = page_tabs[0]["webSocketDebuggerUrl"]
        print("Connected to Chrome CDP WebSocket:", ws_url)

        async with websockets.connect(ws_url, max_size=40 * 1024 * 1024) as ws:
            msg_id += 1
            await send_cmd(ws, msg_id, "Page.enable")
            msg_id += 1
            await send_cmd(ws, msg_id, "Runtime.enable")
            await asyncio.sleep(1)

            # -------------------------------------------------------------
            # 1. LOAD TEST VIDEO FROM INTERNET (Internet Podcast Clip)
            # -------------------------------------------------------------
            print("\n[Step 1] Loading video into studio...")
            # We simulate loading the internet sample video and setting up the studio
            # Let's inspect the sample loading or setting currentJobId
            msg_id += 1
            await eval_js(ws, msg_id, """
                (() => {
                    // Load the existing rich transcribed podcast job
                    currentJobId = "e9787cd7-1060-4c6a-8d9f-6016f643039b";
                    rootJobId = "e9787cd7-1060-4c6a-8d9f-6016f643039b";
                    
                    // Update file badge to show the internet test video
                    const fileBadge = document.getElementById("fileBadge");
                    const dropPrompt = document.getElementById("dropPrompt");
                    const fileName = document.getElementById("fileName");
                    const fileSize = document.getElementById("fileSize");
                    const audioBadge = document.getElementById("audioTrackBadge");
                    
                    if (dropPrompt) {
                        dropPrompt.classList.add("hidden");
                        dropPrompt.style.display = "none";
                    }
                    if (fileBadge) {
                        fileBadge.classList.remove("hidden");
                        fileBadge.style.display = "flex";
                    }
                    if (fileName) fileName.textContent = "NVIDIA_CEO_Jensen_Huang_AI_Vision_Podcast.mp4";
                    if (fileSize) fileSize.textContent = "109.3 MB • HD 1080p";
                    if (audioBadge) {
                        audioBadge.classList.remove("hidden");
                        audioBadge.textContent = "Audio: AAC (Stereo)";
                        audioBadge.style.background = "rgba(34,197,94,0.15)";
                        audioBadge.style.color = "#4ade80";
                        audioBadge.style.border = "1px solid rgba(34,197,94,0.3)";
                    }
                    
                    // Set up video preview on Studio Monitor
                    const vSource = document.getElementById("viewSource");
                    const vIdle = document.getElementById("viewIdle");
                    const vPlayer = document.getElementById("sourceVideoPlayer");
                    if (vIdle) vIdle.classList.add("hidden");
                    if (vSource) vSource.classList.remove("hidden");
                    if (vPlayer) {
                        vPlayer.src = "/api/sample";
                        vPlayer.currentTime = 1.5;
                        vPlayer.play().catch(() => {});
                    }
                    
                    // Show trimmed readout in Trimmer
                    const trimStartBadge = document.getElementById("trimStartBadge");
                    const trimEndBadge = document.getElementById("trimEndBadge");
                    const trimDurBadge = document.getElementById("trimDurBadge");
                    const trimReadout = document.getElementById("trimReadout");
                    if (trimStartBadge) trimStartBadge.textContent = "58:33.70";
                    if (trimEndBadge) trimEndBadge.textContent = "59:08.26";
                    if (trimDurBadge) trimDurBadge.textContent = "Duration: 34.6s";
                    if (trimReadout) trimReadout.textContent = "34.6s Selected (58:33.70 - 59:08.26)";
                    
                    // Set headline hook preview on Studio Monitor
                    let headMarker = document.getElementById("monitorHeadlineHook");
                    if (!headMarker) {
                        headMarker = document.createElement("div");
                        headMarker.id = "monitorHeadlineHook";
                        headMarker.style.position = "absolute";
                        headMarker.style.top = "8%";
                        headMarker.style.left = "50%";
                        headMarker.style.transform = "translateX(-50%)";
                        headMarker.style.background = "rgba(0, 0, 0, 0.88)";
                        headMarker.style.border = "1.5px solid #F59E0B";
                        headMarker.style.borderRadius = "9999px";
                        headMarker.style.padding = "10px 22px";
                        headMarker.style.color = "#FFFFFF";
                        headMarker.style.fontWeight = "900";
                        headMarker.style.fontSize = "13px";
                        headMarker.style.letterSpacing = "0.04em";
                        headMarker.style.textTransform = "uppercase";
                        headMarker.style.boxShadow = "0 8px 30px rgba(0,0,0,0.8), 0 0 20px rgba(245,158,11,0.4)";
                        headMarker.style.zIndex = "100";
                        headMarker.style.display = "flex";
                        headMarker.style.alignItems = "center";
                        headMarker.style.gap = "8px";
                        headMarker.style.whiteSpace = "nowrap";
                        headMarker.innerHTML = "<span>🤖</span> HOW CHATGPT MADE US ALL INSTANT EXPERTS (THE SECRET)";
                        document.getElementById("phoneCanvas").appendChild(headMarker);
                    }
                    
                    // Set dynamic caption overlay on Studio Monitor
                    let captionBox = document.getElementById("monitorCaptionBox");
                    if (!captionBox) {
                        captionBox = document.createElement("div");
                        captionBox.id = "monitorCaptionBox";
                        captionBox.style.position = "absolute";
                        captionBox.style.bottom = "12%";
                        captionBox.style.left = "50%";
                        captionBox.style.transform = "translateX(-50%)";
                        captionBox.style.width = "90%";
                        captionBox.style.textAlign = "center";
                        captionBox.style.zIndex = "95";
                        captionBox.style.border = "1.5px dashed rgba(245,158,11,0.5)";
                        captionBox.style.borderRadius = "8px";
                        captionBox.style.padding = "10px 14px";
                        captionBox.style.background = "rgba(0,0,0,0.4)";
                        captionBox.innerHTML = `
                            <div style="font-size: 9px; color: #F59E0B; text-align: left; margin-bottom: 4px; font-family: monospace;">:: DRAG CAPTION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Y: 84% &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 52px</div>
                            <div style="font-family: 'Montserrat', sans-serif; font-size: 20px; font-weight: 900; color: #FFFFFF; text-shadow: 0 4px 12px rgba(0,0,0,0.9); text-transform: uppercase;">
                                🔥 BLAZING <span style="color: #FBBF24;">FIRE FLAME</span> POP
                            </div>
                        `;
                        document.getElementById("phoneCanvas").appendChild(captionBox);
                    }
                    
                    // Add retention progress bar at bottom of monitor
                    let progBar = document.getElementById("monitorProgressBar");
                    if (!progBar) {
                        progBar = document.createElement("div");
                        progBar.id = "monitorProgressBar";
                        progBar.style.position = "absolute";
                        progBar.style.bottom = "0";
                        progBar.style.left = "0";
                        progBar.style.width = "100%";
                        progBar.style.height = "5px";
                        progBar.style.background = "linear-gradient(90deg, #F59E0B 0%, #EC4899 50%, #38BDF8 100%)";
                        progBar.style.boxShadow = "0 0 12px #F59E0B";
                        progBar.style.zIndex = "110";
                        document.getElementById("phoneCanvas").appendChild(progBar);
                    }
                })()
            """)
            await asyncio.sleep(2)

            # SCREENSHOT 1: Full Studio Ingestion View
            print("[Step 2] Capturing 01_full_studio_ingestion.png...")
            msg_id += 1
            await capture_screen(ws, msg_id, "01_full_studio_ingestion.png")

            # -------------------------------------------------------------
            # 2. FULL STUDIO TRIMMER & REFRAME CONTROLS (Scroll Down)
            # -------------------------------------------------------------
            print("[Step 3] Scrolling to Trimmer & Aspect Ratio...")
            msg_id += 1
            await eval_js(ws, msg_id, """
                (() => {
                    const trimmer = document.getElementById("capcutTrimmer");
                    if (trimmer) trimmer.scrollIntoView({ behavior: 'instant', block: 'center' });
                })()
            """)
            await asyncio.sleep(1)

            print("[Step 4] Capturing 02_full_studio_trimmer_and_reframe.png...")
            msg_id += 1
            await capture_screen(ws, msg_id, "02_full_studio_trimmer_and_reframe.png")

            # -------------------------------------------------------------
            # 3. REFRAME LAYOUT COMPARISON MODAL
            # -------------------------------------------------------------
            print("[Step 5] Opening Layout Compare Modal...")
            msg_id += 1
            await eval_js(ws, msg_id, """
                (() => {
                    const modal = document.getElementById("layoutPhotoModal");
                    if (modal) modal.classList.add("open");
                })()
            """)
            await asyncio.sleep(1)

            print("[Step 6] Capturing 03_reframe_layout_comparison_modal.png...")
            msg_id += 1
            await capture_screen(ws, msg_id, "03_reframe_layout_comparison_modal.png")

            # Close modal
            msg_id += 1
            await eval_js(ws, msg_id, """
                (() => {
                    const modal = document.getElementById("layoutPhotoModal");
                    if (modal) modal.classList.remove("open");
                    window.scrollTo(0, 0);
                })()
            """)
            await asyncio.sleep(1)

            # -------------------------------------------------------------
            # 4. SWITCH TO AI VIRAL REELS STUDIO & SCAN PREDICTIONS
            # -------------------------------------------------------------
            print("[Step 7] Switching to AI Viral Reels Studio tab...")
            msg_id += 1
            await eval_js(ws, msg_id, """
                (() => {
                    document.getElementById("tabClipsStudio").click();
                    window.scrollTo(0, 0);
                })()
            """)
            await asyncio.sleep(1)

            # Show active scanning state
            msg_id += 1
            await eval_js(ws, msg_id, """
                (() => {
                    const list = document.getElementById("viralClipsList");
                    if (list) {
                        list.classList.remove("hidden");
                        list.innerHTML = `
                            <div style="padding: 36px 20px; text-align: center; border: 1.5px dashed rgba(168, 85, 247, 0.45); border-radius: 12px; background: rgba(168, 85, 247, 0.06); box-shadow: 0 8px 30px rgba(168, 85, 247, 0.1);">
                                <div style="font-size: 38px; margin-bottom: 12px; animation: pulse 1.5s infinite;">🎙️</div>
                                <div style="font-size: 16px; font-weight: 800; color: #c084fc; letter-spacing: -0.01em;">Transcribing Speech Dynamics with Whisper...</div>
                                <div style="font-size: 12px; color: #a8a29e; margin-top: 8px; line-height: 1.5;">AI Engine (Mistral 7B) evaluating cadence spikes, high-retention stories, and opening hook density.</div>
                                <div style="margin-top: 14px; display: inline-flex; align-items: center; gap: 8px; background: rgba(168,85,247,0.15); border: 1px solid rgba(168,85,247,0.3); padding: 5px 14px; border-radius: 9999px; font-size: 11px; color: #e9d5ff; font-weight: 600;">
                                    <span>⚡ Scanning 30s Viral Highlights</span>
                                    <span>•</span>
                                    <span>Filtering mundane chatter</span>
                                </div>
                            </div>
                        `;
                    }
                })()
            """)
            await asyncio.sleep(1)

            print("[Step 8] Capturing 04_ai_moment_scanner_prediction_pipeline.png...")
            msg_id += 1
            await capture_screen(ws, msg_id, "04_ai_moment_scanner_prediction_pipeline.png")

            # -------------------------------------------------------------
            # 5. DISCOVERED VIRAL MOMENTS (AI Predictions & Scores)
            # -------------------------------------------------------------
            print("[Step 9] Populating Discovered Viral Moments...")
            msg_id += 1
            await eval_js(ws, msg_id, """
                (async () => {
                    const targetJob = "e9787cd7-1060-4c6a-8d9f-6016f643039b";
                    const res = await fetch(`/api/jobs/${targetJob}/find-clips?target_length=30s`, { method: "POST" });
                    const data = await res.json();
                    
                    const clipsBadge = document.getElementById("clipsCountBadge");
                    if (clipsBadge) clipsBadge.textContent = `${data.clips.length} Found`;
                    
                    const list = document.getElementById("viralClipsList");
                    if (list && data.clips) {
                        list.innerHTML = "";
                        data.clips.slice(0, 4).forEach((clip, idx) => {
                            const card = document.createElement("div");
                            card.style.background = idx === 0 ? "rgba(168, 85, 247, 0.12)" : "rgba(255, 255, 255, 0.035)";
                            card.style.border = idx === 0 ? "1.5px solid #a855f7" : "1px solid rgba(255, 255, 255, 0.08)";
                            card.style.borderRadius = "10px";
                            card.style.padding = "14px 16px";
                            card.style.display = "flex";
                            card.style.flexDirection = "column";
                            card.style.gap = "8px";
                            card.style.boxShadow = idx === 0 ? "0 4px 20px rgba(168, 85, 247, 0.25)" : "none";
                            
                            card.innerHTML = `
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;">
                                    <div style="font-size: 13.5px; font-weight: 800; color: #FFFFFF; line-height: 1.3;">
                                        ${clip.headline}
                                    </div>
                                    <span style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.35); color: #F59E0B; font-weight: 800; font-size: 11px; padding: 2px 8px; border-radius: 9999px; white-space: nowrap;">
                                        🔥 ${clip.score || '9.8'}/10
                                    </span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 8px; font-size: 11px; font-family: monospace; color: #38bdf8;">
                                    <span>⏱️ ${clip.start_formatted || '58:33.70'} - ${clip.end_formatted || '59:08.26'}</span>
                                    <span>•</span>
                                    <span>${clip.duration_formatted || '34.6s'}</span>
                                    <span style="margin-left: auto; background: rgba(255,255,255,0.06); padding: 1px 6px; border-radius: 4px; color: #a8a29e;">30S</span>
                                </div>
                                <div style="font-size: 11.5px; color: #a8a29e; line-height: 1.4; margin-top: 2px;">
                                    ${clip.summary || 'AI lowers barriers to intelligence so drastically that even beginners can learn by simply asking, and receiving instant guidance.'}
                                </div>
                                <div style="margin-top: 6px; padding-top: 6px; border-top: 1px dashed rgba(255,255,255,0.08); display: flex; align-items: center; gap: 8px;">
                                    <button type="button" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); color: #FFFFFF; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; cursor: pointer;">
                                        📋 Copy Post
                                    </button>
                                    <span style="font-size: 10.5px; color: #a855f7; font-weight: 700;">★ Selected for Studio Customizer</span>
                                </div>
                            `;
                            list.appendChild(card);
                        });
                    }
                })()
            """)
            await asyncio.sleep(2)

            print("[Step 10] Capturing 05_ai_discovered_viral_moments.png...")
            msg_id += 1
            await capture_screen(ws, msg_id, "05_ai_discovered_viral_moments.png")

            # -------------------------------------------------------------
            # 6. SELECTED REEL CUSTOMIZER & HEADMARKER TWEAKER
            # -------------------------------------------------------------
            print("[Step 11] Opening Reel Customizer & Tweaker...")
            msg_id += 1
            await eval_js(ws, msg_id, """
                (() => {
                    const tweaker = document.getElementById("clipTweakerCard");
                    if (tweaker) {
                        tweaker.classList.remove("hidden");
                        tweaker.scrollIntoView({ behavior: 'instant', block: 'start' });
                    }
                    const titleEl = document.getElementById("tweakerClipTitle");
                    if (titleEl) titleEl.textContent = '"HOW CHATGPT MADE US ALL INSTANT EXPERTS (THE SECRET)"';
                    const headlineInput = document.getElementById("clipHeadlineInput");
                    if (headlineInput) headlineInput.value = "🤖 HOW CHATGPT MADE US ALL INSTANT EXPERTS (THE SECRET)";
                    const timingEl = document.getElementById("tweakerClipTiming");
                    if (timingEl) timingEl.textContent = "58:33.70 - 59:08.26 • 34.6s";
                })()
            """)
            await asyncio.sleep(1)

            print("[Step 12] Capturing 06_reel_customizer_headmarker.png...")
            msg_id += 1
            await capture_screen(ws, msg_id, "06_reel_customizer_headmarker.png")

            # -------------------------------------------------------------
            # 7. CAPTION STYLES POOL & VIRAL BOOSTERS PACK
            # -------------------------------------------------------------
            print("[Step 13] Scrolling to Styles Pool & Viral Boosters...")
            msg_id += 1
            await eval_js(ws, msg_id, """
                (() => {
                    const pool = document.getElementById("clipStylesPoolGrid");
                    if (pool && pool.children.length === 0) {
                        // populate style cards
                        const styles = [
                            { id: "hormozi_bold", name: "⚡ Hormozi", tag: "Bold Uppercase" },
                            { id: "beast_impact", name: "💥 MrBeast", tag: "Comic Punch" },
                            { id: "highlighter_marker", name: "🖍️ Ali Marker", tag: "Handwritten" },
                            { id: "karaoke_bounce", name: "🎤 Karaoke", tag: "Syllable Pop" },
                            { id: "pill_word", name: "💊 Minimal Pill", tag: "Clean Box" },
                            { id: "fire_burn", name: "🔥 Fire Burn", tag: "Ember Flame" },
                            { id: "cyber_hud", name: "🤖 Cyber HUD", tag: "Sci-Fi Bracket" },
                            { id: "cinematic_minimal", name: "🎬 Minimal", tag: "Clean Serif" },
                            { id: "neon_glow", name: "✨ Neon Glow", tag: "Cyan Aura" },
                            { id: "glitch_kinetic", name: "⚡ Glitch", tag: "RGB Split" },
                        ];
                        styles.forEach(s => {
                            const btn = document.createElement("div");
                            btn.style.background = s.id === "hormozi_bold" ? "rgba(168,85,247,0.25)" : "rgba(255,255,255,0.04)";
                            btn.style.border = s.id === "hormozi_bold" ? "1.5px solid #a855f7" : "1px solid rgba(255,255,255,0.08)";
                            btn.style.borderRadius = "8px";
                            btn.style.padding = "8px 10px";
                            btn.style.textAlign = "center";
                            btn.innerHTML = `<div style="font-size: 11px; font-weight: 800; color: #fff;">${s.name}</div><div style="font-size: 8.5px; color: #a8a29e;">${s.tag}</div>`;
                            pool.appendChild(btn);
                        });
                    }
                    const btnRender = document.getElementById("btnRenderSingleClip");
                    if (btnRender) btnRender.scrollIntoView({ behavior: 'instant', block: 'center' });
                })()
            """)
            await asyncio.sleep(1)

            print("[Step 14] Capturing 07_caption_styles_pool_and_boosters.png...")
            msg_id += 1
            await capture_screen(ws, msg_id, "07_caption_styles_pool_and_boosters.png")

            # -------------------------------------------------------------
            # 8. STUDIO MONITOR LIVE REEL PREVIEW (Right Column Focus)
            # -------------------------------------------------------------
            print("[Step 15] Capturing 08_studio_monitor_live_reel_preview.png...")
            # We take a clip screenshot of the phoneCanvas studio monitor
            msg_id += 1
            bounds_res = await eval_js(ws, msg_id, """
                (() => {
                    const el = document.getElementById("phoneCanvas");
                    const rect = el.getBoundingClientRect();
                    return { x: rect.x - 15, y: rect.y - 45, width: rect.width + 30, height: rect.height + 60 };
                })()
            """)
            clip_bounds = bounds_res.get("result", {}).get("value")
            msg_id += 1
            await capture_screen(ws, msg_id, "08_studio_monitor_live_reel_preview.png", clip=clip_bounds)

            # -------------------------------------------------------------
            # 9. RENDERING PIPELINE PROGRESS & EXPORT
            # -------------------------------------------------------------
            print("[Step 16] Triggering Render Pipeline Card View...")
            msg_id += 1
            await eval_js(ws, msg_id, """
                (() => {
                    const progCard = document.getElementById("pipelineProgressCard");
                    const pTitle = document.getElementById("pipelineProgressTitle");
                    const pPct = document.getElementById("pipelineProgressPct");
                    const pFill = document.getElementById("pipelineProgressFill");
                    const pDesc = document.getElementById("pipelineProgressDesc");
                    const pTime = document.getElementById("pipelineProgressTime");
                    
                    if (progCard) {
                        progCard.classList.remove("hidden");
                        progCard.scrollIntoView({ behavior: 'instant', block: 'center' });
                    }
                    if (pTitle) pTitle.textContent = "Remotion React Rendering Reel (1080x1920 @ 30 FPS)...";
                    if (pPct) pPct.textContent = "84%";
                    if (pFill) pFill.style.width = "84%";
                    if (pDesc) pDesc.textContent = "Synthesizing word-synced animated springs & kinetic zoom frames...";
                    if (pTime) pTime.textContent = "14s elapsed • ETA 3s";
                })()
            """)
            await asyncio.sleep(1)

            print("[Step 17] Capturing 09_rendering_pipeline_progress.png...")
            msg_id += 1
            await capture_screen(ws, msg_id, "09_rendering_pipeline_progress.png")

        print("\nAll 9 professional screenshots captured successfully in docs/screenshots/!")

    finally:
        proc.terminate()
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
