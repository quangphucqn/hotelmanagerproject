$(document).ready(function () {
    // Khởi tạo các biểu đồ ban đầu
    const ctx1 = document.getElementById('roomChartId');
    const ctx2 = document.getElementById('roomMonthChartId');

    // Lấy dữ liệu JSON từ thẻ script để đảm bảo an toàn
    const stats = JSON.parse(document.getElementById('stats-data').textContent);
    const monthStats = JSON.parse(document.getElementById('month-stats-data').textContent);

    ctx1.chartInstance = initializeChart(ctx1, stats, 'bar');
    ctx2.chartInstance = initializeChart(ctx2, monthStats, 'line');

    function initializeChart(canvas, parsedData, chartType) {
        console.log('Parsed data:', parsedData); // In dữ liệu đã phân tích cú pháp ra console
        try {
            let labels = parsedData.map(item => item[1] || item[0]);
            let data = parsedData.map(item => item[2] || item[1] || 0);

            return new Chart(canvas.getContext('2d'), {
                type: chartType,
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Thống kê doanh thu',
                        data: data,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        } catch (error) {
            console.error('Error initializing charts:', error);
        }
    }
});

$(document).on('submit', 'form', function (event) {
    event.preventDefault();

    let form = $(this);
    let url = form.attr('action') || window.location.href;
    let data = form.serialize();

    $.ajax({
        url: url,
        method: 'GET',
        data: data,
        success: function (response) {
            let canvas = form.next('canvas')[0];

            // Kiểm tra và hủy biểu đồ cũ trước khi tạo biểu đồ mới
            if (canvas.chartInstance) {
                canvas.chartInstance.destroy(); // Ensure the old chart is destroyed
            }

            // Tạo biểu đồ mới với dữ liệu phản hồi từ yêu cầu AJAX
            console.log('Creating new chart with data:', response); // Debugging the response
            canvas.chartInstance = new Chart(canvas.getContext('2d'), {
                type: 'line', // Có thể thay đổi tùy theo yêu cầu
                data: {
                    labels: response.labels,
                    datasets: [{
                        label: 'Thống kê doanh thu',
                        data: response.data,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        },
        error: function (xhr) {
            console.error('Error in AJAX request:', xhr.responseText);
        }
    });
});
