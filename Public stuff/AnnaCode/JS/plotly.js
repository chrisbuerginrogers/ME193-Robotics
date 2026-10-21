export function newPlot(divName, data, layout){
    Plotly.newPlot(document.getElementById(divName), data, layout, {responsive: true, staticPlot: true});
}

export function update(divName, data, layout){
    Plotly.update(document.getElementById(divName),  data, layout);
}

export function react(divName, data, layout, config){
    Plotly.react(document.getElementById(divName), data, layout, config);
}

export function purge(divName){
    Plotly.purge(document.getElementById(divName));
}
