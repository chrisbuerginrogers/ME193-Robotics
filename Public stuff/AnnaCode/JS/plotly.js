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

// Calls cb(customdata) when a point that carries customdata is clicked
export function onPointClick(divName, cb){
    document.getElementById(divName).on('plotly_click', (ev) => {
        const p = ev.points && ev.points[0];
        if (p && p.customdata !== undefined) cb(p.customdata);
    });
}

// Calls cb(JSON string of the customdata ids) when points are box/lasso-selected
export function onSelect(divName, cb){
    document.getElementById(divName).on('plotly_selected', (ev) => {
        const ids = ((ev && ev.points) || []).map(p => p.customdata).filter(v => v !== undefined);
        if (ids.length) cb(JSON.stringify(ids));
    });
}
