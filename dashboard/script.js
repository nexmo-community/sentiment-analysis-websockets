var smoothie = new SmoothieChart({ maxValue: 1, minValue: 0 });
smoothie.streamTo(document.getElementById("mycanvas"), 3000);

const ws = new WebSocket("wss://SOCKET_BASE_URL/dashboard");

var series = {};

ws.onmessage = function(evt) {
  const tones = JSON.parse(evt.data);

  tones.forEach(function(tone) {
    if (series[tone.tone_id]) {
      addNewEntry(series[tone.tone_id], tone.score);
    } else {
      const toneId = tone.tone_id;
      const color = random_rgb();
      const newEntry = {
        timeSeries: new TimeSeries(),
        stroke: color,
        fill: "rgba(255,255,255,0.7)"
      };

      series[toneId] = newEntry;
      addSeriesToChart(newEntry);
      addToList(toneId, color);
    }
  });
};

function addToList(toneId, color) {
  var list = document.getElementById("toneList");
  var entry = document.createElement("li");
  entry.appendChild(document.createTextNode(toneId));
  entry.style.color = color
  list.appendChild(entry);
}

function addSeriesToChart(entry) {
  smoothie.addTimeSeries(entry.timeSeries, {
    strokeStyle: entry.stroke,
    fillStyle: entry.fill,
    lineWidth: 6
  });
}

function addNewEntry(entry, score) {
  entry.timeSeries.append(new Date().getTime(), score);
}

function random_rgb() {
  var o = Math.round,
    r = Math.random,
    s = 255;
  return "rgba(" + o(r() * s) + "," + o(r() * s) + "," + o(r() * s) + ")";
}
