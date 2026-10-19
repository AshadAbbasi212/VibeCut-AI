/**
 * Dynamic Captions Studio Pro — Professional Frontend Application
 * Fully integrated with Remotion, faster-whisper, and FastAPI backend.
 */

document.addEventListener("DOMContentLoaded", () => {
  // =========================================================================
  // DOM Element References
  // =========================================================================

  // Top Nav & Health
  const engineStatusBadge = document.getElementById("engineStatusBadge");
  const engineStatusText = document.getElementById("engineStatusText");
  const sampleQuickBtn = document.getElementById("sampleQuickBtn");

  // Dock Tabs
  const dockTabs = document.querySelectorAll(".dock-tab");
  const dockPanes = document.querySelectorAll(".dock-tab-pane");
  const tabEditorBtn = document.getElementById("tabEditorBtn");
  const captionCountBadge = document.getElementById("captionCountBadge");

  // Tab 1: Video & Trim
  const dropZone = document.getElementById("dropZone");
  const videoFileInput = document.getElementById("videoFileInput");
  const browseBtn = document.getElementById("browseBtn");
  const dropPrompt = document.getElementById("dropPrompt");
  const fileBadge = document.getElementById("fileBadge");
  const fileName = document.getElementById("fileName");
  const fileSize = document.getElementById("fileSize");
  const fileDurationTag = document.getElementById("fileDurationTag");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const loadSampleBtn = document.getElementById("loadSampleBtn");

  const trimStart = document.getElementById("trimStart");
  const trimEnd = document.getElementById("trimEnd");
  const trim15sBtn = document.getElementById("trim15sBtn");
  const trim30sBtn = document.getElementById("trim30sBtn");
  const trim60sBtn = document.getElementById("trim60sBtn");
  const trimResetBtn = document.getElementById("trimResetBtn");

  // Tab 2: Styles & Engine
  const presetCards = document.querySelectorAll(".pro-preset-card");
  const llmProviderSelect = document.getElementById("llmProvider");
  const videoLanguageSelect = document.getElementById("videoLanguage");
  const renderConcurrencySelect = document.getElementById("renderConcurrency");
  const draftToggle = document.getElementById("draftToggle");

  // Action Button
  const startJobBtn = document.getElementById("startJobBtn");
  const startJobBtnText = document.getElementById("startJobBtnText");

  // Tab 3: Caption Editor
  const editorEmptyState = document.getElementById("editorEmptyState");
  const timelineEditorContainer = document.getElementById("timelineEditorContainer");
  const phraseEditorList = document.getElementById("phraseEditorList");
  const editorPhraseCount = document.getElementById("editorPhraseCount");
  const editorDurationVal = document.getElementById("editorDurationVal");
  const saveEditsBtn = document.getElementById("saveEditsBtn");
  const rerenderBtn = document.getElementById("rerenderBtn");

  // Tab 4: Exports
  const exportVideoBtn = document.getElementById("exportVideoBtn");
  const exportSrtBtn = document.getElementById("exportSrtBtn");
  const exportVttBtn = document.getElementById("exportVttBtn");
  const exportJsonBtn = document.getElementById("exportJsonBtn");
  const jsonDrawer = document.getElementById("jsonDrawer");
  const jsonCodeView = document.getElementById("jsonCodeView");
  const copyJsonBtn = document.getElementById("copyJsonBtn");

  // Stage Panel & Views
  const stageStatusTag = document.getElementById("stageStatusTag");
  const viewIdle = document.getElementById("viewIdle");
  const viewProcessing = document.getElementById("viewProcessing");
  const viewResult = document.getElementById("viewResult");

  // Processing Elements
  const processingPercentText = document.getElementById("processingPercentText");
  const processingHeading = document.getElementById("processingHeading");
  const processingStepDescription = document.getElementById("processingStepDescription");
  const progressBarFill = document.getElementById("progressBarFill");
  const progressTimeElapsed = document.getElementById("progressTimeElapsed");

  // Result Video Player
  const studioResultVideo = document.getElementById("studioResultVideo");
  const overlayPlayBtn = document.getElementById("overlayPlayBtn");
  const playPauseBtn = document.getElementById("playPauseBtn");
  const playIcon = document.getElementById("playIcon");
  const stepBackBtn = document.getElementById("stepBackBtn");
  const stepForwardBtn = document.getElementById("stepForwardBtn");
  const currentTimeDisplay = document.getElementById("currentTimeDisplay");
  const durationDisplay = document.getElementById("durationDisplay");
  const timelineScrubber = document.getElementById("timelineScrubber");
  const scrubberPlayed = document.getElementById("scrubberPlayed");
  const speedToggleBtn = document.getElementById("speedToggleBtn");
  const muteToggleBtn = document.getElementById("muteToggleBtn");
  const fullscreenBtn = document.getElementById("fullscreenBtn");

  const quickDownloadMp4Btn = document.getElementById("quickDownloadMp4Btn");
  const editCaptionsJumpBtn = document.getElementById("editCaptionsJumpBtn");
  const newJobBtn = document.getElementById("newJobBtn");

  // Style Gallery & Sandbox
  const sandboxTextInput = document.getElementById("sandboxTextInput");
  const galleryFilterChips = document.querySelectorAll(".filter-chip");
  const galleryGrid = document.getElementById("galleryGrid");
  const toastShelf = document.getElementById("toastShelf");

  // =========================================================================
  // State Management
  // =========================================================================
  let selectedFile = null;
  let currentJobId = null;
  let pollInterval = null;
  let jobStartTime = null;
  let currentTimeline = null;
  let availableStyles = [];
  let isTimelineDirty = false;

  // =========================================================================
  // 1. Initial Engine Health Check & Style Catalog Fetch
  // =========================================================================
  async function checkEngineHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        engineStatusText.textContent = `Remotion v4 Core Ready • v${data.version}`;
      } else {
        engineStatusText.textContent = "Engine Offline";
        engineStatusBadge.style.color = "var(--accent-rose)";
      }
    } catch (e) {
      engineStatusText.textContent = "Connecting to Engine...";
    }
  }
  checkEngineHealth();

  async function loadStyleCatalog() {
    try {
      const res = await fetch("/api/styles");
      if (res.ok) {
        const data = await res.json();
        availableStyles = data.styles || [];
        renderStyleGallery(availableStyles);
      }
    } catch (e) {
      console.warn("Could not load style catalog:", e);
    }
  }
  loadStyleCatalog();

  // =========================================================================
  // 2. Dock Tab Navigation
  // =========================================================================
  dockTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetPaneId = tab.dataset.tab;
      dockTabs.forEach((t) => t.classList.remove("active"));
      dockPanes.forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const targetPane = document.getElementById(targetPaneId);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  function switchDockTab(tabId) {
    const tabBtn = document.querySelector(`.dock-tab[data-tab="${tabId}"]`);
    if (tabBtn) tabBtn.click();
  }

  // =========================================================================
  // 3. Video Upload, Drag & Drop, and Duration Probe
  // =========================================================================
  browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    videoFileInput.click();
  });

  dropZone.addEventListener("click", (e) => {
    if (e.target !== removeFileBtn && !fileBadge.contains(e.target)) {
      videoFileInput.click();
    }
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleSelectedVideo(e.dataTransfer.files[0]);
    }
  });

  videoFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleSelectedVideo(e.target.files[0]);
    }
  });

  removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    resetSelectedVideo();
  });

  function handleSelectedVideo(file) {
    if (!file.type.startsWith("video/") && !file.name.endsWith(".mp4") && !file.name.endsWith(".mov") && !file.name.endsWith(".webm")) {
      showToast("Please select a valid video file (MP4, MOV, or WebM).", "error");
      return;
    }

    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = `${(file.size / (1024 * 1024)).toFixed(1)} MB`;

    // Measure video duration using local blob URL
    const tempVideo = document.createElement("video");
    tempVideo.preload = "metadata";
    tempVideo.src = URL.createObjectURL(file);
    tempVideo.onloadedmetadata = () => {
      URL.revokeObjectURL(tempVideo.src);
      const dur = Math.round(tempVideo.duration);
      fileDurationTag.textContent = `${dur}s Duration`;
      if (tempVideo.videoWidth && tempVideo.videoHeight) {
        fileDurationTag.textContent += ` • ${tempVideo.videoWidth}x${tempVideo.videoHeight}`;
      }
    };

    dropPrompt.classList.add("hidden");
    fileBadge.classList.remove("hidden");
    stageStatusTag.textContent = `Ready • ${file.name}`;
    showToast(`Loaded ${file.name}`, "success");
  }

  function resetSelectedVideo() {
    selectedFile = null;
    videoFileInput.value = "";
    dropPrompt.classList.remove("hidden");
    fileBadge.classList.add("hidden");
    stageStatusTag.textContent = "Stage Ready • 9:16 Frame";
  }

  // Load Synthetic Sample
  async function loadSampleVideo() {
    const origText = loadSampleBtn.textContent;
    loadSampleBtn.textContent = "Fetching Sample...";
    loadSampleBtn.disabled = true;

    try {
      const res = await fetch("/api/sample");
      if (!res.ok) throw new Error("Sample file not found on server");
      const blob = await res.blob();
      const sampleFile = new File([blob], "synthetic_sample.mp4", { type: "video/mp4" });
      handleSelectedVideo(sampleFile);
      showToast("Synthetic sample clip loaded (12s)", "success");
    } catch (err) {
      showToast(`Could not load sample: ${err.message}`, "error");
    } finally {
      loadSampleBtn.textContent = origText;
      loadSampleBtn.disabled = false;
    }
  }

  loadSampleBtn.addEventListener("click", loadSampleVideo);
  sampleQuickBtn.addEventListener("click", loadSampleVideo);

  // Trimming Quick Preset Buttons
  trim15sBtn.addEventListener("click", () => {
    trimStart.value = "0";
    trimEnd.value = "15";
    setActiveTrimBtn(trim15sBtn);
  });
  trim30sBtn.addEventListener("click", () => {
    trimStart.value = "0";
    trimEnd.value = "30";
    setActiveTrimBtn(trim30sBtn);
  });
  trim60sBtn.addEventListener("click", () => {
    trimStart.value = "0";
    trimEnd.value = "60";
    setActiveTrimBtn(trim60sBtn);
  });
  trimResetBtn.addEventListener("click", () => {
    trimStart.value = "";
    trimEnd.value = "";
    setActiveTrimBtn(trimResetBtn);
  });

  function setActiveTrimBtn(btn) {
    [trim15sBtn, trim30sBtn, trim60sBtn, trimResetBtn].forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
  }

  // =========================================================================
  // 4. Preset Cards Selection
  // =========================================================================
  presetCards.forEach((card) => {
    card.addEventListener("click", () => {
      presetCards.forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      const radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });

  function getSelectedPreset() {
    const checked = document.querySelector('input[name="preset"]:checked');
    return checked ? checked.value : "bold_creator";
  }

  // =========================================================================
  // 5. Job Creation & Polling Pipeline
  // =========================================================================
  startJobBtn.addEventListener("click", async () => {
    if (!selectedFile) {
      showToast("Please upload a video or click 'Try Sample Reel' first!", "error");
      switchDockTab("tab-source");
      return;
    }

    startJobBtn.disabled = true;
    setStageView("processing");
    stageStatusTag.textContent = "Engine Rendering...";
    jobStartTime = Date.now();

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("preset", getSelectedPreset());
    formData.append("llm_provider", llmProviderSelect.value);
    formData.append("language", videoLanguageSelect.value);

    if (draftToggle && draftToggle.checked) {
      formData.append("draft", "true");
    }
    if (trimStart && trimStart.value.trim()) {
      formData.append("trim_start", trimStart.value.trim());
    }
    if (trimEnd && trimEnd.value.trim()) {
      formData.append("trim_end", trimEnd.value.trim());
    }
    if (renderConcurrencySelect && renderConcurrencySelect.value !== "auto") {
      formData.append("concurrency", renderConcurrencySelect.value);
    }

    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to submit render job");
      }

      const job = await res.json();
      currentJobId = job.id;
      showToast(`Job queued: ${job.id}`, "success");
      startJobPolling(currentJobId);
    } catch (err) {
      showToast(`Error: ${err.message}`, "error");
      setStageView("idle");
      startJobBtn.disabled = false;
      stageStatusTag.textContent = "Error Occurred";
    }
  });

  function startJobPolling(jobId) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const job = await res.json();
        updateProgressPipeline(job);

        if (job.status === "completed") {
          clearInterval(pollInterval);
          onJobCompleted(job);
        } else if (job.status === "failed") {
          clearInterval(pollInterval);
          onJobFailed(job);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1000);
  }

  function updateProgressPipeline(job) {
    const pct = Math.round(job.progress * 100);
    progressBarFill.style.width = `${Math.max(5, pct)}%`;
    processingPercentText.textContent = `${pct}%`;

    const elapsed = Math.floor((Date.now() - jobStartTime) / 1000);
    progressTimeElapsed.textContent = `Elapsed: ${elapsed}s`;

    // Step Explanations
    const stepLabels = {
      queued: "Allocating CPU workers and resources...",
      trimming: "Trimming video stream to selected time range...",
      probing: "Analyzing dimensions, framerate, and audio channels...",
      transcribing: "Aligning speech with faster-whisper word timestamps...",
      chunking: "Structuring natural conversational phrases and pauses...",
      planning: "Assigning 10–15 distinct styles without repetition...",
      rendering: "Composing animated vertical frames in Remotion...",
      completed: "Finalizing and muxing MP4 with FFmpeg...",
      failed: "Render failed.",
    };

    if (job.step === "rendering" && pct >= 95) {
      processingStepDescription.textContent = "Muxing audio stream & finalizing MP4...";
    } else {
      processingStepDescription.textContent = stepLabels[job.step] || job.step;
    }

    // Update 5-Step Visual Checklist
    const steps = ["probing", "transcribing", "chunking", "planning", "rendering"];
    const currentIdx = steps.indexOf(job.step);

    steps.forEach((sId, idx) => {
      const el = document.getElementById(`pipe_${sId}`);
      if (!el) return;
      const node = el.querySelector(".pipe-node");

      if (idx < currentIdx || job.status === "completed") {
        el.className = "pipeline-item completed";
        if (node) node.textContent = "✓";
      } else if (idx === currentIdx) {
        el.className = "pipeline-item active";
        if (node) node.textContent = "●";
      } else {
        el.className = "pipeline-item";
        if (node) node.textContent = "○";
      }
    });
  }

  async function onJobCompleted(job) {
    stageStatusTag.textContent = `Render Complete • ${job.id}`;
    startJobBtn.disabled = false;
    showToast("Video rendered successfully with dynamic captions!", "success");

    // Load video output into studio player
    studioResultVideo.src = `/api/jobs/${job.id}/output`;
    studioResultVideo.load();

    // Enable download links
    exportVideoBtn.href = `/api/jobs/${job.id}/output`;
    exportVideoBtn.download = `${job.id}_captioned.mp4`;
    exportVideoBtn.classList.remove("disabled");

    quickDownloadMp4Btn.href = `/api/jobs/${job.id}/output`;
    quickDownloadMp4Btn.download = `${job.id}_captioned.mp4`;

    exportSrtBtn.href = `/api/jobs/${job.id}/export/srt`;
    exportSrtBtn.download = `${job.id}.srt`;
    exportSrtBtn.classList.remove("disabled");

    exportVttBtn.href = `/api/jobs/${job.id}/export/vtt`;
    exportVttBtn.download = `${job.id}.vtt`;
    exportVttBtn.classList.remove("disabled");

    exportJsonBtn.classList.remove("disabled");

    // Fetch timeline and populate transcript editor
    try {
      const tlRes = await fetch(`/api/jobs/${job.id}/timeline`);
      if (tlRes.ok) {
        currentTimeline = await tlRes.json();
        populateTranscriptEditor(currentTimeline);
        jsonCodeView.textContent = JSON.stringify(currentTimeline, null, 2);
      }
    } catch (e) {
      console.warn("Could not fetch timeline metadata:", e);
    }

    setStageView("result");
  }

  function onJobFailed(job) {
    stageStatusTag.textContent = "Render Failed";
    startJobBtn.disabled = false;
    showToast(`Rendering failed: ${job.error || "Unknown error"}`, "error");
    setStageView("idle");
  }

  // =========================================================================
  // 6. Transcript & Inline Caption Editor
  // =========================================================================
  function populateTranscriptEditor(timeline) {
    if (!timeline || !timeline.events || timeline.events.length === 0) {
      editorEmptyState.classList.remove("hidden");
      timelineEditorContainer.classList.add("hidden");
      return;
    }

    editorEmptyState.classList.add("hidden");
    timelineEditorContainer.classList.remove("hidden");
    phraseEditorList.innerHTML = "";

    const events = timeline.events;
    editorPhraseCount.textContent = events.length;
    captionCountBadge.textContent = events.length;
    captionCountBadge.classList.remove("hidden");

    if (timeline.video && timeline.video.durationSec) {
      editorDurationVal.textContent = `${timeline.video.durationSec}s`;
    }

    events.forEach((ev, idx) => {
      const item = document.createElement("div");
      item.className = "phrase-item";
      item.id = `phrase_item_${ev.id || idx}`;
      item.dataset.start = ev.start;
      item.dataset.end = ev.end;

      // Top row: timestamp badge + style dropdown
      const topRow = document.createElement("div");
      topRow.className = "phrase-top-row";

      const timeBadge = document.createElement("span");
      timeBadge.className = "phrase-timestamp";
      timeBadge.textContent = `${formatTime(ev.start)} – ${formatTime(ev.end)}`;
      timeBadge.title = "Click to jump video to this phrase";
      timeBadge.addEventListener("click", () => {
        studioResultVideo.currentTime = ev.start;
        studioResultVideo.play();
      });

      const styleSelect = document.createElement("select");
      styleSelect.className = "phrase-style-select";

      // Populate style dropdown from available styles or defaults
      const styleList = availableStyles.length > 0
        ? availableStyles.map((s) => s.id)
        : ["title3d", "neon_glow", "typewriter_terminal", "paper_cutout", "glitch_kinetic", "quote_editorial", "comic_bubble", "gradient_outline", "minimal_underline", "blob_card", "serif_title", "numbered_point", "handwritten", "arc_letters", "sticker", "pill_word"];

      styleList.forEach((sId) => {
        const opt = document.createElement("option");
        opt.value = sId;
        opt.textContent = sId;
        if (sId === ev.style) opt.selected = true;
        styleSelect.appendChild(opt);
      });

      styleSelect.addEventListener("change", (e) => {
        ev.style = e.target.value;
        markTimelineDirty();
      });

      topRow.appendChild(timeBadge);
      topRow.appendChild(styleSelect);

      // Edit input
      const input = document.createElement("input");
      input.type = "text";
      input.className = "phrase-edit-input";
      input.value = ev.text;
      input.addEventListener("input", (e) => {
        ev.text = e.target.value;
        markTimelineDirty();
      });

      item.appendChild(topRow);
      item.appendChild(input);
      phraseEditorList.appendChild(item);
    });
  }

  function markTimelineDirty() {
    isTimelineDirty = true;
    saveEditsBtn.classList.remove("hidden");
    rerenderBtn.classList.remove("hidden");
    jsonCodeView.textContent = JSON.stringify(currentTimeline, null, 2);
  }

  // Save Edits to Server
  saveEditsBtn.addEventListener("click", async () => {
    if (!currentJobId || !currentTimeline) return;

    saveEditsBtn.disabled = true;
    saveEditsBtn.textContent = "Saving...";

    try {
      const res = await fetch(`/api/jobs/${currentJobId}/timeline`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentTimeline),
      });

      if (!res.ok) throw new Error("Server rejected timeline update");
      showToast("Caption edits saved successfully!", "success");
      saveEditsBtn.textContent = "✓ Edits Saved";
      setTimeout(() => {
        saveEditsBtn.textContent = "💾 Save & Apply Changes";
        saveEditsBtn.disabled = false;
      }, 2000);
    } catch (err) {
      showToast(`Save failed: ${err.message}`, "error");
      saveEditsBtn.disabled = false;
      saveEditsBtn.textContent = "💾 Save & Apply Changes";
    }
  });

  // Fast Re-render with Updated Timeline
  rerenderBtn.addEventListener("click", async () => {
    if (!currentJobId) return;

    // First ensure edits are saved
    try {
      await fetch(`/api/jobs/${currentJobId}/timeline`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentTimeline),
      });

      rerenderBtn.disabled = true;
      rerenderBtn.textContent = "Re-rendering...";
      setStageView("processing");
      jobStartTime = Date.now();

      const form = new FormData();
      if (draftToggle && draftToggle.checked) {
        form.append("draft", "true");
      }

      const res = await fetch(`/api/jobs/${currentJobId}/rerender`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) throw new Error("Re-render request failed");
      showToast("Re-rendering captions directly from timeline...", "success");
      startJobPolling(currentJobId);
    } catch (err) {
      showToast(`Re-render failed: ${err.message}`, "error");
      rerenderBtn.disabled = false;
      rerenderBtn.textContent = "⚡ Fast Re-Render MP4";
    }
  });

  // Jump from result view to editor tab
  editCaptionsJumpBtn.addEventListener("click", () => {
    switchDockTab("tab-editor");
  });

  // =========================================================================
  // 7. Custom 9:16 Video Player Controls
  // =========================================================================
  function togglePlayPause() {
    if (studioResultVideo.paused) {
      studioResultVideo.play();
    } else {
      studioResultVideo.pause();
    }
  }

  playPauseBtn.addEventListener("click", togglePlayPause);
  overlayPlayBtn.addEventListener("click", togglePlayPause);

  studioResultVideo.addEventListener("play", () => {
    playIcon.textContent = "❚❚";
    overlayPlayBtn.classList.add("fade-out");
  });

  studioResultVideo.addEventListener("pause", () => {
    playIcon.textContent = "▶";
    overlayPlayBtn.classList.remove("fade-out");
  });

  studioResultVideo.addEventListener("timeupdate", () => {
    const cur = studioResultVideo.currentTime;
    const dur = studioResultVideo.duration || 1;
    const pct = (cur / dur) * 100;
    scrubberPlayed.style.width = `${pct}%`;

    currentTimeDisplay.textContent = formatTime(cur);
    durationDisplay.textContent = formatTime(dur);

    // Sync highlight in transcript editor
    syncActiveCaptionHighlight(cur);
  });

  studioResultVideo.addEventListener("loadedmetadata", () => {
    durationDisplay.textContent = formatTime(studioResultVideo.duration);
  });

  // Click on Scrubber
  timelineScrubber.addEventListener("click", (e) => {
    const rect = timelineScrubber.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    studioResultVideo.currentTime = pos * (studioResultVideo.duration || 1);
  });

  // Step 1s back/forward
  stepBackBtn.addEventListener("click", () => {
    studioResultVideo.currentTime = Math.max(0, studioResultVideo.currentTime - 1);
  });
  stepForwardBtn.addEventListener("click", () => {
    studioResultVideo.currentTime = Math.min(studioResultVideo.duration || 999, studioResultVideo.currentTime + 1);
  });

  // Playback Speed Toggle
  const speeds = [1.0, 1.25, 1.5, 2.0];
  let speedIdx = 0;
  speedToggleBtn.addEventListener("click", () => {
    speedIdx = (speedIdx + 1) % speeds.length;
    const s = speeds[speedIdx];
    studioResultVideo.playbackRate = s;
    speedToggleBtn.textContent = `${s.toFixed(1)}x`;
  });

  // Mute Toggle
  muteToggleBtn.addEventListener("click", () => {
    studioResultVideo.muted = !studioResultVideo.muted;
    muteToggleBtn.textContent = studioResultVideo.muted ? "🔇" : "🔊";
  });

  // Fullscreen
  fullscreenBtn.addEventListener("click", () => {
    if (!document.fullscreenElement) {
      document.getElementById("videoContainer").requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  });

  // Spacebar hotkey
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" && e.target.tagName !== "INPUT" && e.target.tagName !== "SELECT" && e.target.tagName !== "TEXTAREA") {
      e.preventDefault();
      togglePlayPause();
    }
  });

  // Highlight active phrase in transcript during playback
  function syncActiveCaptionHighlight(currentTime) {
    const items = phraseEditorList.querySelectorAll(".phrase-item");
    items.forEach((item) => {
      const start = parseFloat(item.dataset.start);
      const end = parseFloat(item.dataset.end);
      if (currentTime >= start && currentTime <= end) {
        item.classList.add("active-playing");
      } else {
        item.classList.remove("active-playing");
      }
    });
  }

  // =========================================================================
  // 8. Style Library Showcase & Live Sandbox
  // =========================================================================
  function renderStyleGallery(styles) {
    galleryGrid.innerHTML = "";
    const testText = sandboxTextInput.value.trim() || "MAKING MONEY IS A SKILL";

    styles.forEach((s) => {
      const card = document.createElement("div");
      card.className = "style-showcase-card";
      card.dataset.category = s.category || "all";

      const stage = document.createElement("div");
      stage.className = "showcase-stage";

      // Render custom preview representation
      const previewEl = createStylePreviewElement(s.id, testText);
      stage.appendChild(previewEl);

      const info = document.createElement("div");
      info.className = "showcase-info";

      const header = document.createElement("div");
      header.className = "showcase-header";

      const idSpan = document.createElement("span");
      idSpan.className = "showcase-id";
      idSpan.textContent = s.id;

      const tagSpan = document.createElement("span");
      tagSpan.className = "showcase-tag";
      tagSpan.textContent = s.tag || s.category;

      header.appendChild(idSpan);
      header.appendChild(tagSpan);

      const desc = document.createElement("p");
      desc.className = "showcase-desc";
      desc.textContent = s.description;

      info.appendChild(header);
      info.appendChild(desc);

      card.appendChild(stage);
      card.appendChild(info);
      galleryGrid.appendChild(card);
    });
  }

  function createStylePreviewElement(styleId, text) {
    const el = document.createElement("div");
    switch (styleId) {
      case "title3d":
        el.className = "preview-title3d-live";
        el.textContent = text.toUpperCase();
        break;
      case "neon_glow":
        el.className = "preview-neon-live";
        el.textContent = text.toUpperCase();
        break;
      case "typewriter_terminal":
        el.className = "preview-terminal-live";
        el.textContent = `> ${text.toLowerCase()} _`;
        break;
      case "paper_cutout":
        el.className = "preview-cutout-live";
        el.textContent = text.toUpperCase();
        break;
      case "glitch_kinetic":
        el.className = "preview-glitch-live";
        el.textContent = text.toUpperCase();
        break;
      case "quote_editorial":
        el.className = "preview-quote-live";
        el.textContent = `“ ${text} ”`;
        break;
      case "comic_bubble":
        el.className = "preview-comic-live";
        el.textContent = `POW! ${text}`;
        break;
      case "gradient_outline":
        el.className = "preview-gradient-live";
        el.textContent = text.toUpperCase();
        break;
      case "minimal_underline":
        el.className = "preview-underline-live";
        el.textContent = text;
        break;
      case "blob_card":
        el.className = "preview-blob-glow-live";
        el.textContent = text;
        break;
      case "serif_title":
        el.className = "preview-serif-live";
        el.textContent = text;
        break;
      case "numbered_point":
        el.className = "preview-number-live";
        el.textContent = `① ${text}`;
        break;
      case "handwritten":
        el.className = "preview-handwritten-live";
        el.textContent = text;
        break;
      case "arc_letters":
        el.className = "preview-title3d-live";
        el.textContent = text;
        break;
      case "sticker":
        el.className = "preview-sticker-live";
        el.textContent = `✨ ${text}`;
        break;
      case "pill_word":
      default:
        el.className = "preview-pill-live";
        el.textContent = text;
        break;
    }
    return el;
  }

  // Live Sandbox Input
  sandboxTextInput.addEventListener("input", () => {
    if (availableStyles.length > 0) {
      renderStyleGallery(availableStyles);
    }
  });

  // Filter Chips
  galleryFilterChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      galleryFilterChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      const filter = chip.dataset.filter;

      const cards = galleryGrid.querySelectorAll(".style-showcase-card");
      cards.forEach((card) => {
        if (filter === "all" || card.dataset.category === filter) {
          card.style.display = "flex";
        } else {
          card.style.display = "none";
        }
      });
    });
  });

  // =========================================================================
  // 9. JSON Viewer & Copy Tools
  // =========================================================================
  exportJsonBtn.addEventListener("click", () => {
    jsonDrawer.classList.toggle("hidden");
  });

  copyJsonBtn.addEventListener("click", () => {
    if (currentTimeline) {
      navigator.clipboard.writeText(JSON.stringify(currentTimeline, null, 2)).then(() => {
        showToast("Timeline JSON copied to clipboard!", "success");
      });
    }
  });

  newJobBtn.addEventListener("click", () => {
    setStageView("idle");
    studioResultVideo.pause();
    studioResultVideo.src = "";
    resetSelectedVideo();
    switchDockTab("tab-source");
  });

  // =========================================================================
  // Helper Functions
  // =========================================================================
  function setStageView(viewName) {
    viewIdle.classList.toggle("hidden", viewName !== "idle");
    viewProcessing.classList.toggle("hidden", viewName !== "processing");
    viewResult.classList.toggle("hidden", viewName !== "result");
  }

  function formatTime(sec) {
    if (isNaN(sec) || sec === null) return "00:00.00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 100);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(ms).padStart(2, "0")}`;
  }

  function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `pro-toast ${type}`;
    toast.innerHTML = `
      <span>${type === "success" ? "✓" : "⚠️"}</span>
      <span>${message}</span>
    `;
    toastShelf.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
});
