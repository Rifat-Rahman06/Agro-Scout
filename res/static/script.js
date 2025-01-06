var backend;

new QWebChannel(qt.webChannelTransport, function (channel) {
  backend = channel.objects.bridge;
});

var map = L.map('map').setView([23.7978814, 90.4499017], 20);


L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

//var mymarker = L.marker([23.7978814, 90.4499017], { icon: icons['0'] }).addTo(map);
const mapElement = document.querySelector('.leaflet-container');
    if (mapElement)
        mapElement.style.filter = 'invert(100%) hue-rotate(180deg)';



//Add log
var logo;
function add_log(disease_class, lat, lon, nitrogen, phosphorus, potassium, water, time) {
  const logContainer = document.querySelector(".log-container");

    let htmlContent = "";
      htmlContent = `
      <div class="log-row">
        <div class="log-data-top">
          <p class="log-data-title">Diseased plant detected</p>
          <p class="log-data-class">Class : <span id="disease-class" style="color: #FFCF97;">${disease_class}</span></p>
        </div>
        <div class="log-data-middle">
          <img class="log-data-icon" src=${logo} alt="disease">
          <p class="log-data-location">Lat : <span id="log-lat" style="color: white;">${lat}</span> | Lon : <span id="log-lon" style="color: white;">${lon}</span> | Time : <span id="log-time" style="color: white;">${time}</span></p><div class="get-suggestion" onclick="suggestion_log(this)">Suggestions!</div>
        </div>
        <div class="log-data-bottom">
          <p class="log-data-status">Nitrogen : <span id="nit-value" style="color: white;">${nitrogen}</span>  | Phosphorus : <span id="pho-value" style="color: white;" >${phosphorus}</span> | Potassium : <span id="pot-value" style="color: white;" >${potassium}</span> | Water level:<span id="wat-value" style="color: white;">${water}</span></p>
        </div>
      </div>
    `;

    logContainer.innerHTML += htmlContent;
}




// Initialize the grid
const grid = document.querySelector(".grid-container");
if (grid) {
  let htmlContent = "";
  for (let i = 0; i < 150; i++) {
    htmlContent += `
        <div class="grid-item">
          <div class="tooltip">
            <div class="left-content">
              <p class="tooltips-el">Nitrogen : <span class="tooltips-nit-value" style="color: white;">20%</span></p>
              <p class="tooltips-el">Phosphorus :  <span class="tooltips-pho-value" style="color: white;">76%</span></p>
              <p class="tooltips-el">Potassium :  <span class="tooltips-pot-value" style="color: white;">38%</span></p>
              <p class="tooltips-wat">Water :  <span class="tooltips-wat-value" style="color: white;">100%</span></p>
            </div>
            <div class="tooltips-divider"></div>
            <div onclick="suggestion_area(this)" class="right-content">Get suggestion</div>
          </div>
        </div>
    `;
  }

  grid.innerHTML = htmlContent;
}

//Getting the color for the grid

// function getColor(value) {
//   let colorValue = Math.min(255, Math.max(0, 255 - Math.floor(value * 2.55)));
//   return `rgb(${colorValue}, ${255 - colorValue}, 0)`;
// }

function getColor(value) {
  let redValue = Math.min(255, Math.floor(255 * (value / 100)));
  let greenValue = Math.min(216, Math.floor(216 - (value / 100) * 116));
  let blueValue = Math.min(130, Math.floor(130 - (value / 100) * 30));

  return `rgb(${redValue}, ${greenValue}, ${blueValue})`;
}

for (let i = 0; i < 150; i++) {
  // Random values for NPK and water
  let nitrogen = Math.floor(Math.random() * 101);
  let phosphorus = Math.floor(Math.random() * 101);
  let potassium = Math.floor(Math.random() * 101);
  let water = Math.floor(Math.random() * 101);
  set_grid(i, nitrogen, phosphorus, potassium, water);
}

// Set the grid values
function set_grid(index_value, n, p, k, water) {
  const gridItems = document.querySelectorAll(".grid-item");
  let color = getColor(Math.max(n, p, k));
  gridItems[index_value].style.backgroundColor = color;
  gridItems[index_value].querySelector(".tooltips-nit-value").innerText =n + "%";
  gridItems[index_value].querySelector(".tooltips-pho-value").innerText =p + "%";
  gridItems[index_value].querySelector(".tooltips-pot-value").innerText =k + "%";
  gridItems[index_value].querySelector(".tooltips-wat-value").innerText =water + "%";
}

function suggestion_area(element) {
  const gridItem = element.closest(".grid-item");

  const nitrogen = gridItem.querySelector(".tooltips-nit-value").innerText;
  const phosphorus = gridItem.querySelector(".tooltips-pho-value").innerText;
  const potassium = gridItem.querySelector(".tooltips-pot-value").innerText;
  const water = gridItem.querySelector(".tooltips-wat-value").innerText;

  suggestion_container(true);

  backend.area_suggestion(nitrogen, phosphorus, potassium, water);
}


function suggestion_log(element) {
  const logRow = element.closest(".log-row");

  const diseaseClass = logRow.querySelector("#disease-class").innerText;
  const lat = logRow.querySelector("#log-lat").innerText;
  const lon = logRow.querySelector("#log-lon").innerText;
  const nitrogen = logRow.querySelector("#nit-value").innerText;
  const phosphorus = logRow.querySelector("#pho-value").innerText;
  const potassium = logRow.querySelector("#pot-value").innerText;
  const water = logRow.querySelector("#wat-value").innerText;

  suggestion_container(true);

  backend.log_suggestion(diseaseClass, lat,lon,nitrogen,phosphorus,potassium,water);
}





function set_area_suggestion(data) {
  document.getElementById("suggestion-content").innerText = data;
}

function set_log_suggestion(data) {
  document.getElementById("suggestion-content").innerText = data;
}


function set_icons(icons) {
  document.getElementById("project-logo").src = icons["logo.svg"];
  document.getElementById("sync-logo").src = icons["model.svg"];
  document.getElementById("area-logo").src = icons["area.svg"];
  document.getElementById("connections-logo").src = icons["connection.svg"];
  logo = icons["location.svg"];
  document.getElementById("tick-logo").src = icons["compass_tick.svg"];
  document.getElementById("compas-logo").src = icons["compass.svg"];
  document.getElementById("tick-logo").src = icons["compass_tick.svg"];
  document.getElementById("battery-logo").src = icons["battery.svg"];
  document.getElementById("speed-logo").src = icons["speed.svg"];
  document.getElementById("spray-logo").src = icons["spray.svg"];
  document.getElementById("plant-logo").src = icons["plant.svg"];
  document.getElementById("tilt-logo").src = icons["tilt.svg"];
  document.getElementById("position-logo").src = icons["position.svg"];
  document.getElementById("close-suggestion-logo").src = icons["cross.svg"];
}

function suggestion_container(state) {
  document.getElementById("suggestion-container").style.display = state
    ? "flex"
    : "none";
}

function compass(degrees) {
  const element = document.getElementById("tick-logo");
  element.style.transform = `rotate(${degrees}deg)`;
}

function set_battery(data) {
  document.getElementById("battery-value").innerText = data + "%";
}

function set_speed(data) {
  document.getElementById("speed-value").innerText = data + "%";
}

function set_spray(data) {
  document.getElementById("spray-value").innerText = data + "%";
}

function set_diseased_count(data) {
  document.getElementById("diseased-count-value").innerText = data;
}

function set_tilt(x, y) {
  document.getElementById("x-value").innerText = x;
  document.getElementById("y-value").innerText = y;
}

function set_position(lat, lon) {
  document.getElementById("lat-value").innerText = lat;
  document.getElementById("lon-value").innerText = lon;
}
