async function searchSong() {
  const q = document.getElementById("search").value;
  const res = await fetch(`/api/search?q=${q}`);
  const data = await res.json();

  document.getElementById("result").innerHTML = `
    <div class="card">
      <img src="${data.thumbnail}" width="200"><br>
      <b>${data.title}</b><br>
      ${data.artist}<br><br>

      <audio controls src="/api/stream/${data.id}"></audio><br><br>

      <select id="quality">
        <option value="low">Low (64kbps)</option>
        <option value="medium">Medium (128kbps)</option>
        <option value="high">High (192kbps)</option>
        <option value="veryhigh">Very High (320kbps)</option>
      </select>

      <br><br>
      <a id="download" href="#">Download</a>
    </div>
  `;

  document.getElementById("download").onclick = () => {
    const q = document.getElementById("quality").value;
    window.location = `/api/download/${data.id}?quality=${q}`;
  };
}
