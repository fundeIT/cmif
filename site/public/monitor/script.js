/* Budget Monitor Script
 *
 * This script run the interactive elements for Budget Monitor.
 * It loads year, office, program, and code controls, and based in their values
 * updates the month by month plot. It also computes a set of budgetary
 * indicators.
 *
 * (c) FUNDE
 *     2021
 */

'use strict';

import '../node_modules/d3/dist/d3.min.js'

// Base url
const server = '/api/v2/monthly'

// Default color set
let col = ['green', 'blue', 'orange']

// Control objects
var ctrl = {
  year: document.getElementById('year'),
  office: document.getElementById('office'),
  program: document.getElementById('program'),
  object: document.getElementById('object'),
  plot: document.getElementById('plot')
}

ctrl.year.onchange = function() {
  getOffices();
  getMonthlyData();
}
getYears();

ctrl.office.onchange = function() {
  getDetails('program');
  getDetails('object');
  getMonthlyData();
}

ctrl.program.onchange = getMonthlyData;
ctrl.object.onchange = getMonthlyData;

function getYears() {
  const url = server + '?dict=years'
  fetch(url)
    .then(response => response.json())
    .then(function(data) {
      updateYearCtrl(data)
    })
}

function updateYearCtrl(data) {
  let element = d3.select('#year')
  element.selectAll('*').remove()
  element.selectAll('option')
    .data(data)
    .enter()
    .append('option')
    .text(d => d.name)
    .attr('value', d => d.id)
  element.style.display = 'block'
  ctrl['year'].selectedIndex = ctrl['year'].children.length - 1;
  getOffices();
}

function getOffices() {
  if (ctrl.year.selectedIndex >= 0) {
    var year = ctrl.year.options[ctrl.year.selectedIndex].getAttribute('value')
    const url = server + `/${year}?dict=offices`
    fetch(url)
      .then(response => response.json())
      .then(function(data) {
        updateCtrl(data, 'office')
        getDetails('program');
        getDetails('object');
        getMonthlyData();
      })
  }
}

function getCtrlValue(element) {
  let index = ctrl[element].selectedIndex;
  let value = '';
  if (index >= 0)
    value = ctrl[element].options[index].getAttribute('value');
  return value;
}

function getDetails(element) {
  let year = getCtrlValue('year');
  if (year == '')
    return;
  let office = getCtrlValue('office');
  if (office == '')
    return;
  let url = server + `/${year}/${office}?dict=${element}`
  fetch(url)
    .then(response => response.json())
    .then(function(data) {
      let empty_element = [{id: '', name: '--'}] 
      updateCtrl(empty_element.concat(data), element)
    })
}

function updateCtrl(data, element) {
  let index = ctrl[element].selectedIndex
  let value = -1;
  if (index >= 0)
    value = ctrl[element].options[index].getAttribute('value')
  var sel = d3.select('#' + element)
  sel.selectAll('*').remove()
  sel.selectAll('option')
    .data(data)
    .enter()
    .append('option')
    .text(d => d.id + ' ' + d.name)
    .attr('value', d => d.id)
  sel.style.display = 'block'
  let options = ctrl[element].children;
  for (let i = 0; i < options.length; i++) {
    let nv = options[i].getAttribute('value')
    if (nv == value)
      options[i].selected = true;
  }
}

function getMonthlyData() {
  let year = getCtrlValue('year');
  let office = getCtrlValue('office');
  let program = getCtrlValue('program');
  let object = getCtrlValue('object');
  let url = server + `/${year}/${office}`
  if (program != '')
    url = `${url}/${program}`
  else if (object != '')
    url = `${url}/object`
  if (object != '')
    url = `${url}/${object}`;
  console.log(url);
  fetch(url)
    .then(response => response.json())
    .then(function(data) {
      updatePlot(data);
      updateDownload(data);
      updateIndicators(data);
    })
  let note = document.getElementById('apiurl')
  note.setAttribute('href', url);
  note.textContent = 'https://fiscal.funde.org' + url;
}

function updatePlot(data) {
  let width = plot.clientWidth;
  let height = width * 3 / 4;
  let margin = 40;
  let sel = d3.select('#plot');
  let months = ['Ene', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  sel.selectAll('*').remove();
  let svg = sel.append('svg')
    .attr('width', width)
    .attr('height', height)
  let x = d3.scaleLinear()
    .domain([1, d3.max(data, d => d.month)])
    .range([margin * 2, width - margin / 2]);
  let y = d3.scaleLinear()
    .domain([0, d3.max(data, d => Math.max(d.approved, d.modified, d.accrued, 100.0))])
    .range([height - margin * 2, margin / 2]);
  let accrued = d3.area()
    .x(d => x(d.month))
    .y0(d => y(0))
    .y1(d => y(d.accrued));
  svg.append('g')
    .append('path')
    .attr('d', accrued(data))
    .attr('fill', col[0])
    .attr('fill-opacity', 0.5)
    .attr('stroke', col[0]);
  let line = function(element, value, color) {
    let transf = d3.line()
      .x(d => x(d.month))
      .y(d => y(d[value]))
    svg.append('g')
      .append('path')
      .attr('d', transf(data))
      .attr('fill', 'none')
      .attr('stroke', color)
  }
  let circles = function(element, value, color) {
    element.append('g')
      .selectAll('circle')
      .data(data)
      .enter()
      .append('circle')
      .attr('cx', d => x(d.month))
      .attr('cy', d => y(d[value]))
      .attr('r', 5)
      .attr('fill', color)
      .attr('fill-opacity', 0.5)
      .append('title')
      .text(d => d3.format('.2s')(d[value]))
  } 
  line(svg, 'approved', col[1]);
  line(svg, 'modified', col[2]);
  circles(svg, 'approved', col[1]);
  circles(svg, 'modified', col[2]);
  circles(svg, 'accrued', col[0]);
  let x_axis = d3.axisBottom()
    .scale(x)
  let y_axis = d3.axisLeft()
    .scale(y)
    .tickFormat(d3.format('.2s'))
  svg.append('g')
    .attr('transform', `translate(0, ${height - margin * 1.5})`) 
    .call(x_axis);
  svg.append('g')
    .attr('transform', `translate(${margin * 1.5}, 0)`) 
    .call(y_axis);
  svg.append('g')
    .append('text')
    .attr('x', width - margin * 0.5)
    .attr('y', height - margin * 1.5 - 3)
    .attr('fill', '#000')
    .attr('font-size', '8px')
    .attr('font-weight', 'bold')
    .attr('text-anchor', 'end')
    .text('Meses')
}

function updateDownload(data) {
  let csv = 'month,approved,modified,accrued\n'
  for (let i = 0; i < data.length; i++) {
    csv += data[i].month + ','
    csv += data[i].approved + ','
    csv += data[i].modified + ','
    csv += data[i].accrued + '\n'
  }
  document.getElementById('download').href = URL.createObjectURL(new Blob([csv]));
}

function updateIndicators(data) {
  let fields = ['approved', 'modified', 'accrued'];
  let accum = {};
  let form = d3.format('$,.2f')
  for (let i = 0; i < fields.length; i++) {
    accum[fields[i]] = 0;
    for (let j = 0; j < data.length; j++) 
      accum[fields[i]] += data[j][fields[i]];
    let element = document.getElementById('ind-' + fields[i])
    element.textContent = form(accum[fields[i]]);
  }
  document.getElementById('ind-shifted')
    .textContent = form(accum['modified'] - accum['approved'])
  document.getElementById('ind-balance')
    .textContent = form(accum['modified'] - accum['accrued']);
  document.getElementById('ind-efficiency')
    .textContent = d3.format(".1%")(accum['accrued'] / accum['modified'])
  document.getElementById('ind-credibility')
    .textContent = d3.format(".1%")(1 - Math.abs(accum['accrued'] - accum['approved']) / accum['approved'])
}
