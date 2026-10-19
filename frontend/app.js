/**
 * Dynamic Captions Studio — Minimalist Frontend Controller
 * Fully integrated with Remotion, faster-whisper, and FastAPI backend.
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

  const subPosition = document.getElementById("subPosition");
  const videoLanguage = document.getElementById("videoLanguage");
  const llmProvider = document.getElementById("llmProvider");
  const draftToggle = document.getElementById("draftToggle");

  const startJobBtn = document.getElementById("startJobBtn");
  const btnProgressFill = document.getElementById("btnProgressFill");
  const btnTextLabel = document.getElementById("btnTextLabel");

  // Prominent Pipeline Progress Card references
  const pipelineProgressCard = document.getElementById("pipelineProgressCard");
  const pipelineProgressTitle = document.getElementById("pipelineProgressTitle");
  const pipelineProgressPct = document.getElementById("pipelineProgressPct");
  const pipelineProgressFill = document.getElementById("pipelineProgressFill");
  const pipelineProgressDesc = document.getElementById("pipelineProgressDesc");
  const pipelineProgressTime = document.getElementById("pipelineProgressTime");

  const stageStatus = document.getElementById("stageStatus");
  const phoneCanvas = document.getElementById("phoneCanvas");
  const arSelectedLabel = document.getElementById("arSelectedLabel");
  const allArButtons = document.querySelectorAll(".btn-ar, .btn-ar-opt");

  const viewIdle = document.getElementById("viewIdle");
  const viewSource = document.getElementById("viewSource");
  const sourceVideoPlayer = document.getElementById("sourceVideoPlayer");
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

  // State Management
  let selectedFile = null;
  let currentJobId = null;
  let pollInterval = null;
  let jobStartTime = null;
  let currentTimeline = null;
  let selectedAspectRatio = "9:16";

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

  // 2. Synchronized Aspect Ratio Selector (Both in Options & on Canvas)
  function setAspectRatio(ar) {
    selectedAspectRatio = ar;
    allArButtons.forEach((b) => {
      b.classList.toggle("active", b.dataset.ar === ar);
    });

    const labels = {
      "9:16": "9:16 Vertical (Shorts/Reels)",
      "16:9": "16:9 Landscape (YouTube)",
      "1:1": "1:1 Square (Feed)",
      "4:5": "4:5 Portrait (Instagram)",
    };
    if (arSelectedLabel) arSelectedLabel.textContent = labels[ar] || ar;
    phoneCanvas.className = "phone-canvas ar-" + ar.replace(":", "-");
    stageStatus.textContent = `Preview (${ar})`;
    showToast(`Switched canvas to ${ar}`);
  }

  allArButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      setAspectRatio(btn.dataset.ar);
    });
  });

  // 2b. Creator Customization Options State & Wiring
  let selectedCaptionSize = "medium";
  let selectedBgStyle = "transparent";
  let selectedStylePacing = "sentence";
  let selectedHighlightColor = "#38BDF8";

  // Caption Size Chips
  const captionSizeChips = document.querySelectorAll("#captionSizeChips .btn-custom-chip");
  const captionSizeSelectedLabel = document.getElementById("captionSizeSelectedLabel");
  captionSizeChips.forEach((btn) => {
    btn.addEventListener("click", () => {
      captionSizeChips.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedCaptionSize = btn.dataset.size;
      const sizeLabels = {
        small: "Small (38px)",
        medium: "Medium (52px Sweet Spot)",
        large: "Large (68px)",
      };
      if (captionSizeSelectedLabel) captionSizeSelectedLabel.textContent = sizeLabels[selectedCaptionSize] || selectedCaptionSize;
      showToast(`Caption font size: ${selectedCaptionSize}`);
    });
  });

  // Background Style Chips
  const bgStyleChips = document.querySelectorAll("#bgStyleChips .btn-custom-chip");
  const bgStyleSelectedLabel = document.getElementById("bgStyleSelectedLabel");
  bgStyleChips.forEach((btn) => {
    btn.addEventListener("click", () => {
      bgStyleChips.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedBgStyle = btn.dataset.bg;
      const bgLabels = {
        transparent: "Transparent (No Box)",
        glass: "Dark Glass (Frosted Blur)",
        solid: "Solid (White Pill)",
      };
      if (bgStyleSelectedLabel) bgStyleSelectedLabel.textContent = bgLabels[selectedBgStyle] || selectedBgStyle;
      showToast(`Backdrop: ${selectedBgStyle}`);
    });
  });

  // Style Pacing Chips
  const pacingChips = document.querySelectorAll("#pacingChips .btn-custom-chip");
  const pacingSelectedLabel = document.getElementById("pacingSelectedLabel");
  pacingChips.forEach((btn) => {
    btn.addEventListener("click", () => {
      pacingChips.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedStylePacing = btn.dataset.pacing;
      const pacingLabels = {
        sentence: "Sentence by Sentence",
        phrase: "Dynamic Phrase",
      };
      if (pacingSelectedLabel) pacingSelectedLabel.textContent = pacingLabels[selectedStylePacing] || selectedStylePacing;
      showToast(`Pacing: ${selectedStylePacing}`);
    });
  });

  // Highlight Color Swatches
  const colorSwatches = document.querySelectorAll("#highlightColorSwatches .btn-color-swatch");
  const highlightColorSelectedLabel = document.getElementById("highlightColorSelectedLabel");
  colorSwatches.forEach((btn) => {
    btn.addEventListener("click", () => {
      colorSwatches.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedHighlightColor = btn.dataset.color;
      if (highlightColorSelectedLabel) highlightColorSelectedLabel.textContent = btn.title || selectedHighlightColor;
      showToast(`Highlight color: ${btn.title}`);
    });
  });

  // 3. File Selection & Instant Video Preview
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
    sourceVideoPlayer.pause();
    sourceVideoPlayer.src = "";
    dropPrompt.classList.remove("hidden");
    fileBadge.classList.add("hidden");
    stageStatus.textContent = "Preview Canvas";
    showStage("idle");
  });

  function handleFile(file) {
    if (!file.type.startsWith("video/") && !file.name.endsWith(".mp4") && !file.name.endsWith(".mov") && !file.name.endsWith(".webm")) {
      showToast("Please select a video file (MP4, MOV, WebM).");
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = `${(file.size / (1024 * 1024)).toFixed(1)} MB`;

    dropPrompt.classList.add("hidden");
    fileBadge.classList.remove("hidden");
    stageStatus.textContent = `Raw Source • ${file.name}`;

    // Instant Preview in Canvas
    const objectUrl = URL.createObjectURL(file);
    sourceVideoPlayer.src = objectUrl;
    sourceVideoPlayer.load();
    showStage("source");

    showToast(`Loaded ${file.name} • Ready to render`);
  }

  // Sample Video Loader
  async function loadSample() {
    showToast("Fetching synthetic sample clip...");
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

  // 4. Preset Selection
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

  // 5. Trimming Quick Buttons
  trim15sBtn.addEventListener("click", () => { trimStart.value = "0"; trimEnd.value = "15"; });
  trim30sBtn.addEventListener("click", () => { trimStart.value = "0"; trimEnd.value = "30"; });
  trim60sBtn.addEventListener("click", () => { trimStart.value = "0"; trimEnd.value = "60"; });
  trimResetBtn.addEventListener("click", () => { trimStart.value = ""; trimEnd.value = ""; });

  // 6. Start Job with Real-Time Upload Progress & Dual Progress Bars
  startJobBtn.addEventListener("click", async () => {
    if (!selectedFile) {
      showToast("No video uploaded yet — auto-loading synthetic sample reel (12s)...");
      await loadSample();
      if (!selectedFile) {
        showToast("Please upload a video or click 'Load Sample Reel'!");
        return;
      }
    }

    startJobBtn.disabled = true;
    showStage("processing");
    stageStatus.textContent = "Rendering...";
    jobStartTime = Date.now();

    // Show and initialize prominent Pipeline Progress Card
    if (pipelineProgressCard) pipelineProgressCard.classList.remove("hidden");
    if (pipelineProgressTitle) pipelineProgressTitle.textContent = "Uploading Video to Engine...";
    if (pipelineProgressPct) pipelineProgressPct.textContent = "0%";
    if (pipelineProgressFill) pipelineProgressFill.style.width = "5%";
    if (pipelineProgressDesc) pipelineProgressDesc.textContent = `Streaming ${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB to local studio runner...`;
    if (pipelineProgressTime) pipelineProgressTime.textContent = "0s elapsed";

    // Prepare FormData
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("preset", getSelectedPreset());
    formData.append("llm_provider", llmProvider.value);
    formData.append("language", videoLanguage.value);
    formData.append("aspect_ratio", selectedAspectRatio);
    formData.append("subtitle_position", subPosition ? subPosition.value : "lower");
    formData.append("caption_size", selectedCaptionSize);
    formData.append("background_style", selectedBgStyle);
    formData.append("style_pacing", selectedStylePacing);
    formData.append("highlight_color", selectedHighlightColor);

    if (draftToggle.checked) {
      formData.append("draft", "true");
    }
    if (trimStart.value.trim()) {
      formData.append("trim_start", trimStart.value.trim());
    }
    if (trimEnd.value.trim()) {
      formData.append("trim_end", trimEnd.value.trim());
    }

    // Use XMLHttpRequest for real-time Upload Progress
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/jobs", true);

    // Initial Processing State
    procTitle.textContent = "Uploading Video to Engine...";
    procStep.textContent = `Streaming ${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB to local studio runner...`;
    procFill.style.width = "5%";
    procPct.textContent = "0%";
    btnTextLabel.textContent = "Uploading Video... 0%";
    btnProgressFill.style.width = "5%";

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const uploadPct = Math.round((e.loaded / e.total) * 100);
        const loadedMb = (e.loaded / (1024 * 1024)).toFixed(1);
        const totalMb = (e.total / (1024 * 1024)).toFixed(1);

        // Map upload to 0% - 25% of overall pipeline
        const mappedPct = Math.min(25, Math.round(uploadPct * 0.25));
        procFill.style.width = `${Math.max(5, mappedPct)}%`;
        procPct.textContent = `${uploadPct}% Uploaded`;
        procStep.textContent = `Uploaded ${loadedMb} MB / ${totalMb} MB (${uploadPct}%)...`;

        // Update prominent progress card
        if (pipelineProgressPct) pipelineProgressPct.textContent = `${uploadPct}%`;
        if (pipelineProgressFill) pipelineProgressFill.style.width = `${Math.max(5, uploadPct)}%`;
        if (pipelineProgressDesc) pipelineProgressDesc.textContent = `Uploaded ${loadedMb} MB / ${totalMb} MB (${uploadPct}%)...`;
        const elapsed = Math.floor((Date.now() - jobStartTime) / 1000);
        if (pipelineProgressTime) pipelineProgressTime.textContent = `${elapsed}s elapsed`;

        btnTextLabel.textContent = `Uploading Video... ${uploadPct}%`;
        btnProgressFill.style.width = `${uploadPct}%`;
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const job = JSON.parse(xhr.responseText);
          currentJobId = job.id;
          procTitle.textContent = "Processing Video...";
          procStep.textContent = "Aligning speech with faster-whisper timestamps...";
          procFill.style.width = "25%";
          procPct.textContent = "25%";
          btnTextLabel.textContent = "Transcribing Speech...";

          if (pipelineProgressTitle) pipelineProgressTitle.textContent = "Processing Video...";
          if (pipelineProgressDesc) pipelineProgressDesc.textContent = "Aligning speech with faster-whisper timestamps...";
          if (pipelineProgressPct) pipelineProgressPct.textContent = "25%";
          if (pipelineProgressFill) pipelineProgressFill.style.width = "25%";

          startPolling(currentJobId);
        } catch (err) {
          onFailed({ error: "Failed to parse job response" });
        }
      } else {
        let msg = "Upload failed";
        try {
          const errData = JSON.parse(xhr.responseText);
          msg = errData.detail || msg;
        } catch {}
        onFailed({ error: msg });
      }
    };

    xhr.onerror = () => {
      onFailed({ error: "Network error during upload" });
    };

    xhr.send(formData);
  });

  // 7. Polling Pipeline Progress
  function startPolling(jobId) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const job = await res.json();
        updatePipelineProgress(job);

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

  function updatePipelineProgress(job) {
    // Map job.progress (0.0 to 1.0) into overall percent (25% to 100%)
    const jobPct = Math.round(job.progress * 100);
    const overallPct = Math.min(100, Math.max(25, 25 + Math.round(job.progress * 75)));

    procFill.style.width = `${overallPct}%`;
    procPct.textContent = `${overallPct}%`;
    btnProgressFill.style.width = `${overallPct}%`;

    const elapsed = Math.floor((Date.now() - jobStartTime) / 1000);
    procElapsed.textContent = `${elapsed}s elapsed`;

    const stepLabels = {
      queued: "Queued in render queue...",
      trimming: "Trimming video clip to range...",
      probing: "Analyzing dimensions & audio channels...",
      transcribing: "Aligning speech with faster-whisper...",
      chunking: "Structuring natural cadence & phrases...",
      planning: "Assigning 10–15 distinct styles...",
      rendering: "Composing animated frames in Remotion...",
      completed: "Finalizing and muxing MP4...",
      failed: "Render failed.",
    };

    const currentStepText = (job.step === "rendering" && jobPct >= 95)
      ? "Muxing audio & finalizing MP4 with FFmpeg..."
      : (stepLabels[job.step] || job.step);

    procTitle.textContent = "Rendering Video...";
    procStep.textContent = currentStepText;
    btnTextLabel.textContent = `Rendering... ${overallPct}%`;

    // Prominent Progress Card
    if (pipelineProgressCard) pipelineProgressCard.classList.remove("hidden");
    if (pipelineProgressTitle) pipelineProgressTitle.textContent = `Rendering Video (${overallPct}%)`;
    if (pipelineProgressPct) pipelineProgressPct.textContent = `${overallPct}%`;
    if (pipelineProgressFill) pipelineProgressFill.style.width = `${overallPct}%`;
    if (pipelineProgressDesc) pipelineProgressDesc.textContent = currentStepText;
    if (pipelineProgressTime) pipelineProgressTime.textContent = `${elapsed}s elapsed`;
  }

  async function onCompleted(job) {
    stageStatus.textContent = `Complete (${selectedAspectRatio})`;
    startJobBtn.disabled = false;
    btnProgressFill.style.width = "0%";
    btnTextLabel.textContent = "Generate Captioned Video ⚡";
    showToast("Render complete! Loading captioned video...");

    // Update prominent card to 100% complete
    if (pipelineProgressFill) pipelineProgressFill.style.width = "100%";
    if (pipelineProgressPct) pipelineProgressPct.textContent = "100%";
    if (pipelineProgressTitle) pipelineProgressTitle.textContent = "✓ Render Complete!";
    if (pipelineProgressDesc) pipelineProgressDesc.textContent = "Captioned MP4 finalized and ready to download!";
    setTimeout(() => {
      if (pipelineProgressCard) pipelineProgressCard.classList.add("hidden");
    }, 6000);

    // Pause source video if playing
    sourceVideoPlayer.pause();

    // Setup Result Video
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
    btnProgressFill.style.width = "0%";
    btnTextLabel.textContent = "Generate Captioned Video ⚡";
    showToast(`Error: ${job.error || "Render failed"}`);
    showStage(selectedFile ? "source" : "idle");
  }

  // 8. Caption Timeline Inspector & Editor
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
    showStage(selectedFile ? "source" : "idle");
    stageStatus.textContent = selectedFile ? `Raw Source • ${selectedFile.name}` : "Preview Canvas";
    resultVideo.pause();
    resultVideo.src = "";
    resultActions.classList.add("hidden");
    editorCard.classList.add("hidden");
  });

  // Stage Switcher
  function showStage(stage) {
    viewIdle.classList.toggle("hidden", stage !== "idle");
    viewSource.classList.toggle("hidden", stage !== "source");
    viewProcessing.classList.toggle("hidden", stage !== "processing");
    viewResult.classList.toggle("hidden", stage !== "result");
  }

  // Toast Helper
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 3000);
  }
});
