document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('viewAllHoles').addEventListener('click', function () {
        const rows = document.querySelectorAll('table tbody tr');
        rows.forEach(row => {
            row.style.display = '';
        });
    });

    document.getElementById('viewSingleHole').addEventListener('click', function () {
        const selectedHole = document.getElementById('holeNumber').value;
        const rows = document.querySelectorAll('table tbody tr');
        rows.forEach((row, index) => {
            if (index + 1 === parseInt(selectedHole)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const figures = JSON.parse('{{ graph_json | tojson | escapejs }}');
    console.log("Graph JSON Data:", figures);

    const graphDiv = document.getElementById('graph');
    if (figures.data && figures.layout) {
        Plotly.newPlot(graphDiv, figures.data, figures.layout).catch(error => {
            console.error('Plotly error:', error);
            graphDiv.innerHTML = 'Failed to load the graph.';
        });
    } else {
        graphDiv.innerHTML = 'No data available for the graph.';
    }
});
