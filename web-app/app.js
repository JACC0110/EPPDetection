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
    alert("Por favor proporciona un archivo de video o una URL.");
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

    summaryEl.innerHTML = `<p><strong>ID del Video:</strong> <code>${data.video_id}</code></p>
      <p><strong>Frames analizados:</strong> ${data.frames_analyzed}</p>
      <p><strong>Incumplimientos encontrados:</strong> ${data.violations.length}</p>`;

    if (data.violations.length === 0) {
      violationsEl.innerHTML = "<p style='color: #22c55e;'>✓ No se detectaron incumplimientos.</p>";
      return;
    }

    for (const violation of data.violations) {
      const card = document.createElement("div");
      card.className = "violation";

      const info = document.createElement("div");
      info.innerHTML = `
        <dl>
          <dt>Tiempo (s)</dt><dd>${violation.video_time?.toFixed(2) || "-"}</dd>
          <dt>Cumplidos</dt><dd>${violation.cumplidos?.join(", ") || "-"}</dd>
          <dt>Faltantes</dt><dd>${violation.faltantes?.join(", ") || "-"}</dd>
        </dl>
      `;

      const imgContainer = document.createElement("div");
      imgContainer.className = "violation-image-container";

      const img = document.createElement("img");
      img.src = violation.image_url || "";
      img.alt = `Violación @ ${violation.video_time}s`;
      img.loading = "lazy";

      imgContainer.appendChild(img);
      card.append(info, imgContainer);
      violationsEl.appendChild(card);
    }
  } catch (err) {
    summaryEl.innerHTML = `<p style="color: #b91c1c;">❌ Error: ${err.message}</p>`;
  }
});
