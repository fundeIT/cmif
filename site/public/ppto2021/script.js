/* 2021 Budget Visualization
 * Fundación Nacional para el Desarrollo
 * Centro de Monitoreo e Incidencia Fiscal
 *
 * Nov. 2020
 */

'use strict';

import '../node_modules/d3/dist/d3.min.js'

// Global variables
const high_color = '#80c0f0'
const low_color = '#f0a780'
const height = 800;
const width = document.querySelector("#plot1").clientWidth;
const left_panel = document.querySelector("#left-panel")
const right_panel = document.querySelector("#right-panel")
var selected_rect = null;
var offices;

// Navigation controls
d3.select("#btn-forward")
    .on('click', function (e) {
        left_panel.classList.add("hidden");
        right_panel.classList.remove("hidden");
    })
    .style('cursor', 'pointer')
d3.select("#btn-back")
    .on('click', function (e) {
        right_panel.classList.add("hidden");
        left_panel.classList.remove("hidden");
    })
    .style('cursor', 'pointer')

function draw(data, tag) {
	 let colors = d3.scaleLinear().domain([-1, 0, 1])
        .range([low_color, 'white', high_color])
    var h = d3.hierarchy(data);
    // var max = findMax(h.children);
    let max = Math.max.apply(
    	Math, h.children.map(
    		d => Math.abs(d.data.diff)
    	)
    )
    h.sum(d => d.value)
     .sort((a, b) => d3.descending(a.value, b.value));

    if (data.name != "root")
        h.value = data.value

    d3.treemap()
        .size([width, height])
        .padding(2)
        (h);

    d3.select(tag).selectAll("*").remove();
    var svg = d3.select(tag)
        .append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', '0 0 ' + width + ' ' + height)
            .attr('preserveAspectRatio', 'none')

    svg.selectAll('rect')
        .data(h.children)
        .enter()
        .append('rect')
        .attr('x', d => d.x0)
        .attr('y', d => d.y0)
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0)
        .style('stroke', 'lightgray')
        .style('fill', function (d, i) {
            return colors(d.data.diff / max);
        })
        .append('title')
        .text(d => improvedLabel(d))

    svg.selectAll('foreignObject')
        .data(h.children)
        .enter()
        .append('foreignObject')
        .attr('x', d => d.x0)
        .attr('y', d => d.y0)
        .attr('width', d => d.x1 - d.x0)
        .attr('height', 1)
        .append('xhtml:body')
        .style('font-size', d => (d.x1 - d.x0) > (width * 0.2) ? '12px' : parseInt(60 * (d.x1 - d.x0) / width) + 'px')
        .style('background', 'rgba(255, 255, 255, 0.1')
        .html(d => formatLabel(d))


    if (tag === '#plot1') {
        svg.selectAll('rect')
            .on('click', onRectClick);
        // .on('mouseout', function() { heads(data) })
        svg.selectAll('foreignObject')
            .on('click', onRectClick);
            // .on('mouseout', function(e, d) { heads(data) })
    }
}

function onRectClick(e, d) {
    e.target.style.stroke = "solid 3px red";
    heads(d.data, true);
}

function moneyFormat(value) {
    return `USD ${(value / 1e6).toFixed(1)} Mill.`;
}

function heads(d, down_level) {

    var previous = 0;
    var current = 0;
    var name = (function(d) {
        if (d.name === 'root')
            return "CIFRAS GLOBALES";
        else
            return d.name;
     })(d);
    d.children.forEach(function (item) {
        previous += item.enacted_2020;
        current += item.proposed_2021;
    })
    document.getElementById('label').innerHTML =
        `<strong>${name}</strong><br/>` +
        `<small>Aprobado 2020: ${moneyFormat(previous)}</small> - ` +
        (name != 'CIFRAS GLOBALES' ?
        `<small><a href="${offices[d.code].link}" target="_blank">Propuesto 2021</a>: ${moneyFormat(current)}</small> ` :
        `<small>Propuesto 2021: ${moneyFormat(current)}</small> `);
    d.children.forEach(function (data) {
        data.value = data.proposed_2021;
    });
    draw(d, '#plot2');
    if (down_level)
        document.querySelector("#btn-forward").dispatchEvent(new Event('click'));
}

function deploy(d, level) {
    d[level].forEach(function (data) {
        data.value = data.proposed_2021;
    });
    d.children = d[level];
    draw(d, '#plot1');
    d.children = d['head_' + level];
    heads(d, false);
}

function load_data() {
    fetch('comparative.json')
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            d3.selectAll('input[name="level"]')
                .on('change', function(e) {
                    deploy(data, e.srcElement.value)
                })
            var radio = document.getElementById('CG')
            radio.checked = true;
            radio.dispatchEvent(new Event('change'));
            // console.log(offices)
        })
}

fetch('offices.json')
    .then(function (response) {
        return response.json()
    })
    .then(function (data) {
        offices = data
        load_data()
    })

function formatLabel(d) {
    return `<strong>${d.data.name}</strong><br/>${(d.data.value / 1e6).toFixed(1)} Mill ` +
    `(Dif. ${moneyFormat(d.data.diff)})`
}

function formatLabelNoHTML(d) {
    return `${d.data.name} ${(d.data.value / 1e6).toFixed(1)} Mill ` +
    `(Dif. ${moneyFormat(d.data.diff)})`
}

function improvedLabel(d) {
    return `${d.data.name}\n` +
           `  Propuesto 2021 : ${(d.data.value / 1e6).toFixed(1)} Mill\n` +
           `  Aprobado 2020 : ${(d.data.enacted_2020 / 1e6).toFixed(1)} Mill\n` +
           `  Diferencia : ${moneyFormat(d.data.diff)})`
}
