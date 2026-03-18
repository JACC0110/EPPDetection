const VIDEO_SERVICE_URL = "http://127.0.0.1:8001/process-video";

const form = document.getElementById("analyzeForm");
const resultsSection = document.getElementById("results");
const summaryEl = document.getElementById("summary");
const violationsEl = document.getElementById("violations");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData();
  const fileInput = document.getElementById("videoFile");
  const urlInput = document.getElementById("videoUrl");

  if (fileInput.files.length > 0) {
    formData.append("file", fileInput.files[0]);
  } else if (urlInput.value.trim()) {
    formData.append("video_url", urlInput.value.trim());
  } else {
    alert("Please provide a video file or a video URL.");
    return;
  }

  const selectedPpe = Array.from(document.querySelectorAll("input[name='ppe']:checked")).map(
    (input) => input.value
  );
  if (selectedPpe.length) {
    formData.append("required_items", selectedPpe.join(","));
  }

  summaryEl.innerHTML = "<p>Analizando video…</p>";
  violationsEl.innerHTML = "";
  resultsSection.hidden = false;

  try {
    const response = await fetch(VIDEO_SERVICE_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => null);
      throw new Error(error?.detail || response.statusText);
    }

    const data = await response.json();

    summaryEl.innerHTML = `<p>Video ID: <code>${data.video_id}</code></p>
      <p>Frames analizados: ${data.frames_analyzed}</p>
      <p>Violations: ${data.violations.length}</p>`;

    if (data.violations.length === 0) {
      violationsEl.innerHTML = "<p>No violations detected.</p>";
      return;
    }

    for (const violation of data.violations) {
      const card = document.createElement("div");
      card.className = "violation";

      const info = document.createElement("div");
      info.innerHTML = `
        <dl>
          <dt>Video time</dt><dd>${violation.video_time?.toFixed(2)}s</dd>
          <dt>Missing items</dt><dd>${violation.missing_items?.join(", ") || "-"}</dd>
          <dt>Image</dt><dd>${violation.image_path || "-"}</dd>
        </dl>
      `;

      const img = document.createElement("img");
      img.src = violation.image_path || "";
      img.alt = `Violation @ ${violation.video_time}s`;
      img.loading = "lazy";

      card.append(info, img);
      violationsEl.appendChild(card);
    }
  } catch (err) {
    summaryEl.innerHTML = `<p style="color: #b91c1c;">Error: ${err.message}</p>`;
  }
});
