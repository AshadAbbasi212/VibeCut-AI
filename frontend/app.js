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

  // Style Pool references
  const stylesPoolGrid = document.getElementById("stylesPoolGrid");
  const stylesBadgeCount = document.getElementById("stylesBadgeCount");
  const selectAllStylesBtn = document.getElementById("selectAllStylesBtn");
  const clearAllStylesBtn = document.getElementById("clearAllStylesBtn");
  const stylesSummaryBadge = document.getElementById("stylesSummaryBadge");
  const stylesSummaryText = document.getElementById("stylesSummaryText");
  const stylePresetQuickBtns = document.querySelectorAll(".btn-style-preset-quick");

  // CapCut Trimmer references
  const trimReadout = document.getElementById("trimReadout");
  const trimStartBadge = document.getElementById("trimStartBadge");
  const trimEndBadge = document.getElementById("trimEndBadge");
  const trimDurBadge = document.getElementById("trimDurBadge");
  const trimTrackWrapper = document.getElementById("trimTrackWrapper");
  const trimShadeLeft = document.getElementById("trimShadeLeft");
  const trimWindow = document.getElementById("trimWindow");
  const trimHandleLeft = document.getElementById("trimHandleLeft");
  const trimHandleRight = document.getElementById("trimHandleRight");
  const trimShadeRight = document.getElementById("trimShadeRight");
  const trimPlayhead = document.getElementById("trimPlayhead");
  const btnPlayCut = document.getElementById("btnPlayCut");
  const playCutIcon = document.getElementById("playCutIcon");
  const playCutLabel = document.getElementById("playCutLabel");

  // Draggable Caption & Positioning references
  const draggableCaptionBox = document.getElementById("draggableCaptionBox");
  const dragCoordBadge = document.getElementById("dragCoordBadge");
  const dragSizeBadge = document.getElementById("dragSizeBadge");
  const dragSampleText = document.getElementById("dragSampleText");
  const snapGuideUpper = document.getElementById("snapGuideUpper");
  const snapGuideCenter = document.getElementById("snapGuideCenter");
  const snapGuideLower = document.getElementById("snapGuideLower");
  const subPosLabel = document.getElementById("subPosLabel");
  const subPosSlider = document.getElementById("subPosSlider");
  const subPosQuickChips = document.querySelectorAll("#subPosQuickChips .btn-custom-chip");
  const captionSizeSlider = document.getElementById("captionSizeSlider");

  const subPosition = document.getElementById("subPosition");
  const videoLanguage = document.getElementById("videoLanguage");
  const llmProvider = document.getElementById("llmProvider");
  const aiDirectorBadge = document.getElementById("aiDirectorBadge");
  const aiEnhanceToggle = document.getElementById("aiEnhanceToggle");
  const draftToggle = document.getElementById("draftToggle");

  const startJobBtn = document.getElementById("startJobBtn");
  const btnProgressFill = document.getElementById("btnProgressFill");
  const btnTextLabel = document.getElementById("btnTextLabel");

  // Viral Boosters & Retention DOM references
  const headlineHookToggle = document.getElementById("headlineHookToggle");
  const headlineHookStateBadge = document.getElementById("headlineHookStateBadge");
  const headlineHookSettings = document.getElementById("headlineHookSettings");
  const headlineHookInput = document.getElementById("headlineHookInput");
  const headlineStyleChips = document.querySelectorAll("#headlineStyleChips .btn-custom-chip");
  const headlineDurationChips = document.querySelectorAll("#headlineDurationChips .btn-custom-chip");
  const headlineDurationInput = document.getElementById("headlineDurationInput");
  const clipLengthChips = document.querySelectorAll("#clipLengthSelector .btn-custom-chip");
  const btnFindViralClips = document.getElementById("btnFindViralClips");
  const findClipsBtnIcon = document.getElementById("findClipsBtnIcon");
  const findClipsBtnText = document.getElementById("findClipsBtnText");
  const viralClipsList = document.getElementById("viralClipsList");
  const progressBarToggle = document.getElementById("progressBarToggle");
  const progBarBottomBtn = document.getElementById("progBarBottomBtn");
  const autoEmojisToggle = document.getElementById("autoEmojisToggle");
  const kineticZoomToggle = document.getElementById("kineticZoomToggle");
  const soundEffectsToggle = document.getElementById("soundEffectsToggle");
  const bgMusicToggle = document.getElementById("bgMusicToggle");
  const watermarkInput = document.getElementById("watermarkInput");

  const canvasHeadlineHook = document.getElementById("canvasHeadlineHook");
  const canvasHeadlineHookInner = document.getElementById("canvasHeadlineHookInner");
  const canvasProgressBar = document.getElementById("canvasProgressBar");
  const canvasProgressBarFill = document.getElementById("canvasProgressBarFill");
  const canvasWatermark = document.getElementById("canvasWatermark");
  const canvasWatermarkText = document.getElementById("canvasWatermarkText");
  const viralClipsActions = document.getElementById("viralClipsActions");
  const btnBatchExportZip = document.getElementById("btnBatchExportZip");
  const batchZipIcon = document.getElementById("batchZipIcon");
  const batchZipLabel = document.getElementById("batchZipLabel");

  // Studio Mode Switcher references
  const tabFullStudio = document.getElementById("tabFullStudio");
  const tabClipsStudio = document.getElementById("tabClipsStudio");
  const fullStudioSection = document.getElementById("fullStudioSection");
  const clipsStudioSection = document.getElementById("clipsStudioSection");
  const btnSwitchToClips = document.getElementById("btnSwitchToClips");

  // AI Viral Reels Studio Tweaker DOM references
  const clipsCountBadge = document.getElementById("clipsCountBadge");
  const clipTweakerCard = document.getElementById("clipTweakerCard");
  const tweakerClipTitle = document.getElementById("tweakerClipTitle");
  const tweakerClipTiming = document.getElementById("tweakerClipTiming");
  const btnPlayActiveClip = document.getElementById("btnPlayActiveClip");
  const tweakerHeadlineStyleBadge = document.getElementById("tweakerHeadlineStyleBadge");
  const clipHeadlineInput = document.getElementById("clipHeadlineInput");
  const clipHeadlineStyleChips = document.querySelectorAll("#clipHeadlineStyleChips .btn-custom-chip");
  const clipHeadlineDurationChips = document.querySelectorAll("#clipHeadlineDurationChips .btn-custom-chip");
  const clipFontSizeChips = document.querySelectorAll("#clipFontSizeChips .btn-custom-chip");
  const clipFontSizeSlider = document.getElementById("clipFontSizeSlider");
  const clipFontSizeLabel = document.getElementById("clipFontSizeLabel");
  const clipPosChips = document.querySelectorAll("#clipPosChips .btn-custom-chip");
  const clipPosSlider = document.getElementById("clipPosSlider");
  const clipPosLabel = document.getElementById("clipPosLabel");
  const clipStyleChips = document.querySelectorAll("#clipStylePresetRow .btn-style-preset-quick");
  const clipStyleLabel = document.getElementById("clipStyleLabel");
  const clipHighlightColorSwatches = document.querySelectorAll("#clipHighlightColorSwatches .btn-color-swatch");
  const clipWatermarkInput = document.getElementById("clipWatermarkInput");
  const clipWatermarkBadge = document.getElementById("clipWatermarkBadge");
  const clipWatermarkToggle = document.getElementById("clipWatermarkToggle");
  const clipWatermarkInputContainer = document.getElementById("clipWatermarkInputContainer");
  const clipHeadlinePosChips = document.querySelectorAll("#clipHeadlinePosChips .btn-custom-chip");
  const clipHeadlinePosSlider = document.getElementById("clipHeadlinePosSlider");
  const clipHeadlinePosLabel = document.getElementById("clipHeadlinePosLabel");
  const clipStyleAiNotice = document.getElementById("clipStyleAiNotice");
  const watermarkToggle = document.getElementById("watermarkToggle");
  const watermarkInputContainer = document.getElementById("watermarkInputContainer");
  const clipKineticZoomToggle = document.getElementById("clipKineticZoomToggle");
  const clipPopSfxToggle = document.getElementById("clipPopSfxToggle");
  const clipBgMusicToggle = document.getElementById("clipBgMusicToggle");
  const clipAutoEmojisToggle = document.getElementById("clipAutoEmojisToggle");
  const btnRenderSingleClip = document.getElementById("btnRenderSingleClip");
  const clipBtnProgressFill = document.getElementById("clipBtnProgressFill");
  const clipBtnTextLabel = document.getElementById("clipBtnTextLabel");
  const btnBatchExportZipDedicated = document.getElementById("btnBatchExportZipDedicated");
  const clipLayoutChips = document.querySelectorAll("#clipLayoutChips .btn-custom-chip");
  const clipLayoutLabel = document.getElementById("clipLayoutLabel");
  const clipLayoutDescNotice = document.getElementById("clipLayoutDescNotice");
  const clipAiEnhanceToggle = document.getElementById("clipAiEnhanceToggle");
  const clipAiEnhanceBadge = document.getElementById("clipAiEnhanceBadge");

  let selectedClipLayout = "split_podcast";
  let selectedHeadlinePosRatio = 0.08;

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
  const allLayoutButtons = document.querySelectorAll(".btn-layout-opt");
  const allLayoutCards = document.querySelectorAll(".layout-style-card");
  const layoutSelectedLabel = document.getElementById("layoutSelectedLabel");
  const videoLayoutField = document.getElementById("videoLayoutField");
  const btnOpenPhotoModal = document.getElementById("btnOpenPhotoModal");
  const btnClosePhotoModal = document.getElementById("btnClosePhotoModal");
  const layoutPhotoModal = document.getElementById("layoutPhotoModal");
  const modalSelectButtons = document.querySelectorAll("[data-select-layout]");

  const viewIdle = document.getElementById("viewIdle");
  const viewSource = document.getElementById("viewSource");
  const sourceVideoPlayer = document.getElementById("sourceVideoPlayer");
  const sourceSingleWrap = document.getElementById("sourceSingleWrap");
  
  const sourceBlurWrap = document.getElementById("sourceBlurWrap");
  const sourceBlurBg = document.getElementById("sourceBlurBg");
  const sourceBlurMain = document.getElementById("sourceBlurMain");

  const sourceSplitWrap = document.getElementById("sourceSplitWrap");
  const sourceSplitTop = document.getElementById("sourceSplitTop");
  const sourceSplitBottom = document.getElementById("sourceSplitBottom");

  const sourceTripleWrap = document.getElementById("sourceTripleWrap");
  const sourceTripleTop = document.getElementById("sourceTripleTop");
  const sourceTripleMid = document.getElementById("sourceTripleMid");
  const sourceTripleBot = document.getElementById("sourceTripleBot");

  const sourcePhotoPreview = document.getElementById("sourcePhotoPreview");
  const sourcePhotoPreviewBadge = document.getElementById("sourcePhotoPreviewBadge");

  const viewProcessing = document.getElementById("viewProcessing");
  const viewResult = document.getElementById("viewResult");

  const procTitle = document.getElementById("procTitle");
  const procStep = document.getElementById("procStep");
  const procFill = document.getElementById("procFill");
  const procPct = document.getElementById("procPct");
  const procElapsed = document.getElementById("procElapsed");

  const resultVideo = document.getElementById("resultVideo");
  const closeResultBtn = document.getElementById("closeResultBtn");
  const resultActions = document.getElementById("resultActions");
  const downloadMp4Btn = document.getElementById("downloadMp4Btn");
  const downloadSrtBtn = document.getElementById("downloadSrtBtn");
  const downloadVttBtn = document.getElementById("downloadVttBtn");
  const resetBtn = document.getElementById("resetBtn");

  const editorCard = document.getElementById("editorCard");
  const eventCount = document.getElementById("eventCount");
  const phrasesList = document.getElementById("phrasesList");
  const saveEditsBtn = document.getElementById("saveEditsBtn");
  const rerenderBtn = document.getElementById("rerenderBtn");
  const toast = document.getElementById("toast");

  // State Management
  let selectedFile = null;
  let currentJobId = null;
  let pollInterval = null;
  let jobStartTime = null;
  let currentTimeline = null;
  let selectedAspectRatio = "9:16";

  // Viral Boosters State
  let selectedHeadlineHookEnabled = false;
  let selectedHeadlineHookText = "🔥 WAIT TILL THE END...";
  let selectedHeadlineHookStyle = "badge";
  let selectedHeadlineDuration = null; // null = full video sticky, or 5.0, 10.0
  let selectedClipLength = "30s";
  let activeViralClips = [];
  let selectedProgressBar = true;
  let selectedProgressBarPos = "bottom";
  let selectedAutoEmojis = true;

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
    const resolutionMap = {
      "9:16": "1080×1920 • 30 FPS • 9:16",
      "16:9": "1920×1080 • 30 FPS • 16:9",
      "1:1": "1080×1080 • 30 FPS • 1:1",
      "4:5": "1080×1350 • 30 FPS • 4:5",
    };
    if (stageStatus) stageStatus.textContent = resolutionMap[ar] || `${ar} • 30 FPS`;
    updateSourcePreviewFraming();
    showToast(`Switched canvas to ${ar}`);
  }

  allArButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      setAspectRatio(btn.dataset.ar);
    });
  });

  // 2b. Video Reframe Layout Selector & Live Framing Preview Engine
  let selectedVideoLayout = "active_speaker";

  const layoutPhotoMap = {
    active_speaker: "/assets/layouts/solo_fullscreen_clean.jpg?v=clean3",
    blur_fit: "/assets/layouts/blur_fit_clean.jpg?v=clean3",
    split_podcast: "/assets/layouts/split_podcast_clean.jpg?v=clean3",
    split_triple: "/assets/layouts/split_triple_clean.jpg?v=clean3",
    focus_left: "/assets/layouts/solo_fullscreen_clean.jpg?v=clean3",
    focus_right: "/assets/layouts/solo_fullscreen_clean.jpg?v=clean3",
    fill: "/assets/layouts/solo_fullscreen_clean.jpg?v=clean3",
  };

  const layoutLabels = {
    active_speaker: "Solo Full-Screen (Active Speaker)",
    blur_fit: "Ambient Frosted Blur (Zero Crop)",
    split_podcast: "Podcast Split (Dual-Cam Stack)",
    split_triple: "3-Way Panel Stack (Trio)",
    focus_left: "Left Speaker Focus",
    focus_right: "Right Speaker Focus",
    fill: "Center Zoom (Full Crop)",
  };

  function setVideoLayout(layout) {
    selectedVideoLayout = layout;

    // Toggle active state on 4 visual photo cards
    allLayoutCards.forEach((card) => {
      card.classList.toggle("active", card.dataset.layout === layout);
    });

    // Toggle active state on manual override buttons
    allLayoutButtons.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.layout === layout);
    });

    if (layoutSelectedLabel) {
      layoutSelectedLabel.textContent = layoutLabels[layout] || layout;
    }

    updateSourcePreviewFraming();
    showToast(`Selected Layout: ${layoutLabels[layout] || layout}`);
  }

  // Bind 4 visual photo cards
  allLayoutCards.forEach((card) => {
    card.addEventListener("click", () => {
      setVideoLayout(card.dataset.layout);
    });
  });

  // Bind manual static crop buttons
  allLayoutButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      setVideoLayout(btn.dataset.layout);
    });
  });

  // Initial layout synchronization
  allLayoutCards.forEach((card) => {
    card.classList.toggle("active", card.dataset.layout === selectedVideoLayout);
  });
  if (layoutSelectedLabel) {
    layoutSelectedLabel.textContent = layoutLabels[selectedVideoLayout] || selectedVideoLayout;
  }
  updateSourcePreviewFraming();

  // Photo Comparison Modal Handlers
  if (btnOpenPhotoModal && layoutPhotoModal) {
    btnOpenPhotoModal.addEventListener("click", () => {
      layoutPhotoModal.classList.add("open");
    });
  }

  if (btnClosePhotoModal && layoutPhotoModal) {
    btnClosePhotoModal.addEventListener("click", () => {
      layoutPhotoModal.classList.remove("open");
    });
  }

  if (layoutPhotoModal) {
    layoutPhotoModal.addEventListener("click", (e) => {
      if (e.target === layoutPhotoModal) {
        layoutPhotoModal.classList.remove("open");
      }
    });
  }

  modalSelectButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const chosen = btn.dataset.selectLayout;
      if (chosen) {
        setVideoLayout(chosen);
        if (layoutPhotoModal) layoutPhotoModal.classList.remove("open");
      }
    });
  });

  function updateSourcePreviewFraming() {
    const isVerticalAR = selectedAspectRatio === "9:16";
    const hasSource = sourceVideoPlayer && sourceVideoPlayer.src && sourceVideoPlayer.src.length > 0 && !sourceVideoPlayer.src.endsWith("#");
    const isLandscape = hasSource && sourceVideoPlayer.videoWidth > sourceVideoPlayer.videoHeight;

    // When NO video is loaded yet, show the high-res photo still right in phoneCanvas
    if (!hasSource) {
      if (sourcePhotoPreview && sourcePhotoPreviewBadge) {
        if (viewIdle && !viewIdle.classList.contains("hidden")) {
          // If in idle state, we can display the selected photo in viewSource
          viewIdle.classList.add("hidden");
          if (viewSource) viewSource.classList.remove("hidden");
        }
        sourcePhotoPreview.src = layoutPhotoMap[selectedVideoLayout] || layoutPhotoMap.active_speaker;
        sourcePhotoPreview.classList.remove("hidden");
        sourcePhotoPreviewBadge.classList.remove("hidden");
        sourcePhotoPreviewBadge.textContent = `📸 ${layoutLabels[selectedVideoLayout] || "Style"} Preview`;
        if (sourceCanvasTag) {
          sourceCanvasTag.innerHTML = `<span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #22c55e; margin-right: 4px; box-shadow: 0 0 6px #22c55e;"></span>Framing Preview`;
        }

        if (sourceSingleWrap) sourceSingleWrap.classList.add("hidden");
        if (sourceBlurWrap) sourceBlurWrap.classList.add("hidden");
        if (sourceSplitWrap) sourceSplitWrap.classList.add("hidden");
        if (sourceTripleWrap) sourceTripleWrap.classList.add("hidden");
      }
      return;
    }

    // Video IS loaded: Hide static photo overlay and display dynamic video layout
    if (sourcePhotoPreview) sourcePhotoPreview.classList.add("hidden");
    if (sourcePhotoPreviewBadge) sourcePhotoPreviewBadge.classList.add("hidden");
    if (sourceCanvasTag) {
      sourceCanvasTag.innerHTML = `<span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #38bdf8; margin-right: 4px; box-shadow: 0 0 6px #38bdf8;"></span>Live Stream`;
    }

    // Hide all layout wraps initially
    if (sourceSingleWrap) sourceSingleWrap.classList.add("hidden");
    if (sourceBlurWrap) sourceBlurWrap.classList.add("hidden");
    if (sourceSplitWrap) sourceSplitWrap.classList.add("hidden");
    if (sourceTripleWrap) sourceTripleWrap.classList.add("hidden");

    // Layout 1: Ambient Frosted Blur (16:9 contained with dynamic blurred mirror backdrop)
    if (isVerticalAR && isLandscape && selectedVideoLayout === "blur_fit") {
      if (sourceBlurWrap) {
        sourceBlurWrap.classList.remove("hidden");
        if (sourceBlurBg && sourceBlurBg.src !== sourceVideoPlayer.src) {
          sourceBlurBg.src = sourceVideoPlayer.src;
        }
        if (sourceBlurMain && sourceBlurMain.src !== sourceVideoPlayer.src) {
          sourceBlurMain.src = sourceVideoPlayer.src;
        }
        if (sourceBlurBg) sourceBlurBg.currentTime = sourceVideoPlayer.currentTime;
        if (sourceBlurMain) sourceBlurMain.currentTime = sourceVideoPlayer.currentTime;
      }
      return;
    }

    // Layout 2: Podcast Split (Dual-Cam Stack)
    if (isVerticalAR && isLandscape && selectedVideoLayout === "split_podcast") {
      if (sourceSplitWrap) {
        sourceSplitWrap.classList.remove("hidden");
        if (sourceSplitTop && sourceSplitTop.src !== sourceVideoPlayer.src) {
          sourceSplitTop.src = sourceVideoPlayer.src;
        }
        if (sourceSplitBottom && sourceSplitBottom.src !== sourceVideoPlayer.src) {
          sourceSplitBottom.src = sourceVideoPlayer.src;
        }
        if (sourceSplitTop) sourceSplitTop.currentTime = sourceVideoPlayer.currentTime;
        if (sourceSplitBottom) sourceSplitBottom.currentTime = sourceVideoPlayer.currentTime;
      }
      return;
    }

    // Layout 3: 3-Way Panel Stack (Trio)
    if (isVerticalAR && isLandscape && selectedVideoLayout === "split_triple") {
      if (sourceTripleWrap) {
        sourceTripleWrap.classList.remove("hidden");
        if (sourceTripleTop && sourceTripleTop.src !== sourceVideoPlayer.src) {
          sourceTripleTop.src = sourceVideoPlayer.src;
        }
        if (sourceTripleMid && sourceTripleMid.src !== sourceVideoPlayer.src) {
          sourceTripleMid.src = sourceVideoPlayer.src;
        }
        if (sourceTripleBot && sourceTripleBot.src !== sourceVideoPlayer.src) {
          sourceTripleBot.src = sourceVideoPlayer.src;
        }
        if (sourceTripleTop) sourceTripleTop.currentTime = sourceVideoPlayer.currentTime;
        if (sourceTripleMid) sourceTripleMid.currentTime = sourceVideoPlayer.currentTime;
        if (sourceTripleBot) sourceTripleBot.currentTime = sourceVideoPlayer.currentTime;
      }
      return;
    }

    // Layout 4 & Overrides: Solo Full-Screen (Active Speaker, Fill, Left/Right Focus)
    if (sourceSingleWrap) {
      sourceSingleWrap.classList.remove("hidden");
      if (sourceVideoPlayer) {
        if (selectedVideoLayout === "focus_left") {
          sourceVideoPlayer.style.objectFit = "cover";
          sourceVideoPlayer.style.objectPosition = "15% center";
        } else if (selectedVideoLayout === "focus_right") {
          sourceVideoPlayer.style.objectFit = "cover";
          sourceVideoPlayer.style.objectPosition = "85% center";
        } else if (selectedVideoLayout === "fill" || selectedVideoLayout === "active_speaker") {
          sourceVideoPlayer.style.objectFit = "cover";
          sourceVideoPlayer.style.objectPosition = "center center";
        } else {
          sourceVideoPlayer.style.objectFit = "contain";
          sourceVideoPlayer.style.objectPosition = "center center";
        }
      }
    }
  }

  // Synchronize playback between main source video and multi-layer preview wraps
  if (sourceVideoPlayer) {
    const getActiveChildVideos = () => {
      const active = [];
      if (sourceSplitWrap && !sourceSplitWrap.classList.contains("hidden")) {
        if (sourceSplitTop) active.push(sourceSplitTop);
        if (sourceSplitBottom) active.push(sourceSplitBottom);
      }
      if (sourceBlurWrap && !sourceBlurWrap.classList.contains("hidden")) {
        if (sourceBlurBg) active.push(sourceBlurBg);
        if (sourceBlurMain) active.push(sourceBlurMain);
      }
      if (sourceTripleWrap && !sourceTripleWrap.classList.contains("hidden")) {
        if (sourceTripleTop) active.push(sourceTripleTop);
        if (sourceTripleMid) active.push(sourceTripleMid);
        if (sourceTripleBot) active.push(sourceTripleBot);
      }
      return active;
    };

    sourceVideoPlayer.addEventListener("play", () => {
      const children = getActiveChildVideos();
      children.forEach((v) => {
        v.currentTime = sourceVideoPlayer.currentTime;
        v.play().catch(() => {});
      });
    });

    sourceVideoPlayer.addEventListener("pause", () => {
      const children = getActiveChildVideos();
      children.forEach((v) => v.pause());
    });

    sourceVideoPlayer.addEventListener("seeked", () => {
      const children = getActiveChildVideos();
      children.forEach((v) => {
        v.currentTime = sourceVideoPlayer.currentTime;
      });
    });

    sourceVideoPlayer.addEventListener("timeupdate", () => {
      const children = getActiveChildVideos();
      children.forEach((v) => {
        if (Math.abs(v.currentTime - sourceVideoPlayer.currentTime) > 0.25) {
          v.currentTime = sourceVideoPlayer.currentTime;
        }
      });
    });

    sourceVideoPlayer.addEventListener("loadedmetadata", () => {
      updateSourcePreviewFraming();
    });
  }

  // 2b. Creator Customization Options State & Wiring
  let selectedCaptionSize = "medium";
  let selectedBgStyle = "transparent";
  let selectedStylePacing = "sentence";
  let selectedHighlightColor = "#38BDF8";
  let activeShowcaseStyle = "hormozi_bold";

  function getNumericCaptionSize(size) {
    if (size === "small") return 38;
    if (size === "medium") return 52;
    if (size === "large") return 68;
    const num = parseInt(size, 10);
    if (!isNaN(num) && num >= 16 && num <= 160) return num;
    return 52;
  }

  // Caption Size Chips & Slider Wiring
  const captionSizeChips = document.querySelectorAll("#captionSizeChips .btn-custom-chip");
  const captionSizeSelectedLabel = document.getElementById("captionSizeSelectedLabel");

  function setCaptionSize(size, updateSlider = true) {
    selectedCaptionSize = size;
    const numericPx = getNumericCaptionSize(size);

    // Update active class on chips
    captionSizeChips.forEach((btn) => {
      const btnSize = btn.dataset.size;
      const isMatch = btnSize === size || (size === String(numericPx) && getNumericCaptionSize(btnSize) === numericPx);
      btn.classList.toggle("active", isMatch);
    });

    // Update slider position if requested
    if (updateSlider && captionSizeSlider) {
      captionSizeSlider.value = numericPx;
    }
    if (clipFontSizeSlider && updateSlider) {
      clipFontSizeSlider.value = numericPx;
    }

    // Update label text
    const sizeLabels = {
      small: "Small (38px Compact)",
      medium: "Medium (52px Sweet Spot)",
      large: "Large (68px Bold Pop)",
      "38": "Small (38px Compact)",
      "52": "Medium (52px Sweet Spot)",
      "68": "Large (68px Bold Pop)",
    };
    if (captionSizeSelectedLabel) {
      captionSizeSelectedLabel.textContent = sizeLabels[size] || `Custom (${numericPx}px)`;
    }
    if (clipFontSizeLabel) {
      clipFontSizeLabel.textContent = sizeLabels[size] || `${numericPx}px Custom`;
    }

    if (clipFontSizeChips) {
      clipFontSizeChips.forEach((btn) => {
        const btnSize = btn.dataset.size;
        const isMatch = btnSize === size || (size === String(numericPx) && getNumericCaptionSize(btnSize) === numericPx);
        btn.classList.toggle("active", isMatch);
      });
    }

    // Update canvas screen badge
    if (dragSizeBadge) {
      dragSizeBadge.textContent = `${numericPx}px`;
    }

    if (typeof updateCaptionShowcase === "function") updateCaptionShowcase();
  }

  captionSizeChips.forEach((btn) => {
    btn.addEventListener("click", () => {
      setCaptionSize(btn.dataset.size, true);
      showToast(`Caption font size: ${btn.dataset.size}`);
    });
  });

  if (clipFontSizeChips) {
    clipFontSizeChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        setCaptionSize(btn.dataset.size, true);
        showToast(`Clip font size: ${btn.dataset.size}`);
      });
    });
  }

  if (captionSizeSlider) {
    captionSizeSlider.addEventListener("input", (e) => {
      const val = e.target.value;
      let matchedNamed = val;
      if (val === "38") matchedNamed = "small";
      else if (val === "52") matchedNamed = "medium";
      else if (val === "68") matchedNamed = "large";
      setCaptionSize(matchedNamed, false);
      if (clipFontSizeSlider) clipFontSizeSlider.value = val;
    });
  }

  if (clipFontSizeSlider) {
    clipFontSizeSlider.addEventListener("input", (e) => {
      const val = e.target.value;
      let matchedNamed = val;
      if (val === "38") matchedNamed = "small";
      else if (val === "52") matchedNamed = "medium";
      else if (val === "68") matchedNamed = "large";
      setCaptionSize(matchedNamed, false);
      if (captionSizeSlider) captionSizeSlider.value = val;
    });
  }

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
      if (typeof updateCaptionShowcase === "function") updateCaptionShowcase();
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
      if (typeof updateCaptionShowcase === "function") updateCaptionShowcase();
      showToast(`Highlight color: ${btn.title}`);
    });
  });

  // AI Director UI & Local API Key Management
  function updateAiDirectorUI() {
    const prov = llmProvider ? llmProvider.value : "none";
    const isAi = prov !== "none";

    if (aiDirectorBadge) {
      if (isAi) {
        aiDirectorBadge.textContent = prov.toUpperCase();
        aiDirectorBadge.style.background = "rgba(139, 92, 246, 0.25)";
        aiDirectorBadge.style.color = "#c084fc";
        aiDirectorBadge.style.borderColor = "rgba(168, 85, 247, 0.5)";
      } else {
        aiDirectorBadge.textContent = "OFF";
        aiDirectorBadge.style.background = "rgba(100, 116, 139, 0.15)";
        aiDirectorBadge.style.color = "#94a3b8";
        aiDirectorBadge.style.borderColor = "rgba(100, 116, 139, 0.3)";
      }
    }

    if (aiEnhanceToggle) {
      aiEnhanceToggle.disabled = !isAi;
      if (!isAi) aiEnhanceToggle.checked = false;
    }
  }

  if (llmProvider) {
    llmProvider.addEventListener("change", updateAiDirectorUI);
  }

  // Initialize AI Director UI state
  updateAiDirectorUI();

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
    resetStudioForNewVideo();
  });

  function handleFile(file) {
    if (!file.type.startsWith("video/") && !file.name.endsWith(".mp4") && !file.name.endsWith(".mov") && !file.name.endsWith(".webm")) {
      showToast("Please select a video file (MP4, MOV, WebM).");
      return;
    }

    // Clean up previous render or job state
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
    if (resultVideo) {
      resultVideo.pause();
      resultVideo.removeAttribute("src");
      resultVideo.load();
    }
    if (resultActions) resultActions.classList.add("hidden");
    if (editorCard) editorCard.classList.add("hidden");
    if (pipelineProgressCard) pipelineProgressCard.classList.add("hidden");
    if (startJobBtn) startJobBtn.disabled = false;
    if (btnProgressFill) btnProgressFill.style.width = "0%";
    if (btnTextLabel) btnTextLabel.textContent = "Generate Captioned Video ⚡";
    currentJobId = null;
    currentTimeline = null;

    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = `${(file.size / (1024 * 1024)).toFixed(1)} MB`;

    dropPrompt.classList.add("hidden");
    fileBadge.classList.remove("hidden");
    const shortName = file.name.length > 20 ? file.name.slice(0, 18) + "..." : file.name;
    stageStatus.textContent = shortName;
    stageStatus.title = `Raw Source: ${file.name}`;

    // Instant Preview in Canvas across all layout layers
    const objectUrl = URL.createObjectURL(file);
    sourceVideoPlayer.src = objectUrl;
    if (sourceSplitTop) { sourceSplitTop.src = objectUrl; sourceSplitTop.load(); }
    if (sourceSplitBottom) { sourceSplitBottom.src = objectUrl; sourceSplitBottom.load(); }
    if (sourceBlurBg) { sourceBlurBg.src = objectUrl; sourceBlurBg.load(); }
    if (sourceBlurMain) { sourceBlurMain.src = objectUrl; sourceBlurMain.load(); }
    if (sourceTripleTop) { sourceTripleTop.src = objectUrl; sourceTripleTop.load(); }
    if (sourceTripleMid) { sourceTripleMid.src = objectUrl; sourceTripleMid.load(); }
    if (sourceTripleBot) { sourceTripleBot.src = objectUrl; sourceTripleBot.load(); }
    sourceVideoPlayer.load();
    showStage("source");
    updateSourcePreviewFraming();

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

  // =========================================================================
  // 4. Style Pool Multi-Selector, Live Examples & Presets
  // =========================================================================
  const ALL_AVAILABLE_STYLES = [
    { id: "hormozi_bold", name: "Hormozi Bold", icon: "⚡", tag: "Trending", sampleText: "VIRAL BOLD", desc: "Alex Hormozi uppercase, yellow pop, heavy drop shadow" },
    { id: "beast_impact", name: "MrBeast Impact", icon: "⚡", tag: "Viral Hook", sampleText: "RETENTION POP", desc: "MrBeast pop, 3D black stroke, lime & cyber-yellow punch" },
    { id: "highlighter_marker", name: "Ali Marker", icon: "🖍️", tag: "Educational", sampleText: "SMART HIGHLIGHT", desc: "Ali Abdaal text with animated pastel highlighter sweep" },
    { id: "cinematic_minimal", name: "Cinematic A24", icon: "🎬", tag: "Documentary", sampleText: "LETTERBOX SUB", desc: "A24 / Netflix widescreen frosted glass subtitle pill" },
    { id: "cyber_hud", name: "Cyberpunk HUD", icon: "🤖", tag: "Sci-Fi HUD", sampleText: "[HUD TARGET]", desc: "Futuristic telemetry brackets, monospace console, cyan glow" },
    { id: "retro_vaporwave", name: "Retro 80s", icon: "🌴", tag: "Aesthetic", sampleText: "RETRO 80s", desc: "Dual chrome gradient, glowing grid card" },
    { id: "karaoke_bounce", name: "Karaoke Bounce", icon: "🎤", tag: "Kinetic", sampleText: "KARAOKE •", desc: "Word-by-word hopping bounce physics dot with amber glow" },
    { id: "fire_burn", name: "Fiery Flame", icon: "🔥", tag: "High Energy", sampleText: "FIRE BLAZE", desc: "Flame gradient text with flickering fiery red shadow" },
    { id: "title3d", name: "3D Pop Title", icon: "🧊", tag: "3D Pop", sampleText: "POP 3D", desc: "Extruded multi-layer isometric 3D typography" },
    { id: "neon_glow", name: "Cyber Neon", icon: "💡", tag: "Glow", sampleText: "CYBER NEON", desc: "Electric cyan luminous glow with pulsing flicker" },
    { id: "pill_word", name: "Dynamic Pill", icon: "💊", tag: "Minimal", sampleText: "CLEAN PILL", desc: "Sleek pill badge with word-by-word active pill" },
    { id: "typewriter_terminal", name: "Hacker Terminal", icon: "💻", tag: "Tech", sampleText: "> CODE_", desc: "Monospace retro terminal console with blinking prompt" },
    { id: "glitch_kinetic", name: "Kinetic Glitch", icon: "💥", tag: "Glitch", sampleText: "GLITCH", desc: "RGB channel split displacement with kinetic jitter" },
    { id: "quote_editorial", name: "Editorial Quote", icon: "📰", tag: "Luxury", sampleText: "“Editorial”", desc: "Magazine serif typography with amber quotation mark" },
    { id: "comic_bubble", name: "Comic Bubble", icon: "💬", tag: "Pop Art", sampleText: "POW!", desc: "Pop-art dialogue speech bubble with bold black stroke" },
    { id: "paper_cutout", name: "Paper Cutout", icon: "✂️", tag: "Craft", sampleText: "TORN NOTE", desc: "Layered kraft-paper torn note with washi tape" },
    { id: "gradient_outline", name: "Gradient Outline", icon: "🌈", tag: "Modern", sampleText: "OUTLINE", desc: "Iridescent gradient-bordered capsule with subtle glow" },
    { id: "minimal_underline", name: "Minimal Underline", icon: "✨", tag: "Clean", sampleText: "MINIMAL", desc: "Swiss minimalist typography with expanding underline" },
    { id: "blob_card", name: "Blob Card", icon: "🫧", tag: "Glass", sampleText: "BLOB CARD", desc: "Organic morphing SVG blob card with spring pop-in" },
    { id: "serif_title", name: "Serif Title", icon: "🏛️", tag: "Editorial", sampleText: "EDITORIAL", desc: "Editorial Fraunces serif with oval doodle" },
    { id: "numbered_point", name: "Numbered Step", icon: "🔢", tag: "List", sampleText: "01 STEP", desc: "Italic serif numeral badge with circle doodle" },
    { id: "handwritten", name: "Marker Script", icon: "✍️", tag: "Script", sampleText: "Script", desc: "Casual expressive handwritten script with soft shadow" },
    { id: "arc_letters", name: "Arc Curve", icon: "🪐", tag: "Curved", sampleText: "ARC CURVE", desc: "Curved letter placement along an arching trajectory" },
    { id: "sticker", name: "Graphic Sticker", icon: "🏷️", tag: "Graphic", sampleText: "★ STICKER", desc: "Vector graphic sticker with drop-shadow glow and float" },
  ];

  // All 24 styles active by default
  let selectedStyles = ALL_AVAILABLE_STYLES.map((s) => s.id);

  function renderStylesPool() {
    if (!stylesPoolGrid) return;
    stylesPoolGrid.innerHTML = "";

    ALL_AVAILABLE_STYLES.forEach((style) => {
      const isSelected = selectedStyles.includes(style.id);
      const card = document.createElement("div");
      card.className = `style-chip-item ${isSelected ? "active" : ""}`;
      card.dataset.styleId = style.id;
      card.title = `${style.name} — ${style.desc}`;

      card.innerHTML = `
        <div class="style-chip-top">
          <span class="style-chip-icon">${style.icon}</span>
          <span class="style-chip-check" title="Toggle style inclusion">✓</span>
        </div>
        <span class="style-chip-title">${style.name}</span>
        <div class="style-mini-sample style-sample-${style.id}">
          ${style.sampleText || style.tag}
        </div>
      `;

      card.addEventListener("click", (e) => {
        if (e.target.closest(".style-chip-check")) {
          toggleStyleSelection(style.id);
        } else {
          if (!selectedStyles.includes(style.id)) {
            selectedStyles.push(style.id);
            renderStylesPool();
          }
        }
        updateCaptionShowcase(style.id);
      });

      card.addEventListener("mouseenter", () => {
        updateCaptionShowcase(style.id);
      });

      stylesPoolGrid.appendChild(card);
    });

    updateStylesSummary();
  }

  function toggleStyleSelection(styleId) {
    if (selectedStyles.includes(styleId)) {
      if (selectedStyles.length === 1) {
        showToast("At least 1 style must remain selected.");
        return;
      }
      selectedStyles = selectedStyles.filter((id) => id !== styleId);
    } else {
      selectedStyles.push(styleId);
    }
    renderStylesPool();
  }

  function updateStylesSummary() {
    const count = selectedStyles.length;
    if (stylesBadgeCount) {
      stylesBadgeCount.textContent = `${count} of ${ALL_AVAILABLE_STYLES.length} Selected`;
    }

    if (stylesSummaryBadge && stylesSummaryText) {
      if (count === 1) {
        const found = ALL_AVAILABLE_STYLES.find((s) => s.id === selectedStyles[0]);
        stylesSummaryBadge.textContent = "SINGLE STYLE MODE";
        stylesSummaryText.textContent = `All video captions will consistently use ${found ? found.name : selectedStyles[0]}.`;
      } else if (count === ALL_AVAILABLE_STYLES.length) {
        stylesSummaryBadge.textContent = "DYNAMIC MIX (ALL 24)";
        stylesSummaryText.textContent = "Rotating smoothly through all 24 creator styles sentence-by-sentence.";
      } else {
        stylesSummaryBadge.textContent = `${count} STYLES POOL`;
        stylesSummaryText.textContent = `Custom pool: video rotates exclusively through your ${count} chosen styles.`;
      }
    }

    updateCaptionShowcase();
  }

  function updateCaptionShowcase(styleId) {
    if (styleId) {
      activeShowcaseStyle = styleId;
    } else if (selectedStyles.length > 0) {
      if (!selectedStyles.includes(activeShowcaseStyle)) {
        activeShowcaseStyle = selectedStyles[0];
      }
    }

    const styleObj = ALL_AVAILABLE_STYLES.find((s) => s.id === activeShowcaseStyle) || ALL_AVAILABLE_STYLES[0];
    const showcaseContainer = document.getElementById("showcaseCaptionContainer");
    const specsPill = document.getElementById("showcaseSpecsPill");
    const scTagStyle = document.getElementById("scTagStyle");
    const scTagSize = document.getElementById("scTagSize");
    const scTagBg = document.getElementById("scTagBg");
    const scTagColor = document.getElementById("scTagColor");
    const numericPx = getNumericCaptionSize(selectedCaptionSize);
    const sizeLabels = { small: "38px Small", medium: "52px Medium", large: "68px Large" };
    const displaySizeStr = sizeLabels[selectedCaptionSize] || `${numericPx}px Custom`;

    if (showcaseContainer) {
      let wordsHtml = "";
      if (styleObj.id === "beast_impact") {
        wordsHtml = `<div class="showcase-caption-text style-beast_impact bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">MASSIVE</span> <span class="sc-word sc-highlight">RETENTION</span> <span class="sc-word">HOOK</span></div>`;
      } else if (styleObj.id === "highlighter_marker") {
        wordsHtml = `<div class="showcase-caption-text style-highlighter_marker bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">Smart</span> <span class="sc-word sc-highlight">Educational</span> <span class="sc-word">Highlighter</span></div>`;
      } else if (styleObj.id === "cinematic_minimal") {
        wordsHtml = `<div class="showcase-caption-text style-cinematic_minimal bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">A24</span> <span class="sc-word sc-highlight">WIDESCREEN</span> <span class="sc-word">SUBTITLE</span></div>`;
      } else if (styleObj.id === "cyber_hud") {
        wordsHtml = `<div class="showcase-caption-text style-cyber_hud bg-${selectedBgStyle}" id="showcaseCaptionText"><span style="color:#00F5FF;font-weight:900;margin-right:4px;">[HUD]</span> <span class="sc-word">TARGET</span> <span class="sc-word sc-highlight">LOCKED</span> <span style="color:#00F5FF;font-weight:900;margin-left:4px;">01</span></div>`;
      } else if (styleObj.id === "typewriter_terminal") {
        wordsHtml = `<div class="showcase-caption-text style-typewriter_terminal bg-${selectedBgStyle}" id="showcaseCaptionText">&gt; <span class="sc-word">CODE</span> <span class="sc-word sc-highlight">EXECUTE</span><span class="cursor-blink" style="animation:pulse-dot 0.8s infinite;">_</span></div>`;
      } else if (styleObj.id === "quote_editorial" || styleObj.id === "serif_title") {
        wordsHtml = `<div class="showcase-caption-text style-${styleObj.id} bg-${selectedBgStyle}" id="showcaseCaptionText">“<span class="sc-word">Inspiring</span> <span class="sc-word sc-highlight">Editorial</span> <span class="sc-word">Thought</span>”</div>`;
      } else if (styleObj.id === "comic_bubble") {
        wordsHtml = `<div class="showcase-caption-text style-comic_bubble bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">VIRAL</span> <span class="sc-word sc-highlight">POW!</span> <span class="sc-word">COMIC</span></div>`;
      } else if (styleObj.id === "paper_cutout") {
        wordsHtml = `<div class="showcase-caption-text style-paper_cutout bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">TORN</span> <span class="sc-word sc-highlight">KRAFT</span> <span class="sc-word">NOTE</span></div>`;
      } else if (styleObj.id === "gradient_outline") {
        wordsHtml = `<div class="showcase-caption-text style-gradient_outline bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">IRIDESCENT</span> <span class="sc-word sc-highlight">GRADIENT</span> <span class="sc-word">CAPSULE</span></div>`;
      } else if (styleObj.id === "minimal_underline") {
        wordsHtml = `<div class="showcase-caption-text style-minimal_underline bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">Swiss</span> <span class="sc-word sc-highlight">Minimal</span> <span class="sc-word">Underline</span></div>`;
      } else if (styleObj.id === "numbered_point") {
        wordsHtml = `<div class="showcase-caption-text style-numbered_point bg-${selectedBgStyle}" id="showcaseCaptionText"><span style="display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:var(--accent);color:#000;font-size:12px;font-weight:900;margin-right:6px;">01</span> <span class="sc-word">ACTIONABLE</span> <span class="sc-word sc-highlight">STEP</span></div>`;
      } else if (styleObj.id === "handwritten") {
        wordsHtml = `<div class="showcase-caption-text style-handwritten bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">Expressive</span> <span class="sc-word sc-highlight">Handwritten</span> <span class="sc-word">Script</span></div>`;
      } else if (styleObj.id === "arc_letters") {
        wordsHtml = `<div class="showcase-caption-text style-arc_letters bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">CURVED</span> <span class="sc-word sc-highlight">ARC</span> <span class="sc-word">BOUNCE</span></div>`;
      } else if (styleObj.id === "sticker") {
        wordsHtml = `<div class="showcase-caption-text style-sticker bg-${selectedBgStyle}" id="showcaseCaptionText"><span style="margin-right:6px;">🏷️</span> <span class="sc-word">STICKER</span> <span class="sc-word sc-highlight">BADGE</span></div>`;
      } else if (styleObj.id === "blob_card") {
        wordsHtml = `<div class="showcase-caption-text style-blob_card bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">ORGANIC</span> <span class="sc-word sc-highlight">BLOB</span> <span class="sc-word">CARD</span></div>`;
      } else if (styleObj.id === "pill_word") {
        wordsHtml = `<div class="showcase-caption-text style-pill_word bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">CLEAN</span> <span class="sc-word sc-highlight">SPOKEN</span> <span class="sc-word">PILL</span></div>`;
      } else if (styleObj.id === "title3d") {
        wordsHtml = `<div class="showcase-caption-text style-title3d bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">EXTRUDED</span> <span class="sc-word sc-highlight">3D POP</span> <span class="sc-word">TITLE</span></div>`;
      } else if (styleObj.id === "retro_vaporwave") {
        wordsHtml = `<div class="showcase-caption-text style-retro_vaporwave bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">SYNTHWAVE</span> <span class="sc-word sc-highlight">RETRO</span> <span class="sc-word">80S</span></div>`;
      } else if (styleObj.id === "fire_burn") {
        wordsHtml = `<div class="showcase-caption-text style-fire_burn bg-${selectedBgStyle}" id="showcaseCaptionText">🔥 <span class="sc-word">BLAZING</span> <span class="sc-word sc-highlight">FIRE</span> <span class="sc-word">FLAME</span></div>`;
      } else if (styleObj.id === "karaoke_bounce") {
        wordsHtml = `<div class="showcase-caption-text style-karaoke_bounce bg-${selectedBgStyle}" id="showcaseCaptionText">🎤 <span class="sc-word">KARAOKE</span> <span class="sc-word sc-highlight">• BOUNCE</span> <span class="sc-word">SYNC</span></div>`;
      } else if (styleObj.id === "neon_glow") {
        wordsHtml = `<div class="showcase-caption-text style-neon_glow bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">ELECTRIC</span> <span class="sc-word sc-highlight">NEON</span> <span class="sc-word">GLOW</span></div>`;
      } else if (styleObj.id === "glitch_kinetic") {
        wordsHtml = `<div class="showcase-caption-text style-glitch_kinetic bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">KINETIC</span> <span class="sc-word sc-highlight">RGB</span> <span class="sc-word">GLITCH</span></div>`;
      } else {
        wordsHtml = `<div class="showcase-caption-text style-${styleObj.id} bg-${selectedBgStyle}" id="showcaseCaptionText"><span class="sc-word">VIRAL</span> <span class="sc-word sc-highlight" id="showcaseHighlightWord">CAPTIONS</span> <span class="sc-word">THAT</span> <span class="sc-word sc-pop">POP</span></div>`;
      }
      showcaseContainer.innerHTML = wordsHtml;

      const showcaseText = document.getElementById("showcaseCaptionText");
      if (showcaseText) {
        showcaseText.style.fontSize = `${Math.round(numericPx * 0.404)}px`;
      }
    }

    const bgLabels = { transparent: "Transparent", glass: "Dark Glass", solid: "White Pill" };

    if (specsPill) {
      specsPill.textContent = `${styleObj.name} • ${displaySizeStr} • ${bgLabels[selectedBgStyle] || selectedBgStyle}`;
    }
    if (scTagStyle) scTagStyle.textContent = `${styleObj.icon} ${styleObj.name}`;
    if (scTagSize) scTagSize.textContent = `📏 ${displaySizeStr}`;
    if (scTagBg) scTagBg.textContent = `🔲 ${bgLabels[selectedBgStyle] || selectedBgStyle}`;
    if (scTagColor) scTagColor.textContent = `🎨 ${highlightColorSelectedLabel ? highlightColorSelectedLabel.textContent : selectedHighlightColor}`;

    updateDraggableCaptionPreview();
  }

  function updateDraggableCaptionPreview() {
    if (!dragSampleText || !draggableCaptionBox) return;

    const styleObj = ALL_AVAILABLE_STYLES.find((s) => s.id === activeShowcaseStyle) || ALL_AVAILABLE_STYLES[0];
    const numericPx = getNumericCaptionSize(selectedCaptionSize);

    // Dynamic font size on preview canvas (52px base -> ~14px on ~280px canvas, ratio ~0.27)
    dragSampleText.style.fontSize = `${Math.round(numericPx * 0.27)}px`;
    if (dragSizeBadge) {
      dragSizeBadge.textContent = `${numericPx}px`;
    }
    
    // Sync backdrop styling to draggable box on phoneCanvas
    if (selectedBgStyle === "transparent") {
      draggableCaptionBox.style.background = "rgba(10, 12, 18, 0.45)";
      draggableCaptionBox.style.backdropFilter = "blur(8px)";
      draggableCaptionBox.style.border = "1.5px dashed var(--accent)";
      draggableCaptionBox.style.boxShadow = "none";
    } else if (selectedBgStyle === "glass") {
      draggableCaptionBox.style.background = "rgba(15, 23, 42, 0.85)";
      draggableCaptionBox.style.backdropFilter = "blur(14px)";
      draggableCaptionBox.style.border = "1.5px solid rgba(56, 189, 248, 0.5)";
      draggableCaptionBox.style.boxShadow = "0 8px 28px rgba(0,0,0,0.6)";
    } else if (selectedBgStyle === "solid") {
      draggableCaptionBox.style.background = "#ffffff";
      draggableCaptionBox.style.backdropFilter = "none";
      draggableCaptionBox.style.border = "1.5px solid #ffffff";
      draggableCaptionBox.style.boxShadow = "0 8px 28px rgba(0,0,0,0.7)";
    }

    // Reset default properties
    dragSampleText.style.fontStyle = "normal";
    dragSampleText.style.letterSpacing = "normal";
    dragSampleText.style.transform = "none";

    // Style-specific typography for canvas draggable overlay
    if (styleObj.id === "beast_impact") {
      dragSampleText.innerHTML = `MASSIVE <span class="highlight" style="color: #22C55E; background: none; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000;">RETENTION HOOK</span> POP`;
      dragSampleText.style.fontFamily = "'Montserrat', sans-serif";
      dragSampleText.style.fontWeight = "900";
      dragSampleText.style.textTransform = "uppercase";
      dragSampleText.style.transform = "rotate(-2deg)";
    } else if (styleObj.id === "highlighter_marker") {
      dragSampleText.innerHTML = `Smart <span class="highlight" style="background: #FEF08A; color: #0A0A0B; padding: 1px 6px; border-radius: 3px; text-shadow: none;">Educational</span> Marker`;
      dragSampleText.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
      dragSampleText.style.fontWeight = "800";
      dragSampleText.style.textTransform = "none";
    } else if (styleObj.id === "cinematic_minimal") {
      dragSampleText.innerHTML = `A24 <span class="highlight" style="color: #F59E0B; font-weight: 800;">WIDESCREEN</span> SUBTITLE`;
      dragSampleText.style.fontFamily = "'Inter', sans-serif";
      dragSampleText.style.fontWeight = "600";
      dragSampleText.style.letterSpacing = "0.14em";
      dragSampleText.style.textTransform = "uppercase";
    } else if (styleObj.id === "cyber_hud") {
      dragSampleText.innerHTML = `[HUD] <span class="highlight" style="color: #00F5FF; text-shadow: 0 0 8px #00F5FF;">TARGET LOCKED</span> 01`;
      dragSampleText.style.fontFamily = "'JetBrains Mono', monospace";
      dragSampleText.style.fontWeight = "700";
      dragSampleText.style.textTransform = "uppercase";
    } else if (styleObj.id === "hormozi_bold") {
      dragSampleText.innerHTML = `CREATING <span class="highlight" style="color: #FACC15; background: none; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000;">DYNAMIC CAPTIONS</span> THAT POP`;
      dragSampleText.style.fontFamily = "'Montserrat', sans-serif";
      dragSampleText.style.fontWeight = "900";
      dragSampleText.style.textTransform = "uppercase";
    } else if (styleObj.id === "retro_vaporwave") {
      dragSampleText.innerHTML = `SYNTHWAVE <span class="highlight" style="color: #38BDF8; background: none;">DYNAMIC CAPTIONS</span> 80S`;
      dragSampleText.style.fontFamily = "'Montserrat', sans-serif";
      dragSampleText.style.fontWeight = "800";
      dragSampleText.style.textTransform = "uppercase";
    } else if (styleObj.id === "fire_burn") {
      dragSampleText.innerHTML = `🔥 BLAZING <span class="highlight" style="color: #EF4444; background: none; text-shadow: 0 0 10px #EF4444;">FIRE FLAME</span> POP`;
      dragSampleText.style.fontFamily = "'Montserrat', sans-serif";
      dragSampleText.style.fontWeight = "900";
      dragSampleText.style.textTransform = "uppercase";
    } else if (styleObj.id === "karaoke_bounce") {
      dragSampleText.innerHTML = `🎤 KARAOKE <span class="highlight" style="color: #FBBF24; background: none;">• BOUNCE</span> SYNC`;
      dragSampleText.style.fontFamily = "'Montserrat', sans-serif";
      dragSampleText.style.fontWeight = "800";
      dragSampleText.style.textTransform = "uppercase";
    } else if (styleObj.id === "typewriter_terminal") {
      dragSampleText.innerHTML = `&gt; CODE <span class="highlight" style="color: #22C55E; background: none; text-decoration: underline;">EXECUTE</span>_`;
      dragSampleText.style.fontFamily = "'JetBrains Mono', monospace";
      dragSampleText.style.fontWeight = "700";
      dragSampleText.style.textTransform = "none";
    } else if (styleObj.id === "quote_editorial" || styleObj.id === "serif_title") {
      dragSampleText.innerHTML = `“Creating <span class="highlight" style="color: #F59E0B;">Dynamic Captions</span> that pop”`;
      dragSampleText.style.fontFamily = "'Fraunces', Georgia, serif";
      dragSampleText.style.fontStyle = "italic";
      dragSampleText.style.fontWeight = "700";
      dragSampleText.style.textTransform = "none";
    } else if (styleObj.id === "comic_bubble") {
      dragSampleText.innerHTML = `VIRAL <span class="highlight" style="color: #EF4444; background: none;">POW!</span> COMIC`;
      dragSampleText.style.fontFamily = "'Montserrat', sans-serif";
      dragSampleText.style.fontWeight = "900";
      dragSampleText.style.textTransform = "uppercase";
    } else if (styleObj.id === "handwritten") {
      dragSampleText.innerHTML = `Expressive <span class="highlight" style="color: #38BDF8;">Handwritten</span> Script`;
      dragSampleText.style.fontFamily = "'Caveat', cursive";
      dragSampleText.style.fontWeight = "700";
      dragSampleText.style.textTransform = "none";
    } else if (styleObj.id === "neon_glow") {
      dragSampleText.innerHTML = `ELECTRIC <span class="highlight" style="color: #FFFFFF; text-shadow: 0 0 12px #38BDF8;">NEON GLOW</span> CAPTIONS`;
      dragSampleText.style.fontFamily = "'Montserrat', sans-serif";
      dragSampleText.style.fontWeight = "800";
      dragSampleText.style.textTransform = "uppercase";
    } else if (styleObj.id === "minimal_underline") {
      dragSampleText.innerHTML = `Swiss <span class="highlight" style="border-bottom: 2.5px solid var(--accent); padding-bottom: 1px;">Minimal Underline</span>`;
      dragSampleText.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
      dragSampleText.style.fontWeight = "800";
      dragSampleText.style.textTransform = "none";
    } else if (styleObj.id === "pill_word") {
      dragSampleText.innerHTML = `CLEAN <span class="highlight" style="background: var(--accent); color: #0A0A0B; padding: 2px 8px; border-radius: 9999px; text-shadow: none;">SPOKEN PILL</span>`;
      dragSampleText.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
      dragSampleText.style.fontWeight = "800";
      dragSampleText.style.textTransform = "none";
    } else if (styleObj.id === "sticker") {
      dragSampleText.innerHTML = `🏷️ STICKER <span class="highlight" style="color: #22C55E;">BADGE</span> POP`;
      dragSampleText.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
      dragSampleText.style.fontWeight = "800";
      dragSampleText.style.textTransform = "uppercase";
    } else {
      dragSampleText.innerHTML = `CREATING <span class="highlight" style="color: ${selectedHighlightColor};">DYNAMIC CAPTIONS</span> THAT POP`;
      dragSampleText.style.fontFamily = "'Montserrat', 'Plus Jakarta Sans', sans-serif";
      dragSampleText.style.fontWeight = "800";
      dragSampleText.style.textTransform = "uppercase";
    }

    if (selectedBgStyle === "solid") {
      dragSampleText.style.color = "#090a0f";
      dragSampleText.style.textShadow = "none";
    } else {
      dragSampleText.style.color = "#ffffff";
      dragSampleText.style.textShadow = "0 2px 8px rgba(0,0,0,0.95)";
    }
  }

  if (selectAllStylesBtn) {
    selectAllStylesBtn.addEventListener("click", () => {
      selectedStyles = ALL_AVAILABLE_STYLES.map((s) => s.id);
      renderStylesPool();
      updateCaptionShowcase("hormozi_bold");
      showToast("Selected all 24 caption styles.");
    });
  }

  if (clearAllStylesBtn) {
    clearAllStylesBtn.addEventListener("click", () => {
      selectedStyles = ["hormozi_bold"];
      renderStylesPool();
      updateCaptionShowcase("hormozi_bold");
      showToast("Reset to single style: Hormozi Bold.");
    });
  }

  // 1-Click Preset Shortcuts
  if (stylePresetQuickBtns) {
    stylePresetQuickBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const pick = btn.dataset.pick;
        if (pick === "all") {
          selectedStyles = ALL_AVAILABLE_STYLES.map((s) => s.id);
          updateCaptionShowcase("hormozi_bold");
        } else if (pick) {
          selectedStyles = [pick];
          updateCaptionShowcase(pick);
        }
        renderStylesPool();
        showToast(`Preset: ${btn.textContent.trim()}`);
      });
    });
  }

  // High-Level Radio Presets sync
  presetChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      presetChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      const radio = chip.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
        if (radio.value === "minimal_pill") {
          selectedStyles = ["pill_word", "minimal_underline", "highlighter_marker"];
          updateCaptionShowcase("highlighter_marker");
        } else if (radio.value === "calm_serif") {
          selectedStyles = ["cinematic_minimal", "serif_title", "quote_editorial", "blob_card", "minimal_underline"];
          updateCaptionShowcase("cinematic_minimal");
        } else {
          selectedStyles = ALL_AVAILABLE_STYLES.map((s) => s.id);
          updateCaptionShowcase("beast_impact");
        }
        renderStylesPool();
      }
    });
  });

  function getSelectedPreset() {
    const checked = document.querySelector('input[name="preset"]:checked');
    return checked ? checked.value : "bold_creator";
  }

  renderStylesPool();

  // =========================================================================
  // 5. CapCut-Style Dual-Handle Visual Video Trimmer
  // =========================================================================
  let videoTotalDuration = 12.0;
  let trimStartSec = 0.0;
  let trimEndSec = 12.0;
  let isPlayingCut = false;
  let currentDragHandle = null;
  let dragTrackRect = null;
  let windowDragStartSec = 0;
  let windowDragStartEndSec = 0;
  let windowDragStartPct = 0;

  function formatTime(seconds) {
    const s = Math.max(0, seconds);
    const m = Math.floor(s / 60);
    const remSec = (s % 60).toFixed(2);
    return `${m.toString().padStart(2, "0")}:${remSec.padStart(5, "0")}`;
  }

  function initTrimmerDuration(duration) {
    if (!duration || isNaN(duration) || duration <= 0) return;
    videoTotalDuration = duration;
    trimStartSec = 0.0;
    trimEndSec = duration;
    updateTrimmerDisplay();
  }

  function updateTrimmerDisplay() {
    if (videoTotalDuration <= 0) return;
    const startPct = Math.max(0, Math.min(100, (trimStartSec / videoTotalDuration) * 100));
    const endPct = Math.max(0, Math.min(100, (trimEndSec / videoTotalDuration) * 100));
    const widthPct = Math.max(0.5, endPct - startPct);

    if (trimShadeLeft) trimShadeLeft.style.width = `${startPct}%`;
    if (trimWindow) {
      trimWindow.style.left = `${startPct}%`;
      trimWindow.style.width = `${widthPct}%`;
    }
    if (trimShadeRight) {
      trimShadeRight.style.left = `${endPct}%`;
      trimShadeRight.style.width = `${Math.max(0, 100 - endPct)}%`;
    }

    if (trimStartBadge) trimStartBadge.textContent = formatTime(trimStartSec);
    if (trimEndBadge) trimEndBadge.textContent = formatTime(trimEndSec);
    const clipDur = (trimEndSec - trimStartSec).toFixed(1);
    if (trimDurBadge) trimDurBadge.textContent = `Duration: ${clipDur}s`;
    if (trimReadout) {
      trimReadout.textContent = `${clipDur}s Selected (${formatTime(trimStartSec)} - ${formatTime(trimEndSec)})`;
    }

    // Sync hidden form inputs
    if (trimStart) trimStart.value = trimStartSec > 0.05 ? trimStartSec.toFixed(2) : "";
    if (trimEnd) trimEnd.value = trimEndSec < videoTotalDuration - 0.05 ? trimEndSec.toFixed(2) : "";
  }

  // Handle Drag Interactions
  if (trimTrackWrapper) {
    function onPointerDown(e, handleType) {
      currentDragHandle = handleType;
      dragTrackRect = trimTrackWrapper.getBoundingClientRect();
      windowDragStartSec = trimStartSec;
      windowDragStartEndSec = trimEndSec;
      windowDragStartPct = (e.clientX - dragTrackRect.left) / dragTrackRect.width;

      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp);
      e.preventDefault();
      e.stopPropagation();
    }

    if (trimHandleLeft) {
      trimHandleLeft.addEventListener("pointerdown", (e) => onPointerDown(e, "left"));
    }
    if (trimHandleRight) {
      trimHandleRight.addEventListener("pointerdown", (e) => onPointerDown(e, "right"));
    }
    if (trimWindow) {
      trimWindow.addEventListener("pointerdown", (e) => {
        if (e.target !== trimHandleLeft && e.target !== trimHandleRight && !trimHandleLeft.contains(e.target) && !trimHandleRight.contains(e.target)) {
          onPointerDown(e, "window");
        }
      });
    }

    function onPointerMove(e) {
      if (!currentDragHandle || !dragTrackRect) return;
      const x = Math.max(0, Math.min(dragTrackRect.width, e.clientX - dragTrackRect.left));
      const pct = x / dragTrackRect.width;
      const targetSec = pct * videoTotalDuration;

      if (currentDragHandle === "left") {
        trimStartSec = Math.max(0, Math.min(trimEndSec - 0.35, targetSec));
        if (sourceVideoPlayer) {
          sourceVideoPlayer.currentTime = trimStartSec;
        }
      } else if (currentDragHandle === "right") {
        trimEndSec = Math.min(videoTotalDuration, Math.max(trimStartSec + 0.35, targetSec));
        if (sourceVideoPlayer) {
          sourceVideoPlayer.currentTime = trimEndSec;
        }
      } else if (currentDragHandle === "window") {
        const deltaPct = pct - windowDragStartPct;
        const deltaSec = deltaPct * videoTotalDuration;
        const dur = windowDragStartEndSec - windowDragStartSec;

        let newStart = windowDragStartSec + deltaSec;
        let newEnd = newStart + dur;

        if (newStart < 0) {
          newStart = 0;
          newEnd = dur;
        } else if (newEnd > videoTotalDuration) {
          newEnd = videoTotalDuration;
          newStart = videoTotalDuration - dur;
        }

        trimStartSec = Math.max(0, newStart);
        trimEndSec = Math.min(videoTotalDuration, newEnd);
        if (sourceVideoPlayer) {
          sourceVideoPlayer.currentTime = trimStartSec;
        }
      }

      updateTrimmerDisplay();
    }

    function onPointerUp() {
      currentDragHandle = null;
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
    }
  }

  // Play Cut Button (Loop restricted chunk)
  if (btnPlayCut) {
    btnPlayCut.addEventListener("click", () => {
      if (!sourceVideoPlayer || !sourceVideoPlayer.src) {
        showToast("Load a video first to preview cut!");
        return;
      }

      if (isPlayingCut) {
        sourceVideoPlayer.pause();
        isPlayingCut = false;
        if (playCutLabel) playCutLabel.textContent = "Play Cut (Loop)";
        if (playCutIcon) playCutIcon.textContent = "▶";
        btnPlayCut.classList.remove("playing");
      } else {
        sourceVideoPlayer.currentTime = trimStartSec;
        sourceVideoPlayer.play();
        isPlayingCut = true;
        if (playCutLabel) playCutLabel.textContent = "Pause Cut";
        if (playCutIcon) playCutIcon.textContent = "⏸";
        btnPlayCut.classList.add("playing");
        if (trimPlayhead) trimPlayhead.classList.remove("hidden");
      }
    });

    sourceVideoPlayer.addEventListener("timeupdate", () => {
      if (videoTotalDuration <= 0) return;
      const cur = sourceVideoPlayer.currentTime;

      if (trimPlayhead) {
        const pct = (cur / videoTotalDuration) * 100;
        trimPlayhead.style.left = `${pct}%`;
      }

      if (canvasProgressBarFill) {
        const dur = videoTotalDuration > 0 ? videoTotalDuration : (sourceVideoPlayer.duration || 1);
        if (dur > 0) {
          const pct = (cur / dur) * 100;
          canvasProgressBarFill.style.width = `${Math.min(100, Math.max(0, pct))}%`;
        }
      }

      if (selectedHeadlineHookEnabled && canvasHeadlineHook) {
        if (selectedHeadlineDuration !== null && cur > selectedHeadlineDuration) {
          canvasHeadlineHook.style.opacity = "0";
          canvasHeadlineHook.style.transition = "opacity 0.4s ease";
        } else {
          canvasHeadlineHook.style.opacity = "1";
        }
      }

      if (isPlayingCut) {
        if (cur >= trimEndSec || cur < trimStartSec - 0.2) {
          sourceVideoPlayer.currentTime = trimStartSec;
        }
      }
    });

    sourceVideoPlayer.addEventListener("pause", () => {
      if (isPlayingCut) {
        isPlayingCut = false;
        if (playCutLabel) playCutLabel.textContent = "Play Cut (Loop)";
        if (playCutIcon) playCutIcon.textContent = "▶";
        btnPlayCut.classList.remove("playing");
      }
    });
  }

  // Preset Buttons for Trimming & AI Viral Clips
  if (trim15sBtn) {
    trim15sBtn.addEventListener("click", () => {
      setClipLength("15s");
      fetchViralClips("15s");
    });
  }
  if (trim30sBtn) {
    trim30sBtn.addEventListener("click", () => {
      setClipLength("30s");
      fetchViralClips("30s");
    });
  }
  if (trim60sBtn) {
    trim60sBtn.addEventListener("click", () => {
      setClipLength("60s");
      fetchViralClips("60s");
    });
  }
  if (trimResetBtn) {
    trimResetBtn.addEventListener("click", () => {
      trimStartSec = 0.0;
      trimEndSec = videoTotalDuration;
      updateTrimmerDisplay();
      if (sourceVideoPlayer) sourceVideoPlayer.currentTime = 0;
      if (viralClipsList) {
        viralClipsList.querySelectorAll(".viral-clip-card").forEach(c => c.classList.remove("active"));
      }
      showToast("Reset to full video");
    });
  }

  function setClipLength(len) {
    selectedClipLength = len;
    if (clipLengthChips) {
      clipLengthChips.forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.length === len);
      });
    }
  }

  if (clipLengthChips) {
    clipLengthChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        setClipLength(btn.dataset.length || "30s");
        fetchViralClips(selectedClipLength);
      });
    });
  }

  if (btnFindViralClips) {
    btnFindViralClips.addEventListener("click", () => {
      fetchViralClips(selectedClipLength);
    });
  }

  async function fetchViralClips(targetLen) {
    const len = targetLen || selectedClipLength || "30s";
    setClipLength(len);

    if (!selectedFile && !currentJobId) {
      showToast("Please upload a video or click Sample Video first!");
      return;
    }

    if (btnFindViralClips) btnFindViralClips.disabled = true;
    if (findClipsBtnIcon) findClipsBtnIcon.textContent = "⏳";
    if (findClipsBtnText) findClipsBtnText.textContent = "Scanning...";
    showToast(`🤖 AI scanning video for ${len} viral moments...`);

    try {
      let data;
      if (currentJobId) {
        const res = await fetch(`/api/jobs/${currentJobId}/find-clips?target_length=${encodeURIComponent(len)}`, {
          method: "POST",
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Failed to find clips");
        }
        data = await res.json();
      } else {
        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("target_length", len);
        if (llmProvider && llmProvider.value) {
          formData.append("llm_provider", llmProvider.value);
        }
        const res = await fetch("/api/clips/discover", {
          method: "POST",
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Failed to analyze clips");
        }
        data = await res.json();
      }

      const clips = data.clips || [];
      activeViralClips = clips;
      renderViralClips(clips);

      if (clips.length > 0) {
        applyViralClip(clips[0]);
        showToast(`✨ Found ${clips.length} viral clips! Top: "${clips[0].headline}"`);
      } else {
        showToast("No distinct clips found matching length.");
      }
    } catch (err) {
      console.error("AI Clip Extraction Error:", err);
      showToast(`AI Clip Finder: ${err.message}`);
    } finally {
      if (btnFindViralClips) btnFindViralClips.disabled = false;
      if (findClipsBtnIcon) findClipsBtnIcon.textContent = "✨";
      if (findClipsBtnText) findClipsBtnText.textContent = "Find Clips";
    }
  }

  function renderViralClips(clips) {
    if (!viralClipsList) return;
    if (viralClipsActions) {
      if (clips && clips.length > 0) viralClipsActions.classList.remove("hidden");
      else viralClipsActions.classList.add("hidden");
    }

    if (!clips || clips.length === 0) {
      viralClipsList.innerHTML = `<div style="padding: 10px; font-size: 11px; color: var(--text-dim); text-align: center;">No viral clips found for this length.</div>`;
      viralClipsList.classList.remove("hidden");
      return;
    }

    viralClipsList.innerHTML = clips.map((clip, idx) => `
      <div class="viral-clip-card ${idx === 0 ? "active" : ""}" data-clip-id="${clip.id}">
        <div class="viral-clip-header">
          <span class="viral-clip-headline">${clip.headline}</span>
          <span class="viral-clip-score">🔥 ${clip.virality_score ? clip.virality_score.toFixed(1) : "8.5"}/10</span>
        </div>
        <div class="viral-clip-meta">
          <span class="viral-clip-time">⏱️ ${formatTime(clip.start)} - ${formatTime(clip.end)} (${clip.duration.toFixed(1)}s)</span>
          <span class="badge" style="font-size: 9px; text-transform: uppercase; background: rgba(255,255,255,0.06);">${clip.target_length}</span>
        </div>
        <div class="viral-clip-summary">${clip.summary || "Key discussion excerpt"}</div>
        <div class="viral-clip-footer">
          <button type="button" class="btn-copy-post" data-clip-idx="${idx}" title="Copy viral hook, caption, and hashtags for TikTok / Reels">
            📋 Copy Post
          </button>
        </div>
      </div>
    `).join("");

    viralClipsList.classList.remove("hidden");

    // Click on clip card applies clip to player & trimmer
    const cards = viralClipsList.querySelectorAll(".viral-clip-card");
    cards.forEach((card, idx) => {
      card.addEventListener("click", () => {
        cards.forEach((c) => c.classList.remove("active"));
        card.classList.add("active");
        applyViralClip(clips[idx]);
      });
    });

    // Wire Copy Post button (Feature #4: Social Media Copy & Hashtag Generator)
    viralClipsList.querySelectorAll(".btn-copy-post").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation(); // Don't trigger card selection
        const idx = parseInt(btn.dataset.clipIdx, 10);
        const clip = clips[idx];
        if (!clip) return;
        const post = clip.social_post;
        let textToCopy = "";
        if (post) {
          textToCopy = `${post.hook}\n\n${post.caption}\n\n${(post.hashtags || []).join(" ")}`;
        } else {
          textToCopy = `${clip.headline}\n\n${clip.summary || "Watch till the end!"}\n\n#reels #viral #podcast #shorts`;
        }
        navigator.clipboard.writeText(textToCopy).then(() => {
          const oldText = btn.textContent;
          btn.textContent = "✅ Copied!";
          showToast("📋 Social media post copy & hashtags copied to clipboard!");
          setTimeout(() => { btn.textContent = oldText; }, 2000);
        }).catch(() => {
          showToast("Could not copy to clipboard");
        });
      });
    });
  }

  // Feature #1: Batch Multi-Clip Export to ZIP
  if (btnBatchExportZip) {
    btnBatchExportZip.addEventListener("click", async () => {
      if (!currentJobId) {
        showToast("Please process a video first before batch exporting clips!");
        return;
      }
      if (btnBatchExportZip.disabled) return;
      btnBatchExportZip.disabled = true;
      if (batchZipIcon) batchZipIcon.textContent = "⏳";
      if (batchZipLabel) batchZipLabel.textContent = "Rendering ZIP...";
      showToast("📦 Batch rendering all clips into MP4s and building ZIP...");

      try {
        const res = await fetch(`/api/jobs/${currentJobId}/batch-render-clips`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ clips: activeViralClips || [] }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Batch render failed");
        }
        const data = await res.json();
        showToast(`🎉 Rendered ${data.clips_count} reels! Downloading ZIP...`);

        // Trigger ZIP download
        const downloadLink = document.createElement("a");
        downloadLink.href = data.zip_url;
        downloadLink.download = data.filename || `${currentJobId}_viral_reels.zip`;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
      } catch (err) {
        console.error("Batch Export ZIP Error:", err);
        showToast(`Batch Export Error: ${err.message}`);
      } finally {
        btnBatchExportZip.disabled = false;
        if (batchZipIcon) batchZipIcon.textContent = "📦";
        if (batchZipLabel) batchZipLabel.textContent = "Export All Clips (.ZIP)";
      }
    });
  }

  let activeSelectedClip = null;

  // ── Mode Switcher Tab Logic ──
  function switchStudioMode(mode) {
    const isClips = (mode === "clips");
    if (tabFullStudio) tabFullStudio.classList.toggle("active", !isClips);
    if (tabClipsStudio) tabClipsStudio.classList.toggle("active", isClips);
    if (fullStudioSection) fullStudioSection.classList.toggle("hidden", isClips);
    if (clipsStudioSection) clipsStudioSection.classList.toggle("hidden", !isClips);

    if (isClips) {
      if (!selectedFile && !currentJobId) {
        showToast("Drop or load a video to start discovering viral reels!");
      } else {
        showToast("✨ AI Viral Reels Studio active");
      }
    } else {
      showToast("🎞️ Full Video Studio active");
    }
  }

  if (tabFullStudio) {
    tabFullStudio.addEventListener("click", () => switchStudioMode("full"));
  }
  if (tabClipsStudio) {
    tabClipsStudio.addEventListener("click", () => switchStudioMode("clips"));
  }
  if (btnSwitchToClips) {
    btnSwitchToClips.addEventListener("click", () => switchStudioMode("clips"));
  }

  function applyViralClip(clip) {
    if (!clip) return;
    activeSelectedClip = clip;
    trimStartSec = clip.start;
    trimEndSec = clip.end;
    updateTrimmerDisplay();

    if (sourceVideoPlayer) {
      sourceVideoPlayer.currentTime = clip.start;
      sourceVideoPlayer.play().catch(() => {});
    }

    selectedHeadlineHookText = clip.headline;
    if (headlineHookInput) headlineHookInput.value = clip.headline;
    selectedHeadlineHookEnabled = true;
    if (headlineHookToggle) headlineHookToggle.checked = true;
    if (headlineHookSettings) headlineHookSettings.classList.remove("hidden");
    updateHeadlineHookPreview();

    // Populate and display Dedicated Clip Tweaker Card
    if (clipTweakerCard) {
      clipTweakerCard.classList.remove("hidden");
    }
    if (tweakerClipTitle) {
      tweakerClipTitle.textContent = `"${clip.headline}"`;
      tweakerClipTitle.title = clip.headline;
    }
    if (tweakerClipTiming) {
      tweakerClipTiming.textContent = `${formatTime(clip.start)} - ${formatTime(clip.end)} (${clip.duration.toFixed(1)}s)`;
    }
    if (clipHeadlineInput) {
      clipHeadlineInput.value = clip.headline;
    }
    selectedHeadlinePosRatio = 0.08;
    if (clipHeadlinePosSlider) clipHeadlinePosSlider.value = 8;
    if (clipHeadlinePosLabel) clipHeadlinePosLabel.textContent = "Top 8% Safe Zone";
    if (clipHeadlinePosChips) {
      clipHeadlinePosChips.forEach((b) => b.classList.toggle("active", b.dataset.pos === "0.08"));
    }
    if (clipWatermarkInput && watermarkInput) {
      clipWatermarkInput.value = watermarkInput.value || "@antigravity";
    }
    if (clipWatermarkToggle) {
      clipWatermarkToggle.checked = false; // Optional by default
    }
    if (clipWatermarkInputContainer) {
      clipWatermarkInputContainer.classList.add("hidden");
    }
    if (clipWatermarkBadge) {
      clipWatermarkBadge.textContent = "Disabled";
    }
    selectedStyles = ["ai_auto"];
    if (clipStyleLabel) clipStyleLabel.textContent = "AI Smart Director";
    if (clipStyleAiNotice) clipStyleAiNotice.classList.remove("hidden");
    if (clipStyleChips) {
      clipStyleChips.forEach((b) => b.classList.toggle("active", b.dataset.stylePick === "ai_auto"));
    }
    if (clipFontSizeLabel) {
      clipFontSizeLabel.textContent = `${captionSizeSlider ? captionSizeSlider.value : 52}px (${selectedCaptionSize})`;
    }
    if (clipFontSizeSlider && captionSizeSlider) {
      clipFontSizeSlider.value = captionSizeSlider.value;
    }
    if (clipPosSlider && subPosSlider) {
      clipPosSlider.value = subPosSlider.value;
    }
    if (clipPosLabel) {
      clipPosLabel.textContent = subPosLabel ? subPosLabel.textContent : "Bottom (79% Safe Zone)";
    }

    const clipLayoutDescriptions = {
      split_podcast: "👥 Podcast Split Stack keeps both host and guest in frame simultaneously — ideal for 16:9 podcast interviews.",
      active_speaker: "⚡ Active Speaker cuts dynamically between speakers with broadcast pacing.",
      blur_fit: "✨ Ambient Blur fits the full 16:9 video over a frosted mirror backdrop — zero cropping.",
      fill: "📱 Center Zoom crops the center 9:16 window for vertical feeds.",
      focus_left: "👈 Left Focus locks onto the left side of the 16:9 frame (host seat).",
      focus_right: "👉 Right Focus locks onto the right side of the 16:9 frame (guest seat).",
    };
    const clipLayoutNames = {
      split_podcast: "Podcast Split Stack",
      active_speaker: "Active Speaker (Auto-Cut)",
      blur_fit: "Ambient Blur (16:9)",
      fill: "Center Zoom (Fill)",
      focus_left: "Left Host Focus",
      focus_right: "Right Guest Focus",
    };

    // Initialize layout for this clip (default to split_podcast or active layout)
    selectedClipLayout = selectedVideoLayout || "split_podcast";
    if (clipLayoutChips) {
      clipLayoutChips.forEach((b) => b.classList.toggle("active", b.dataset.layout === selectedClipLayout));
    }
    if (clipLayoutLabel) {
      clipLayoutLabel.textContent = clipLayoutNames[selectedClipLayout] || selectedClipLayout;
    }
    if (clipLayoutDescNotice) {
      clipLayoutDescNotice.innerHTML = `<span>${clipLayoutDescriptions[selectedClipLayout] || ""}</span>`;
    }
    if (clipAiEnhanceToggle) {
      clipAiEnhanceToggle.checked = aiEnhanceToggle ? aiEnhanceToggle.checked : true;
    }
    if (clipAiEnhanceBadge) {
      clipAiEnhanceBadge.textContent = (clipAiEnhanceToggle && clipAiEnhanceToggle.checked) ? "Active" : "Disabled";
    }
    updateSourceSplitPreview();

    // Update status badge on studio monitor cleanly
    const shortHeadline = clip.headline.length > 20 ? clip.headline.slice(0, 18) + "..." : clip.headline;
    if (stageStatus) {
      stageStatus.textContent = `Clip: ${shortHeadline}`;
      stageStatus.title = clip.headline;
    }

    showToast(`🎯 Selected: "${clip.headline}" — Ready to tweak below!`);
  }

  // ── Dedicated Clip Tweaker Event Listeners ──
  if (clipHeadlineInput) {
    clipHeadlineInput.addEventListener("input", (e) => {
      const val = e.target.value.trim();
      selectedHeadlineHookText = val;
      if (headlineHookInput) headlineHookInput.value = val;
      if (activeSelectedClip) activeSelectedClip.headline = val;
      if (tweakerClipTitle) tweakerClipTitle.textContent = val ? `"${val}"` : `"Untitled Clip"`;
      updateHeadlineHookPreview();
    });
  }

  if (clipHeadlineStyleChips) {
    clipHeadlineStyleChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        clipHeadlineStyleChips.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        selectedHeadlineHookStyle = btn.dataset.style || "badge";
        if (headlineStyleChips) {
          headlineStyleChips.forEach((b) => b.classList.toggle("active", b.dataset.style === selectedHeadlineHookStyle));
        }
        if (tweakerHeadlineStyleBadge) {
          tweakerHeadlineStyleBadge.textContent = `${btn.querySelector(".chip-label").textContent} Style`;
        }
        updateHeadlineHookPreview();
      });
    });
  }

  if (clipHeadlineDurationChips) {
    clipHeadlineDurationChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        clipHeadlineDurationChips.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const dur = btn.dataset.duration;
        selectedHeadlineDuration = dur === "full" ? null : parseFloat(dur);
        if (headlineDurationChips) {
          headlineDurationChips.forEach((b) => b.classList.toggle("active", b.dataset.duration === dur));
        }
        showToast(`Headline duration: ${btn.querySelector(".chip-label").textContent}`);
      });
    });
  }

  if (clipStyleChips) {
    clipStyleChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        clipStyleChips.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const stylePick = btn.dataset.stylePick;
        if (stylePick === "ai_auto") {
          selectedStyles = ["ai_auto"];
          if (clipStyleLabel) clipStyleLabel.textContent = "AI Smart Director";
          if (clipStyleAiNotice) clipStyleAiNotice.classList.remove("hidden");
          if (draggableCaptionBox) {
            draggableCaptionBox.className = `draggable-caption-box style-beast_impact size-${selectedCaptionSize}`;
          }
          showToast("🤖 AI Smart Director: Tone-matched dynamic styles");
        } else {
          selectedStyles = [stylePick];
          if (clipStyleLabel) clipStyleLabel.textContent = btn.textContent;
          if (clipStyleAiNotice) clipStyleAiNotice.classList.add("hidden");
          if (draggableCaptionBox) {
            draggableCaptionBox.className = `draggable-caption-box style-${stylePick} size-${selectedCaptionSize}`;
          }
          if (typeof updateCaptionShowcase === "function") updateCaptionShowcase();
          showToast(`Active Style: ${btn.textContent}`);
        }
      });
    });
  }

  if (clipHeadlinePosChips) {
    clipHeadlinePosChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        clipHeadlinePosChips.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        selectedHeadlinePosRatio = parseFloat(btn.dataset.pos) || 0.08;
        if (clipHeadlinePosSlider) clipHeadlinePosSlider.value = Math.round(selectedHeadlinePosRatio * 100);
        if (clipHeadlinePosLabel) clipHeadlinePosLabel.textContent = `${btn.querySelector(".chip-label").textContent} (${Math.round(selectedHeadlinePosRatio * 100)}%)`;
        updateHeadlineHookPreview();
      });
    });
  }

  if (clipHeadlinePosSlider) {
    clipHeadlinePosSlider.addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10);
      selectedHeadlinePosRatio = val / 100.0;
      if (clipHeadlinePosLabel) clipHeadlinePosLabel.textContent = `${val}% on Screen`;
      if (clipHeadlinePosChips) {
        clipHeadlinePosChips.forEach((b) => b.classList.toggle("active", Math.abs(parseFloat(b.dataset.pos) * 100 - val) < 5));
      }
      updateHeadlineHookPreview();
    });
  }

  if (clipHighlightColorSwatches) {
    clipHighlightColorSwatches.forEach((btn) => {
      btn.addEventListener("click", () => {
        clipHighlightColorSwatches.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        selectedHighlightColor = btn.dataset.color || "#38BDF8";
        const mainSwatches = document.querySelectorAll("#highlightColorSwatches .btn-color-swatch");
        if (mainSwatches) {
          mainSwatches.forEach((b) => b.classList.toggle("active", b.dataset.color === selectedHighlightColor));
        }
        const canvasHighlight = document.querySelector("#draggableCaptionBox .highlight");
        if (canvasHighlight) canvasHighlight.style.color = selectedHighlightColor;
        if (typeof updateCaptionShowcase === "function") updateCaptionShowcase();
        showToast(`Accent Color: ${selectedHighlightColor}`);
      });
    });
  }

  if (clipWatermarkInput) {
    clipWatermarkInput.addEventListener("input", (e) => {
      const val = e.target.value.trim();
      if (watermarkInput) watermarkInput.value = val;
      if (clipWatermarkToggle && clipWatermarkToggle.checked) {
        if (clipWatermarkBadge) clipWatermarkBadge.textContent = val || "@handle";
      }
      updateWatermarkPreview();
    });
  }

  if (watermarkToggle) {
    watermarkToggle.addEventListener("change", (e) => {
      if (watermarkInputContainer) {
        watermarkInputContainer.classList.toggle("hidden", !e.target.checked);
      }
      updateWatermarkPreview();
      showToast(e.target.checked ? "Brand Watermark: Enabled" : "Brand Watermark: Disabled");
    });
  }

  if (clipWatermarkToggle) {
    clipWatermarkToggle.addEventListener("change", (e) => {
      const isChecked = e.target.checked;
      if (clipWatermarkInputContainer) {
        clipWatermarkInputContainer.classList.toggle("hidden", !isChecked);
      }
      if (clipWatermarkBadge) {
        clipWatermarkBadge.textContent = isChecked ? (clipWatermarkInput ? clipWatermarkInput.value.trim() || "@handle" : "@handle") : "Disabled";
      }
      updateWatermarkPreview();
      showToast(isChecked ? "Creator Watermark: Enabled" : "Creator Watermark: Disabled");
    });
  }

  const clipLayoutDescriptionsGlobal = {
    split_podcast: "👥 Podcast Split Stack keeps both host and guest in frame simultaneously — ideal for 16:9 podcast interviews.",
    active_speaker: "⚡ Active Speaker cuts dynamically between speakers with broadcast pacing.",
    blur_fit: "✨ Ambient Blur fits the full 16:9 video over a frosted mirror backdrop — zero cropping.",
    fill: "📱 Center Zoom crops the center 9:16 window for vertical feeds.",
    focus_left: "👈 Left Focus locks onto the left side of the 16:9 frame (host seat).",
    focus_right: "👉 Right Focus locks onto the right side of the 16:9 frame (guest seat).",
  };
  const clipLayoutNamesGlobal = {
    split_podcast: "Podcast Split Stack",
    active_speaker: "Active Speaker (Auto-Cut)",
    blur_fit: "Ambient Blur (16:9)",
    fill: "Center Zoom (Fill)",
    focus_left: "Left Host Focus",
    focus_right: "Right Guest Focus",
  };

  if (clipLayoutChips) {
    clipLayoutChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        clipLayoutChips.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        selectedClipLayout = btn.dataset.layout || "split_podcast";
        selectedVideoLayout = selectedClipLayout;
        if (clipLayoutLabel) {
          clipLayoutLabel.textContent = clipLayoutNamesGlobal[selectedClipLayout] || selectedClipLayout;
        }
        if (clipLayoutDescNotice) {
          clipLayoutDescNotice.innerHTML = `<span>${clipLayoutDescriptionsGlobal[selectedClipLayout] || ""}</span>`;
        }
        if (allLayoutCards) {
          allLayoutCards.forEach((card) => card.classList.toggle("active", card.dataset.layout === selectedClipLayout));
        }
        if (layoutSelectedLabel) {
          layoutSelectedLabel.textContent = clipLayoutNamesGlobal[selectedClipLayout] || selectedClipLayout;
        }
        updateSourceSplitPreview();
        showToast(`Layout: ${clipLayoutNamesGlobal[selectedClipLayout] || selectedClipLayout}`);
      });
    });
  }

  if (clipAiEnhanceToggle) {
    clipAiEnhanceToggle.addEventListener("change", (e) => {
      const isChecked = e.target.checked;
      if (clipAiEnhanceBadge) {
        clipAiEnhanceBadge.textContent = isChecked ? "Active" : "Disabled";
      }
      if (aiEnhanceToggle) {
        aiEnhanceToggle.checked = isChecked;
      }
      showToast(isChecked ? "🎬 Scene-Aware Vision: Enabled" : "🎬 Scene-Aware Vision: Disabled");
    });
  }

  if (btnPlayActiveClip) {
    btnPlayActiveClip.addEventListener("click", () => {
      if (!activeSelectedClip || !sourceVideoPlayer) return;
      sourceVideoPlayer.currentTime = activeSelectedClip.start;
      sourceVideoPlayer.play().catch(() => {});
      showToast(`▶ Playing clip from ${formatTime(activeSelectedClip.start)}`);
    });
  }

  if (btnBatchExportZipDedicated && btnBatchExportZip) {
    btnBatchExportZipDedicated.addEventListener("click", () => {
      btnBatchExportZip.click();
    });
  }

  updateTrimmerDisplay();

  // Calibrate Trimmer when video metadata is loaded
  sourceVideoPlayer.addEventListener("loadedmetadata", () => {
    if (sourceVideoPlayer.duration && !isNaN(sourceVideoPlayer.duration)) {
      initTrimmerDuration(sourceVideoPlayer.duration);
    }
  });

  // =========================================================================
  // 5b. Drag-and-Drop Caption Placement on Video Canvas
  // =========================================================================
  let currentSubtitleY = 0.79; // Default 79% lower safe zone
  let isDraggingCaption = false;

  function setSubtitlePosition(posFract, trigger = "manual") {
    const clamped = Math.max(0.10, Math.min(0.88, posFract));
    currentSubtitleY = clamped;
    const pct = Math.round(clamped * 100);

    if (draggableCaptionBox) {
      draggableCaptionBox.style.top = `${clamped * 100}%`;
    }
    if (dragCoordBadge) {
      dragCoordBadge.textContent = `Y: ${pct}%`;
    }
    if (subPosSlider) {
      subPosSlider.value = pct;
    }
    if (clipPosSlider) {
      clipPosSlider.value = pct;
    }

    // Guideline highlights
    const isNearUpper = Math.abs(clamped - 0.18) < 0.025;
    const isNearCenter = Math.abs(clamped - 0.50) < 0.025;
    const isNearLower = Math.abs(clamped - 0.79) < 0.025;

    if (snapGuideUpper) snapGuideUpper.classList.toggle("highlight", isNearUpper);
    if (snapGuideCenter) snapGuideCenter.classList.toggle("highlight", isNearCenter);
    if (snapGuideLower) snapGuideLower.classList.toggle("highlight", isNearLower);

    // Update quick chips active state across both panels
    if (subPosQuickChips) {
      subPosQuickChips.forEach((btn) => {
        const p = btn.dataset.pos;
        btn.classList.toggle("active", (p === "upper" && isNearUpper) || (p === "center" && isNearCenter) || (p === "lower" && isNearLower));
      });
    }
    if (clipPosChips) {
      clipPosChips.forEach((btn) => {
        const p = btn.dataset.pos;
        btn.classList.toggle("active", (p === "upper" && isNearUpper) || (p === "center" && isNearCenter) || (p === "lower" && isNearLower));
      });
    }

    // Update label text
    const labelText = isNearUpper
      ? "Top (18% Safe Zone)"
      : isNearCenter
      ? "Center (50% Mid-Screen)"
      : isNearLower
      ? "Bottom (79% Safe Zone)"
      : `Custom (${pct}% Y Position)`;

    if (subPosLabel) subPosLabel.textContent = labelText;
    if (clipPosLabel) clipPosLabel.textContent = labelText;

    if (subPosition) {
      if (isNearUpper) subPosition.value = "upper";
      else if (isNearCenter) subPosition.value = "center";
      else subPosition.value = "lower";
    }
  }

  // Mouse & Touch Drag on Canvas Overlay
  if (draggableCaptionBox && phoneCanvas) {
    draggableCaptionBox.addEventListener("pointerdown", (e) => {
      isDraggingCaption = true;
      draggableCaptionBox.classList.add("dragging");
      try { draggableCaptionBox.setPointerCapture(e.pointerId); } catch {}
      e.preventDefault();
    });

    draggableCaptionBox.addEventListener("pointermove", (e) => {
      if (!isDraggingCaption) return;
      const rect = phoneCanvas.getBoundingClientRect();
      if (rect.height <= 0) return;

      let newY = (e.clientY - rect.top) / rect.height;

      // Smart magnetic snap to Safe Zones
      if (Math.abs(newY - 0.18) < 0.035) newY = 0.18;
      else if (Math.abs(newY - 0.50) < 0.035) newY = 0.50;
      else if (Math.abs(newY - 0.79) < 0.035) newY = 0.79;

      setSubtitlePosition(newY, "drag");
    });

    draggableCaptionBox.addEventListener("pointerup", (e) => {
      if (!isDraggingCaption) return;
      isDraggingCaption = false;
      draggableCaptionBox.classList.remove("dragging");
      try { draggableCaptionBox.releasePointerCapture(e.pointerId); } catch {}
      showToast(`Caption anchored at Y: ${Math.round(currentSubtitleY * 100)}%`);
    });
  }

  // Position Slider Sync
  if (subPosSlider) {
    subPosSlider.addEventListener("input", (e) => {
      setSubtitlePosition(parseFloat(e.target.value) / 100, "slider");
    });
  }

  if (clipPosSlider) {
    clipPosSlider.addEventListener("input", (e) => {
      setSubtitlePosition(parseFloat(e.target.value) / 100, "slider");
    });
  }

  // Quick Preset Chips Sync
  if (subPosQuickChips) {
    subPosQuickChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        const p = btn.dataset.pos;
        if (p === "upper") setSubtitlePosition(0.18, "preset");
        else if (p === "center") setSubtitlePosition(0.50, "preset");
        else setSubtitlePosition(0.79, "preset");
        showToast(`Position: ${btn.querySelector(".chip-label").textContent}`);
      });
    });
  }

  if (clipPosChips) {
    clipPosChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        const p = btn.dataset.pos;
        if (p === "upper") setSubtitlePosition(0.18, "preset");
        else if (p === "center") setSubtitlePosition(0.50, "preset");
        else setSubtitlePosition(0.79, "preset");
        showToast(`Position: ${btn.querySelector(".chip-label").textContent}`);
      });
    });
  }

  setSubtitlePosition(0.79);

  // =========================================================================
  // Viral Boosters & Retention Live Controls & Canvas Overlay Sync
  // =========================================================================
  function updateHeadlineHookPreview() {
    if (canvasHeadlineHook) {
      canvasHeadlineHook.style.top = `${Math.round(selectedHeadlinePosRatio * 1000) / 10}%`;
    }
    if (selectedHeadlineHookEnabled && selectedHeadlineHookText.trim().length > 0) {
      if (canvasHeadlineHook) canvasHeadlineHook.classList.remove("hidden");
      if (headlineHookSettings) headlineHookSettings.classList.remove("hidden");
      if (headlineHookStateBadge) {
        headlineHookStateBadge.textContent = "ON";
        headlineHookStateBadge.style.background = "rgba(34, 197, 94, 0.15)";
        headlineHookStateBadge.style.color = "#22c55e";
      }
      if (canvasHeadlineHookInner) {
        canvasHeadlineHookInner.textContent = selectedHeadlineHookText;
        if (selectedHeadlineHookStyle === "badge") {
          canvasHeadlineHookInner.style.background = "linear-gradient(135deg, rgba(20, 20, 26, 0.94), rgba(10, 10, 15, 0.98))";
          canvasHeadlineHookInner.style.border = "2px solid #F59E0B";
          canvasHeadlineHookInner.style.borderRadius = "9999px";
          canvasHeadlineHookInner.style.boxShadow = "0 10px 25px rgba(0,0,0,0.7), 0 0 20px rgba(245, 158, 11, 0.35)";
          canvasHeadlineHookInner.style.color = "#FFFFFF";
          canvasHeadlineHookInner.style.fontFamily = "'Inter', sans-serif";
          canvasHeadlineHookInner.style.fontWeight = "900";
          canvasHeadlineHookInner.style.fontSize = "13px";
          canvasHeadlineHookInner.style.letterSpacing = "0.5px";
          canvasHeadlineHookInner.style.padding = "6px 16px";
          canvasHeadlineHookInner.style.textTransform = "uppercase";
        } else if (selectedHeadlineHookStyle === "glass") {
          canvasHeadlineHookInner.style.background = "rgba(255, 255, 255, 0.15)";
          canvasHeadlineHookInner.style.backdropFilter = "blur(16px)";
          canvasHeadlineHookInner.style.webkitBackdropFilter = "blur(16px)";
          canvasHeadlineHookInner.style.border = "1px solid rgba(255, 255, 255, 0.3)";
          canvasHeadlineHookInner.style.borderRadius = "12px";
          canvasHeadlineHookInner.style.boxShadow = "0 10px 25px rgba(0,0,0,0.5)";
          canvasHeadlineHookInner.style.color = "#FFFFFF";
          canvasHeadlineHookInner.style.fontFamily = "'Inter', sans-serif";
          canvasHeadlineHookInner.style.fontWeight = "800";
          canvasHeadlineHookInner.style.fontSize = "13px";
          canvasHeadlineHookInner.style.letterSpacing = "0px";
          canvasHeadlineHookInner.style.padding = "6px 16px";
          canvasHeadlineHookInner.style.textTransform = "none";
        } else if (selectedHeadlineHookStyle === "clean") {
          canvasHeadlineHookInner.style.background = "#FFFFFF";
          canvasHeadlineHookInner.style.border = "2px solid #000000";
          canvasHeadlineHookInner.style.borderRadius = "8px";
          canvasHeadlineHookInner.style.boxShadow = "0 8px 20px rgba(0,0,0,0.7)";
          canvasHeadlineHookInner.style.color = "#0A0A0C";
          canvasHeadlineHookInner.style.fontFamily = "'Inter', sans-serif";
          canvasHeadlineHookInner.style.fontWeight = "900";
          canvasHeadlineHookInner.style.fontSize = "13px";
          canvasHeadlineHookInner.style.letterSpacing = "-0.3px";
          canvasHeadlineHookInner.style.padding = "6px 16px";
          canvasHeadlineHookInner.style.textTransform = "none";
        } else if (selectedHeadlineHookStyle === "cyber") {
          canvasHeadlineHookInner.style.background = "rgba(10, 10, 24, 0.94)";
          canvasHeadlineHookInner.style.border = "2px solid #00F0FF";
          canvasHeadlineHookInner.style.borderRadius = "6px";
          canvasHeadlineHookInner.style.boxShadow = "0 0 20px rgba(0, 240, 255, 0.4)";
          canvasHeadlineHookInner.style.color = "#00F0FF";
          canvasHeadlineHookInner.style.fontFamily = "'JetBrains Mono', monospace";
          canvasHeadlineHookInner.style.fontWeight = "900";
          canvasHeadlineHookInner.style.fontSize = "12px";
          canvasHeadlineHookInner.style.letterSpacing = "1.5px";
          canvasHeadlineHookInner.style.padding = "6px 16px";
          canvasHeadlineHookInner.style.textTransform = "uppercase";
        }
      }
    } else {
      if (canvasHeadlineHook) canvasHeadlineHook.classList.add("hidden");
      if (headlineHookSettings) headlineHookSettings.classList.add("hidden");
      if (headlineHookStateBadge) {
        headlineHookStateBadge.textContent = "OFF";
        headlineHookStateBadge.style.background = "rgba(255,255,255,0.06)";
        headlineHookStateBadge.style.color = "var(--text-dim)";
      }
    }
  }

  function updateProgressBarPreview() {
    if (!canvasProgressBar) return;
    if (selectedProgressBar) {
      canvasProgressBar.classList.remove("hidden");
      if (selectedProgressBarPos === "top") {
        canvasProgressBar.style.top = "0";
        canvasProgressBar.style.bottom = "auto";
      } else {
        canvasProgressBar.style.bottom = "0";
        canvasProgressBar.style.top = "auto";
      }
      if (canvasProgressBarFill) {
        canvasProgressBarFill.style.background = `linear-gradient(90deg, ${selectedHighlightColor}, #ec4899, #FBBF24)`;
        canvasProgressBarFill.style.boxShadow = `0 0 10px ${selectedHighlightColor}`;
      }
    } else {
      canvasProgressBar.classList.add("hidden");
    }
  }

  if (headlineHookToggle) {
    headlineHookToggle.addEventListener("change", (e) => {
      selectedHeadlineHookEnabled = e.target.checked;
      updateHeadlineHookPreview();
      showToast(selectedHeadlineHookEnabled ? "Top Headline Hook Card: Enabled" : "Top Headline Hook Card: Disabled");
    });
  }

  if (headlineHookInput) {
    headlineHookInput.addEventListener("input", (e) => {
      selectedHeadlineHookText = e.target.value;
      updateHeadlineHookPreview();
    });
  }

  if (headlineStyleChips) {
    headlineStyleChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        headlineStyleChips.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        selectedHeadlineHookStyle = btn.dataset.style || "badge";
        updateHeadlineHookPreview();
        const lbl = btn.querySelector(".chip-label");
        showToast(`Hook Style: ${lbl ? lbl.textContent : selectedHeadlineHookStyle}`);
      });
    });
  }

  if (headlineDurationChips) {
    headlineDurationChips.forEach((btn) => {
      btn.addEventListener("click", () => {
        headlineDurationChips.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const dur = btn.dataset.duration;
        if (dur === "5") {
          selectedHeadlineDuration = 5.0;
          if (headlineDurationInput) headlineDurationInput.value = "5";
          showToast("Headline Duration: Vanishes after 5s");
        } else if (dur === "10") {
          selectedHeadlineDuration = 10.0;
          if (headlineDurationInput) headlineDurationInput.value = "10";
          showToast("Headline Duration: Vanishes after 10s");
        } else {
          selectedHeadlineDuration = null;
          if (headlineDurationInput) headlineDurationInput.value = "";
          showToast("Headline Duration: Sticky for Full Video");
        }
      });
    });
  }

  if (progressBarToggle) {
    progressBarToggle.addEventListener("change", (e) => {
      selectedProgressBar = e.target.checked;
      updateProgressBarPreview();
      showToast(selectedProgressBar ? "Retention Progress Bar: Enabled" : "Retention Progress Bar: Disabled");
    });
  }

  if (progBarBottomBtn && progBarTopBtn) {
    progBarBottomBtn.addEventListener("click", () => {
      progBarBottomBtn.classList.add("active");
      progBarTopBtn.classList.remove("active");
      selectedProgressBarPos = "bottom";
      updateProgressBarPreview();
    });
    progBarTopBtn.addEventListener("click", () => {
      progBarTopBtn.classList.add("active");
      progBarBottomBtn.classList.remove("active");
      selectedProgressBarPos = "top";
      updateProgressBarPreview();
    });
  }

  if (autoEmojisToggle) {
    autoEmojisToggle.addEventListener("change", (e) => {
      selectedAutoEmojis = e.target.checked;
      showToast(selectedAutoEmojis ? "3D Viral Stickers: Enabled" : "3D Viral Stickers: Disabled");
    });
  }

  if (kineticZoomToggle) {
    kineticZoomToggle.addEventListener("change", (e) => {
      showToast(e.target.checked ? "🎥 Kinetic Punch-In Zooms: Enabled" : "Kinetic Zooms: Disabled");
    });
  }

  if (soundEffectsToggle) {
    soundEffectsToggle.addEventListener("change", (e) => {
      showToast(e.target.checked ? "🔊 Viral Pop SFX: Enabled" : "Viral Pop SFX: Disabled");
    });
  }

  if (bgMusicToggle) {
    bgMusicToggle.addEventListener("change", (e) => {
      showToast(e.target.checked ? "🎵 Lo-Fi Ambient Beat: Enabled" : "Lo-Fi Ambient Beat: Disabled");
    });
  }

  function updateWatermarkPreview() {
    if (!canvasWatermark) return;
    const isClipsMode = tabClipsStudio && tabClipsStudio.classList.contains("active");
    const isEnabled = isClipsMode 
      ? (clipWatermarkToggle ? clipWatermarkToggle.checked : false)
      : (watermarkToggle ? watermarkToggle.checked : false);
    const textVal = isClipsMode
      ? (clipWatermarkInput ? clipWatermarkInput.value.trim() : "")
      : (watermarkInput ? watermarkInput.value.trim() : "");

    if (isEnabled && textVal) {
      canvasWatermark.classList.remove("hidden");
      if (canvasWatermarkText) {
        canvasWatermarkText.textContent = textVal.startsWith("@") ? textVal : `@${textVal}`;
      }
    } else {
      canvasWatermark.classList.add("hidden");
    }
  }

  if (watermarkInput) {
    watermarkInput.addEventListener("input", updateWatermarkPreview);
  }

  updateHeadlineHookPreview();
  updateProgressBarPreview();
  updateWatermarkPreview();

  // =========================================================================
  // 6. Start Job with Real-Time Upload Progress & Dual Progress Bars
  // =========================================================================
  async function submitVideoJob(overrides = {}) {
    if (startJobBtn.disabled || (btnRenderSingleClip && btnRenderSingleClip.disabled)) return;

    if (!selectedFile) {
      showToast("Please upload a video before rendering!");
      return;
    }

    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }

    startJobBtn.disabled = true;
    if (btnRenderSingleClip) btnRenderSingleClip.disabled = true;
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
    formData.append("preset", overrides.preset || getSelectedPreset());
    formData.append("llm_provider", llmProvider.value);
    if (aiEnhanceToggle && aiEnhanceToggle.checked) {
      formData.append("ai_enhance", "true");
    }
    formData.append("language", videoLanguage.value);
    formData.append("aspect_ratio", overrides.aspect_ratio || selectedAspectRatio);
    formData.append("subtitle_position", subPosition ? subPosition.value : "lower");
    formData.append("caption_size", overrides.caption_size || selectedCaptionSize);
    formData.append("background_style", selectedBgStyle);
    formData.append("style_pacing", selectedStylePacing);
    formData.append("highlight_color", overrides.highlight_color || selectedHighlightColor);
    formData.append("selected_styles", overrides.selected_styles !== undefined ? overrides.selected_styles : selectedStyles.join(","));
    formData.append("subtitle_y", overrides.subtitle_y !== undefined ? overrides.subtitle_y : currentSubtitleY.toFixed(2));
    formData.append("video_layout", selectedVideoLayout);
    formData.append("progress_bar", (overrides.progress_bar !== undefined ? overrides.progress_bar : selectedProgressBar) ? "true" : "false");
    formData.append("progress_bar_position", selectedProgressBarPos);

    const hookText = overrides.headline_hook !== undefined ? overrides.headline_hook : (selectedHeadlineHookEnabled ? selectedHeadlineHookText : "");
    if (hookText && hookText.trim()) {
      formData.append("headline_hook", hookText.trim());
      formData.append("headline_style", overrides.headline_style || selectedHeadlineHookStyle);
      const hookDur = overrides.headline_duration !== undefined ? overrides.headline_duration : selectedHeadlineDuration;
      if (hookDur !== null && hookDur !== undefined) {
        formData.append("headline_duration", hookDur.toString());
      }
      formData.append("headline_y", (overrides.headline_y !== undefined ? overrides.headline_y : selectedHeadlinePosRatio).toString());
    }

    formData.append("auto_emojis", (overrides.auto_emojis !== undefined ? overrides.auto_emojis : selectedAutoEmojis) ? "true" : "false");
    if (overrides.kinetic_zoom !== undefined ? overrides.kinetic_zoom : (kineticZoomToggle && kineticZoomToggle.checked)) {
      formData.append("kinetic_zoom", "true");
    }
    if (overrides.sound_effects !== undefined ? overrides.sound_effects : (soundEffectsToggle && soundEffectsToggle.checked)) {
      formData.append("sound_effects", "true");
    }
    const bgMusicVal = overrides.bg_music !== undefined ? overrides.bg_music : ((bgMusicToggle && bgMusicToggle.checked) ? "lofi" : "");
    if (bgMusicVal) {
      formData.append("bg_music", bgMusicVal);
    }
    const isWatermarkActive = overrides.watermark_text !== undefined
      ? Boolean(overrides.watermark_text)
      : (watermarkToggle && watermarkToggle.checked);
    const watermarkVal = isWatermarkActive 
      ? (overrides.watermark_text !== undefined ? overrides.watermark_text : (watermarkInput ? watermarkInput.value.trim() : ""))
      : "";
    if (watermarkVal) {
      formData.append("watermark_text", watermarkVal);
    }

    if (draftToggle.checked) {
      formData.append("draft", "true");
    }

    if (overrides.trim_start !== undefined) {
      formData.append("trim_start", parseFloat(overrides.trim_start).toFixed(2));
    } else if (trimStartSec > 0.05) {
      formData.append("trim_start", trimStartSec.toFixed(2));
    }

    if (overrides.trim_end !== undefined) {
      formData.append("trim_end", parseFloat(overrides.trim_end).toFixed(2));
    } else if (trimEndSec < videoTotalDuration - 0.05) {
      formData.append("trim_end", trimEndSec.toFixed(2));
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
    if (clipBtnTextLabel) clipBtnTextLabel.textContent = "Uploading Reel... 0%";
    if (clipBtnProgressFill) clipBtnProgressFill.style.width = "5%";

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
        if (clipBtnTextLabel) clipBtnTextLabel.textContent = `Uploading Reel... ${uploadPct}%`;
        if (clipBtnProgressFill) clipBtnProgressFill.style.width = `${uploadPct}%`;
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
          if (clipBtnTextLabel) clipBtnTextLabel.textContent = "Transcribing Speech...";

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
  }

  startJobBtn.addEventListener("click", () => submitVideoJob({}));

  if (btnRenderSingleClip) {
    btnRenderSingleClip.addEventListener("click", async () => {
      if (!activeSelectedClip) {
        showToast("Please select a clip to render!");
        return;
      }
      if (btnRenderSingleClip.disabled) return;

      const hookText = clipHeadlineInput ? clipHeadlineInput.value.trim() : activeSelectedClip.headline;
      const isWatermarkOn = clipWatermarkToggle ? clipWatermarkToggle.checked : false;
      const watermarkVal = isWatermarkOn && clipWatermarkInput ? clipWatermarkInput.value.trim() : null;

      // FAST PATH: If currentJobId is present, call dedicated lightning-fast /render-clip endpoint!
      if (currentJobId) {
        btnRenderSingleClip.disabled = true;
        startJobBtn.disabled = true;
        showStage("processing");
        stageStatus.textContent = "Rendering Viral Reel...";
        jobStartTime = Date.now();

        if (pipelineProgressCard) pipelineProgressCard.classList.remove("hidden");
        if (pipelineProgressTitle) pipelineProgressTitle.textContent = "Rendering Viral Reel...";
        if (pipelineProgressPct) pipelineProgressPct.textContent = "15%";
        if (pipelineProgressFill) pipelineProgressFill.style.width = "15%";
        if (pipelineProgressDesc) pipelineProgressDesc.textContent = `Slicing and rendering "${hookText || activeSelectedClip.headline}"...`;
        if (pipelineProgressTime) pipelineProgressTime.textContent = "0s elapsed";

        if (clipBtnTextLabel) clipBtnTextLabel.textContent = "Rendering Reel... 15%";
        if (clipBtnProgressFill) clipBtnProgressFill.style.width = "15%";

        try {
          const payload = {
            start: activeSelectedClip.start,
            end: activeSelectedClip.end,
            headline: hookText || null,
            headline_style: selectedHeadlineHookStyle,
            headline_duration: selectedHeadlineDuration,
            headline_y: selectedHeadlinePosRatio,
            caption_size: selectedCaptionSize,
            subtitle_y: currentSubtitleY,
            selected_styles: selectedStyles.length > 0 ? selectedStyles[0] : "ai_auto",
            watermark_text: watermarkVal,
            video_layout: selectedClipLayout || "split_podcast",
            ai_enhance: clipAiEnhanceToggle ? clipAiEnhanceToggle.checked : false,
            kinetic_zoom: clipKineticZoomToggle ? clipKineticZoomToggle.checked : false,
            sound_effects: clipPopSfxToggle ? clipPopSfxToggle.checked : true,
            bg_music: (clipBgMusicToggle && clipBgMusicToggle.checked) ? "lofi" : null,
            progress_bar: true,
            auto_emojis: clipAutoEmojisToggle ? clipAutoEmojisToggle.checked : true,
            aspect_ratio: "9:16",
            draft: draftToggle ? draftToggle.checked : false,
          };

          const res = await fetch(`/api/jobs/${currentJobId}/render-clip`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "Single clip render request failed");
          }

          const clipJob = await res.json();
          currentJobId = clipJob.id;
          startPolling(clipJob.id);
          return;
        } catch (err) {
          console.error("Render clip error:", err);
          showToast(`Render failed: ${err.message}`);
          btnRenderSingleClip.disabled = false;
          startJobBtn.disabled = false;
          showStage(selectedFile ? "source" : "idle");
          return;
        }
      }

      // FALLBACK PATH: If currentJobId is not set, submit via submitVideoJob with exact overrides
      const overrides = {
        trim_start: activeSelectedClip.start.toFixed(2),
        trim_end: activeSelectedClip.end.toFixed(2),
        aspect_ratio: "9:16",
        headline_hook: hookText,
        headline_style: selectedHeadlineHookStyle,
        headline_duration: selectedHeadlineDuration,
        headline_y: selectedHeadlinePosRatio,
        caption_size: selectedCaptionSize,
        subtitle_y: currentSubtitleY.toFixed(2),
        selected_styles: selectedStyles.length > 0 ? selectedStyles[0] : "ai_auto",
        watermark_text: watermarkVal || "",
        video_layout: selectedClipLayout || "split_podcast",
        ai_enhance: clipAiEnhanceToggle ? (clipAiEnhanceToggle.checked ? "true" : "false") : "false",
        kinetic_zoom: clipKineticZoomToggle ? clipKineticZoomToggle.checked : false,
        sound_effects: clipPopSfxToggle ? clipPopSfxToggle.checked : true,
        bg_music: (clipBgMusicToggle && clipBgMusicToggle.checked) ? "lofi" : "",
        progress_bar: true,
        auto_emojis: clipAutoEmojisToggle ? clipAutoEmojisToggle.checked : true,
      };

      await submitVideoJob(overrides);
    });
  }

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
    if (clipBtnProgressFill) clipBtnProgressFill.style.width = `${overallPct}%`;

    const elapsed = Math.floor((Date.now() - jobStartTime) / 1000);
    procElapsed.textContent = `${elapsed}s elapsed`;

    const stepLabels = {
      queued: "Queued in render queue...",
      trimming: "Trimming video clip to range...",
      probing: "Analyzing dimensions & audio channels...",
      transcribing: "Aligning speech with faster-whisper...",
      chunking: "Structuring natural cadence & phrases...",
      analyzing: "AI Director: Analyzing video scenes, speakers & context...",
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
    if (clipBtnTextLabel) clipBtnTextLabel.textContent = `Rendering Reel... ${overallPct}%`;

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
    if (btnRenderSingleClip) btnRenderSingleClip.disabled = false;
    if (clipBtnProgressFill) clipBtnProgressFill.style.width = "0%";
    if (clipBtnTextLabel) clipBtnTextLabel.textContent = "⚡ Render This Viral Reel (MP4)";
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
    if (btnRenderSingleClip) btnRenderSingleClip.disabled = false;
    if (clipBtnProgressFill) clipBtnProgressFill.style.width = "0%";
    if (clipBtnTextLabel) clipBtnTextLabel.textContent = "⚡ Render This Viral Reel (MP4)";
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
        if (rerenderBtn) rerenderBtn.classList.remove("hidden");
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

  if (rerenderBtn) {
    rerenderBtn.addEventListener("click", async () => {
      if (!currentJobId || !currentTimeline) return;
      rerenderBtn.textContent = "Re-rendering...";
      rerenderBtn.disabled = true;
      try {
        // Sync headline hook & duration state to currentTimeline
        if (selectedHeadlineHookEnabled && selectedHeadlineHookText.trim()) {
          currentTimeline.headlineHook = selectedHeadlineHookText.trim();
          currentTimeline.headlineStyle = selectedHeadlineHookStyle;
          currentTimeline.headlineDuration = selectedHeadlineDuration;
        } else {
          currentTimeline.headlineHook = null;
        }

        if (kineticZoomToggle) currentTimeline.kineticZoom = kineticZoomToggle.checked;
        if (soundEffectsToggle) currentTimeline.soundEffects = soundEffectsToggle.checked;
        if (bgMusicToggle) currentTimeline.bgMusic = bgMusicToggle.checked ? "lofi" : null;
        if (watermarkInput) currentTimeline.watermarkText = watermarkInput.value.trim() || null;

        // Save timeline edits first
        await fetch(`/api/jobs/${currentJobId}/timeline`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(currentTimeline),
        });

        // Trigger fast re-render on existing job
        const formData = new FormData();
        if (draftToggle && draftToggle.checked) {
          formData.append("draft", "true");
        }
        const res = await fetch(`/api/jobs/${currentJobId}/rerender`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error("Re-render request failed");

        showToast("Re-rendering video with updated captions...");
        showStage("processing");
        stageStatus.textContent = "Re-rendering...";
        jobStartTime = Date.now();
        procTitle.textContent = "Re-rendering Video...";
        procStep.textContent = "Composing updated frames with Remotion...";
        procFill.style.width = "40%";
        if (pipelineProgressCard) pipelineProgressCard.classList.remove("hidden");
        startPolling(currentJobId);
      } catch (err) {
        showToast(`Re-render error: ${err.message}`);
      } finally {
        rerenderBtn.textContent = "⚡ Re-render";
        rerenderBtn.disabled = false;
      }
    });
  }

  // Full Studio Reset for loading or generating a new video
  function resetStudioForNewVideo() {
    // 0. Cancel active backend job if still processing/queued
    if (currentJobId) {
      try {
        fetch(`/api/jobs/${currentJobId}/cancel`, { method: "POST" }).catch(() => {});
      } catch {}
    }

    // 1. Terminate any active polling
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }

    // 2. Stop and detach result video
    if (resultVideo) {
      resultVideo.pause();
      resultVideo.removeAttribute("src");
      resultVideo.load();
    }

    // 3. Stop and detach all source preview players
    const previewPlayers = [
      sourceVideoPlayer,
      sourceSplitTop,
      sourceSplitBottom,
      sourceBlurBg,
      sourceBlurMain,
      sourceTripleTop,
      sourceTripleMid,
      sourceTripleBot,
    ];
    previewPlayers.forEach((p) => {
      if (p) {
        try {
          p.pause();
          p.removeAttribute("src");
          p.load();
        } catch {}
      }
    });

    // 4. Reset file state & file inputs
    selectedFile = null;
    currentJobId = null;
    currentTimeline = null;
    if (videoFileInput) videoFileInput.value = "";
    if (dropPrompt) dropPrompt.classList.remove("hidden");
    if (fileBadge) fileBadge.classList.add("hidden");
    if (fileName) fileName.textContent = "";
    if (fileSize) fileSize.textContent = "";

    // 5. Reset trimmer state
    trimStartSec = 0.0;
    trimEndSec = 12.0;
    videoTotalDuration = 12.0;
    updateTrimmerDisplay();
    if (trimReadout) trimReadout.textContent = "Full Video";

    // 6. Reset UI action bars, cards, and generate button
    if (resultActions) resultActions.classList.add("hidden");
    if (editorCard) editorCard.classList.add("hidden");
    if (saveEditsBtn) saveEditsBtn.classList.add("hidden");
    if (rerenderBtn) rerenderBtn.classList.add("hidden");
    if (pipelineProgressCard) pipelineProgressCard.classList.add("hidden");

    if (startJobBtn) startJobBtn.disabled = false;
    if (btnProgressFill) btnProgressFill.style.width = "0%";
    if (btnTextLabel) btnTextLabel.textContent = "Generate Captioned Video ⚡";

    activeSelectedClip = null;
    if (clipTweakerCard) clipTweakerCard.classList.add("hidden");
    if (btnRenderSingleClip) btnRenderSingleClip.disabled = false;
    if (clipBtnProgressFill) clipBtnProgressFill.style.width = "0%";
    if (clipBtnTextLabel) clipBtnTextLabel.textContent = "⚡ Render This Viral Reel (MP4)";
    if (clipsCountBadge) clipsCountBadge.textContent = "0 Found";

    // 7. Reset canvas stage to idle
    showStage("idle");
    if (stageStatus) stageStatus.textContent = "Preview Canvas";
    updateSourcePreviewFraming();
    showToast("Ready for new video! 🎬");
  }

  if (closeResultBtn) {
    closeResultBtn.addEventListener("click", resetStudioForNewVideo);
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", resetStudioForNewVideo);
  }

  // Stage Switcher
  function showStage(stage) {
    viewIdle.classList.toggle("hidden", stage !== "idle");
    viewSource.classList.toggle("hidden", stage !== "source");
    viewProcessing.classList.toggle("hidden", stage !== "processing");
    viewResult.classList.toggle("hidden", stage !== "result");

    const showDraggable = (stage === "idle" || stage === "source");
    if (draggableCaptionBox) draggableCaptionBox.classList.toggle("hidden", !showDraggable);
    if (snapGuideUpper) snapGuideUpper.classList.toggle("hidden", !showDraggable);
    if (snapGuideCenter) snapGuideCenter.classList.toggle("hidden", !showDraggable);
    if (snapGuideLower) snapGuideLower.classList.toggle("hidden", !showDraggable);

    // Hide preview overlays when processing or viewing final result
    const showOverlays = (stage === "idle" || stage === "source");
    if (canvasHeadlineHook) {
      canvasHeadlineHook.classList.toggle("hidden", !showOverlays || !selectedHeadlineHookEnabled);
    }
    if (canvasProgressBar) {
      canvasProgressBar.classList.toggle("hidden", !showOverlays || !selectedProgressBar);
    }
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
