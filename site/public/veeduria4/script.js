import '../node_modules/d3/dist/d3.min.js';

// Base url
const path = '/veeduria4';

var data;
var groups;
var lastCircle = 'circle0';
var lastMap = 'map1';
var geo;
var start = true;
var flag = true;

var shpidx = new Array(300).fill();

var objs = {
  selDep: document.getElementById('seldep'),
  selMun: document.getElementById('selmun'),
  pltInfFnd: document.getElementById('pltinffnd'),
  mapInfFnd: document.getElementById('mapinffnd'),
}

let rad = document.getElementsByName('fig');
rad[0].addEventListener('change', function() {
  if (rad[0].value == 'on') {
    objs.mapInfFnd.style.display = 'block'
    objs.pltInfFnd.style.display = 'none'
  }
  else {
    objs.mapInfFnd.style.display = 'none'
    objs.pltInfFnd.style.display = 'block'
  }
})
rad[1].addEventListener('change', function() {
  if (rad[0].value == 'on') {
    objs.mapInfFnd.style.display = 'none'
    objs.pltInfFnd.style.display = 'block'
  }
  else {
    objs.mapInfFnd.style.display = 'block'
    objs.pltInfFnd.style.display = 'none'
  }
})
rad[0].value = 'on'
rad[1].value = 'off'

d3.csv(path + "/fullds.csv")
  .then(function(d) {
    data = d;
    // Adding index number as attribute
    for (let i = 0; i < data.length; i++) {
      data[i]['index'] = i;
      shpidx[data[i]['shp2']] = i;
    }
    groups = d3.group(d, d => d.dep);
    populateDepartmens();
    objs.selDep.onchange = changeDepartment;
    objs.selMun.onchange = updateMun;
    plotInfFnd();
    updateReport(0)
    // Loading geodata, being sure data has been
    // loaded previously
    fetch(path + '/mun.geojson')
      .then(response => response.json())
      .then(function(d) {
        geo = d;
        mapInfFnd();
    })
})

function changeDepartment() {
  populateMunicipalities();
  updateReport(
    objs.selMun.options[objs.selMun.selectedIndex].getAttribute('value')
  )
}

function populateDepartmens() {
  let el = d3.select('#seldep');
  el.selectAll('*').remove();
  el.selectAll('option')
    .data(groups.keys())
    .enter()
    .append('option')
    .text(d => d)
    .attr('value', d => d.index)
    .attr('shape', d => d.shp2)
  populateMunicipalities();
}

function populateMunicipalities() {
  let el = d3.select('#selmun');
  el.selectAll('*').remove();
  el.selectAll('option')
    .data(groups.get(objs.selDep.value))
    .enter()
    .append('option')
    .text(d => d.mun)
    .attr('value', d => d.index)
    .attr('shape', d => d.shp2)
  // if (flag) { 
  //    )
  // }
}

function mapInfFnd() {
  let width = objs.mapInfFnd.clientWidth;
  let height = width * 2.5 / 4;
  let margin = 40;
  let sel = d3.select('#mapinffnd');
  let svg = sel.append('svg')
    .attr('width', width)
    .attr('height', height)
  let projection = d3.geoEquirectangular();
  projection.fitExtent([[margin,margin],[width - margin,height - margin]], geo)
  let geoGenerator = d3.geoPath()
    .projection(projection);
  let scolor = d3.scaleSequential().domain([0, 5])
    .interpolator(d3.interpolateRainbow);
  svg.append('g')
    .selectAll('path')
    .data(geo.features)
    .enter()
    .append('path')
    .attr('d', geoGenerator)
    .attr('stroke', 'gray')
    .attr('id', d => 'map' + d.properties.ID_2)
    .attr('shape', d => d.properties.ID_2)
    .attr('fill', d => shpidx[d.properties.ID_2] >= 0 ? 
      scolor(data[shpidx[d.properties.ID_2]].agr) : "white")
    .on('mouseenter', updateMap)
    .on('mouseout', resetMap)
}

function plotInfFnd() {
  let width = objs.pltInfFnd.clientWidth;
  let height = width * 4 / 4;
  let margin = 40;
  let sel = d3.select('#pltinffnd');
  let svg = sel.append('svg')
    .attr('width', width)
    .attr('height', height)
  let x = d3.scaleLog()
    .domain([d3.min(data, d => d.trfpop) * 0.5, d3.max(data, d => d.trfpop) * 3.5])
    .range([margin, width - margin]);
  let y = d3.scaleLog()
    .domain([d3.min(data, d => d.infpop) * 0.5, d3.max(data, d => d.infpop) * 3.5])
    .range([height - margin, margin]);
  let scolor = d3.scaleSequential().domain([0,5])
    .interpolator(d3.interpolateRainbow);
  svg.append('g')
    .selectAll('circle')
    .data(data)
    .enter()
    .append('circle')
      .attr('cx', d => x(d.trfpop))
      .attr('cy', d => y(d.infpop))
      .attr('r', 3)
      .attr('id', (d, i) => 'circle' + i)
      .attr('index', (d, i) => i)
      .attr('class', 'point')
      .on('mouseenter', updatePoint)
      .on('mouseout', resetPoint)
      .style('fill', d => scolor(d.agr))
      .style('stroke', 'gray')
      .append('title')
        .text(d => d.mun)
  let x_axis = d3.axisBottom()
    .scale(x)
    .tickFormat(d3.format('.1f'))
  let y_axis = d3.axisLeft()
    .scale(y)
    .tickFormat(d3.format('.1f'))
  svg.append('g')
    .attr('transform', `translate(0, ${height - margin})`) 
    .call(x_axis);
  svg.append('g')
    .attr('transform', `translate(${margin}, 0)`) 
    .call(y_axis);
  svg.append('g')
    .append('text')
    .attr('x', width - margin)
    .attr('y', height - margin * 0.2)
    .attr('fill', '#000')
    .attr('font-size', '10px')
    .attr('font-weight', 'bold')
    .attr('text-anchor', 'end')
    .text('Fondos transferidos (miles de USD / miles de hab)')
  svg.append('g')
    .append('text')
    .attr('x', margin * 0.1)
    .attr('y', margin * 0.9)
    .attr('fill', '#000')
    .attr('font-size', '10px')
    .attr('font-weight', 'bold')
    .text('Infecciones confirmadas (casos / miles de hab)')
  if (start) {
    objs.pltInfFnd.style.display = 'none'
    start = false
  }
}

function updatePoint(el) {
  document.getElementById(lastCircle).setAttribute('r', 3)
  el.target.setAttribute('r', 9)
  let index = parseInt(el.target.getAttribute('index'))
  updateReport(index)
  lastCircle = 'circle' + index
}

function resetPoint(el) {
  el.target.setAttribute('r', 3)
}

function updateMap(el) {
  document.getElementById(lastMap).setAttribute('stroke-width', 1)
  el.target.setAttribute('stroke-width', 3)
  let shape = parseInt(el.target.getAttribute('shape'))
  lastMap = 'map' + shape
  let index = shpidx[shape]
  if (index >=0 && index < data.length)
    updateReport(index)
}

function resetMap(el) {
  el.target.setAttribute('stroke-width', 1)
}

function updateMun(el) {
  let index = parseInt(el.target.options[el.target.selectedIndex].getAttribute('value'));
  updateReport(index)
  document.getElementById(lastCircle).setAttribute('r', 3)
  document.getElementById(lastMap).setAttribute('stroke-width', 1)
  document.getElementById('circle' + index).setAttribute('r', 9)
  document.getElementById('map' + data[index].shp2).setAttribute('stroke-width', 3)
  lastCircle = 'circle' + index
  lastMap = 'map' + data[index].shp2
}

function updateReport(index) {
  if (index >= 0) {
    let row = data[index]
    document.getElementById('datTransf').value = d3.format(",.0f")(row.funding)
    document.getElementById('datFndPop').value = d3.format(",.2f")(row.trfpop)
    document.getElementById('datInfec').value = d3.format(',.0f')(row.cases)
    document.getElementById('datInfPop').value = d3.format(',.1f')(row.infpop)
    objs.selDep.value = row.dep
    populateMunicipalities(); 
    objs.selMun.value = row.index
  }
}

