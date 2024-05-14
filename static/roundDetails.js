document.addEventListener('DOMContentLoaded', function () {
    const graphData = {{ graph_json | tojson | safe
}};
if (graphData && graphData.data && graphData.layout) {
    Plotly.newPlot('graph', graphData.data, graphData.layout);
} else {
    document.getElementById('graph').innerHTML = 'No data available for the graph.';
}
});