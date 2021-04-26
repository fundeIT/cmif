import '../node_modules/d3/dist/d3.min.js';

// Base url
const path = '/veeduria4';

var objs = {
  selDep: document.getElementById('seldep'),
  selMun: document.getElementById('selmun'),
  pltInfFnd: document.getElementById('pltinffnd'),
  pltInfPop: document.getElementById('pltinfpop'),
  pltFndPop: document.getElementById('pltfndpop')
}

var data;
var groups;
var lastCircle = 'circle0';

d3.csv(path + "/fullds.csv")
  .then(function(d) {
    data = d;
    groups = d3.group(d, d => d.dep);
    populateDepartmens();
    objs.selDep.onchange = populateMunicipalities;
    objs.selMun.onchange = updateMun;
    plotInfFnd();
})

function populateDepartmens() {
  let el = d3.select('#seldep');
  el.selectAll('*').remove();
  el.selectAll('option')
    .data(groups.keys())
    .enter()
    .append('option')
    .text(d => d)
    .attr('value', d => d)
  populateMunicipalities();
}

function populateMunicipalities() {
  // console.log(deps.get(objs.selDep.value));
  let el = d3.select('#selmun');
  el.selectAll('*').remove();
  el.selectAll('option')
    .data(groups.get(objs.selDep.value))
    .enter()
    .append('option')
    .text(d => d.mun)
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
      .style('fill', d => scolor(d.grp))
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

function updateMun(el) {
  console.log(el.target.value)
  let index;
  for (let i = 0; i < data.length; i++) {
    if (data[i]['mun'] == el.target.value) {
      index = i
      break
    }
  }
  updateReport(index)
  document.getElementById(lastCircle).setAttribute('r', 3)
  document.getElementById('circle' + index).setAttribute('r', 9)
  lastCircle = 'circle' + index
}

function updateReport(index) {
  let row = data[index]
  document.getElementById('datTransf').value = d3.format(",.0f")(row.funding)
  document.getElementById('datFndPop').value = d3.format(",.2f")(row.trfpop)
  document.getElementById('datInfec').value = d3.format(',.0f')(row.cases)
  document.getElementById('datInfPop').value = d3.format(',.1f')(row.infpop)
  objs.selDep.value = row.dep
  populateMunicipalities(); 
  objs.selMun.value = row.mun
}

function lm(d, ya, xa) {
  var lr = {};
  let n = d.length;
  let sum_x = 0;
  let sum_y = 0;
  let sum_xy = 0;
  let sum_xx = 0;
  let sum_yy = 0;
  for (let i = 0; i < d.length; i++) {
    let x = +(d[i][xa]);
    let y = +(d[i][ya]);
    sum_x += x
    sum_y += y
    sum_xy += x * y
    sum_xx += x * x
    sum_yy += y * y
  }
  lr['slope'] = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x);
  lr['intercept'] = (sum_y - lr.slope * sum_x) / n;
  console.log(sum_x, lr)
  return lr;
}