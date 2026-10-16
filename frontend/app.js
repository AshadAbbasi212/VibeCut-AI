/**
 * Dynamic Captions Studio — Frontend Single-Page Application
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const dropZone = document.getElementById("dropZone");
  const videoFileInput = document.getElementById("videoFileInput");
  const browseBtn = document.getElementById("browseBtn");
  const dropPrompt = document.getElementById("dropPrompt");
  const fileBadge = document.getElementById("fileBadge");
  const fileName = document.getElementById("fileName");
  const fileSize = document.getElementById("fileSize");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const loadSampleBtn = document.getElementById("loadSampleBtn");

  const presetCards = document.querySelectorAll(".preset-card");
  const llmProviderSelect = document.getElementById("llmProvider");
  const videoLanguageSelect = document.getElementById("videoLanguage");
  const startJobBtn = document.getElementById("startJobBtn");

  const stageEmpty = document.getElementById("stageEmpty");
  const stageProcessing = document.getElementById("stageProcessing");
  const stageResult = document.getElementById("stageResult");
  const stageBadge = document.getElementById("stageBadge");

  const processingTitle = document.getElementById("processingTitle");
  const processingStep = document.getElementById("processingStep");
  const progressBarFill = document.getElementById("progressBarFill");
  const progressPercent = document.getElementById("progressPercent");
  const progressTime = document.getElementById("progressTime");

  const resultVideo = document.getElementById("resultVideo");
  const downloadBtn = document.getElementById("downloadBtn");
  const resetBtn = document.getElementById("resetBtn");
  const eventsList = document.getElementById("eventsList");
  const eventCount = document.getElementById("eventCount");
  const toggleJsonBtn = document.getElementById("toggleJsonBtn");
  const jsonViewer = document.getElementById("jsonViewer");
  const jsonCode = document.getElementById("jsonCode");
  const copyJsonBtn = document.getElementById("copyJsonBtn");

  // State
  let selectedFile = null;
  let currentJobId = null;
  let pollInterval = null;
  let jobStartTime = null;

  // 1. File Handling
  browseBtn.addEventListener("click", () => videoFileInput.click());
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
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  videoFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    videoFileInput.value = "";
    dropPrompt.classList.remove("hidden");
    fileBadge.classList.add("hidden");
    stageBadge.textContent = "Awaiting Input";
  });

  function handleFileSelected(file) {
    if (!file.type.startsWith("video/") && !file.name.endsWith(".mp4") && !file.name.endsWith(".mov")) {
      alert("Please select a video file (MP4, MOV, WebM).");
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = `${(file.size / (1024 * 1024)).toFixed(1)} MB`;

    dropPrompt.classList.add("hidden");
    fileBadge.classList.remove("hidden");
    stageBadge.textContent = "Ready to Render";
  }

  // Load sample video
  loadSampleBtn.addEventListener("click", async () => {
    loadSampleBtn.textContent = "Fetching sample...";
    loadSampleBtn.disabled = true;
    try {
      const res = await fetch("/api/sample");
      if (!res.ok) throw new Error("Sample video not found on server");
      const blob = await res.blob();
      const sampleFile = new File([blob], "synthetic_sample.mp4", { type: "video/mp4" });
      handleFileSelected(sampleFile);
    } catch (err) {
      alert(`Could not load sample video: ${err.message}`);
    } finally {
      loadSampleBtn.textContent = "Load Synthetic Sample (12s)";
      loadSampleBtn.disabled = false;
    }
  });

  // 2. Preset Selection
  presetCards.forEach((card) => {
    card.addEventListener("click", () => {
      presetCards.forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      const input = card.querySelector("input");
      if (input) input.checked = true;
    });
  });

  function getSelectedPreset() {
    const checked = document.querySelector('input[name="preset"]:checked');
    return checked ? checked.value : "bold_creator";
  }

  // 3. Start Job & Polling
  startJobBtn.addEventListener("click", async () => {
    if (!selectedFile) {
      alert("Please upload or load a video first!");
      return;
    }

    startJobBtn.disabled = true;
    showStage("processing");
    stageBadge.textContent = "Rendering";
    jobStartTime = Date.now();

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("preset", getSelectedPreset());
    formData.append("llm_provider", llmProviderSelect.value);
    formData.append("language", videoLanguageSelect.value);

    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Job creation failed");
      }

      const job = await res.json();
      currentJobId = job.id;
      startPolling(currentJobId);
    } catch (err) {
      alert(`Error starting job: ${err.message}`);
      showStage("empty");
      startJobBtn.disabled = false;
      stageBadge.textContent = "Error";
    }
  });

  function startPolling(jobId) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) throw new Error(`Status check failed (${res.status})`);
        const job = await res.json();
        updateProgressUI(job);

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
    }, 1200);
  }

  function updateProgressUI(job) {
    const pct = Math.round(job.progress * 100);
    progressBarFill.style.width = `${Math.max(5, pct)}%`;
    progressPercent.textContent = `${pct}%`;

    const elapsedSec = Math.floor((Date.now() - jobStartTime) / 1000);
    progressTime.textContent = `Elapsed: ${elapsedSec}s`;

    // Step message
    const stepNames = {
      queued: "Waiting in queue...",
      probing: "Analyzing video dimensions & audio...",
      transcribing: "Transcribing speech with faster-whisper...",
      chunking: "Structuring natural cadence & phrases...",
      planning: "Assigning dynamic styles & avoiding collisions...",
      rendering: "Composing animated vertical MP4 with Remotion...",
      completed: "Render complete! Preparing video...",
      failed: "Render failed.",
    };
    processingStep.textContent = stepNames[job.step] || job.step;

    // Highlight checklist
    const stepIds = ["probing", "transcribing", "chunking", "planning", "rendering"];
    const currentStepIdx = stepIds.indexOf(job.step);

    stepIds.forEach((sId, idx) => {
      const el = document.getElementById(`step_${sId}`);
      if (!el) return;
      if (idx < currentStepIdx || job.status === "completed") {
        el.className = "step-item completed";
        el.querySelector(".step-icon").textContent = "✓";
      } else if (idx === currentStepIdx) {
        el.className = "step-item active";
        el.querySelector(".step-icon").textContent = "●";
      } else {
        el.className = "step-item";
        el.querySelector(".step-icon").textContent = "○";
      }
    });
  }

  async function onJobCompleted(job) {
    stageBadge.textContent = "Completed";
    startJobBtn.disabled = false;

    // Set video src
    resultVideo.src = `/api/jobs/${job.id}/output`;
    downloadBtn.href = `/api/jobs/${job.id}/output`;
    downloadBtn.download = `${job.id}_captioned.mp4`;

    // Fetch and render timeline
    try {
      const tlRes = await fetch(`/api/jobs/${job.id}/timeline`);
      if (tlRes.ok) {
        const timeline = await tlRes.json();
        renderTimelineEvents(timeline);
      }
    } catch (e) {
      console.warn("Could not load timeline:", e);
    }

    showStage("result");
  }

  function onJobFailed(job) {
    stageBadge.textContent = "Failed";
    startJobBtn.disabled = false;
    alert(`Caption generation failed: ${job.error || "Unknown error occurred"}`);
    showStage("empty");
  }

  function renderTimelineEvents(timeline) {
    eventsList.innerHTML = "";
    eventCount.textContent = timeline.events.length;
    jsonCode.textContent = JSON.stringify(timeline, null, 2);

    timeline.events.forEach((ev) => {
      const row = document.createElement("div");
      row.className = "event-row";

      const timeSpan = document.createElement("span");
      timeSpan.className = "event-time";
      timeSpan.textContent = `${ev.start.toFixed(2)}s - ${ev.end.toFixed(2)}s`;

      const textSpan = document.createElement("span");
      textSpan.className = "event-text";
      textSpan.textContent = ev.text;

      const badgeSpan = document.createElement("span");
      badgeSpan.className = "event-badge";
      badgeSpan.textContent = ev.style;

      row.appendChild(timeSpan);
      row.appendChild(textSpan);
      row.appendChild(badgeSpan);
      eventsList.appendChild(row);
    });
  }

  // Toggle JSON viewer
  toggleJsonBtn.addEventListener("click", () => {
    jsonViewer.classList.toggle("hidden");
    toggleJsonBtn.textContent = jsonViewer.classList.contains("hidden") ? "View JSON" : "Hide JSON";
  });

  // Copy JSON
  copyJsonBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(jsonCode.textContent).then(() => {
      copyJsonBtn.textContent = "Copied!";
      setTimeout(() => (copyJsonBtn.textContent = "Copy JSON"), 2000);
    });
  });

  // Reset
  resetBtn.addEventListener("click", () => {
    showStage("empty");
    stageBadge.textContent = "Awaiting Input";
    resultVideo.pause();
    resultVideo.src = "";
  });

  function showStage(stage) {
    stageEmpty.classList.toggle("hidden", stage !== "empty");
    stageProcessing.classList.toggle("hidden", stage !== "processing");
    stageResult.classList.toggle("hidden", stage !== "result");
  }
});
