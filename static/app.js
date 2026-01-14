async function search() {
async function search() {
  const q = document.getElementById("query").value.trim();
  if (!q) return;

  const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
  const data = await res.json();

  const results = document.getElementById("results");
  results.innerHTML = "";
  document.getElementById("player").innerHTML = "";

  if (data.length === 0) {
    results.innerHTML = "<p>No results found</p>";
    return;
  }

  data.forEach(song => {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <img src="${song.thumbnail}">
      <b>${song.title}</b><br>
      ${song.artist || ""}
    `;
    div.onclick = () => playSong(song.id);
    results.appendChild(div);
  });
}

async function playSong(id) {
  const res = await fetch(`/api/stream/${id}`);
  const d = await res.json();

  document.getElementById("player").innerHTML = `
    <div class="card">
      <img src="${d.thumbnail}">
      <h3>${d.title}</h3>
      ${d.artist}<br><br>

      <audio controls autoplay src="${d.stream_url}"></audio><br><br>

      <select id="q">
        <option value="low">Low (64kbps)</option>
        <option value="medium">Medium (128kbps)</option>
        <option value="high">High (192kbps)</option>
        <option value="veryhigh">Very High (320kbps)</option>
      </select>

      <br><br>
      <button onclick="download('${id}')">Download</button>
    </div>
  `;
}

function download(id) {
  const q = document.getElementById("q").value;
  window.location = `/api/download/${id}?quality=${q}`;
}
