function drawChart(accounts, accountValues) {
    const ctx = document.getElementById('netWorthChart').getContext('2d');

    // Extract unique dates as categories for x-axis labels
    const labels = [...new Set(accountValues.map(value => value.date))].sort();

    // Create datasets for each account, with translucent background based on line color
    const accountDatasets = accounts.map(account => {
        const data = labels.map(date => {
            const entry = accountValues.find(value => value.account_id === account.id && value.date === date);
            return entry ? entry.value : 0;
        });

        return {
            label: account.name,
            data: data,
            borderColor: account.line_color || 'rgba(75, 192, 192, 1)',  // Use line color
            backgroundColor: hexToRGBA(account.line_color || '#cccccc', 0.2),  // Generate translucent background
            fill: true
        };
    });

    // Calculate total net worth for each date
    const totalNetWorthData = labels.map(date => {
        return accounts.reduce((total, account) => {
            const entry = accountValues.find(value => value.account_id === account.id && value.date === date);
            return total + (entry ? entry.value : 0);
        }, 0);
    });

    // Add a solid line dataset for the total net worth
    const totalNetWorthDataset = {
        label: 'Total Net Worth',
        data: totalNetWorthData,
        borderColor: 'rgba(0, 0, 0, 0.8)',  // Solid black line
        borderWidth: 2,
        fill: false
    };

    // Combine all datasets
    const chartData = {
        labels: labels,
        datasets: [...accountDatasets, totalNetWorthDataset]
    };

    const chartOptions = {
        responsive: true,
        scales: {
            x: {
                type: 'category'
            },
            y: {
                beginAtZero: true
            }
        }
    };

    new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: chartOptions
    });
}

// Helper function to convert hex color to RGBA with transparency
function hexToRGBA(hex, alpha = 0.2) {
    // Remove '#' if present
    hex = hex.replace('#', '');
    // Parse r, g, b values
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    // Return RGBA string with specified alpha
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
