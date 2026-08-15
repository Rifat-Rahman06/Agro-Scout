var backend;
var auto_state = false;

new QWebChannel(qt.webChannelTransport, function (channel) {
  backend = channel.objects.bridge;
});

var map = L.map('map').setView([23.7978814, 90.4499017], 20);


L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);


// const mapElement = document.querySelector('.leaflet-container');
//     if (mapElement)
//         mapElement.style.filter = 'invert(100%) hue-rotate(180deg)';

L.HtmlIcon = L.Icon.extend({
  options: {},

  initialize: function (options) {
      L.Util.setOptions(this, options); 
  },

  createIcon: function () {
      var div = document.createElement('div');
      div.innerHTML = this.options.html; 
      return div; 
  },

  createShadow: function () {
      return null; 
  }
});
  
  const markersArray = [];
  
  
  const HTMLIcon = L.HtmlIcon.extend({
      options: {
          html: "<div class=\"map__marker\"></div>", 
      }
  });


let highlightedMarker = null;

// Function to create and add a blinking marker
function addBlinkingMarker(lat, lon) {
    const customHtmlIcon = new HTMLIcon();
    const marker = new L.Marker(new L.LatLng(lat, lon), { icon: customHtmlIcon });
    markersArray.push(marker); 
    map.addLayer(marker); 
}


// New method to highlight a marker based on lat and lon
function highlightMarkerAt(lat, lon) {
  // Find the marker with the specified coordinates
  const markerToHighlight = markersArray.find(marker => {
      const { lat: markerLat, lng: markerLng } = marker.getLatLng();
      return markerLat === lat && markerLng === lon;
  });

  if (markerToHighlight) {
      // Reset the previous highlighted marker
      if (highlightedMarker && highlightedMarker !== markerToHighlight) {
          resetMarkerColor(highlightedMarker);
      }

      // Highlight the current marker
      const markerDiv = markerToHighlight.getElement().querySelector('.map__marker');
      if (markerDiv) {
          markerDiv.style.backgroundColor = 'rgb(29, 192, 162)'; // Change to red
      }

      // Set the highlighted marker to the current one
      highlightedMarker = markerToHighlight;
  }
}

function resetMarkerColor(marker) {
  const markerDiv = marker.getElement().querySelector('.map__marker');
  if (markerDiv) {
      const originalColor = getOriginalMarkerColor();
      markerDiv.style.backgroundColor = originalColor; // Reset to original color
  }
}

// Function to get the original color of the marker from CSS
function getOriginalMarkerColor() {
  const markerDiv = document.createElement('div');
  markerDiv.innerHTML = "<div class=\"map__marker\"></div>";
  document.body.appendChild(markerDiv);
  const originalColor = window.getComputedStyle(markerDiv.firstChild).backgroundColor; // Get original color from CSS
  document.body.removeChild(markerDiv); // Clean up
  return originalColor;
}


// Event listener for map clicks
map.on('click', function (e) {
  if (highlightedMarker) {
      resetMarkerColor(highlightedMarker);
      highlightedMarker = null; 
  }
});

var iconWidth = 30; 
var iconHeight = 30;

var icons = {};

var mymarker = L.marker([23.7978814, 90.4499017]).addTo(map);

function set_heading(angle) {
  if (icons[angle]) {
    mymarker.setIcon(icons[angle]);
  }
}

function update_location(lat,lon){
  mymarker.setLatLng([lat, lon]);
}



function removeMarker(lat, lon) {
    
  const markerToRemove = markersArray.find(marker => {
      const { lat: markerLat, lng: markerLng } = marker.getLatLng();
      return markerLat === lat && markerLng === lon;
  });

  if (markerToRemove) {
     
      map.removeLayer(markerToRemove);
      
      markersArray.splice(markersArray.indexOf(markerToRemove), 1);
      
  }
}


var markerCoords = [];
var rectangle = null; 
var canSelectArea = false; 
function onMapClick(e) {
    if (!canSelectArea) return; // Only proceed if canSelectArea is true

    // Add a marker at the clicked location
    var marker = L.marker(e.latlng).addTo(map);

    // Store the clicked location in the markerCoords array
    markerCoords.push(e.latlng);

    // Check if four markers have been placed
    if (markerCoords.length === 4) {
      // Create a rectangle using the four coordinates
      var bounds = L.latLngBounds(markerCoords);
      
      // Remove existing rectangle if present
      removeRectangle();

      rectangle = L.rectangle(bounds, { color: "#ff7800", weight: 1 }).addTo(map);

      var topLeft = bounds.getNorthWest();
      var bottomRight = bounds.getSouthEast();

      backend.autonomous(topLeft.lat ,topLeft.lng,bottomRight.lat,  bottomRight.lng);
       
      markerCoords.forEach(latlng => {
        map.eachLayer(function(layer) {
            if (layer instanceof L.Marker) {
                // Check if the marker's position matches the current latlng
                if (layer.getLatLng().equals(latlng)) {
                    map.removeLayer(layer); // Remove the specific marker
                }
            }
        });
    });
      markerCoords = [];
      canSelectArea = false;
      document.getElementById('select-area-text').innerText = 'Stop';
      document.getElementById('select-area-btn').style.background = 'rgba(255,0,0,.2)';
      document.getElementById('select-area-btn').style.border = '1px solid rgba(255,0,0,.6)';
    }
  }


function removeRectangle() {
if (rectangle) {
    map.removeLayer(rectangle);
    rectangle = null; 
}
}


function removeAll() {
  removeRectangle();
  markerCoords.forEach(latlng => {
      map.eachLayer(function(layer) {
          if (layer instanceof L.Marker) {
              // Check if the marker's position matches the current latlng
              if (layer.getLatLng().equals(latlng)) {
                  map.removeLayer(layer); // Remove the specific marker
              }
          }
      });
  });
    markerCoords = [];

  }

  map.on('click', onMapClick);


function auto_state_toggle(){
  auto_state = !auto_state;
  if(auto_state){
    canSelectArea = true;
  }
  else {
    removeAll();
    document.getElementById('select-area-text').innerText = 'Select Area';
    document.getElementById('select-area-btn').style.background = 'rgba(119, 216, 130, .4)';
    document.getElementById('select-area-btn').style.border = '1px solid #77d882';
    backend.stopp();

  }
}









//Add log
var logo;
function add_log(disease_class, lat, lon, nitrogen, phosphorus, potassium, water, time) {
  const logContainer = document.querySelector(".log-container");

    let htmlContent = "";
      htmlContent = `
          <div id="log_instance" class="log-row" 
        data-lat="${lat}" data-lon="${lon}" onclick="highlight(this)">
      <div class="log-data-top">
        <p class="log-data-title">Diseased plant detected</p>
        <p class="log-data-class">Class : <span id="disease-class" style="color: #FFCF97;">${disease_class}</span></p>
      </div>
      <div class="log-data-middle">
        <img class="log-data-icon" src=${logo} alt="disease">
        <p class="log-data-location">Lat : <span id="log-lat" style="color: white;">${lat}</span> | 
          Lon : <span id="log-lon" style="color: white;">${lon}</span> | 
          Time : <span id="log-time" style="color: white;">${time}</span></p>
        <div class="get-suggestion" onclick="suggestion_log(this)">Suggestions!</div>
      </div>
      <div class="log-data-bottom">
        <p class="log-data-status">Nitrogen : <span id="nit-value" style="color: white;">${nitrogen}</span>  | 
          Phosphorus : <span id="pho-value" style="color: white;" >${phosphorus}</span> | 
          Potassium : <span id="pot-value" style="color: white;" >${potassium}</span> | 
          Water level:<span id="wat-value" style="color: white;">${water}</span></p>
      </div>
    </div>

    `;

    logContainer.innerHTML += htmlContent;
}

function highlight(element) {

  const lat = parseFloat(element.dataset.lat);  
  const lon = parseFloat(element.dataset.lon);
  
  highlightMarkerAt(lat, lon);
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
              <p class="tooltips-el">Nitrogen : <span class="tooltips-nit-value" style="color: white;">NULL</span></p>
              <p class="tooltips-el">Phosphorus :  <span class="tooltips-pho-value" style="color: white;">NULL</span></p>
              <p class="tooltips-el">Potassium :  <span class="tooltips-pot-value" style="color: white;">NULL</span></p>
              <p class="tooltips-wat">Water :  <span class="tooltips-wat-value" style="color: white;">NULL</span></p>
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

function getColor_2(n , p , k, water) {
  if(n>=20 && n<=60 && p >= 20 && p <= 40 && k >= 100 && k <= 300 && water >=40 && water <= 80){
    return `rgb(66, 252, 72)`;
  }
  else{
    return `rgb(252, 66, 69)`;
  }
  
}

// for (let i = 0; i < 1; i++) {
//   // Random values for NPK and water
//   let nitrogen = Math.floor(Math.random() * 101);
//   let phosphorus = Math.floor(Math.random() * 101);
//   let potassium = Math.floor(Math.random() * 101);
//   let water = Math.floor(Math.random() * 101);
//   set_grid(i, nitrogen, phosphorus, potassium, water);
// }

// Set the grid values
function set_grid(index_value, n, p, k, water) {
  const gridItems = document.querySelectorAll(".grid-item");
  // let color = getColor(Math.max(n, p, k));
  let color = getColor_2(n,p,k,water);
  gridItems[index_value].style.backgroundColor = color;
  gridItems[index_value].querySelector(".tooltips-nit-value").innerText =n + " mg/kg";
  gridItems[index_value].querySelector(".tooltips-pho-value").innerText =p + " mg/kg";
  gridItems[index_value].querySelector(".tooltips-pot-value").innerText =k + " mg/kg";
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

function connection_status(text){
  ob = document.getElementById('connection-text');
  ob.textContent  = text;
}

function set_icons(ic) {
  document.getElementById("project-logo").src = ic["logo.svg"];
  document.getElementById("sync-logo").src = ic["model.svg"];
  document.getElementById("area-logo").src = ic["area.svg"];
  document.getElementById("connections-logo").src = ic["connection.svg"];
  logo = ic["location.svg"];
  document.getElementById("tick-logo").src = ic["compass_tick.svg"];
  document.getElementById("compas-logo").src = ic["compass.svg"];
  document.getElementById("tick-logo").src = ic["compass_tick.svg"];
  document.getElementById("battery-logo").src = ic["battery.svg"];
  document.getElementById("speed-logo").src = ic["speed.svg"];
  document.getElementById("spray-logo").src = ic["spray.svg"];
  document.getElementById("plant-logo").src = ic["plant.svg"];
  document.getElementById("tilt-logo").src = ic["position.svg"];
  document.getElementById("position-logo").src = ic["position.svg"];
  document.getElementById("close-suggestion-logo").src = ic["cross.svg"];
  for (const key of Object.keys(ic)) {
    const match = key.match(/^(\d{1,3})\.svg$/);
    if (match) {
      icons[match[1]] = L.icon({ iconUrl: ic[key], iconSize: [iconWidth, iconHeight] });
    }
  }
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
