/**
 * Dynamic Captions Studio — Minimalist Frontend Controller
 * Connected directly to FastAPI endpoints.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM References
  const engineStatus = document.getElementById("engineStatus");
  const quickSampleBtn = document.getElementById("quickSampleBtn");
  const loadSampleBtn = document.getElementById("loadSampleBtn");

  const dropZone = document.getElementById("dropZone");
  const videoFileInput = document.getElementById("videoFileInput");
  const browseBtn = document.getElementById("browseBtn");
  const dropPrompt = document.getElementById("dropPrompt");
  const fileBadge = document.getElementById("fileBadge");
  const fileName = document.getElementById("fileName");
  const fileSize = document.getElementById("fileSize");
  const removeFileBtn = document.getElementById("removeFileBtn");

  const presetChips = document.querySelectorAll(".preset-chip");
  const trimStart = document.getElementById("trimStart");
  const trimEnd = document.getElementById("trimEnd");
  const trim15sBtn = document.getElementById("trim15sBtn");
  const trim30sBtn = document.getElementById("trim30sBtn");
  const trim60sBtn = document.getElementById("trim60sBtn");
  const trimResetBtn = document.getElementById("trimResetBtn");

  const llmProvider = document.getElementById("llmProvider");
  const videoLanguage = document.getElementById("videoLanguage");
  const draftToggle = document.getElementById("draftToggle");
  const startJobBtn = document.getElementById("startJobBtn");

  const stageStatus = document.getElementById("stageStatus");
  const timeElapsedBadge = document.getElementById("timeElapsedBadge");
  const viewIdle = document.getElementById("viewIdle");
  const viewProcessing = document.getElementById("viewProcessing");
  const viewResult = document.getElementById("viewResult");

  const procTitle = document.getElementById("procTitle");
  const procStep = document.getElementById("procStep");
  const procFill = document.getElementById("procFill");
  const procPct = document.getElementById("procPct");
  const procElapsed = document.getElementById("procElapsed");

  const resultVideo = document.getElementById("resultVideo");
  const resultActions = document.getElementById("resultActions");
  const downloadMp4Btn = document.getElementById("downloadMp4Btn");
  const downloadSrtBtn = document.getElementById("downloadSrtBtn");
  const downloadVttBtn = document.getElementById("downloadVttBtn");
  const resetBtn = document.getElementById("resetBtn");

  const editorCard = document.getElementById("editorCard");
  const eventCount = document.getElementById("eventCount");
  const phrasesList = document.getElementById("phrasesList");
  const saveEditsBtn = document.getElementById("saveEditsBtn");
  const toast = document.getElementById("toast");

  // State
  let selectedFile = null;
  let currentJobId = null;
  let pollInterval = null;
  let jobStartTime = null;
  let currentTimeline = null;

  // 1. Health Check
  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        engineStatus.textContent = "Engine Ready";
      }
    } catch {
      engineStatus.textContent = "Connecting...";
    }
  }
  checkHealth();

  // 2. File Selection & Drag & Drop
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
      handleFile(e.dataTransfer.files[0]);
    }
  });

  videoFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  });

  removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    videoFileInput.value = "";
    dropPrompt.classList.remove("hidden");
    fileBadge.classList.add("hidden");
    stageStatus.textContent = "Preview Canvas";
  });

  function handleFile(file) {
    if (!file.type.startsWith("video/") && !file.name.endsWith(".mp4") && !file.name.endsWith(".mov")) {
      showToast("Please select a video file (MP4, MOV).");
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = `${(file.size / (1024 * 1024)).toFixed(1)} MB`;

    dropPrompt.classList.add("hidden");
    fileBadge.classList.remove("hidden");
    stageStatus.textContent = `Ready • ${file.name}`;
    showToast(`Loaded ${file.name}`);
  }

  // Sample Clip Loader
  async function loadSample() {
    showToast("Fetching sample video...");
    try {
      const res = await fetch("/api/sample");
      if (!res.ok) throw new Error("Sample file not found on server");
      const blob = await res.blob();
      const sample = new File([blob], "synthetic_sample.mp4", { type: "video/mp4" });
      handleFile(sample);
    } catch (err) {
      showToast(`Could not load sample: ${err.message}`);
    }
  }
  loadSampleBtn.addEventListener("click", loadSample);
  quickSampleBtn.addEventListener("click", loadSample);

  // 3. Preset Selection
  presetChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      presetChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      const radio = chip.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });

  function getSelectedPreset() {
    const checked = document.querySelector('input[name="preset"]:checked');
    return checked ? checked.value : "bold_creator";
  }

  // 4. Trimming Presets
  trim15sBtn.addEventListener("click", () => { trimStart.value = "0"; trimEnd.value = "15"; });
  trim30sBtn.addEventListener("click", () => { trimStart.value = "0"; trimEnd.value = "30"; });
  trim60sBtn.addEventListener("click", () => { trimStart.value = "0"; trimEnd.value = "60"; });
  trimResetBtn.addEventListener("click", () => { trimStart.value = ""; trimEnd.value = ""; });

  // 5. Start Job & Polling Pipeline
  startJobBtn.addEventListener("click", async () => {
    if (!selectedFile) {
      showToast("Please upload a video or click 'Load Sample Reel'!");
      return;
    }

    startJobBtn.disabled = true;
    showStage("processing");
    stageStatus.textContent = "Rendering...";
    jobStartTime = Date.now();

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("preset", getSelectedPreset());
    formData.append("llm_provider", llmProvider.value);
    formData.append("language", videoLanguage.value);
    if (draftToggle.checked) {
      formData.append("draft", "true");
    }
    if (trimStart.value.trim()) {
      formData.append("trim_start", trimStart.value.trim());
    }
    if (trimEnd.value.trim()) {
      formData.append("trim_end", trimEnd.value.trim());
    }

    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to start job");
      }

      const job = await res.json();
      currentJobId = job.id;
      showToast(`Job queued: ${job.id}`);
      startPolling(currentJobId);
    } catch (err) {
      showToast(`Error: ${err.message}`);
      showStage("idle");
      startJobBtn.disabled = false;
      stageStatus.textContent = "Error";
    }
  });

  function startPolling(jobId) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const job = await res.json();
        updateProgress(job);

        if (job.status === "completed") {
          clearInterval(pollInterval);
          onCompleted(job);
        } else if (job.status === "failed") {
          clearInterval(pollInterval);
          onFailed(job);
        }
      } catch (e) {
        console.error("Polling:", e);
      }
    }, 1000);
  }

  function updateProgress(job) {
    const pct = Math.round(job.progress * 100);
    procFill.style.width = `${Math.max(5, pct)}%`;
    procPct.textContent = `${pct}%`;

    const elapsed = Math.floor((Date.now() - jobStartTime) / 1000);
    procElapsed.textContent = `${elapsed}s`;
    timeElapsedBadge.textContent = `Elapsed: ${elapsed}s`;

    const steps = {
      queued: "Queued...",
      trimming: "Trimming video clip...",
      probing: "Analyzing dimensions & audio...",
      transcribing: "Aligning speech with faster-whisper...",
      chunking: "Structuring natural cadence & phrases...",
      planning: "Assigning 10–15 distinct styles...",
      rendering: "Composing animated MP4 with Remotion...",
      completed: "Finalizing MP4...",
      failed: "Failed.",
    };

    if (job.step === "rendering" && pct >= 95) {
      procStep.textContent = "Muxing audio & finalizing MP4...";
    } else {
      procStep.textContent = steps[job.step] || job.step;
    }
  }

  async function onCompleted(job) {
    stageStatus.textContent = "Completed";
    startJobBtn.disabled = false;
    showToast("Render complete! Loading video...");

    // Setup Video
    resultVideo.src = `/api/jobs/${job.id}/output`;
    resultVideo.load();

    // Setup Download Links
    downloadMp4Btn.href = `/api/jobs/${job.id}/output`;
    downloadMp4Btn.download = `${job.id}_captioned.mp4`;

    downloadSrtBtn.href = `/api/jobs/${job.id}/export/srt`;
    downloadSrtBtn.download = `${job.id}.srt`;

    downloadVttBtn.href = `/api/jobs/${job.id}/export/vtt`;
    downloadVttBtn.download = `${job.id}.vtt`;

    resultActions.classList.remove("hidden");

    // Fetch and populate timeline
    try {
      const tlRes = await fetch(`/api/jobs/${job.id}/timeline`);
      if (tlRes.ok) {
        currentTimeline = await tlRes.json();
        renderTimeline(currentTimeline);
      }
    } catch (e) {
      console.warn("Could not load timeline:", e);
    }

    showStage("result");
  }

  function onFailed(job) {
    stageStatus.textContent = "Failed";
    startJobBtn.disabled = false;
    showToast(`Error: ${job.error || "Render failed"}`);
    showStage("idle");
  }

  // 6. Caption Timeline Inspector & Editor
  function renderTimeline(timeline) {
    if (!timeline || !timeline.events || timeline.events.length === 0) {
      editorCard.classList.add("hidden");
      return;
    }

    editorCard.classList.remove("hidden");
    phrasesList.innerHTML = "";
    eventCount.textContent = timeline.events.length;

    timeline.events.forEach((ev) => {
      const row = document.createElement("div");
      row.className = "phrase-row";

      const time = document.createElement("span");
      time.className = "phrase-time";
      time.textContent = `${ev.start.toFixed(1)}s - ${ev.end.toFixed(1)}s`;
      time.title = "Click to jump video to this moment";
      time.style.cursor = "pointer";
      time.addEventListener("click", () => {
        resultVideo.currentTime = ev.start;
        resultVideo.play();
      });

      const input = document.createElement("input");
      input.type = "text";
      input.className = "phrase-input";
      input.value = ev.text;
      input.addEventListener("input", (e) => {
        ev.text = e.target.value;
        saveEditsBtn.classList.remove("hidden");
      });

      const badge = document.createElement("span");
      badge.className = "phrase-badge";
      badge.textContent = ev.style;

      row.appendChild(time);
      row.appendChild(input);
      row.appendChild(badge);
      phrasesList.appendChild(row);
    });
  }

  saveEditsBtn.addEventListener("click", async () => {
    if (!currentJobId || !currentTimeline) return;
    saveEditsBtn.textContent = "Saving...";
    try {
      const res = await fetch(`/api/jobs/${currentJobId}/timeline`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentTimeline),
      });
      if (!res.ok) throw new Error("Failed to save");
      showToast("Caption text saved!");
      saveEditsBtn.textContent = "✓ Saved";
      setTimeout(() => {
        saveEditsBtn.textContent = "💾 Save Changes";
      }, 2000);
    } catch (err) {
      showToast(`Error saving: ${err.message}`);
      saveEditsBtn.textContent = "💾 Save Changes";
    }
  });

  resetBtn.addEventListener("click", () => {
    showStage("idle");
    stageStatus.textContent = "Preview Canvas";
    resultVideo.pause();
    resultVideo.src = "";
    resultActions.classList.add("hidden");
    editorCard.classList.add("hidden");
  });

  // Helpers
  function showStage(stage) {
    viewIdle.classList.toggle("hidden", stage !== "idle");
    viewProcessing.classList.toggle("hidden", stage !== "processing");
    viewResult.classList.toggle("hidden", stage !== "result");
  }

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 3000);
  }
});
